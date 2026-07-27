# H4 formal SITL disposition

```text
H4: NOT-RUN
FORMAL_SITL_RUN: false
HARDWARE_ACCESSED: NO
```

No command card was generated for approval and no SITL, PX4, MicroXRCEAgent, or MAVROS process was started. The exact production source is not recoverable, H0 is NO-GO, H1/H2 are not satisfied, and PX4's lock/toolchain/board/RC profile remains ungoverned. Any existing synthetic/offline scenario output is expressly not formal SITL evidence.

Before a formal run can even be requested, provide one immutable candidate ledger for root, Offboard, PX4, px4_msgs, Agent, parameters, world, model, ROS domain/ports, and profile. Then submit an exact bounded command card for user approval; verify no USB/serial/hardware passthrough before execution.

