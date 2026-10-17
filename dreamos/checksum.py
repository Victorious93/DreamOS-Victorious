"""SHA-256 artifact verification using the standard `sha256sum` file format.

Checksums detect corruption/accidental change only; they are NOT signatures.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path, PurePosixPath

LINE = re.compile(r"^([0-9a-fA-F]{64}) [ *](.+)$")


class ChecksumError(ValueError):
    """Checksum file malformed or an artifact failed verification."""


def sha256_file(path: str | Path, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def parse_sums(text: str) -> list[tuple[str, str]]:
    entries, seen = [], set()
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip("\r")
        if not line.strip() or line.startswith("#"):
            continue
        m = LINE.match(line)
        if not m:
            raise ChecksumError(f"line {n}: malformed checksum line")
        digest, name = m.group(1).lower(), m.group(2)
        p = PurePosixPath(name)
        if p.is_absolute() or "\\" in name or any(part in {"", ".", ".."} for part in name.split("/")):
            raise ChecksumError(f"line {n}: unsafe path {name!r}")
        if name in seen:
            raise ChecksumError(f"line {n}: duplicate entry {name!r}")
        seen.add(name)
        entries.append((digest, name))
    if not entries:
        raise ChecksumError("checksum file has no entries")
    return entries


def verify_sums(sums_file: str | Path, base: str | Path | None = None) -> list[str]:
    """Verify every listed artifact relative to `base` (default: sums file dir)."""
    sums_file = Path(sums_file)
    root = Path(base) if base is not None else sums_file.parent
    entries = parse_sums(sums_file.read_text(encoding="utf-8"))
    failures = []
    for digest, name in entries:
        target = root / name
        if not target.is_file() or target.is_symlink():
            failures.append(f"{name}: missing")
        elif sha256_file(target) != digest:
            failures.append(f"{name}: SHA-256 mismatch")
    if failures:
        raise ChecksumError("; ".join(failures))
    return [name for _, name in entries]


def write_sums(files: list[str | Path], base: str | Path) -> str:
    base = Path(base).resolve()
    lines = []
    for f in sorted(Path(x).resolve() for x in files):
        rel = f.relative_to(base).as_posix()
        lines.append(f"{sha256_file(f)}  {rel}")
    return "\n".join(lines) + "\n"
