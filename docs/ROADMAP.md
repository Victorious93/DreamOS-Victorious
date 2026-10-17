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
