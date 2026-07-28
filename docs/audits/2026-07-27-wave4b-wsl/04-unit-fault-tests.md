# H2 unit and fault-test disposition

```text
H2: NO-GO
TESTS EXECUTED IN THIS WSL WAVE: 0
```

The required complete matrix was not run, because the exact Offboard candidate is unavailable and H0 is NO-GO. Historical partial standalone/static tests are not reused.

Missing current-candidate evidence includes ACK accepted/reject/timeout/mismatch; no/stale/lost RC; kill latch; duplicate writer; owner/lease loss; DDS/PX4/Agent/node restart; stale setpoint; clock jump; serial odd/short/partial/reordered/CRC/disconnect/reconnect; vision reset/dropout/NaN/Inf; and process exit/resource release. Each failed-path test must establish all control-writer counts are zero.

Serial additionally has a known protocol conflict: ROS uses additive checksum without a tail (`protocol_defs.hpp:9-18`) while STM32 requires CRC16 plus tail (`Serial_32/include/serial.h:20-40`); the ROS parser accesses `j+1` without prior odd-length rejection (`serial_driver.cpp:93-95`).
