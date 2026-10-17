# DreamOS Victorious

**Phase 1 — Android ROM source integration foundation (NOT flashable).**

A Victorious Framework project for a customized Android operating-system experience, with device-specific ROM builds as the physical target and VMOS/vPhone evaluation as independent virtual targets.

## Verified implementation status

| Component | Status |
| --- | --- |
| Host-side profile validator | Implemented and unit tested |
| Reproducible source bundle (`zip`) | Implemented and unit tested |
| Bundle manifest / SHA-256 integrity verifier | Implemented and unit tested |
| Read-only ADB property collection script | Implemented, **not tested with a real device** |
| Common AOSP product configuration | Example for device product inheritance, **not yet built with AOSP** |
| Physical ROM image / OTA / recovery / installer | **Not implemented** |
| VMOS/vPhone-compatible bootable image | **Not implemented**; proprietary import requirements unknown |
| Magisk / Xposed integration | **Not bundled**; root remains external opt-in |
| Location testing | Configuration only; no service or app implemented |

**Do not flash the ZIP produced by the bundle command.** It contains source files, not Android partition images or a recovery installation script.

## Requirements

- Python 3.10+ for the host tooling, with no third-party Python dependencies.
- Linux is recommended for eventual AOSP/Lineage builds. Android toolchain and an actual supported target are **not** provided here.

## Get started (Phase 1)

```bash
python3 -m dreamos doctor
bash scripts/test.sh
cp profiles/device-template.json profiles/my-device.json
# Edit my-device.json using VERIFIED values for your chosen device.
python3 -m dreamos validate profiles/my-device.json
python3 -m dreamos bundle profiles/my-device.json --out build/dreamos-source-bundle.zip
python3 -m dreamos verify build/dreamos-source-bundle.zip
```

The provided device templates intentionally fail validation until device information has been verified and placeholders replaced. The `bundle` command **does not** call Android build tools, flash hardware, change bootloaders, modify SELinux or provide root. The supplied AOSP configuration is meant to be copied into a compatible Android source tree and inherited by an existing, verified device product makefile. See [integration steps](docs/INTEGRATION.md).

To collect properties from an already-connected authorized test phone (read-only):

```bash
adb devices -l
bash scripts/collect-device-info.sh YOUR_DEVICE_SERIAL
```

Do not publish `ro.build.fingerprint` output if device/environment details should remain private.

## Project layout

```
DreamOS-Victorious/
  dreamos/                    Python source-bundle CLI, validation, verification
  aosp/vendor/dreamos/        Minimal AOSP product configuration
  profiles/                   Non-functional templates requiring real device data
  scripts/                    Test runner and read-only device-property collector
  tests/                      Offline automated tests
  docs/                       Architecture, integration, security, device gates, roadmap
  .github/workflows/          Offline CI
```

## Development policy

- Keep physical and virtual targets in separate profiles and build pipelines.
- Do not disable SELinux, verified boot, disk encryption or bootloader security to work around compatibility errors.
- Treat Magisk/Xposed as explicitly user-enabled, version/device-specific optional integrations. Never imply they ship here.
- No arbitrary device flashing or `fastboot flash` command is part of this repository.
- The name and scope are recovered from an earlier DreamOS project conversation. The original Claude transcript could not be re-opened when this foundation was generated. Treat unrecovered original requirements as pending verification; see [provenance](docs/PROVENANCE.md).

Copyright 2026 Victorious Framework. Licensed under Apache-2.0; see [LICENSE](LICENSE).
