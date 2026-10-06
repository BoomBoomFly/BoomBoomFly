#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
# 默认同步自写独立仓库；可显式选择一个或多个范围。
if [[ $# == 0 ]]; then
  repository_list="$(python3 "${project_root}/Scripts/repository.py" --list)"
  mapfile -t repositories <<< "${repository_list}"
  set -- "${repositories[@]}"
fi
# 先验证全部范围，避免拼写错误前已经执行部分同步。
for repository in "$@"; do
  [[ "${repository}" != main ]] || { echo "错误：主仓库请单独同步。" >&2; exit 1; }
  python3 "${project_root}/Scripts/repository.py" "${repository}" >/dev/null
done
for repository in "$@"; do
  relative="$(python3 "${project_root}/Scripts/repository.py" "${repository}")"
  target="${project_root}/${relative}"
  url="https://github.com/BoomBoomFly/${repository}.git"
  if [[ -e "${target}/.git" ]]; then
    echo "更新 ${repository}（当前分支的 upstream）"
    git -C "${target}" pull --ff-only
  elif [[ -e "${target}" ]]; then
    echo "错误：${target} 已存在，但不是独立 Git 仓库；保留原目录。" >&2
    exit 1
  else
    mkdir -p "$(dirname -- "${target}")"
    git clone "${url}" "${target}"
  fi
done
