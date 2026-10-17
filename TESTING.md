# Testing

## Host tests (exist and pass) [Certain]
```bash
bash scripts/test.sh                     # compileall + unittest (43 tests as of 0.2.0-dev)
ruff check --select E9,F dreamos tests   # lint
bash scripts/validate-profiles.sh        # templates must be rejected; real profiles must pass
shellcheck scripts/*.sh                  # in CI (not installed on the dev box)
```
Coverage: profile validation (tests/test_profile.py), bundle build/verify and tamper/traversal rejection (tests/test_bundle.py), CLI (tests/test_cli.py), SHA-256 checksum files (tests/test_checksum.py), host diagnostics (tests/test_envcheck.py).

## Tests that do NOT exist [Certain]
- No AOSP/Lineage compile test, no image build, no emulator or device boot test, no instrumentation tests, no VMOS/vPhone import test.
- `collect-device-info.sh` has never been run against a real phone.
