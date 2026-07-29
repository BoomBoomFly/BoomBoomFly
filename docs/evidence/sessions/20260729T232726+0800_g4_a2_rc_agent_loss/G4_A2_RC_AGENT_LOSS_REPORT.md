# G4-A2 real RC loss and Agent exit report

Date: 2026-07-29 (Asia/Shanghai)

## Authorization and safety boundary

The user continued the explicitly proposed G4-A2 group: real RC loss/recovery
and Agent exit. All propellers remained removed, the vehicle remained fixed,
and ESC propulsion power remained isolated. This session did not publish any
`/fmu/in/*` topic, write a parameter, send `VehicleCommand`, Arm, Kill, change
mode, or start a motor.

## Clean-boot preflight

- Boot ID: `0b6ed0dd-0802-4601-a3f4-10d0bcdfcb0b`.
- Boot start: `2026-07-29 23:25:34`.
- Agent SHA-256:
  `4cbc5038cb74391a8ecec3ed6cd94e588530cae937b5498d6796bf2c68433995`.
- The binary was restored from the previously archived runtime bundle whose
  SHA-256 is
  `5294b364f5574fa4a985e024bea8e4aac107fddf55d4942a17868930798e2d55`.
- Guard preflight: PASS, MemAvailable 2,404,892 KiB and DMA free-above-high
  1,544,000 KiB.
- `/dev/ttyTHS0` was initially unowned; the guarded Agent became its only owner.
- All five observed PX4 output topics had exactly one publisher. All 27
  `/fmu/in/*` topics had zero publishers.

## RC loss and recovery: PASS for the disarmed ground condition

The read-only probe ran for 104.002 seconds and recorded:

| Event | Probe elapsed time |
|---|---:|
| RC online baseline | 0.017 s |
| `RcChannels.signal_lost`: false to true | 19.245 s |
| `FailsafeFlags.manual_control_signal_lost`: false to true | 19.712 s |
| `RcChannels.signal_lost`: true to false | 49.013 s |
| `FailsafeFlags.manual_control_signal_lost`: true to false | 49.097 s |

Actual PX4 state throughout the observable RC-loss window:

- `VehicleStatus.arming_state=1` (DISARMED) only.
- `VehicleStatus.nav_state=2` (POSCTL) only.
- `VehicleStatus.failsafe=false` only.
- `VehicleLandDetected.landed=true` only.
- 3,479 RC, 151 failsafe, 159 vehicle-status, 79 land-detector, and 78
  timesync samples.
- Non-increasing PX4 timestamps: zero for all five streams.
- 104 graph samples checked every discovered `/fmu/in/*` topic; writer
  violations: zero.

The observed ground/disarmed response was therefore RC-loss flags without a
mode change, vehicle failsafe, or Land transition. This is an observation, not
an inference from parameters.

## Agent exit and recovery

The only Agent was terminated with Ctrl-C after RC recovery. PX4 output samples
stopped, then all five observed DDS publishers disappeared after the Fast DDS
discovery lease expired at probe time 98.977 seconds. The probe observed five
additional seconds with every output publisher at zero and no input writer.

The same guarded Agent was then restarted read-only. Direct recovery samples
showed:

- `arming_state=1`, `nav_state=2`, `failsafe=false`;
- `landed=true`, `at_rest=true`;
- RC `signal_lost=false`, 18 channels;
- `manual_control_signal_lost=false`;
- `offboard_control_signal_lost=true`, as expected with no Offboard stream,
  without a vehicle failsafe transition.

The recovery Agent was stopped. After DDS lease cleanup, Domain 0 contained
only `/parameter_events` and `/rosout`; Agent and serial owners were zero. This
boot had zero matched page-allocation, Tegra UART RX DMA, or descriptor errors.

## Important limitation

Agent exit removes the same telemetry path needed to observe PX4 during the
gap. Current persisted logging parameters are `SDLOG_MODE=0` and
`SDLOG_BOOT_BAT=0`; because this test never Armed, no flight ULog was available
to establish the internal mode/failsafe/Land state during that gap.

Therefore:

- Agent DDS data-plane exit and recovery: PASS.
- PX4 state before exit and after reconnect: directly observed and unchanged.
- PX4 internal state during the telemetry gap: BLOCKED / not evidenced.

The gap must not be described as a verified failsafe/Land response. A future
logging strategy or independently observable transport requires separate
review and authorization; no parameter was changed in this session.

## Software verification and gate effect

The new probe has four fail-closed tests for sequencing, timestamp regression,
Armed state, and input writer detection. All runtime tests passed: 24 tests, 0
failures, 0 errors. G4 RC-loss ground/disarmed evidence is PASS. G4 overall
remains BLOCKED, and G5 remains PROHIBITED. This report is not authorization to
install propellers, Arm, or fly.
