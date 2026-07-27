#!/usr/bin/env python3
"""Validate synthetic active/archive/optional dependency profile catalogs."""

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import sys


EXACT_SHA = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_PROFILES = {
    "active": "active",
    "archive": "archive",
    "optional-perception": "optional",
    "optional-navigation": "optional",
}
OPTIONAL_PROFILE_IDS = {
    "perception": "optional-perception",
    "navigation": "optional-navigation",
}
REQUIRED_DECISION = {
    "path": "src/serial_driver_ros",
    "status": "REQUIRES_MAINTAINER_DECISION",
}


class ProfileError(RuntimeError):
    """A deterministic catalog structure or policy error."""


def load_catalog(path):
    """Load one strict JSON fixture without third-party dependencies."""
    try:
        with Path(path).open("r", encoding="utf-8") as stream:
            data = json.load(stream)
    except (OSError, ValueError) as exc:
        raise ProfileError("cannot load catalog {}: {}".format(path, exc))
    if not isinstance(data, dict):
        raise ProfileError("catalog must be a JSON object")
    return data


def _safe_source_path(value):
    if not isinstance(value, str) or not value:
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and len(path.parts) >= 2
        and path.parts[0] == "src"
        and ".." not in path.parts
        and "." not in path.parts
        and str(path) == value
    )


def validate_catalog(catalog):
    """Return all fail-closed policy issues in deterministic order."""
    issues = []
    expected_top = {
        "schema_version",
        "default_restore",
        "canonical_urls",
        "profiles",
        "maintainer_decisions",
    }
    extra_top = sorted(set(catalog) - expected_top)
    missing_top = sorted(expected_top - set(catalog))
    if extra_top:
        issues.append("unknown top-level fields: {}".format(extra_top))
    if missing_top:
        issues.append("missing top-level fields: {}".format(missing_top))
    if missing_top:
        return issues

    if catalog["schema_version"] != 1:
        issues.append("schema_version must be 1")
    if catalog["default_restore"] != ["active"]:
        issues.append("default_restore must be exactly ['active']")

    canonical_urls = catalog["canonical_urls"]
    if not isinstance(canonical_urls, dict) or not canonical_urls:
        issues.append("canonical_urls must be a non-empty object")
        canonical_urls = {}
    else:
        for repository_id, url in sorted(canonical_urls.items()):
            if not isinstance(repository_id, str) or not repository_id:
                issues.append("canonical repository IDs must be non-empty strings")
            if (
                not isinstance(url, str)
                or not url.startswith("https://")
                or not url.endswith(".git")
            ):
                issues.append(
                    "canonical URL for {} must be exact HTTPS and end in .git".format(
                        repository_id
                    )
                )

    profiles = catalog["profiles"]
    if not isinstance(profiles, dict):
        issues.append("profiles must be an object")
        profiles = {}
    missing_profiles = sorted(set(EXPECTED_PROFILES) - set(profiles))
    extra_profiles = sorted(set(profiles) - set(EXPECTED_PROFILES))
    if missing_profiles:
        issues.append("missing profiles: {}".format(missing_profiles))
    if extra_profiles:
        issues.append("unknown profiles: {}".format(extra_profiles))

    seen_paths = {}
    seen_ids = {}
    for profile_id in sorted(EXPECTED_PROFILES):
        profile = profiles.get(profile_id)
        if not isinstance(profile, dict):
            if profile_id in profiles:
                issues.append("{} must be an object".format(profile_id))
            continue
        if set(profile) != {"kind", "repositories"}:
            issues.append(
                "{} must contain exactly kind and repositories".format(profile_id)
            )
        if profile.get("kind") != EXPECTED_PROFILES[profile_id]:
            issues.append(
                "{}.kind must be {}".format(
                    profile_id, EXPECTED_PROFILES[profile_id]
                )
            )
        repositories = profile.get("repositories")
        if not isinstance(repositories, list) or not repositories:
            issues.append("{} repositories must be a non-empty list".format(profile_id))
            continue
        for index, entry in enumerate(repositories):
            label = "{}.repositories[{}]".format(profile_id, index)
            if not isinstance(entry, dict):
                issues.append("{} must be an object".format(label))
                continue
            required_entry = {"repository_id", "path", "type", "url", "version"}
            if set(entry) != required_entry:
                issues.append(
                    "{} must contain exactly {}".format(
                        label, sorted(required_entry)
                    )
                )
                continue
            repository_id = entry["repository_id"]
            path = entry["path"]
            url = entry["url"]
            version = entry["version"]
            if not isinstance(repository_id, str) or not repository_id:
                issues.append("{}.repository_id is required".format(label))
            elif repository_id in seen_ids:
                issues.append(
                    "duplicate repository_id {} in {} and {}".format(
                        repository_id, seen_ids[repository_id], profile_id
                    )
                )
            else:
                seen_ids[repository_id] = profile_id
            if not _safe_source_path(path):
                issues.append("{}.path must be a safe src/ path".format(label))
            elif path in seen_paths:
                issues.append(
                    "duplicate path {} in {} and {}".format(
                        path, seen_paths[path], profile_id
                    )
                )
            else:
                seen_paths[path] = profile_id
            if entry["type"] != "git":
                issues.append("{}.type must be git".format(label))
            expected_url = canonical_urls.get(repository_id)
            if expected_url is None:
                issues.append(
                    "{} has no canonical URL for {}".format(label, repository_id)
                )
            elif url != expected_url:
                issues.append(
                    "URL mismatch for {}: expected {}, got {}".format(
                        repository_id, expected_url, url
                    )
                )
            if not isinstance(version, str) or not EXACT_SHA.fullmatch(version):
                issues.append(
                    "{} uses a moving or non-exact ref: {}".format(label, version)
                )

    decisions = catalog["maintainer_decisions"]
    if not isinstance(decisions, list):
        issues.append("maintainer_decisions must be a list")
        decisions = []
    if REQUIRED_DECISION not in decisions:
        issues.append(
            "src/serial_driver_ros must remain REQUIRES_MAINTAINER_DECISION"
        )
    decision_paths = set()
    for index, decision in enumerate(decisions):
        label = "maintainer_decisions[{}]".format(index)
        if not isinstance(decision, dict) or set(decision) != {"path", "status"}:
            issues.append("{} must contain exactly path and status".format(label))
            continue
        path = decision["path"]
        if not _safe_source_path(path):
            issues.append("{}.path must be a safe src/ path".format(label))
        if path in decision_paths:
            issues.append("duplicate maintainer decision path {}".format(path))
        decision_paths.add(path)
        if path in seen_paths:
            issues.append(
                "unresolved decision path {} must not appear in a restore profile".format(
                    path
                )
            )

    return issues


def selected_profiles(catalog, with_archive=False, optional=()):
    """Resolve a validated profile selection without changing the catalog."""
    issues = validate_catalog(catalog)
    if issues:
        raise ProfileError("; ".join(issues))
    profile_ids = list(catalog["default_restore"])
    if with_archive:
        profile_ids.append("archive")
    for name in optional:
        profile_id = OPTIONAL_PROFILE_IDS[name]
        if profile_id not in profile_ids:
            profile_ids.append(profile_id)
    repositories = []
    for profile_id in profile_ids:
        repositories.extend(catalog["profiles"][profile_id]["repositories"])
    return profile_ids, repositories


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Validate a synthetic exact-SHA dependency profile catalog and "
            "resolve an explicit offline restore selection."
        )
    )
    parser.add_argument("catalog", help="Strict JSON profile catalog")
    parser.add_argument(
        "--with-archive",
        action="store_true",
        help="Explicitly add the archive profile to the default active selection",
    )
    parser.add_argument(
        "--with-optional",
        action="append",
        choices=sorted(OPTIONAL_PROFILE_IDS),
        default=[],
        help="Explicitly add one optional source profile; repeat as needed",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        catalog = load_catalog(args.catalog)
        profile_ids, repositories = selected_profiles(
            catalog,
            with_archive=args.with_archive,
            optional=args.with_optional,
        )
    except ProfileError as exc:
        print(
            json.dumps(
                {"status": "FAIL", "issues": str(exc).split("; ")},
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    print(
        json.dumps(
            {
                "status": "PASS",
                "selected_profiles": profile_ids,
                "repository_paths": [entry["path"] for entry in repositories],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
