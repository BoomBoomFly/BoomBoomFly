#!/usr/bin/env python3
"""同步已存在的清单仓库：分支快进，固定提交仅 fetch；不覆盖本地修改。"""
import argparse
import subprocess
import sys
from pathlib import Path

from verify_repos import (CORE_MANIFEST_ROOTS, PERCEPTION_DEPS_MANIFEST_ROOT,
                          FULL_SHA, git, load_manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("pull", "update"))
    parser.add_argument("--with-perception-deps", "--with-perception", action="store_true")
    args = parser.parse_args()
    manifests = list(CORE_MANIFEST_ROOTS)
    if args.with_perception_deps or args.mode == "update":
        manifests.append(PERCEPTION_DEPS_MANIFEST_ROOT)
    repositories = []
    missing = []
    for manifest, base in manifests:
        for relative, spec in load_manifest(manifest).items():
            repo = base / relative
            if repo.is_symlink():
                sys.exit(f"error: repository path is a symlink: {repo}")
            if not repo.exists() or (repo.is_dir() and not any(repo.iterdir())):
                if args.mode == "pull":
                    missing.append((repo, str(spec["version"]), spec["url"]))
                continue
            top = git(repo, "rev-parse", "--show-toplevel")
            if top.returncode or Path(top.stdout.strip()).resolve() != repo.resolve():
                sys.exit(f"error: not a Git repository: {repo}")
            status = git(repo, "status", "--porcelain")
            # 固定提交只 fetch，不改工作树；本地构建产物不应阻塞其他仓库。
            if status.returncode or (status.stdout and not FULL_SHA.fullmatch(str(spec["version"]))):
                sys.exit(f"error: refusing to update dirty repository: {repo}")
            if git(repo, "remote", "get-url", "origin").stdout.strip() != spec["url"]:
                sys.exit(f"error: origin differs from manifest: {repo}")
            repositories.append((repo, str(spec["version"])))

    # 所有已有路径检查通过后再克隆；Git 可以直接克隆到空占位目录。
    for repo, version, url in missing:
        repo.parent.mkdir(parents=True, exist_ok=True)
        if FULL_SHA.fullmatch(version):
            subprocess.run(["git", "clone", "--no-checkout", url, str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "checkout", "--detach", version], check=True)
        else:
            subprocess.run(["git", "clone", "--branch", version, url, str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "submodule", "update", "--init", "--recursive"], check=True)

    for repo, version in repositories:
        def run(*args):
            subprocess.run(["git", "-C", str(repo), *args], check=True)

        print(f"[SYNC] {repo} ({version})", flush=True)
        run("fetch", "origin")
        if FULL_SHA.fullmatch(version):
            continue
        target = f"refs/remotes/origin/{version}"
        # 旧清单导入的是 detached HEAD，只有可快进时才迁回分支，保留本地提交。
        run("merge-base", "--is-ancestor", "HEAD", target)
        run("switch", version)
        run("merge", "--ff-only", target)
        if git(repo, "rev-parse", "HEAD").stdout != git(repo, "rev-parse", target).stdout:
            sys.exit(f"error: local branch has extra commits: {repo}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        sys.exit(f"error: {error}")
