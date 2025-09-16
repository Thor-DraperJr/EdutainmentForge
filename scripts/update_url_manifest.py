#!/usr/bin/env python3
"""Update or refresh the URL manifest for Microsoft Learn modules.

Usage examples:
  python scripts/update_url_manifest.py --module learn.azure.prepare-to-develop-ai-solutions-azure
  python scripts/update_url_manifest.py --all
  python scripts/update_url_manifest.py --module UID1 --module UID2 --force

Environment overrides:
  URL_MANIFEST_PATH
  URL_MANIFEST_REFRESH_DAYS

"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List

# Make src available
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from content.clean_catalog import CleanCatalogService  # type: ignore  # noqa
from content.url_cache import get_url_cache


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Refresh URL manifest for modules")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--module', action='append', dest='modules', help='Module UID(s) to refresh (repeatable)')
    g.add_argument('--all', action='store_true', help='Refresh all curated modules we know about')
    p.add_argument('--force', action='store_true', help='Ignore refresh age and force re-scrape')
    p.add_argument('--skip-head', action='store_true', help='Skip HEAD validation')
    p.add_argument('--verbose', action='store_true', help='Verbose output')
    return p.parse_args()


def collect_all_curated_module_uids(service: CleanCatalogService) -> List[str]:
    # Aggregate curated modules from known certification sets (re-using existing helper methods)
    curated = []
    # We rely on internal curated lists; just call the public get_modules_for_certification
    # for certifications we mark as ready.
    certs = [
        'certification.azure-ai-engineer',
        'certification.identity-and-access-administrator',
        'certification.azure-security-engineer',
        'certification.security-operations-analyst',
        'certification.security-compliance-and-identity-fundamentals',
        'certification.cybersecurity-architect-expert',
        'certification.azure-fundamentals',
        'certification.azure-solutions-architect-expert',
    ]
    seen = set()
    for cert in certs:
        try:
            mods = service.get_modules_for_certification(cert)
            for m in mods:
                if m.uid and m.uid not in seen:
                    curated.append(m.uid)
                    seen.add(m.uid)
        except Exception:
            continue
    return curated


def main() -> int:
    args = parse_args()
    cache = get_url_cache()
    service = CleanCatalogService()

    if args.all:
        target_uids = collect_all_curated_module_uids(service)
    else:
        target_uids = args.modules or []

    if not target_uids:
        print("No modules to refresh.")
        return 0

    refreshed = 0
    skipped = 0
    for uid in target_uids:
        # Get module baseline metadata from catalog (title/url/etc.)
        module_obj = None
        # Attempt to find the module in one of the certification sets quickly
        if args.verbose:
            print(f"[INFO] Locating module metadata for {uid}...")
        # We brute force search curated sets for simplicity (hackathon scope)
        for cert in ['certification.azure-ai-engineer','certification.identity-and-access-administrator','certification.azure-security-engineer','certification.security-operations-analyst','certification.security-compliance-and-identity-fundamentals','certification.cybersecurity-architect-expert','certification.azure-fundamentals','certification.azure-solutions-architect-expert']:
            try:
                for m in service.get_modules_for_certification(cert):
                    if m.uid == uid:
                        module_obj = m
                        break
                if module_obj:
                    break
            except Exception:
                continue
        if not module_obj:
            if args.verbose:
                print(f"[WARN] Could not resolve curated metadata for {uid}; skipping.")
            continue

        # Refresh decision
        if not args.force and not cache.needs_refresh(uid) and cache.get_module(uid):
            skipped += 1
            if args.verbose:
                print(f"[SKIP] {uid} (fresh enough)")
            continue

        try:
            if args.verbose:
                print(f"[REFRESH] {uid}")
            cache.refresh_module(
                uid=module_obj.uid,
                module_url=module_obj.url,
                level=module_obj.level,
                duration_minutes=module_obj.duration_minutes,
                verify_head=not args.skip_head,
            )
            refreshed += 1
        except Exception as e:
            print(f"[ERROR] Failed refreshing {uid}: {e}")

    print(f"Completed. Refreshed={refreshed} Skipped={skipped} TotalTargets={len(target_uids)}")
    print(f"Manifest written at {cache.manifest_path}")
    return 0


if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main())
