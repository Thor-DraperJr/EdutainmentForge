"""Persistent URL manifest cache for Microsoft Learn modules and units.

Stores stable metadata (module + unit URLs, titles, durations) in JSON manifest.
Includes 30-day refresh logic and optional HEAD validation of unit URLs.
"""
from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

import requests
from bs4 import BeautifulSoup
from utils.logger import get_logger

logger = get_logger(__name__)

try:
    # Azure dependencies are optional until blob mode is enabled
    from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
    from azure.storage.blob import BlobServiceClient
except Exception:  # pragma: no cover - we intentionally avoid failing if azure libs missing locally
    DefaultAzureCredential = None  # type: ignore
    ManagedIdentityCredential = None  # type: ignore
    BlobServiceClient = None  # type: ignore

DEFAULT_MANIFEST_PATH = Path("data/catalog/url_manifest.json")
REFRESH_DAYS_DEFAULT = 30
HEAD_TIMEOUT = 6
GET_TIMEOUT = 20
USER_AGENT = "EdutainmentForge/1.0 (URLManifestCache)"

_LOCK = threading.RLock()


@dataclass
class UnitMeta:
    uid: str
    title: str
    url: str
    duration_minutes: int = 0
    type: str = "content"
    last_verified: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "ok"  # ok | missing | redirected

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uid": self.uid,
            "title": self.title,
            "url": self.url,
            "duration_minutes": self.duration_minutes,
            "type": self.type,
            "last_verified": self.last_verified,
            "status": self.status,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "UnitMeta":
        return UnitMeta(
            uid=d.get("uid", ""),
            title=d.get("title", ""),
            url=d.get("url", ""),
            duration_minutes=d.get("duration_minutes", 0),
            type=d.get("type", "content"),
            last_verified=d.get("last_verified", datetime.utcnow().isoformat()),
            status=d.get("status", "ok"),
        )


@dataclass
class ModuleMeta:
    uid: str
    title: str
    url: str
    level: str = "Unknown"
    duration_minutes: int = 0
    units: List[UnitMeta] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_refreshed: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uid": self.uid,
            "title": self.title,
            "url": self.url,
            "level": self.level,
            "duration_minutes": self.duration_minutes,
            "units": [u.to_dict() for u in self.units],
            "generated_at": self.generated_at,
            "last_refreshed": self.last_refreshed,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "ModuleMeta":
        return ModuleMeta(
            uid=d.get("uid", ""),
            title=d.get("title", ""),
            url=d.get("url", ""),
            level=d.get("level", "Unknown"),
            duration_minutes=d.get("duration_minutes", 0),
            units=[UnitMeta.from_dict(u) for u in d.get("units", [])],
            generated_at=d.get("generated_at", datetime.utcnow().isoformat()),
            last_refreshed=d.get("last_refreshed", datetime.utcnow().isoformat()),
        )


class UrlMetadataCache:
    def __init__(self, manifest_path: Path = DEFAULT_MANIFEST_PATH, refresh_days: int = REFRESH_DAYS_DEFAULT):
        self.manifest_path = manifest_path
        self.refresh_days = refresh_days
        self._data: Dict[str, ModuleMeta] = {}
        self._loaded = False
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    # ---------------- Manifest Load/Save -----------------
    def load(self) -> None:
        with _LOCK:
            if self._loaded:
                return
            if self.manifest_path.exists():
                try:
                    raw = json.loads(self.manifest_path.read_text(encoding="utf-8"))
                    modules = raw.get("modules", {})
                    for uid, mod_dict in modules.items():
                        self._data[uid] = ModuleMeta.from_dict(mod_dict)
                except Exception:
                    # Corrupt file -> backup and start fresh
                    backup = self.manifest_path.with_suffix(".corrupt")
                    try:
                        self.manifest_path.rename(backup)
                    except Exception:
                        pass
                    self._data = {}
            self._loaded = True

    def save(self) -> None:
        with _LOCK:
            self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": 1,
                "generated_at": datetime.utcnow().isoformat(),
                "modules": {uid: mm.to_dict() for uid, mm in self._data.items()},
            }
            tmp = self.manifest_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            tmp.replace(self.manifest_path)
            # Hook for subclasses (e.g., blob upload)
            self._post_save_hook(payload)

    # Subclasses may override
    def _post_save_hook(self, payload: Dict[str, Any]) -> None:  # pragma: no cover - default noop
        return

    # ---------------- Query Interface -----------------
    def get_module(self, uid: str) -> Optional[ModuleMeta]:
        self.load()
        return self._data.get(uid)

    def needs_refresh(self, uid: str) -> bool:
        mod = self.get_module(uid)
        if not mod:
            return True
        try:
            last = datetime.fromisoformat(mod.last_refreshed.replace("Z", ""))
        except Exception:
            return True
        return datetime.utcnow() - last > timedelta(days=self.refresh_days)

    def upsert_module(self, module: ModuleMeta) -> None:
        with _LOCK:
            self._data[module.uid] = module
            self.save()

    # ---------------- Extraction Logic -----------------
    def extract_units_from_html(self, html: str, module_url: str, module_uid: Optional[str] = None) -> List[UnitMeta]:
        """Parse module page HTML to find unit anchors and construct unit metadata."""
        soup = BeautifulSoup(html, "html.parser")
        anchors = []
        # Common selectors for unit navigation
        selectors = [
            ".unit-navigation a",
            "nav.unit-navigation a",
            "ol a",
            "ul a"
        ]
        seen = set()
        module_slug = module_url.rstrip('/').split('/')[-1]
        module_base = module_url.rstrip('/')
        module_path_prefix = f"/training/modules/{module_slug}/"
        for sel in selectors:
            for a in soup.select(sel):
                href_raw = a.get("href") or ""
                text = (a.get_text() or "").strip()
                if not href_raw or not text:
                    continue
                # Normalize early
                href = href_raw
                if href.startswith("/en-us"):
                    href = href[6:]
                if href.startswith("/"):
                    href = f"https://learn.microsoft.com{href}"
                if not href.startswith("http"):
                    continue
                if not href.endswith("/"):
                    href += "/"
                # Strict: ensure path portion contains correct module path prefix
                if module_path_prefix not in href:
                    continue
                key = (href, text.lower())
                if key in seen:
                    continue
                seen.add(key)
                anchors.append((href, text))
        # Deduplicate while preserving order
        units: List[UnitMeta] = []
        for href, text in anchors:
            slug_part = href.rstrip('/').split('/')[-1]
            base_uid_prefix = (module_uid or module_url.rstrip('/').split('/')[-1])
            # Ensure we never leak another module's prefix
            unit_uid = f"{base_uid_prefix}.{slug_part}"
            lower = text.lower()
            if "knowledge" in lower:
                utype = "knowledge-check"
            elif "summary" in lower:
                utype = "summary"
            elif "exercise" in lower:
                utype = "exercise"
            else:
                utype = "content"
            units.append(UnitMeta(uid=unit_uid, title=text, url=href, type=utype))

        if not units:
            # Fallback: parse data-unit-uid blocks (current MS Learn layout)
            import re
            pattern = re.compile(r'data-unit-uid="(learn\.[^"]+)"')
            matches = list(pattern.finditer(html))
            # derive canonical slug from asset meta if present
            asset_slug = None
            try:
                asset_tag = soup.find("meta", attrs={"name": "asset_id"})
                if asset_tag and asset_tag.get("content"):
                    # e.g., modules/prepare-azure-ai-development/index
                    asset_slug = asset_tag.get("content").split('/')[-2]
            except Exception:
                pass
            base_slug = asset_slug or module_url.rstrip('/').split('/')[-1]
            base_url = f"https://learn.microsoft.com/en-us/training/modules/{base_slug}/"
            for m in matches:
                uid_full = m.group(1)
                # Capture a window after the match for title extraction
                window = html[m.start(): m.start() + 800]
                title_match = re.search(r'<span class="title">([^<]+)</span>', window)
                raw_title = title_match.group(1).strip() if title_match else uid_full.split('.')[-1].replace('-', ' ').title()
                short = uid_full.split('.')[-1]
                unit_url = base_url + short + '/'
                ltitle = raw_title.lower()
                if 'knowledge' in ltitle:
                    utype = 'knowledge-check'
                elif 'summary' in ltitle:
                    utype = 'summary'
                elif 'exercise' in ltitle:
                    utype = 'exercise'
                else:
                    utype = 'content'
                # If module_uid provided but uid_full lacks it as prefix, normalize to module_uid + slug
                if module_uid and not uid_full.startswith(module_uid + "."):
                    uid_full = f"{module_uid}.{short}"
                units.append(UnitMeta(uid=uid_full, title=raw_title, url=unit_url, type=utype))
            # De-duplicate by uid while preserving order
            seen_uid = set()
            deduped = []
            for u in units:
                if u.uid in seen_uid:
                    continue
                seen_uid.add(u.uid)
                deduped.append(u)
            units = deduped
        # Final normalization pass: enforce module_url path for unit URLs (replace if mismatched)
        normalized_units: List[UnitMeta] = []
        base_module_path = module_url.rstrip('/') + '/'
        for u in units:
            if module_slug not in u.url:
                # Rebuild URL from module_url plus last segment of existing url
                last = u.url.rstrip('/').split('/')[-1]
                u.url = base_module_path + last + '/'
            normalized_units.append(u)
        return normalized_units

    # ---------------- Refresh Workflow -----------------
    def refresh_module(self, uid: str, module_url: str, level: str = "Unknown", duration_minutes: int = 0, verify_head: bool = True) -> ModuleMeta:
        resp = self.session.get(module_url, timeout=GET_TIMEOUT)
        resp.raise_for_status()
        units = self.extract_units_from_html(resp.text, module_url, module_uid=uid)
        # Validation: all unit uids must start with module uid
        for u in units:
            if not u.uid.startswith(uid + "."):
                raise ValueError(f"Unit UID '{u.uid}' does not start with module UID '{uid}'")
        if verify_head:
            for u in units:
                try:
                    h = self.session.head(u.url, timeout=HEAD_TIMEOUT, allow_redirects=True)
                    if h.status_code >= 400:
                        u.status = "missing"
                    elif h.history:
                        u.status = "redirected"
                except Exception:
                    u.status = "missing"
        module = ModuleMeta(
            uid=uid,
            title=self._infer_title(resp.text) or uid,
            url=module_url,
            level=level,
            duration_minutes=duration_minutes,
            units=units,
            last_refreshed=datetime.utcnow().isoformat(),
        )
        self.upsert_module(module)
        return module

    def _infer_title(self, html: str) -> str:
        try:
            soup = BeautifulSoup(html, "html.parser")
            h1 = soup.find("h1")
            if h1 and h1.get_text(strip=True):
                return h1.get_text(strip=True)
            title = soup.find("title")
            if title and title.get_text(strip=True):
                return title.get_text(strip=True).split('-')[0].strip()
        except Exception:
            pass
        return ""


_cache_singleton: Optional[UrlMetadataCache] = None

def get_url_cache() -> UrlMetadataCache:
    global _cache_singleton
    if _cache_singleton is None:
        refresh_days = int(os.getenv("URL_MANIFEST_REFRESH_DAYS", str(REFRESH_DAYS_DEFAULT)))
        manifest_path = Path(os.getenv("URL_MANIFEST_PATH", str(DEFAULT_MANIFEST_PATH)))
        use_blob = os.getenv("LEARN_MANIFEST_USE_BLOB", "false").lower() == "true"
        if use_blob:
            account = os.getenv("LEARN_MANIFEST_STORAGE_ACCOUNT")
            container = os.getenv("LEARN_MANIFEST_CONTAINER", "learn-metadata")
            blob_name = os.getenv("LEARN_MANIFEST_BLOB", "url_manifest.json")
            # Fallback: local file still used as on-disk cache layer
            try:
                if BlobServiceClient is None:
                    raise RuntimeError("azure-storage-blob not available")
                credential = None
                # Prefer managed identity where available
                if ManagedIdentityCredential is not None:
                    try:
                        credential = ManagedIdentityCredential()
                        # A lightweight get_token call to verify (optional)
                        credential.get_token("https://storage.azure.com/.default")  # type: ignore
                    except Exception:
                        credential = None
                if credential is None and DefaultAzureCredential is not None:
                    credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
                if not account:
                    raise RuntimeError("LEARN_MANIFEST_STORAGE_ACCOUNT not set")
                blob_url = f"https://{account}.blob.core.windows.net"
                service = BlobServiceClient(account_url=blob_url, credential=credential)
                container_client = service.get_container_client(container)
                try:
                    container_client.get_container_properties()
                except Exception:
                    # Attempt create if lacking or log failure
                    try:
                        container_client.create_container()
                    except Exception:
                        pass

                class BlobBackedUrlMetadataCache(UrlMetadataCache):  # type: ignore
                    def __init__(self, *args, **kwargs):
                        super().__init__(*args, **kwargs)
                        self._container = container_client
                        self._blob_name = blob_name
                        self._download_once = False

                    def load(self) -> None:  # type: ignore
                        with _LOCK:
                            if self._loaded:
                                return
                            # Download blob if exists, else fall back to local file
                            if not self._download_once:
                                try:
                                    blob_client = self._container.get_blob_client(self._blob_name)
                                    if blob_client.exists():  # type: ignore
                                        data = blob_client.download_blob(max_concurrency=1).readall()
                                        raw = json.loads(data.decode("utf-8"))
                                        modules = raw.get("modules", {})
                                        for uid, mod_dict in modules.items():
                                            self._data[uid] = ModuleMeta.from_dict(mod_dict)
                                        logger.info(
                                            "Loaded manifest from blob %s/%s (modules=%d)",
                                            self._container.container_name,  # type: ignore
                                            self._blob_name,
                                            len(self._data),
                                        )
                                        self._download_once = True
                                    else:
                                        logger.info(
                                            "Blob %s/%s not found; starting with local or empty manifest",
                                            self._container.container_name,  # type: ignore
                                            self._blob_name,
                                        )
                                except Exception as e:
                                    logger.warning("Failed to download manifest blob: %s", e)
                            # Also allow local file override for development merges
                            if self.manifest_path.exists():
                                try:
                                    raw = json.loads(self.manifest_path.read_text(encoding="utf-8"))
                                    modules = raw.get("modules", {})
                                    for uid, mod_dict in modules.items():
                                        self._data[uid] = ModuleMeta.from_dict(mod_dict)
                                except Exception:
                                    pass
                            self._loaded = True

                    def _post_save_hook(self, payload: Dict[str, Any]) -> None:  # type: ignore
                        # Upload JSON to blob
                        try:
                            blob_client = self._container.get_blob_client(self._blob_name)
                            blob_client.upload_blob(
                                json.dumps(payload, indent=2), overwrite=True, max_concurrency=1
                            )
                            logger.info(
                                "Uploaded manifest to blob %s/%s (modules=%d)",
                                self._container.container_name,  # type: ignore
                                self._blob_name,
                                len(payload.get("modules", {})),
                            )
                        except Exception as e:
                            logger.warning("Failed to upload manifest blob: %s", e)

                _cache_singleton = BlobBackedUrlMetadataCache(
                    manifest_path=manifest_path, refresh_days=refresh_days
                )
            except Exception:
                # Fallback to local-only cache if blob init fails
                _cache_singleton = UrlMetadataCache(manifest_path=manifest_path, refresh_days=refresh_days)
        else:
            _cache_singleton = UrlMetadataCache(manifest_path=manifest_path, refresh_days=refresh_days)
    return _cache_singleton
