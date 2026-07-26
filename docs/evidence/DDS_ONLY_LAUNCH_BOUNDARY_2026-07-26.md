# DDS-only launch boundary

Status: **STATIC BOUNDARY ONLY — PRODUCTION DISABLED**

The launch guard parses Python with `ast` and XML with
`xml.etree.ElementTree`. It does not import launch modules, construct a
`LaunchDescription`, start a process, open a device, or execute a shell
command.

The current profile statically allowlists only
`src/offboard_cpp/launch/offboard_control.launch.py`, with one exact
`offboard_cpp/offboard_node` instance. This allowlist is not runtime
authorization: `production_enabled` is fixed to `false`.

Every other launch path observed in the current mixed source workspace is
listed exactly in `historical_denied_inventory`. A new or missing launch file
requires profile review and returns nonzero. Direct `--check-file` scans reject
dangerous historical files rather than treating their historical classification
as a pass.

## Enforced checks

- Reject MAVROS, archived PX4 bringup, mock RC, serial, RPLIDAR, RealSense,
  USB-camera, and VPU experiment launch content.
- Reject `/dev/ttyTHS0`, `/dev/ttyACM*`, and `/dev/ttyUSB*`.
- Reject automatic Micro XRCE-DDS Agent process launch.
- Inspect `Node`, `ExecuteProcess`, `IncludeLaunchDescription`, launch argument
  defaults, shell commands, and referenced YAML parameter files.
- Reject multiple statically identifiable writers to one `/fmu/in/*` topic.
- Return `REQUIRES_REVIEW` for dynamic launch content that cannot be resolved
  statically.

Exit code `0` means the static boundary passed, `1` means a denied condition or
configuration error was found, and `2` means human review is required.

No launch file was imported or run while establishing this boundary. No
hardware, PX4 parameter, firmware, or `/fmu/in/*` access was performed.
