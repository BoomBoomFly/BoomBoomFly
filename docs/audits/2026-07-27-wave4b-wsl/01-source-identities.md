# Source identities and recovery ledger

| Component | Branch / disposition | Exact SHA | Remote recovery |
|---|---|---|---|
| root source candidate | `wsl/wave4b-native-ready` | `1ea582b8e7fa8aff4d284cf108c9a6c7bb510b56` | pushed and GitHub commit API returned exact SHA |
| Offboard | `wsl/wave4b-offboard-latest` | `722e05afa931df4fd46aa19944830d951d68ba65` | pushed; exact API recovery |
| vision | `wsl/wave4b-vision-safety` | `b366db72cde55d9a1a7ef6bb734073fd8a43c4ae` | pushed; exact API recovery |
| px4_msgs | detached lock | `392e831c1f659429ca83902e66820d7094591410` | exact API recovery |
| communication | gitlink, `update=none` | `df256c180dbd4167f879b697e38d547521f1f8e2` | exact API recovery; not initialized in candidate |
| serial | quarantine only | `9d8c07814ad0f64f76c5fd8fe12072aebcbef431` | pushed; exact API recovery |
| Micro XRCE-DDS Agent | lock only; not run | `57d086216d01ec43121845d385894a25987f8a2c` | exact fetch/API recovery |
| PX4 | external lock; not run | `54f0455ffcd755534539a7cf33a09a20bf71d29d` (`v1.16.2`) | exact API recovery |

All checked-out candidate worktrees were clean before evidence documentation.
The original dirty native-style checkout at
`/home/aa/px4_ws/BoomBoomFly` was read only and was not copied, staged,
committed, reset, cleaned, or overwritten.

The root now has a valid `.gitmodules` mapping for `src/communication` to
`https://github.com/BoomBoomFly/communication.git`; `update=none` prevents
blind recursive initialization. Active sources are exact 40-character locks
in `workspace.lock.repos`. Serial is absent from active manifests and exists
only in `workspace.quarantine.repos`.

PX4 recovery evidence enumerates 33 locked objects: 28 isolated exact fetches
and five previously timing-out large repositories verified by the GitHub
commit API. The GitLab `libfc-sensor-api` object succeeded by exact fetch.
Thus every listed PX4 nested object is remotely present without relying on the
dirty external PX4 checkout.

Patch SHA256:

- root baseline `de3c3104…` to source candidate: `70a466efbdff8683b1f31b1293ee9f9c550d11beb427c1df9f24f07b6a29742c`
- Offboard upstream `cded3dc5…` to candidate: `9b5dfc71a4cc2b0e86ac3be8c5ffb3dbb8bca0b6382dca9115f134f2565e1530`
- vision `origin/master` to candidate: `1595d55c8c8a57554044473c04a8559018abd60c5e9af733e8c3e4e1ca57b3fd`
- serial `origin/master` to quarantine: `f733c6ddaef81c02c276bb70c3c5347495ac872e5fc7d6f66f2d7f0799ca27c2`

The source root commit-object SHA256 is
`4879639b2ad2020b7b4a3918542b8455388b4299d46e8f703f90a075d64c047e`.
