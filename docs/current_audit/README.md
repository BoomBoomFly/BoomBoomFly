# Historical audit snapshot

`docs/current_audit/` preserves the 2026-07-27 audit snapshot produced against
root `0ed9d148...`. The directory name is historical and does not mean that its
recorded branch, HEAD, package boundary, findings, or gate status describe the
current checkout.

Use these active coordination records instead:

- [`docs/handoff.md`](../handoff.md)
- [Wave 4B WSL summary](../audits/2026-07-27-wave4b-wsl/00-summary.md)
- [Wave 4B open findings](../audits/2026-07-27-wave4b-wsl/07-open-findings.md)
- [Wave 4B immutable handoff](../audits/2026-07-27-wave4b-wsl/08-handoff.json)

Revalidate every source identity and gate on the target environment before use.
The original files in this directory remain unchanged as historical evidence;
this marker only prevents the directory name from being mistaken for a live
status claim.
