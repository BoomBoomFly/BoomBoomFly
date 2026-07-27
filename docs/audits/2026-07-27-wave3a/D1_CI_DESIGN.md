# Wave 3A D1 — locked offline CI gate design

Date: 2026-07-27
Status: **DESIGN VALIDATED; EXECUTABLE WORKFLOW BLOCKED**

## Scope and non-claims

This record defines the root job graph, fail-closed behavior, dependency lock
requirements, artifacts, and negative fixture coverage. It does not create a
GitHub Actions workflow, alter a remote ruleset, enable a required check, fetch
dependencies, run SITL, or access hardware.

The repository has no root `.github/` directory at this baseline. Third-party
nested-repository workflows are not BoomBoomFly gates. The stdlib oracle in
`test/ci_design/` validates this design only; it is not workflow execution
evidence.

## Baseline and observed environment

- root branch: `agent/wave3a-software-gates`
- root HEAD: `f34f5e647846cf20bbe8003b52c21035831b4fe1`
- requested platform: Ubuntu 20.04, ROS 2 Foxy, Python 3.8
- local POSIX-PATH probe: Python 3.8.10, `jsonschema==4.19.2`,
  GCC 9.4.0 (`9.4.0-1ubuntu1~20.04.2`), CMake 3.16.3
- supplied known blocker: another canonical environment reports
  `jsonschema==3.2.0`, which has no `Draft202012Validator`
- supplied known blocker: the raw PATH may select a non-executable
  WindowsApps `ninja`
- supplied known blocker: ROS logging/network probes in DDS-only testing may
  be sandbox-denied
- supplied known blocker: `src/vision_to_dds` has existing upstream lint
  failures

The 4.19.2 local probe does not erase the supplied 3.2.0 failure. They describe
different environment resolutions and must appear as separate ledger rows
until the runner and Python environment are immutable.

## Proposed job graph

```text
governance-static ──┬── dds-boundary ───────────┐
                    ├── evidence-integrity ─────┼── dds-build-test
                    └── supply-chain-static ────┘
python-unit ─────────── sitl-spec-offline
```

All jobs are fail-closed, bounded by a timeout, use a clean checkout, and have
network disabled after a separately attested dependency restore. No job may
write a PX4 parameter, publish `/fmu/in/*`, launch ROS/PX4/Agent nodes, access
hardware, or promote mock/parser results to SITL evidence.

| Job | Purpose | Authoritative offline entries | Timeout |
|---|---|---|---:|
| `governance-static` | diff, launch safety, CI graph shape | `git diff --check`; launch guard; D1 oracle | 10 min |
| `python-unit` | syntax and canonical stdlib suite | `compileall`; repository `unittest discover` | 15 min |
| `dds-boundary` | exact production package/forbidden set | `verify_package_boundary.py` | 10 min |
| `evidence-integrity` | index and preserved-checkout receipts | `validate_index.py`; receipt validator | 15 min |
| `sitl-spec-offline` | catalog/schema/parser only | catalog validator; offline SITL-spec unit tests | 15 min |
| `supply-chain-static` | source receipts and policy fixtures | receipt validator; D1 negative fixture oracle | 15 min |
| `dds-build-test` | isolated allowlisted build/test | `test_dds_only.sh` with all output below `/tmp` | 45 min |

`sitl-spec-offline` must label every output `OFFLINE_SYNTHETIC`; it is neither
formal PX4 SITL nor bench evidence. `dds-build-test` is not authorized until
the environment preflight succeeds. The production package allowlist and
forbidden set remain unchanged.

## Required runner and dependency lock

An executable workflow is prohibited until one reviewed lock record contains
all of the following:

1. immutable Ubuntu 20.04 runner or container image digest, including
   architecture;
2. ROS 2 Foxy apt repository/snapshot identity and exact installed package
   versions;
3. Python 3.8 runtime artifact hash and exact package lock with hashes;
4. an exact `jsonschema` version that exposes `Draft202012Validator`; the
   current design does not lower any schema to accommodate 3.2.0;
5. exact `colcon-core`, extensions, CMake, Ninja, GCC/G++ and linker packages;
6. exact source manifest SHAs and approved URLs, with no moving ref;
7. offline dependency cache/bundle digest and provenance;
8. lock validator identity and hash.

The design oracle intentionally leaves `runner_image_digest`,
`ros_apt_snapshot`, `python_runtime`, `colcon_bundle`, and `compiler_bundle`
unresolved and sets `workflow_enabled=false`. Enabling it while any field is
empty is a deterministic failure.

The PATH preflight records `type -a ninja`, resolved path, executable bit, and
version under both the raw PATH and the minimal POSIX PATH. A raw-PATH failure
remains in the ledger even if the comparison passes.

## Job behavior and failure classification

Every command records command text, start/end timestamps, exit code, root SHA,
environment-lock digest, and stdout/stderr artifact hashes. Failures are
classified without allowlisting:

| Class | Example | Presentation |
|---|---|---|
| `REAL_REGRESSION` | a new unit/contract failure | red job, exact test and diff |
| `UPSTREAM_EXISTING` | existing `vision_to_dds` lint | red job with named cases; never ignored |
| `ENVIRONMENT` | `jsonschema==3.2.0`, WindowsApps Ninja | red preflight with actual/resolved versions |
| `SANDBOX` | denied ROS log/network probe | red/blocked row with denied operation |
| `DEPENDENCY_LOCK` | missing runner/apt/compiler digest | workflow creation remains blocked |

No fallback may delete negative tests, lower a schema, weaken a topic/profile
allowlist, add `|| true`, or relabel failure as success.

## Artifacts and retention

- successful job summaries, selected package lists, and checksums: 14 days;
- failed-job diagnostics, raw stdout/stderr, and test XML: 30 days;
- machine-readable validation ledger, source/toolchain identities, and
  artifact manifests: 90 days.

Artifacts must contain no credentials or unnecessary permanent hardware
identifiers. A secret scan runs before upload. Release artifacts are out of
scope and may never be assembled from this design-only graph.

## Negative fixtures

The D1 oracle has exactly one deliberately broken fixture for each required
category:

| Category | Broken condition | Required result |
|---|---|---|
| manifest | moving `main` ref | non-zero |
| profile | forbidden package in production set | non-zero |
| topic | legacy topic plus duplicate writer | non-zero |
| link | missing target escaping repository | non-zero |
| schema | wrong draft, weakened properties/required set | non-zero |
| secret | synthetic scanner-match metadata | non-zero |
| license | absent SPDX identity and policy denial | non-zero |

These fixtures contain no live secret and are never dependency inputs. The
oracle also rejects duplicate/missing jobs, graph cycles, fail-open commands,
unknown dependencies, non-positive retention, network-enabled jobs, and
premature workflow enablement.

## Known blockers and decision

Executable workflow creation remains blocked by the five unresolved immutable
lock fields, the conflicting observed Python/jsonschema environments, and the
lack of an approved offline dependency bundle. Remote required-check and
branch-protection configuration also requires a separate maintainer/admin
action after the workflow exists and has stable check names.

`dds-build-test` additionally remains conditional on a clean preflight. If it
runs, sandbox restrictions, known nested dependency lint, and genuine new
regressions must remain separate ledger classifications.

Decision:

- D1 design and negative fixture semantics: **PASS**
- executable root workflow: **BLOCKED**
- remote required checks/ruleset: **NOT_APPLICABLE / NOT AUTHORIZED**
- formal SITL evidence from this graph: **BLOCKED**
- production enablement: **BLOCKED**
