# Changelog

## [Unreleased] — 0.2.0-dev (2026-10-17)
### Added (VMOS Pro V1, branch feature/vmos-pro-v1)
- `python3 -m dreamos vmos check|list|diff|apply` (dreamos/vmos.py): VMOS Pro ROM zip layout/naming check incl. one nested zip (nested 7z detected, not unpacked), SHA-256 inventory, ROM/dir diff, overlay apply + deterministic repack preserving entry order, compression, timestamps, Unix modes, setuid bits and symlinks.
- Overlay format `overlays/<name>/overlay.json` (build.prop set/remove, files under system/app|priv-app|media|fonts|etc/dreamos); blocks security props (ro.secure, ro.debuggable, ro.adb.secure, ...), root/hook binaries, setuid modes, unsafe paths. Example: overlays/example/.
- Profile validator: API 22/25 accepted only for virtual profiles with virtualization_targets == ["vmos"]; VMOS profiles must be ARM. Physical rules unchanged (28-99).
- tests/test_vmos.py and VMOS profile tests (59 tests total), synthetic fake ROMs only.
- `python3 -m dreamos env [--path P] [--strict]`: read-only host diagnostics compared against AOSP build needs (dreamos/envcheck.py) and `scripts/env-diagnostics.sh`.
- `python3 -m dreamos sha256 create|verify`: sha256sum-format artifact verification with traversal/duplicate rejection (dreamos/checksum.py).
- `scripts/validate-profiles.sh`: validates all profiles, asserts templates stay rejected.
- `.github/workflows/lint-test.yml`: ruff, shellcheck, unit tests on Python 3.10/3.12.
- Tests: tests/test_checksum.py, tests/test_envcheck.py (15 new; 43 total).
- Docs: GROK.md, BUILD.md, DEVICE_SUPPORT.md, SECURITY.md, TESTING.md, RELEASES.md, CHANGELOG.md; status update in docs/ROADMAP.md.
### Unchanged
- All original Phase 1 code, tests and docs kept as-is (only `dreamos/__main__.py` gained two subcommands).

## 0.1.0 — Phase 1 foundation (from DreamOS-Victorious-Phase1.zip)
- Profile validator, deterministic non-flashable source bundle + SHA-256 manifest verifier, read-only ADB collector, AOSP `common.mk`, 28 unit tests, CI.
