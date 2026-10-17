# ContentOps Portable Host Readiness Receipt Producer — 2026-10-17

Status: `IMPLEMENTED / TESTED / INTEGRATED / READ_ONLY / PORTABLE`

## BEFORE

ContentOps produced a rich in-repo host readiness receipt, but a foreign consumer had no stable
serialization/hash boundary for validating it without importing ContentOps code. The Goal 4 receipt
also mixed implementation/runtime evidence with current host observations in a repository-specific
shape.

## AFTER

`host_readiness_observation_consumer_v1.py` now exports
`contentops.portable_host_readiness_receipt.v1` with:

- strict canonical JSON bytes: sorted keys, compact separators, ASCII UTF-8, NaN/Infinity rejected;
- self-hash `portable_receipt_sha256` over the payload excluding that field;
- source repository, branch, head, producer schema and verified source receipt hash;
- observation ID, observed/known-at/as-of UTC clocks, age and freshness;
- read-only rights basis, redaction policy, secret detection, and raw-payload exclusion;
- explicit proof layers `IMPLEMENTED`, `TESTED`, `INTEGRATED`, `HOST_OBSERVED`,
  `RUNTIME_PROVEN`, `PUBLICLY_PROVEN`, each carrying only an allowed state;
- packet/V3/shadow hashes, zero-effect counters, and a compact exact observation projection.

The validator is pure JSON-shape/hash logic and does not import Main or require ContentOps code on
the receiving side. Tampered source receipts and secret-bearing input are blocked; no untrusted
payload is copied into the portable envelope.

## Preserved current observation

Fixture: [portable_host_readiness_receipts_v1.json](../../tests/fixtures/portable_host_readiness_receipts_v1.json)

The `current_real` case preserves the Goal 4 observation:

- BrowserOS Neo MCP `PASS` at `http://127.0.0.1:9010/mcp`, `browseros-neo 0.0.72`, protocol
  `2025-06-18`, allowlist `name_session/read/tabs`, read-only;
- CDP 9222 and 9223 `UNAVAILABLE`;
- all three ContentOps tasks `Disabled` / state `1`;
- account and destination identity `MISSING`;
- SQLite read-only integrity `ok`, foreign-key violations `0`, counts preserved, zero-effect
  counters preserved;
- Main packet, V3 and Goal 4 shadow receipt hashes preserved;
- portable classification remains `NOT_VERIFIED`, with runtime/public proof false.

The same fixture set contains compact `healthy`, `unavailable`, `ambiguous`, `stale`, and
tampered-wire cases. Their portable hashes are:

| Case | Classification | Portable SHA-256 |
|---|---|---|
| `current_real` | `NOT_VERIFIED` | `04a77221e760f3f0ee02d793db8932974c4db006c5740cc82795666302fed213` |
| `healthy` | `HOST_OBSERVED` | `97d54d6e696c2201adb58f31b1a261a59ccc0ffb4436f91d20290e56726d334d` |
| `unavailable` | `NOT_VERIFIED` | `37fd2e379f66eeb6c3941538cb43d8578ce1b52a8469f12ff4d717c34fab09c3` |
| `ambiguous` | `AMBIGUOUS` | `2cc4fdb0053a0615c26aedfcd34ba9d08cd9480d4ae3a43c42e798268db0f5f6` |
| `stale` | `STALE` | `0e7ca516c303b69d9a1ec076b8ef861c4a28a6ad785fb5ecf6321cb7a327c550` |
| `tampered` | rejected | all-zero self-hash; validator returns `portable_receipt_hash_invalid` |

## Reused and changed

- Reused: Goal 4 host observer, BrowserOS preflight, identity/readback gates, Main handoff,
  scheduled shadow, and existing zero-effect/read-only boundaries.
- Changed: one portable exporter/validator in the existing host-readiness owner, one compact
  fixture set, and compatibility regressions. No second scheduler, status owner, analyzer,
  database lane, publisher, or Main repository change.

## Evidence

Focused new portable tests: `7 passed`.

Focused owner compatibility set: `69 passed`:

```powershell
python -m pytest -q tests/test_portable_host_readiness_receipt_v1.py tests/test_host_readiness_observation_consumer_v1.py tests/test_main_analysis_handoff_consumer_v1.py tests/test_scheduled_shadow_production_day_v1.py tests/test_v1_simple_gemini_scheduler_browseros_dry_run_v1.py tests/test_browser_rendered_source_recovery_v1.py
```

Ruff, `py_compile`, and `git diff --check` passed. No login, account selection, cookie/storage/token
read, provider call, task launch, store/database mutation, public write, deployment, or V2 activation
occurred.

Remote readback: [PR #73](https://github.com/fatcat2109/capital-chronicle-contentops/pull/73) is
`OPEN/CLEAN`, based on `18bcd94c908a3afcc4dc0ce156418f3a89a8e16f`, with exact head
`27d5c0b7df9dee15d41b99ac64c08f19dd434c49`. Exact-head CI run
[39041124272](https://github.com/fatcat2109/capital-chronicle-contentops/actions/runs/39041124272)
is green for both `branch-codegraph-refresh` and `deterministic-validation`.

## Blockers

Current identity/CDP readiness remains `NOT_VERIFIED`; the portable producer preserves that state
and does not convert it into runtime or public proof. `UNKNOWN_WRITE` remains a hard stop.

## Exactly one NEXT

Have Main validate the portable fixture set using only canonical JSON/hash rules, then stop on any
source-head mismatch, stale/ambiguous/unavailable classification, secret-material marker, or
`UNKNOWN_WRITE`.
