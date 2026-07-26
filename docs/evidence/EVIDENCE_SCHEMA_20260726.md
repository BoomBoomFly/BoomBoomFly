# Evidence schema remediation — 2026-07-26

## Scope

This record documents `BBF-NEXT-T08`: machine-verifiable evidence metadata, a
non-destructive legacy evidence index, and release/rollback manifests. It does
not claim a software release, parameter capture, rollback exercise, bench test,
or hardware validation.

Implementation began from:

- repository: `https://github.com/BoomBoomFly/BoomBoomFly.git`;
- branch: `agent/wave1-evidence`;
- baseline HEAD: `5a0e6edd4930474506a1046d414425893ebd800f`.

## Legacy evidence handling

The two pre-existing evidence files were not edited. Their byte hashes are
recorded in `index.yaml`, both with `status: historical`. In particular,
`PX4_PARAMS_20260724T203458+0800.json` predates later maintainer-reported PX4
transport changes and cannot represent current parameters.

## Safety boundary

Work was limited to static schemas, validators, documentation, and synthetic
test fixtures under `/tmp`. No launch file was started, no hardware device was
opened, no `/fmu/in/*` message was sent, no PX4 parameter was read or written,
and no firmware was built or flashed.

## Validation

Local validation commands and exit codes are recorded after implementation
testing in the Wave 1 validation report. This file remains an implementation
note, not a `current` operational acceptance record.
