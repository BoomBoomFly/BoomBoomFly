#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
# 默认同步自写独立仓库；可显式选择一个或多个范围。
if [[ $# == 0 ]]; then
  set -- uav_ws uav_control uav_vio_bridge uav_bringup uav_mission swarm_ws ugv_ws
fi
# 先验证全部范围，避免拼写错误前已经执行部分同步。
for repository in "$@"; do
  case "${repository}" in
    uav_control|uav_vio_bridge|uav_bringup|uav_mission|uav_ws|swarm_ws|ugv_ws) ;;
    *) echo "错误：未知仓库 ${repository}" >&2; exit 1 ;;
  esac
done
for repository in "$@"; do
  case "${repository}" in
    uav_ws|swarm_ws|ugv_ws) target="${project_root}/${repository}" ;;
    *) target="${project_root}/uav_ws/src/${repository}" ;;
  esac
  url="https://github.com/BoomBoomFly/${repository}.git"
  if [[ -e "${target}/.git" ]]; then
    echo "更新 ${repository}（当前分支的 upstream）"
    git -C "${target}" pull --ff-only
  elif [[ -e "${target}" ]]; then
    echo "错误：${target} 已存在，但不是独立 Git 仓库；保留原目录。" >&2
    exit 1
  else
    mkdir -p "$(dirname -- "${target}")"
    git clone "${url}" "${target}"
  fi
done
