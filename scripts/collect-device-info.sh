#!/usr/bin/env bash
# Read-only ADB information collector: nothing is flashed, unlocked or rooted.
set -euo pipefail
if [[ $# -ne 1 || -z "$1" ]]; then
  echo 'Usage: scripts/collect-device-info.sh <adb-serial>' >&2
  exit 2
fi
command -v adb >/dev/null || { echo 'adb not found' >&2; exit 2; }
serial="$1"
for key in ro.product.device ro.product.manufacturer ro.product.model ro.product.cpu.abi ro.build.version.sdk ro.build.fingerprint ro.boot.slot_suffix ro.boot.verifiedbootstate ro.boot.vbmeta.device_state; do
  printf '%s=' "$key"
  adb -s "$serial" shell getprop "$key" | tr -d '\r'
  printf '\n'
done
printf 'SELinux=' 
adb -s "$serial" shell getenforce | tr -d '\r'
printf '\n'
