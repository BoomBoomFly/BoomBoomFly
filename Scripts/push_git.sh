#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ $# != 2 || -z "${2//[[:space:]]/}" ]]; then
  echo "用法：$0 {main|uav_control|uav_vio_bridge|uav_bringup|uav_mission} \"提交说明\"" >&2
  exit 1
fi

case "$1" in
  main) target="${project_root}" ;;
  uav_control|uav_vio_bridge|uav_bringup|uav_mission) target="${project_root}/ros_ws/src/$1" ;;
  *) echo "错误：未知仓库 $1" >&2; exit 1 ;;
esac

# 显式检查独立仓库，防止 Git 向上查找误用父仓库。
[[ -e "${target}/.git" ]] || { echo "错误：${target} 不是独立 Git 仓库。" >&2; exit 1; }
branch="$(git -C "${target}" symbolic-ref --quiet --short HEAD)" || {
  echo "错误：当前处于 detached HEAD。" >&2; exit 1;
}
git -C "${target}" remote get-url origin >/dev/null

if [[ "$1" == main ]]; then
  excluded=(ros_ws/src/uav_control ros_ws/src/uav_vio_bridge ros_ws/src/uav_bringup ros_ws/src/uav_mission ros_ws/src/thirdparty ros_ws/upstream
            ros_ws/build ros_ws/install ros_ws/log references reference docker/kalibr/source)
  paths=(.)
  for path in "${excluded[@]}"; do
    # 不自动取消用户的暂存；有越界暂存时在任何修改前停止。
    if ! git -C "${target}" diff --cached --quiet -- "${path}"; then
      echo "错误：暂存区包含独立仓库或第三方路径 ${path}，请先自行处理。" >&2
      exit 1
    fi
    paths+=(":(exclude)${path}")
  done
  git -C "${target}" add -A -- "${paths[@]}"
else
  git -C "${target}" add -A
fi

git -C "${target}" diff --cached --check
if git -C "${target}" diff --cached --quiet; then
  echo "没有新改动，直接推送已有提交"
else
  git -C "${target}" commit -m "$2"
fi
# 不自动 pull 或 force；推送失败时保留本地提交，供处理后重试。
git -C "${target}" -c push.followTags=false push --set-upstream origin "HEAD:refs/heads/${branch}"
