import importlib.util
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "Scripts/runtime/px4_post_sdlog_capture.py"


def load_capture():
    spec = importlib.util.spec_from_file_location(
        "px4_post_sdlog_capture", SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Px4PostSdlogCaptureTest(unittest.TestCase):
    def setUp(self):
        self.capture = load_capture()

    def test_select_recent_ulogs_is_exact_and_sorted(self):
        files = [
            {"path": "/log/2026-07-29/23_00.ulg", "size_bytes": 100},
            {"path": "/log/2026-07-30/00_01.ulg", "size_bytes": 200},
            {"path": "/log/2026-07-30/00_13.ulg", "size_bytes": 300},
            {"path": "/log/2026-07-30/notes.txt", "size_bytes": 10},
        ]
        self.assertEqual(
            self.capture.select_recent_ulogs(files, 2),
            files[1:3],
        )

    def test_select_recent_ulogs_rejects_missing_files(self):
        with self.assertRaisesRegex(
            self.capture.CaptureError, "requested 2 recent ULogs"
        ):
            self.capture.select_recent_ulogs(
                [{"path": "/log/a.ulg", "size_bytes": 1}], 2
            )

    def test_download_rejects_non_ulog_magic(self):
        class FakeFtp:
            @staticmethod
            def read(path, size):
                return b"x" * size

        class FakeMavftpModule:
            @staticmethod
            def MAVFTP(connection, target_system, target_component):
                return FakeFtp()

        with tempfile.TemporaryDirectory(prefix="px4_ulog_capture.") as temp:
            with self.assertRaisesRegex(
                self.capture.CaptureError, "lacks ULog magic"
            ):
                self.capture.download_ulogs(
                    object(),
                    FakeMavftpModule(),
                    [{"path": "/log/a.ulg", "size_bytes": 16}],
                    temp,
                )


if __name__ == "__main__":
    unittest.main()
