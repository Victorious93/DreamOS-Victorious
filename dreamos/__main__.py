"""CLI for host-side DreamOS foundation work; never flashes a device."""
from __future__ import annotations

import argparse
import json
import shutil
import sys

from . import __version__
from .bundle import BundleError, build_bundle, verify_bundle
from .profile import ProfileError, load_profile


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m dreamos", description="DreamOS Victorious source-factory tools (no flashing)")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="inspect available host tools (read-only)")
    p = sub.add_parser("validate", help="validate a device profile")
    p.add_argument("profile")
    p = sub.add_parser("bundle", help="generate a source integration ZIP (not a ROM)")
    p.add_argument("profile")
    p.add_argument("--out", required=True)
    p = sub.add_parser("verify", help="verify a DreamOS source ZIP and hashes")
    p.add_argument("bundle")
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            print(json.dumps({"python": sys.version.split()[0], "tools": {key: shutil.which(key) for key in ("git", "java", "adb", "fastboot", "repo", "m")}, "note": "missing tools are not automatically installed"}, indent=2))
        elif args.command == "validate":
            data = load_profile(args.profile)
            print(f"VALID: {data['name']} ({data['target']}, {data['codename']})")
        elif args.command == "bundle":
            out = build_bundle(args.profile, args.out)
            print(f"CREATED: {out} [source-only, NOT flashable]")
        elif args.command == "verify":
            manifest = verify_bundle(args.bundle)
            print(f"VERIFIED: source-only bundle for {manifest['device_codename']}, {len(manifest['contents'])} files")
    except (ProfileError, BundleError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
