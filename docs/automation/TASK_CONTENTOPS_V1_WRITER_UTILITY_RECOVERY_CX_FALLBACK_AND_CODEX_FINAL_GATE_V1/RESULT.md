# V1 writer utility recovery, CX fallback, and Codex final gate

Result: `TRIGGER_V1_CODEX_EDITORIAL_BRAIN_VERTICAL_SLICE`

The accepted grounded-research recovery was fast-forwarded to master at `1c51487c40be4cc196f96fbf710e547e51d00e2e` and deployed at an idle boundary. This branch adds `cx/gpt-5.6-sol(xhigh)` as the fifth and final 9Router model for V1 grounded research and article writing only. Cheap leaf work and V2 model policy are unchanged.

The fixed committed rank-1 Reuters/MarketWatch/CNN packet was replayed with zero write authority. The normal non-CX writer reached source/factual validity but failed utility after its single bounded repair. One separate CX utility rescue ran against the same governed evidence and was not accepted. The replay therefore stopped at the owner-specified Codex gate. No final article or release plan was accepted, and no rejected raw model output was retained.

Measured replay totals were two writer logical invocations, six provider attempts, and 83,186 accounted tokens. Public writes, publisher calls, publication-coordinator calls, UNKNOWN_WRITE, pending reconciliation, and pending readback were all zero.

Focused validation passed 170 tests. It covers fifth-model reachability after four 503 responses, no rotation on factual failure, exact identity policy, finite budgets, one repair, one CX rescue, unsupported-claim rejection, thin-copy rejection, concise attribution, bound reader links, duplicate-publisher removal, provider-adapter integration, candidate walking, and the throughput zero-write seam.

Next action: implement the separately authorized fresh isolated Codex editorial-brain vertical slice. Do not tune the writer prompt again or add another provider model.
