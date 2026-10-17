# GROK.md — agent notes for DreamOS Victorious

Same rules as CLAUDE.md (read it first). Additional facts verified 2026-10-17:

- Scope: DreamOS Victorious only. Not RootForge OS, DroidCommand AI, VictorSuite or Custom-RR.
- State: host-side Python tooling only. **No ROM, system image, boot image, OTA, recovery package or VMOS/vPhone image exists. No boot test has ever been run.**
- Run before/after every change: `bash scripts/test.sh`, `ruff check --select E9,F dreamos tests`, `bash scripts/validate-profiles.sh`.
- Host checks: `python3 -m dreamos env` (read-only; `--strict` exits 1 if the host can't build AOSP).
- Never push to `main`; use feature branches and draft PRs.
- Label claims [Certain] / [Likely] / [Guessing] in status reports.
