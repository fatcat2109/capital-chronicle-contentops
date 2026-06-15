# 0174CP — Next-Platform Account-Binding Selection & Official-Docs Gate

Decision-only, strictly local gate. Selects the **next** supervised publishing
target after the Telegram live pilot (0174CN) and the post-pilot ledger (0174CO).

## What this gate is

- A deterministic, redaction-safe **selection packet** comparing three candidates
  for the next supervised publishing target:
  - `x` (X / create-post)
  - `linkedin` (LinkedIn Posts API)
  - `telegram_second_gate` (second supervised Telegram post)
- Grounded **only** in official platform documentation read out-of-band and
  recorded as symbolic citation metadata (host + title + accessed date).

## What this gate is NOT

- No network library is imported (no urllib / requests / httpx / socket).
- No platform API call, OAuth flow, token exchange, or account binding.
- No environment / credential / `.env` read.
- No posting, scheduling, webhook, reply/DM, or metrics fetch.
- It does not alter any existing Telegram live gate.

## Recommendation

**Telegram second-gate** is the recommended next step:

- Path already proven end-to-end: identity (0174CK), target binding (0174CL),
  dry-run preflight (0174CM), one live post (0174CN), ledger (0174CO).
- Reuses an existing validated bot token: no OAuth flow, no app review.
- Lowest credential-complexity class and simplest redacted audit.
- Lowest risk of accidentally enabling replies / DMs / scheduler / metrics.

X and LinkedIn remain strategically valuable (reach and institutional credibility
respectively) but each require OAuth / member-or-organization roles, product or
access-tier review, and version pinning that must be verified in a dedicated
requirements task before any live path.

## Next task

`TASK_CONTENTOPS_0174CQ_TELEGRAM_SECOND_SUPERVISED_POST_DRY_RUN_WITH_DURABLE_LEDGER_GATE_V0`

## Artifacts

- `next_platform_account_binding_selection_packet.json` — deterministic,
  redaction-scanned selection packet (sorted keys, stable separators, trailing
  newline). `status: pass`, `official_source_count: 4`, redaction clean.

## CLI

```
python -m live_contentops.cli next-platform-account-binding-selection-gate
python -m live_contentops.cli next-platform-account-binding-selection-gate --write-next-platform-selection
```

Preview-only by default (fail-closed). The packet file is written only when the
explicit `--write-next-platform-selection` flag is passed AND the redaction scan
passes AND `status` is `pass`.

## Verification

- `tests/test_next_platform_account_binding_selection_gate.py` — 17 tests, all pass.
- `tests/test_security_scans.py` — passes (no env/network/credential tokens).
