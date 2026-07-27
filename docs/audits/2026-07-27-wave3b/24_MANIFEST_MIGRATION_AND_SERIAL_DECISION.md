# Wave 3B G2 — manifest migration and serial decision

> Capture date: 2026-07-27 (Asia/Shanghai)
> Execution boundary: offline/static/verify-only; no clone, fetch, checkout,
> build, DDS wrapper, ROS launch, SITL, hardware, or nested-repository change
> Archive/optional migration: **PASS**
> Serial conclusion: **REQUIRES_MAINTAINER_DECISION**

## 1. Read-only serial and alternate-source audit

| Item | Observed identity/state | Conclusion |
|---|---|---|
| root `src/serial_driver_ros` | index mode `160000`, gitlink `87f3907f0b3b906d474a8d1e1dc9677ab0c4298f`; directory has no `.git`; root has no tracked `.gitmodules`; gitlink object is unavailable in the root object database (`git cat-file` exit 128) | not an independently verifiable checkout or reproducible source definition |
| protected `src/serial_driver_ros2/` | independent repo, branch `main`, HEAD `8614989c8b9e60176a83d5d32a058801fafdb8d6`, origin `https://github.com/BoomBoomFly/serial_driver_ros2.git`, package name `serial_driver` | protected dirty candidate, not a canonical selection |
| protected checkout changes | modified `CMakeLists.txt`, `config/serial_config.yaml`, `launch/serial_driver.launch.py`, `src/serial_driver.cpp`; untracked `src/serial_orinnano.cpp` | **PROTECTED DIRTY STATE**; no mutation performed |
| `../communication` | absent | cannot serve as a locally verifiable replacement source |

The root gitlink has no verifiable origin/package metadata in the current
workspace, while the protected ROS 2 checkout has a different path and local
changes. No exact-commit maintainer decision establishes one canonical serial
source. Therefore neither serial path was admitted to active, archive, or
optional manifests, and no checkout was moved, deleted, renamed, staged, or
edited.

## 2. Applied source-profile migration

The previous 16-entry exact lock was split without changing any frozen commit
or canonical URL:

| Profile | Manifest | Entries | Default? |
|---|---|---:|---|
| active | `workspace.lock.repos` | 4 | yes |
| archive | `workspace.archive.repos` | 1 (`src/px4_bringup`) | no |
| optional perception | `workspace.optional-perception.repos` | 3 | no |
| optional navigation | `workspace.optional-navigation.repos` | 8 | no |

The complete governed inventory remains 16 unique paths. Every version is a
lowercase exact 40-character SHA. `src/px4_bringup` is locked at
`0fbdcbf6ee53d6927de75af1d98f22cf5bd4f917` and is available only with
`--with-archive`. Perception/navigation sources require their matching
`--with-optional` flag.

`workspace.repos` is now explicitly a non-governed moving developer index for
the four active sources plus absent `../communication`. It can be selected only
with an explicit `--manifest workspace.repos --allow-moving-refs`; it is not
part of default or governed profile composition.

## 3. Installer and validator enforcement

The installer now provides explicit `--with-archive` and repeatable
`--with-optional {perception,navigation}` selection. It validates all selected
manifests before restore processing and rejects:

- custom `--manifest` combined with a profile flag;
- `--allow-moving-refs` without explicit `--manifest`;
- duplicate target paths across composed manifests;
- unsafe paths and non-exact governed refs;
- existing dirty checkout, wrong origin, wrong HEAD, or missing checkout.

The standard-library dependency-profile validator now reads the real `.repos`
files and freezes expected profile ownership and canonical URLs. Synthetic and
real-manifest tests cover duplicate paths, moving archive refs, abbreviated
SHAs, URL substitution, unresolved serial admission, default exclusion, and
explicit profile composition.

The production boundary was not relaxed: there is no diff in
`config/profiles/dds_only_packages.yaml` or `workspace.excluded_packages`.
`px4_bringup`, `serial`, and `serial_driver` remain forbidden/excluded.

## 4. Offline validation

| Check | Result |
|---|---|
| installer `--help` inspected before implementation | PASS |
| validator `--help` inspected before implementation | PASS |
| `bash -n Scripts/installation/uav_px4_dds_install.sh` | PASS |
| Python compile for validator/tests | PASS |
| dependency-profile unit tests | PASS — 15/15 |
| real manifest inventory | PASS — 16 exact-SHA, unique canonical paths |
| duplicate/moving archive/URL mismatch/non-exact SHA | PASS — each returns nonzero |
| G2-scoped `git diff --check` | PASS |

The verify-only matrix intentionally audited the current workspace rather than
changing it:

| Selection | Exit | Classification | Exact observation |
|---|---:|---|---|
| default active | 1 | EXPECTED BLOCKER | 3/4 locked sources verified; local `offboard_cpp@976d6217d73a28b72e64300e2dd04bcbeeee30d7` differs from published restore lock `cded3dc5b6906420db3767abd82b2df7ba6ea9f0` |
| active + archive | 1 | EXPECTED BLOCKER | archive `px4_bringup` verified exact; same active offboard blocker |
| active + optional perception | 1 | PROTECTED DIRTY STATE | exact HEADs verified; `librealsense`, `realsense-ros`, and `vision_opencv` are dirty; same active offboard blocker |
| active + optional navigation | 1 | PROTECTED DIRTY STATE | exact HEADs verified; `navigation_msgs` is dirty; same active offboard blocker |
| explicit moving index | 1 | EXPECTED BLOCKER | authorization accepted; local offboard does not match moving `DDS`, and `../communication` is absent |

All five executions ended with "no files or Git refs were changed". The local
Wave 3B offboard nested identity is deliberately separate from the published
root restore lock. Publishing/maintainer selection of a remotely recoverable
offboard commit is a follow-up and does not invalidate archive/optional path
migration.

## 5. Gate decision

| Gate | Result |
|---|---|
| archive/optional manifest migration | **PASS** |
| default excludes archive/optional | **PASS** |
| exact-SHA/canonical URL/path mutual exclusion | **PASS** |
| installer explicit selection | **PASS** |
| production allowlist/forbidden unchanged | **PASS** |
| canonical serial source/path | **REQUIRES_MAINTAINER_DECISION** |
| DDS-only wrapper | **NOT RUN BY G2** — coordinator-owned Phase 3; serial conflict must remain fail-closed |

**G2 result:** the archive/optional migration is complete and independently
validated. The serial conflict is not resolved and must not be bypassed. A
maintainer must select one exact canonical repository, path, package contract,
and disposition for the protected dirty checkout before the DDS wrapper can be
expected to pass that gate.
