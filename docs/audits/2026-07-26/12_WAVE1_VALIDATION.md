# BoomBoomFly Wave 1 validation

## Result

Wave 1's new receipt, environment, package-boundary, launch-guard, evidence,
release, and rollback checks pass their positive and negative suites. The
authoritative isolated DDS-only build completed for exactly `px4_msgs`,
`offboard_cpp`, and `vision_to_dds`.

The authoritative test wrapper was interrupted after 14 minutes 54 seconds
without completing its first package. Direct CTest isolated the result:
`offboard_cpp` passes 2/2; `px4_msgs` passes 28/29 with the generated-Python
uncrustify check timing out at 60 seconds; `vision_to_dds` passes 3/6 and has
pre-existing copyright, cpplint, and uncrustify failures. These failures were
not hidden, ignored, or changed because fixing production package source is
outside T00/T01/T08.

Final independent reviewer disposition: **FINAL PASS — P0=0, P1=0**.

## Validation environment

- Repository: `/home/c/BoomBoomFly`
- Branch: `agent/audit-wave1-remediation`
- Wave 1 start HEAD: `5a0e6edd4930474506a1046d414425893ebd800f`
- Code integration HEAD: `b4aba4a063f12c85662309e0513af0af0e8d1308`
- Unified temporary root: `/tmp/boomboomfly_wave1_validation`
- Build root: `/tmp/boomboomfly_wave1_validation/dds_authoritative/build`
- Install root: `/tmp/boomboomfly_wave1_validation/dds_authoritative/install`
- Log root: `/tmp/boomboomfly_wave1_validation/dds_authoritative/log`
- Final static artifacts:
  `/tmp/boomboomfly_wave1_validation/artifacts/final`

No existing repository `build/`, `install/`, or `log/` directory was cleaned
or used for this validation.

## Wave 1 validator and negative-test matrix

The final batch command is:

```bash
bash /tmp/boomboomfly_wave1_validation/run_static_validation.sh
```

The machine-readable command/exit-code index is:

```text
/tmp/boomboomfly_wave1_validation/artifacts/final/exit-codes.tsv
```

| Check | Command | Expected exit | Result |
|---|---|---:|---|
| Diff whitespace | `git diff --check` | 0 | See final exit index |
| Shell syntax | `bash -n Scripts/{installation,build,test}/...` | 0 | See final exit index |
| Python syntax | `PYTHONPYCACHEPREFIX=/tmp/boomboomfly_wave1_validation/pycache python3 -m compileall Scripts test` | 0 | See final exit index |
| Evidence tests | `python3 test/evidence/test_evidence_validation.py` | 0 | 14 positive/negative tests |
| Environment tests | `python3 test/environment/test_verify_environment.py` | 0 | 16 positive/negative tests |
| Receipt tests | `python3 test/workspace_receipts/test_verify_workspace_receipts.py` | 0 | 8 positive/negative tests |
| Package boundary tests | `python3 test/package_boundary/test_package_boundary.py` | 0 | 9 positive/negative tests |
| Launch guard tests | `python3 test/launch_guard/test_launch_safety.py` | 0 | 11 positive/negative tests |
| Evidence index | `python3 Scripts/evidence/validate_index.py` | 0 | See final exit index |
| Rollback paper template | `python3 Scripts/evidence/validate_manifest.py --kind rollback docs/evidence/ROLLBACK_TEMPLATE.yaml` | 0 | Schema-valid unverified template |
| Environment schema | `python3 Scripts/installation/verify_environment.py --repository-root /home/c/BoomBoomFly` | 0 | See final exit index |
| Current environment provenance | same command with `--check-current --json-summary` | 1 | Expected stale branch/HEAD rejection |
| Receipt schema/replay/approval | `python3 Scripts/installation/verify_workspace_receipts.py --repository-root /home/c/BoomBoomFly --check-replay --replay-root /tmp/boomboomfly_wave1_validation/receipt-replay` | 2 | Expected `UNAPPROVED`; zero receipt errors |
| Package full inventory | `python3 Scripts/test/verify_package_boundary.py --workspace-root /home/c/BoomBoomFly --log-base /tmp/boomboomfly_wave1_validation/package-boundary-final` | 0 | Exact allowlist and full classification |
| Launch full inventory | `python3 Scripts/test/launch_guard/check_launch_safety.py --repository-root /home/c/BoomBoomFly` | 0 | Historical denials classified; production disabled |

The negative suites cover required-field omission, bad hashes, stale HEAD,
broken supersession, false rollback verification, wrong origin/HEAD/patch and
content hashes, absent receipt approval, untrusted/invalid signatures,
forbidden and indirect package dependencies, missing/unclassified packages,
dangerous launch `Node`/`ExecuteProcess`, device paths, dynamic content, and
production-node allowlist drift.

## DDS-only build and package tests

The authoritative command was:

```bash
bash Scripts/test/test_dds_only.sh \
  --output-root /tmp/boomboomfly_wave1_validation/dds_authoritative
```

The build phase returned success and built exactly:

```text
px4_msgs
offboard_cpp
vision_to_dds
```

Build logs:

```text
/tmp/boomboomfly_wave1_validation/dds_authoritative/log/build/
```

The combined wrapper later exited `2` after operator interruption during the
long-running first-package test; no build result was invalidated. Direct,
read-only package tests were then run from the isolated build directories:

| Package | Command | Exit | Result | Artifact |
|---|---|---:|---|---|
| `offboard_cpp` | `(cd .../build/offboard_cpp && ctest --output-on-failure)` | 0 | PASS, 2/2 | `.../build/offboard_cpp/Testing/Temporary/LastTest.log` |
| `px4_msgs` | `(cd .../build/px4_msgs && ctest --output-on-failure)` | 8 | BLOCKED, 28/29; generated-Python uncrustify timeout | `.../build/px4_msgs/Testing/Temporary/LastTest.log` |
| `vision_to_dds` | `(cd .../build/vision_to_dds && ctest --output-on-failure)` | 8 | FAIL, 3/6; existing copyright/cpplint/uncrustify findings | `.../build/vision_to_dds/Testing/Temporary/LastTest.log` |

No package source was changed to suppress these truthful pre-existing
failures. The Wave 1 boundary, schema, and static launch tests are independent
and pass.

## Explicit unverified or blocked items

- Four dirty checkout receipts are hash-valid and replayable but remain
  `UNAPPROVED` because no trusted maintainer key/signature is configured.
- The checked-in environment receipt describes the original audit worktree;
  it is not relabeled current after integration, so current comparison fails
  closed on branch/HEAD.
- PX4 source, recursive submodule lock, ARM toolchain, and Micro XRCE-DDS Agent
  remain missing or unverified. No software was downloaded or installed.
- `px4_msgs` generated-Python uncrustify exceeds its 60-second CTest limit on
  this host.
- Existing `vision_to_dds` copyright and formatting lint failures remain.
- Production launch is intentionally disabled.

## Independent review

The read-only reviewer initially found five P1 issues:

1. environment current comparison was too weak;
2. receipt approval could be self-asserted;
3. an undiscovered forbidden direct dependency could bypass the boundary;
4. production launch did not enforce the exact Node set;
5. a populated paper rollback template could claim verification.

After correction, two residual P1 issues were found in recursive PX4
submodule provenance comparison and receipt approval independence. After those
were fixed, one final environment edge was found: a present PX4 probe's
`reason` was not compared. It was fixed and covered by the 16-test environment
suite.

The reviewer then inspected the complete diff, final validation artifacts, and
all three reports and returned **FINAL PASS — P0=0, P1=0**.

## Safety observations

- Hardware accessed: no
- Serial devices opened: no
- PX4 parameters accessed or modified: no
- Firmware built or flashed: no
- ROS, launch, Micro XRCE-DDS Agent, MAVROS, Offboard, vision, lidar, camera,
  or VPU nodes started: no
- `/fmu/in/*`, VehicleCommand, or setpoint messages sent: no
- Arm or flight-mode actions: no
- `git reset`, `git clean`, stash, forced checkout, or dirty-checkout writes:
  no
- Remote settings, Issues, releases, protection rules, or PRs modified during
  validation: no
