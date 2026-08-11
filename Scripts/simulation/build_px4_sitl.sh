#!/usr/bin/env bash
set -euo pipefail

if (($# != 0)); then
  echo "usage: $0" >&2
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

echo "[BUILD] PX4 SITL in ${PX4_DIR}"
make -C "${PX4_DIR}" px4_sitl
