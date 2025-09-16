#!/usr/bin/env python
"""Sync certifications_manifest.json with Azure Blob (push/pull/diff).

Env vars reused:
  LEARN_MANIFEST_STORAGE_ACCOUNT (required)
  CERT_MANIFEST_CONTAINER (default: learn-metadata)
  CERT_MANIFEST_BLOB (default: certifications_manifest.json)

Usage:
  python scripts/sync_certifications_manifest_storage.py --diff
  python scripts/sync_certifications_manifest_storage.py --push
  python scripts/sync_certifications_manifest_storage.py --pull
"""
from __future__ import annotations
import os, json, sys, hashlib
from pathlib import Path
import argparse

try:
    from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
    from azure.storage.blob import BlobServiceClient
except Exception as e:  # pragma: no cover
    print("Azure libraries not installed:", e)
    BlobServiceClient = None  # type: ignore

LOCAL_PATH = Path('data/catalog/certifications_manifest.json')

def get_blob_client():
    account = os.getenv('LEARN_MANIFEST_STORAGE_ACCOUNT')
    if not account:
        raise SystemExit('LEARN_MANIFEST_STORAGE_ACCOUNT not set')
    container = os.getenv('CERT_MANIFEST_CONTAINER', 'learn-metadata')
    blob_name = os.getenv('CERT_MANIFEST_BLOB', 'certifications_manifest.json')

    credential = None
    if ManagedIdentityCredential is not None:
        try:
            credential = ManagedIdentityCredential()
            credential.get_token('https://storage.azure.com/.default')  # type: ignore
        except Exception:
            credential = None
    if credential is None and DefaultAzureCredential is not None:
        credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)

    service = BlobServiceClient(account_url=f"https://{account}.blob.core.windows.net", credential=credential)  # type: ignore
    container_client = service.get_container_client(container)
    try:
        container_client.get_container_properties()
    except Exception:
        try:
            container_client.create_container()
        except Exception:
            pass
    return container_client.get_blob_client(blob_name)

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def load_local() -> bytes:
    if not LOCAL_PATH.exists():
        return b''
    return LOCAL_PATH.read_bytes()


def main():
    ap = argparse.ArgumentParser(description='Sync certifications manifest with blob storage')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--push', action='store_true')
    g.add_argument('--pull', action='store_true')
    g.add_argument('--diff', action='store_true')
    args = ap.parse_args()

    if BlobServiceClient is None:
        raise SystemExit('azure-storage-blob not available')

    blob_client = get_blob_client()
    local_bytes = load_local()
    try:
        remote_bytes = blob_client.download_blob(max_concurrency=1).readall()
    except Exception:
        remote_bytes = b''

    if args.diff:
        ls = sha256_bytes(local_bytes) if local_bytes else 'NONE'
        rs = sha256_bytes(remote_bytes) if remote_bytes else 'NONE'
        print(f"local_sha={ls} remote_sha={rs} equal={ls==rs and ls!='NONE'}")
        if local_bytes and not remote_bytes:
            print('Remote missing')
        elif remote_bytes and not local_bytes:
            print('Local missing')
        return
    if args.push:
        if not local_bytes:
            raise SystemExit('Local file missing; nothing to push')
        blob_client.upload_blob(local_bytes, overwrite=True, max_concurrency=1)
        print('Uploaded certifications manifest (bytes=%d)' % len(local_bytes))
        return
    if args.pull:
        if not remote_bytes:
            raise SystemExit('Remote blob missing; nothing to pull')
        LOCAL_PATH.parent.mkdir(parents=True, exist_ok=True)
        LOCAL_PATH.write_bytes(remote_bytes)
        print('Pulled certifications manifest (bytes=%d)' % len(remote_bytes))
        return

if __name__ == '__main__':
    main()
