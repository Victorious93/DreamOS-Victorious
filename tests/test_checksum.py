import hashlib
import io
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from dreamos.__main__ import main
from dreamos.checksum import ChecksumError, parse_sums, sha256_file, verify_sums, write_sums


class ChecksumTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        (self.d / "a.img").write_bytes(b"alpha")
        (self.d / "sub").mkdir()
        (self.d / "sub" / "b.bin").write_bytes(b"beta" * 1000)

    def tearDown(self):
        self.tmp.cleanup()

    def test_known_digest(self):
        self.assertEqual(sha256_file(self.d / "a.img"), hashlib.sha256(b"alpha").hexdigest())

    def test_round_trip(self):
        sums = self.d / "SHA256SUMS"
        sums.write_text(write_sums([self.d / "a.img", self.d / "sub" / "b.bin"], self.d))
        self.assertEqual(verify_sums(sums), ["a.img", "sub/b.bin"])

    def test_binary_marker_accepted(self):
        h = hashlib.sha256(b"alpha").hexdigest()
        self.assertEqual(parse_sums(f"{h} *a.img\n"), [(h, "a.img")])

    def test_tamper_detected(self):
        sums = self.d / "SHA256SUMS"
        sums.write_text(write_sums([self.d / "a.img"], self.d))
        (self.d / "a.img").write_bytes(b"alphX")
        with self.assertRaisesRegex(ChecksumError, "mismatch"):
            verify_sums(sums)

    def test_missing_detected(self):
        sums = self.d / "SHA256SUMS"
        sums.write_text("0" * 64 + "  gone.img\n")
        with self.assertRaisesRegex(ChecksumError, "missing"):
            verify_sums(sums)

    def test_rejects_traversal_absolute_duplicate_malformed_empty(self):
        h = "a" * 64
        for text in (f"{h}  ../x\n", f"{h}  /etc/passwd\n", f"{h}  x\n{h}  x\n", "nothex  x\n", "# only comment\n"):
            with self.subTest(text=text), self.assertRaises(ChecksumError):
                parse_sums(text)

    def test_cli_create_and_verify(self):
        sums = self.d / "SHA256SUMS"
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["sha256", "create", str(sums), str(self.d / "a.img")]), 0)
            self.assertEqual(main(["sha256", "verify", str(sums)]), 0)
        (self.d / "a.img").write_bytes(b"changed")
        with redirect_stderr(io.StringIO()):
            self.assertEqual(main(["sha256", "verify", str(sums)]), 2)


if __name__ == "__main__":
    unittest.main()
