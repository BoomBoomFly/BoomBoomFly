#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PX4_DIR="${ROOT_DIR}/px4"
WS_DIR="${PX4_DIR}/px4_ws"
SRC_DIR="${WS_DIR}/src"

if (($# > 1)); then
  echo "usage: $0 [package-name]" >&2
  exit 2
fi

if ! command -v colcon >/dev/null 2>&1; then
  echo "error: colcon is required but was not found in PATH." >&2
  exit 1
fi

if [[ -z "${ROS_DISTRO:-}" ]]; then
  ros_setups=(/opt/ros/*/setup.bash)
  if ((${#ros_setups[@]} != 1)) || [[ ! -f "${ros_setups[0]}" ]]; then
    echo "error: set ROS_DISTRO or install exactly one ROS 2 distribution under /opt/ros." >&2
    exit 1
  fi
  set +u
  # shellcheck disable=SC1090
  source "${ros_setups[0]}"
  set -u
elif [[ -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]]; then
  set +u
  # shellcheck disable=SC1090
  source "/opt/ros/${ROS_DISTRO}/setup.bash"
  set -u
fi

cd "${WS_DIR}"
if (($# == 1)); then
  colcon build --symlink-install --base-paths "${SRC_DIR}" --packages-up-to "$1"
else
  colcon build --symlink-install --base-paths "${SRC_DIR}" --packages-up-to px4_bringup
fi
