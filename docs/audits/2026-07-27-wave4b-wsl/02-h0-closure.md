# H0 closure review — NO-GO

No H0 item is closed.  All items below are current static observations, not test or hardware claims.

1. **P0 / latest Offboard production safety chain absent.** Current `origin/DDS@cded...` has direct `/fmu/in` writers in `src/node.cpp:28-35`; its FSM directly publishes setpoint/mode (`src/lib/CtrlFSM.cpp:339-340`) and `VehicleCommand` (`:405-417`). There is no `VehicleCommandAck` subscription/correlation, fresh status/timesync/lease/epoch/owner/kill gate, or required WAIT→PRESTREAM→REQUEST_MODE→REQUEST_ARM→ACTIVE lattice. `TEXT_RC` is unconditional (`CMakeLists.txt:33-35`) and `enable_arm` defaults true (`config/ctrl_param.yaml:12-16`).
2. **P0 / serial second execution path is quarantined only for discovery.** Latest serial plus `9d8c078...` has `COLCON_IGNORE`, and a local `colcon list` proved zero discovery.  Its `serial_main.cpp:13-35` still subscribes `/cmd_vel`; `serial_driver.cpp:6-12,26-32` opens the port in construction and writes frames. There is no runtime enable, owner/lease, bounded watchdog, physical interlock, finite/range control, or fault/exit zero-output proof.
4. **P1 / governance and lock failure.** Root gitlink mapping is broken; serial/communication have no unique immutable receipt. Offboard `976d...`, PX4 source/submodules/toolchain/board/RC profile do not form a recoverable approved lock.
5. **P1 / vision is active by code, not demonstrably disabled.** `vision_to_dds.cpp:79-84` creates `/fmu/in/vehicle_visual_odometry`; `:262-345` can publish with no frame/time/epoch/quality/device-health fail-closed gate. It has no test seam or unit suite.

Required next evidence: source changes and tests on latest Offboard `DDS`; written serial disposition; repaired `.gitmodules`/lock/receipt; then a fresh full-workspace candidate and tests.
