#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./run.sh                # only clone missing repos
#   ./run.sh --update       # update existing git repos (pull --ff-only)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="${ROOT_DIR}/src"
DO_UPDATE=0

if [[ "${1:-}" == "--update" ]]; then
	DO_UPDATE=1
fi

mkdir -p "${SRC_DIR}"

clone_or_skip() {
	local repo_url="$1"
	local target_dir="$2"
	local branch="${3:-}"

	local full_path="${SRC_DIR}/${target_dir}"

	if [[ -d "${full_path}/.git" ]]; then
		echo "[SKIP] ${target_dir} already exists"
		if [[ ${DO_UPDATE} -eq 1 ]]; then
			echo "[UPDT] ${target_dir}"
			git -C "${full_path}" fetch --all --prune
			if [[ -n "${branch}" ]]; then
				git -C "${full_path}" checkout "${branch}"
			fi
			git -C "${full_path}" pull --ff-only
		fi
		return
	fi

	if [[ -e "${full_path}" ]]; then
		echo "[WARN] ${target_dir} exists but is not a git repo, skip"
		return
	fi

	echo "[CLONE] ${target_dir}"
	if [[ -n "${branch}" ]]; then
		git clone -b "${branch}" "${repo_url}" "${full_path}"
	else
		git clone "${repo_url}" "${full_path}"
	fi
}

clone_or_skip "https://github.com/PX4/px4_msgs.git" "px4_msgs" "v1.16.1"
clone_or_skip "https://github.com/eProsima/Micro-XRCE-DDS-Agent.git" "Micro-XRCE-DDS-Agent"
clone_or_skip "https://github.com/wanone111/vision_to_dds.git" "vision_to_dds"
clone_or_skip "https://github.com/BoomBoomFly/offboard_cpp.git" "offboard_cpp"
clone_or_skip "https://github.com/BoomBoomFly/serial_driver_ros.git" "serial_driver_ros"
clone_or_skip "https://github.com/IntelRealSense/librealsense.git" "librealsense" "v2.53.1"
clone_or_skip "https://github.com/IntelRealSense/realsense-ros.git" "realsense-ros" "4.0.4"
clone_or_skip "https://github.com/BoomBoomFly/px4_bringup.git" "px4_bringup"

echo "Done."
