#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

SRC_DIR="${PROJECT_ROOT}/src"
DEFAULT_MANIFEST="${PROJECT_ROOT}/workspace.lock.repos"
MANIFEST="${DEFAULT_MANIFEST}"
MANIFEST_EXPLICIT=0
WITH_ARCHIVE=0
WITH_OPTIONAL=()
DO_UPDATE=0
DRY_RUN=0
VERIFY_ONLY=0
SKIP_PACKAGE_CHECK=0
REQUIRE_COLCON=0
WITH_SUBMODULES=1

CLONED_COUNT=0
UPDATED_COUNT=0
VERIFIED_COUNT=0
PLANNED_COUNT=0
BLOCKER_COUNT=0

usage() {
	cat <<EOF
Usage:
  ${SCRIPT_NAME} [options]

Restore the active profile declared by workspace.lock.repos. Project-owned
flight packages follow approved default branches; third-party dependencies use
exact commit SHAs. Archive and optional sources are composed only when their
explicit flags are present. src/communication is restored from main as a normal
manifest repository and is not stored in the root Git tree.
Its Serial/serial_driver_ros checkout is pinned by the communication Git
submodule and is also recorded as quarantine provenance in the manifest.
Quarantine entries are never selected, including through --manifest.
Locked commits are checked out in detached-HEAD state; this script never creates
dependency branches and never runs git pull.

Options:
  --src-dir <path>       Target ROS 2 src directory. Default: ${SRC_DIR}
  --manifest <path>      One custom manifest; mutually exclusive with profile flags.
                         Default active manifest: ${DEFAULT_MANIFEST}
  --with-archive         Add archive entries from ${DEFAULT_MANIFEST}
  --with-optional <name> Add an optional profile: perception or navigation.
                         Repeat to select both profiles.
  --update               Sync existing clean repositories to the manifest ref.
  --verify-only          Audit all repositories without cloning/updating.
  --dry-run              Audit and print planned actions without changing files or Git refs.
  --skip-submodules      Do not initialize dependency submodules.
  --skip-package-check   Do not run colcon package discovery.
  --require-colcon       Fail if colcon is unavailable or package discovery fails.
  -h, --help             Show this help message.

Safety:
  * Existing dirty repositories are never checked out or updated.
  * Existing repositories with a different origin URL are rejected.
  * src/communication is restored at the latest origin/main commit; its recorded
    submodule URL and commit come from that repository's .gitmodules/gitlink.
  * Active/archive/optional target paths must be globally unique.
  * Only the declared project paths may use their approved latest branches.
  * Every other governed or custom manifest entry requires an exact commit SHA.
  * Without --update, a repository at the wrong commit is rejected.
  * Exact lock SHAs are verified after checkout.
  * Audit modes inspect every entry, summarize all blockers, then exit non-zero.
EOF
}

log() {
	printf '%s\n' "$*"
}

warn() {
	printf '[WARN] %s\n' "$*" >&2
}

record_blocker() {
	warn "[BLOCK] $*"
	BLOCKER_COUNT=$((BLOCKER_COUNT + 1))
}

die() {
	printf '[ERROR] %s\n' "$*" >&2
	exit 1
}

require_command() {
	local cmd="$1"
	command -v "${cmd}" >/dev/null 2>&1 || die "Required command not found: ${cmd}"
}

run_cmd() {
	if [[ ${DRY_RUN} -eq 1 ]]; then
		printf '[DRY] '
		printf '%q ' "$@"
		printf '\n'
		return 0
	fi

	"$@"
}

absolute_path() {
	local path="$1"
	if [[ "${path}" == /* ]]; then
		printf '%s\n' "${path}"
	else
		printf '%s/%s\n' "$(pwd)" "${path}"
	fi
}

normalize_repo_url() {
	local url="$1"
	case "${url}" in
		git@github.com:*)
			url="https://github.com/${url#git@github.com:}"
			;;
		ssh://git@github.com/*)
			url="https://github.com/${url#ssh://git@github.com/}"
			;;
	esac
	url="${url%/}"
	url="${url%.git}"
	printf '%s\n' "${url}"
}

is_locked_sha() {
	[[ "$1" =~ ^[0-9a-f]{40}$ ]]
}

is_approved_latest_ref() {
	local manifest_path="$1"
	local ref="$2"
	case "${manifest_path}:${ref}" in
		src/communication:main | src/offboard_cpp:DDS | \
			src/vision_to_dds:master | src/px4_bringup:DDS)
			return 0
			;;
	esac
	return 1
}

repo_is_dirty() {
	[[ -n "$(git -C "$1" status --porcelain --untracked-files=normal)" ]]
}

while [[ $# -gt 0 ]]; do
	case "$1" in
		--src-dir)
			[[ $# -ge 2 ]] || die "--src-dir requires a path"
			SRC_DIR="$2"
			shift 2
			;;
		--manifest)
			[[ $# -ge 2 ]] || die "--manifest requires a path"
			MANIFEST="$2"
			MANIFEST_EXPLICIT=1
			shift 2
			;;
		--with-archive)
			WITH_ARCHIVE=1
			shift
			;;
		--with-optional)
			[[ $# -ge 2 ]] || die "--with-optional requires perception or navigation"
			case "$2" in
				perception | navigation)
					WITH_OPTIONAL+=("$2")
					;;
			*)
				die "Unknown optional profile: $2 (expected perception or navigation)"
				;;
			esac
			shift 2
			;;
		--update)
			DO_UPDATE=1
			shift
			;;
		--verify-only)
			VERIFY_ONLY=1
			shift
			;;
		--dry-run)
			DRY_RUN=1
			shift
			;;
		--skip-submodules)
			WITH_SUBMODULES=0
			shift
			;;
		--skip-package-check)
			SKIP_PACKAGE_CHECK=1
			shift
			;;
		--require-colcon)
			REQUIRE_COLCON=1
			shift
			;;
		-h | --help)
			usage
			exit 0
			;;
		*)
			die "Unknown option: $1"
			;;
	esac
done

[[ ${DO_UPDATE} -eq 0 || ${VERIFY_ONLY} -eq 0 ]] || die "--update and --verify-only cannot be combined"
[[ ${SKIP_PACKAGE_CHECK} -eq 0 || ${REQUIRE_COLCON} -eq 0 ]] || die "--skip-package-check and --require-colcon cannot be combined"
if [[ ${MANIFEST_EXPLICIT} -eq 1 && (${WITH_ARCHIVE} -eq 1 || ${#WITH_OPTIONAL[@]} -gt 0) ]]; then
	die "--manifest cannot be combined with --with-archive or --with-optional"
fi
require_command git
require_command awk

SRC_DIR="$(absolute_path "${SRC_DIR}")"
SELECTED_PROFILES=()
if [[ ${MANIFEST_EXPLICIT} -eq 1 ]]; then
	MANIFEST="$(absolute_path "${MANIFEST}")"
	SELECTED_PROFILES+=("custom")
else
	MANIFEST="${DEFAULT_MANIFEST}"
	SELECTED_PROFILES+=("active")
	if [[ ${WITH_ARCHIVE} -eq 1 ]]; then
		SELECTED_PROFILES+=("archive")
	fi
	declare -A SELECTED_OPTIONAL=()
	for optional_profile in "${WITH_OPTIONAL[@]}"; do
		[[ -z "${SELECTED_OPTIONAL[${optional_profile}]:-}" ]] || continue
		SELECTED_OPTIONAL[${optional_profile}]=1
		SELECTED_PROFILES+=("optional-${optional_profile}")
	done
fi
[[ -f "${MANIFEST}" ]] || die "Manifest not found: ${MANIFEST}"

declare -A SELECTED_PROFILE_SET=()
for selected_profile in "${SELECTED_PROFILES[@]}"; do
	SELECTED_PROFILE_SET[${selected_profile}]=1
done

parse_manifest() {
	local selected_manifest="$1"
	local require_profiles="$2"
	awk -v require_profiles="${require_profiles}" '
	function trim(value) {
		sub(/^[[:space:]]+/, "", value)
		sub(/[[:space:]]+$/, "", value)
		return value
	}
	function clean(value, first, last) {
		value = trim(value)
		first = substr(value, 1, 1)
		last = substr(value, length(value), 1)
		if ((first == "\"" && last == "\"") || (first == "\047" && last == "\047")) {
			value = substr(value, 2, length(value) - 2)
		}
		return value
	}
	function emit() {
		if (path == "") {
			return
		}
		if (type != "git" || url == "" || version == "") {
			printf "Invalid git entry for %s (type/url/version required)\n", path > "/dev/stderr"
			bad = 1
			return
		}
		if (require_profiles == "1" && profile == "") {
			printf "Missing profile marker for %s\n", path > "/dev/stderr"
			bad = 1
			return
		}
		entry_profile = (profile == "" ? "custom" : profile)
		printf "%s\t%s\t%s\t%s\n", entry_profile, path, url, version
	}
	BEGIN {
		in_repositories = 0
		path = ""
		profile = ""
		bad = 0
	}
	/^# profile:[[:space:]]*[a-z-]+[[:space:]]*$/ {
		emit()
		path = ""
		profile = $0
		sub(/^# profile:[[:space:]]*/, "", profile)
		sub(/[[:space:]]*$/, "", profile)
		next
	}
	/^[[:space:]]*#/ { next }
	/^repositories:[[:space:]]*$/ {
		in_repositories = 1
		next
	}
	in_repositories && /^  [^[:space:]][^:]*:[[:space:]]*$/ {
		emit()
		path = $0
		sub(/^  /, "", path)
		sub(/:[[:space:]]*$/, "", path)
		type = ""
		url = ""
		version = ""
		next
	}
	path != "" && /^    type:[[:space:]]*/ {
		type = $0
		sub(/^    type:[[:space:]]*/, "", type)
		type = clean(type)
		next
	}
	path != "" && /^    url:[[:space:]]*/ {
		url = $0
		sub(/^    url:[[:space:]]*/, "", url)
		url = clean(url)
		next
	}
	path != "" && /^    version:[[:space:]]*/ {
		version = $0
		sub(/^    version:[[:space:]]*/, "", version)
		version = clean(version)
		next
	}
	END {
		emit()
		if (!in_repositories) {
			print "Missing top-level repositories mapping" > "/dev/stderr"
			bad = 1
		}
		exit bad
	}
		' "${selected_manifest}"
}

require_profiles=$((1 - MANIFEST_EXPLICIT))
manifest_data="$(parse_manifest "${MANIFEST}" "${require_profiles}")" ||
	die "Failed to parse manifest: ${MANIFEST}"
[[ -n "${manifest_data}" ]] || die "Manifest contains no repositories: ${MANIFEST}"
ALL_REPOSITORIES=()
while IFS= read -r record; do
	ALL_REPOSITORIES+=("${record}")
done <<<"${manifest_data}"

REPOSITORIES=()
declare -A SEEN_TARGETS=()
declare -A PROFILE_ENTRY_COUNTS=()
for record in "${ALL_REPOSITORIES[@]}"; do
	IFS=$'\t' read -r record_profile manifest_path repo_url repo_ref <<<"${record}"
	case "${manifest_path}" in
		src/*)
			target_key="${manifest_path#src/}"
			if [[ -z "${target_key}" || "${target_key}" == /* || "${target_key}" =~ (^|/)\.\.?(/|$) ]]; then
				die "Unsafe manifest target: ${manifest_path}"
			fi
			;;
		*)
			die "Manifest path must be below src/: ${manifest_path}"
			;;
	esac
	[[ -z "${SEEN_TARGETS[${target_key}]:-}" ]] || die "Duplicate manifest target: ${manifest_path}"
	SEEN_TARGETS[${target_key}]=1

	if ! is_locked_sha "${repo_ref}" &&
		! is_approved_latest_ref "${manifest_path}" "${repo_ref}"; then
		die "Manifest ref is not an approved latest branch or 40-character lock SHA for ${manifest_path}: ${repo_ref}"
	fi

	if [[ ${MANIFEST_EXPLICIT} -eq 0 ]]; then
		case "${record_profile}" in
			active | archive | optional-perception | optional-navigation | quarantine) ;;
			*) die "Unknown governed profile for ${manifest_path}: ${record_profile}" ;;
		esac
		PROFILE_ENTRY_COUNTS[${record_profile}]=$((${PROFILE_ENTRY_COUNTS[${record_profile}]:-0} + 1))
	fi

	if [[ ${MANIFEST_EXPLICIT} -eq 1 && "${record_profile}" != "quarantine" ]]; then
		REPOSITORIES+=("${manifest_path}"$'\t'"${repo_url}"$'\t'"${repo_ref}")
	elif [[ ${MANIFEST_EXPLICIT} -eq 0 && -n "${SELECTED_PROFILE_SET[${record_profile}]:-}" ]]; then
		REPOSITORIES+=("${manifest_path}"$'\t'"${repo_url}"$'\t'"${repo_ref}")
	fi
done

if [[ ${MANIFEST_EXPLICIT} -eq 0 ]]; then
	for selected_profile in "${SELECTED_PROFILES[@]}"; do
		[[ ${PROFILE_ENTRY_COUNTS[${selected_profile}]:-0} -gt 0 ]] ||
			die "Selected profile has no repositories: ${selected_profile}"
	done
fi
[[ ${#REPOSITORIES[@]} -gt 0 ]] || die "Profile selection produced no repositories"

if [[ ${DRY_RUN} -eq 1 ]]; then
	[[ -d "${SRC_DIR}" ]] || log "[DRY] mkdir -p ${SRC_DIR}"
elif [[ ${VERIFY_ONLY} -eq 0 ]]; then
	mkdir -p "${SRC_DIR}"
fi

log "Project root: ${PROJECT_ROOT}"
log "Profiles:     ${SELECTED_PROFILES[*]}"
log "Manifest:     ${MANIFEST}"
log "Target src:  ${SRC_DIR}"
log "Repositories:${#REPOSITORIES[@]}"
log "Checkout:    detached HEAD"

resolve_ref() {
	local full_path="$1"
	local ref="$2"
	local candidate

	for candidate in "origin/${ref}" "${ref}" "refs/tags/${ref}" FETCH_HEAD; do
		if git -C "${full_path}" rev-parse --verify --quiet "${candidate}^{commit}" >/dev/null; then
			git -C "${full_path}" rev-parse "${candidate}^{commit}"
			return 0
		fi
	done
	return 1
}

ensure_ref_available() {
	local full_path="$1"
	local ref="$2"

	if ! is_locked_sha "${ref}"; then
		if [[ ${DRY_RUN} -eq 1 ]]; then
			run_cmd git -C "${full_path}" fetch --prune origin \
				"refs/heads/${ref}:refs/remotes/origin/${ref}"
			return 0
		fi
		git -C "${full_path}" fetch --prune origin \
			"refs/heads/${ref}:refs/remotes/origin/${ref}" ||
			die "Unable to fetch latest origin/${ref} in ${full_path}"
		resolve_ref "${full_path}" "${ref}" >/dev/null ||
			die "Fetched branch but cannot resolve origin/${ref} in ${full_path}"
		return 0
	fi

	if resolve_ref "${full_path}" "${ref}" >/dev/null; then
		return 0
	fi

	if [[ ${DRY_RUN} -eq 1 ]]; then
		run_cmd git -C "${full_path}" fetch --tags origin "${ref}"
		log "[DRY] fallback if the exact ref is not advertised:"
		run_cmd git -C "${full_path}" fetch --tags origin '+refs/heads/*:refs/remotes/origin/*'
		return 0
	fi

	if git -C "${full_path}" fetch --tags origin "${ref}"; then
		resolve_ref "${full_path}" "${ref}" >/dev/null ||
			die "Fetched ref but cannot resolve ${ref} in ${full_path}"
		return 0
	fi

	warn "Exact ref ${ref} was not advertised; fetching remote heads and tags"
	if ! git -C "${full_path}" fetch --tags origin '+refs/heads/*:refs/remotes/origin/*'; then
		die "Unable to fetch advertised refs from origin in ${full_path}"
	fi
	resolve_ref "${full_path}" "${ref}" >/dev/null ||
		die "Locked ref ${ref} is not reachable from advertised heads or tags in ${full_path}"
}

checkout_detached() {
	local full_path="$1"
	local ref="$2"
	local resolved_ref

	ensure_ref_available "${full_path}" "${ref}"
	if [[ ${DRY_RUN} -eq 1 ]]; then
		run_cmd git -C "${full_path}" checkout --detach "${ref}"
		return 0
	fi

	resolved_ref="$(resolve_ref "${full_path}" "${ref}")" || die "Unable to resolve ${ref} in ${full_path}"
	run_cmd git -C "${full_path}" checkout --detach "${resolved_ref}"
}

sync_submodules() {
	local full_path="$1"
	[[ ${WITH_SUBMODULES} -eq 1 ]] || return 0

	run_cmd git -C "${full_path}" submodule sync --recursive
	run_cmd git -C "${full_path}" submodule update --init --recursive
}

verify_origin() {
	local full_path="$1"
	local expected_url="$2"
	local actual_url

	actual_url="$(git -C "${full_path}" remote get-url origin 2>/dev/null || true)"
	[[ -n "${actual_url}" ]] || return 1
	[[ "$(normalize_repo_url "${actual_url}")" == "$(normalize_repo_url "${expected_url}")" ]]
}

process_repository() {
	local manifest_path="$1"
	local repo_url="$2"
	local repo_ref="$3"
	local target_dir
	local full_path
	local current_head
	local expected_head

	local repo_blocked=0
	target_dir="${manifest_path#src/}"
	full_path="${SRC_DIR}/${target_dir}"

	log "[PLAN] ${target_dir} <= ${repo_url} @ ${repo_ref}"
	PLANNED_COUNT=$((PLANNED_COUNT + 1))

	if ! git -C "${full_path}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
		if [[ -e "${full_path}" ]]; then
			if [[ ${DRY_RUN} -eq 1 || ${VERIFY_ONLY} -eq 1 ]]; then
				record_blocker "${full_path} exists but is not a Git repository"
				return 0
			fi
			die "${full_path} exists but is not a Git repository"
		fi
		if [[ ${VERIFY_ONLY} -eq 1 ]]; then
			record_blocker "missing repository: ${full_path}"
			return 0
		fi

		log "[CLONE] ${target_dir}"
		# Use init + exact fetch instead of git clone so the restored dependency
		# has no implicit local default branch. Only remote refs/tags and the
		# requested detached commit are created.
		run_cmd mkdir -p "${full_path}"
		run_cmd git -C "${full_path}" init
		run_cmd git -C "${full_path}" remote add origin "${repo_url}"
		if [[ ${DRY_RUN} -eq 1 ]]; then
			run_cmd git -C "${full_path}" fetch --tags origin "${repo_ref}"
			log "[DRY] fallback if the exact ref is not advertised:"
			run_cmd git -C "${full_path}" fetch --tags origin '+refs/heads/*:refs/remotes/origin/*'
			run_cmd git -C "${full_path}" checkout --detach "${repo_ref}"
			if [[ ${WITH_SUBMODULES} -eq 1 ]]; then
				run_cmd git -C "${full_path}" submodule update --init --recursive
			fi
			CLONED_COUNT=$((CLONED_COUNT + 1))
			return 0
		fi

		checkout_detached "${full_path}" "${repo_ref}"
		sync_submodules "${full_path}"
		CLONED_COUNT=$((CLONED_COUNT + 1))
	else
		if ! verify_origin "${full_path}" "${repo_url}"; then
			if [[ ${DRY_RUN} -eq 1 || ${VERIFY_ONLY} -eq 1 ]]; then
				record_blocker "origin mismatch: ${full_path}"
				return 0
			fi
			die "Origin URL mismatch in ${full_path}; refusing to change remotes"
		fi

		if repo_is_dirty "${full_path}"; then
			if [[ ${DRY_RUN} -eq 1 || ${VERIFY_ONLY} -eq 1 ]]; then
				record_blocker "dirty repository: ${full_path}"
				repo_blocked=1
			else
				die "Dirty repository: ${full_path}. Preserve or commit local changes before syncing."
			fi
		fi

		if [[ ${DO_UPDATE} -eq 1 ]] && ! is_locked_sha "${repo_ref}"; then
			ensure_ref_available "${full_path}" "${repo_ref}"
		fi
		current_head="$(git -C "${full_path}" rev-parse HEAD)"
		if is_locked_sha "${repo_ref}"; then
			expected_head="${repo_ref,,}"
		else
			expected_head="$(resolve_ref "${full_path}" "${repo_ref}" || true)"
		fi

		if [[ -n "${expected_head}" && "${current_head,,}" == "${expected_head,,}" ]]; then
			log "[OK] ${target_dir} already at selected ref"
			if [[ ${VERIFY_ONLY} -eq 0 ]]; then
				sync_submodules "${full_path}"
			fi
			VERIFIED_COUNT=$((VERIFIED_COUNT + 1))
			return 0
		fi

		if [[ ${DO_UPDATE} -eq 0 ]]; then
			if [[ ${DRY_RUN} -eq 1 || ${VERIFY_ONLY} -eq 1 ]]; then
				record_blocker "${target_dir} HEAD ${current_head} does not match ${repo_ref}; use --update"
				return 0
			fi
			die "${target_dir} HEAD ${current_head} does not match ${repo_ref}; use --update"
		fi

		if [[ ${repo_blocked} -eq 1 ]]; then
			warn "[SKIP] ${target_dir} cannot be updated until its blocker(s) are resolved"
			return 0
		fi

		log "[SYNC] ${target_dir} -> ${repo_ref} (detached HEAD)"
		checkout_detached "${full_path}" "${repo_ref}"
		sync_submodules "${full_path}"
		UPDATED_COUNT=$((UPDATED_COUNT + 1))
	fi

	if [[ ${DRY_RUN} -eq 0 ]]; then
		current_head="$(git -C "${full_path}" rev-parse HEAD)"
		if is_locked_sha "${repo_ref}"; then
			expected_head="${repo_ref,,}"
		else
			expected_head="$(resolve_ref "${full_path}" "${repo_ref}")" ||
				die "Cannot resolve selected branch after checkout: ${repo_ref}"
		fi
		[[ "${current_head,,}" == "${expected_head,,}" ]] ||
			die "Post-checkout verification failed for ${target_dir}: ${current_head} != ${expected_head}"
	fi
}

verify_ros_packages() {
	local -a required_packages=(
		px4_msgs
		offboard_cpp
		vision_to_dds
	)
	local selected_profile
	for selected_profile in "${SELECTED_PROFILES[@]}"; do
		if [[ "${selected_profile}" == optional-perception ]]; then
			required_packages+=(realsense2_camera)
		fi
	done
	local package
	local colcon_output
	local missing=0

	[[ ${SKIP_PACKAGE_CHECK} -eq 0 ]] || {
		log "[SKIP] ROS package discovery disabled"
		return 0
	}

	if ! command -v colcon >/dev/null 2>&1; then
		if [[ ${REQUIRE_COLCON} -eq 1 ]]; then
			die "colcon is required but not installed"
		fi
		warn "colcon not found; repositories are restored but ROS package discovery was skipped"
		return 0
	fi

	if [[ ${DRY_RUN} -eq 1 ]]; then
		run_cmd colcon list --base-paths "${SRC_DIR}"
		return 0
	fi

	if ! colcon_output="$(colcon list --base-paths "${SRC_DIR}" 2>&1)"; then
		if [[ ${REQUIRE_COLCON} -eq 1 ]]; then
			die "colcon list failed for ${SRC_DIR}: ${colcon_output}"
		fi
		warn "colcon list failed; Git repository restoration remains valid"
		warn "${colcon_output}"
		return 0
	fi
	printf '%s\n' "${colcon_output}"

	for package in "${required_packages[@]}"; do
		if ! awk -v expected="${package}" '$1 == expected { found = 1 } END { exit !found }' <<<"${colcon_output}"; then
			printf '[ERROR] Required ROS package missing: %s\n' "${package}" >&2
			missing=1
		fi
	done

	if [[ ${missing} -ne 0 ]]; then
		if [[ ${REQUIRE_COLCON} -eq 1 ]]; then
			die "Workspace package verification failed"
		fi
		warn "One or more expected ROS packages were not discovered"
	fi
}

for record in "${REPOSITORIES[@]}"; do
	IFS=$'\t' read -r manifest_path repo_url repo_ref <<<"${record}"
	process_repository "${manifest_path}" "${repo_url}" "${repo_ref}"
done

verify_ros_packages

log "Summary: planned=${PLANNED_COUNT} cloned=${CLONED_COUNT} updated=${UPDATED_COUNT} verified=${VERIFIED_COUNT} blockers=${BLOCKER_COUNT}"

log "Default DDS baseline omits archive, navigation and quarantined serial sources"
log "Intentionally excluded from restore/build: offboard_py, cv_yolo_paddle_pkg, opencv_cpp"

if [[ (${DRY_RUN} -eq 1 || ${VERIFY_ONLY} -eq 1) && ${BLOCKER_COUNT} -gt 0 ]]; then
	warn "Audit found ${BLOCKER_COUNT} blocker(s); no files or Git refs were changed"
	exit 1
fi

log "Done."
