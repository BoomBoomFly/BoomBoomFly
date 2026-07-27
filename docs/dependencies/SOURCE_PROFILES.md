# Dependency source profiles

The governed restore set is split into four exact-SHA manifests. Only the
active profile is selected by default.

| Profile | Manifest | Selection | Purpose |
|---|---|---|---|
| active | `workspace.lock.repos` | default | DDS-only source baseline |
| archive | `workspace.archive.repos` | `--with-archive` | provenance-only historical source |
| optional perception | `workspace.optional-perception.repos` | `--with-optional perception` | perception source dependencies |
| optional navigation | `workspace.optional-navigation.repos` | `--with-optional navigation` | navigation and simulation source dependencies |

All governed entries use an exact lowercase 40-character commit SHA. Paths
are globally unique across the four manifests. Profile flags may be combined,
but they cannot be combined with the generic `--manifest` option.

Examples:

```bash
# Active exact profile only.
bash Scripts/installation/uav_px4_dds_install.sh \
  --verify-only --skip-package-check

# Add archived provenance explicitly.
bash Scripts/installation/uav_px4_dds_install.sh \
  --verify-only --skip-package-check --with-archive

# Add both optional profiles explicitly.
bash Scripts/installation/uav_px4_dds_install.sh \
  --verify-only --skip-package-check \
  --with-optional perception --with-optional navigation
```

`workspace.repos` is a non-governed moving developer index for active sources.
It is never selected by default. A caller must supply both an explicit custom
manifest and moving-ref authorization:

```bash
bash Scripts/installation/uav_px4_dds_install.sh \
  --manifest workspace.repos --allow-moving-refs \
  --verify-only --skip-package-check
```

The flags authorize source restore intent only. They do not authorize a build,
ROS launch, SITL, hardware access, firmware generation, firmware flashing, or
flight. Existing dirty repositories, origin mismatches, wrong commits, missing
repositories, duplicate paths, and non-exact governed refs remain fail-closed.

## Serial source decision

Neither `src/serial_driver_ros` nor `src/serial_driver_ros2` belongs to a
restore profile. The root index contains a legacy `src/serial_driver_ros`
gitlink, while the existing protected `src/serial_driver_ros2/` is a separate
dirty untracked checkout. The canonical serial source and path remain:

```text
REQUIRES_MAINTAINER_DECISION
```

Do not delete, move, rename, stage, or use the protected checkout to make a
restore/build validator pass. The production DDS-only package allowlist and
forbidden set are unchanged by the profile migration.
