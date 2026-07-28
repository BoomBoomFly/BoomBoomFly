#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  cat <<'EOF'
Usage: build_dds_only.sh [options]

Build the exact BoomBoomFly DDS-only package allowlist. All colcon output is
required to resolve below /tmp.

Options:
  --workspace-root PATH  Repository root (default: script's Git worktree)
  --profile PATH         DDS-only package profile
  --output-root PATH     Isolated output root below /tmp (default: mktemp)
  --ros-setup PATH       ROS setup script (default: /opt/ros/foxy/setup.bash)
  --help                 Show this help
EOF
}

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
WORKSPACE_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
PROFILE=""
OUTPUT_ROOT=""
ROS_SETUP="/opt/ros/foxy/setup.bash"

while (($#)); do
  case "$1" in
    --workspace-root)
      [[ $# -ge 2 ]] || { echo "ERROR: --workspace-root requires a value" >&2; exit 3; }
      WORKSPACE_ROOT="$2"
      shift 2
      ;;
    --profile)
      [[ $# -ge 2 ]] || { echo "ERROR: --profile requires a value" >&2; exit 3; }
      PROFILE="$2"
      shift 2
      ;;
    --output-root)
      [[ $# -ge 2 ]] || { echo "ERROR: --output-root requires a value" >&2; exit 3; }
      OUTPUT_ROOT="$2"
      shift 2
      ;;
    --ros-setup)
      [[ $# -ge 2 ]] || { echo "ERROR: --ros-setup requires a value" >&2; exit 3; }
      ROS_SETUP="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 3
      ;;
  esac
done

WORKSPACE_ROOT="$(realpath -e -- "$WORKSPACE_ROOT")"
PROFILE="${PROFILE:-$WORKSPACE_ROOT/config/profiles/dds_only_packages.yaml}"
PROFILE="$(realpath -e -- "$PROFILE")"
if [[ -z "$OUTPUT_ROOT" ]]; then
  OUTPUT_ROOT="$(mktemp -d /tmp/boomboomfly_dds_build.XXXXXX)"
else
  OUTPUT_ROOT="$(realpath -m -- "$OUTPUT_ROOT")"
fi
case "$OUTPUT_ROOT" in
  /tmp/*) ;;
  *)
    echo "ERROR: --output-root must resolve below /tmp: $OUTPUT_ROOT" >&2
    exit 3
    ;;
esac
[[ -f "$ROS_SETUP" ]] || {
  echo "ERROR: ROS setup script is missing: $ROS_SETUP" >&2
  exit 2
}
command -v colcon >/dev/null || {
  echo "ERROR: colcon is missing" >&2
  exit 2
}

mkdir -p -- "$OUTPUT_ROOT"/{artifacts,build,install,log}
SELECTION="$OUTPUT_ROOT/artifacts/package-selection.tsv"

set +u
# Do not inherit packages from an unrelated ROS workspace. The only underlay
# permitted by this authoritative entry point is the explicitly selected ROS
# distribution setup below.
unset AMENT_PREFIX_PATH COLCON_PREFIX_PATH CMAKE_PREFIX_PATH ROS_PACKAGE_PATH PYTHONPATH LD_LIBRARY_PATH PKG_CONFIG_PATH
# shellcheck disable=SC1090
source "$ROS_SETUP"
set -u

python3 -c \
  'import json, pathlib, sys
profile_path = pathlib.Path(sys.argv[1])
root = pathlib.Path(sys.argv[2]).resolve()
profile = json.loads(profile_path.read_text(encoding="utf-8"))
packages = profile.get("production_packages")
if not isinstance(packages, list) or not packages:
    raise SystemExit("ERROR: production_packages must be a non-empty list")
seen = set()
for item in packages:
    name = item.get("name")
    relative = item.get("path")
    if not isinstance(name, str) or not name or name in seen:
        raise SystemExit("ERROR: invalid or duplicate package name")
    if not isinstance(relative, str) or not relative.startswith("src/"):
        raise SystemExit("ERROR: invalid package path for {}".format(name))
    path = (root / relative).resolve()
    if root not in path.parents or not (path / "package.xml").is_file():
        raise SystemExit("ERROR: package {} is missing {}".format(name, path / "package.xml"))
    seen.add(name)
    print("{}\t{}".format(name, path))' \
  "$PROFILE" "$WORKSPACE_ROOT" >"$SELECTION"

PACKAGE_NAMES=()
PACKAGE_PATHS=()
while IFS=$'\t' read -r package_name package_path; do
  [[ -n "$package_name" && -n "$package_path" ]] || {
    echo "ERROR: invalid package selection record" >&2
    exit 2
  }
  PACKAGE_NAMES+=("$package_name")
  PACKAGE_PATHS+=("$package_path")
done <"$SELECTION"
[[ ${#PACKAGE_NAMES[@]} -gt 0 ]] || {
  echo "ERROR: DDS-only selection is empty" >&2
  exit 2
}

# Keep generated ROS interface compilation deterministic and bounded on both
# WSL and the later ARM64 rebuild; px4_msgs must not race multiple generators.
CMAKE_BUILD_PARALLEL_LEVEL=1 colcon \
  --log-base "$OUTPUT_ROOT/log/build" \
  build \
  --parallel-workers 1 \
  --paths "${PACKAGE_PATHS[@]}" \
  --build-base "$OUTPUT_ROOT/build" \
  --install-base "$OUTPUT_ROOT/install" \
  --packages-select "${PACKAGE_NAMES[@]}"

printf '{"status":"PASS","action":"build","output_root":"%s","packages":%d}\n' \
  "$OUTPUT_ROOT" "${#PACKAGE_NAMES[@]}"
