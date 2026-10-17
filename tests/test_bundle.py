import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from dreamos.bundle import BundleError, build_bundle, verify_bundle
from tests.test_profile import physical_profile


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.profile = self.base / "device.json"
        self.profile.write_text(json.dumps(physical_profile()))
        self.zip = self.base / "output.zip"

    def test_build_then_verify(self):
        build_bundle(self.profile, self.zip)
        report = verify_bundle(self.zip)
        self.assertEqual(report["artifact_type"], "dreamos-source-bundle")
        self.assertIs(report["flashable"], False)
        self.assertEqual(report["device_codename"], "reference_device")
        self.assertTrue(any(x["path"].endswith("common.mk") for x in report["contents"]))

    def test_deterministic(self):
        build_bundle(self.profile, self.zip)
        before = self.zip.read_bytes()
        build_bundle(self.profile, self.zip)
        self.assertEqual(self.zip.read_bytes(), before)

    def test_wrong_extension(self):
        with self.assertRaises(BundleError):
            build_bundle(self.profile, self.base / "image.img")

    def test_reject_tamper(self):
        build_bundle(self.profile, self.zip)
        with zipfile.ZipFile(self.zip) as zf:
            files = {name: zf.read(name) for name in zf.namelist()}
        files["profile.json"] += b"\nTAMPER"
        with zipfile.ZipFile(self.zip, "w") as zf:
            for name, content in files.items():
                zf.writestr(name, content)
        with self.assertRaisesRegex(BundleError, "integrity mismatch"):
            verify_bundle(self.zip)

    def test_reject_traversal(self):
        with zipfile.ZipFile(self.zip, "w") as zf:
            zf.writestr("../oops", "bad")
        with self.assertRaisesRegex(BundleError, "unsafe"):
            verify_bundle(self.zip)

    def test_reject_duplicate_entries(self):
        with zipfile.ZipFile(self.zip, "w") as zf:
            zf.writestr("bad.txt", "first")
            zf.writestr("bad.txt", "second")
        with self.assertRaisesRegex(BundleError, "duplicate"):
            verify_bundle(self.zip)

    def test_reject_missing_manifest(self):
        with zipfile.ZipFile(self.zip, "w") as zf:
            zf.writestr("profile.json", "{}")
        with self.assertRaisesRegex(BundleError, "missing"):
            verify_bundle(self.zip)

    def test_reject_extra_file(self):
        build_bundle(self.profile, self.zip)
        with zipfile.ZipFile(self.zip, "a") as zf:
            zf.writestr("extra.txt", "surprise")
        with self.assertRaises(BundleError):
            verify_bundle(self.zip)

    def test_reject_unsafe_flashable_manifest(self):
        build_bundle(self.profile, self.zip)
        with zipfile.ZipFile(self.zip) as zf:
            files = {name: zf.read(name) for name in zf.namelist()}
        m = json.loads(files["manifest.json"])
        m["flashable"] = True
        files["manifest.json"] = json.dumps(m).encode()
        with zipfile.ZipFile(self.zip, "w") as zf:
            for name, content in files.items():
                zf.writestr(name, content)
        with self.assertRaisesRegex(BundleError, "unsafe flashable"):
            verify_bundle(self.zip)
