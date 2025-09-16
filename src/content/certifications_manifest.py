"""Certification & role tracking manifest.

Tracks ingestion progress for roles -> certifications -> learning paths -> modules.
Status lifecycle per module reference:
  pending: identified but not yet validated/refreshed
  validating: currently being fetched/checked (transient; not persisted long-term)
  refreshed: successfully ingested (module exists in url manifest)
  failed: attempted but failed (store last_error for triage)

Manifest structure example:
{
  "version": 1,
  "generated_at": "ISO",
  "roles": {
     "ai-engineer": {
        "certifications": [
          {
            "id": "azure-ai-engineer-associate",
            "title": "Azure AI Engineer Associate",
            "url": "https://learn.microsoft.com/...",
            "learning_paths": [
              {
                "id": "azure-ai-foundations",
                "title": "Azure AI foundations",
                "url": "https://learn.microsoft.com/...",
                "modules": [
                   {"uid": "learn.wwl.prepare-azure-ai-development", "status": "refreshed"}
                ]
              }
            ]
          }
        ]
     }
  }
}
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import threading

from utils.logger import get_logger

logger = get_logger(__name__)

_CERT_MANIFEST_PATH = Path("data/catalog/certifications_manifest.json")
_LOCK = threading.RLock()

VALID_MODULE_STATUSES = {"pending", "refreshed", "failed"}


def _utcnow() -> str:
    return datetime.utcnow().isoformat()


@dataclass
class ModuleRef:
    uid: str
    status: str = "pending"
    last_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"uid": self.uid, "status": self.status, "last_error": self.last_error}

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "ModuleRef":
        return ModuleRef(
            uid=d.get("uid", ""),
            status=d.get("status", "pending"),
            last_error=d.get("last_error")
        )


@dataclass
class LearningPath:
    id: str
    title: str
    url: str
    modules: List[ModuleRef] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "modules": [m.to_dict() for m in self.modules]
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "LearningPath":
        return LearningPath(
            id=d.get("id", ""),
            title=d.get("title", ""),
            url=d.get("url", ""),
            modules=[ModuleRef.from_dict(m) for m in d.get("modules", [])]
        )


@dataclass
class Certification:
    id: str
    title: str
    url: str
    learning_paths: List[LearningPath] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "learning_paths": [lp.to_dict() for lp in self.learning_paths]
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Certification":
        return Certification(
            id=d.get("id", ""),
            title=d.get("title", ""),
            url=d.get("url", ""),
            learning_paths=[LearningPath.from_dict(lp) for lp in d.get("learning_paths", [])]
        )


@dataclass
class RoleTrack:
    id: str
    certifications: List[Certification] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "certifications": [c.to_dict() for c in self.certifications]
        }

    @staticmethod
    def from_dict(role_id: str, d: Dict[str, Any]) -> "RoleTrack":
        return RoleTrack(
            id=role_id,
            certifications=[Certification.from_dict(c) for c in d.get("certifications", [])]
        )


class CertificationsManifest:
    def __init__(self, path: Path = _CERT_MANIFEST_PATH):
        self.path = path
        self.version = 1
        self.generated_at = _utcnow()
        self.roles: Dict[str, RoleTrack] = {}
        self._loaded = False

    def load(self) -> None:
        with _LOCK:
            if self._loaded:
                return
            if self.path.exists():
                try:
                    raw = json.loads(self.path.read_text(encoding="utf-8"))
                    for role_id, role_obj in raw.get("roles", {}).items():
                        self.roles[role_id] = RoleTrack.from_dict(role_id, role_obj)
                    self.generated_at = raw.get("generated_at", self.generated_at)
                except Exception as e:
                    logger.warning("Failed to load certifications manifest: %s", e)
            self._loaded = True

    def save(self) -> None:
        with _LOCK:
            payload = {
                "version": self.version,
                "generated_at": _utcnow(),
                "roles": {rid: rt.to_dict() for rid, rt in self.roles.items()}
            }
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            tmp.replace(self.path)
            logger.info("Saved certifications manifest (roles=%d)", len(self.roles))

    # --- Mutation / Query helpers ---
    def upsert_role(self, role_id: str) -> RoleTrack:
        self.load()
        if role_id not in self.roles:
            self.roles[role_id] = RoleTrack(id=role_id)
        return self.roles[role_id]

    def add_or_update_certification(self, role_id: str, cert: Certification) -> None:
        role = self.upsert_role(role_id)
        existing = next((c for c in role.certifications if c.id == cert.id), None)
        if existing:
            existing.title = cert.title
            existing.url = cert.url
            # Merge learning paths by id
            for lp in cert.learning_paths:
                ex_lp = next((x for x in existing.learning_paths if x.id == lp.id), None)
                if ex_lp:
                    # Merge modules by uid (keep status if already refreshed)
                    for m in lp.modules:
                        ex_mod = next((em for em in ex_lp.modules if em.uid == m.uid), None)
                        if ex_mod:
                            if ex_mod.status != "refreshed":
                                ex_mod.status = m.status
                                ex_mod.last_error = m.last_error
                        else:
                            ex_lp.modules.append(m)
                else:
                    existing.learning_paths.append(lp)
        else:
            role.certifications.append(cert)
        self.save()

    def update_module_status(self, module_uid: str, status: str, last_error: Optional[str] = None) -> None:
        if status not in VALID_MODULE_STATUSES:
            raise ValueError(f"Invalid status {status}")
        self.load()
        for role in self.roles.values():
            for cert in role.certifications:
                for lp in cert.learning_paths:
                    for m in lp.modules:
                        if m.uid == module_uid:
                            m.status = status
                            m.last_error = last_error
        self.save()

    def summary(self) -> Dict[str, Any]:
        self.load()
        totals = {s: 0 for s in VALID_MODULE_STATUSES}
        role_breakdown: Dict[str, Dict[str, int]] = {}
        for rid, role in self.roles.items():
            rb = {s: 0 for s in VALID_MODULE_STATUSES}
            for cert in role.certifications:
                for lp in cert.learning_paths:
                    for m in lp.modules:
                        if m.status in totals:
                            totals[m.status] += 1
                            rb[m.status] += 1
            role_breakdown[rid] = rb
        totals['roles'] = len(self.roles)
        return {"totals": totals, "roles": role_breakdown}


__all__ = [
    "CertificationsManifest",
    "Certification",
    "LearningPath",
    "ModuleRef",
]
