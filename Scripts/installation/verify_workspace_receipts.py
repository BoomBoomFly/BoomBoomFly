#!/usr/bin/env python3
"""Capture and verify fail-closed receipts for preserved dirty checkouts."""

import argparse
import base64
import binascii
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


EXIT_OK = 0
EXIT_INVALID = 1
EXIT_UNAPPROVED = 2
HEX64 = set("0123456789abcdef")
REQUIRED_RECEIPT_KEYS = {
    "schema_version",
    "receipt_id",
    "baseline_status",
    "observed_at",
    "repository",
    "checkout",
    "tracked_diff",
    "staged_diff",
    "untracked_files",
    "file_mode_differences",
    "classifications",
    "patch",
    "content",
    "applicable_platform",
    "business_purpose",
    "replay_order",
    "maintainer_confirmation",
}


class ReceiptError(RuntimeError):
    """Expected verification or capture error."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in HEX64 for character in value.lower())
    )


def run(
    command: Sequence[str],
    acceptable: Iterable[int] = (0,),
    input_bytes: Optional[bytes] = None,
) -> bytes:
    completed = subprocess.run(
        list(command),
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode not in tuple(acceptable):
        stderr = completed.stderr.decode("utf-8", "replace").strip()
        raise ReceiptError(
            "command failed (exit {}): {}\n{}".format(
                completed.returncode, " ".join(command), stderr
            )
        )
    return completed.stdout


def git(repo: Path, arguments: Sequence[str], acceptable: Iterable[int] = (0,)) -> bytes:
    return run(["git", "-C", str(repo)] + list(arguments), acceptable=acceptable)


def git_with_work_tree(
    git_dir: Path,
    work_tree: Path,
    arguments: Sequence[str],
    acceptable: Iterable[int] = (0,),
) -> bytes:
    return run(
        [
            "git",
            "-C",
            str(work_tree),
            "--git-dir",
            str(git_dir),
            "--work-tree",
            str(work_tree),
        ]
        + list(arguments),
        acceptable=acceptable,
    )


def resolve_git_root(candidate: Path) -> Path:
    output = run(
        ["git", "-C", str(candidate), "rev-parse", "--show-toplevel"]
    ).decode("utf-8", "strict").strip()
    return Path(output).resolve()


def safe_relative(value: str, label: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or value in ("", "."):
        raise ReceiptError("{} must be a repository-relative path: {}".format(label, value))
    return path


def within(root: Path, relative: str, label: str) -> Path:
    path = safe_relative(relative, label)
    resolved = (root / path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        raise ReceiptError("{} escapes repository root: {}".format(label, relative))
    return resolved


def normalize_origin(value: str) -> str:
    normalized = value.strip()
    if normalized.startswith("git@github.com:"):
        normalized = "https://github.com/" + normalized[len("git@github.com:") :]
    elif normalized.startswith("ssh://git@github.com/"):
        normalized = "https://github.com/" + normalized[len("ssh://git@github.com/") :]
    return normalized.rstrip("/").removesuffix(".git") if sys.version_info >= (3, 9) else (
        normalized.rstrip("/")[:-4]
        if normalized.rstrip("/").endswith(".git")
        else normalized.rstrip("/")
    )


def untracked_paths(repo: Path) -> List[str]:
    output = git(repo, ["ls-files", "--others", "--exclude-standard", "-z"])
    return sorted(
        (os.fsdecode(item) for item in output.split(b"\0") if item),
        key=lambda value: os.fsencode(value),
    )


def canonical_patch(repo: Path) -> Tuple[bytes, bytes]:
    tracked = git(
        repo,
        [
            "diff",
            "--binary",
            "--full-index",
            "--no-ext-diff",
            "--no-textconv",
            "HEAD",
            "--",
        ],
    )
    combined = bytearray(tracked)
    for relative in untracked_paths(repo):
        addition = git(
            repo,
            [
                "diff",
                "--no-index",
                "--binary",
                "--full-index",
                "--no-ext-diff",
                "--no-textconv",
                "--",
                "/dev/null",
                relative,
            ],
            acceptable=(0, 1),
        )
        combined.extend(addition)
    return tracked, bytes(combined)


def staged_patch(repo: Path) -> bytes:
    return git(
        repo,
        [
            "diff",
            "--cached",
            "--binary",
            "--full-index",
            "--no-ext-diff",
            "--no-textconv",
            "HEAD",
            "--",
        ],
    )


def git_mode(path: Path) -> Optional[str]:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(mode):
        return "120000"
    if stat.S_ISDIR(mode):
        return "160000"
    if stat.S_ISREG(mode):
        return "100755" if mode & stat.S_IXUSR else "100644"
    raise ReceiptError("unsupported working-tree object: {}".format(path))


def head_entry(repo: Path, relative: str) -> Tuple[str, str]:
    output = git(repo, ["ls-tree", "HEAD", "--", relative]).decode(
        "utf-8", "surrogateescape"
    )
    if not output.strip():
        raise ReceiptError("HEAD entry missing for changed path: {}".format(relative))
    metadata = output.split("\t", 1)[0].split()
    return metadata[0], metadata[2]


def worktree_blob(repo: Path, relative: str) -> Optional[str]:
    path = repo / relative
    if not path.exists() and not path.is_symlink():
        return None
    if path.is_dir() and not path.is_symlink():
        try:
            return git(path, ["rev-parse", "HEAD"]).decode("ascii").strip()
        except ReceiptError:
            return None
    return git(
        repo, ["hash-object", "--path={}".format(relative), "--", relative]
    ).decode("ascii").strip()


def index_entry(repo: Path, relative: str) -> Tuple[Optional[str], Optional[str]]:
    output = git(repo, ["ls-files", "--stage", "--", relative]).decode(
        "utf-8", "surrogateescape"
    )
    if not output.strip():
        return None, None
    first = output.splitlines()[0].split(None, 3)
    if len(first) < 3 or first[2] != "0":
        raise ReceiptError(
            "unexpected index entry for changed path: {}".format(relative)
        )
    return first[0], first[1]


def modification_category(relative: str) -> str:
    lowered = relative.lower()
    config_markers = (
        "/launch/",
        ".launch.py",
        ".yaml",
        ".yml",
        ".json",
        ".xml",
        "cmakelists.txt",
        ".cmake",
        "package.xml",
    )
    if any(marker in lowered for marker in config_markers):
        return "configuration_modification"
    return "source_modification"


def changed_paths(repo: Path, cached: bool = False) -> List[Tuple[str, str]]:
    arguments = ["diff"]
    if cached:
        arguments.append("--cached")
    arguments += ["--name-status", "-z", "--no-renames", "HEAD", "--"]
    fields = git(repo, arguments).split(b"\0")
    fields = [field for field in fields if field]
    if len(fields) % 2:
        raise ReceiptError("unexpected git name-status output")
    result = []
    for index in range(0, len(fields), 2):
        status_value = fields[index].decode("ascii", "strict")
        relative = os.fsdecode(fields[index + 1])
        result.append((status_value, relative))
    return result


def changed_entries(repo: Path, cached: bool = False) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for status_value, relative in changed_paths(repo, cached=cached):
        old_mode, old_blob = head_entry(repo, relative)
        if cached:
            new_mode, new_blob = index_entry(repo, relative)
        else:
            new_mode = git_mode(repo / relative)
            new_blob = worktree_blob(repo, relative)
        categories: List[str] = []
        if status_value.startswith("D") or new_mode is None:
            categories.append("deletion")
        else:
            content_changed = new_blob != old_blob
            mode_changed = new_mode != old_mode
            if mode_changed and not content_changed:
                categories.append("mode_only")
            else:
                if mode_changed:
                    categories.append("mode_change")
                if content_changed:
                    categories.append(modification_category(relative))
        entries.append(
            {
                "path": relative,
                "git_status": status_value,
                "old_mode": old_mode,
                "new_mode": new_mode,
                "categories": categories,
            }
        )
    return sorted(entries, key=lambda item: os.fsencode(item["path"]))


def object_metadata(path: Path, relative: str) -> Dict[str, Any]:
    mode = git_mode(path)
    if mode is None:
        raise ReceiptError("working-tree path disappeared: {}".format(path))
    if mode == "120000":
        content = os.fsencode(os.readlink(str(path)))
        kind = "symlink"
    elif mode == "160000":
        content = b""
        kind = "directory"
    else:
        content = path.read_bytes()
        kind = "regular"
    return {
        "path": relative,
        "type": kind,
        "mode": mode,
        "sha256": sha256_bytes(content),
    }


def untracked_entries(repo: Path) -> List[Dict[str, Any]]:
    entries = []
    for relative in untracked_paths(repo):
        metadata = object_metadata(repo / relative, relative)
        metadata["categories"] = ["untracked", modification_category(relative)]
        entries.append(metadata)
    return entries


def list_content_paths(
    repo: Path,
    git_dir: Optional[Path] = None,
    work_tree: Optional[Path] = None,
) -> List[str]:
    arguments = ["ls-files", "--cached", "--others", "--exclude-standard", "-z"]
    if git_dir is None:
        output = git(repo, arguments)
    else:
        if work_tree is None:
            raise ReceiptError("work tree is required with git dir")
        output = git_with_work_tree(git_dir, work_tree, arguments)
    return sorted(
        set(os.fsdecode(item) for item in output.split(b"\0") if item),
        key=lambda value: os.fsencode(value),
    )


def content_manifest(
    repo: Path,
    git_dir: Optional[Path] = None,
    work_tree: Optional[Path] = None,
) -> Tuple[str, int]:
    tree = work_tree if work_tree is not None else repo
    entries = []
    for relative in list_content_paths(repo, git_dir=git_dir, work_tree=work_tree):
        path = tree / relative
        if not path.exists() and not path.is_symlink():
            continue
        entries.append(object_metadata(path, relative))
    encoded = json.dumps(
        entries, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256_bytes(encoded), len(entries)


def parse_lock_manifest(path: Path) -> Dict[str, Dict[str, str]]:
    repositories: Dict[str, Dict[str, str]] = {}
    current: Optional[str] = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if line.startswith("  ") and not line.startswith("    ") and line.endswith(":"):
            current = line.strip()[:-1]
            repositories[current] = {}
        elif current is not None and line.startswith("    ") and ":" in line:
            key, value = line.strip().split(":", 1)
            repositories[current][key] = value.strip().strip("'\"")
    return repositories


def count_categories(
    tracked: Sequence[Dict[str, Any]], untracked: Sequence[Dict[str, Any]]
) -> Dict[str, int]:
    counts = {
        "mode_only": 0,
        "mode_change": 0,
        "deletion": 0,
        "source_modification": 0,
        "configuration_modification": 0,
        "untracked": 0,
    }
    for entry in list(tracked) + list(untracked):
        for category in entry["categories"]:
            if category in counts:
                counts[category] += 1
    return counts


def capture_receipt(
    output_root: Path,
    source_root: Path,
    relative_repository: str,
    receipt_name: str,
    observed_at: str,
) -> Tuple[Path, Path]:
    relative_path = safe_relative(relative_repository, "capture repository")
    source_repo = (source_root / relative_path).resolve()
    if not source_repo.is_dir():
        raise ReceiptError("capture repository missing: {}".format(source_repo))
    if git(source_repo, ["status", "--porcelain", "-z"]) == b"":
        raise ReceiptError("capture repository is not dirty: {}".format(relative_repository))

    lock_path = output_root / "workspace.lock.repos"
    lock_entries = parse_lock_manifest(lock_path)
    if relative_repository not in lock_entries:
        raise ReceiptError("repository is not in workspace.lock.repos: {}".format(relative_repository))

    head = git(source_repo, ["rev-parse", "HEAD"]).decode("ascii").strip()
    expected = lock_entries[relative_repository].get("version")
    if head != expected:
        raise ReceiptError(
            "capture HEAD does not match lock for {}: {} != {}".format(
                relative_repository, head, expected
            )
        )
    origin = git(source_repo, ["remote", "get-url", "origin"]).decode(
        "utf-8", "strict"
    ).strip()
    expected_origin = lock_entries[relative_repository].get("url", "")
    if normalize_origin(origin) != normalize_origin(expected_origin):
        raise ReceiptError("capture origin does not match lock: {}".format(relative_repository))

    branch_output = git(
        source_repo, ["symbolic-ref", "--short", "-q", "HEAD"], acceptable=(0, 1)
    ).decode("utf-8", "strict").strip()
    checkout_state = (
        {"state": "branch", "branch": branch_output}
        if branch_output
        else {"state": "detached", "branch": None}
    )
    tracked_bytes, patch_bytes = canonical_patch(source_repo)
    staged_bytes = staged_patch(source_repo)
    tracked = changed_entries(source_repo)
    staged = changed_entries(source_repo, cached=True)
    untracked = untracked_entries(source_repo)
    mode_entries = expected_mode_differences(tracked)
    tree_hash, tree_count = content_manifest(source_repo)

    patch_relative = Path("docs/evidence/receipts/patches") / (
        receipt_name + ".patch.b64"
    )
    patch_path = output_root / patch_relative
    patch_path.parent.mkdir(parents=True, exist_ok=True)
    encoded_patch = base64.b64encode(patch_bytes) + b"\n"
    patch_path.write_bytes(encoded_patch)

    receipt = {
        "schema_version": "1.0.0",
        "receipt_id": "workspace-receipt-{}".format(receipt_name),
        "baseline_status": "unverified",
        "observed_at": observed_at,
        "repository": {
            "path": relative_repository,
            "origin": origin,
            "lock_manifest": "workspace.lock.repos",
            "base_sha": expected,
            "head": head,
        },
        "checkout": checkout_state,
        "tracked_diff": {
            "changed_file_count": len(tracked),
            "patch_sha256": sha256_bytes(tracked_bytes),
            "entries": tracked,
        },
        "staged_diff": {
            "changed_file_count": len(staged),
            "patch_sha256": sha256_bytes(staged_bytes),
            "entries": staged,
        },
        "untracked_files": untracked,
        "file_mode_differences": {
            "count": len(mode_entries),
            "entries": mode_entries,
        },
        "classifications": count_categories(tracked, untracked),
        "patch": {
            "format": "git-diff-binary-v1+base64",
            "artifact_path": patch_relative.as_posix(),
            "artifact_sha256": sha256_bytes(encoded_patch),
            "sha256": sha256_bytes(patch_bytes),
            "includes": ["tracked_diff", "staged_diff", "untracked_files"],
        },
        "content": {
            "algorithm": "workspace-content-manifest-sha256-v1",
            "entry_count": tree_count,
            "sha256": tree_hash,
        },
        "applicable_platform": {
            "status": "unverified",
            "value": None,
            "observed_context": (
                "Audit documents associate this checkout with the Ubuntu 20.04, "
                "ROS 2 Foxy and aarch64 workspace; applicability is not confirmed."
            ),
        },
        "business_purpose": {
            "status": "unverified",
            "value": None,
            "observed_context": (
                "The current differences are preserved observations. Their business "
                "necessity has not been confirmed by a maintainer."
            ),
        },
        "replay_order": [
            "verify_origin_and_head",
            "apply_patch_artifact",
            "verify_content_manifest_sha256",
            "obtain_maintainer_confirmation",
        ],
        "maintainer_confirmation": {
            "status": "unapproved",
            "reviewer": None,
            "confirmed_at": None,
            "notes": "No maintainer confirmation was present at capture time.",
        },
    }
    receipt_path = output_root / "docs/evidence/receipts" / (
        receipt_name + ".json"
    )
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt_path, patch_path


def json_schema_errors(instance: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema is required for receipt validation"]
    try:
        validator = jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        )
    except jsonschema.exceptions.SchemaError as error:
        return ["invalid workspace receipt schema: {}".format(error.message)]
    errors = []
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.path) or "<root>"
        errors.append("schema {}: {}".format(location, error.message))
    return errors


def require_mapping(value: Any, label: str, errors: List[str]) -> Dict[str, Any]:
    if not isinstance(value, dict):
        errors.append("{} must be an object".format(label))
        return {}
    return value


def validate_structure(receipt: Dict[str, Any]) -> List[str]:
    errors = []
    missing = sorted(REQUIRED_RECEIPT_KEYS - set(receipt))
    if missing:
        errors.append("missing required field(s): {}".format(", ".join(missing)))
    if receipt.get("schema_version") != "1.0.0":
        errors.append("unsupported schema_version")
    if receipt.get("baseline_status") not in ("unverified", "approved"):
        errors.append("baseline_status must be unverified or approved")
    repository = require_mapping(receipt.get("repository"), "repository", errors)
    for field in ("path", "origin", "lock_manifest", "base_sha", "head"):
        if field not in repository:
            errors.append("repository.{} is required".format(field))
    for field in ("base_sha", "head"):
        value = repository.get(field)
        if not isinstance(value, str) or len(value) != 40:
            errors.append("repository.{} must be a 40-character SHA".format(field))
    patch = require_mapping(receipt.get("patch"), "patch", errors)
    content = require_mapping(receipt.get("content"), "content", errors)
    for label, mapping in (("patch", patch), ("content", content)):
        if not is_sha256(mapping.get("sha256")):
            errors.append("{}.sha256 must be a SHA-256".format(label))
    if not is_sha256(patch.get("artifact_sha256")):
        errors.append("patch.artifact_sha256 must be a SHA-256")
    confirmation = require_mapping(
        receipt.get("maintainer_confirmation"), "maintainer_confirmation", errors
    )
    if confirmation.get("status") not in ("approved", "unapproved"):
        errors.append("maintainer_confirmation.status must be approved or unapproved")
    if confirmation.get("status") == "approved":
        if not confirmation.get("reviewer") or not confirmation.get("confirmed_at"):
            errors.append("approved receipt requires reviewer and confirmed_at")
    return errors


def expected_mode_differences(
    tracked: Sequence[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    return [
        {
            "path": entry["path"],
            "old_mode": entry["old_mode"],
            "new_mode": entry["new_mode"],
        }
        for entry in tracked
        if entry["old_mode"] != entry["new_mode"]
        and entry["new_mode"] is not None
    ]


def compare_inventory(
    label: str,
    recorded: Dict[str, Any],
    actual_entries: Sequence[Dict[str, Any]],
    errors: List[str],
) -> None:
    recorded_entries = recorded.get("entries")
    recorded_count = recorded.get("changed_file_count")
    if not isinstance(recorded_entries, list):
        errors.append("{}.entries must be an array".format(label))
        return
    if recorded_count != len(recorded_entries):
        errors.append("{} count does not match entries length".format(label))
    if list(actual_entries) != recorded_entries:
        errors.append("{} entries mismatch".format(label))
    if recorded_count != len(actual_entries):
        errors.append("{} changed_file_count mismatch".format(label))


def validate_approval(
    receipt: Dict[str, Any], errors: List[str], warnings: List[str]
) -> None:
    confirmation = receipt["maintainer_confirmation"]
    approved = confirmation["status"] == "approved"
    if not approved:
        warnings.append("UNAPPROVED: maintainer confirmation is absent")
        if receipt["baseline_status"] == "approved":
            errors.append("baseline_status=approved requires maintainer approval")
        return
    if receipt["baseline_status"] != "approved":
        errors.append("approved confirmation requires baseline_status=approved")
    for label in ("applicable_platform", "business_purpose"):
        claim = receipt[label]
        if claim.get("status") not in ("verified", "approved"):
            errors.append(
                "approved receipt requires {} status verified/approved".format(label)
            )
        value = claim.get("value")
        if not isinstance(value, str) or not value.strip():
            errors.append("approved receipt requires non-empty {} value".format(label))


def patch_paths_are_safe(patch: bytes) -> bool:
    for raw_line in patch.splitlines():
        if not raw_line.startswith((b"diff --git ", b"--- ", b"+++ ")):
            continue
        text = raw_line.decode("utf-8", "surrogateescape")
        if "/home/" in text or "/root/" in text:
            return False
        fields = text.split()
        for field in fields[1:]:
            if field == "/dev/null":
                continue
            candidate = field[2:] if field.startswith(("a/", "b/")) else field
            if candidate.startswith("/") or ".." in Path(candidate).parts:
                return False
    return True


def decode_patch_artifact(
    root: Path, receipt: Dict[str, Any]
) -> Tuple[Path, bytes]:
    artifact_path = within(root, receipt["patch"]["artifact_path"], "patch artifact")
    encoded = artifact_path.read_bytes()
    if sha256_bytes(encoded) != receipt["patch"]["artifact_sha256"]:
        raise ReceiptError("patch artifact hash mismatch")
    try:
        decoded = base64.b64decode(encoded.strip(), validate=True)
    except (ValueError, binascii.Error) as error:
        raise ReceiptError("patch artifact is not valid base64: {}".format(error))
    return artifact_path, decoded


def validate_receipt(
    root: Path,
    receipt_path: Path,
    source_root: Optional[Path] = None,
    schema_document: Optional[Dict[str, Any]] = None,
) -> Tuple[List[str], List[str], Optional[Dict[str, Any]]]:
    errors: List[str] = []
    warnings: List[str] = []
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return ["cannot read receipt: {}".format(error)], warnings, None
    if not isinstance(receipt, dict):
        return ["receipt root must be an object"], warnings, None
    if schema_document is not None:
        errors.extend(json_schema_errors(receipt, schema_document))
    errors.extend(validate_structure(receipt))
    if errors:
        return errors, warnings, receipt

    repository = receipt["repository"]
    try:
        source_root = source_root if source_root is not None else root
        repository_path = safe_relative(repository["path"], "repository.path")
        repo = (source_root / repository_path).resolve()
        actual_repo_root = resolve_git_root(repo)
        if actual_repo_root != repo:
            errors.append("repository.path is not a Git toplevel")
        manifest_path = within(root, repository["lock_manifest"], "lock manifest")
        lock = parse_lock_manifest(manifest_path)
        locked = lock.get(repository["path"])
        if locked is None:
            errors.append("repository is absent from lock manifest")
        else:
            if locked.get("version") != repository["base_sha"]:
                errors.append("base SHA does not match lock manifest")
            if normalize_origin(locked.get("url", "")) != normalize_origin(
                repository["origin"]
            ):
                errors.append("receipt origin does not match lock manifest")

        actual_origin = git(repo, ["remote", "get-url", "origin"]).decode(
            "utf-8", "strict"
        ).strip()
        actual_head = git(repo, ["rev-parse", "HEAD"]).decode("ascii").strip()
        if normalize_origin(actual_origin) != normalize_origin(repository["origin"]):
            errors.append("origin mismatch")
        if actual_head != repository["head"] or actual_head != repository["base_sha"]:
            errors.append("HEAD mismatch")

        tracked_bytes, combined_bytes = canonical_patch(repo)
        staged_bytes = staged_patch(repo)
        actual_tracked = changed_entries(repo)
        actual_staged = changed_entries(repo, cached=True)
        compare_inventory(
            "tracked_diff", receipt["tracked_diff"], actual_tracked, errors
        )
        compare_inventory(
            "staged_diff", receipt["staged_diff"], actual_staged, errors
        )
        if sha256_bytes(tracked_bytes) != receipt["tracked_diff"]["patch_sha256"]:
            errors.append("tracked patch hash mismatch")
        if sha256_bytes(staged_bytes) != receipt["staged_diff"]["patch_sha256"]:
            errors.append("staged patch hash mismatch")
        if sha256_bytes(combined_bytes) != receipt["patch"]["sha256"]:
            errors.append("working patch hash mismatch")

        _, decoded_patch = decode_patch_artifact(root, receipt)
        if not patch_paths_are_safe(decoded_patch):
            errors.append("patch contains an absolute or escaping path")
        if sha256_bytes(decoded_patch) != receipt["patch"]["sha256"]:
            errors.append("decoded patch hash mismatch")
        if decoded_patch != combined_bytes:
            errors.append("decoded patch does not match checkout")

        actual_untracked = untracked_entries(repo)
        if actual_untracked != receipt["untracked_files"]:
            errors.append("untracked file inventory mismatch")
        recorded_modes = receipt["file_mode_differences"]
        actual_modes = expected_mode_differences(actual_tracked)
        if recorded_modes.get("count") != len(recorded_modes.get("entries", [])):
            errors.append("file_mode_differences count does not match entries length")
        if recorded_modes.get("entries") != actual_modes:
            errors.append("file_mode_differences entries mismatch")
        if recorded_modes.get("count") != len(actual_modes):
            errors.append("file_mode_differences count mismatch")
        actual_classifications = count_categories(actual_tracked, actual_untracked)
        if receipt["classifications"] != actual_classifications:
            errors.append("classifications mismatch")
        content_hash, entry_count = content_manifest(repo)
        if content_hash != receipt["content"]["sha256"]:
            errors.append("content hash mismatch")
        if entry_count != receipt["content"]["entry_count"]:
            errors.append("content entry count mismatch")
    except (OSError, ReceiptError, KeyError, TypeError) as error:
        errors.append(str(error))

    validate_approval(receipt, errors, warnings)
    return errors, warnings, receipt


def filesystem_manifest(root: Path) -> str:
    entries = []
    for path in sorted(root.rglob("*"), key=lambda item: os.fsencode(str(item.relative_to(root)))):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            content = os.fsencode(os.readlink(str(path)))
            kind = "symlink"
        elif path.is_dir():
            continue
        elif path.is_file():
            content = path.read_bytes()
            kind = "regular"
        else:
            raise ReceiptError("unsupported archive object: {}".format(path))
        entries.append(
            {
                "path": relative,
                "type": kind,
                "mode": git_mode(path),
                "sha256": sha256_bytes(content),
            }
        )
    return sha256_bytes(
        json.dumps(
            entries, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    )


def replay_receipt(
    root: Path,
    receipt: Dict[str, Any],
    replay_root: Path,
    source_root: Optional[Path] = None,
) -> List[str]:
    errors: List[str] = []
    try:
        replay_root = replay_root.resolve()
        tmp_root = Path(tempfile.gettempdir()).resolve()
        replay_root.relative_to(tmp_root)
        replay_root.mkdir(parents=True, exist_ok=True)
        source_root = source_root if source_root is not None else root
        repo = within(
            source_root, receipt["repository"]["path"], "repository.path"
        )
        _, decoded_patch = decode_patch_artifact(root, receipt)
        git_dir_text = git(repo, ["rev-parse", "--absolute-git-dir"]).decode(
            "utf-8", "strict"
        ).strip()
        git_dir = Path(git_dir_text)
        with tempfile.TemporaryDirectory(
            prefix="boomboomfly_receipt_replay_", dir=str(replay_root)
        ) as temporary:
            tree = Path(temporary) / "tree"
            tree.mkdir()
            replay_patch_path = Path(temporary) / "workspace.patch"
            replay_patch_path.write_bytes(decoded_patch)
            archive_process = subprocess.Popen(
                ["git", "-C", str(repo), "archive", "--format=tar", "HEAD"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if archive_process.stdout is None:
                raise ReceiptError("cannot open git archive stream")
            extract_process = subprocess.run(
                ["tar", "-xf", "-", "-C", str(tree)],
                stdin=archive_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            archive_process.stdout.close()
            stderr = archive_process.stderr.read() if archive_process.stderr else b""
            if archive_process.stderr is not None:
                archive_process.stderr.close()
            returncode = archive_process.wait()
            if returncode != 0:
                raise ReceiptError(
                    "git archive failed: {}".format(stderr.decode("utf-8", "replace"))
                )
            if extract_process.returncode != 0:
                raise ReceiptError(
                    "tar extraction failed: {}".format(
                        extract_process.stderr.decode("utf-8", "replace")
                    )
                )
            base_hash = filesystem_manifest(tree)
            git_with_work_tree(git_dir, tree, ["apply", "--check", str(replay_patch_path)])
            git_with_work_tree(
                git_dir,
                tree,
                ["apply", "--whitespace=nowarn", str(replay_patch_path)],
            )
            replayed_hash, replayed_count = content_manifest(
                repo, git_dir=git_dir, work_tree=tree
            )
            if replayed_hash != receipt["content"]["sha256"]:
                errors.append("replayed content hash mismatch")
            if replayed_count != receipt["content"]["entry_count"]:
                errors.append("replayed content entry count mismatch")
            git_with_work_tree(
                git_dir, tree, ["apply", "--reverse", "--check", str(replay_patch_path)]
            )
            git_with_work_tree(
                git_dir,
                tree,
                [
                    "apply",
                    "--reverse",
                    "--whitespace=nowarn",
                    str(replay_patch_path),
                ],
            )
            if filesystem_manifest(tree) != base_hash:
                errors.append("reverse apply did not restore archive content")
    except (OSError, ReceiptError, KeyError, ValueError) as error:
        errors.append(str(error))
    return errors


def default_root() -> Path:
    return Path(__file__).resolve().parents[2]


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(
        description=(
            "Verify preserved dirty-checkout receipts without modifying the checkouts. "
            "A structurally valid but unapproved receipt exits 2."
        )
    )
    argument_parser.add_argument(
        "--repository-root",
        type=Path,
        default=default_root(),
        help="BoomBoomFly checkout to verify (default: root containing this script)",
    )
    argument_parser.add_argument(
        "--receipts-dir",
        type=Path,
        help="Receipt directory (default: docs/evidence/receipts below repository root)",
    )
    argument_parser.add_argument(
        "--schema",
        type=Path,
        help="Schema path to require (default: docs/evidence/schemas/workspace_receipt.schema.json)",
    )
    argument_parser.add_argument(
        "--receipt",
        action="append",
        type=Path,
        help="Verify one explicit receipt path; repeatable",
    )
    argument_parser.add_argument(
        "--check-replay",
        action="store_true",
        help="Clean-apply and reverse each patch in a temporary archive copy",
    )
    argument_parser.add_argument(
        "--replay-root",
        type=Path,
        default=Path(tempfile.gettempdir()),
        help="Parent for temporary replay directories; must be below the system temp directory",
    )
    argument_parser.add_argument(
        "--capture",
        action="store_true",
        help="Explicitly write one unapproved receipt and patch artifact",
    )
    argument_parser.add_argument(
        "--source-workspace-root",
        type=Path,
        help=(
            "Workspace containing dirty checkouts; useful when receipts are in "
            "an isolated worktree (default: --repository-root)"
        ),
    )
    argument_parser.add_argument(
        "--capture-repository",
        help="Repository-relative dirty checkout path for --capture",
    )
    argument_parser.add_argument(
        "--receipt-name",
        help="Repository-relative receipt/patch basename for --capture",
    )
    argument_parser.add_argument(
        "--observed-at",
        help="ISO-8601 capture time (default: current UTC time)",
    )
    return argument_parser


def main(arguments: Optional[Sequence[str]] = None) -> int:
    options = parser().parse_args(arguments)
    try:
        root = resolve_git_root(options.repository_root)
        schema = (
            options.schema
            if options.schema is not None
            else root / "docs/evidence/schemas/workspace_receipt.schema.json"
        )
        if not schema.is_file():
            raise ReceiptError("schema not found: {}".format(schema))
        schema_document = json.loads(schema.read_text(encoding="utf-8"))
        try:
            import jsonschema
        except ImportError:
            raise ReceiptError("jsonschema is required for receipt validation")
        try:
            jsonschema.Draft202012Validator.check_schema(schema_document)
        except jsonschema.exceptions.SchemaError as error:
            raise ReceiptError(
                "invalid workspace receipt schema: {}".format(error.message)
            )

        if options.capture:
            if not options.capture_repository or not options.receipt_name:
                raise ReceiptError(
                    "--capture requires --capture-repository and --receipt-name"
                )
            source_root = resolve_git_root(
                options.source_workspace_root
                if options.source_workspace_root is not None
                else root
            )
            observed_at = options.observed_at or datetime.datetime.now(
                datetime.timezone.utc
            ).replace(microsecond=0).isoformat()
            receipt_path, patch_path = capture_receipt(
                root,
                source_root,
                options.capture_repository,
                options.receipt_name,
                observed_at,
            )
            print(
                json.dumps(
                    {
                        "result": "UNAPPROVED",
                        "receipt": receipt_path.relative_to(root).as_posix(),
                        "patch": patch_path.relative_to(root).as_posix(),
                    },
                    sort_keys=True,
                )
            )
            return EXIT_UNAPPROVED

        receipts_dir = (
            options.receipts_dir
            if options.receipts_dir is not None
            else root / "docs/evidence/receipts"
        )
        receipt_paths = (
            options.receipt
            if options.receipt
            else sorted(receipts_dir.glob("*.json"))
        )
        if not receipt_paths:
            raise ReceiptError("no receipt files found")
        verification_source_root = (
            resolve_git_root(options.source_workspace_root)
            if options.source_workspace_root is not None
            else root
        )

        error_count = 0
        unapproved_count = 0
        for receipt_path in receipt_paths:
            path = receipt_path if receipt_path.is_absolute() else root / receipt_path
            errors, warnings, receipt = validate_receipt(
                root,
                path,
                source_root=verification_source_root,
                schema_document=schema_document,
            )
            if options.check_replay and receipt is not None and not errors:
                errors.extend(
                    replay_receipt(
                        root,
                        receipt,
                        options.replay_root,
                        source_root=verification_source_root,
                    )
                )
            for error in errors:
                print("[INVALID] {}: {}".format(path, error), file=sys.stderr)
            for warning in warnings:
                print("[UNAPPROVED] {}: {}".format(path, warning), file=sys.stderr)
            error_count += len(errors)
            if warnings:
                unapproved_count += 1
        if error_count:
            result = "INVALID"
            exit_code = EXIT_INVALID
        elif unapproved_count:
            result = "UNAPPROVED"
            exit_code = EXIT_UNAPPROVED
        else:
            result = "PASS"
            exit_code = EXIT_OK
        print(
            json.dumps(
                {
                    "errors": error_count,
                    "receipts": len(receipt_paths),
                    "result": result,
                    "unapproved": unapproved_count,
                },
                sort_keys=True,
            )
        )
        return exit_code
    except (OSError, ReceiptError, json.JSONDecodeError) as error:
        print("[INVALID] {}".format(error), file=sys.stderr)
        print(
            json.dumps(
                {"errors": 1, "receipts": 0, "result": "INVALID", "unapproved": 0},
                sort_keys=True,
            )
        )
        return EXIT_INVALID


if __name__ == "__main__":
    sys.exit(main())
