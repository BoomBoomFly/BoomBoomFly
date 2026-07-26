# BoomBoomFly toolchain baseline — 2026-07-26

Status: `PARTIALLY VERIFIED`

This baseline was collected read-only for `BBF-NEXT-T00`. It did not install
software, access a device, start ROS/PX4/Micro XRCE-DDS processes, write PX4
parameters, or touch firmware. The machine-readable record is
[`environment/current_environment.json`](environment/current_environment.json).

## Verified host baseline

| Component | Requirement | Result |
| --- | --- | --- |
| OS | DDS-only build | Ubuntu 20.04.6 LTS |
| Kernel / architecture | environment identity | 5.10.104-tegra / aarch64 |
| ROS | DDS-only build | Foxy; exact core/base/rclcpp/RMW Debian versions recorded |
| Python / Git / colcon-core | validation and restore | 3.8.10 / 2.25.1 / 0.21.0 |
| CMake / Ninja | build tooling | 3.16.3 / 1.11.1.git.kitware.jobserver-1 |
| GCC / G++ | DDS-only build | 9.4.0 / 9.4.0; aarch64-linux-gnu |
| arm-none-eabi-gcc / g++ | future T02 | `missing` / `missing` |
| MicroXRCEAgent | future T02 | `missing` from PATH and package probe |
| managed PX4 source | future T02 | `missing` |
| PX4 recursive submodules | future T02 | `unverified` because source is missing |

MicroXRCEAgent was never executed. Its probe is limited to executable path and
package provenance. The managed PX4 result covers explicit repository candidates;
a bounded host search encountered an unreadable `/opt` path, so a whole-host
absence claim remains `unverified`.

## Machine-verifiable boundary

Run from any directory:

```bash
python3 /path/to/BoomBoomFly/Scripts/installation/verify_environment.py
```

Use `--check-current` to compare safe read-only probes with the checked-in
inventory. Capture requires explicit output and should target an isolated path:

```bash
python3 Scripts/installation/verify_environment.py \
  --capture \
  --output /tmp/boomboomfly_environment.json
```

The verifier returns 0 only for a valid inventory/placeholder and a successful
requested comparison. Schema or comparison failures return 1; argument/I/O errors
return 2; internal subprocess failures return 3. It rejects a moving `latest`
version and contradictory `present`, `missing`, or `unverified` records.

## T02 lock placeholder and blockers

[`environment/px4_source_toolchain_lock.template.json`](environment/px4_source_toolchain_lock.template.json)
is intentionally `template=true` and `status=unverified`. It cannot be treated as
a locked/current dependency record. T02 remains blocked on:

1. an approved PX4 source origin and exact commit;
2. the full recursive submodule origin/SHA set;
3. exact ARM cross-compiler versions;
4. an immutable environment/container identity;
5. two isolated builds with explained artifact hash results.

The current file is a host inventory, not an apt snapshot, rosdep resolution lock,
or reproducible PX4 build receipt.
