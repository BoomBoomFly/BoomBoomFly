#!/usr/bin/env python3
"""Verify that the working tree matches the exact vcstool manifests."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "px4" / "px4_ws" / "src"
CORE_MANIFEST_ROOTS = (
    (ROOT / "manifests" / "boomboom.repos", SOURCES),
    (ROOT / "manifests" / "upstream.repos", ROOT / "px4" / "upstream"),
)
PERCEPTION_MANIFEST_ROOT = (
    ROOT / "manifests" / "perception.repos",
    SOURCES,
)
FULL_SHA = re.compile(r"[0-9a-f]{40}")


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", "-C", str(repo), *args),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def normalize_url(value: str) -> str:
    return value.strip().removesuffix("/")


def load_manifest(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8") as stream:
        document = yaml.safe_load(stream)
    repositories = document.get("repositories") if isinstance(document, dict) else None
    if not isinstance(repositories, dict):
        raise ValueError(f"{path}: missing repositories mapping")
    return repositories


def verify_repository(
    manifest: Path,
    base: Path,
    relative: str,
    specification: dict[str, str],
    errors: list[str],
) -> Path:
    label = f"{manifest.name}:{relative}"
    version = str(specification.get("version", ""))
    if FULL_SHA.fullmatch(version) is None:
        errors.append(f"{label}: version is not an exact 40-character commit: {version!r}")

    repo = (base / relative).resolve()
    if not repo.is_dir():
        errors.append(f"{label}: repository directory is missing: {repo}")
        return repo

    top_level = git(repo, "rev-parse", "--show-toplevel")
    if top_level.returncode != 0 or Path(top_level.stdout.strip()).resolve() != repo:
        errors.append(f"{label}: directory is not the root of a Git repository")
        return repo

    head = git(repo, "rev-parse", "HEAD")
    if head.returncode != 0 or head.stdout.strip() != version:
        errors.append(f"{label}: HEAD {head.stdout.strip()!r} does not match {version}")

    expected_url = normalize_url(str(specification.get("url", "")))
    actual_url = git(repo, "remote", "get-url", "origin")
    if actual_url.returncode != 0 or normalize_url(actual_url.stdout) != expected_url:
        errors.append(
            f"{label}: origin {actual_url.stdout.strip()!r} does not match {expected_url!r}"
        )

    status = git(repo, "status", "--porcelain")
    if status.returncode != 0 or status.stdout:
        errors.append(f"{label}: working tree is dirty\n{status.stdout.rstrip()}")

    if base == SOURCES and relative.startswith("boomboom/") and (repo / ".gitmodules").is_file():
        submodules = git(repo, "submodule", "status", "--recursive")
        if submodules.returncode != 0:
            errors.append(f"{label}: unable to inspect submodules: {submodules.stderr.strip()}")
        for line in submodules.stdout.splitlines():
            if line[:1] in {"-", "+", "U"}:
                errors.append(f"{label}: submodule is not at its recorded commit: {line}")

    return repo


def unmanaged_ros_packages(managed: set[Path], errors: list[str]) -> None:
    boomboom = SOURCES / "boomboom"
    if not boomboom.is_dir():
        return
    for package_xml in sorted(boomboom.rglob("package.xml")):
        package_dir = package_xml.parent.resolve()
        owner = git(package_dir, "rev-parse", "--show-toplevel")
        if owner.returncode != 0:
            errors.append(f"unmanaged ROS package (no Git owner): {package_dir}")
            continue
        owner_path = Path(owner.stdout.strip()).resolve()
        if owner_path not in managed:
            errors.append(
                f"unmanaged ROS package: {package_dir} belongs to unlisted repository {owner_path}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="verify that checked-out repositories match the exact manifests"
    )
    parser.add_argument(
        "--with-perception",
        action="store_true",
        help="also verify repositories from manifests/perception.repos",
    )
    args = parser.parse_args()

    errors: list[str] = []
    managed: set[Path] = set()
    repository_count = 0
    manifest_roots = list(CORE_MANIFEST_ROOTS)
    if args.with_perception:
        manifest_roots.append(PERCEPTION_MANIFEST_ROOT)

    for manifest, base in manifest_roots:
        try:
            repositories = load_manifest(manifest)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(str(exc))
            continue
        for relative, specification in sorted(repositories.items()):
            if not isinstance(specification, dict) or specification.get("type") != "git":
                errors.append(f"{manifest.name}:{relative}: only Git repositories are supported")
                continue
            managed.add(
                verify_repository(manifest, base, relative, specification, errors)
            )
            repository_count += 1

    for repository in tuple(managed):
        submodules = git(
            repository, "submodule", "foreach", "--quiet", "--recursive", "pwd"
        )
        if submodules.returncode != 0:
            errors.append(
                f"{repository}: unable to enumerate submodules: {submodules.stderr.strip()}"
            )
            continue
        managed.update(Path(line).resolve() for line in submodules.stdout.splitlines() if line)

    unmanaged_ros_packages(managed, errors)

    if errors:
        print("repository verification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"verified {repository_count} exact, clean repositories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
