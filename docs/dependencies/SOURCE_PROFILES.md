# Dependency source profiles

The governed restore set is stored in one exact-SHA manifest. Profile markers
inside `workspace.lock.repos` preserve active-by-default and explicit opt-in
selection without duplicating repository identities across files.

| Profile | Manifest | Selection | Purpose |
|---|---|---|---|
| active | `workspace.lock.repos` | default | DDS-only source baseline |
| archive | `workspace.lock.repos` | `--with-archive` | provenance-only historical source |
| optional perception | `workspace.lock.repos` | `--with-optional perception` | perception source dependencies |
| optional navigation | `workspace.lock.repos` | `--with-optional navigation` | navigation and simulation source dependencies |

All entries, including an explicitly supplied custom manifest, must use an
exact lowercase 40-character commit SHA and a safe `src/` path. Paths are
globally unique across the single governed manifest. Profile flags may be combined,
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

The former non-governed moving developer index `workspace.repos` was retired
after it diverged from the root gitlink layout and exact source locks. Custom
manifests remain supported through `--manifest`, but moving branches/tags and
workspace-external targets are rejected.

Restore flags authorize source restore intent only. They do not authorize a build,
ROS launch, SITL, hardware access, firmware generation, firmware flashing, or
flight. Existing dirty repositories, origin mismatches, wrong commits, missing
repositories, duplicate paths, and non-exact refs remain fail-closed.

## Serial source decision

No serial actuator package belongs to an approved restore or production
profile. Root `.gitmodules` maps `src/communication`, whose gitlink is pinned to
`eaaae53435ce706b32ee7dffc0c6643b43a12afe`. Communication in turn maps
`Serial/serial_driver_ros` and pins it to quarantine commit
`9d8c07814ad0f64f76c5fd8fe12072aebcbef431`. Both commits are reachable from
their governed remotes and `git submodule status --recursive` resolves the
complete chain.

The serial origin, immutable SHA, path, and offline recovery source are now
governed. `COLCON_IGNORE` enforces discovery quarantine only; production
admission, maintainer ownership, protocol, authority, interlock, and runtime
safety approval remain:

```text
REQUIRES_MAINTAINER_DECISION
```

Do not add serial to production discovery, launch, or execution until that
decision is approved. The production DDS-only package allowlist and forbidden
set are unchanged.
