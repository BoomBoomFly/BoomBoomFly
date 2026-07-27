# Wave 3B A2 — PX4 exact source and toolchain provenance

> Capture time: 2026-07-27T16:24:42+08:00
> Capture mode: local read-only inspection, except for this report
> Result: **BLOCKED** — no verifiable PX4-Autopilot source checkout is
> available, and the firmware toolchain is not closed

## 1. Scope and safety boundary

A2 independently rechecked the Wave 3A A1 conclusion. It did not use the
network, clone, fetch, download, generate messages, build PX4, run SITL, start
ROS/PX4/Micro XRCE-DDS processes, inspect hardware, write a parameter, create
an artifact, or flash firmware. No manifest, lock, nested checkout, historical
audit, or protected dirty checkout was modified.

The repository was resolved dynamically and observed as:

| Item | Observation |
|---|---|
| root | `/home/c/BoomBoomFly` |
| branch | `agent/wave3b-integration-gates` |
| HEAD | `afb4fdcecb22596056432492d1ad284919b065cd` |
| protected pre-existing checkout | `src/serial_driver_ros2/` remained untracked and untouched |

The root also contained the coordinator-created untracked Wave 3B audit
directory during this capture.

## 2. PX4 source inventory

### 2.1 Managed candidates

All three managed candidates were absent:

| Candidate | Result |
|---|---|
| `PX4-Autopilot` | missing |
| `src/PX4-Autopilot` | missing |
| `../PX4-Autopilot` | missing |

Neither `workspace.lock.repos` nor `workspace.repos` contains a
PX4-Autopilot entry. The exact-source lock remains the intentionally
unverified template
`docs/evidence/environment/px4_source_toolchain_lock.template.json`, whose
source fields are null and whose submodule list is empty.

### 2.2 Bounded local recheck

A bounded read-only search inspected Git origins and source signatures under
`/home/c` and `/tmp`, to maximum depths 7 and 12 respectively. It found no Git
origin containing `PX4-Autopilot`, no
`src/modules/uxrce_dds_client/dds_topics.yaml`, and no `.px4` firmware
artifact. The only `msg/RcChannels.msg` found was the locked ROS-side file:

```text
/home/c/BoomBoomFly/src/px4_msgs/msg/RcChannels.msg
```

A second signature search under `/opt`, `/usr/local/src`, and `/srv` found no
match. It could not read `/opt/containerd`. Several system-private `/tmp`
directories were also unreadable. This is therefore not a whole-host absence
claim. It is sufficient to establish that no approved managed checkout or
verifiable candidate was presented to A2.

Earlier audit text names
`54f0455ffcd755534539a7cf33a09a20bf71d29d` as an intended PX4 v1.16.2
candidate. No local PX4 Git object, canonical origin, tag object, or recursive
submodule inventory ties that text to source in this evidence set. It remains
an unverified candidate and is not promoted to a lock.

### 2.3 Source provenance result

The following required facts cannot be derived without the source repository:

- canonical PX4-Autopilot origin;
- exact checked-out source commit;
- the PX4 `v1.16.2` tag object and its peeled commit;
- every recursive submodule path, origin, and exact SHA;
- source-side message definitions and metadata-generation workflow;
- the baseline `dds_topics.yaml`;
- uXRCE-DDS message/type generator source and configuration;
- board configuration, NuttX/compiler constraints, and exact build target.

**PX4 source provenance: BLOCKED.**

## 3. Exact local `px4_msgs` identity

The ROS message side is locally verifiable:

| Property | Exact observation |
|---|---|
| origin | `https://github.com/PX4/px4_msgs.git` |
| checkout | detached, clean |
| HEAD | `392e831c1f659429ca83902e66820d7094591410` |
| commit parent | `18f0b7872345c798225487d53f8bdb1c06c0d01c` |
| commit time | `2025-08-07T20:13:41+01:00` |
| annotated tag object | `v1.16.2` = `bcade9dd878bbdbc9cefb20b0fee41c2eca3cd09` |
| peeled tag commit | `392e831c1f659429ca83902e66820d7094591410` |
| `msg` tree | `ff5176c2d2dbb335460c97eaf0c9d6a1f6c2afc4` |
| message file count | 226 |
| `RcChannels.msg` blob | `b932dfd33b15c8c220e5219dd75ddca857818195` |

The tag object contains an SSH signature and states that the messages match
PX4 stable release 1.16.2. A2 proved the local tag-to-commit relationship, but
did not have an approved signer trust policy with which to promote that
statement into PX4-Autopilot source provenance. The tag is exact
`px4_msgs` evidence, not a substitute for the missing PX4 source commit.

Selected B/C integration message blobs at the same exact commit are:

| Message | Git blob |
|---|---|
| `RcChannels.msg` | `b932dfd33b15c8c220e5219dd75ddca857818195` |
| `VehicleCommand.msg` | `96162e9f89f9e784db63f2a4a7a5f047fd997637` |
| `VehicleCommandAck.msg` | `c11a5f8c5dfdc0dbcbe10e504a812eb31046a868` |
| `VehicleStatus.msg` | `0a94fde86c896b8ce55078105c4c4eb96a5d4820` |
| `OffboardControlMode.msg` | `885164a652cb758c7672da2aea96f0cad5750149` |
| `TrajectorySetpoint.msg` | `150be404b94fddd63beaee85d22a94f88b3ff93c` |

`workspace.lock.repos` pins this exact `px4_msgs` commit. The moving/restoration
manifest uses the release tag, but the exact lock is the full commit above.

## 4. Source-to-message field comparison

The locked ROS-side `RcChannels` payload order is:

| Order | Field | Locked ROS type/shape | PX4 source comparison |
|---:|---|---|---|
| 1 | `timestamp` | `uint64` | **BLOCKED — source absent** |
| 2 | `timestamp_last_valid` | `uint64` | **BLOCKED — source absent** |
| 3 | `channels` | `float32[18]` | **BLOCKED — source absent** |
| 4 | `channel_count` | `uint8` | **BLOCKED — source absent** |
| 5 | `function` | `int8[29]` | **BLOCKED — source absent** |
| 6 | `rssi` | `uint8` | **BLOCKED — source absent** |
| 7 | `signal_lost` | `bool` | **BLOCKED — source absent** |
| 8 | `frame_drop_count` | `uint32` | **BLOCKED — source absent** |

The local file also defines function indices 0 through 28 and
`FUNCTION_FLTBTN_SLOT_COUNT=6`. Those constants are exact on the
`px4_msgs` side. No field, constant, ordering, version, serialization, or
generated-type equality with PX4-Autopilot can be claimed until the
source-side `msg/RcChannels.msg` is read from the approved exact source.

The same limitation applies to the other 225 ROS message files. A repository
tag string or a message-sync statement cannot replace a field-level
source-tree comparison.

## 5. Generator and DDS profile identity

Two distinct generator layers must not be conflated:

1. The local ROS package builds its checked-in `.msg` files through
   `rosidl_generate_interfaces`. Its observed dependencies are:

   | Package | Installed version |
   |---|---|
   | `ros-foxy-rosidl-default-generators` | `1.0.1-1focal.20230527.052209` |
   | `ros-foxy-rosidl-generator-c` | `1.3.1-1focal.20230527.050858` |
   | `ros-foxy-rosidl-generator-cpp` | `1.3.1-1focal.20230527.051037` |
   | `ros-foxy-rosidl-typesupport-fastrtps-c` | `1.0.4-1focal.20230527.051617` |
   | `ros-foxy-rosidl-typesupport-fastrtps-cpp` | `1.0.4-1focal.20230527.051412` |

2. The PX4 metadata/message synchronization and uXRCE-DDS endpoint generation
   live with the missing PX4 source. Their workflow commit, scripts, inputs,
   generator binary/module versions, generated type identity, and output
   hashes are **BLOCKED**.

No `dds_topics.yaml` was found in the inspected local candidates. Therefore
the default topic profile, any proposed `rc_channels` profile, direction,
generated DataWriter/type name, producer QoS, and baseline-topic regression
cannot be verified. A2 did not create a profile or generation output.

## 6. Host and toolchain observation

The host can be identified, but it is not an immutable PX4 toolchain lock:

| Item | Observation | A2 conclusion |
|---|---|---|
| OS | Ubuntu 20.04.6 LTS; Linux `5.10.104-tegra`; `aarch64` | observed host only |
| Python | `/usr/bin/python3`; 3.8.10; package `python3.8=3.8.10-0ubuntu1~20.04.18`; SHA-256 `330ad6775d2db4d95524b249d38e14b9046672b8468fa6fbf7f89b7c683d1f6b` | observed, PX4 Python requirements unavailable |
| CMake | `/usr/bin/cmake`; 3.16.3; package `3.16.3-1ubuntu1.20.04.1`; SHA-256 `6f4d31b3c0a427e33d331104639efe143428d401d405e2df0937df2c0571de47` | observed |
| Ninja | `/home/c/.local/bin/ninja`; reported `1.11.1.git.kitware.jobserver-1`; Python distribution `ninja==1.11.1.1`, installed by pip; launcher SHA-256 `a73e9e61adce6958e9ff6c19d58ff783c73ce7e2528fb3beb427d13744a1833a` | observed; no direct-url metadata |
| host GCC | `/usr/bin/gcc`; 9.4.0; target `aarch64-linux-gnu`; package `gcc-9=9.4.0-1ubuntu1~20.04.2`; SHA-256 `b7572dab602cd7a01a1a5b43dfa41d78a0c3b13e1ee77b21948eedbed0bd3ab1` | host compiler only |
| host G++ | `/usr/bin/g++`; 9.4.0; target `aarch64-linux-gnu`; package `g++-9=9.4.0-1ubuntu1~20.04.2`; SHA-256 `31b78d51d2b088dd3496337656d3bdd177b1a0d008fff4799fa4ee26777f8648` | host compiler only |
| ARM GCC/G++ | `arm-none-eabi-gcc` and `arm-none-eabi-g++` absent from PATH, both lookup exit 1 | **BLOCKED** |
| immutable toolchain/container | lock template value is null | **BLOCKED** |
| board target | runbook offers `px4_fmu-v3_default` or a maintainer-approved actual target | planned choice, not an approved source/toolchain identity |

The exact PX4 source is also needed to determine its supported Python modules,
compiler constraints, NuttX toolchain/submodules, board configuration, and
generator dependencies. No build was attempted.

### Corrected bwrap result

Bubblewrap is available as the `bwrap` executable:

```text
command -v bwrap                 exit 0, stdout /usr/bin/bwrap
/usr/bin/bwrap --version         exit 0, stdout bubblewrap 0.4.0
```

The real minimum capability probe was:

```text
/usr/bin/bwrap --ro-bind / / --proc /proc --dev /dev \
  --unshare-all --die-with-parent /bin/true
```

It returned exit `0` with empty stderr. The earlier Codex launcher exit 101
claiming no `bwrap` was a launcher failure and is not evidence that the host
lacks Bubblewrap. A2 is not blocked by Bubblewrap.

## 7. Gate classification

| Gate | Classification | Reason |
|---|---|---|
| exact local `px4_msgs` origin/commit/tag/tree | **PASS** | origin, clean detached SHA, annotated tag object and peeled commit observed |
| exact PX4-Autopilot origin/commit/tag | **EXPECTED BLOCKER** | no approved managed source checkout |
| recursive PX4 submodule origin/SHA inventory | **EXPECTED BLOCKER** | source absent |
| PX4-to-`px4_msgs` field equality | **EXPECTED BLOCKER** | only ROS-side definitions are available |
| PX4 message/DDS generator identity | **EXPECTED BLOCKER** | source scripts and generator inputs absent |
| baseline/custom `dds_topics.yaml` | **EXPECTED BLOCKER** | no local profile found |
| host tool identity | **PASS (OBSERVATION ONLY)** | versions, packages, paths, and selected binary hashes recorded |
| immutable PX4 toolchain and ARM compiler | **EXPECTED BLOCKER** | no immutable digest; ARM cross-compiler absent |
| board/toolchain identity | **EXPECTED BLOCKER** | planned FMUv3 target is not an approved lock |
| bwrap executable and sandbox capability | **PASS** | real executable/version/probe all returned zero |
| source/profile generation, build, SITL, flash | **NOT APPLICABLE** | outside A2 authorization and prerequisites absent |

**A2 final result: BLOCKED.** No source/toolchain lock proposal is justified,
and no lock file was created or modified.

## 8. Minimum offline recovery/import plan

The smallest safe recovery path is:

1. A maintainer approves the canonical PX4-Autopilot origin, exact 40-hex
   v1.16.2 commit, and board target. The unverified SHA copied in older audit
   text is not approval.
2. Provide an offline Git bundle or read-only checkout containing the source
   commit, annotated release tag object, and history needed to verify the
   tag-to-commit relationship. Record the bundle/content SHA-256 before import.
3. Provide every recursive submodule as exact Git objects plus a manifest of
   path, canonical origin, and 40-hex commit. Do not run `submodule update`
   against the network.
4. Provide an immutable PX4 toolchain image/archive with a verified digest, or
   an equivalently exact offline package lock including ARM GCC/G++, Python
   dependencies, CMake, Ninja, NuttX tooling, and host architecture.
5. In a separate managed checkout, verify Git object integrity, origin,
   `v1.16.2^{commit}`, recursive submodules, board configuration,
   source-side messages, metadata workflow/generator identity, and baseline
   `dds_topics.yaml`.
6. Compare every source message used by the DDS profile against the locked
   `px4_msgs` files field by field. Only after all identities agree may A2
   propose a non-template lock. Generation/build/SITL and any firmware
   artifact remain later, separately authorized gates.

This plan imports approved offline material only; it does not authorize
download, build, flash, or hardware access.

## 9. Read-only command ledger

Representative commands actually executed for this report were:

```text
git rev-parse --show-toplevel
git rev-parse HEAD
git branch --show-current
git status --short --branch
git -C src/px4_msgs remote -v
git -C src/px4_msgs rev-parse HEAD
git -C src/px4_msgs status --short --branch
git -C src/px4_msgs rev-parse 'v1.16.2^{commit}'
git -C src/px4_msgs show-ref --tags -d
git -C src/px4_msgs cat-file -p refs/tags/v1.16.2
git -C src/px4_msgs rev-parse HEAD:msg
git -C src/px4_msgs hash-object msg/RcChannels.msg
git -C src/px4_msgs ls-tree -r --name-only HEAD msg
find /home/c /tmp -maxdepth 12 -type f <source-signature predicates>
find /opt /usr/local/src /srv -maxdepth 12 -type f <source-signature predicates>
grep -n PX4-Autopilot workspace.lock.repos workspace.repos
dpkg-query -W <tool and rosidl packages>
python3 -VV
cmake --version
ninja --version
gcc -dumpfullversion -dumpversion
gcc -dumpmachine
g++ -dumpfullversion -dumpversion
g++ -dumpmachine
sha256sum <observed host tool paths>
command -v bwrap
/usr/bin/bwrap --version
/usr/bin/bwrap --ro-bind / / --proc /proc --dev /dev --unshare-all \
  --die-with-parent /bin/true
```

Search stderr and exit codes were captured during execution. The inaccessible
paths are disclosed in section 2.2; the successful Bubblewrap probe had empty
stderr as recorded above.
