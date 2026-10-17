"""CLI for host-side DreamOS foundation work; never flashes a device."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile

from . import __version__
from .bundle import BundleError, build_bundle, verify_bundle
from .checksum import ChecksumError, verify_sums, write_sums
from .envcheck import assess, collect
from .vmos import VmosError, apply_overlay, check_rom, diff_roms, list_rom
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
    p = sub.add_parser("env", help="read-only host diagnostics vs AOSP build requirements")
    p.add_argument("--path", default=".", help="filesystem to measure free space on")
    p.add_argument("--strict", action="store_true", help="exit 1 if host is not AOSP-build ready")
    p = sub.add_parser("sha256", help="create or verify sha256sum-format checksum files")
    p.add_argument("action", choices=["verify", "create"])
    p.add_argument("sums_file", help="SHA256SUMS file (verify) or output path (create)")
    p.add_argument("files", nargs="*", help="artifacts to hash (create only)")
    v = sub.add_parser("vmos", help="VMOS Pro ROM zip tools (host-only; never imports or flashes)")
    vs = v.add_subparsers(dest="vmos_cmd", required=True)
    p = vs.add_parser("check", help="check VMOS Pro ROM zip layout/naming")
    p.add_argument("rom")
    p = vs.add_parser("list", help="list ROM files with SHA-256 (JSON)")
    p.add_argument("rom")
    p = vs.add_parser("diff", help="diff two ROMs (zip or unpacked directory)")
    p.add_argument("a")
    p.add_argument("b")
    p = vs.add_parser("apply", help="apply a DreamOS overlay directory and repack")
    p.add_argument("rom")
    p.add_argument("overlay")
    p.add_argument("--out", required=True)
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
        elif args.command == "env":
            info = collect(args.path)
            report = {"host": info, "assessment": assess(info)}
            print(json.dumps(report, indent=2))
            if args.strict and not report["assessment"]["aosp_build_ready"]:
                return 1
        elif args.command == "vmos":
            if args.vmos_cmd == "check":
                report = check_rom(args.rom).as_dict()
                print(json.dumps(report, indent=2))
                return 0 if report["ok"] else 1
            if args.vmos_cmd == "list":
                print(json.dumps(list_rom(args.rom), indent=2, sort_keys=True))
            elif args.vmos_cmd == "diff":
                print(json.dumps(diff_roms(args.a, args.b), indent=2))
            else:
                out = apply_overlay(args.rom, args.overlay, args.out)
                print(f"CREATED: {out} [UNTESTED in VMOS Pro until imported on a device]")
        elif args.command == "sha256":
            if args.action == "verify":
                names = verify_sums(args.sums_file)
                print(f"SHA256 OK: {len(names)} artifacts")
            else:
                if not args.files:
                    raise ChecksumError("create needs at least one file")
                from pathlib import Path
                out = Path(args.sums_file)
                out.write_text(write_sums(args.files, out.parent), encoding="utf-8")
                print(f"WROTE: {out}")
    except (ProfileError, BundleError, ChecksumError, VmosError, OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
