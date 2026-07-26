# Workspace receipt approvals

Receipt fields such as `baseline_status` and `maintainer_confirmation` are
observations or claims. Editing those fields does not approve a checkout.

An approval is valid only when all of the following are present and verified:

- a separate approval JSON conforming to
  `docs/evidence/schemas/workspace_receipt_approval.schema.json`;
- a SHA-256 binding to the exact receipt plus checkout origin, HEAD, patch and
  content hashes;
- an OpenSSH detached signature over the canonical `signed_payload`;
- a matching maintainer identity and exact Ed25519 public key in
  `approvals/trusted_maintainers.json`.

The trust list is intentionally empty in Wave 1. No current receipt is
maintainer-approved. Adding a signer or approval is a maintainer governance
action and must not be inferred from receipt contents.
