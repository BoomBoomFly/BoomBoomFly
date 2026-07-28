# H4 formal SITL disposition

```text
H4: NOT-RUN
FORMAL_SITL_RUN: false
HARDWARE ACCESSED: NO
```

No PX4, MicroXRCEAgent, MAVROS, simulator, or SITL process was started. H3 is
test-only and synthetic by design and is not promoted to H4.

The exact PX4 root and every enumerated nested object are remotely recoverable,
but the formal H4 command card still needs a fixed board/toolchain/RC/profile,
world/model, Agent invocation, ports/domain, parameters, timeout, expected
outputs, cleanup, and explicit user approval. This is the remaining WSL P1.

Until formal H4 succeeds and native ARM64 independently rebuilds the source
candidate, `READY FOR H5-A REQUEST` remains NO.
