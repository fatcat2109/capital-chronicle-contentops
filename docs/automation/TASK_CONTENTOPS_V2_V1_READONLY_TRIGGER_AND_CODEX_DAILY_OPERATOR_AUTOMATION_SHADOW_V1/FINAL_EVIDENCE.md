# Task 3 final evidence

Classification: `BLOCKED_NATIVE_CODEX_APP_FRESH_XHIGH_HANDOFF`

The implementation, deterministic tests, real V1 read-only ingestion, durable candidate decisions,
and native HIGH scheduled parent all passed their bounded shadow proof. The task does not qualify for
`PASS_V2_V1_READONLY_TRIGGER_AND_CODEX_DAILY_OPERATOR_AUTOMATION_SHADOW` because the real scheduled
parent could not obtain native project metadata and therefore could not create the required fresh
isolated XHIGH child. No substitute execution or provenance was fabricated.

## Git authority

- Repository: `fatcat2109/capital-chronicle-contentops`
- Branch: `task/v2-v1-readonly-trigger-codex-daily-operator-shadow-v1`
- Fresh `origin/master`: `95e8373efd000085df22ed7e7f3623e9444e8aee`
- Verified Task-2 correction baseline and remote tip: `edbdb948d40fd589ea2df001c86af2faf1ef4c8f`
- Frozen implementation HEAD used by the real proof: `1d9bfa80e17a39e41aadac173587a000911e9308`
- Implementation commits:
  - `93f12332fc1ab974fa2e7d5953f9d7d026880b6a` — `feat(v2): add read-only daily operator shadow spine`
  - `5f337cde1288b1d212745b2fc508df350268e7b0` — `chore(v2): refresh generated code context`
  - `e0f082d39d179bb17d272e223782bef011d67f49` — `fix(v2): hash native child result from file`
  - `1d9bfa80e17a39e41aadac173587a000911e9308` — `chore(v2): bind context to native handoff fix`
- The frozen implementation was pushed and its remote branch tip matched byte-for-byte before the
  scheduled proof.

## V1 read-only proof

- Store: `A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3`
- Canonical surface: `published_corpus_read_model_v1.load_published_corpus` plus read-only
  `performance_observations` queries.
- Publication contract: `SUBSTACK_DISPATCH_CONFIRMED_AND_EXACT_RECONCILIATION_CONFIRMED_AND_VALID_CANONICAL_URL`
- SQLite URI: `mode=ro`; `PRAGMA query_only=1`; connection `total_changes=0`; no write API exposed.
- Snapshot: `80f5d0403558cf7e538318d3dd5a2de6122e535c31de34e02603571086f2fbb2`
- Database SHA-256 before/after automation: `aadf204d473b3a769d7f471043f99f8aa9498a5553782b30d2710d5dbba1bb45`
- Database data version, size, and modification time stayed unchanged during both reads.
- V1 write count: `0`; V1 scheduler mutation count: `0`; second V1 store created: `false`.

## Candidate decisions and durable outbox

Both runs evaluated the same proof instant, `2026-08-18T14:45:22Z`, against the same V1 snapshot.

1. `v1candver_3150e993545261fa52dffbfa24b13180`: `DEFERRED`, fresh age 0 days,
   four evidence references, reason `approved_content_too_thin_for_video_qualification`, no job.
2. `v1candver_34a1720234457fb6171ed8414a578a6e`: `ABSTAIN`, stale age 6 days,
   three evidence references, reason `candidate_outside_freshness_window`, no job.

The first run durably inserted the two immutable decisions. The second run returned both as
`idempotent_replay=true`; durable totals remained two decisions and zero video jobs. The canonical
V2 store and queue were extended in place; no parallel general queue or scheduler was added.

## Real native automation proof

- Automation: `v2-daily-operator-shadow` / `V2 Daily Operator — Shadow`
- Kind: standalone daily scheduled task, bounded proof schedule at 21:43 local time.
- Project: `2fa93564-32a4-4a4b-aa79-bb4aeb1cd4fb`
- Parent task: `01a01553-c7d7-7972-b2ae-a34fa9b4c369`
- Parent receipt: native Codex Desktop App, `gpt-5.6-sol`, `high`.
- Operator runs: `v2shadow_20260818T144522Z_01a01553_a` and
  `v2shadow_20260818T144522Z_01a01553_b`.
- Result: `NO_GENUINE_QUALIFIED_CANDIDATE_NO_VIDEO`; empty review queue;
  `public_write_authority=false`.
- The parent then attempted the expressly allowed `SHADOW_ISOLATION_PROBE`. Native project lookup
  returned no metadata, child task ID, or worktree after repeated waits exceeding five minutes.
  The parent terminated only the lookup and emitted
  `BLOCKED_NATIVE_CODEX_APP_FRESH_XHIGH_HANDOFF`.
- Fresh child/XHIGH provenance: none, truthfully. `record-handoff` and `finalize-automation` were not
  run because no actual child provenance existed.

The exact automation was created, run once, then paused after the blocker. No V1 or unrelated
automation was mutated. The four existing V1 scheduled tasks remain paused. The only scheduler/app
mutations were: create `v2-daily-operator-shadow`; pause `v2-daily-operator-shadow` after the hard
stop.

## Actual-app screenshots

- `screenshots/automation_configuration_actual_app.png` — scheduled configuration and bounded run.
- `screenshots/automation_run_blocked_actual_app.png` — completed native task with exact blocker,
  parent model/effort, zero-write result, and evidence links.
- `screenshots/automation_paused_after_blocker_actual_app.png` — actual Scheduled/Paused view showing
  this V2 automation and the four pre-existing paused V1 tasks.

Builder evidence does not claim Jim/ChatGPT App-UI acceptance.

## Validation

- Final focused compatibility suite: `68 passed, 1 skipped in 16.13s`.
- Ruff: passed.
- `compileall`: passed.
- `git diff --check`: passed before the real proof.
- Generated graph: 7,226 nodes / 13,596 edges before; 7,243 nodes / 13,629 edges after.
- `python scripts/generate_codex_context_index.py --check`: `CODEGRAPH_CURRENT`.
- The repository had no `.codegraph/` index, so `codegraph explore` truthfully reported unavailable;
  repository-owned generated context was refreshed and checked instead.
- Platform/public writes: `0`; publication adapter calls: `0`; browser/CDP calls: `0`;
  CLI/SDK/API/9Router creative calls: `0`; TTS/ElevenLabs spend: `0`.

Task 4 was not started, and the current V2 execution pointer was not advanced because Task 3 did not
pass.
