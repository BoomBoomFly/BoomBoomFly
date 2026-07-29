import importlib.util
import pathlib
import types
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "Scripts/runtime/g4_a2_rc_agent_loss_probe.py"


def load_probe():
    spec = importlib.util.spec_from_file_location("g4_a2_probe", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def message(timestamp, **fields):
    return types.SimpleNamespace(timestamp=timestamp, **fields)


class G4A2ProbeTest(unittest.TestCase):
    def setUp(self):
        self.probe = load_probe()

    def seed_common(self, state):
        state.on_status(
            message(100, arming_state=1, nav_state=0, failsafe=False), 0.0
        )
        state.on_land(message(100, landed=True), 0.0)
        state.on_timesync(message(100))
        state.on_graph(
            0.0,
            {topic: 1 for topic in self.probe.OUTPUT_TOPICS},
            {"/fmu/in/vehicle_command": 0},
        )

    def test_complete_disarmed_loss_recovery_and_agent_exit_passes(self):
        state = self.probe.ProbeState()
        self.seed_common(state)
        state.on_rc(message(100, signal_lost=False), 0.0)
        state.on_failsafe(message(100, manual_control_signal_lost=False), 0.0)
        state.on_rc(message(200, signal_lost=True), 1.0)
        state.on_failsafe(message(200, manual_control_signal_lost=True), 1.0)
        state.on_rc(message(300, signal_lost=False), 2.0)
        state.on_failsafe(message(300, manual_control_signal_lost=False), 2.0)
        state.on_status(
            message(200, arming_state=1, nav_state=0, failsafe=False), 2.0
        )
        state.on_land(message(200, landed=True), 2.0)
        state.on_timesync(message(200))
        state.on_graph(
            3.0,
            {topic: 0 for topic in self.probe.OUTPUT_TOPICS},
            {"/fmu/in/vehicle_command": 0},
        )

        result = state.result(4.0)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["failures"], [])
        self.assertEqual(result["action"], "COMPLETE")

    def test_armed_or_input_writer_fails_closed(self):
        state = self.probe.ProbeState()
        self.seed_common(state)
        state.on_status(
            message(200, arming_state=2, nav_state=0, failsafe=False), 1.0
        )
        state.on_graph(
            1.0,
            {topic: 0 for topic in self.probe.OUTPUT_TOPICS},
            {"/fmu/in/vehicle_command": 1},
        )
        result = state.result(2.0)
        self.assertIn("vehicle_not_always_disarmed", result["failures"])
        self.assertIn("fmu_input_writer_detected", result["failures"])

    def test_missing_loss_and_timestamp_regression_fail_closed(self):
        state = self.probe.ProbeState()
        self.seed_common(state)
        state.on_rc(message(200, signal_lost=False), 0.0)
        state.on_rc(message(199, signal_lost=False), 1.0)
        state.on_failsafe(message(200, manual_control_signal_lost=False), 0.0)
        result = state.result(2.0)
        self.assertIn("rc_signal_lost_not_observed", result["failures"])
        self.assertIn("rc_timestamp_nonincreasing", result["failures"])

    def test_action_sequence_is_explicit(self):
        state = self.probe.ProbeState()
        self.assertEqual(state.action(), "WAIT_BASELINE")
        self.seed_common(state)
        state.on_rc(message(100, signal_lost=False), 0.0)
        self.assertEqual(state.action(), "TURN_RC_OFF")
        state.on_rc(message(200, signal_lost=True), 1.0)
        self.assertEqual(state.action(), "WAIT_PX4_MANUAL_LOSS")
        state.on_failsafe(message(200, manual_control_signal_lost=True), 1.0)
        self.assertEqual(state.action(), "TURN_RC_ON")
        state.on_rc(message(300, signal_lost=False), 2.0)
        self.assertEqual(state.action(), "READY_FOR_AGENT_EXIT")


if __name__ == "__main__":
    unittest.main()
