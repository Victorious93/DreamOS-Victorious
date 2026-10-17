import json
import tempfile
import unittest
from pathlib import Path

from dreamos.profile import ProfileError, load_profile, validate_profile


def physical_profile():
    return {
        "schema": 1,
        "name": "Test Reference Device",
        "target": "physical",
        "codename": "reference_device",
        "manufacturer": "Example Corp",
        "model": "Example Device",
        "arch": "arm64-v8a",
        "android_api": 35,
        "source_paths": {"device": "device/example/reference", "kernel": "kernel/example/reference", "vendor": "vendor/example/reference"},
        "security": {"selinux": "enforcing", "verified_boot": "preserve", "root": "none", "xposed": "none", "location_testing": "disabled"},
        "virtualization_targets": [],
    }


class ProfileTests(unittest.TestCase):
    def test_valid_physical(self):
        self.assertEqual(validate_profile(physical_profile())["codename"], "reference_device")

    def test_reject_wrong_nested_types(self):
        for field, value in (("target", []), ("arch", []), ("android_api", "35")):
            d = physical_profile()
            d[field] = value
            with self.subTest(field=field), self.assertRaises(ProfileError):
                validate_profile(d)
        d = physical_profile()
        d["security"]["root"] = []
        with self.assertRaises(ProfileError):
            validate_profile(d)
        d = physical_profile()
        d["virtualization_targets"] = [{}]
        with self.assertRaises(ProfileError):
            validate_profile(d)

    def test_templates_are_not_build_targets(self):
        root = Path(__file__).resolve().parent.parent
        for file in ("device-template.json", "virtual-template.json"):
            with self.subTest(file=file), self.assertRaises(ProfileError):
                load_profile(root / "profiles" / file)

    def test_valid_virtual(self):
        d = physical_profile()
        d["target"] = "virtual"
        d["source_paths"]["kernel"] = ""
        d["source_paths"]["vendor"] = ""
        d["virtualization_targets"] = ["vmos", "vphone"]
        self.assertIs(validate_profile(d), d)

    def test_missing_field(self):
        d = physical_profile()
        del d["security"]
        with self.assertRaises(ProfileError):
            validate_profile(d)

    def test_unknown_field(self):
        d = physical_profile()
        d["unreviewed"] = True
        with self.assertRaises(ProfileError):
            validate_profile(d)

    def test_codename_injection(self):
        d = physical_profile()
        d["codename"] = "device; touch /tmp/file"
        with self.assertRaises(ProfileError):
            validate_profile(d)

    def test_absolute_path(self):
        d = physical_profile()
        d["source_paths"]["device"] = "/tmp/device"
        with self.assertRaises(ProfileError):
            validate_profile(d)

    def test_parent_traversal(self):
        d = physical_profile()
        d["source_paths"]["vendor"] = "vendor/example/../../secret"
        with self.assertRaises(ProfileError):
            validate_profile(d)

    def test_disallow_permissive_selinux(self):
        d = physical_profile()
        d["security"]["selinux"] = "permissive"
        with self.assertRaises(ProfileError):
            validate_profile(d)

    def test_disallow_disable_avb(self):
        d = physical_profile()
        d["security"]["verified_boot"] = "disable"
        with self.assertRaises(ProfileError):
            validate_profile(d)

    def test_no_virtualization_in_physical(self):
        d = physical_profile()
        d["virtualization_targets"] = ["vmos"]
        with self.assertRaises(ProfileError):
            validate_profile(d)

    def test_no_bool_as_android_api(self):
        d = physical_profile()
        d["android_api"] = True
        with self.assertRaises(ProfileError):
            validate_profile(d)

    def test_duplicate_virtual_targets(self):
        d = physical_profile()
        d["target"] = "virtual"
        d["virtualization_targets"] = ["vmos", "vmos"]
        with self.assertRaises(ProfileError):
            validate_profile(d)

    def test_json_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "profile.json"
            p.write_text(json.dumps(physical_profile()))
            self.assertEqual(load_profile(p)["model"], "Example Device")

    def test_reject_oversized_profile(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "profile.json"
            p.write_text("x" * (1024 * 1024 + 1))
            with self.assertRaises(ProfileError):
                load_profile(p)
