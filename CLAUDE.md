# DreamOS Victorious development agent instructions

Read README.md, docs/SECURITY.md and docs/ROADMAP.md before modifying code.

- DreamOS is a dedicated Android ROM/virtual-Android project, **not** RootForge OS, Custom-RR, VictorSuite or DroidCommand AI. Do not modify unrelated repositories.
- Current baseline is host-only Phase 1. Never claim this tree emits a bootable OS, OTA, VMOS image or recovery package.
- Before any target-specific changes, verify codename, architecture, Android branch, kernel/device/vendor trees, slot/partition map, AVB requirements, licensing and recovery plan.
- Keep SELinux enforcing and verified boot preserved. Make privileged/root features explicit opt-in and assess device-specific regressions.
- Physical device and virtual VMOS/vPhone builds must remain separate pipelines and profiles.
- Add automated tests for each host tool change. Report commands actually executed and results, distinguishing host tests from device testing.
- Do not add unattended bootloader unlocks, silent root installs, arbitrary firmware flashes, generic ROM ZIPs or unsupported vendor API assumptions.
- Preserve licenses and document changes with evidence. Prefer small, reviewable patches.

Attribution: Victorious Framework. Maintainer: Victorious.
