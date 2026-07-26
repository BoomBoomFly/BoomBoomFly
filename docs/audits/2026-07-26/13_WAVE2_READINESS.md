# BoomBoomFly Wave 2 readiness

This document is a planning gate only. Wave 1 did not implement T02, T03, T04,
or T06 feature code.

## Summary

| Task | Decision | Recommended parallelism |
|---|---|---:|
| T02 — PX4 `rc_channels` profile | **BLOCKED** | 2 after blockers close |
| T03 — ACK/freshness/PRESTREAM | **PARTIALLY READY** | 2 |
| T04 — owner/lease/graph guard | **PARTIALLY READY** | 3 |
| T06 — required CI | **PARTIALLY READY** | 3 |

## T02 — PX4 v1.16.2 `rc_channels` firmware profile

Decision: **BLOCKED**

Prerequisites already available:

- unified evidence and rollback schemas;
- dirty checkout receipt/replay mechanism;
- environment/PX4 lock schemas and blocker template;
- exact DDS-only package boundary.

Blocking conditions:

- no approved PX4 source origin and exact commit;
- no recursive PX4 submodule origin/SHA lock;
- ARM cross-compiler is not locked and the recorded probe is missing;
- Micro XRCE-DDS Agent is not present/locked;
- no immutable environment/container identity;
- the four preserved dependency receipts lack maintainer signatures;
- no T02-specific source, generator, SITL, or FMUv3 evidence exists.

Start condition: a maintainer selects the PX4 v1.16.2 source commit and signing
identity, the recursive submodules and cross-toolchain are locked, and the
T00/T08 validators pass those exact inputs.

Recommended parallelism: two agents may prepare the static generator/profile
work and evidence harness after the lock is real; SITL and FMUv3 build remain
serial gates. No flash or hardware work is authorized.

Next Codex prompt summary:

> Implement only BBF-NEXT-T02 from an approved exact PX4 v1.16.2
> source/submodule/toolchain lock. Add the minimal `rc_channels` DDS publication,
> generator assertions, isolated SITL with a real PX4 publisher, and FMUv3
> build/hash evidence. Do not access hardware, flash, modify parameters, or use
> mock output as acceptance.

## T03 — ACK, feedback freshness, and PRESTREAM

Decision: **PARTIALLY READY**

Prerequisites already available:

- T01 exact package/build boundary;
- isolated `offboard_cpp` build/test entrypoint;
- evidence schema for commands, raw logs, results, and artifacts.

Blocking/partial conditions:

- write the failing ACK/freshness/PRESTREAM unit tests first;
- freeze ACK correlation, PX4 reboot epoch, clock, and freshness contracts;
- SITL acceptance remains blocked on T02;
- no current runtime authority/lease contract exists yet, so the T03/T04
  interface must be frozen before integration.

Allowed next start: pure unit design and implementation within
`src/offboard_cpp`, with no ROS graph, PX4, hardware, mode, arm, parameter, or
firmware action.

Recommended parallelism: two agents for ACK transaction tests and
freshness/clock wrappers; FSM integration remains serial.

Next Codex prompt summary:

> Implement BBF-NEXT-T03 only. Begin with failing table-driven tests for every
> VehicleCommand ACK result, correlation/timeout, first/stale/reboot/clock
> behavior, and PRESTREAM continuity. Keep PX4 control publish count zero before
> readiness. Use the T01 DDS-only entrypoint; defer SITL to the locked T02
> profile and do not touch hardware or parameters.

## T04 — owner/lease and runtime graph guard

Decision: **PARTIALLY READY**

Prerequisites already available:

- T01 package and exact static launch boundary;
- production launch remains disabled;
- fail-closed evidence and validation patterns.

Blocking/partial conditions:

- a reviewed control-authority ADR is required;
- owner ID, lease ID, sequence, deadline, renewal, revocation, and manual
  recovery semantics must be frozen;
- the command-envelope interface shared with T03 must be frozen before either
  integration path proceeds;
- runtime graph discovery transient behavior and fail-closed deadlines need
  explicit tests.

Allowed next start: ADR/schema and synthetic graph/lease fault tests below
`/tmp`. No production launch or hardware graph is authorized.

Recommended parallelism: three agents for protocol/schema, graph guard, and
fault fixtures; integration remains serial.

Next Codex prompt summary:

> Implement BBF-NEXT-T04 only after an explicit authority ADR. Define one atomic
> owner/lease/sequence/deadline envelope, continuous graph cardinality checks,
> fail-closed lease revocation, and manual recovery. Test duplicate/restarted
> writers and owners entirely with synthetic fixtures; do not enable production
> launch or send `/fmu/in/*`.

## T06 — root required CI and quality gates

Decision: **PARTIALLY READY**

Prerequisites already available:

- T00 environment, receipt, and approval validators;
- T01 authoritative package/build/test and launch guard entrypoints;
- T08 evidence/index/release/rollback validators;
- deterministic negative test suites for the new Wave 1 gates.

Blocking/partial conditions:

- CI runner image/tool versions must be locked; the current host inventory is
  not a reproducible container or apt/rosdep lock;
- the empty receipt signer trust list and unapproved receipts must remain
  visible blockers, not be bypassed;
- Foxy/aarch64 versus hosted runner behavior needs an explicit strategy;
- existing package lint/test failures, if any, must be reported and fixed in
  their owning task rather than suppressed;
- remote required-check and branch-protection configuration needs separate
  administrator authorization and was not changed in Wave 1.

Allowed next start: workflow/config code for manifest, schema, package boundary,
launch guard, syntax, and isolated build/test jobs. Do not alter remote
repository settings in the implementation task.

Recommended parallelism: three agents for manifest/schema jobs, DDS build/test,
and static-analysis/lint; final workflow integration and negative CI proof are
serial.

Next Codex prompt summary:

> Implement BBF-NEXT-T06 only. Pin every action, image, package, and tool; run
> Wave 1 receipt/environment/evidence/package/launch gates and the authoritative
> DDS-only build/test with artifacts. Add intentional negative CI fixtures.
> Never weaken checks, hide current blockers, use moving `latest`, access
> hardware, or change remote branch protection without separate authorization.

## Wave 2 coordination order

1. Close T02 source/submodule/toolchain/signature blockers.
2. In parallel, freeze the T03/T04 shared authority and command-envelope
   interfaces and begin their pure unit/ADR work.
3. Start T06 static jobs immediately, but gate build/test promotion on the
   locked environment and truthful existing test results.
4. Integrate T03 before T04 runtime ownership into the production-disabled
   profile; enablement is a later, separately reviewed decision.
