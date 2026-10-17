# Building DreamOS Victorious

## What can be built today [Certain]
Only host artifacts: a **non-flashable** source-integration ZIP and checksum files.

```bash
python3 -m dreamos env                      # host diagnostics vs AOSP requirements
python3 -m dreamos validate profiles/<p>.json
python3 -m dreamos bundle profiles/<p>.json --out build/dreamos-source-bundle.zip
python3 -m dreamos verify build/dreamos-source-bundle.zip
python3 -m dreamos sha256 create build/SHA256SUMS build/dreamos-source-bundle.zip
python3 -m dreamos sha256 verify build/SHA256SUMS
```
Shipped templates intentionally fail validation; a real verified device profile is required for `bundle`.

## What cannot be built yet [Certain]
No Android image. No AOSP/LineageOS tree has been checked out or compiled for this project.

## Host requirements for a real Android build [Likely — public AOSP guidance]
| Resource | Needed | Current dev box (2026-10-17) |
| --- | --- | --- |
| Disk free | 300 GB min, 400+ GB recommended | ~75 GB free of 125 GB ❌ |
| RAM | 32 GB min, 64 GB recommended | 15.6 GB, no swap ❌ |
| CPU | 8+ cores (more = faster) | 8 vCPU Xeon ✅ (slow) |
| OS | 64-bit Linux x86_64 | Debian 13 trixie ✅ |
| `repo` | required | missing ❌ |
| git / Java / Python | required (AOSP ships its own JDK) | git 2.47, OpenJDK 21, Python 3.13 ✅ |
| adb / fastboot | only for device work | missing |

Next steps once a suitable builder exists: see docs/INTEGRATION.md and docs/ROADMAP.md Phase 2.
