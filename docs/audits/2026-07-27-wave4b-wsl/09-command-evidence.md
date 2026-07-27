# Command evidence and safety boundary

Executed only: environment identity; local Git branch/HEAD/remote/status/lock hashes; local `git cat-file` for the required SHA; static source/profile/launch/script inspection; and creation of the isolated root worktree. All commands completed without opening a device or starting a robotics process.

| Command class | Result | Safety scope |
|---|---|---|
| hostname/user/uname/ROS environment | captured | read-only |
| target repository identity/status/remote | captured | local Git only |
| `git worktree add -b wsl/wave4b-20260727 ... de3c310...` | success | dedicated Linux-native worktree; no submodule init |
| root `git submodule status --recursive` | exit 128 | expected broken mapping; no update attempted |
| Offboard `git cat-file -e 976d...^{commit}` | exit 128 | exact candidate unavailable locally |
| static source/launch/profile inspection | completed | no ROS graph or device opened |

Explicitly not run: `colcon build/test/test-result`, `ros2 run/launch`, PX4/SITL, Agent, MAVROS, serial/camera/lidar access, `/fmu/in/*` publishing, arming/mode/actuator commands, parameter writes, flash, package installation, fetch/pull/push/merge/rebase/reset/clean.

Historical Wave 4A logs are not this candidate's evidence, especially its statement about a serial `COLCON_IGNORE` marker; that marker is absent at the currently inspected serial SHA.
