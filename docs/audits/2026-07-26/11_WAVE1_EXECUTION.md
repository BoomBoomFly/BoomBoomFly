# BoomBoomFly Wave 1 execution

## Repository and integration baseline

- Canonical origin: `https://github.com/BoomBoomFly/BoomBoomFly.git`
- Integration branch: `agent/audit-wave1-remediation`
- HEAD before Wave 1: `5a0e6edd4930474506a1046d414425893ebd800f`
- Integration HEAD before these reports: `b4aba4a063f12c85662309e0513af0af0e8d1308`
- Initial root working tree: clean
- Historical audit reference `agent/follow-latest-offboard@3ce28094...` was not
  treated as the current checkout.

The coordinator created independent branches/worktrees below
`/tmp/boomboomfly_wave1/` for evidence, environment, receipts, package
boundary, launch guard, and review. Integrations were serialized in the
required order. A later execution-environment restart reclaimed those
temporary worktrees and validation artifacts; the committed repository state
was preserved and the final validation tree was recreated from scratch at
`/tmp/boomboomfly_wave1_validation`.

## Agent ownership and results

| Agent | Scope | Result |
|---|---|---|
| A | T00 dirty checkout receipts | Four exact receipts and replay artifacts; approval self-claims replaced by detached allowlisted Ed25519 approvals; current receipts remain `UNAPPROVED`. |
| B | T00 environment/toolchain | Host inventory, schemas, PX4 lock placeholder, strict current provenance comparison including recursive submodule state. |
| C | T01 package boundary | Exact three-package allowlist, full workspace classification, build/test entrypoints, and fail-closed dependency tests. |
| D | T01 launch boundary | Python/XML static scan, exact production Node multiset, dangerous action/device tests, and production disabled profile. |
| E | T08 evidence/release/rollback | Unified schemas, validators, legacy index, templates, and rollback execution-evidence binding. |
| Reviewer | Independent read-only review | Initial five P1 and two residual P1 were reproduced and returned for correction; final disposition is recorded in `12_WAVE1_VALIDATION.md`. |

No two write agents owned the same file. The coordinator alone integrated and
committed agent output.

## T00 — dirty checkout and environment baseline

Status: **COMPLETE WITH EXPLICIT APPROVAL BLOCKER**

Implemented:

- `docs/evidence/receipts/{librealsense,navigation_msgs,realsense_ros,vision_opencv}.json`
- exact base64 patch artifacts under `docs/evidence/receipts/patches/`
- `docs/evidence/schemas/workspace_receipt.schema.json`
- `docs/evidence/schemas/workspace_receipt_approval.schema.json`
- `docs/evidence/receipts/APPROVALS.md`
- empty, explicit `docs/evidence/receipts/approvals/trusted_maintainers.json`
- `Scripts/installation/verify_workspace_receipts.py`
- `test/workspace_receipts/test_verify_workspace_receipts.py`
- `docs/evidence/environment/current_environment.json`
- environment and PX4 lock schemas plus the intentionally unverified lock template
- `Scripts/installation/verify_environment.py`
- `test/environment/test_verify_environment.py`
- `docs/evidence/WORKSPACE_BASELINE_2026-07-26.md`
- `docs/evidence/TOOLCHAIN_BASELINE_20260726.md`

The four preserved checkouts were read only. Receipts record origin, HEAD/base,
branch state, tracked/staged/untracked state, file modes, classifications,
patch/content hashes, platform/purpose claims, replay order, and approval
state. Receipt-local approval fields cannot produce PASS: a detached approval
must bind the exact receipt and checkout hashes and verify against an
allowlisted Ed25519 maintainer key. The trust list is intentionally empty.

Environment probes record raw argv, stdout/stderr, exit code, requirement, and
present/missing/unverified state. Missing tools were not installed. No moving
`latest` dependency was introduced. PX4 source, recursive submodules, ARM
toolchain, and Micro XRCE-DDS Agent remain explicit future-T02 blockers.

## T01 — DDS-only package and launch boundaries

Status: **COMPLETE FOR STATIC/BUILD BOUNDARY; PRODUCTION LAUNCH DISABLED**

The only production workspace packages are:

- `px4_msgs`
- `offboard_cpp`
- `vision_to_dds`

Implemented:

- `config/profiles/dds_only_packages.yaml`
- `Scripts/test/verify_package_boundary.py`
- `Scripts/build/build_dds_only.sh`
- `Scripts/test/test_dds_only.sh`
- `test/package_boundary/test_package_boundary.py`
- `config/profiles/dds_only_launch.yaml` and its schema
- `Scripts/test/launch_guard/check_launch_safety.py`
- `test/launch_guard/` fixtures and tests
- the two dated DDS-only boundary evidence documents

The package verifier classifies the complete current workspace, compares exact
allowlisted discovery, checks direct and transitive manifest dependencies, and
rejects forbidden dependencies even when the forbidden package is not
discovered. The authoritative wrappers clear inherited ROS workspace
underlays, use explicit paths and package names, and write only below `/tmp`.

The launch guard statically parses Python and XML without importing or running
launch code. It rejects forbidden packages/processes, serial devices, hardware
nodes, Agent auto-start, dangerous YAML/defaults, dynamic unresolved content,
duplicate `/fmu/in/*` writers, and any mismatch from the exact allowlisted Node
multiset. Historical launch files remain present and classified. The profile
has `production_enabled: false`.

## T08 — evidence, release, and rollback schemas

Status: **COMPLETE**

Implemented:

- evidence metadata, index, release, and rollback schemas
- `Scripts/evidence/validate_evidence.py`
- `Scripts/evidence/validate_index.py`
- `Scripts/evidence/validate_manifest.py`
- `docs/evidence/index.yaml`
- release and rollback templates
- `test/evidence/test_evidence_validation.py`
- `docs/evidence/SCHEMA.md` and dated implementation note

The legacy evidence files were indexed without rewriting them. Historical PX4
parameter evidence cannot become current through indexing. Supersession links,
HEAD/origin provenance, required fields, artifact paths/hashes, and rollback
critical fields are fail-closed. A rollback marked `verified` must bind
hash-valid, current, reviewer-approved rollback execution metadata for the
current HEAD; populating a paper template is insufficient.

## Audit finding mapping

| Finding | Wave 1 treatment |
|---|---|
| `BBF-AUD-010` | Exact DDS-only package and launch boundary; forbidden discovery/action tests. |
| `BBF-AUD-011` | Four replayable dirty checkout receipts; signed external approval gate. |
| `BBF-AUD-021` | Rollback manifest structure and verified-execution binding only; no exercise claimed. |
| `BBF-AUD-028` | Machine-readable environment inventory and explicit PX4/toolchain lock blockers. |
| `BBF-AUD-030` | AST/XML launch guard and dangerous fixture tests. |
| `BBF-AUD-031` | Exact package dependency closure and direct forbidden dependency checks. |
| `BBF-AUD-033` | Unified evidence/index/release/rollback provenance and hash schemas. |
| `BBF-AUD-038` | Non-destructive machine-readable evidence index and dated execution reports. |

## Local commit sequence

The work is split into reviewable evidence, environment, receipt, package,
launch, corrective, and documentation commits. No build/install/log output is
tracked. No push or PR occurred before the final validation and review gates.

## Unfinished approvals and limitations

- All four checkout receipts are internally valid but lack a trusted
  maintainer key/signature and therefore remain `UNAPPROVED`.
- The environment capture is immutable evidence for the initial Wave 1
  checkout/worktree. `--check-current` correctly reports a branch/HEAD mismatch
  after integration commits rather than silently relabeling it current.
- The PX4 source/toolchain lock remains a template: PX4 source, recursive
  submodule SHAs, ARM cross-compiler, and Micro XRCE-DDS Agent are not locked.
- Production remains disabled. No runtime graph authority, command ACK FSM,
  firmware profile, CI workflow, SITL, bench, or flight capability was added.

## Safety boundary compliance

- Hardware accessed: no
- Serial device paths opened: no
- ROS/PX4/Micro XRCE-DDS launch or nodes started: no
- PX4 parameters read or written: no
- Firmware built or flashed: no
- Arm/mode/setpoint/VehicleCommand or `/fmu/in/*` messages sent: no
- `git reset`, `git clean`, stash, or forced checkout used: no
- Four preserved dirty checkouts modified: no
- Historical evidence/directories deleted or rewritten: no
- Remote repository settings, releases, Issues, or protection rules modified: no
- T02–T11 feature code implemented: no
