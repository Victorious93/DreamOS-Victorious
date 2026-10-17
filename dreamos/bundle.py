"""Generate and verify deterministic, NON-FLASHABLE source integration bundles."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath

from . import __version__
from .profile import load_profile

SOURCE_ROOT = Path(__file__).resolve().parent.parent
BUNDLE_FILES = {
    "vendor/dreamos/config/common.mk": "aosp/vendor/dreamos/config/common.mk",
    "vendor/dreamos/config/edition.conf": "aosp/vendor/dreamos/config/edition.conf",
    "docs/INTEGRATION.md": "docs/INTEGRATION.md",
    "docs/SECURITY.md": "docs/SECURITY.md",
}
MAX_ARCHIVE_BYTES = 10 * 1024 * 1024
MAX_ENTRY_BYTES = 5 * 1024 * 1024
MAX_TOTAL_BYTES = 10 * 1024 * 1024

class BundleError(ValueError):
    """Bundle failed validation."""


def _canonical_json(data: object) -> bytes:
    return (json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _zipinfo(name: str) -> zipfile.ZipInfo:
    item = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
    item.compress_type = zipfile.ZIP_DEFLATED
    item.create_system = 3
    item.external_attr = 0o100644 << 16
    return item


def build_bundle(profile_path: str | Path, output: str | Path) -> Path:
    profile = load_profile(profile_path)
    out = Path(output)
    if out.suffix.lower() != ".zip":
        raise BundleError("output must have a .zip extension")
    files: dict[str, bytes] = {}
    for destination, source in BUNDLE_FILES.items():
        files[destination] = (SOURCE_ROOT / source).read_bytes()
    files["profile.json"] = _canonical_json(profile)
    manifest = {
        "schema": 1,
        "artifact_type": "dreamos-source-bundle",
        "flashable": False,
        "version": __version__,
        "device_codename": profile["codename"],
        "target": profile["target"],
        "contents": [{"path": name, "sha256": _digest(files[name]), "size": len(files[name])} for name in sorted(files)],
    }
    files["manifest.json"] = _canonical_json(manifest)
    out.parent.mkdir(parents=True, exist_ok=True)
    # Atomic replace: interrupted writes do not leave a truncated final archive.
    tmp = out.with_name(out.name + ".tmp")
    try:
        with zipfile.ZipFile(tmp, "w") as zf:
            for name, content in sorted(files.items()):
                zf.writestr(_zipinfo(name), content)
        verify_bundle(tmp)
        tmp.replace(out)
    finally:
        tmp.unlink(missing_ok=True)
    return out


def _valid_entry(name: str) -> bool:
    p = PurePosixPath(name)
    return bool(name) and not name.startswith("/") and "\\" not in name and all(part not in {"", ".", ".."} for part in name.split("/")) and not p.is_absolute() and not name.endswith("/")


def verify_bundle(path: str | Path) -> dict:
    path = Path(path)
    if not path.is_file() or path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise BundleError("bundle missing or larger than permitted")
    try:
        with zipfile.ZipFile(path, "r") as zf:
            infos = zf.infolist()
            names = [i.filename for i in infos]
            if len(infos) > 50 or len(names) != len(set(names)) or any(not _valid_entry(n) for n in names):
                raise BundleError("unsafe or duplicate ZIP entries")
            if any(i.file_size > MAX_ENTRY_BYTES for i in infos) or sum(i.file_size for i in infos) > MAX_TOTAL_BYTES:
                raise BundleError("ZIP uncompressed size limit exceeded")
            if any((i.external_attr >> 16) & 0o170000 == 0o120000 for i in infos):
                raise BundleError("symlinks not permitted")
            if "manifest.json" not in names:
                raise BundleError("manifest.json missing")
            manifest = json.loads(zf.read("manifest.json"))
            if not isinstance(manifest, dict) or set(manifest) != {"schema", "artifact_type", "flashable", "version", "device_codename", "target", "contents"}:
                raise BundleError("invalid manifest layout")
            if manifest["schema"] != 1 or manifest["artifact_type"] != "dreamos-source-bundle" or manifest["flashable"] is not False:
                raise BundleError("wrong bundle type or unsafe flashable claim")
            contents = manifest["contents"]
            if not isinstance(contents, list) or len(contents) != len(names) - 1:
                raise BundleError("manifest content count mismatch")
            seen: set[str] = set()
            for item in contents:
                if not isinstance(item, dict) or set(item) != {"path", "sha256", "size"}:
                    raise BundleError("invalid manifest entry")
                name = item["path"]
                if name in seen or name not in names or name == "manifest.json":
                    raise BundleError("manifest paths missing or duplicated")
                seen.add(name)
                payload = zf.read(name)
                if _digest(payload) != item["sha256"] or len(payload) != item["size"]:
                    raise BundleError(f"integrity mismatch: {name}")
            if seen != set(names) - {"manifest.json"}:
                raise BundleError("unlisted bundle contents")
            return manifest
    except (OSError, zipfile.BadZipFile, RuntimeError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        if isinstance(exc, BundleError):
            raise
        raise BundleError(f"invalid bundle: {exc}") from exc
