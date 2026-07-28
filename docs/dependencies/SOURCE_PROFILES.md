# Dependency source profiles

The governed restore set is split into four exact-SHA manifests. Only the
active profile is selected by default.

| Profile | Manifest | Selection | Purpose |
|---|---|---|---|
| active | `workspace.lock.repos` | default | DDS-only source baseline |
| archive | `workspace.archive.repos` | `--with-archive` | provenance-only historical source |
| optional perception | `workspace.optional-perception.repos` | `--with-optional perception` | perception source dependencies |
| optional navigation | `workspace.optional-navigation.repos` | `--with-optional navigation` | navigation and simulation source dependencies |

All entries, including an explicitly supplied custom manifest, must use an
exact lowercase 40-character commit SHA and a safe `src/` path. Paths are
globally unique across the selected manifests. Profile flags may be combined,
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
profile. The current root index records
`src/communication@df256c180dbd4167f879b697e38d547521f1f8e2` as a gitlink
without a matching `.gitmodules` entry. That protected dirty communication
checkout contains an untracked nested repository at
`src/communication/Serial/serial_driver_ros@87f3907f0b3b906d474a8d1e1dc9677ab0c4298f`.

The WSL Wave 4B handoff also records a separate local quarantine commit
`9d8c078...`; it is not advertised by the recorded serial remote and is not
recoverable from the supplied manifests. `COLCON_IGNORE` proves package
discovery isolation only, not source governance or runtime safety. The
canonical origin, immutable SHA, path, production disposition, maintainer,
protocol, and offline recovery source remain:

```text
REQUIRES_MAINTAINER_DECISION
```

Do not delete, move, rename, stage, or use either protected dirty checkout to
make a restore/build validator pass. Do not add serial to production discovery,
launch, or execution until the decision is approved. The production DDS-only
package allowlist and forbidden set are unchanged.
