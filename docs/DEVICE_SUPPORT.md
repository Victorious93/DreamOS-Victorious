# Target support and release gates

There is **no confirmed supported target** as of Phase 1. A profile is a build declaration and not evidence of compatibility.

For each physical target, track the exact codename, OEM/model and variant, SoC, Android branch/API, architecture, kernel repo/commit, device tree, proprietary vendor blobs (provenance/permission), build fingerprint, A/B vs A-only slotting, AVB and rollback requirements, dynamic partitions and filesystem format, bootloader unlock route, recovery availability and a tested device rescue path. Identify radios, biometrics, encryption and modem firmware constraints. A booting emulator does not prove a phone build works.

For each virtual target, record the exact VMOS/vPhone product, version, supported ABI, Android guest version, import format, limits, root capability, API/SDK restrictions and vendor documentation. Unknown requirements are blocking, not optional.

The `scripts/collect-device-info.sh` helper is read-only and gathers some observable state from an authorized ADB-connected device; it does not determine every item above, and it intentionally never unlocks, flashes or modifies a phone.
