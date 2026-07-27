# Wave 3B D2 — local offline CI implementation

Date: 2026-07-27  
Status: **IMPLEMENTATION PASS; EXECUTION BLOCKED; NON-REQUIRED**

## Scope and safety boundary

D2 adds a local GitHub Actions workflow definition and its fail-closed local
launcher. It does not change a branch-protection rule, ruleset, required check,
remote repository, dependency checkout, hardware device, PX4 parameter, or
firmware. No workflow command accesses a device path, launches ROS/PX4/Agent,
runs formal SITL, or publishes a real topic. `sitl-spec-offline` remains
explicitly `OFFLINE_SYNTHETIC`.

The workflow is manual-only (`workflow_dispatch`) and has read-only repository
permission. It has no `push`, `pull_request`, or scheduled trigger and contains
no `continue-on-error`.

## Implemented graph

The stable job IDs are:

1. `governance-static`
2. `python-unit`
3. `dds-boundary`
4. `evidence-integrity`
5. `sitl-spec-offline`
6. `supply-chain-static`
7. `dds-build-test`

Dependent jobs use `always()` only so a failed dependency produces a visible
`UPSTREAM_GATE_BLOCKED` ledger instead of a silent GitHub skip. It does not
convert a failure to success. In particular, `dds-build-test` remains red or
blocked when its prerequisites fail.

The implementation files are:

- `.github/workflows/wave3b-offline-gates.yml`
- `Scripts/ci/run_offline_gate.py`
- `test/ci_design/workflow_contract.json`
- `test/ci_design/validate_workflow.py`
- `test/ci_design/test_wave3b_workflow.py`
- updated `test/ci_design/job_graph.json`

## Frozen contract and isolation

The checked contract fixes Ubuntu 20.04 x86_64, Python 3.8.10,
`jsonschema==4.19.2` with `Draft202012Validator`, ROS 2 Foxy, and Bubblewrap
0.4.0. The action references are exact 40-character commits:

- `actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683`
  (`v4.2.2`)
- `actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02`
  (`v4.6.2`)

Gate commands run only after the lock preflight passes. The launcher uses
Bubblewrap with `--unshare-all`, a read-only repository bind, an ephemeral
`/tmp`, and no device bind. Artifact retention is explicit: summary 14 days,
diagnostics 30 days, and machine-readable ledger 90 days.

The supply-chain job now executes the CI-design unit suite. The suite proves
that each committed deliberately invalid manifest, profile, topic, link,
schema, secret, and license fixture returns non-zero. No fixture, allowlist,
schema, or forbidden set was weakened.

## Corrected Bubblewrap evidence

The package name `bubblewrap` was not treated as an executable. No
`command -v bubblewrap` probe was run. Fresh host probes produced:

| Probe | Exit | stdout | stderr |
|---|---:|---|---|
| `command -v bwrap` | 0 | `/usr/bin/bwrap` | empty |
| `/usr/bin/bwrap --version` | 0 | `bubblewrap 0.4.0` | empty |
| no-network/no-device-bind `bwrap --unshare-all ... /bin/true` | 0 | empty | empty |

Therefore Bubblewrap is **PASS**, not `BLOCKED_BY_EXECUTION_ENVIRONMENT`.
The Codex inner launcher separately emitted an incorrect pre-command
“bubblewrap is unavailable” panic. Host execution above supersedes that stale
launcher conclusion for D2 capability classification.

## Validation results

| Check | Result |
|---|---|
| workflow static validator | PASS |
| `test/ci_design` unittest discovery | PASS, 13 tests |
| seven negative fixture CLI outcomes | PASS, all non-zero |
| Python compile check for new runner/validator/tests | PASS |
| D2 path `git diff --check` | PASS |
| real `governance-static` launcher preflight | EXPECTED BLOCKER, exit 78 |

The exit-78 ledger classified the preflight as
`BLOCKED_BY_DEPENDENCY_LOCK` and preserved the successful bwrap path, version,
capability exit codes, stdout, and stderr.

## Remaining blockers

The following immutable lock values remain intentionally null and fail closed:

- runner image digest;
- ROS apt snapshot;
- ROS package-set SHA-256;
- Python runtime SHA-256;
- Python requirements SHA-256;
- colcon bundle SHA-256;
- compiler bundle SHA-256;
- offline dependency bundle SHA-256.

In addition, GitHub retired the hosted `ubuntu-20.04` label on 2025-04-15.
The frozen Foxy contract therefore needs a reviewed immutable Ubuntu 20.04
container or an attested self-hosted runner before remote execution can be
claimed. D2 does not silently migrate to Ubuntu 22.04/24.04 because that would
change the requested Foxy/toolchain identity.

## Decision

- local workflow graph and static enforcement: **PASS**
- bwrap executable/version/capability: **PASS**
- reproducible execution with exact dependency restore: **BLOCKED**
- `dds-build-test` execution: **BLOCKED**, visibly fail-closed
- remote required checks/ruleset: **NOT AUTHORIZED / NOT MODIFIED**
- hardware, formal SITL, armed bench, or flight evidence: **NOT APPLICABLE**
