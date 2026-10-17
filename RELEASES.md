# Releases

**No releases have been published. No ROM or image release exists.** [Certain]

Planned process (Phase 6): tag `vX.Y.Z` on a reviewed commit → CI builds artifacts → `python3 -m dreamos sha256 create SHA256SUMS <artifacts>` → sign checksums with a release key held on a secure runner → publish with build log, source revisions and device acceptance report. A ROM release requires Phase 4 exit criteria (boot + hardware acceptance on a named device).
