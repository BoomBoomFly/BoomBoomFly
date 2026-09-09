#!/usr/bin/env bash
set -euo pipefail

if (($#)); then
  echo "usage: $0" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/../push_git.sh" all "chore: sync local changes"
