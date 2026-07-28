# Dependency source profiles

`workspace.lock.repos` is the only root repository manifest. Project-owned
flight packages follow their declared default branches so every `--update`
resolves the latest remote commit. Third-party dependencies remain locked to
exact lowercase 40-character commit SHAs.

| Profile | Selection | Repository policy |
|---|---|---|
| active | default | `offboard_cpp:DDS`, `vision_to_dds:master`; third party exact SHA |
| archive | `--with-archive` | `px4_bringup:DDS` |
| optional perception | `--with-optional perception` | exact SHA |
| optional navigation | `--with-optional navigation` | exact SHA |
| quarantine | never selected | exact recovery SHA, excluded from build |

Only these path/ref pairs may move:

```text
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

## Communication submodule

`src/communication` is the companion-computer-to-MCU communication submodule.
It follows `main` independently of the ROS source manifest. The standard
installer initializes it and checks out the latest remote commit:

```bash
bash Scripts/installation/uav_px4_dds_install.sh \
  --update \
  --skip-package-check
```

Use `--skip-submodules` only when the communication checkout is intentionally
not required.

The submodule is not a PX4 transport or ROS control package and must not publish
PX4 `/fmu/*` or control `/offboard/*` topics.

The serial driver recovery identity remains in the `quarantine` profile. The
installer never selects that profile, and the DDS-only package boundary rejects
it from the flight-control workspace.
