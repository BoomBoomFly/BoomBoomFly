import importlib.util
import math
import pathlib
import struct
import types
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "Scripts/runtime/px4_param_snapshot.py"


def load_snapshot():
    spec = importlib.util.spec_from_file_location("px4_param_snapshot", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def raw_float(format_string, value):
    encoded = struct.pack(format_string, value)
    return struct.unpack("<f", encoded.ljust(4, b"\0"))[0]


class Px4ParamSnapshotTest(unittest.TestCase):
    def setUp(self):
        self.snapshot = load_snapshot()

    def test_int32_minus_one_nan_bit_pattern_decodes(self):
        raw = raw_float("<i", -1)
        self.assertTrue(math.isnan(raw))
        self.assertEqual(
            self.snapshot.decode_param_value(
                raw, self.snapshot.MAV_PARAM_TYPE_INT32
            ),
            -1,
        )

    def test_integer_types_use_bytewise_encoding(self):
        cases = (
            ("<B", 255, self.snapshot.MAV_PARAM_TYPE_UINT8),
            ("<b", -12, self.snapshot.MAV_PARAM_TYPE_INT8),
            ("<H", 65530, self.snapshot.MAV_PARAM_TYPE_UINT16),
            ("<h", -32000, self.snapshot.MAV_PARAM_TYPE_INT16),
            ("<I", 0xF1234567, self.snapshot.MAV_PARAM_TYPE_UINT32),
            ("<i", -1234567, self.snapshot.MAV_PARAM_TYPE_INT32),
        )
        for format_string, value, param_type in cases:
            with self.subTest(param_type=param_type):
                self.assertEqual(
                    self.snapshot.decode_param_value(
                        raw_float(format_string, value), param_type
                    ),
                    value,
                )

    def test_real32_requires_finite_value(self):
        self.assertAlmostEqual(
            self.snapshot.decode_param_value(
                1.25, self.snapshot.MAV_PARAM_TYPE_REAL32
            ),
            1.25,
        )
        with self.assertRaisesRegex(self.snapshot.SnapshotError, "non-finite"):
            self.snapshot.decode_param_value(
                float("nan"), self.snapshot.MAV_PARAM_TYPE_REAL32
            )

    def test_unsupported_and_64_bit_types_fail_closed(self):
        with self.assertRaisesRegex(self.snapshot.SnapshotError, "64-bit"):
            self.snapshot.decode_param_value(
                0.0, self.snapshot.MAV_PARAM_TYPE_UINT64
            )
        with self.assertRaisesRegex(self.snapshot.SnapshotError, "unsupported"):
            self.snapshot.decode_param_value(0.0, 99)

    def test_param_name_accepts_bytes_and_text(self):
        self.assertEqual(
            self.snapshot.param_name(types.SimpleNamespace(param_id=b"TEST\0")),
            "TEST",
        )
        self.assertEqual(
            self.snapshot.param_name(types.SimpleNamespace(param_id="TEST\0")),
            "TEST",
        )


if __name__ == "__main__":
    unittest.main()
