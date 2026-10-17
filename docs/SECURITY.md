# DreamOS security and privacy contract

## Baseline

- Security-preserving configuration: SELinux `enforcing`; preserve verified-boot policy and existing encryption. Any plan to change these requires a separately reviewed, device-specific design, not a generic toggle.
- Least privilege by default. No root binaries, Magisk payloads, Xposed hooks, recovery installers, or universal flash scripts in Phase 1.
- No telemetry collection. The local CLI reads a profile and copies approved source material into a reproducible ZIP. Its `doctor` command checks local tool paths only.
- Profiles provide declared target metadata, **not proof** that vendor binaries, device kernels or VMOS importer APIs work.
- Only read-only `adb shell getprop` and `getenforce` operations are supplied for manual device inspection; they run for the explicit serial only.
- The bundle format includes SHA-256 checksums for accidental modification detection and `flashable: false`. **These checksums are not cryptographic signatures and do not authenticate a publisher.** Verification rejects unlisted files, duplicate paths, traversal paths, oversized archives, symlinks and altered contents.

## Root, Xposed and location testing

Root and hook frameworks must be opt-in, device-dependent, version-pinned and auditable. Integrating Magisk cannot be done reliably from a device-agnostic source ZIP. A future feature may expose clear consent, version detection, on/off capability state and recovery guidance, but must not silently install or hide privileged components.

Location testing is intended for an owned or authorized test environment, using official Android developer mock-location mechanisms when supported. The profile value `android_mock_location` is an intent flag only: no mock-location APK or runtime injection is shipped.

## Secrets and distribution

Do not commit private keys, firmware dumps containing user data, personal fingerprints, private signing credentials or device-specific proprietary files without appropriate permission. Never publish a real device's recovery image and claim generic compatibility.
