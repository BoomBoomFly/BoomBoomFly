# Dependency source profiles

`workspace.lock.repos` is the only root repository manifest. Project-owned
flight packages follow their declared default branches so every `--update`
resolves the latest remote commit. Third-party dependencies remain locked to
exact lowercase 40-character commit SHAs.

| Profile | Selection | Repository policy |
|---|---|---|
| active | default | `offboard_cpp:DDS`, `vision_to_dds:master`, `communication:main`; third party exact SHA |
| archive | `--with-archive` | `px4_bringup:DDS` |
| optional perception | `--with-optional perception` | exact SHA |
| optional navigation | `--with-optional navigation` | exact SHA |
| quarantine | never selected | exact recovery SHA, excluded from build |

Only these path/ref pairs may move:

```text
src/communication -> main
src/offboard_cpp  -> DDS
src/vision_to_dds -> master
src/px4_bringup   -> DDS
```

All other manifest entries, including custom entries, require an exact commit
SHA and a safe path below `src/`. Paths are globally unique. Profile flags may
be combined, but cannot be combined with `--manifest`.

Update the active flight packages and selected perception dependencies:

```bash
bash Scripts/installation/uav_px4_dds_install.sh \
  --with-optional perception \
  --update \
  --skip-package-check
```

Add the latest `px4_bringup` archive checkout:

```bash
bash Scripts/installation/uav_px4_dds_install.sh \
  --with-archive \
  --update \
  --skip-package-check
```

Audit existing checkouts without changing them:

```bash
bash Scripts/installation/uav_px4_dds_install.sh \
  --with-optional perception \
  --verify-only \
  --skip-package-check
```

The installer rejects dirty repositories, origin mismatches, duplicate or
external paths, unapproved moving refs and mismatched commits. Profile
selection only restores source; it does not build packages or start ROS,
simulation, DDS Agent or hardware processes.

## Communication checkout

`src/communication` is the companion-computer-to-MCU communication repository.
It is not stored in the root Git tree. The active root manifest and standard
installer create it from the latest `main` commit:

```bash
bash Scripts/installation/uav_px4_dds_install.sh \
  --update \
  --skip-package-check
```

The checkout is not a PX4 transport or ROS control package and must not publish
PX4 `/fmu/*` or control `/offboard/*` topics.

The serial driver recovery identity remains in the `quarantine` profile. The
installer never selects that profile, and the DDS-only package boundary rejects
it from the flight-control workspace.
