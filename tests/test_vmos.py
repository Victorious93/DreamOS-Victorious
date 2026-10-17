"""Tests use tiny synthetic fake ROMs only (no real VMOS files)."""
import io
import json
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from dreamos.__main__ import main
from dreamos.vmos import (SEVEN_Z_MAGIC, VmosError, apply_overlay, check_rom, diff_roms,
                          edit_build_prop, list_rom, load_overlay)

PROP = "ro.build.version.sdk=25\nro.build.version.release=7.1.2\nro.product.cpu.abilist=arm64-v8a\nro.product.model=VM\n"


def _info(name, mode=0o644, link=False, stored=False):
    i = zipfile.ZipInfo(name, date_time=(2019, 5, 6, 7, 8, 10))
    i.create_system = 3
    i.compress_type = zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED
    i.external_attr = ((0o120000 if link else 0o100000) | mode) << 16
    return i


def fake_rom_bytes(prop=PROP, extra=()):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(_info("system/build.prop"), prop)
        z.writestr(_info("system/bin/sh", 0o755, stored=True), b"\x7fELF-fake")
        z.writestr(_info("system/bin/toolbox", 0o755), b"tb")
        z.writestr(_info("system/bin/ls", 0o777, link=True), "toolbox")
        z.writestr(_info("system/xbin/fake-setuid", 0o6755), b"x")
        for name, data in extra:
            z.writestr(_info(name), data)
    return buf.getvalue()


class VmosTests(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.d = Path(self._t.name)

    def tearDown(self):
        self._t.cleanup()

    def rom(self, name="rom.zip", nested=False, **kw):
        data = fake_rom_bytes(**kw)
        p = self.d / name
        if nested:
            with zipfile.ZipFile(p, "w") as z:
                z.writestr(_info("inner.zip", stored=True), data)
        else:
            p.write_bytes(data)
        return p

    def overlay(self, spec, files=None):
        o = self.d / "ov"
        o.mkdir(exist_ok=True)
        for k, v in (files or {}).items():
            (o / k).parent.mkdir(parents=True, exist_ok=True)
            (o / k).write_bytes(v)
        (o / "overlay.json").write_text(json.dumps(spec))
        return o

    def good_overlay(self):
        return self.overlay({"schema": 1,
                             "build_prop": {"set": {"ro.product.model": "DreamOS", "ro.dreamos.version": "0.2"}, "remove": []},
                             "files": [{"src": "apps/Hello.apk", "dest": "system/app/Hello/Hello.apk"},
                                       {"src": "theme/bootanimation.zip", "dest": "system/media/bootanimation.zip"}]},
                            {"apps/Hello.apk": b"APK", "theme/bootanimation.zip": b"BOOT"})

    # --- check
    def test_check_flat_and_nested(self):
        for nested in (False, True):
            r = check_rom(self.rom(nested=nested)).as_dict()
            self.assertTrue(r["ok"], r)
            self.assertEqual((r["sdk"], r["abi"]), ("25", "arm64-v8a"))
            self.assertEqual(r["nested"], "inner.zip" if nested else None)
            self.assertTrue(any("symlink" in w for w in r["warnings"]))

    def test_check_bad_name_missing_prop_traversal_7z(self):
        p = self.rom(name="my rom.zip")
        self.assertTrue(any("special" in e for e in check_rom(p).errors))
        p = self.d / "noprop.zip"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("system/x", b"1")
        self.assertTrue(any("build.prop" in e for e in check_rom(p).errors))
        p = self.d / "trav.zip"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("system/build.prop", PROP)
            z.writestr("../evil", b"1")
        self.assertTrue(any("unsafe" in e for e in check_rom(p).errors))
        p = self.d / "seven.zip"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("rom.7z", SEVEN_Z_MAGIC + b"rest")
        r = check_rom(p)
        self.assertEqual(r.nested_kind, "7z")
        self.assertTrue(any("7z" in w for w in r.warnings))
        (self.d / "junk.zip").write_bytes(b"nope")
        self.assertFalse(check_rom(self.d / "junk.zip").as_dict()["ok"])

    # --- list / diff
    def test_list_nested_matches_flat(self):
        self.assertEqual(list_rom(self.rom("a.zip")), list_rom(self.rom("b.zip", nested=True)))
        inv = list_rom(self.rom("c.zip"))
        self.assertEqual(inv["system/xbin/fake-setuid"]["mode"], "0o6755")
        self.assertTrue(inv["system/bin/ls"]["symlink"])

    def test_diff(self):
        a = self.rom("a.zip")
        b = self.rom("b.zip", prop=PROP + "x=1\n", extra=[("system/app/N.apk", b"n")])
        d = diff_roms(a, b)
        self.assertEqual(d["added"], ["system/app/N.apk"])
        self.assertEqual(d["changed"], ["system/build.prop"])
        self.assertEqual(diff_roms(a, a), {"added": [], "removed": [], "changed": [], "mode_changed": []})

    def test_diff_against_directory(self):
        a = self.rom("a.zip")
        tree = self.d / "tree"
        with zipfile.ZipFile(a) as z:
            z.extract("system/build.prop", tree)
        d = diff_roms(a, tree)
        self.assertNotIn("system/build.prop", d["changed"] + d["added"])
        self.assertIn("system/bin/sh", d["removed"])

    # --- build.prop
    def test_edit_build_prop(self):
        out = edit_build_prop("# c\na=1\nb=2\na=3\n", {"a": "9", "n": "x"}, ["b"])
        self.assertEqual(out, "# c\na=9\n# DreamOS Victorious overlay\nn=x\n")

    # --- apply
    def test_apply_flat_and_nested_preserves_details(self):
        ov = self.good_overlay()
        for nested in (False, True):
            src = self.rom("src.zip", nested=nested)
            out = apply_overlay(src, ov, self.d / f"out{int(nested)}.zip")
            r = check_rom(out).as_dict()
            self.assertTrue(r["ok"], r)
            d = diff_roms(src, out)
            self.assertEqual(d["added"], ["system/app/Hello/Hello.apk", "system/media/bootanimation.zip"])
            self.assertEqual(d["changed"], ["system/build.prop"])
            self.assertEqual(d["mode_changed"], [])
            inv = list_rom(out)
            self.assertEqual(inv["system/xbin/fake-setuid"]["mode"], "0o6755")
            self.assertTrue(inv["system/bin/ls"]["symlink"])
            with zipfile.ZipFile(out) as z:
                if nested:
                    self.assertEqual(z.namelist(), ["inner.zip"])
                    self.assertEqual(z.getinfo("inner.zip").compress_type, zipfile.ZIP_STORED)
                    z = zipfile.ZipFile(io.BytesIO(z.read("inner.zip")))
                self.assertEqual(z.namelist()[:5], ["system/build.prop", "system/bin/sh", "system/bin/toolbox", "system/bin/ls", "system/xbin/fake-setuid"])
                self.assertEqual(z.getinfo("system/bin/sh").compress_type, zipfile.ZIP_STORED)
                self.assertEqual(z.getinfo("system/bin/sh").date_time, (2019, 5, 6, 7, 8, 10))
                prop = z.read("system/build.prop").decode()
                self.assertIn("ro.product.model=DreamOS", prop)
                self.assertIn("ro.dreamos.version=0.2", prop)
                self.assertNotIn("ro.product.model=VM", prop)

    def test_apply_deterministic(self):
        ov = self.good_overlay()
        src = self.rom("src.zip", nested=True)
        a = apply_overlay(src, ov, self.d / "a.zip").read_bytes()
        b = apply_overlay(src, ov, self.d / "b.zip").read_bytes()
        self.assertEqual(a, b)

    def test_apply_replaces_existing_file(self):
        src = self.rom("src.zip", extra=[("system/media/bootanimation.zip", b"OLD")])
        out = apply_overlay(src, self.good_overlay(), self.d / "o.zip")
        with zipfile.ZipFile(out) as z:
            self.assertEqual(z.read("system/media/bootanimation.zip"), b"BOOT")
            self.assertEqual(z.namelist().count("system/media/bootanimation.zip"), 1)

    def test_apply_refuses_bad_inputs(self):
        ov = self.good_overlay()
        src = self.rom("src.zip")
        with self.assertRaises(VmosError):
            apply_overlay(src, ov, src)
        with self.assertRaises(VmosError):
            apply_overlay(src, ov, self.d / "bad name.zip")
        p = self.d / "seven.zip"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("rom.7z", SEVEN_Z_MAGIC)
        with self.assertRaises(VmosError):
            apply_overlay(p, ov, self.d / "o.zip")
        self.assertFalse((self.d / "o.zip").exists())

    def test_overlay_safety_rules(self):
        bad_specs = [
            {"schema": 2},
            {"schema": 1, "build_prop": {"set": {"ro.secure": "0"}}},
            {"schema": 1, "build_prop": {"set": {"ro.debuggable": "1"}}},
            {"schema": 1, "build_prop": {"remove": ["ro.adb.secure"]}},
            {"schema": 1, "build_prop": {"set": {"a": "x\ny=1"}}},
            {"schema": 1, "files": [{"src": "f", "dest": "system/xbin/su"}]},
            {"schema": 1, "files": [{"src": "f", "dest": "system/app/magisk.apk"}]},
            {"schema": 1, "files": [{"src": "f", "dest": "system/bin/f"}]},
            {"schema": 1, "files": [{"src": "f", "dest": "system/app/../../x"}]},
            {"schema": 1, "files": [{"src": "../f", "dest": "system/app/f"}]},
            {"schema": 1, "files": [{"src": "f", "dest": "system/app/My App.apk"}]},
            {"schema": 1, "files": [{"src": "f", "dest": "system/app/f", "mode": "4755"}]},
            {"schema": 1, "files": [{"src": "missing", "dest": "system/app/f"}]},
            {"schema": 1, "files": [{"src": "f", "dest": "system/app/f"}, {"src": "f", "dest": "system/app/f"}]},
        ]
        for spec in bad_specs:
            with self.subTest(spec=spec), self.assertRaises(VmosError):
                load_overlay(self.overlay(spec, {"f": b"1"}))

    def test_cli(self):
        src = self.rom("src.zip", nested=True)
        ov = self.good_overlay()
        out = self.d / "cli.zip"
        with redirect_stdout(io.StringIO()) as s:
            self.assertEqual(main(["vmos", "check", str(src)]), 0)
            self.assertEqual(main(["vmos", "apply", str(src), str(ov), "--out", str(out)]), 0)
            self.assertEqual(main(["vmos", "list", str(out)]), 0)
            self.assertEqual(main(["vmos", "diff", str(src), str(out)]), 0)
        self.assertIn("UNTESTED", s.getvalue())
        (self.d / "junk.zip").write_bytes(b"x")
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(main(["vmos", "check", str(self.d / "junk.zip")]), 1)
            self.assertEqual(main(["vmos", "list", str(self.d / "junk.zip")]), 2)


if __name__ == "__main__":
    unittest.main()
