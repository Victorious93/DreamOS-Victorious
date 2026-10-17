"""Strict validation for device-specific DreamOS build metadata."""
from __future__ import annotations

import json
import re
from pathlib import Path

CODENAME = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")
SUPPORTED_ARCHES = frozenset({"arm64-v8a", "armeabi-v7a", "x86_64", "x86"})
SUPPORTED_TARGETS = frozenset({"physical", "virtual"})
SUPPORTED_VIRTUALIZATION = frozenset({"vmos", "vphone"})
# VMOS Pro guest ROMs: Android 5.1.1 (API 22), 7.1.2 (API 25), 9 (API 28). [Likely, community sources]
VMOS_LEGACY_APIS = frozenset({22, 25})
VMOS_ARCHES = frozenset({"arm64-v8a", "armeabi-v7a"})
REQUIRED = {"schema", "name", "target", "codename", "manufacturer", "model", "arch", "android_api", "source_paths", "security", "virtualization_targets"}
SOURCE_PATH_FIELDS = {"device", "kernel", "vendor"}
SECURITY_FIELDS = {"selinux", "verified_boot", "root", "xposed", "location_testing"}

class ProfileError(ValueError):
    """Profile contains missing, unsupported or unsafe values."""


def _path(value: object, name: str, *, required: bool) -> str:
    if not isinstance(value, str):
        raise ProfileError(f"{name} must be a string")
    if not value and not required:
        return value
    p = Path(value)
    if not value or p.is_absolute() or "/" not in value or "\\" in value or any(segment in {"", ".", ".."} for segment in value.split("/")):
        raise ProfileError(f"{name} must be a safe relative AOSP source-tree path")
    if value.startswith("-") or any(c in value for c in "\n\r\x00"):
        raise ProfileError(f"{name} contains invalid characters")
    return value


def validate_profile(data: object) -> dict:
    if not isinstance(data, dict):
        raise ProfileError("profile root must be a JSON object")
    if set(data) != REQUIRED:
        raise ProfileError(f"profile fields mismatch (missing={sorted(REQUIRED-set(data))}, extra={sorted(set(data)-REQUIRED)})")
    if type(data["schema"]) is not int or data["schema"] != 1:
        raise ProfileError("schema must be 1")
    for field in ("name", "manufacturer", "model"):
        val = data[field]
        if not isinstance(val, str) or not (2 <= len(val.strip()) <= 100) or "replace with" in val.lower() or any(c in val for c in "\n\r\x00"):
            raise ProfileError(f"{field} must be a nonempty one-line string")
    if not isinstance(data["target"], str) or data["target"] not in SUPPORTED_TARGETS:
        raise ProfileError("target must be physical or virtual")
    if not isinstance(data["codename"], str) or not CODENAME.fullmatch(data["codename"]):
        raise ProfileError("codename must be 2-64 lowercase letters/digits/_/-")
    if data["codename"] in {"replace_me", "example", "placeholder"}:
        raise ProfileError("replace the template codename with a verified target")
    if not isinstance(data["arch"], str) or data["arch"] not in SUPPORTED_ARCHES:
        raise ProfileError("unsupported Android architecture")
    if type(data["android_api"]) is not int or not (28 <= data["android_api"] <= 99 or data["android_api"] in VMOS_LEGACY_APIS):
        raise ProfileError("android_api must be an integer between 28 and 99 (22/25 only for VMOS Pro virtual profiles)")
    paths = data["source_paths"]
    if not isinstance(paths, dict) or set(paths) != SOURCE_PATH_FIELDS:
        raise ProfileError("source_paths must contain device, kernel, vendor")
    for name, value in paths.items():
        _path(value, f"source_paths.{name}", required=(data["target"] == "physical"))
        if "yourvendor" in value or "verified/virtual-target" in value:
            raise ProfileError(f"source_paths.{name} is still a template")
    if not paths["device"]:
        raise ProfileError("device source path is required")
    security = data["security"]
    if not isinstance(security, dict) or set(security) != SECURITY_FIELDS:
        raise ProfileError("security must contain selinux, verified_boot, root, xposed, location_testing")
    policies = {
        "selinux": {"enforcing"},
        "verified_boot": {"preserve"},
        "root": {"none", "external_opt_in"},
        "xposed": {"none", "external_opt_in"},
        "location_testing": {"disabled", "android_mock_location"},
    }
    for field, valid in policies.items():
        if not isinstance(security[field], str) or security[field] not in valid:
            raise ProfileError(f"security.{field} must be one of {sorted(valid)}")
    vt = data["virtualization_targets"]
    if not isinstance(vt, list) or any(not isinstance(v, str) for v in vt) or len(vt) != len(set(vt)) or any(v not in SUPPORTED_VIRTUALIZATION for v in vt):
        raise ProfileError("virtualization_targets must be a unique list of vmos/vphone")
    if data["target"] == "physical" and vt:
        raise ProfileError("physical profile cannot simultaneously claim virtual targets; use separate profiles")
    if data["android_api"] in VMOS_LEGACY_APIS and not (data["target"] == "virtual" and vt == ["vmos"]):
        raise ProfileError("android_api 22/25 is only allowed for virtual profiles targeting exactly ['vmos'] (VMOS Pro 5.1.1/7.1.2 guests)")
    if "vmos" in vt and data["arch"] not in VMOS_ARCHES:
        raise ProfileError("VMOS Pro guests are ARM only (armeabi-v7a or arm64-v8a)")
    return data


def load_profile(path: str | Path) -> dict:
    path = Path(path)
    if not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise ProfileError("profile not found or too large")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, OSError, json.JSONDecodeError) as exc:
        raise ProfileError(f"unable to parse profile: {exc}") from exc
    return validate_profile(data)
