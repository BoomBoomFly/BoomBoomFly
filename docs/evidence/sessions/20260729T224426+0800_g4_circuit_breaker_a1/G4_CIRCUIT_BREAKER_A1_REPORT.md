# G4 circuit-breaker A1 controlled parameter transaction

Date: 2026-07-29 (Asia/Shanghai)

## Scope and safety boundary

The user approved exactly one parameter risk group with all propellers removed,
the vehicle fixed in place, and ESC propulsion power isolated. The transaction
did not send `VehicleCommand`, Arm, motor, or flight-mode commands.

Approved changes:

| Parameter | Before | After | Rollback value |
|---|---:|---:|---:|
| `CBRK_SUPPLY_CHK` | 894281 | 0 | 894281 |
| `CBRK_IO_SAFETY` | 22027 | 0 | 22027 |
| `CBRK_USB_CHK` | 197848 | 0 | 197848 |

`CBRK_FLIGHTTERM` was explicitly excluded and remained `121212`.

## Preconditions

- Approved 974/974 live baseline SHA-256:
  `7ff75ac24b0f91d5dcd931ad39c18eda8db068ba22316f71c227cd693e3e99fb`.
- PX4 heartbeat source was system/component `1/1`, autopilot `12` (PX4).
- Heartbeat `base_mode=81`; `MAV_MODE_FLAG_SAFETY_ARMED` was not set.
- The live old value and MAV parameter type were checked before each write.
- `ModemManager` was temporarily stopped because the PX4 ACM device was marked
  `ID_MM_CANDIDATE=1`. No Agent, offboard, vision, or mission process owned a
  flight-controller serial device during the transaction.

## Transaction result

Attempt 7 passed. Each `PARAM_SET` received a matching `PARAM_VALUE` readback.
The same connection then captured all 974 parameters in 1.138761 seconds.

- Transaction JSON SHA-256:
  `cf4a3a731e7743c23e3ff1bb8e33d4d521500ea989a97984e536d22e5427c62c`.
- Immediate post-write snapshot SHA-256:
  `01f41a7f2b437105be2bb77b2d4b15ee50e8f4276e77c23b32f7729c6e1bb8c1`.
- Baseline-to-post differences were exactly the three approved parameters and
  PX4's derived `_HASH_CHECK` value.
- `CBRK_FLIGHTTERM` remained `121212`; all other parameter records were equal.

Earlier attempts terminated before a write (`writes=[]`) because no MAVLink
heartbeat was available or the bootloader ACM endpoint switched to the PX4
application endpoint. Attempt 4 aborted in the re-enumeration monitor before
starting the transaction tool. No partial group was created.

## Cold-boot persistence

The flight controller was disconnected for more than 10 seconds after the
successful transaction. The verifier ignored the first bootloader ACM endpoint
and captured the PX4 application endpoint on try 2.

- Cold-boot snapshot: 974/974 complete, source `1/1`.
- Cold-boot snapshot SHA-256:
  `5282cbbecaf0150d4567acdd10a9e0af31f29e2946768b02e7bece37df79b423`.
- Recovery rounds: 4 full-list retries while the parameter service started.
- The entire parameter dictionary is bytewise equal to the immediate post-write
  dictionary.
- The three approved values remain zero and `CBRK_FLIGHTTERM` remains `121212`.

## Tool verification

`px4_param_snapshot.py` was hardened to retry `PARAM_REQUEST_LIST` when a valid
PX4 heartbeat arrives before the parameter service is ready. A fake-connection
test covers the initial-silence recovery path.

Command:

```text
python3 -m unittest discover -s test/runtime -p 'test_px4_*.py' -v
```

Result: 20 tests, 0 failures, 0 errors. `git diff --check` passed.

## Gate effect
