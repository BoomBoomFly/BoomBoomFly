# H0 closure review — NO-GO

No H0 item is closed.  All items below are current static observations, not test or hardware claims.

1. **P0 / Offboard identity unavailable.** Required `976d...` cannot be checked out locally. The actual `cded...` source has direct `/fmu/in` writers in `src/node.cpp:28-35`; its FSM directly publishes setpoint/mode (`src/lib/CtrlFSM.cpp:339-340`) and `VehicleCommand` (`:405-417`). No exact candidate means no valid production-fix claim.
2. **P0 / production safety chain absent in the available non-candidate.** There is no `VehicleCommandAck` subscription/correlation, fresh status/timesync/lease/epoch/owner/kill gate, or required WAIT→PRESTREAM→REQUEST_MODE→REQUEST_ARM→ACTIVE lattice. `TEXT_RC` is unconditional (`CMakeLists.txt:33-35`) and `enable_arm` defaults true (`config/ctrl_param.yaml:12-16`). This observation cannot be used to certify `976d...`.
3. **P0 / serial second execution path and non-canonical source.** `serial_main.cpp:13-35` subscribes `/cmd_vel`; `serial_driver.cpp:6-12,26-32` opens the port in construction and writes frames. There is no enable, owner/lease, bounded watchdog, physical interlock, finite/range control, or fault/exit zero-output proof. `COLCON_IGNORE` is absent, so discovery=0 and quarantine=effective are not proven.
4. **P1 / governance and lock failure.** Root gitlink mapping is broken; serial/communication have no unique immutable receipt. Offboard `976d...`, PX4 source/submodules/toolchain/board/RC profile do not form a recoverable approved lock.
5. **P1 / vision is active by code, not demonstrably disabled.** `vision_to_dds.cpp:79-84` creates `/fmu/in/vehicle_visual_odometry`; `:262-345` can publish with no frame/time/epoch/quality/device-health fail-closed gate. It has no test seam or unit suite.

Required next evidence: maintainer-provided immutable Offboard `976d...` source bundle/receipt; written serial disposition; repaired `.gitmodules`/lock/receipt; then source changes and tests on one exact candidate.
