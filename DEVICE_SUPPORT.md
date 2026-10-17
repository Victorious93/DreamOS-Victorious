# Device support

**No supported device. No virtual target confirmed.** [Certain]

| Target | Profile | Validated | Built | Booted |
| --- | --- | --- | --- | --- |
| Physical (template) | profiles/device-template.json | rejected by design | no | no |
| Virtual VMOS/vPhone (template) | profiles/virtual-template.json | rejected by design | no | no |

Gates and required facts per target: docs/DEVICE_SUPPORT.md. Read-only data collection: `scripts/collect-device-info.sh <serial>` (never run against a real device yet).
Blocking input needed from the owner: exact device codename/model, or exact VMOS/vPhone product + version.
