# Agent guard post-reboot evidence

Time: 2026-07-30T02:37:30+08:00

The Jetson reboot restored the production memory and DMA guard margins. The
previous verified Agent binary was under `/tmp` and was removed by the reboot.
It was rebuilt offline from clean source
`57d086216d01ec43121845d385894a25987f8a2c` using the same locked Release,
system-dependency, single-job configuration recorded by G2.

The rebuilt binary reproduced SHA-256
`4cbc5038cb74391a8ecec3ed6cd94e588530cae937b5498d6796bf2c68433995`
exactly.

The guard was then run with explicit `ROS_DOMAIN_ID=0`, serial device
`/dev/ttyTHS0`, baud rate 921600, and `--check-only`. Result:

- MemAvailable: 2387044 KiB;
- DMA free-above-high: 1287120 KiB;
- exact Agent SHA: PASS;
- unique process/serial checks: PASS;
- overall guard: PASS.

The Agent was not started and `/dev/ttyTHS0` remained unowned. This is only a
preflight result; it is not RC mapping evidence and does not change G4.
