#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PX4_DIR="${ROOT_DIR}/px4"
WS_DIR="${PX4_DIR}/px4_ws"

if [[ -n "${ROS_DISTRO:-}" && -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]]; then
  ros_setup="/opt/ros/${ROS_DISTRO}/setup.bash"
else
  ros_setups=(/opt/ros/*/setup.bash)
  if ((${#ros_setups[@]} != 1)) || [[ ! -f "${ros_setups[0]}" ]]; then
    echo "error: set ROS_DISTRO or install exactly one ROS 2 distribution under /opt/ros." >&2
    return 1 2>/dev/null || exit 1
  fi
  ros_setup="${ros_setups[0]}"
fi

set +u
# shellcheck disable=SC1090
source "${ros_setup}"
set -u

if [[ -f "${WS_DIR}/install/setup.bash" ]]; then
  set +u
  # shellcheck disable=SC1091
  source "${WS_DIR}/install/setup.bash"
  set -u
fi
