#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BOOMBOOM_DIR="${ROOT_DIR}/px4/px4_ws/src/boomboom"

if (($#)); then
  echo "usage: $0" >&2
  exit 2
fi

# 先检查全部仓库，再推送；不自动提交、不推送第三方仓库。
repos=()
for repo in "${BOOMBOOM_DIR}"/*; do
  [[ -e "${repo}/.git" ]] || continue
  if [[ -n "$(git -C "${repo}" status --porcelain)" ]]; then
    echo "error: commit local changes before pushing: ${repo}" >&2
    exit 1
  fi
  branch="$(git -C "${repo}" branch --show-current)"
  if [[ -z "${branch}" ]] || ! git -C "${repo}" rev-parse --verify '@{upstream}' >/dev/null 2>&1; then
    echo "error: branch with an upstream is required: ${repo}" >&2
    exit 1
  fi
  repos+=("${repo}")
done

if ((${#repos[@]} == 0)); then
  echo "error: no repositories found in ${BOOMBOOM_DIR}" >&2
  exit 1
fi

for repo in "${repos[@]}"; do
  branch="$(git -C "${repo}" branch --show-current)"
  remote="$(git -C "${repo}" config --get "branch.${branch}.remote")"
  target="$(git -C "${repo}" config --get "branch.${branch}.merge")"
  echo "[PUSH] ${repo##*/} (${branch} -> ${remote}/${target#refs/heads/})"
  git -C "${repo}" push --no-follow-tags "${remote}" "HEAD:${target}"
done
