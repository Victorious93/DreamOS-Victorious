# Changelog

## [Unreleased] — 0.2.0-dev (2026-10-17)
### Added
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
