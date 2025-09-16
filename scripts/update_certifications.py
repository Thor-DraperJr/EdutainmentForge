#!/usr/bin/env python
"""Incrementally update certifications manifest.

Usage examples:
  python scripts/update_certifications.py --add-cert \
     --role ai-engineer \
     --cert-id azure-ai-engineer-associate \
     --cert-title "Azure AI Engineer Associate" \
     --cert-url https://learn.microsoft.com/en-us/credentials/certifications/azure-ai-engineer/ \
     --lp-id azure-ai-foundations --lp-title "Azure AI foundations" --lp-url https://learn.microsoft.com/en-us/training/paths/azure-ai-foundations/ \
     --module learn.wwl.prepare-azure-ai-development \
     --module learn.azure-ai-fundamentals.explore-azure-openai

  python scripts/update_certifications.py --summary

Notes:
- This script only manipulates the certifications manifest; it does not refresh module units.
- Use refresh_modules.py separately, then mark statuses with --mark.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
sys.path.append('src')

from content.certifications_manifest import (
    CertificationsManifest, Certification, LearningPath, ModuleRef
)


def parse_args():
    ap = argparse.ArgumentParser(description="Update or summarize certifications manifest")
    ap.add_argument('--manifest-path', default='data/catalog/certifications_manifest.json')
    ap.add_argument('--add-cert', action='store_true', help='Add or update a certification with learning path + modules')
    ap.add_argument('--role', help='Role id (e.g., ai-engineer)')
    ap.add_argument('--cert-id')
    ap.add_argument('--cert-title')
    ap.add_argument('--cert-url')
    ap.add_argument('--lp-id')
    ap.add_argument('--lp-title')
    ap.add_argument('--lp-url')
    ap.add_argument('--module', action='append', help='Module UID (repeatable)')
    ap.add_argument('--mark', action='append', nargs=2, metavar=('MODULE_UID','STATUS'), help='Update module status (pending|refreshed|failed)')
    ap.add_argument('--summary', action='store_true', help='Print summary and exit')
    return ap.parse_args()


def main():
    args = parse_args()
    manifest = CertificationsManifest(path=Path(args.manifest_path))
    manifest.load()

    if args.add_cert:
        required = ['role','cert-id','cert-title','cert-url','lp-id','lp-title','lp-url']
        missing = [r for r in required if getattr(args, r.replace('-', '_')) is None]
        if missing:
            raise SystemExit(f"Missing required args for --add-cert: {missing}")
        modules = [ModuleRef(uid=m, status='pending') for m in (args.module or [])]
        lp = LearningPath(id=args.lp_id, title=args.lp_title, url=args.lp_url, modules=modules)
        cert = Certification(id=args.cert_id, title=args.cert_title, url=args.cert_url, learning_paths=[lp])
        manifest.add_or_update_certification(args.role, cert)
        print(f"Added/updated certification {args.cert_id} under role {args.role}")

    if args.mark:
        for module_uid, status in args.mark:
            manifest.update_module_status(module_uid, status)
            print(f"Marked {module_uid} -> {status}")

    if args.summary:
        summary = manifest.summary()
        print("Summary:")
        print(summary)

    if not (args.add_cert or args.mark or args.summary):
        print("No action specified. Use --add-cert, --mark, or --summary.")


if __name__ == '__main__':
    main()
