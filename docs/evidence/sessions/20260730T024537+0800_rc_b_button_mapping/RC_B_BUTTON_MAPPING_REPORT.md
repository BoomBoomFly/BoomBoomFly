# RC B Button / Channel 8 Read-only Mapping

Recorded: 2026-07-30T02:45:37+08:00 through 2026-07-30T02:51:28+08:00

## Safety envelope

- Propellers removed.
- Vehicle physically fixed.
- ESC propulsion power isolated.
- Independent hard power cutoff available.
- Vehicle remained disarmed and landed.
- No `/fmu/in/*` publisher was present.
- No Arm, Disarm, Land, Kill, Offboard, parameter write, firmware write, or motor command was issued by the workstation.

## Physical control and observed values

The operator identified the physical control as the `B` push button and identified it as RC channel 8 (one-based), which is `channels[7]` in the DDS `RcChannels` array.

| Recorded state | Frames | Channel 8 min | median | max | span |
|---|---:|---:|---:|---:|---:|
| Operator-described confirmation state | 222 | 0.9999998808 | 0.9999998808 | 0.9999998808 | 0.0 |
| After one operator-performed switch | 222 | -1.0 | -1.0 | -1.0 | 0.0 |

Only channel 8 is attributed to this action. The other channel values are retained in the raw evidence but are not assigned to physical controls by this session.

## PX4 interpretation

The most recent cold-boot parameter evidence is:

`../20260729T234922+0800_g4_agent_gap_ulog/artifacts/parameters-final-cold-boot-retry.json`

- `RC_MAP_KILL_SW=8`
- `RC_KILLSWITCH_TH=0.75`
- `RC_MAP_OFFB_SW=6`
- `COM_KILL_DISARM=5.0`

PX4 source at commit `a8f2dbdfff4792c92f576060ab947f8e588d6f8b` rescales an RC channel from `[-1, 1]` to `[0, 1]` and reports the switch ON when the rescaled value is greater than the threshold (`src/modules/rc_update/rc_update.cpp`, lines 532-541). `ManualControl` requests `ACTION_KILL` for a transition to ON and `ACTION_UNKILL` for a transition to OFF (`src/modules/manual_control/ManualControl.cpp`, lines 232-236).

Therefore, with the recorded parameters:

- Channel 8 `+1.0` maps to PX4 kill switch ON.
- Channel 8 `-1.0` maps to PX4 kill switch OFF.

The post-switch state is consistent with a transition from Kill ON to Kill OFF. The DDS output set did not provide an independent `manual_control_switches` or command-ACK observation, so this session does not claim direct observation of `ACTION_UNKILL`.

## Post-switch read-only status

The four-second post-switch probe observed:

- `arming_states=[1]` (Disarmed)
- `landed_values=[true]`
- `failsafe_values=[false]`
- `rc_signal_lost=false`
- `manual_control_signal_lost=false`
- all enumerated `/fmu/in/*` publisher counts equal to zero

The probe's overall status is `FAIL` only because the G4 RC/Agent-loss probe expects fault injection and recovery events that were intentionally not performed in this mapping session. Its baseline safety observations are valid; this result is not a G4 PASS.

## Configuration conclusion

- RC channel 8 is conclusively mapped to the B button with stable endpoints `-1.0` and `+1.0`.
- The installed PX4 parameter set already assigns channel 8 as the PX4 kill switch.
- A push button is not recommended as the production kill control unless it is physically guarded, latching, has an unambiguous persistent indication, and the operator explicitly accepts its semantics.
- The application production YAML must remain fail-closed (`kill_channel: -1`) until the physical-control suitability decision is confirmed.
- This ground, disarmed mapping is not G4 kill evidence and does not permit propeller installation or flight.

Current gate remains **NO-GO**; G4 remains incomplete and G5 remains prohibited.
