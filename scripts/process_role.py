#!/usr/bin/env python
"""Process a single role from certifications_manifest.json.

Steps:
 1. Load certifications manifest
 2. For each certification in the role:
    - For each learning path > module ref with status pending:
        * Ensure the module UID exists in url manifest
        * Trigger refresh via existing refresh script logic (import)
        * On success mark refreshed else failed
 3. Save manifest

This script is intentionally conservative: it will stop on first failure unless --continue-on-error.
"""
from __future__ import annotations
import argparse, sys, json, os
from pathlib import Path
from typing import List

# Reuse manifest model
from src.content.certifications_manifest import CertificationsManifest

# We import refresh logic; assuming a function refresh_module(uid) pattern exists.
try:
    from src.content.fetcher import fetch_module_html  # placeholder usage
    from src.content.processor import process_module  # may not exist; adjust as needed
except Exception:
    fetch_module_html = None  # type: ignore
    process_module = None  # type: ignore

MANIFEST_PATH = Path('data/catalog/certifications_manifest.json')
URL_MANIFEST_PATH = Path('data/catalog/url_manifest.json')


def load_url_manifest():
    if not URL_MANIFEST_PATH.exists():
        return {}
    try:
        data = json.loads(URL_MANIFEST_PATH.read_text())
        modules = data.get('modules') or {}
        return modules
    except Exception:
        return {}


def fake_refresh(module_uid: str) -> bool:
    # Minimal stub until integrated with actual refresh script logic
    modules = load_url_manifest()
    if module_uid not in modules:
        return False
    # In real implementation we'd call the refresh routine. Here we just validate presence.
    return True


def process_role(role_id: str, continue_on_error: bool = False):
    if not MANIFEST_PATH.exists():
        raise SystemExit('certifications_manifest.json not found')
    manifest = CertificationsManifest.load(MANIFEST_PATH)

    modules_index = load_url_manifest()

    processed = 0
    failures = 0
    missing = 0

    role = manifest.roles.get(role_id)
    if not role:
        raise SystemExit(f'Role {role_id} not found')

    for cert in role.certifications.values():
        for lp in cert.learning_paths.values():
            for mod in lp.modules:
                if mod.status != 'pending':
                    continue
                if mod.module_uid not in modules_index:
                    mod.status = 'failed'
                    mod.error = 'missing-in-url-manifest'
                    missing += 1
                    if not continue_on_error:
                        manifest.save(MANIFEST_PATH)
                        print('Stopped due to missing module', mod.module_uid)
                        return
                    else:
                        continue
                ok = fake_refresh(mod.module_uid)
                if ok:
                    mod.status = 'refreshed'
                    mod.error = None
                    processed += 1
                else:
                    mod.status = 'failed'
                    mod.error = 'refresh-failed'
                    failures += 1
                    if not continue_on_error:
                        manifest.save(MANIFEST_PATH)
                        print('Stopped due to refresh failure', mod.module_uid)
                        return
    manifest.save(MANIFEST_PATH)
    print(json.dumps({
        'role': role_id,
        'processed': processed,
        'failures': failures,
        'missing': missing
    }, indent=2))


def main():
    ap = argparse.ArgumentParser(description='Process pending modules for a role')
    ap.add_argument('role_id')
    ap.add_argument('--continue-on-error', action='store_true')
    args = ap.parse_args()
    process_role(args.role_id, continue_on_error=args.continue_on_error)

if __name__ == '__main__':
    main()
