#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
# 当前仅同步已存在远程仓库的自写包，不更新第三方或预留包。
for package in uav_control uav_vio_bridge uav_bringup; do
  target="${project_root}/ros_ws/src/${package}"
  url="https://github.com/BoomBoomFly/${package}.git"
  if [[ -e "${target}/.git" ]]; then
    echo "更新 ${package}（当前分支的 upstream）"
    git -C "${target}" pull --ff-only
  elif [[ -e "${target}" ]]; then
    echo "错误：${target} 已存在，但不是独立 Git 仓库；保留原目录。" >&2
    exit 1
  else
    mkdir -p "$(dirname -- "${target}")"
    git clone "${url}" "${target}"
  fi
done
