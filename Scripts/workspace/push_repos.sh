#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BOOMBOOM_DIR="${ROOT_DIR}/px4/px4_ws/src/boomboom"

if (($#)); then
  echo "usage: $0" >&2
  exit 2
fi

# 先检查全部仓库的上游，再依次提交并推送子仓库和根仓库；不推送第三方仓库。
repos=()
for repo in "${BOOMBOOM_DIR}"/* "${ROOT_DIR}"; do
  [[ -e "${repo}/.git" ]] || continue
  branch="$(git -C "${repo}" branch --show-current)"
  if [[ -z "${branch}" ]] || ! git -C "${repo}" rev-parse --verify '@{upstream}' >/dev/null 2>&1; then
    echo "error: branch with an upstream is required: ${repo}" >&2
    exit 1
  fi
  repos+=("${repo}")
done

if ((${#repos[@]} == 0)); then
  echo "error: no repositories found in ${ROOT_DIR}" >&2
  exit 1
fi

for repo in "${repos[@]}"; do
  git -C "${repo}" add -A
  if ! git -C "${repo}" diff --cached --quiet; then
    echo "[COMMIT] ${repo##*/}"
    git -C "${repo}" commit -m "chore: sync local changes"
  fi
  branch="$(git -C "${repo}" branch --show-current)"
  remote="$(git -C "${repo}" config --get "branch.${branch}.remote")"
  target="$(git -C "${repo}" config --get "branch.${branch}.merge")"
  echo "[PUSH] ${repo##*/} (${branch} -> ${remote}/${target#refs/heads/})"
  git -C "${repo}" push --no-follow-tags "${remote}" "HEAD:${target}"
done
