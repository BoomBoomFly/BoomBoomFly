#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
target="${project_root}/ros_ws/src/uav_control"
readonly url="https://github.com/BoomBoomFly/uav_control.git"

# 当前仅同步已存在远程仓库的自写包，不更新第三方或预留包。
if [[ -e "${target}/.git" ]]; then
  echo "更新 uav_control（当前分支的 upstream）"
  git -C "${target}" pull --ff-only
elif [[ -e "${target}" ]]; then
  echo "错误：${target} 已存在，但不是独立 Git 仓库；保留原目录。" >&2
  exit 1
else
  mkdir -p "$(dirname -- "${target}")"
  git clone "${url}" "${target}"
fi
