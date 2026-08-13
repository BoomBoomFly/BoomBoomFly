#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PX4_DIR="${ROOT_DIR}/px4"
WS_DIR="${PX4_DIR}/px4_ws"
SRC_DIR="${WS_DIR}/src"
UPSTREAM_DIR="${PX4_DIR}/upstream"
ROS_MANIFEST="${ROOT_DIR}/manifests/boomboom.repos"
UPSTREAM_MANIFEST="${ROOT_DIR}/manifests/upstream.repos"
PERCEPTION_DEPS_MANIFEST="${ROOT_DIR}/manifests/perception_deps.repos"
WITH_PERCEPTION_DEPS=0

usage() {
  echo "usage: $0 [--with-perception-deps]" >&2
}

while (($#)); do
  case "$1" in
    --with-perception-deps|--with-perception)
      WITH_PERCEPTION_DEPS=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 2
      ;;
  esac
  shift
done

if ! command -v vcs >/dev/null 2>&1; then
  echo "error: vcstool is required; install the 'python3-vcstool' package first." >&2
  exit 1
fi

for manifest in "${ROS_MANIFEST}" "${UPSTREAM_MANIFEST}"; do
  if [[ ! -f "${manifest}" ]]; then
    echo "error: manifest not found: ${manifest}" >&2
    exit 1
  fi
done

if ((WITH_PERCEPTION_DEPS)) && [[ ! -f "${PERCEPTION_DEPS_MANIFEST}" ]]; then
  echo "error: manifest not found: ${PERCEPTION_DEPS_MANIFEST}" >&2
  exit 1
fi

mkdir -p "${SRC_DIR}" "${UPSTREAM_DIR}"
vcs import --recursive --skip-existing "${SRC_DIR}" < "${ROS_MANIFEST}"
vcs import --recursive --skip-existing "${UPSTREAM_DIR}" < "${UPSTREAM_MANIFEST}"

if ((WITH_PERCEPTION_DEPS)); then
  vcs import --recursive --skip-existing "${SRC_DIR}" < "${PERCEPTION_DEPS_MANIFEST}"
fi
