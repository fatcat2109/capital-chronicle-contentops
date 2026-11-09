# CC-331 — TOUCH export acceptance

The existing plan-status consumer accepts all five rows of CC-330's copied export,
preserving the two original setup IDs and each event's exact clock. The fill confirms
the EUR/USD model position at **03:32 ET on 6 November**, rather than the preceding
trigger's 03:31 ET. Its internal clock remains `2026-11-06T08:32:25.128000Z`.

Jim's decision 106, recorded on 9 November, supersedes the item's older instruction
to suppress fills. It permits confirming a model position. Account identity,
tickets, exact fill price, size, P&L and targets remain private under decision 40.
The existing public wording and notices are reused.

The earlier trigger normalizes with its own source ID and clock, then receives
`FILL_EVENT_SUPERSEDES_TRIGGER`. The other four rows compose. The fill retains the
existing public TRIGGERED key, so a later backfilled trigger cannot republish it.
Only an unsent earlier trigger is retired. Already published bytes and ambiguous
sends are retained, and prevent another confirmation while readback is pending.

## Verification

- **85 distinct targeted tests passed**, in two sequential pytest processes:
  [composer and TOUCH tests](pytest-touch.xml) and
  [publication, recovery and rationale tests](pytest-consumers.xml).
- [Exact-reader replay](revalidation-20261110.json) reads both copied files using
  Main commit `ef053ea0d36e372d6cf3053c6c2abfa0d62499a0` and its own schema validators
  and snapshot-join checks. Six unmodified reader/dependency/schema files are
  extracted from Git into a temporary directory; no Main checkout is changed.
- The dry run leaves the isolated store byte-for-byte unchanged and creates no
  outbox row. A writable replay creates one local fill row; repetition creates
  zero rows and preserves its exact payload. Public transport calls remain zero.
- Controlled coordinator tests prove that the fill reaches the existing publisher
  once. Privacy tests inject private fields and verify they never reach copy.
- The input fixture has exact-byte Git attributes. Its SHA256 values match
  CC-330's retained `fill-touch-output`, recorded in the replay evidence.

Reproduce from this checkout:

```powershell
python -B scripts/revalidate_plan_status_cc331.py --main-repository 'A:\Capital Chronicle\Worktrees\codex-main-exec-b' --evidence tests/evidence/cc-331/revalidation-20261110.json
```

## Operating consumer

The existing `CapitalChronicle-PlanStatusPosts-V1` task runs
`pythonw.exe -B scripts\plan_status_posts.py --publish` from
`A:\Capital Chronicle\ContentOps`. It imports this consumer on each invocation;
integration needs no restart or schedule change. The acceptance artifact records
the actual implementation root and hash used by the replay.

The branch starts at the current Publisher operating head `7ad363a5`, preserving
the already installed policy and consumer changes. The remote default branch
predates those changes. The two pre-existing telemetry/duplicate-ledger edits
remain outside this item's commits. This run performs no public write or Main
integration.
