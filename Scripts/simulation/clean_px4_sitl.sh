#!/usr/bin/env bash
set -euo pipefail

if (($# != 0)); then
  echo "usage: $0" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PX4_DIR="${ROOT_DIR}/px4/upstream/PX4-Autopilot"
BUILD_DIR="${PX4_DIR}/build/px4_sitl_default"

if [[ ! -d "${PX4_DIR}" ]]; then
  echo "error: PX4-Autopilot is missing; run Scripts/workspace/pull_repos.sh first." >&2
  exit 1
fi

if [[ ! -d "${BUILD_DIR}" ]]; then
  echo "[CLEAN] no PX4 SITL build directory: ${BUILD_DIR}"
  exit 0
fi

echo "[CLEAN] removing ${BUILD_DIR}"
rm -rf -- "${BUILD_DIR}"
