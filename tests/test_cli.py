import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from dreamos.__main__ import main
from tests.test_profile import physical_profile


class CliTests(unittest.TestCase):
    def test_doctor_no_mutation(self):
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(["doctor"]), 0)
        self.assertIn("tools", json.loads(out.getvalue()))

    def test_validate_and_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "valid.json"
            out = Path(td) / "bundle.zip"
            path.write_text(json.dumps(physical_profile()))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["validate", str(path)]), 0)
                self.assertEqual(main(["bundle", str(path), "--out", str(out)]), 0)
                self.assertEqual(main(["verify", str(out)]), 0)

    def test_invalid_returns_2(self):
        with redirect_stderr(io.StringIO()):
            self.assertEqual(main(["validate", "/not-found.json"]), 2)
