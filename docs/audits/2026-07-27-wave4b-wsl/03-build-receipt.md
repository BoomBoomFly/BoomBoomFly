# H1-WSL build receipt — PASS

Tested source root: `1ea582b8e7fa8aff4d284cf108c9a6c7bb510b56`.

```text
boundary: PASS
build: PASS (3/3)
test: PASS (3/3)
test-result: PASS
Summary: 14598 tests, 0 errors, 0 failures, 0 skipped
HARDWARE_ACCESSED: NO
```

Formal output root:
`/tmp/boomboomfly-wave4b-h1-20260728-08`. The independent boundary run is
`/tmp/boomboomfly-wave4b-h1-boundary-20260728-08`.

Selected packages were exactly:

```text
px4_msgs
offboard_cpp
vision_to_dds
```

The boundary JSON reports 83 classified repository entries, three discovered
production packages, and no override or path leakage. Build/install/log/test
results were created only under this new `/tmp` tree. ROS logs were also
forced below that tree.

Key receipt manifest:

```text
SHA256(/tmp/boomboomfly-wave4b-h1-20260728-08/SHA256SUMS)
= 804d532b0400121e037589e95d4e7640c35029e20df336b9a8d27bde33f9eb6f
```

`SHA256SUMS` covers boundary/selection artifacts, all colcon logs, all xUnit
files, the console receipts, and the Offboard/vision executables and tests.

Earlier attempts are retained as negative evidence and are not counted:
attempts 01/02/04 were interrupted infrastructure hangs; 03 had a transient
generator SIGSEGV; 05 exposed ROS template lint and home-log issues; 06 was
blocked by sandbox `getifaddrs`; 07 passed on the parent source before the H3
harness compatibility fix. Attempt 08 is the only final-source formal receipt.

This x86_64 WSL result is only `H1-WSL PRECHECK: PASS`; it does not replace the
native ARM64 rebuild.

## Master-integration recheck

After resolving `master@bcde328…` into the candidate, root
`7cbd4276ab27ef97c93436529cefb1fa5a3ab1c9` was rebuilt in fresh
`/tmp/boomboomfly-wave4b-h1-merge-20260728-10`:

```text
boundary: PASS
build: PASS (3/3)
test: PASS (3/3)
test-result: 14598 tests, 0 errors, 0 failures, 0 skipped
SHA256(SHA256SUMS): 4d4ae48bb1542bc2c3ad0529bb95eb58cee404e57c16ecef2efc0dea742eea63
```

The immediately preceding `...-09` directory failed during the known
transient Foxy Python generator `unknown opcode` condition and was retained as
negative evidence; it was not promoted to PASS.
