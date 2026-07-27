# Wave 3A G1 — archive and optional dependency source-profile design

> Capture date: 2026-07-27 (Asia/Shanghai)
> Implementation level: design plus synthetic offline validator/tests
> Actual root-manifest migration: **NO**
> Result: **PASS (DESIGN ONLY)**

## 1. Scope and safety boundary

G1 defines a future exact-source split between the default active dependency
set, archived sources, and optional perception/navigation sources. The only
implementation in this wave is a pure Python standard-library validator and
synthetic fixtures under `test/dependency_profiles/`.

G1 did not modify `workspace.repos`, `workspace.lock.repos`,
`workspace.excluded_packages`, the installer, a DDS-only profile, or any nested
checkout. It did not clone, fetch, pull, restore, update, check out, migrate, or
delete a repository. The synthetic validator only reads strict JSON fixtures
and prints a proposed selection; it does not invoke Git, vcstool, colcon, or the
installer.

## 2. Current state observed before design

The current repository has two overlapping root manifests:

| File | Entries | Current role | G1 observation |
|---|---:|---|---|
| `workspace.lock.repos` | 16 | installer default | all entries use exact 40-character SHAs |
| `workspace.repos` | 17 | developer/moving source list | contains tags/branches and external `../communication@main` |

The installer's existing `--help` states that its default is
`workspace.lock.repos`. It supports a generic `--manifest` override and
`--allow-moving-refs`, but has no explicit archive or optional-profile
selection. Therefore the present CLI cannot make archive/optional intent
machine-obvious.

`src/px4_bringup` is currently present in both manifests:

| Property | Observation |
|---|---|
| origin | `https://github.com/AyasOwen/px4_bringup.git` |
| exact lock/current HEAD | `0fbdcbf6ee53d6927de75af1d98f22cf5bd4f917` |
| moving source ref | `DDS` |
| checkout state | clean branch `DDS` at capture |
| package boundary | forbidden and listed in `workspace.excluded_packages` |
| production purpose | none; archived MAVROS-era provenance only |

The indexed `src/serial_driver_ros` entry remains a gitlink at
`87f3907f0b3b906d474a8d1e1dc9677ab0c4298f`, while its directory does not
contain an independently identifiable checkout. G1 therefore preserves:

```text
src/serial_driver_ros: REQUIRES_MAINTAINER_DECISION
```

It is not admitted to active, archive, perception, or navigation profiles.
Likewise, `../communication@main` is not eligible for a governed profile until
an exact SHA, canonical placement, ownership, and restore policy are approved.

## 3. Target source-profile model

All governed profile entries must have:

- one stable repository ID;
- one repository-relative `src/...` target;
- `type: git`;
- one exact canonical HTTPS URL ending in `.git`;
- one lowercase 40-character commit SHA;
- exactly one owner profile.

The target files and selection semantics are:

| Profile | Proposed file | Selection | Policy |
|---|---|---|---|
| active | `workspace.lock.repos` | default, always | exact SHA only |
| archive | `workspace.archive.repos` | explicit `--with-archive` | exact SHA only; never production |
| optional perception | `workspace.optional-perception.repos` | explicit `--with-optional perception` | exact SHA only |
| optional navigation | `workspace.optional-navigation.repos` | explicit `--with-optional navigation` | exact SHA only |

The existing `workspace.repos` moving list must not be composed into governed
restores. A later maintainer-approved migration should either deprecate it or
clearly retain it as a non-governed developer index; it must never silently
override exact profile commits.

### 3.1 Proposed dependency ownership

This is a migration design, not an applied manifest:

| Profile | Current locked source candidates |
|---|---|
| active | `px4_msgs`, `Micro-XRCE-DDS-Agent`, `offboard_cpp`, `vision_to_dds` |
| archive | `px4_bringup` |
| optional perception | `librealsense`, `realsense-ros`, `vision_opencv` |
| optional navigation | `gazebo_ros_pkgs`, `imu_tools`, `navigation2`, `navigation_msgs`, `rplidar_ros`, `rtabmap`, `rtabmap_ros`, `slam_toolbox` |

Before migration, the coordinator must confirm that the active set closes all
DDS-only source/build dependencies on a clean restore. System ROS dependencies
do not justify silently importing an optional source profile.

## 4. Fail-closed catalog contract

The Wave 3A synthetic validator uses a strict JSON catalog. JSON syntax is a
valid YAML 1.2 subset, and using it here keeps the test independent of PyYAML
and the host `jsonschema` version.

It enforces:

1. `default_restore` is exactly `["active"]`;
2. the only profiles are `active`, `archive`,
   `optional-perception`, and `optional-navigation`;
3. every repository in every profile uses a lowercase exact SHA;
4. each repository ID resolves to one exact canonical URL;
5. active/archive/optional paths are globally mutually exclusive;
6. repository IDs are globally unique across profiles;
7. paths are safe repository-relative `src/...` targets;
8. `src/serial_driver_ros` remains an unresolved maintainer decision and
   cannot enter any restore profile.

The validator rejects a tag, branch, `latest`, abbreviated SHA, uppercase SHA,
missing canonical URL, URL substitution, duplicate ID, duplicate target,
unsafe target, implicit archive selection, and an unresolved decision path in
a restore profile.

The catalog is intentionally synthetic and does not validate the current root
manifests. A production integration must first add an approved parser/adapter
for the real profile files and test that its canonical inventory is identical
to the validator input. Synthetic PASS is not restore or supply-chain evidence.

## 5. Installer CLI design

A future installer change should expose intent directly:

```text
uav_px4_dds_install.sh [existing options]
  [--with-archive]
  [--with-optional perception]
  [--with-optional navigation]
```

Required semantics:

- no profile flag: resolve only the active exact manifest;
- `--with-archive`: add archive after validating every profile and the merged
  path/ID/URL inventory;
- `--with-optional <name>`: repeatable, allow only the two frozen names;
- validate the complete selection before creating a directory or invoking Git;
- display selected profile IDs, manifests, repository paths, URLs, and exact
  SHAs in dry-run/verify output;
- keep existing dirty-checkout protections;
- reject duplicate paths or repository IDs across the composed selection;
- reject `--allow-moving-refs` with any governed profile;
- make generic `--manifest` mutually exclusive with profile-selection flags;
- preserve nonzero exit on wrong URL, wrong HEAD, dirty checkout, missing
  manifest, or non-exact ref.

Archive and optional flags authorize source restoration only. They do not
authorize a build, launch, hardware access, production enablement, firmware
generation, or firmware flash.

## 6. Minimal `px4_bringup` archive migration

After explicit maintainer approval, the smallest safe migration is:

1. freeze the current canonical identity
   `AyasOwen/px4_bringup@0fbdcbf6ee53d6927de75af1d98f22cf5bd4f917`;
2. add that single exact entry to `workspace.archive.repos`;
3. remove the `src/px4_bringup` entry from both active root manifests in the
   same logical change;
4. keep `px4_bringup` unchanged in `workspace.excluded_packages`,
   `config/profiles/dds_only_packages.yaml`, and launch-deny inventory;
5. validate path uniqueness, URL identity, exact SHA, default-plan absence,
   explicit archive-plan presence, and current-checkout non-mutation;
6. verify that default restore/build behavior and the DDS-only production
   allowlist/forbidden set are unchanged.

Do not move or delete the current checkout as part of the manifest edit.
Checkout disposition requires a separate maintainer decision after provenance
and any user changes are reviewed.

## 7. DDS-only boundary invariants

G1 captured these files before and after its implementation:

| Protected file | SHA-256 |
|---|---|
| `workspace.repos` | `4cca7c582fc9b344a8eec2b4df47d20287693e2bc501f07364e6727dc27fb12f` |
| `workspace.lock.repos` | `043f0f07fb786cab4a2ba1ef49f75e9484e29d9cd470615776f1ce9d8eb9b5e9` |
| `workspace.excluded_packages` | `3e4babf7e68fca81d6afc4e86edc8271ddd97392c831a882b13a96e435a042f1` |
| `Scripts/installation/uav_px4_dds_install.sh` | `6ceb4248c6c2a2a9550cfb23c9ca18fa86526be222b63b532066b70e24c26c3f` |
| `config/profiles/dds_only_packages.yaml` | `5db74886c901eec86118f338dd67c126a8fab9c1ccb205ca3566f851e51f6786` |
| `config/profiles/dds_only_launch.yaml` | `ec5f06680ded075a05e860ba407580a291ea46d89a49803faf799150b7f67293` |

No diff was present for these files after G1. Consequently:

- the DDS-only production allowlist is unchanged;
- the forbidden package set is unchanged;
- the forbidden launch/topic/device patterns are unchanged;
- the default installer still uses the current full exact lock;
- no archive/optional root manifest exists yet;
- no actual dependency migration occurred.

## 8. Synthetic validation results

Command:

```bash
python3 -m unittest discover \
  -s test/dependency_profiles \
  -p 'test_*.py' \
  -v
```

Result: **10 tests, 10 passed, 0 failed**.

Direct CLI outcomes:

| Fixture/selection | Expected | Observed |
|---|---|---|
| valid default | only `active` / `src/px4_msgs` | exit `0`, PASS |
| explicit archive + both optional profiles | active plus three explicit profiles | unit PASS |
| archive ref `DDS` | reject moving ref | exit `1`, FAIL |
| archive path duplicates active path | reject global path collision | exit `1`, FAIL |
| archive URL differs from canonical URL | reject URL substitution | exit `1`, FAIL |
| optional ref `main` | reject moving ref | unit PASS |
| duplicate repository ID | reject duplicate identity | unit PASS |
| unresolved serial-driver path added to a profile | reject admission | unit PASS |

The tests are offline policy tests. They are not proof that vcstool restored a
source tree, that the current 16 entries were migrated, or that a DDS-only
build passed.

## 9. Gate result and next approval point

| Gate | Result |
|---|---|
| exact-SHA archive/profile policy design | **PASS** |
| default excludes archive/optional | **PASS (SYNTHETIC)** |
| moving archive ref rejected | **PASS (SYNTHETIC)** |
| path duplicate rejected | **PASS (SYNTHETIC)** |
| URL mismatch rejected | **PASS (SYNTHETIC)** |
| DDS-only allowlist/forbidden set unchanged | **PASS** |
| `serial_driver_ros` decision preserved | **PASS** |
| installer archive/optional flags implemented | **NOT_APPLICABLE — DESIGN ONLY** |
| root-manifest migration | **NOT_APPLICABLE — NOT PERFORMED** |
| `px4_bringup` migration | **NOT_APPLICABLE — NOT PERFORMED** |

**G1 final status: PASS (DESIGN ONLY). Actual manifest migration: NO.**
Maintainer approval and a coordinator-owned root-manifest change remain
required before the synthetic contract may be integrated into restore logic.
