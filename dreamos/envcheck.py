"""Read-only host diagnostics compared against AOSP/LineageOS build needs.

Never installs, downloads or modifies anything. Thresholds are approximate
public guidance (AOSP: >=400 GB free recommended for checkout+build, 32-64 GB RAM).
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path

GIB = 1024 ** 3
REQUIREMENTS = {
    "disk_free_gib": 300,      # minimum; 400+ recommended
    "ram_gib": 32,             # minimum practical; 64 recommended
    "cpu_cores": 8,
}
TOOLS = ("git", "repo", "java", "python3", "adb", "fastboot", "make", "ccache", "m")


def _ram_bytes(meminfo: str | None = None) -> int | None:
    if meminfo is None:
        try:
            meminfo = Path("/proc/meminfo").read_text()
        except OSError:
            return None
    for line in meminfo.splitlines():
        if line.startswith("MemTotal:"):
            return int(line.split()[1]) * 1024
    return None


def _distro(os_release: str | None = None) -> str:
    if os_release is None:
        try:
            os_release = Path("/etc/os-release").read_text()
        except OSError:
            return platform.platform()
    for line in os_release.splitlines():
        if line.startswith("PRETTY_NAME="):
            return line.split("=", 1)[1].strip().strip('"')
    return "unknown"


def _java_version() -> str | None:
    if not shutil.which("java"):
        return None
    try:
        out = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None
    text = (out.stderr or out.stdout).strip().splitlines()
    return text[0] if text else None


def collect(path: str | Path = ".") -> dict:
    disk = shutil.disk_usage(path)
    ram = _ram_bytes()
    return {
        "os": platform.system(),
        "distro": _distro(),
        "kernel": platform.release(),
        "machine": platform.machine(),
        "cpu_cores": os.cpu_count() or 0,
        "ram_gib": round(ram / GIB, 1) if ram else None,
        "disk_free_gib": round(disk.free / GIB, 1),
        "disk_path": str(Path(path).resolve()),
        "java": _java_version(),
        "python": platform.python_version(),
        "tools": {t: shutil.which(t) for t in TOOLS},
    }


def assess(info: dict) -> dict:
    """Return per-check verdicts and an overall AOSP build readiness flag."""
    checks = {}
    for key, minimum in REQUIREMENTS.items():
        value = info.get(key)
        checks[key] = {"have": value, "need": minimum, "ok": value is not None and value >= minimum}
    checks["linux_x86_64"] = {
        "have": f"{info.get('os')}/{info.get('machine')}", "need": "Linux/x86_64",
        "ok": info.get("os") == "Linux" and info.get("machine") in {"x86_64", "AMD64"},
    }
    for tool in ("git", "repo"):
        checks[f"tool_{tool}"] = {"have": info["tools"].get(tool), "need": "on PATH", "ok": bool(info["tools"].get(tool))}
    return {"aosp_build_ready": all(c["ok"] for c in checks.values()), "checks": checks,
            "device_tools": {t: bool(info["tools"].get(t)) for t in ("adb", "fastboot")}}
