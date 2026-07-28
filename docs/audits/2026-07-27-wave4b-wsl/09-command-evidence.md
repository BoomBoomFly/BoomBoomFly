# Command evidence and safety boundary

## Gate commands

| Command / evidence root | Exit | Result |
|---|---:|---|
| `verify_h0_production.py` | 0 | sole Offboard writer; arm false; no TEXT_RC; vision false; serial false |
| `verify_serial_quarantine.py` | 0 | exact clean serial source; discovery/package/launch refs 0 |
| package boundary `...-08` | 0 | exactly 3 production packages |
| `test_dds_only.sh`, output `...h1-20260728-08` | 0 | build/test/test-result PASS |
| H2 Offboard/RC/contract/vision binaries | 0 | PASS; RC 7/7, contract 1/1, vision 4/4 |
| H2 serial quarantine unittest | 0 | 6/6 PASS |
| H3 precursor `...-01` | 1 | test-spy property error before any production-node start |
| H3 final `...-02`, domain 217 | 0 | PASS, output count 0, clean restart/exit |
| final H3 forbidden-process inventory | 0 | count 0 |
| exact remote recovery fetch/API reads | 0 | every listed root/nested SHA recovered |

H1 attempt ledger:

| Attempt | Exit | Disposition |
|---|---:|---|
| 01 | 130 | interrupted verbose CTest pipe hang; direct diagnostic tests passed but not a receipt |
| 02 | 130 | same infrastructure failure |
| 03 | 2 | transient px4_msgs generator SIGSEGV |
| 04 | 130 | Foxy sequential executor hang before build |
| 05 | 1 | exposed Offboard home log plus obsolete vision template lint failures |
| 06 | 1 | all remaining tests except sandbox-denied `getifaddrs` passed |
| 07 | 0 | successful parent-source confirmation; superseded |
| 08 | 0 | final source candidate formal PASS |

The final receipt uses one package worker and CMake build concurrency one.
CTest quiet console mode avoids the Foxy async-line deadlock while retaining
xUnit and `LastTest.log`. The rclcpp tests and H3 ran outside the Codex
filesystem/network sandbox solely to permit local interface enumeration;
`ROS_LOCALHOST_ONLY=1` was used for H3.

## Commands explicitly not run

- no `/dev/tty*` open or probe;
- no PX4, MicroXRCEAgent, MAVROS, QGC, serial, camera, or lidar process;
- no real `/fmu/in/*` graph;
- no arm, mode, takeoff/land, actuator, or motor command;
- no parameter write or firmware flash;
- no package install/uninstall, udev/network/group/permission change;
- no reset, clean, restore, forced push, merge, or rebase;
- no formal SITL.

All build/test/log output is under unique `/tmp` paths. The original dirty
workspace remained untouched. Failed attempts are preserved as negative
evidence and were not relabeled successful.

```text
HARDWARE_ACCESSED: NO
REAL_FMU_GRAPH_USED: false
FORMAL_SITL_RUN: false
```
