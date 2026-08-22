# V1 official Codex direct-provider canary

Status: `BLOCKED_CANARY_LOCAL_VALIDATION_FAILED_NO_SECOND_PROOF_RUN`

The official ChatGPT-authenticated Codex SDK/App Server transport was implemented behind the
canonical V1 editorial seam and passed local transport/contract regressions. The single authorized
Italy production proof started one fresh ephemeral `gpt-5.6-sol / XHIGH` thread and reached current
deterministic product validation. The returned article failed the institutional-edge gate on six
structured-output/epistemic binding checks, so the canonical candidate walk failed closed with zero
public writes.

No replacement thread, second production proof, public-write adapter, provider publication write,
or production-store mutation was attempted. Because the task explicitly forbids a second production
proof, this branch does **not** claim
`PASS_OFFICIAL_CODEX_DIRECT_PROVIDER_CURRENT_HEAD_CANARY_VERTICAL_PROOF` and does not update current
routing authority to mark the direct provider proven.

The implementation was subsequently hardened locally so a future authorized run persists the
secret-free TurnResult receipt before product validation and may use its one bounded repair on the
same in-memory SDK thread when deterministic local product validation rejects the initial article.
That hardening was tested only with fake SDK transport; it was not exercised in a second live proof.

Raw canary artifacts remain untracked under
`artifacts/v1_official_codex_direct_provider_canary_20260822/`.
