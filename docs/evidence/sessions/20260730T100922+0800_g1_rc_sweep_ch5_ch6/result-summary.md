# G1 RC sweep: CH5 / CH6

- Props: removed; no control node or `/fmu/in/*` writer was started.
- Agent: exactly one `/usr/local/bin/MicroXRCEAgent` on `/dev/ttyTHS0` at 921600 baud, ROS domain 0.
- Bag: 89.181 s, 13,248 messages: RC 4,140; battery 8,746; vehicle status 183; land detected 90; timesync 89.
- CH5 raw levels observed: `-1.0`, `0.0`, `+1.0`.
- CH6 raw levels observed: `-1.0`, `0.0`, `+1.0`.
- CH7 remained `+1.0` throughout; no arm switch actuation was requested or observed.
- CH8 remained `+1.0` throughout this scan.  The preceding passive baseline captured CH8 at `-1.0`; this must be resolved against the physical kill-switch marking before configuring the adapter, because the adapter interprets values at or above its kill threshold as an asserted kill.
- VehicleStatus: arming state DISARMED for all 183 samples; nav state MANUAL for all samples; failsafe false for all samples.
- VehicleLandDetected: `landed=true` and `at_rest=true` for all 90 samples.

Result: PASS for CH5/CH6 raw-range collection and no-unintended-arm verification.  G1 remains IN PROGRESS: the physical semantics of CH6 activation and CH8 kill must be confirmed before calibrated thresholds can replace fail-closed placeholders.
