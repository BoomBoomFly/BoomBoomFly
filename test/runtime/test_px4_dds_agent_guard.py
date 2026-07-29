import hashlib
import importlib.util
import os
import pathlib
import tempfile
import types
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "Scripts/runtime/px4_dds_agent_guard.py"


def load_guard():
    spec = importlib.util.spec_from_file_location("px4_dds_agent_guard", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Px4DdsAgentGuardTest(unittest.TestCase):
    def setUp(self):
        self.guard = load_guard()
        self.temp = tempfile.TemporaryDirectory(prefix="px4_dds_guard_test.")
        self.root = pathlib.Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_memory_and_dma_parsing(self):
        meminfo = self.root / "meminfo"
        zoneinfo = self.root / "zoneinfo"
        meminfo.write_text("MemAvailable: 1572864 kB\n", encoding="utf-8")
        zoneinfo.write_text(
            "Node 0, zone DMA\n"
            "  pages free 100000\n"
            "        min 6000\n"
            "        low 7500\n"
            "        high 9000\n"
            "Node 0, zone Normal\n",
            encoding="utf-8",
        )
        self.assertEqual(self.guard.read_mem_available_kib(meminfo), 1572864)
        values = self.guard.read_zone_watermarks(zoneinfo)
        self.assertEqual(self.guard.dma_headroom_kib(values, 4096), 364000)

    def test_missing_or_low_watermarks_fail_closed(self):
        missing = self.root / "missing"
        missing.write_text("MemTotal: 10 kB\n", encoding="utf-8")
        with self.assertRaises(self.guard.GuardError):
            self.guard.read_mem_available_kib(missing)
        zone = self.root / "zone"
        zone.write_text("Node 0, zone DMA\n  pages free 1\n", encoding="utf-8")
        with self.assertRaises(self.guard.GuardError):
            self.guard.read_zone_watermarks(zone)

    def test_development_processes_are_detected(self):
        for pid, command in (("101", b"pylance\0--stdio\0"),
                             ("102", b"cpptools\0"),
                             ("103", b"safe_process\0")):
            process = self.root / pid
            process.mkdir()
            (process / "cmdline").write_bytes(command)
        matches = self.guard.development_processes(self.root, own_pid=999)
        self.assertEqual([pid for pid, _ in matches], [101, 102])

    def test_serial_owner_is_detected(self):
        process = self.root / "201"
        descriptors = process / "fd"
        descriptors.mkdir(parents=True)
        (process / "cmdline").write_bytes(b"MicroXRCEAgent\0serial\0")
        (descriptors / "3").symlink_to("/dev/null")
        owners = self.guard.serial_owners("/dev/null", self.root, own_pid=999)
        self.assertEqual([pid for pid, _ in owners], [201])

    def test_agent_requires_absolute_path_and_exact_sha(self):
        agent = self.root / "MicroXRCEAgent"
        agent.write_bytes(b"agent-test-binary")
        agent.chmod(0o755)
        digest = hashlib.sha256(agent.read_bytes()).hexdigest()
        self.assertEqual(self.guard.validate_agent(str(agent), digest), digest)
        with self.assertRaises(self.guard.GuardError):
            self.guard.validate_agent("MicroXRCEAgent", digest)
        with self.assertRaises(self.guard.GuardError):
            self.guard.validate_agent(str(agent), "0" * 64)

    def test_preflight_rejects_low_memory_before_launch(self):
        agent = self.root / "agent"
        agent.write_bytes(b"agent")
        agent.chmod(0o755)
        digest = hashlib.sha256(agent.read_bytes()).hexdigest()
        meminfo = self.root / "meminfo"
        zoneinfo = self.root / "zoneinfo"
        proc_root = self.root / "proc"
        serial_dev = self.root / "serial"
        meminfo.write_text("MemAvailable: 1000 kB\n", encoding="utf-8")
        zoneinfo.write_text(
            "Node 0, zone DMA\n  pages free 100000\n"
            "        min 1\n        low 2\n        high 3\n",
            encoding="utf-8",
        )
        proc_root.mkdir()
        serial_dev.write_bytes(b"")
        args = types.SimpleNamespace(
            agent=str(agent),
            agent_sha256=digest,
            baudrate=921600,
            meminfo=str(meminfo),
            zoneinfo=str(zoneinfo),
            min_mem_available_mib=1024,
            min_dma_headroom_mib=256,
            proc_root=str(proc_root),
            serial_dev=str(serial_dev),
        )
        old_domain = os.environ.get("ROS_DOMAIN_ID")
        os.environ["ROS_DOMAIN_ID"] = "0"
        try:
            with self.assertRaisesRegex(self.guard.GuardError, "MemAvailable"):
                self.guard.preflight(args)
        finally:
            if old_domain is None:
                os.environ.pop("ROS_DOMAIN_ID", None)
            else:
                os.environ["ROS_DOMAIN_ID"] = old_domain

    def test_preflight_requires_explicit_domain_zero(self):
        args = types.SimpleNamespace(agent="unused", agent_sha256="0" * 64)
        old_domain = os.environ.pop("ROS_DOMAIN_ID", None)
        try:
            with self.assertRaisesRegex(self.guard.GuardError, "ROS_DOMAIN_ID=0"):
                self.guard.preflight(args)
        finally:
            if old_domain is not None:
                os.environ["ROS_DOMAIN_ID"] = old_domain


if __name__ == "__main__":
    unittest.main()
