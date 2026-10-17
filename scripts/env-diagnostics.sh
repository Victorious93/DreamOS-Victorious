#!/usr/bin/env bash
# Read-only host diagnostics. Installs and downloads nothing.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
exec python3 -m dreamos env --path "${1:-.}"
