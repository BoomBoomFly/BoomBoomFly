# DDS-only package boundary — 2026-07-26

Status: `current` for static package selection; no launch or hardware action was
performed.

## Decision

The authoritative production package allowlist is exactly:

- `px4_msgs` at `src/px4_msgs`
- `offboard_cpp` at `src/offboard_cpp`
- `vision_to_dds` at `src/vision_to_dds`

The machine-readable authority is
`config/profiles/dds_only_packages.yaml`. It classifies 81 package names and
relative paths: three production packages, the 13 names in
`workspace.excluded_packages`, and 65 managed non-production packages.
`test_mavros` is classified as forbidden but is intentionally absent from
normal colcon discovery because its source contains a discovery barrier.

The selection was re-established from the current `workspace.lock.repos`,
`workspace.repos`, `workspace.excluded_packages`, current package manifests,
`colcon list`, and the package dependency graph. The current workspace graph
for the production set is:

```text
px4_msgs -> offboard_cpp
px4_msgs -> vision_to_dds
```

Dependencies supplied by the ROS/system underlay are not added to the
workspace production allowlist.

## Enforcement

`Scripts/test/verify_package_boundary.py` fails closed when:

- a profile entry is missing, duplicated, unsafe, or has a path/name mismatch;
- the forbidden profile and `workspace.excluded_packages` differ;
- an allowlisted package is absent;
- full workspace discovery returns an unknown package or a known package at a
  different path;
- authoritative discovery from the three explicit package paths differs from
  the allowlist;
- an allowlisted package directly or transitively names a non-allowlisted
  workspace package dependency.

Historical and support sources remain available for recovery and provenance.
Their presence under `src/` does not authorize them: the build and test
wrappers use exact `--paths` and `--packages-select` values read from the
profile. MAVROS, old PX4 bringup, serial experiments, RPLIDAR, RealSense,
navigation, Gazebo, USB/VPU experiments, Micro XRCE-DDS Agent, and other
non-production packages cannot enter the authoritative build plan.

## Entry points

```bash
bash Scripts/build/build_dds_only.sh \
  --output-root /tmp/boomboomfly_wave1_validation

bash Scripts/test/test_dds_only.sh \
  --output-root /tmp/boomboomfly_wave1_validation
```

Both wrappers derive the repository with `git rev-parse`, accept explicit
workspace/profile/output paths, require every output path to resolve below
`/tmp`, and print a structured final summary. They do not start ROS nodes,
launch files, Micro XRCE-DDS Agent, PX4, or hardware.

## Static validation

The package-boundary tests create synthetic workspaces only below `/tmp`.
They include positive validation and negative cases for forbidden allowlist
injection, indirect forbidden dependency, missing package, direct disallowed
dependency, new unclassified package, authoritative discovery leakage, and
excluded/profile drift.

The core build is intentionally separate from the static boundary decision.
Its logs and build/install/test-result trees must be recorded under the
caller-selected `/tmp` output root. Missing ROS/colcon dependencies are
reported as blockers, never converted to success.

## Limitations

- This boundary does not make any launch safe; the independent launch guard is
  authoritative for launch actions.
- It does not remove or modify historical source directories.
- The current complete package inventory includes packages inside retained
  dirty checkouts. Any package addition, removal, or path change therefore
  requires an explicit profile review.
- Existing package tests, including known `vision_to_dds` lint status, are not
  weakened by this change. `test_dds_only.sh` returns nonzero on a package test
  failure.
