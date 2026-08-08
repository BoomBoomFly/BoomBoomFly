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

printf '%-42s %-16s %-12s %s\n' 'repository' 'branch' 'commit' 'state'
while IFS= read -r repo_dir; do
  [[ "$(git -C "${repo_dir}" rev-parse --show-toplevel 2>/dev/null || true)" == "${repo_dir}" ]] || continue
  branch="$(git -C "${repo_dir}" branch --show-current)"
  [[ -n "${branch}" ]] || branch='detached'
  commit="$(git -C "${repo_dir}" rev-parse --short HEAD)"
  state='clean'
  [[ -z "$(git -C "${repo_dir}" status --porcelain)" ]] || state='dirty'
  printf '%-42s %-16s %-12s %s\n' "${repo_dir#"${ROOT_DIR}/"}" "${branch}" "${commit}" "${state}"
done < <(list_repository_candidates | sort)
