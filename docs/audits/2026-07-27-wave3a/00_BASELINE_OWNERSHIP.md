# Wave 3A baseline and ownership

Date: 2026-07-27
Repository root: resolved with `git rev-parse --show-toplevel` as
`/home/c/BoomBoomFly`

## Root baseline

| Item | Observed value |
|---|---|
| Starting branch | `master` |
| Starting HEAD | `f34f5e647846cf20bbe8003b52c21035831b4fe1` |
| `origin/master` divergence | `0 0`; local `master` and `origin/master` are identical |
| Root remote | `origin https://github.com/BoomBoomFly/BoomBoomFly.git` |
| Created work branch | `agent/wave3a-software-gates` |
| Root dirty state before branch creation | untracked `src/serial_driver_ros2/` |
| Tracked gitlink | `src/serial_driver_ros` at index SHA `87f3907f0b3b906d474a8d1e1dc9677ab0c4298f` |

The observed divergence differs from the expected “local master ahead of
origin/master by 6 commits”. Actual state wins. No reset, clean, stash, fetch,
pull, or overwrite was performed.

`src/serial_driver_ros` is an empty directory in this checkout. It has no
nested `.git` metadata, and `git submodule status` fails because `.gitmodules`
contains no mapping for the tracked gitlink. It therefore cannot provide a
checkout HEAD/origin/status. The sibling untracked checkout
`src/serial_driver_ros2` is protected as pre-existing user state:

- branch: `main` tracking `origin/main`
- HEAD: `8614989c8b9e60176a83d5d32a058801fafdb8d6`
- origin: `https://github.com/BoomBoomFly/serial_driver_ros2.git`
- dirty: four modified files and one untracked file

## Protected checkout inventory

| Path | Identity | Dirty state | Wave 3A disposition |
|---|---|---|---|
| `src/mavlink` | detached `22b62f8d55feb72f306d4c0147467beee490030d`; origin `https://github.com/mavlink/mavlink-gbp-release.git` | 233 modified, 2 untracked | read-only |
| `src/mavros` | detached `48b53ccdf95f10b2ab3366c6e061fad2a76bd6c8`; origin `git@github.com:mavlink/mavros.git` | 325 modified | read-only |
| `src/serial_driver_ros` | index gitlink `87f3907f0b3b906d474a8d1e1dc9677ab0c4298f`; checkout identity unavailable | empty/uninitialized; root does not currently report a work-tree modification | read-only; `REQUIRES_MAINTAINER_DECISION` |
| `src/serial_driver_ros2` | `main@8614989c8b9e60176a83d5d32a058801fafdb8d6`; origin `https://github.com/BoomBoomFly/serial_driver_ros2.git` | 4 modified, 1 untracked | read-only, preserve |
| `../communication` | path absent under `/home/c`; no identity available | `NOT_AVAILABLE` | no access; record blocker |

Before B1 writes, `src/offboard_cpp` was independently verified clean on
branch `DDS`, HEAD `cded3dc5b6906420db3767abd82b2df7ba6ea9f0`,
origin `https://github.com/BoomBoomFly/offboard_cpp.git`. The directory is
ignored by the root repository, so B1 changes and any later local commit must
be managed within that nested repository without changing a root manifest.

## Exclusive writers

| Work line | Exclusive write range |
|---|---|
| Coordinator | this baseline, post-validation ledger, Wave 3A summary, `docs/planning/NEXT_PARALLEL_TASKS.md`, `docs/handoff.md`, local commits |
| A1 | `docs/audits/2026-07-27-wave3a/A1_PX4_RC_CHANNELS_ALIGNMENT.md` |
| B1 | `src/offboard_cpp/test/**` only |
| C1 | new authority ADR, authority schema, independent authority tests/fixtures, C1 report |
| D1 | CI design report and CI-only offline fixtures; no executable workflow |
| G1 | dependency-profile design report and, only if separately approved, validator/tests; no manifest migration |
| F1 | `tools/sitl_acceptance/**`, `test/sitl_acceptance/**`, `docs/verification/**`, F1 report |
| H | hardware runbook, hardware inventory, prop-off bench evidence only; sole hardware accessor |

No two writers may modify the same file. Workers do not commit. The
coordinator reviews and commits after validation.

## Frozen B1/C1 consumer boundary

C1 owns an independent envelope validator whose observable result is
`accept/reject`, a stable rejection event code, and latch state. B1's contract
consumer may publish only when the envelope result is accepted and its own
ACK, freshness, status, and PRESTREAM gates are all satisfied. Any rejection
or latch keeps the synthetic `/fmu/in/*` publish count at zero. Manual recovery
may return to a non-active ready state; it never enters `ACTIVE`
automatically.

Wave 3A does not integrate this boundary into the production Offboard FSM.

## Environment observations

- Python: `3.8.10`
- installed `jsonschema`: `4.19.2` (not the anticipated `3.2.0`)
- selected Ninja: `/home/c/.local/bin/ninja`, executable, version
  `1.11.1.git.kitware.jobserver-1`
- host `bwrap`: `/usr/bin/bwrap`, version `bubblewrap 0.4.0`
- the default command launcher failed before executing the requested command
  and reported that it could not locate a system or bundled `bwrap`; a
  separately approved host-side probe then resolved and executed
  `/usr/bin/bwrap` successfully. The launcher failure is not evidence that
  `bwrap` is absent from the host. Read-only and in-scope commands were rerun
  through the managed approval path.

These observations are kept separate from code/test regressions. No schema is
downgraded and no negative test or allowlist is relaxed.

## Hardware authorization boundary

Only H may access hardware. The current authorization is:

```text
READ-ONLY HARDWARE INVENTORY: AUTHORIZED
PROP-OFF DISARMED BENCH: AUTHORIZED
FIRMWARE FLASH: REQUIRES PER-ARTIFACT HUMAN GO
PROP-OFF ARMED BENCH: REQUIRES ON-SITE HUMAN GO
PROPELLER INSTALLATION: NOT AUTHORIZED
INDOOR FLIGHT: BLOCKED
ARM / MODE / TAKEOFF / ABORT AUTHORITY: HUMAN ONLY
PRODUCTION: BLOCKED
FLIGHT: NOT AUTHORIZED
```

H0 must stop if identity is incomplete. H1, H3, and H4 cannot be entered
automatically. No authorization permits Codex or a node to arm, change mode,
take off, write parameters, or flash an unconfirmed artifact.
