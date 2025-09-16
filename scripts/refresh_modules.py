#!/usr/bin/env python
"""Bulk refresh Microsoft Learn module metadata and persist to manifest (and blob if enabled).

Usage:
    python scripts/refresh_modules.py --uids data/catalog/module_uids.txt
    python scripts/refresh_modules.py --uid learn.wwl.prepare-azure-ai-development --url https://learn.microsoft.com/en-us/training/modules/prepare-azure-ai-development/
  python scripts/refresh_modules.py --fail-fast

File Format (module_uids.txt): each line: <module_uid> <module_url> [<level>] [<duration_minutes>]
By default slug guessing is disabled to avoid incorrect URLs; every line must include an explicit https URL unless --allow-slug-guess is used.

Examples:
  learn.wwl.prepare-azure-ai-development https://learn.microsoft.com/en-us/training/modules/prepare-to-develop-ai-solutions-azure/ Intermediate 75
  learn.azure.ai-services-intro https://learn.microsoft.com/en-us/training/modules/introduction-ai-services/ Beginner 60

Notes:
- If a module is already fresh (within URL_MANIFEST_REFRESH_DAYS) it is skipped unless --force.
- HEAD verification can be disabled with --skip-head.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List, Tuple

from datetime import datetime

import sys
sys.path.append('src')  # Ensure local src import
from content.url_cache import get_url_cache  # noqa: E402


def parse_line(line: str, allow_slug_guess: bool) -> Tuple[str, str, str, int]:
    parts = line.strip().split()
    if not parts or parts[0].startswith('#'):
        raise ValueError("skip")
    uid = parts[0]
    if len(parts) >= 2 and parts[1].startswith('http'):
        url = parts[1]
        level = parts[2] if len(parts) >= 3 else 'Unknown'
        try:
            duration = int(parts[3]) if len(parts) >= 4 else 0
        except ValueError:
            duration = 0
    else:
        if not allow_slug_guess:
            raise ValueError("explicit_url_required")
        # Derive url from last uid segment (best-effort; may 404)
        slug = uid.split('.')[-1]
        url = f"https://learn.microsoft.com/en-us/training/modules/{slug}/"
        level = parts[1] if len(parts) >= 2 else 'Unknown'
        try:
            duration = int(parts[2]) if len(parts) >= 3 else 0
        except ValueError:
            duration = 0
    return uid, url, level, duration


def load_uid_file(path: Path, allow_slug_guess: bool) -> List[Tuple[str, str, str, int]]:
    items = []
    for raw in path.read_text(encoding='utf-8').splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            items.append(parse_line(raw, allow_slug_guess))
        except ValueError:
            continue
    return items


def main():
    ap = argparse.ArgumentParser(description='Bulk refresh Learn modules into manifest')
    ap.add_argument('--uids', help='Path to file listing module UIDs + explicit URL/level/duration')
    ap.add_argument('--uid', action='append', help='Single module UID (can repeat)')
    ap.add_argument('--url', action='append', help='Explicit module URL matching order of --uid (repeatable)')
    ap.add_argument('--force', action='store_true', help='Force refresh even if fresh')
    ap.add_argument('--skip-head', action='store_true', help='Skip HEAD verification of unit URLs')
    ap.add_argument('--fail-fast', action='store_true', help='Stop on first failure')
    ap.add_argument('--allow-slug-guess', action='store_true', help='Permit slug guessing when URL omitted (not recommended)')
    args = ap.parse_args()

    if not args.uids and not args.uid:
        ap.error('Provide --uids file or at least one --uid')

    modules: List[Tuple[str, str, str, int]] = []
    if args.uids:
        modules.extend(load_uid_file(Path(args.uids), args.allow_slug_guess))
    if args.uid:
        # Map provided urls (if any) positionally
        provided_urls = args.url or []
        for idx, u in enumerate(args.uid):
            if idx < len(provided_urls):
                url = provided_urls[idx]
            else:
                if not args.allow_slug_guess:
                    raise SystemExit("Error: URL required for each --uid unless --allow-slug-guess is set")
                slug = u.split('.')[-1]
                url = f"https://learn.microsoft.com/en-us/training/modules/{slug}/"
            modules.append((u, url, 'Unknown', 0))

    cache = get_url_cache()
    refreshed = 0
    skipped = 0
    failures = 0
    for uid, url, level, duration in modules:
        try:
            if not args.force and not cache.needs_refresh(uid):
                skipped += 1
                continue
            mod = cache.refresh_module(uid, url, level=level, duration_minutes=duration, verify_head=not args.skip_head)
            refreshed += 1
            print(f"REFRESHED {uid} units={len(mod.units)}")
        except Exception as e:
            failures += 1
            print(f"ERROR {uid}: {e}")
            if args.fail_fast:
                break

    print(f"Done. refreshed={refreshed} skipped={skipped} failures={failures}")
    if failures > 0:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
