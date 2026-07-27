# Source identities and reproducibility ledger

All values below were locally re-verified. `origin/master` is a local tracking ref only; no fetch was performed.

| Component | Branch | HEAD | Remote / state | Disposition |
|---|---|---|---|---|
| root baseline | `master` | `de3c3104074c5b851d944cb4c757cbfa7d6ede20` | `BoomBoomFly/BoomBoomFly.git`; local `origin/master` same SHA | dedicated WSL branch made from it |
| root WSL worktree | `wsl/wave4b-20260727` | `de3c3104074c5b851d944cb4c757cbfa7d6ede20` | clean before this evidence package | candidate root only |
| `src/communication` | `main` | `df256c180dbd4167f879b697e38d547521f1f8e2` | `BoomBoomFly/communication.git`; three deletions and untracked nested serial | BLOCKED / not copied |
| nested serial | `master` | `87f3907f0b3b906d474a8d1e1dc9677ab0c4298f` | `BoomBoomFly/serial_driver_ros.git`; clean | BLOCKED / no canonical receipt |
| Offboard required by task | unavailable | `976d6217d73a28b72e64300e2dd04bcbeeee30d7` | `git cat-file -e` failed locally | BLOCKED; do not substitute |
| actual Offboard checkout | `DDS` | `cded3dc5b6906420db3767abd82b2df7ba6ea9f0` | clean; matches existing root lock | evidence only, not candidate |
| `px4_msgs` | detached | `392e831c1f659429ca83902e66820d7094591410` | PX4 origin; clean | identity only |
| PX4 | detached | `54f0455ffcd755534539a7cf33a09a20bf71d29d` | PX4 origin; three nested gitlink dirties | ungoverned; not buildable evidence |
| vision | `master` | `0c3a00137f3c90a4051ac1bc1029ec56beb669b6` | clean | ungoverned direct FMU writer |

Root contains gitlink `src/communication@df256c...` but no `.gitmodules`; `git submodule status --recursive` fails with `no submodule mapping found`.  `workspace.repos` points instead to a workspace-external `../communication`, remote `wanone111/communication.git`, moving `main`.  Existing lock hash: `workspace.lock.repos` SHA256 `365e8ecb681ee98b9c8511c7fc565362a0abc446371d893a3b8f4e87d23d2235`.

The user-specified native dirty `.gitignore` was not present in this WSL checkout.  WSL did not copy, stage, amend, or delete any native dirty content.
