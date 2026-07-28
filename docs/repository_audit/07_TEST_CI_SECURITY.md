# 测试、CI、依赖、安全与可复现性

## 本轮实际执行

仅执行静态、无硬件验证：

| 检查 | 结果 |
|---|---|
| `verify_h0_production.py` | FAIL，exit 2，缺 production SafetyGateAdapter |
| `verify_package_boundary.py` | PASS，75 full discovery / 3 authoritative |
| `verify_serial_quarantine.py` | PASS，serial discovery/production refs 均为 0 |
| build/colcon test | NOT RUN |
| formal SITL | NOT RUN |
| hardware/HIL | NOT AUTHORIZED |

历史 WSL receipt 记录 14,598 tests 和 H2/H3 通过，但绑定锁定的 Offboard/vision
SHA，不适用于当前 checkout。

## [P2-CI-001] CI 仅手工触发且假设 runner 已安装 bubblewrap

- 严重度：P2
- 状态：已确认
- 领域：Test / Security / Build
- 位置：
  - `.github/workflows/wave3b-offline-gates.yml:3-5`
  - `.github/workflows/wave3b-offline-gates.yml:17-31`
- 证据：
  - workflow 只有 `workflow_dispatch`，没有 `pull_request`/`push`。
  - 在运行 gate 前直接 `command -v bwrap`，没有安装或版本锁。
  - 本审查环境因 bwrap 不可用，常规 sandbox command 不能启动；CI runner 是否预装未联网确认。
- 影响：
  - PR/merge 不会自动执行安全门；runner 镜像变化可使所有 job 在业务检查前失败。
- 根因：
  - CI 设计为离线手动证据工作流，而非 required merge gate。
- 建议：
  - 在安全审核后增加 PR/push 触发和 required status。
  - 用固定 container/image 或显式、校验版本的 bwrap provisioning。
- 前置条件：
  - GitHub branch protection 管理权限；不能仅修改 YAML 就声称 required。
- 是否涉及硬件：
  - 否

## [P2-REPRO-001] 系统/ROS 依赖没有形成可重放锁

- 严重度：P2
- 状态：已确认
- 领域：Build / Security / Test
- 位置：
  - `Scripts/installation/uav_px4_dds_install.sh:490-593`
  - `Scripts/README.md:61-90`
  - `docs/evidence/environment/current_environment.json:263-265`
- 证据：
  - source manifest 使用 exact Git SHA，这是正向控制。
  - installer 明确只管理源码，不安装 ROS/系统包/udev/firmware。
  - environment evidence 明确不是 apt snapshot、rosdep resolution lock 或 container digest。
  - 未发现 Dockerfile/devcontainer/apt lock。
- 影响：
  - 相同 source SHA 在不同 apt/ROS/CMake/Python 环境可能得到不同结果。
- 根因：
  - 源码治理已建立，host/toolchain 治理尚停留在 inventory。
- 建议：
  - 固定 OS/arch、ROS repo snapshot、apt package versions、rosdep resolution、
    Python/CMake/colcon 和 compiler identity；产出 SBOM/lock digest。
- 前置条件：
  - 明确 native ARM64 与 WSL/x86_64 是否各自为受支持平台。
- 是否涉及硬件：
  - 否

## [P3-TEST-001] Production 热路径缺少 sanitizer/coverage/静态分析门

- 严重度：P3
- 状态：已确认
- 领域：Test / Code
- 位置：
  - `src/offboard_cpp/CMakeLists.txt:4-9,79-110`
  - `src/vision_to_dds/CMakeLists.txt:9-16,44-53`
  - `.github/workflows/wave3b-offline-gates.yml:9-116`
- 证据：
  - 有 `-Wall -Wextra -Wpedantic`、gtest、ament lint 和大量 Python governance tests。
  - 未见 ASan/UBSan/TSan、clang-tidy/cppcheck 或 coverage job。
  - 串口 odd-length 越界与 Offboard 未初始化状态适合由 sanitizer 捕获。
- 影响：
  - UB、越界和长期内存增长可能在普通单测中漏检。
- 根因：
  - 测试重点是 governance/fail-closed contract，低层 memory/concurrency gate 较弱。
- 建议：
  - Phase 1 添加 isolated ASan/UBSan；TSan 用于未来多线程 executor；coverage 只作趋势指标。
- 前置条件：
  - 先对齐 exact source，避免对错误 checkout 建立基线。
- 是否涉及硬件：
  - 否

## 安全与供应链正向事实

- workflow `permissions: contents: read`。
- `actions/checkout` 和 `actions/upload-artifact` 均固定 immutable commit SHA。
- exact Git source lock 使用 40 字符 SHA；未发现 moving branch 用于 production manifest。
- 静态凭据搜索未发现 `.env`、私钥、证书、p12/pfx、SSH key 或非 fixture 的
  明显 token/password candidate；未打印任何疑似值。
- 未发现 CI 启动 hardware launch；offline gate contract 明确禁止 `/dev`、
  `ros2 launch` 与控制端点。

## 测试覆盖边界

- 有 unit/governance、launch guard、package boundary、authority、receipt、SITL
  schema/timeline synthetic tests。
- 没有本轮当前 SHA 的 clean build、ROS node integration、formal PX4 SITL 或 HIL。
- synthetic SITL fixtures 不能作为 PX4 SITL evidence。
