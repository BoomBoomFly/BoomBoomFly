# Wave 3B canonical validation ledger

Date: 2026-07-27
Root baseline: `afb4fdcecb22596056432492d1ad284919b065cd`
Offboard final: `976d6217d73a28b72e64300e2dd04bcbeeee30d7`
Execution class: offline/static/pure software only

## Canonical PASS results

| Validation | Result |
|---|---|
| `git diff --check` | `PASS` |
| `python3 -m compileall Scripts tools test` | `PASS`; bytecode redirected to `/tmp` |
| root unittest discovery | `PASS`, 152 tests |
| launch safety guard | `PASS`; production remains disabled |
| evidence index | `PASS` |
| offline scenario catalog | `PASS`, 12 normal + 25 fault = 37 |
| C1+C2 authority | `PASS`, 36 tests |
| D1+D2 CI design/workflow | `PASS`, 13 tests |
| G1+G2 dependency profiles | `PASS`, 15 tests |
| F1+F2 offline acceptance | `PASS`, 27 tests |
| B1 nested regression | `PASS`, 12 tests |
| B2 C++17 `-Werror` standalone build/test | `PASS` |
| D2 seven negative fixture classes | `PASS`, every fixture exit 1 |
| real active/archive/optional manifest policy | `PASS`, 16 exact, globally disjoint paths |
| JSON/YAML/JSONL parsing | `PASS`, 97 non-negative structured files |
| deliberately malformed JSON fixture | `PASS` as negative, exit 3 |
| Markdown relative links | `PASS`, 82 files, zero missing/escaping links |
| secret/private-key/token static patterns | `PASS`, zero hits outside the deliberate secret fixture |
| empty files | `PASS`, zero |
| bwrap executable/version/capability | `PASS`; `/usr/bin/bwrap`, `bubblewrap 0.4.0`, probe exit 0, empty stderr |

The F2 Wave 3B timeline contains 16 synthetic records and passes 29 assertions.
Every runtime rejection case has a bounded timeout and zero synthetic publish
delta/count. It remains `OFFLINE_SYNTHETIC` and retains
`px4_source_identity=BLOCKED`.

## Expected blockers and fail-closed results

| Gate | Exit/result | Classification | Evidence |
|---|---:|---|---|
| A2 exact PX4 source/submodules/generator/toolchain | blocked | `EXPECTED BLOCKER` | no approved local PX4-Autopilot source or immutable ARM/board toolchain |
| D2 executable job preflight | 78 | `EXPECTED BLOCKER` | eight immutable dependency/toolchain lock values unresolved |
| package boundary | 2 | `PROTECTED DIRTY STATE` | `serial_driver` expected at `src/serial_driver_ros`, found protected `src/serial_driver_ros2` |
| default manifest verify-only | 1 | `EXPECTED BLOCKER` | local Offboard B2 HEAD is not the published reproducible lock |
| archive verify-only | 1 | `EXPECTED BLOCKER` | archive entry verifies; same active Offboard blocker remains |
| perception verify-only | 1 | `PROTECTED DIRTY STATE` | Offboard mismatch plus three pre-existing dirty optional checkouts |
| navigation verify-only | 1 | `PROTECTED DIRTY STATE` | Offboard mismatch plus dirty `navigation_msgs` |
| moving verify-only | 1 | `EXPECTED BLOCKER` | explicit moving authorization accepted; Offboard ref mismatch and `../communication` absent |
| DDS-only wrapper | 2 | `PROTECTED DIRTY STATE` | stopped before build at package-boundary serial path mismatch |

The DDS wrapper isolated output was
`/tmp/boomboomfly_dds_test.clDhNP`. Its only artifact was
`artifacts/package-boundary-summary.json`, which records the serial path
mismatch. No colcon build or test followed that fail-closed boundary.

## Environment classification

Some Codex inner helper invocations exited 101 before executing and incorrectly
claimed bwrap was absent. They are `ENVIRONMENT FAILURE` of that launcher only.
The same commands were rerun through the approved host execution path. Fresh
real bwrap path, version, and sandbox probes all returned zero with empty
stderr, so the host is not `BLOCKED_BY_EXECUTION_ENVIRONMENT`.

## Regression decision

- new software regression: **none observed**;
- protected state modified: **no**;
- schema/allowlist/negative fixture weakened: **no**;
- remote rules, push, or PR: **not performed**;
- formal SITL: **not run / not authorized by the remaining gates**;
- H0/H1: **not run; no human GO requested because software gates did not all pass**.

## Result taxonomy

```text
PASS: pure-software B/C runtime, CI static contract, manifest migration,
      offline acceptance, governance/evidence/launch checks
EXPECTED BLOCKER: PX4 provenance, immutable CI locks, unpublished Offboard lock,
                  absent moving communication source
NEW REGRESSION: none
ENVIRONMENT FAILURE: Codex inner launcher pre-execution bwrap misdetection only
PROTECTED DIRTY STATE: serial_driver_ros2 and documented optional dirty checkouts
NOT AUTHORIZED: formal SITL, hardware without GO, armed bench, flash, flight
NOT APPLICABLE: hardware evidence and production promotion
```
