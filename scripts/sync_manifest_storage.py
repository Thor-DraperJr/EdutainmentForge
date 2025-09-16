#!/usr/bin/env python
"""Sync local URL manifest with Azure Blob Storage.

Usage:
  python scripts/sync_manifest_storage.py --pull
  python scripts/sync_manifest_storage.py --push
  python scripts/sync_manifest_storage.py --diff

Environment Variables:
  LEARN_MANIFEST_USE_BLOB=true
  LEARN_MANIFEST_STORAGE_ACCOUNT=<account>
  LEARN_MANIFEST_CONTAINER=learn-metadata (default)
  LEARN_MANIFEST_BLOB=url_manifest.json (default)
  URL_MANIFEST_PATH=data/catalog/url_manifest.json (optional override)

Requires azure-identity and azure-storage-blob packages.

Notes:
  - Uses ManagedIdentityCredential if available, otherwise DefaultAzureCredential.
  - Will create container if missing (best-effort) on push.
  - Diff shows module UIDs added/removed/changed counts (units length) only (lightweight).
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Any, Tuple

from datetime import datetime

try:
    from azure.identity import ManagedIdentityCredential, DefaultAzureCredential
    from azure.storage.blob import BlobServiceClient
except Exception as e:  # pragma: no cover - import guard
    raise SystemExit("Azure libraries are required for this script: pip install azure-identity azure-storage-blob")

DEFAULT_LOCAL_PATH = Path(os.getenv("URL_MANIFEST_PATH", "data/catalog/url_manifest.json"))


def _get_blob_client():
    account = os.getenv("LEARN_MANIFEST_STORAGE_ACCOUNT")
    if not account:
        raise SystemExit("LEARN_MANIFEST_STORAGE_ACCOUNT not set")
    container = os.getenv("LEARN_MANIFEST_CONTAINER", "learn-metadata")
    blob_name = os.getenv("LEARN_MANIFEST_BLOB", "url_manifest.json")

    credential = None
    try:
        credential = ManagedIdentityCredential()
        credential.get_token("https://storage.azure.com/.default")
    except Exception:
        credential = None
    if credential is None:
        credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)

    service = BlobServiceClient(account_url=f"https://{account}.blob.core.windows.net", credential=credential)
    container_client = service.get_container_client(container)
    try:
        container_client.get_container_properties()
    except Exception:
        # attempt creation
        try:
            container_client.create_container()
        except Exception:
            pass
    return container_client.get_blob_client(blob_name)


def _load_local(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"version": 1, "generated_at": datetime.utcnow().isoformat(), "modules": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_remote(blob_client) -> Dict[str, Any]:
    try:
        if not blob_client.exists():  # type: ignore
            return {"version": 1, "generated_at": datetime.utcnow().isoformat(), "modules": {}}
        data = blob_client.download_blob(max_concurrency=1).readall().decode("utf-8")
        return json.loads(data)
    except Exception:
        return {"version": 1, "generated_at": datetime.utcnow().isoformat(), "modules": {}}


def _diff(local: Dict[str, Any], remote: Dict[str, Any]) -> Tuple[str, int]:
    lmods = local.get("modules", {})
    rmods = remote.get("modules", {})
    added = sorted(set(lmods) - set(rmods))
    removed = sorted(set(rmods) - set(lmods))
    changed = []
    for k in set(lmods).intersection(rmods):
        if len(lmods[k].get("units", [])) != len(rmods[k].get("units", [])):
            changed.append(k)
    lines = []
    if added:
        lines.append("Added: " + ", ".join(added))
    if removed:
        lines.append("Removed: " + ", ".join(removed))
    if changed:
        lines.append("Changed (unit count): " + ", ".join(changed))
    if not lines:
        lines.append("No differences in module keys or unit counts.")
    return "\n".join(lines), len(added) + len(removed) + len(changed)


def cmd_pull(args):
    blob_client = _get_blob_client()
    remote = _load_remote(blob_client)
    DEFAULT_LOCAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_LOCAL_PATH.write_text(json.dumps(remote, indent=2), encoding="utf-8")
    print(f"Pulled manifest to {DEFAULT_LOCAL_PATH}")


def cmd_push(args):
    blob_client = _get_blob_client()
    local = _load_local(DEFAULT_LOCAL_PATH)
    blob_client.upload_blob(json.dumps(local, indent=2), overwrite=True, max_concurrency=1)
    print("Pushed local manifest to blob")


def cmd_diff(args):
    blob_client = _get_blob_client()
    local = _load_local(DEFAULT_LOCAL_PATH)
    remote = _load_remote(blob_client)
    report, count = _diff(local, remote)
    print(report)
    print(f"Difference items: {count}")


def main():
    parser = argparse.ArgumentParser(description="Sync manifest with Azure Blob storage")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--pull", action="store_true", help="Download blob manifest to local file")
    g.add_argument("--push", action="store_true", help="Upload local manifest to blob")
    g.add_argument("--diff", action="store_true", help="Show differences between local and remote")
    args = parser.parse_args()

    if args.pull:
        cmd_pull(args)
    elif args.push:
        cmd_push(args)
    elif args.diff:
        cmd_diff(args)


if __name__ == "__main__":
    main()
