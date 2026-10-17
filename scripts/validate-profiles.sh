#!/usr/bin/env bash
# Validate every non-template profile; confirm templates are still rejected.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
rc=0
for f in profiles/*.json; do
  case "$f" in
    *-template.json)
      if python3 -m dreamos validate "$f" >/dev/null 2>&1; then echo "FAIL template unexpectedly valid: $f"; rc=1; else echo "ok (template rejected): $f"; fi ;;
    *)
      python3 -m dreamos validate "$f" || rc=1 ;;
  esac
done
exit $rc
