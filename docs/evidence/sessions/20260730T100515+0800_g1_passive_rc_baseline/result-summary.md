# G1 passive RC baseline

- Props: removed; vehicle remained disarmed; no control node or `/fmu/in/*` writer was started.
- Agent: exactly one `/usr/local/bin/MicroXRCEAgent` on `/dev/ttyTHS0` at 921600 baud, ROS domain 0.
- Bag: 14.165 s, 3,543 messages: RC 662; odometry 1,411; battery 1,411; vehicle status 29; land detected 15; timesync 15.
- Current raw RC values: CH5 = -1.0, CH6 = 0.0, CH7 = +1.0, CH8 = -1.0.  These are baseline values only, not yet a switch-range or semantic validation.
- Vehicle status: disarmed, NAVIGATION_STATE_STAB (15), no failsafe; preflight checks passed.
- Landing detector: `landed=true`, `at_rest=true`.
- Battery: connected, 15.614 V, 54.15% remaining, warning none.
- Timesync: DDS source, 7,439 us round-trip time.

Result: PASS for passive-link collection only.  G1 remains IN PROGRESS until controlled RC sweep, T265/vision validation, and prescribed fault-injection evidence are complete.
