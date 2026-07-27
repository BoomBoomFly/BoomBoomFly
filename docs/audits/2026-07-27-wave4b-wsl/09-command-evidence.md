# Command evidence and safety boundary

Executed only: environment identity; local Git branch/HEAD/remote/status/lock hashes; static source/profile/launch/script inspection; isolated-worktree creation; an approved remote `git fetch --prune origin` for Offboard and serial; and one serial discovery-only `colcon list`. All commands completed without opening a device or starting a robotics process.

| Command class | Result | Safety scope |
|---|---|---|
| hostname/user/uname/ROS environment | captured | read-only |
| target repository identity/status/remote | captured | local Git only |
| `git worktree add -b wsl/wave4b-20260727 ... de3c310...` | success | dedicated Linux-native worktree; no submodule init |
| root `git submodule status --recursive` | exit 128 | expected broken mapping; no update attempted |
| Offboard `git cat-file -e 976d...^{commit}` | exit 128 | exact candidate unavailable locally |
| static source/launch/profile inspection | completed | no ROS graph or device opened |
| approved `git fetch --prune origin` | success | Offboard default `DDS@cded...`; serial default `master@87f390...`; no pull/push/merge/rebase |
| serial `colcon list` on `9d8c078...` | exit 0, discovery 0 | package quarantine only; stdout hash is empty; generated `log/` was preserved and moved to `/tmp` |

Explicitly not run: `colcon build/test/test-result`, `ros2 run/launch`, PX4/SITL, Agent, MAVROS, serial/camera/lidar access, `/fmu/in/*` publishing, arming/mode/actuator commands, parameter writes, flash, package installation, pull/push/merge/rebase/reset/clean.

Historical Wave 4A logs are not this candidate's evidence. Its serial-marker statement was absent at upstream `87f390...`; the current marker is the separate, locally committed quarantine `9d8c078...`.
