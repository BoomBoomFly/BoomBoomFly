#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  echo "错误：请使用 source Scripts/setup_ros_environment.bash" >&2
  exit 1
fi

# 在函数内保留路径变量，不向调用 shell 注入 set -e / set -u。
_boomboomfly_setup_ros() {
  local project_root
  project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)" || return 1
  local overlay="${project_root}/ros_ws/install/local_setup.bash"
  if [[ ! -f /opt/ros/humble/setup.bash || ! -f "${overlay}" ]]; then
    echo "错误：需要 ROS 2 Humble 和已编译的 ros_ws/install/local_setup.bash。" >&2
    return 1
  fi
  source /opt/ros/humble/setup.bash || return 1
  source "${overlay}"
}

if _boomboomfly_setup_ros; then
  unset -f _boomboomfly_setup_ros
else
  unset -f _boomboomfly_setup_ros
  return 1
fi
