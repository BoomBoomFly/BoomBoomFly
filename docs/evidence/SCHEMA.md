# BoomBoomFly evidence, release, and rollback schema

## Authority and scope

This directory separates immutable captured artifacts from their machine-readable
metadata. A status in a handoff, issue, or prose report does not override the
machine-readable index. The authoritative schemas are:

- `schemas/evidence.schema.json` for one validation or capture;
- `schemas/evidence_index.schema.json` for the repository index;
- `schemas/release.schema.json` for artifact promotion;
- `schemas/rollback.schema.json` for rollback planning and execution.

All schemas use JSON Schema draft-07. JSON and YAML instances are accepted by
the validators. Commands are stored as an argument vector plus a repository-
relative working directory so paths containing spaces remain unambiguous.

## Evidence lifecycle

The only evidence `status` values are:

| Status | Meaning |
|---|---|
| `current` | Reviewed evidence for the expected repository HEAD; artifacts and hashes verify. |
| `historical` | A dated record that is not a statement about current state. |
| `superseded` | Historical evidence with a valid `superseded_by` link. |
| `unverified` | Incomplete, blocked, or not independently verified. |
| `failed` | A command or acceptance check failed; its logs remain evidence. |

`current` is fail-closed: the root origin and HEAD must match the checked
repository, the reviewer must approve it, raw stdout/stderr must exist and hash
correctly, and the result cannot be failed or unverified. Supersession links are
bidirectional, refer to existing IDs, and cannot contain cycles.

An old parameter snapshot is never promoted merely because it is indexed.
Entries marked `known_historical: true`, including the 2026-07-24 PX4 parameter
snapshot, cannot have `status: current`. A new parameter capture requires a new
evidence ID and complete metadata.

## Artifact and path rules

Every artifact reference contains a repository-relative `path` and lowercase
SHA-256. Absolute paths, `..` traversal, missing files, non-regular files, and
hash mismatches fail validation. Evidence should reference immutable raw logs;
it must not embed personal home paths, unnecessary hardware identifiers, or
credentials in public summaries.

The index records legacy artifacts without rewriting them. A null
`metadata_path` means the legacy artifact predates this schema. Such an entry
cannot be `current`.

## Validation commands and exit codes

Run validators from any directory:

```bash
python3 Scripts/evidence/validate_evidence.py metadata.yaml
python3 Scripts/evidence/validate_index.py
python3 Scripts/evidence/validate_manifest.py --kind release release.yaml
python3 Scripts/evidence/validate_manifest.py --kind rollback rollback.yaml
```

Each command supports `--help`, `--repo-root`, and `--schema`. Summaries are
printed as JSON. Exit codes are stable:

| Exit | Meaning |
|---:|---|
| 0 | All requested checks passed. |
| 2 | Command-line usage error. |
| 3 | Schema or instance structure invalid. |
| 4 | Artifact path, link target, or SHA-256 integrity failure. |
| 5 | Provenance or lifecycle policy failure. |
| 6 | Git, file parsing, or validator dependency unavailable. |

`validate_evidence.py --no-artifact-hash-check` is deliberately non-successful:
it reports an unverified policy result rather than converting a skipped check
into PASS.

## Release manifests

A release manifest binds the exact root and dependency SHAs, environment ID,
release artifacts, acceptance evidence IDs, promotion command, approvals, and
rollback manifest. `lifecycle: template` is not an approval. Candidate and
approved manifests must match the expected repository HEAD and all referenced
artifact hashes.

`RELEASE_TEMPLATE.yaml` is intentionally incomplete and must be copied to a new
immutable manifest, populated, validated, and reviewed. It is not evidence that
a release exists.

## Rollback manifests

Rollback types are `firmware`, `software`, `parameter`, and `configuration`.
Every manifest records:

- pre-state and target-state hashes;
- the exact rollback artifact and command;
- objective stop conditions;
- read-only verification commands and expected results;
- separate operator and observer records;
- execution result and limitations.

`ROLLBACK_TEMPLATE.yaml` has `manifest_state: template`, null people, zero
hashes, and `result: not_run`. The schema prevents a template from claiming a
verified result, and the semantic validator rejects template placeholders in
any planned, executed, or verified manifest. Validators never execute commands,
touch hardware, change PX4 parameters, or flash firmware.
