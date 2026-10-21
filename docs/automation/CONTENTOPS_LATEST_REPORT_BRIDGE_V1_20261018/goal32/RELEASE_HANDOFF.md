# Goal32 — reviewed native packet to existing publisher

Date: 21 October 2026. Classification: `PARTIAL_CAPABILITY_REUSE_COMPONENTS`.
Scope: V1 articles, text/social packages, still media and YouTube Community. V2 video,
audio, Shorts and Reels remain isolated and unassigned. Same worktree, draft PR90 and
owner-manual store/profile as Goal31. No live sends, platform drafts or activation.

## Runnable release candidate

`native_desktop_publication_v1.py` composes the existing `SimplePublicationHandoffV1`,
sole `DurablePublicationCoordinator`, `bind_native_neo_coordinator` and
`NativeNeoExecutor`. It adds no publisher, store, scheduler or Python-to-chat API.
Existing Telegram/Discord/Meta/Threads/LinkedIn transports remain in the canonical
transport runtime. `FinalDailyAppProductionRuntime.reviewed_publication` reuses that
runtime's exact coordinator/executor; the CLI binds the same existing components.

| Component | Existing capability reused | Goal32 delta |
| --- | --- | --- |
| Native review/media handoff | Exact KEEP review, retained media, eight previews, qualified record and plan | Seal review, native result, source/evidence, binding and five artifact hashes in the existing outbox |
| Simple publication handoff | Plan validation, work identity and recovery before resume | Native owner operation calls its existing `resume` |
| Durable coordinator | Canonical first, strict readback, URL finalization, destination-local recovery and deterministic IDs | No replacement or bypass |
| Native Neo executor | Request → begin → actual tool observation → submit, lost-write readback | CLI continuation handles pending identity and publication requests |
| Existing four slots | Production day/window/slot identity and bounded catch-up | Activated windows retain the reviewed slot for publication; zero-write windows continue candidate work |
| Existing Desk | Articles, reviews, media, previews and history | Actual prepared/pending/reconciled records, command and per-destination blockers |

Manual and scheduled entry points use `binding.run_id` as the existing publication
work identity, the persisted plan hash, and the coordinator's existing destination IDs.
Restarting does not create another semantic result or public intent. Preparation/status
never probe a destination or dispatch. Status skips migrations and outbox registration.

## Actual retained workspace proof

`real_packet_operations.json` records preparation, status, manual dispatch rejection and
reopen of `goal31-company-machine-reading`, `goal31-futures-cashflow` and
`goal27-gas-refill-update`. Each is PREPARED with nine NOT_DISPATCHED destinations;
each manual resume is rejected as `OWNER_MANUAL_PUBLICATION_NOT_AUTHORIZED`.
The edition remains **3 KEEP articles / 24 previews / 0 missing**. Reopen performs zero
new model invocations or source requests. These are real private packets, not published
counterparts. No new selector, writer or source cycle was assigned.

`retained_goal31_packet.json.gz` is a lossless public-source editorial packet exported
from the original manual outbox before preparation. Tests relocate its exact article,
evidence and PNG bytes into newly created disposable stores; they do not copy/adopt the
production store. Controlled slot IDs/reviews and observations are explicitly test data.

`preservation_final.json` reconciles the pre-change files, outbox payloads, reviews, profile,
relocation manifest, four PAUSED host tasks and production pause. New internal publication
bindings are the only intended manual outbox additions. The final verification receipt
and exact remote-head CI are separate delivery evidence; local tests are not deployment.

## Supported owner operations

The agent handles command and observation details. Jim does not assemble claim/return JSON.
From this checkout, for the existing manual packet:

```powershell
python scripts/run_native_desktop_editorial.py publication-status --binding "C:/Users/bullw/AppData/Local/CapitalChronicle/ContentOps/editorial-previews/goal31-company-machine-reading/binding.json"
```

`publication-prepare --binding <existing-binding>` seals the reviewed packet without
dispatch. `publication-status` validates that seal and projects the actual records.
The Desk displays the exact continuation command and dispatch boundary. A changed source,
review, native result, artifact or media hash invalidates continuation before tool begin.

After a **separately authorized future production transition**, a genuine registered App
slot uses its `native_operation_binding.json`:

```powershell
python scripts/run_native_desktop_editorial.py publication-prepare --binding <scheduled-binding>
python scripts/run_native_desktop_editorial.py publication-resume --binding <scheduled-binding> --rollout config/native_desktop_rollout_v1.json --native-invocation-id <actual-turn-id>
```

For each returned pending request, use `publication-tool-begin` with the same binding,
rollout, actual invocation ID and `--request-sha256 <exact-request>`. Execute that exact
request through `mcp__browseros_neo__run` in the active Desktop conversation. Submit the
actual observation using `publication-tool-submit` and `--response <observed-return.json>`;
then resume the same operation. The existing executor validates tool name, invocation,
surface, observation time, request/return hashes and exact identity/content/media.
If begin first requests VERIFY_IDENTITY, complete that read-only request before the
original action. Never replace a pending observation with an invented successful return.

A claimed PUBLISH whose return was lost must resume the coordinator for READBACK.
Do not begin it again. A still-live original tool can submit its genuine return. Canonical
Substack identity and an exact real `/p/` URL/content readback precede all eight derivatives.
The existing compiler then binds the real URL with zero model/source calls. Placeholders
remain private. Derivative failures stay local; UNKNOWN_WRITE requires readback before retry.

## Verification and limits

Nine focused controlled tests cover retained real-copy preparation/manual isolation,
canonical-first finalization into eight distinct packages, same-operation restart/dedupe,
crash before action, lost successful-write response and readback-only recovery, local
derivative failure/retry, source/review/artifact invalidation, activation/binding rejection,
the actual scheduler in publication and zero-write modes, pending current-identity request,
and reuse of the production runtime's existing coordinator/executor. See
`controlled_tests.xml`; fixtures prove orchestration, never browser or login truth.

Connected regression evidence: 50 tests passed (five then-current Goal32 controls included);
30 existing UI read-model tests passed. Final UI tests/build/lint and the focused controls
are recorded in `verification.json`. No whole-repository or natural-day reliability claim.
Neo inspected the actual Desk at desktop and 390px mobile, including the opened publication
panel, all three cards and 24 previews. Saved screenshots show the manual boundary and
NOT_DISPATCHED statuses. Existing accepted article/media inspection remains valid because
the original bytes were retained. No external published counterpart is established for these Goal31 manual packets;
no external object was invented and no account/token diagnostic loop was run.

## One finite activation handoff

Goal32 completes the operating composition RC. The next owner decision is an exact, scoped
transition for this native composition: deploy the reviewed bytes through the normal path,
authorize the existing four App tasks and production pause/mode transition, and explicitly
authorize V1 dispatch if desired. This goal performs none of those actions. The current
rollout still declares no public-write authority. A future activated fresh App window must
register its own immutable rollout/window/slot binding; do not flip a manual flag, copy this
manual database into production, or rewrite an old frozen window to manufacture authority.
Destination identity/readback proof is obtained just in time for that destination, without
making every channel a gate on editorial work.

Current unverified external facts: current Substack/X/YouTube publishing identities; API/bot
permission and destination identity validity; actual Goal32 public object/content readbacks;
calendar-time unattended execution, deployment and natural 5–8/day reliability. Configuration,
stored credentials, controlled observations and green CI prove none of these.

Control Tower receiver synchronization is pending: this session exposes no Control Tower
connector and Goal32 forbids messaging other Builders. This discoverable handoff, current
authority/runtime/lane/source pointers and refreshed existing CodeGraph are the transfer
surface. Do not claim receiver synchronization. Exact source/graph/remote/CI identities are
read back into the PR and local Desk delivery receipt after commit.
