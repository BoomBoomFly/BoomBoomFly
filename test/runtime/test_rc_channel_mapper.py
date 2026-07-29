import importlib.util
import pathlib
import tempfile
import types
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "Scripts/runtime/rc_channel_mapper.py"


def load_mapper():
    spec = importlib.util.spec_from_file_location("rc_channel_mapper", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def message(timestamp, channels=None, **overrides):
    fields = {
        "timestamp": timestamp,
        "timestamp_last_valid": timestamp,
        "channels": [0.0] * 18 if channels is None else channels,
        "channel_count": 18,
        "function": [-1] * 29,
        "rssi": 100,
        "signal_lost": False,
        "frame_drop_count": 0,
    }
    fields.update(overrides)
    return types.SimpleNamespace(**fields)


class RcChannelMapperTest(unittest.TestCase):
    def setUp(self):
        self.mapper = load_mapper()

    def test_valid_two_stage_capture_summarizes_all_channels(self):
        state = self.mapper.CaptureState(("safe", "active"))
        state.on_graph(1, {"/fmu/in/vehicle_command": 0})
        state.on_message(message(100), 0.0, "safe")
        channels = [0.0] * 18
        channels[7] = 1.0
        state.on_message(message(200, channels), 3.0, "active")
        result = state.summary()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(result["channels"]), 18)
        self.assertEqual(result["channels"][7]["span"], 1.0)
        self.assertEqual(
            result["channels"][7]["per_stage"]["active"]["median"], 1.0
        )

    def test_signal_loss_bad_count_and_timestamp_fail_closed(self):
        state = self.mapper.CaptureState(("safe",))
        state.on_graph(1, {})
        state.on_message(message(100), 0.0, "safe")
        state.on_message(
            message(100, channel_count=17, signal_lost=True), 0.1, "safe"
        )
        result = state.summary()
        self.assertIn("timestamp_nonincreasing", result["failures"])
        self.assertIn("channel_count_not_18", result["failures"])
        self.assertIn("rc_signal_lost", result["failures"])

    def test_graph_requires_one_rc_publisher_and_zero_input_writers(self):
        state = self.mapper.CaptureState(("safe",))
        state.on_graph(0, {"/fmu/in/vehicle_command": 1})
        state.on_message(message(100), 0.0, "safe")
        result = state.summary()
        self.assertIn("rc_publisher_count_not_one", result["failures"])
        self.assertIn("fmu_input_writer_detected", result["failures"])

    def test_invalid_channel_value_fails_closed(self):
        state = self.mapper.CaptureState(("safe",))
        state.on_graph(1, {})
        channels = [0.0] * 18
        channels[4] = float("nan")
        state.on_message(message(100, channels), 0.0, "safe")
        self.assertIn("invalid_channel_value", state.summary()["failures"])

    def test_outputs_are_hashed(self):
        state = self.mapper.CaptureState(("safe",))
        state.on_graph(1, {})
        state.on_message(message(100), 0.0, "safe")
        with tempfile.TemporaryDirectory(prefix="rc_mapper.") as directory:
            root = pathlib.Path(directory)
            result = self.mapper.write_capture(
                root / "raw.jsonl",
                root / "summary.json",
                state,
                {"switch_label": "test"},
            )
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(len(result["raw_sha256"]), 64)
            self.assertEqual(len(result["summary_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
