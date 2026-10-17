import io
import json
import unittest
from contextlib import redirect_stdout

from dreamos.__main__ import main
from dreamos.envcheck import _distro, _ram_bytes, assess, collect


def fake(**kw):
    info = {"os": "Linux", "machine": "x86_64", "cpu_cores": 16, "ram_gib": 64.0, "disk_free_gib": 500.0,
            "tools": {"git": "/usr/bin/git", "repo": "/usr/bin/repo", "adb": None, "fastboot": None}}
    info.update(kw)
    return info


class EnvTests(unittest.TestCase):
    def test_ready_host(self):
        self.assertTrue(assess(fake())["aosp_build_ready"])

    def test_small_host_not_ready(self):
        r = assess(fake(ram_gib=15.6, disk_free_gib=76.0))
        self.assertFalse(r["aosp_build_ready"])
        self.assertFalse(r["checks"]["ram_gib"]["ok"])
        self.assertFalse(r["checks"]["disk_free_gib"]["ok"])

    def test_missing_repo_not_ready(self):
        self.assertFalse(assess(fake(tools={"git": "/g", "repo": None}))["aosp_build_ready"])

    def test_unknown_ram_not_ready(self):
        self.assertFalse(assess(fake(ram_gib=None))["checks"]["ram_gib"]["ok"])

    def test_arm_host_not_ready(self):
        self.assertFalse(assess(fake(machine="aarch64"))["aosp_build_ready"])

    def test_parsers(self):
        self.assertEqual(_ram_bytes("MemTotal:  1024 kB\n"), 1024 * 1024)
        self.assertIsNone(_ram_bytes("nothing\n"))
        self.assertEqual(_distro('NAME=x\nPRETTY_NAME="Debian GNU/Linux 13 (trixie)"\n'), "Debian GNU/Linux 13 (trixie)")

    def test_collect_real_host_shape(self):
        info = collect(".")
        for key in ("cpu_cores", "disk_free_gib", "python", "tools"):
            self.assertIn(key, info)
        self.assertGreater(info["disk_free_gib"], 0)

    def test_cli_json(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(main(["env"]), 0)
        self.assertIn("aosp_build_ready", json.loads(buf.getvalue())["assessment"])


if __name__ == "__main__":
    unittest.main()
