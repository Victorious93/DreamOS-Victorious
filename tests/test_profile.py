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


def vmos_profile(api=25, arch="arm64-v8a"):
    return {"schema": 1, "name": "VMOS Pro Guest", "target": "virtual", "codename": "vmos_pro_712",
            "manufacturer": "VMOS", "model": "VMOS Pro ROM", "arch": arch, "android_api": api,
            "source_paths": {"device": "device/vmos/pro", "kernel": "", "vendor": ""},
            "security": {"selinux": "enforcing", "verified_boot": "preserve", "root": "none", "xposed": "none",
                         "location_testing": "disabled"},
            "virtualization_targets": ["vmos"]}


class VmosProfileTests(unittest.TestCase):
    def test_vmos_apis_accepted(self):
        for api in (22, 25, 28):
            with self.subTest(api=api):
                self.assertEqual(validate_profile(vmos_profile(api))["android_api"], api)

    def test_legacy_api_rejected_for_physical(self):
        for api in (22, 25, 27, 21):
            d = physical_profile()
            d["android_api"] = api
            with self.subTest(api=api), self.assertRaises(ProfileError):
                validate_profile(d)

    def test_legacy_api_rejected_outside_vmos(self):
        for vt in (["vphone"], ["vmos", "vphone"], []):
            d = vmos_profile(22)
            d["virtualization_targets"] = vt
            with self.subTest(vt=vt), self.assertRaises(ProfileError):
                validate_profile(d)
        for api in (21, 23, 24, 26, 27):
            with self.subTest(api=api), self.assertRaises(ProfileError):
                validate_profile(vmos_profile(api))

    def test_vmos_requires_arm_and_security_baseline(self):
        with self.assertRaises(ProfileError):
            validate_profile(vmos_profile(arch="x86_64"))
        d = vmos_profile()
        d["security"]["selinux"] = "permissive"
        with self.assertRaises(ProfileError):
            validate_profile(d)
