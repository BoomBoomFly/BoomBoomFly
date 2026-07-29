import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "Scripts/runtime/px4_mavftp_get_ulog.py"


def load_downloader():
    spec = importlib.util.spec_from_file_location(
        "px4_mavftp_get_ulog", SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Px4MavftpGetUlogTest(unittest.TestCase):
    def setUp(self):
        self.downloader = load_downloader()

    def test_exact_size_and_magic_pass(self):
        content = self.downloader.ULOG_MAGIC + b"x" * 32
        self.downloader.validate_content("/fs/microsd/log/a.ulg", len(content), content)

    def test_missing_size_or_magic_fails_closed(self):
        with self.assertRaisesRegex(
            self.downloader.DownloadError, "returned no data"
        ):
            self.downloader.validate_content(
                "/fs/microsd/log/a.ulg", 10, None
            )
        with self.assertRaisesRegex(
            self.downloader.DownloadError, "size mismatch"
        ):
            self.downloader.validate_content(
                "/fs/microsd/log/a.ulg", 10, b"x"
            )
        with self.assertRaisesRegex(
            self.downloader.DownloadError, "lacks ULog magic"
        ):
            self.downloader.validate_content(
                "/fs/microsd/log/a.ulg", 10, b"x" * 10
            )


if __name__ == "__main__":
    unittest.main()
