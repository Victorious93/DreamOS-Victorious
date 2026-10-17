"""Host-side tools for VMOS Pro ROM packages: check, list, diff, overlay+repack.

What is known [Likely, community guides; never confirmed by a real import here]:
- VMOS Pro imports a .zip, sometimes containing exactly one nested .zip or .7z.
- The ROM is a plain file tree with system/build.prop; file modes and symlinks matter.
- Path/file names with spaces or special characters fail to import.
Repacks preserve each original entry's order, compression method, timestamps,
external attributes (Unix mode / symlink bit) and create_system. Whether a
Linux-made repack imports in VMOS Pro is UNTESTED.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

SEVEN_Z_MAGIC = b"7z\xbc\xaf\x27\x1c"
SAFE_FILENAME = re.compile(r"^[A-Za-z0-9._-]+$")
BUILD_PROP = "system/build.prop"
PROP_KEY = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
# Overlays may not weaken the guest's security baseline (see docs/SECURITY.md).
DENIED_PROPS = frozenset({"ro.secure", "ro.debuggable", "ro.adb.secure", "ro.build.selinux",
                          "ro.boot.selinux", "persist.sys.root_access", "service.adb.root"})
DENIED_BASENAMES = re.compile(r"^(su|sx|daemonsu|magisk.*|busybox|.*xposed.*)$", re.IGNORECASE)
ALLOWED_DEST_ROOTS = ("system/app/", "system/priv-app/", "system/media/", "system/fonts/", "system/etc/dreamos/")
ALLOWED_MODES = {"0644": 0o644, "0755": 0o755}
FIXED_DATE = (2020, 1, 1, 0, 0, 0)
MAX_ENTRIES = 200_000


class VmosError(ValueError):
    """ROM or overlay is malformed or unsafe."""


def _safe_name(name: str) -> bool:
    n = name[:-1] if name.endswith("/") else name
    return bool(n) and not n.startswith("/") and "\\" not in n and all(p not in {"", ".", ".."} for p in n.split("/"))


def _is_symlink(info: zipfile.ZipInfo) -> bool:
    return info.create_system == 3 and (info.external_attr >> 16) & 0o170000 == 0o120000


def _mode(info: zipfile.ZipInfo) -> str | None:
    return oct((info.external_attr >> 16) & 0o7777) if info.create_system == 3 and info.external_attr >> 16 else None


@dataclass
class Layout:
    nested: str | None          # name of nested archive inside outer zip, if any
    nested_kind: str | None     # "zip" / "7z"
    errors: list
    warnings: list
    props: dict
    entries: int

    def as_dict(self) -> dict:
        return {"ok": not self.errors, "nested": self.nested, "nested_kind": self.nested_kind,
                "errors": self.errors, "warnings": self.warnings, "entries": self.entries,
                "sdk": self.props.get("ro.build.version.sdk"), "release": self.props.get("ro.build.version.release"),
                "abi": self.props.get("ro.product.cpu.abilist") or self.props.get("ro.product.cpu.abi")}


def parse_build_prop(text: str) -> dict:
    props = {}
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            props[k.strip()] = v.strip()
    return props


def _check_entries(zf: zipfile.ZipFile, errors: list, warnings: list, where: str) -> None:
    infos = zf.infolist()
    names = [i.filename for i in infos]
    if len(infos) > MAX_ENTRIES:
        errors.append(f"{where}: too many entries ({len(infos)})")
    if len(names) != len(set(names)):
        errors.append(f"{where}: duplicate entry names")
    bad = [n for n in names if not _safe_name(n)]
    if bad:
        errors.append(f"{where}: unsafe entry paths, e.g. {bad[0]!r}")
    if any(i.flag_bits & 0x1 for i in infos):
        errors.append(f"{where}: encrypted entries are not supported")
    odd = [n for n in names if not all(SAFE_FILENAME.match(p) for p in n.rstrip("/").split("/") if p)]
    if odd:
        warnings.append(f"{where}: {len(odd)} entry names contain spaces/special characters, e.g. {odd[0]!r}")
    links = sum(_is_symlink(i) for i in infos)
    if links:
        warnings.append(f"{where}: {links} symlink entries (preserved on repack)")
    if infos and all(i.create_system != 3 for i in infos):
        warnings.append(f"{where}: no Unix modes stored; file permissions may be lost in VMOS")


def _find_nested(zf: zipfile.ZipFile) -> tuple[str | None, str | None]:
    files = [i for i in zf.infolist() if not i.is_dir()]
    if len(files) == 1 and files[0].filename.lower().endswith((".zip", ".7z")):
        with zf.open(files[0]) as fh:
            head = fh.read(6)
        if head == SEVEN_Z_MAGIC:
            return files[0].filename, "7z"
        if head[:4] == b"PK\x03\x04":
            return files[0].filename, "zip"
        return files[0].filename, "unknown"
    return None, None


def check_rom(path: str | Path) -> Layout:
    path = Path(path)
    errors, warnings, props = [], [], {}
    if not SAFE_FILENAME.match(path.name):
        errors.append(f"file name {path.name!r} has spaces/special characters (VMOS Pro import is reported to fail)")
    if path.suffix.lower() != ".zip":
        errors.append("outer ROM file must be a .zip")
    try:
        with zipfile.ZipFile(path) as zf:
            _check_entries(zf, errors, warnings, "outer")
            nested, kind = _find_nested(zf)
            total = len(zf.infolist())
            if kind == "7z":
                warnings.append("nested .7z cannot be inspected with the stdlib; inner layout unchecked")
            elif kind == "unknown":
                errors.append(f"nested archive {nested!r} is neither zip nor 7z")
            elif kind == "zip":
                with _inner_zip(zf, nested) as inner:
                    _check_entries(inner, errors, warnings, nested)
                    total = len(inner.infolist())
                    props = _read_props(inner, errors)
            else:
                props = _read_props(zf, errors)
    except zipfile.BadZipFile as exc:
        errors.append(f"not a valid zip: {exc}")
        return Layout(None, None, errors, warnings, props, 0)
    return Layout(nested, kind, errors, warnings, props, total)


def _read_props(zf: zipfile.ZipFile, errors: list) -> dict:
    try:
        return parse_build_prop(zf.read(BUILD_PROP).decode("utf-8", "replace"))
    except KeyError:
        errors.append(f"{BUILD_PROP} not found (not a VMOS ROM tree?)")
        return {}


class _inner_zip:
    """Context manager: spool a nested zip to a temp file and open it."""
    def __init__(self, outer: zipfile.ZipFile, name: str):
        self.outer, self.name = outer, name

    def __enter__(self) -> zipfile.ZipFile:
        self.tmp = tempfile.TemporaryFile()
        with self.outer.open(self.name) as src:
            shutil.copyfileobj(src, self.tmp, 1024 * 1024)
        self.tmp.seek(0)
        self.zf = zipfile.ZipFile(self.tmp)
        return self.zf

    def __exit__(self, *exc):
        self.zf.close()
        self.tmp.close()


def _hash_entries(zf: zipfile.ZipFile, prefix: str = "") -> dict:
    out = {}
    for info in zf.infolist():
        if info.is_dir():
            continue
        h = hashlib.sha256()
        with zf.open(info) as fh:
            for block in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(block)
        out[prefix + info.filename] = {"sha256": h.hexdigest(), "size": info.file_size, "mode": _mode(info),
                                       "symlink": _is_symlink(info)}
    return out


def list_rom(path: str | Path) -> dict:
    """SHA-256 inventory of a ROM zip (descends one nested zip) or an unpacked directory."""
    path = Path(path)
    if path.is_dir():
        out = {}
        for f in sorted(path.rglob("*")):
            if f.is_symlink():
                out[f.relative_to(path).as_posix()] = {"sha256": hashlib.sha256(str(f.readlink()).encode()).hexdigest(),
                                                       "size": len(str(f.readlink())), "mode": None, "symlink": True}
            elif f.is_file():
                h = hashlib.sha256(f.read_bytes()).hexdigest()
                out[f.relative_to(path).as_posix()] = {"sha256": h, "size": f.stat().st_size,
                                                       "mode": oct(f.stat().st_mode & 0o7777), "symlink": False}
        return out
    with zipfile.ZipFile(path) as zf:
        nested, kind = _find_nested(zf)
        if kind == "zip":
            with _inner_zip(zf, nested) as inner:
                return _hash_entries(inner)
        return _hash_entries(zf)


def diff_roms(a: str | Path, b: str | Path) -> dict:
    la, lb = list_rom(a), list_rom(b)
    changed = sorted(k for k in la.keys() & lb.keys() if la[k]["sha256"] != lb[k]["sha256"])
    mode = sorted(k for k in la.keys() & lb.keys() if la[k]["sha256"] == lb[k]["sha256"] and la[k]["mode"] != lb[k]["mode"])
    return {"added": sorted(lb.keys() - la.keys()), "removed": sorted(la.keys() - lb.keys()),
            "changed": changed, "mode_changed": mode}


# ---------------------------------------------------------------- overlay
def load_overlay(directory: str | Path) -> dict:
    root = Path(directory)
    try:
        spec = json.loads((root / "overlay.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VmosError(f"cannot read overlay.json: {exc}") from exc
    if not isinstance(spec, dict) or set(spec) - {"schema", "build_prop", "files"} or spec.get("schema") != 1:
        raise VmosError("overlay.json must be {schema:1, build_prop?, files?}")
    bp = spec.get("build_prop", {})
    if not isinstance(bp, dict) or set(bp) - {"set", "remove"}:
        raise VmosError("build_prop must contain only set/remove")
    sets, removes = bp.get("set", {}), bp.get("remove", [])
    if not isinstance(sets, dict) or not isinstance(removes, list):
        raise VmosError("build_prop.set must be an object, remove a list")
    for k, v in sets.items():
        if not PROP_KEY.match(k) or not isinstance(v, str) or any(c in v for c in "\r\n\x00") or len(v) > 256:
            raise VmosError(f"invalid build.prop entry {k!r}")
    for k in list(sets) + removes:
        if not isinstance(k, str) or not PROP_KEY.match(k):
            raise VmosError(f"invalid build.prop key {k!r}")
        if k in DENIED_PROPS:
            raise VmosError(f"build.prop key {k!r} affects the security baseline and is not allowed in overlays")
    files = []
    seen = set()
    for item in spec.get("files", []):
        if not isinstance(item, dict) or set(item) - {"src", "dest", "mode"} or not {"src", "dest"} <= set(item):
            raise VmosError("each file needs src and dest (mode optional)")
        src, dest, mode = item["src"], item["dest"], item.get("mode", "0644")
        if not (isinstance(src, str) and isinstance(dest, str) and _safe_name(src) and _safe_name(dest)) or dest.endswith("/"):
            raise VmosError(f"unsafe overlay path: {src!r} -> {dest!r}")
        if not dest.startswith(ALLOWED_DEST_ROOTS):
            raise VmosError(f"dest {dest!r} must be under one of {ALLOWED_DEST_ROOTS}")
        if not all(SAFE_FILENAME.match(p) for p in dest.split("/")):
            raise VmosError(f"dest {dest!r} has spaces/special characters")
        if DENIED_BASENAMES.match(PurePosixPath(dest).name):
            raise VmosError(f"{dest!r}: root/hook binaries are not shipped by overlays (external opt-in only)")
        if mode not in ALLOWED_MODES:
            raise VmosError(f"mode must be one of {sorted(ALLOWED_MODES)} (no setuid)")
        if dest in seen:
            raise VmosError(f"duplicate dest {dest!r}")
        seen.add(dest)
        path = root / src
        if not path.is_file() or path.is_symlink():
            raise VmosError(f"overlay source missing: {src}")
        files.append({"data": path.read_bytes(), "dest": dest, "mode": ALLOWED_MODES[mode]})
    return {"set": sets, "remove": removes, "files": files}


def edit_build_prop(text: str, sets: dict, removes: list) -> str:
    out, done = [], set()
    for line in text.splitlines():
        key = line.split("=", 1)[0].strip() if "=" in line and not line.lstrip().startswith("#") else None
        if key in removes:
            continue
        if key in sets:
            if key not in done:
                out.append(f"{key}={sets[key]}")
                done.add(key)
            continue
        out.append(line)
    new = [k for k in sets if k not in done]
    if new:
        out.append("# DreamOS Victorious overlay")
        out.extend(f"{k}={sets[k]}" for k in new)
    return "\n".join(out) + "\n"


def _clone_info(info: zipfile.ZipInfo) -> zipfile.ZipInfo:
    new = zipfile.ZipInfo(info.filename, date_time=info.date_time)
    new.compress_type = info.compress_type
    new.external_attr = info.external_attr
    new.create_system = info.create_system
    new.comment = info.comment
    new.extra = b""  # drop timestamps/extra fields from the source host for determinism
    return new


def _new_info(name: str, mode: int) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=FIXED_DATE)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = (0o100000 | mode) << 16
    return info


def _rewrite(src: zipfile.ZipFile, dst: zipfile.ZipFile, overlay: dict) -> None:
    replaced = {f["dest"]: f for f in overlay["files"]}
    have_prop = False
    for info in src.infolist():
        if info.filename in replaced:
            f = replaced.pop(info.filename)
            ni = _clone_info(info)
            ni.external_attr = (0o100000 | f["mode"]) << 16
            ni.create_system = 3
            dst.writestr(ni, f["data"])
            continue
        data = src.read(info)
        if info.filename == BUILD_PROP:
            have_prop = True
            data = edit_build_prop(data.decode("utf-8"), overlay["set"], overlay["remove"]).encode("utf-8")
        dst.writestr(_clone_info(info), data)
    if not have_prop:
        raise VmosError(f"{BUILD_PROP} missing from ROM")
    for dest in sorted(replaced):
        dst.writestr(_new_info(dest, replaced[dest]["mode"]), replaced[dest]["data"])


def apply_overlay(rom: str | Path, overlay_dir: str | Path, out: str | Path) -> Path:
    rom, out = Path(rom), Path(out)
    if not SAFE_FILENAME.match(out.name) or out.suffix.lower() != ".zip":
        raise VmosError("output must be a .zip with no spaces/special characters in its name")
    if out.resolve() == rom.resolve():
        raise VmosError("refusing to overwrite the input ROM")
    layout = check_rom(rom)
    hard = [e for e in layout.errors if not e.startswith("file name")]
    if hard:
        raise VmosError("input ROM failed checks: " + "; ".join(hard))
    if layout.nested_kind == "7z":
        raise VmosError("nested .7z ROMs are not supported yet; convert the inner archive to zip first")
    overlay = load_overlay(overlay_dir)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".tmp")
    try:
        with zipfile.ZipFile(rom) as zf, zipfile.ZipFile(tmp, "w", allowZip64=True) as dst:
            if layout.nested:
                info = zf.getinfo(layout.nested)
                buf = io.BytesIO()
                with _inner_zip(zf, layout.nested) as inner, zipfile.ZipFile(buf, "w", allowZip64=True) as ndst:
                    _rewrite(inner, ndst, overlay)
                for other in zf.infolist():  # keep directory entries etc. in original order
                    if other.filename == layout.nested:
                        dst.writestr(_clone_info(info), buf.getvalue())
                    else:
                        dst.writestr(_clone_info(other), zf.read(other))
            else:
                _rewrite(zf, dst, overlay)
        tmp.replace(out)
    finally:
        tmp.unlink(missing_ok=True)
    return out
