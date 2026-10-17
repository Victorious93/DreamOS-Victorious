# DreamOS Victorious — dependency-ordered roadmap

Each phase has an explicit exit gate. "Planned" means *not implemented*.

## Phase 1 — reproducible foundation [IMPLEMENTED / HOST VERIFIED]

- Versioned schema for physical and virtual targets.
- Safe source-only AOSP module configuration, English-first locale policy and static edition metadata.
- Deterministic ZIP + SHA-256 manifest, verifier, read-only device-info script.
- Python unittest suite, CI workflow, documentation.
- Exit: unit tests pass, ZIP round trip succeeds. Does **not** require a physical phone.

## Phase 2 — reference Android build [PLANNED]

- Select an actual supported AOSP/Lineage branch and known-good device tree or official virtual target.
- Import and pin platform source, kernel/vendor dependencies, and licensing notices.
- Build and boot pristine baseline on a disposable virtual device where possible.
- Integrate product config without regressions; preserve verified boot and SELinux.
- Exit: archived build log + source revision + successful boot and smoke test.

## Phase 3 — DreamOS settings and policies [PLANNED]

- Add Android settings UI for security/privacy controls, English localization and capability reporting.
- Unit/instrumentation tests for permissions, state persistence, error handling, and migration.
- Integrate Android mock-location *testing* support only where user-selected and visible.
- Exit: tested platform permission model and working UI on supported target.

## Phase 4 — physical-device ROM [PLANNED]

- Device-specific BoardConfig, vendor binaries, kernel, partition layouts, AVB/OTA signing, recovery and rollback plan.
- Root/Xposed compatibility review as opt-in extensions, version-pinned and kept separate from the OS security baseline.
- Test boot, Wi-Fi, Bluetooth, cellular, camera, GPS, media codecs, suspend, thermal limits, OTA and recovery on specific supported devices.
- Exit: boot logs and comprehensive device acceptance report; only then consider a signed ROM release.

## Phase 5 — VMOS / vPhone compatibility [PLANNED]

- Establish supported vendor/version-specific import/export specification (do not assume a ROM ZIP can be imported unchanged).
- Separate virtual image producer, virtual hardware manifest and compatibility adapters from physical ROM build.
- Runtime checks for missing APIs, licensing and boot image constraints; preserve permission prompts and state isolation.
- Exit: confirmed import and boot on named VMOS/vPhone versions, with reproducible tests.

## Phase 6 — release engineering [PLANNED]

- CI for real OS builds; artifact verification, SBOM, dependency/vulnerability review, signing from secure runners.
- Compatibility matrix, reproducibility reports, upgrade/rollback tests, documentation and publication.

## Status check — 2026-10-17
- Phase 1: host tooling verified (43 unit tests pass). Added host diagnostics, SHA256SUMS verification, lint+test CI.
- Phase 2 is **blocked**: (a) no target device/virtual product chosen; (b) current dev box has ~75 GB free disk and 15.6 GB RAM vs ≥300 GB / ≥32 GB needed; (c) `repo` not installed; (d) GitHub repo Victorious93/DreamOS-Victorious not found/accessible.
- No ROM, image or boot test exists.

## Retarget — 2026-10-17: VMOS is the PRIMARY target
Don confirmed DreamOS Victorious is a custom ROM for the VMOS app (virtual Android), not a phone ROM. Physical-device work (old Phase 4) is deferred indefinitely.

Revised order (all "planned" unless marked):
- **V0 – Pin the target [PARTLY DONE: product = VMOS Pro app, confirmed 2026-10-17; still need]:** VMOS Pro app version, host phone ABI, guest Android version.
- **V1 – Host tooling for VMOS packages [can start now on this box]:** inspect/validate a VMOS ROM zip layout (zip-in-zip/7z, no spaces in names), file inventory + SHA-256, diff two ROM trees, overlay builder that adds DreamOS files (build.prop lines, apps, theme) to an unpacked tree and repacks; extend profile schema (`vmos_product`, `vmos_app_version`, allow API 22/25/28+).
- **V2 – Mod path (VMOS Pro):** start from Don's own backup of an installed ROM (System backup -> /storage/emulated/0/vmospro/backup), apply DreamOS overlay, repack, import via "Import local ROM", record boot evidence. Fits this box (ROM ~0.5-2 GB).
- **V3 – Source path (optional):** build vmos-dev/open-vmos-aosp_5.1 (Android 5.1, ~50 GB source + ~100 GB output) — does NOT fit this box (75 GB free, 16 GB RAM). Needs a bigger builder. Non-commercial license only.
- **V4 – VMOS Cloud track (optional):** CloudROM-13/14 source needs collaborator access from VMOS support; publish via their platform. VMOS Edge imports only signed official images (custom not possible).
- **V5 – Releases:** only after a confirmed import + boot on a named VMOS version. Proprietary base ROMs are not redistributed; ship an overlay + instructions instead.

- 2026-10-17: V1 host tools implemented on branch feature/vmos-pro-v1 (synthetic tests only). Next: V2 needs Don's VMOS Pro backup zip + an on-device import test.
