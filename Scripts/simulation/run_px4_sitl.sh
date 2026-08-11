#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 [simulation-target]" >&2
  echo "  Ubuntu 20.04 default: gazebo-classic" >&2
  echo "  Ubuntu 22.04 default: gz_x500" >&2
}

if (($# == 1)) && [[ "$1" == "-h" || "$1" == "--help" ]]; then
  usage
  exit 0
fi

if (($# > 1)); then
  usage
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PX4_DIR="${ROOT_DIR}/px4/upstream/PX4-Autopilot"

if [[ ! -f "${PX4_DIR}/Makefile" ]]; then
  echo "error: PX4-Autopilot is missing; run Scripts/workspace/pull_repos.sh first." >&2
  exit 1
fi

if ! command -v make >/dev/null 2>&1; then
  echo "error: make is required but was not found in PATH." >&2
  exit 1
fi

if (($# == 1)); then
  SIMULATION_TARGET="$1"
else
  if [[ ! -r /etc/os-release ]]; then
    echo "error: cannot detect Ubuntu version; pass the PX4 simulation target explicitly." >&2
    usage
    exit 1
  fi

  # shellcheck disable=SC1091
  source /etc/os-release
  if [[ "${ID:-}" != "ubuntu" ]]; then
    echo "error: automatic target selection only supports Ubuntu; pass a target explicitly." >&2
    usage
    exit 1
  fi

  case "${VERSION_ID:-}" in
    20.04)
      SIMULATION_TARGET="gazebo-classic"
      ;;
    22.04)
      SIMULATION_TARGET="gz_x500"
      ;;
    *)
      echo "error: unsupported Ubuntu version ${VERSION_ID:-unknown}; pass a target explicitly." >&2
      usage
      exit 1
      ;;
  esac
fi

echo "[RUN] PX4 SITL target ${SIMULATION_TARGET} in ${PX4_DIR}"
exec make -C "${PX4_DIR}" px4_sitl "${SIMULATION_TARGET}"
