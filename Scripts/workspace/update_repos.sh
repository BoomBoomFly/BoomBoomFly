#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PX4_DIR="${ROOT_DIR}/px4"
SRC_DIR="${PX4_DIR}/px4_ws/src"
UPSTREAM_DIR="${PX4_DIR}/upstream"

list_repository_candidates() {
  local parent
  for parent in "${UPSTREAM_DIR}" "${SRC_DIR}/boomboom" "${SRC_DIR}/external"; do
    [[ -d "${parent}" ]] || continue
    find "${parent}" -mindepth 1 -maxdepth 1 -type d -print
  done
}

repos=()
dirty_repos=()
while IFS= read -r repo_dir; do
  [[ "$(git -C "${repo_dir}" rev-parse --show-toplevel 2>/dev/null || true)" == "${repo_dir}" ]] || continue
  repos+=("${repo_dir}")
  if [[ -n "$(git -C "${repo_dir}" status --porcelain)" ]]; then
    dirty_repos+=("${repo_dir#"${ROOT_DIR}/"}")
  fi
done < <(list_repository_candidates | sort)

if ((${#repos[@]} == 0)); then
  echo "error: no Git repositories found below ${PX4_DIR}" >&2
  exit 1
fi

if ((${#dirty_repos[@]})); then
  printf 'error: refusing to update dirty repositories:\n' >&2
  printf '  %s\n' "${dirty_repos[@]}" >&2
  exit 1
fi

for repo_dir in "${repos[@]}"; do
  relative_path="${repo_dir#"${ROOT_DIR}/"}"
  if [[ "${repo_dir}" == "${UPSTREAM_DIR}/"* ]]; then
    echo "[FETCH] ${relative_path} (manifest-pinned upstream)"
    git -C "${repo_dir}" fetch --prune --tags origin
    continue
  fi
  branch="$(git -C "${repo_dir}" branch --show-current)"
  if [[ -n "${branch}" ]]; then
    echo "[PULL] ${relative_path} (${branch})"
    git -C "${repo_dir}" pull --ff-only
  else
    echo "[FETCH] ${relative_path} (detached lock)"
    git -C "${repo_dir}" fetch --prune --tags origin
  fi
done
