# H3 node integration disposition

```text
H3: NOT-RUN
REAL_FMU_GRAPH_USED: false
HARDWARE_ACCESSED: NO
```

No ROS processes were launched. No fake transport, publisher spy, isolated `ROS_DOMAIN_ID`, test-only launch, process-cleanup evidence, or bounded integration run currently exists for this candidate.

The available production launch is unsafe as a test entrypoint: `src/offboard_cpp/launch/offboard_control.launch.py:38-49` directly launches the production control node; its source writes real `/fmu/in/*` topics. Vision also directly creates its FMU input publisher. H3 remains prohibited until exact-source H0/H1/H2 GO evidence exists and a test-only graph remaps every output away from `/fmu/in/*`, forbids Agent/MAVROS/PX4/serial/camera/lidar, proves a unique writer, and captures cleanup.
