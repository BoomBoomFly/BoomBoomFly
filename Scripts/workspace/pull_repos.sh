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
# vcstool 的 --skip-existing 连空目录也会跳过。只处理所选清单中的空占位目录，
# 已有 Git 仓库继续交给 --skip-existing 保留，非空非仓库目录明确报错。
manifest_pairs=("${ROS_MANIFEST}" "${SRC_DIR}" "${UPSTREAM_MANIFEST}" "${UPSTREAM_DIR}")
if ((WITH_PERCEPTION_DEPS)); then
  manifest_pairs+=("${PERCEPTION_DEPS_MANIFEST}" "${SRC_DIR}")
fi
python3 - "${manifest_pairs[@]}" <<'PY'
import sys
from pathlib import Path

import yaml

empty_directories = []
errors = []
for manifest, base in zip(sys.argv[1::2], sys.argv[2::2]):
    repositories = yaml.safe_load(Path(manifest).read_text())["repositories"]
    for relative in repositories:
        path = Path(base) / relative
        if path.is_symlink():
            errors.append(f"{path}: repository path is a symlink; inspect it before importing")
        elif not path.exists():
            continue
        elif path.is_dir() and (path / ".git").exists():
            continue
        elif path.is_dir() and not any(path.iterdir()):
            empty_directories.append(path)
        else:
            errors.append(f"{path}: existing path is not an empty directory or Git repository")

if errors:
    sys.exit("error: repository import blocked:\n" + "\n".join(errors))
for path in empty_directories:
    path.rmdir()
    print(f"[IMPORT] removed empty placeholder: {path}", flush=True)
PY

vcs import --recursive --skip-existing "${SRC_DIR}" < "${ROS_MANIFEST}"
vcs import --recursive --skip-existing "${UPSTREAM_DIR}" < "${UPSTREAM_MANIFEST}"

if ((WITH_PERCEPTION_DEPS)); then
  vcs import --recursive --skip-existing "${SRC_DIR}" < "${PERCEPTION_DEPS_MANIFEST}"
fi
