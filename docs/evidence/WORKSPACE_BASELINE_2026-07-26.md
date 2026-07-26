# BoomBoomFly preserved checkout baseline receipt

Status: **UNAPPROVED**

Captured at `2026-07-26T17:42:00+08:00` from the local workspace identified by
the canonical BoomBoomFly origin. This receipt set is an observation of four
preserved dirty dependency checkouts. It does not declare the differences to be
an approved production, platform, or business baseline.

No source checkout was modified while capturing or validating these receipts.
Patch replay was performed only against `git archive HEAD` copies below `/tmp`.

## Receipt set

| Checkout | HEAD / checkout | Observed differences | Patch SHA-256 | Content SHA-256 | Approval |
|---|---|---|---|---|---|
| `src/librealsense` | `c94410a420b74e5fb6a414bd12215c05ddd82b69`, detached | 3,347 mode-only changes | `bc0ad35a95799aa9e9a2febc21795b1488fca0e592149b5a3e8e0e2f8bab17ae` | `6798756691f1d67580b57f9f35dd6a3e4268a83fc2cdf61f204d4bed2a093f96` | UNAPPROVED |
| `src/navigation_msgs` | `fe880e99d993e9d4dfbf37f00d839d32994610e1`, branch `foxy` | 13 deleted files under `map_msgs` | `a39a4cf8bae05b484eb529c8ab793e7c1900881685f6dee0029b18805537db25` | `02628c66a0c0ce8bde702c620717c13df732277b2a43f3bab36a36dcc736ec66` | UNAPPROVED |
| `src/realsense-ros` | `8abb4657c0add15f87b0edbfb67eaba2c1c2c439`, detached | 97 mode-only changes; one mode + configuration change; one untracked launch file | `e01635d6d8854c7c9f45268a88dd358d2ec44c1978e5e63789fc356dbdfa25c4` | `c5e3f971b0d0b4b162f18bd02e123eb3cccfe89724ae43fadfeaaec7bbdc1835` | UNAPPROVED |
| `src/vision_opencv` | `72152d9d1d8edcfcafd707a1d0103810db8613ba`, branch `foxy` | 17 deleted files under `image_geometry` | `6c645c92e27afd9168b01bbcb0fbcf751472d623c64fabd7343b8680e0c0e162` | `a4fcf129afab03a8b8d13b8903ea538a5dbe2a1f3626e1e515f63558e46e4d26` | UNAPPROVED |

All four staged diffs were empty at capture time. The
`realsense2_camera/launch/rs_t265_launch.py` untracked file has SHA-256
`3aafdc4f7020f166052ae4e9c312c9172c1e8cce97f10ca6449a7dbafc623ebb`.
The tracked `realsense2_camera/launch/rs_launch.py` additionally contains an
observed, unapproved `tracking_module.frames_queue_size=16` default.

Exact paths, modes, classifications, origin, branch/detached state, staged
state, untracked inventory, replay order, and approval state are in the four
machine-readable receipts under `docs/evidence/receipts/`.

## Verification contract

Patch artifacts use a single-line base64 container so CRLF and trailing whitespace in
the observed source bytes remain exact without making the root Git diff itself
whitespace-invalid. Each receipt records both the container SHA-256 and the
decoded canonical patch SHA-256.

The verifier recomputes:

1. canonical origin and locked HEAD;
2. tracked and staged diff hashes;
3. the combined binary patch, including non-ignored untracked files;
4. the untracked file inventory;
5. a canonical path/type/mode/content manifest hash;
6. clean patch apply, replayed content hash, reverse apply, and restored base
   content when `--check-replay` is requested.

Exit codes are:

- `0`: every receipt is internally consistent and maintainer-approved;
- `1`: schema, origin, HEAD, patch, content, path, or replay verification failed;
- `2`: observations are internally consistent but at least one receipt remains
  `UNAPPROVED`.

Example, using explicit roots and no current-directory assumption:

```bash
PYTHONPYCACHEPREFIX=/tmp/boomboomfly_receipt_pycache \
python3 Scripts/installation/verify_workspace_receipts.py \
  --repository-root /path/to/BoomBoomFly \
  --check-replay \
  --replay-root /tmp/boomboomfly_workspace_receipts
```

For this capture the expected result is `UNAPPROVED`, exit code `2`. A
maintainer must review the platform applicability, business purpose, and exact
differences before changing any receipt to approved. Regenerating a receipt is
not approval.
