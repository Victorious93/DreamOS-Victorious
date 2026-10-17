# Security policy

The full contract is in docs/SECURITY.md. Summary [Certain, enforced by validator + tests]:
- Profiles must keep SELinux `enforcing` and verified boot `preserve`; root/Xposed only `none` or `external_opt_in`.
- No flashing, unlocking, rooting or downloading code in this repo. `env`, `doctor` and `collect-device-info.sh` are read-only.
- SHA-256 manifests/SHA256SUMS detect corruption only — **they are not signatures** and do not authenticate a publisher. Signed releases are future work (Phase 6).
- Report vulnerabilities privately to the maintainer (Victorious93); do not open public issues with exploit details.
