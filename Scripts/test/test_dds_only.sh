#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  cat <<'EOF'
Usage: test_dds_only.sh [options]

Build and test the exact BoomBoomFly DDS-only package allowlist. All colcon
output is required to resolve below /tmp.

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
  OUTPUT_ROOT="$(mktemp -d /tmp/boomboomfly_dds_test.XXXXXX)"
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

bash "$WORKSPACE_ROOT/Scripts/build/build_dds_only.sh" \
  --workspace-root "$WORKSPACE_ROOT" \
  --profile "$PROFILE" \
  --output-root "$OUTPUT_ROOT" \
  --ros-setup "$ROS_SETUP"

set +u
# Match the build entry point clean underlay boundary before loading the
# isolated install space.
unset AMENT_PREFIX_PATH COLCON_PREFIX_PATH CMAKE_PREFIX_PATH ROS_PACKAGE_PATH PYTHONPATH LD_LIBRARY_PATH PKG_CONFIG_PATH
# shellcheck disable=SC1090
source "$ROS_SETUP"
# shellcheck disable=SC1090
source "$OUTPUT_ROOT/install/setup.bash"
set -u

PACKAGE_NAMES=()
while IFS=$'\t' read -r package_name package_path; do
  [[ -n "$package_name" && -n "$package_path" ]] || {
    echo "ERROR: invalid package selection record" >&2
    exit 2
  }
  PACKAGE_NAMES+=("$package_name")
done <"$OUTPUT_ROOT/artifacts/package-selection.tsv"

# px4_msgs generated-code lint commands exceed the default async pipe line
# limit when CTest is verbose. Quiet console mode avoids that transport
# deadlock; xUnit plus CTest LastTest.log retain the complete test evidence.
colcon \
  --log-base "$OUTPUT_ROOT/log/test" \
  test \
  --build-base "$OUTPUT_ROOT/build" \
  --install-base "$OUTPUT_ROOT/install" \
  --test-result-base "$OUTPUT_ROOT/test-results" \
  --packages-select "${PACKAGE_NAMES[@]}" \
  --return-code-on-test-failure \
  --ctest-args -Q

colcon \
  --log-base "$OUTPUT_ROOT/log/test-result" \
  test-result \
  --test-result-base "$OUTPUT_ROOT/test-results" \
  --verbose

printf '{"status":"PASS","action":"test","output_root":"%s","packages":%d}\n' \
  "$OUTPUT_ROOT" "${#PACKAGE_NAMES[@]}"
