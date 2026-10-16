# ContentOps Current Host Read-Only Preflight — 2026-10-16

Status: `PARTIAL / READ_ONLY / NO_PUBLIC_WRITE`

This packet records the bounded current-host preflight run for the ContentOps V1
recovery lane. It is an observation receipt, not a new runtime or authority owner.
The production store was opened read-only. No scheduler, process, browser session,
credential, publication, dispatch, or runtime mutation was performed.

## BEFORE

- Repository lane: `codex/v1-browser-rendered-source-recovery-v1`.
- Source commit: `4cdbf9d8098250479d5797ce4222c0f7680d0eb5`.
- Source remote readback: `origin/codex/v1-browser-rendered-source-recovery-v1` and
  `origin/pull/55/head` both resolve to the same commit.
- ContentOps authority remains `SIMPLE_GEMINI_RUNTIME` for routine editorial work and
  `DurablePublicationCoordinator` for publication/readback.
- V2 public-write authority remains zero.
- Existing local WIP in the primary checkout and the two unrelated V6 telemetry files
  in this worktree were preserved.

## AFTER / OBSERVED HOST STATE

### Process and scheduler ownership

The host process readback found no process matching the bounded ContentOps runtime
classification (`ContentOps`, `daily_app`, `Start_ContentOps`, or a 9223 owner).
The relevant Windows task readback was:

| Task | Observed state |
| --- | --- |
| `CapitalChronicle_ContentOps_V1_Daily_App_Runtime` | `Disabled` |
| `CapitalChronicle_ContentOps_V1_Hourly_Audit` | `Disabled` |
| `CapitalChronicle_ContentOps_V1_Simple_Scheduler` | `Disabled` |

This proves a disabled configured task state at readback time. It does not prove
historical task execution, cold-start behavior, or future unattended behavior.

### Production-store integrity and recovery backlog

Read-only SQLite inspection of
`A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3` returned:

- file present and opened with `mode=ro`;
- `PRAGMA integrity_check = ok`;
- foreign-key violations: `0`;
- `operational_windows = 0` and `scheduler_ticks = 0`;
- `operating_mode = KILL_SWITCH`, `state_version = 36`;
- `UNKNOWN`/`AMBIGUOUS` status rows across outbox, dispatch, and reconciliation tables: `0`;
- readbacks: `85`;
- reconciliations: `58` (`45 RECONCILED_CONFIRMED`, `5 RECONCILED_ABSENT_SAFE_TO_RETRY`,
  `8 RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE`);
- outbox: `83` rows (`50 DISPATCH_CONFIRMED`, `27 DERIVATIVE_EXPIRED_STALE_NO_WRITE`,
  `3 READY`, `2 RECONCILED_ABSENT_SAFE_TO_RETRY`, `1 ASYNC_DERIVATIVE_FINALIZATION_FAILED`);
- platform dispatches: `58` rows (`51 DISPATCH_CONFIRMED`, `3 DERIVATIVE_EXPIRED_STALE_NO_WRITE`,
  `2 DISPATCH_CONFIRMED_NO_WRITE`, `2 RECONCILED_ABSENT_SAFE_TO_RETRY`).

The store is structurally healthy at rest. The `READY`, finalization-failed, and
content-incomplete rows are a recovery/housekeeping backlog; they are not classified
as `UNKNOWN_WRITE` by the current rows.

### Edge profile and destination identities

`http://127.0.0.1:9223/json/version` and `/json/list` were both unreachable. The bounded
Edge process classification found no instance exposing the canonical `contentops-social-main`
profile or a 9223 remote-debugging owner. Therefore current Edge attachment, browser
profile ownership, and live destination identity are `NOT_VERIFIED`.

The read-only store snapshot contains nine destination-readiness rows, but their latest
timestamps are 2026-09-01/02 and cannot be promoted to current host proof:

- stored rows show `READY_AUTHENTICATED` for Substack and YouTube Community;
- stored rows show `READY_NON_BROWSER_BINDING` for Discord, Facebook Page, Instagram Business,
  LinkedIn, Telegram, and Threads;
- stored X row is `REAUTH_REQUIRED` with `identity_match = 0` and no destination identity.

These values remain historical/stored diagnostics until a fresh canonical Edge 9223
readback is available.

## CLOSED CELLS

- At-rest SQLite structural integrity: closed `PASS`.
- At-rest foreign-key check: closed `PASS`.
- At-rest `UNKNOWN`/`AMBIGUOUS` row scan: closed `0`.
- Relevant scheduled-task state: closed as `Disabled` for the three ContentOps tasks.
- Current process ownership: closed as no matching ContentOps process in the bounded filter.

## NOT_VERIFIED / BLOCKERS

- Current Edge `contentops-social-main` CDP 9223 attachment and destination identities:
  `NOT_VERIFIED` because both local CDP endpoints were unreachable.
- Current live process command-line ownership beyond the bounded classification:
  `NOT_VERIFIED`.
- Current scheduler execution, cold-start, unattended runtime, and future calendar behavior:
  `NOT_VERIFIED`; disabled task state is not execution proof.
- Current public-provider account/session readiness: `NOT_VERIFIED`.
- Current live publication or readback: not attempted; no public write occurred.

## REUSED

- Existing V1 store and reconciliation tables.
- Existing `UNKNOWN_WRITE = STOP RETRY -> READ BACK -> RECONCILE` contract.
- Existing canonical source/evidence/epistemic validators.
- Existing BrowserOS Neo rendered-source seam on the same recovery branch.
- Existing `SIMPLE_GEMINI_RUNTIME` and `DurablePublicationCoordinator` ownership.

## CHANGED

- Added this read-only host-preflight receipt:
  `docs/automation/CONTENTOPS_CURRENT_HOST_READ_ONLY_PREFLIGHT_20261016.md`.
- No runtime/store/configuration mutation.
- No browser session, secret, cookie, token, credential, provider, or public destination write.
- No unrelated files were staged.

## EVIDENCE

- Browser-recovery implementation baseline: `4cdbf9d8098250479d5797ce4222c0f7680d0eb5`.
- The packet was committed as a descendant of that baseline; remote branch and PR-head
  readback matched after push.
- Browser/evidence/runtime focused regression: `167 passed`.
- The focused run covered browser-rendered recovery, public-secondary loading, epistemic-state
  preservation, Simple Gemini wiring, evidence adapters/loaders, route-health persistence, and
  V1 runtime preflight.
- `git diff --check`: passed for the recovery branch range.

## AUTHORITY

- Implemented: browser-rendered source-recovery architecture is present on the branch.
- Tested: focused code/test slice is green (`167 passed`).
- Branch-integrated: yes, branch is at the tested commit and remote-parity readback matches.
- Merged: not claimed.
- Deployed: not claimed.
- Runtime-proven: only the read-only at-rest store/task observations above; current Edge/browser
  attachment is not proven.
- Live-published: not claimed; no publication was attempted.

## NEXT

`PRODUCT_FIRST_AUTONOMOUS_V1_RESUME`: retain the recovery branch and let the existing
`SIMPLE_GEMINI_RUNTIME` / `DurablePublicationCoordinator` path observe the next authorized
routine window. Obtain a fresh owner-authorized Edge 9223 identity/readiness readback only when
an exact live boundary requires it; do not create a second scheduler, store, publisher, or V2
public-write path.
