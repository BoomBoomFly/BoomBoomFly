# H2 unit and fault evidence — GO

Dedicated evidence root: `/tmp/boomboomfly-wave4b-h2-20260728-01`.

| Required scenario | Result and zero-writer evidence |
|---|---|
| ACK accepted | PASS; correlated mode/arm ACK plus newer status is the only tested route to ACTIVE |
| ACK rejected/timeout | PASS; each latches fault and returns setpoint=false, mode=false, command=NONE |
| wrong command/sequence/target/origin; no pending; late ACK | PASS; all correlation mismatches fail closed |
| no/stale/lost RC | PASS; 7 RC gtests cover no first frame, signal loss, short channels, bad index, stale, non-finite/out-of-range, and valid normalization; gate `rc_fresh=false` has zero outputs |
| kill stale/latch | PASS; readiness loss/latch yields zero outputs and requires manual recovery |
| duplicate writer | PASS; `single_writer=false` yields zero outputs |
| owner/lease/epoch/authority sequence loss | PASS; mismatch or sequence change yields zero outputs |
| DDS/PX4/Agent/node restart | PASS at common epoch/restart gate; restart returns WAIT/zero; H3 executes two real production-node runs |
| stale setpoint/mode pair | PASS; each freshness/pairing loss yields zero outputs |
| clock jump, zero/frozen/backward/future/stale timestamp | PASS; timestamp gate rejects each and restart clears the prior epoch |
| serial odd/short/partial/reordered/CRC/disconnect/reconnect | PASS by quarantine containment, not parser repair: discovery=0, launch refs=0, package refs=0, execution/writer path unreachable |
| vision dropout/reset/NaN/Inf | PASS for the authorized disabled profile: no publisher and zero output; unit gate also rejects invalid finite/epoch/time/freshness states |
| node exit/resource release | PASS in H3: clean SIGINT exits, publisher inventory returns to zero, forbidden process count 0 |

Executed suites:

- `test_safety_gate`: PASS
- `test_rc_input`: 7/7 PASS
- `test_topic_contract`: 1/1 PASS
- `test_vision_safety`: 4/4 PASS
- serial quarantine governance tests: 6/6 PASS
- final colcon result: 14,598 tests, zero failures

The fail-closed output contract is structural: `SafetyGate::latch`,
FAULT_LATCHED, manual recovery, and restart all return
`publish_setpoint=false`, `publish_mode=false`, and `CommandKind::NONE`.
The sole ROS adapter publishes only when those decision fields authorize it.
H3 independently observed message count 0 for all control topics.

The serial runtime protocol remains unsafe and untested because it is outside
production. Re-enabling serial requires a new governance decision and the
sanitizer/golden-vector/runtime suite; removing quarantine would reopen P0.

```text
H2: GO
HARDWARE ACCESSED: NO
```
