# Wave 3A canonical validation ledger

Date: 2026-07-27
Scope: static, offline, synthetic, and unit validation only
Root start identity:
`agent/wave3a-software-gates@f34f5e647846cf20bbe8003b52c21035831b4fe1`

This ledger records commands executed on the combined Wave 3A worktree. It is
not SITL, bench, hardware, flight, or production evidence. No ROS, PX4,
Micro XRCE-DDS Agent, launch file, or device was started or opened.

## Startup identity

| Probe | Observed value |
|---|---|
| `command -v bwrap` | `/usr/bin/bwrap` |
| `bwrap --version` | `bubblewrap 0.4.0` |
| `git rev-parse --show-toplevel` | `/home/c/BoomBoomFly` |
| root branch | `agent/wave3a-software-gates` |
| root start HEAD | `f34f5e647846cf20bbe8003b52c21035831b4fe1` |
| protected root dirty path | pre-existing untracked `src/serial_driver_ros2/` |
| B1 repository start | `src/offboard_cpp`, `DDS@cded3dc5b6906420db3767abd82b2df7ba6ea9f0` |
| B1 local candidate commit | `c744757a2df467807af240e34188869af65c603e` |

The default command launcher failed before executing the first probe and said
that it could not locate a system or bundled `bwrap`. The separately approved
host-side probes above then resolved and executed `/usr/bin/bwrap`. The
launcher failure is not evidence that the host lacks bubblewrap.

## Canonical and local validation

| Command/check | Exit | Result | Scope or classification |
|---|---:|---|---|
| `python3 -m unittest discover -s test -p 'test_*.py' -v` | 0 | `PASS` | 115 tests; 0 failures/errors/skips |
| `python3 -m unittest discover -s src/offboard_cpp/test -p 'test_*.py' -v` | 0 | `PASS` | B1 12 tests; 0 failures/errors/skips |
| `python3 -m compileall -q tools/authority test/authority test/ci_design test/dependency_profiles src/offboard_cpp/test` with cache under `/tmp` | 0 | `PASS` | syntax only |
| authority valid-envelope CLI | 0 | `PASS` | `AUTH_ACCEPTED`, latch `CLEAR`, consumer `READY` |
| `validate_ci_design.py --config test/ci_design/job_graph.json` | 0 | `PASS` | design document only; no workflow ran |
| dependency-profile valid default CLI | 0 | `PASS` | selected only `active` / `src/px4_msgs` |
| `Scripts/evidence/validate_index.py` | 0 | `PASS` | existing evidence index unchanged |
| `Scripts/test/launch_guard/check_launch_safety.py` | 0 | `PASS` | production disabled; no launch executed |
| `git diff --check` before root staging | 0 | `PASS` | tracked planning/handoff edits |
| B1 staged `git diff --cached --check` | 0 | `PASS` | one EOF blank line was removed before commit |
| protected manifest/profile SHA-256 comparison | 0 | `PASS` | all six hashes match the G1 report; no diff |
| `Scripts/test/verify_package_boundary.py` | 2 | `BLOCKED` | protected `src/serial_driver_ros2` is discovered as `serial_driver`, but the profile expects `src/serial_driver_ros` |
| `Scripts/test/test_dds_only.sh --output-root /tmp/boomboomfly_wave3a_dds_only` | 2 | `BLOCKED` | stopped at the same package-boundary check before build/test |

The first D1 direct invocation omitted the required `--config` selector and
returned argparse exit 2. It was an operator invocation error, not a product
result; the corrected command above returned 0. No failed result was relabeled
as a pass.

The DDS wrapper wrote
`/tmp/boomboomfly_wave3a_dds_only/artifacts/package-boundary-summary.json` with:

```json
{"error":"package serial_driver path mismatch: expected src/serial_driver_ros, found src/serial_driver_ros2","status":"FAIL"}
```

No build phase ran after that fail-closed preflight. The conflicting checkout
was present before Wave 3A, has its own nested Git metadata and user changes,
and was not modified, moved, cleaned, staged, or committed by the root work.
This is an environment/worktree blocker, not a Wave 3A regression.

## Gate classification

| Classification | Result |
|---|---|
| Wave 3A offline/static/unit regressions | 0 found |
| root canonical Python suite | `PASS` |
| B1 test-only contract suite | `PASS` |
| DDS-only build/test | `BLOCKED` before build by protected checkout path conflict |
| formal PX4 DDS SITL | `BLOCKED`, not run |
| hardware/serial/device activity | `NOT_APPLICABLE`, none performed |
| firmware/parameters/arm/mode/topic publication | `NOT_APPLICABLE`, none performed |
| production | `BLOCKED` |

Passing synthetic or unit gates does not implement the B/C runtime boundary,
enable a workflow, migrate a manifest, prove a PX4 publisher, or authorize the
next verification level.
