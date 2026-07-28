# H3 no-hardware node integration — GO

Successful evidence:
`/tmp/boomboomfly-wave4b-h3-20260728-02/h3-result.json`.

The bounded harness used `ROS_DOMAIN_ID=217` and
`ROS_LOCALHOST_ONLY=1`. It did not start PX4, MicroXRCEAgent, MAVROS, serial,
camera, lidar, or a production launch. Every apparent FMU input was remapped
to `/wave4b_h3/fmu/in/*`; the harness failed if any real `/fmu/in/*` topic
appeared.

Results:

- disabled production vision node: clean exit, estimator publisher count 0,
  message count 0;
- Offboard run 1: exactly one publisher on each of the three remapped control
  outputs; no-input, incomplete/stale input, and kill-latched message count 0;
- clean SIGINT and post-exit publisher count 0;
- Offboard run 2 repeated the same inventory and zero-output checks, proving
  restart does not auto-resume;
- final forbidden process count 0.

The one failed precursor
`/tmp/boomboomfly-wave4b-h3-20260728-01` stopped while constructing the test
spy because Foxy exposes `Node.subscriptions` as read-only. No production node
started in that attempt. The private-list compatibility fix is part of tested
root source `1ea582b8…`.

```text
H3: GO
HARDWARE_ACCESSED: NO
REAL_FMU_GRAPH_USED: false
FORMAL_SITL_RUN: false
```
