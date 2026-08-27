# ContentOps V1 Simple Gemini Runtime Reset V1

Authority date: 2026-08-27
Status: `CURRENT_V1_EXECUTION_AUTHORITY`

This owner-approved reset supersedes routine Codex Desktop newsroom production and the legacy
evidence-ready/split-phase worker critical path. Historical artifacts remain valid evidence; they
do not route current execution.

## Current V1 routine path

```text
current headline sidecars + canonical reconciled published memory + optional read-only CC context
-> deterministic duplicate suppression and a packet of at most 32 current candidates
-> one strict 9Router gemini-3.5-flash(high) selection admitting one useful primary and <=2 useful fallbacks
-> ordered first-party-aware candidate source walk under one shared deterministic maximum of 6 total GETs
-> one bounded 9Router gemini-3.5-flash(high) article-writing invocation for the first source-qualified candidate
-> deterministic material-claim/source-byte validation
-> at most one bounded 9Router gemini-3.5-flash(high) revision without source expansion
-> one qualified zero-write canonical article record
-> exactly eight UNDISPATCHED derivative intents
-> separate existing DurablePublicationCoordinator only after explicit public-write authority
```

The source walk performs a maximum 6 requests total across the fixed admitted candidate plan.
For each candidate it uses the shortest governed route: exact already-bound trustworthy source;
existing allowlisted official/company-primary locator followed by exact accepted document bytes;
then existing reputable-secondary locator/resolution fallback. Every route consumes the same
ledger. Locator/search/listing bytes are discovery-only and never satisfy article evidence.

Normal success uses two logical model invocations. Three is the absolute ceiling when the one
revision is needed. Each Simple logical invocation uses only `vx/gemini-3.5-flash(high)` with one
provider attempt and no fallback/retry. A candidate-local source failure preserves its blocker and
continues only to the next candidate admitted by the original selection while shared budget remains;
there is no second selection or frontier reopening. Codex runtime model calls required: `0`.

The production proof runner opens the existing production store with migrations disabled and uses
the canonical publication read model through SQLite read-only/query-only access. Duplicate filtering
happens before selection; only compact published-memory counts and set hashes enter the model prompt.

The reset intentionally removes from the routine critical path: broad evidence-ready pools,
semantic leaf/global checkpoint replay, native PREPARE/COMPLETE worker handoffs, deficit-driven
multi-candidate catch-up inside one scheduled task, and any scheduled Codex repo building/debugging.

`SimpleFirstPartyAwareEvidenceResolver` composes the existing
`BoundedOfficialPrimaryEvidenceLoader` and `BoundedPublicSecondaryEvidenceLoader` without creating
another evidence schema or authority. The existing loaders remain deterministic source-byte
authority for the fixed admitted candidate walk. 9Router has no native web-search/citation authority. Model-provided source
timestamps are not authority. Every material fact, number, quote, or causal claim must bind to
retrieved source bytes. Proprietary Capital Chronicle forecast/probability/scenario/regime/numeric
claims remain unavailable in this initial reset lane unless exact publication-authorized CC
authority is added later.

Substack remains canonical and the eight derivative destinations remain Telegram, Discord, X,
LinkedIn, Facebook Page, Instagram Business, Threads, and YouTube Community. The reset produces
intent only; it grants no public write. The existing publication coordinator remains the sole
public-write owner and `UNKNOWN_WRITE = STOP RETRY -> READ BACK -> RECONCILE`.

## Reuse / supersession

- PR #19 locator/retrieval primitives: `CURRENTLY_PROVEN_AND_REUSE` as selected-story donor only.
- PR #20 article/package proof: `CURRENTLY_PROVEN_AND_REUSE`.
- PR #29 material-claim/validate-after concepts: `CURRENTLY_PROVEN_AND_REUSE` as verifier donor.
- PR #30 native split-phase redesign: `SUPERSEDED_DO_NOT_REUSE` for routing; host evidence remains valid.
- PR #31 legacy resume/revision repair: `SUPERSEDED_DO_NOT_REUSE` for routing; runtime evidence remains valid.
- Codex Desktop: builder/debugger/host-proof capacity only, second-last execution lane.

## Acceptance sequence

1. Static implementation and exact-head CI.
2. One isolated zero-write host canary using current real sidecars and 9Router.
3. Inspect the real article, source/claim bindings, model/request economics, and eight intents.
4. Bind the same CLI/runtime operation to the owner-locked four-window lightweight local scheduler
   and prove injected-clock due/idle/duplicate/restart behavior with zero public write.
5. Public-write enablement/readback remains a separate owner-gated step.

Steps 1–4 are now complete for the current Simple path. The scheduler performs one independent
canonical one-article invocation per bounded slot; it does not turn Simple into a multi-article
call. Its stable identity is production day + canonical window + slot ordinal. Before every slot it
reloads canonical reconciled publication memory and adds only valid countable zero-write qualified
records from the same persistent scheduler output root, so a PASS becomes duplicate-suppression
memory before the next slot. Terminal window/slot receipts are hash-bound and restart-safe. No
fifth window, material-event expansion, Codex Automation/Desktop routing, second publication store,
publication coordinator dispatch, or public/provider write was added.

Final target remains 5–8 useful published articles per newsroom production day without filler.

## Current host proof

The final 2026-08-27 news-peg/public-metadata-integrity current-sidecar canary passed: 32 governed
candidates, one verified Flash selection, three admitted candidates, two total deterministic GETs
(configured NVIDIA issuer feed then exact current earnings release), one verified Flash writer,
deterministic validation PASS with twenty-two supported material claims across the earnings-led
title, dek, search title, meta description, social hook, and body, zero revisions, one qualified article, and exactly eight
UNDISPATCHED intents. Production memory was read through SQLite read-only/query-only access with
migrations disabled and unchanged bytes. Codex runtime calls, public writes, provider publication
writes, and `UNKNOWN_WRITE` were all zero. This proves the article path; it grants no scheduler or
public-write authority.

The current local-scheduler host proof also passed its exact bounded claim. An injected production-
shaped 17:00 Bangkok due tick derived one canonical production-day/window identity and two bounded
slot identities, then reached the canonical Simple operation independently for both slots. Each
slot received 32 candidates and used two source GETs; slot 1 qualified in two Flash logical calls
without revision, while slot 2 saw the refreshed memory (`3 canonical + 1 zero-write qualified`),
selected a distinct story, and qualified in three calls with the one permitted revision. Both
records persisted exactly eight UNDISPATCHED intents. A second process repeated the due tick with
zero model/source/memory work because the terminal window survived restart; an idle tick also
performed zero semantic/network work. The production SQLite SHA-256 was unchanged before/after.
Codex runtime, public write, provider publication write, publication-coordinator dispatch, and
`UNKNOWN_WRITE` counters remained zero. This is scheduler mechanics evidence, not a full
production-day, 5–8/day, or public-publication acceptance claim.

## Persistent current-host closure

The production scheduler root is now fixed at
`A:\Capital Chronicle\Runtime\ContentOps\simple_gemini_scheduler_v1`; proof roots remain explicit
overrides. One detached Simple scheduler process owns the root through one process-lifetime OS lock
and a hash-bound PID identity. Launcher readback proved `STARTED`, sequential duplicate
`ALREADY_RUNNING`, clean `STOPPED`, and `RESTARTED` on the same root. Terminal production-day,
window, and slot identities survived the restart. Repeated idle polls and terminal-window polls
performed zero Simple/model/source/memory work. Checkpoint and safety exceptions remain visible and
are never converted into blind semantic retries; every acquired window lock releases through an
unconditional `try/finally`.

The existing canonical intake path was current-host revalidated rather than rebuilt. The locked
`CapitalChronicleBot` Chrome/CDP 9222 profile was resumed, the canonical X list route returned
`READY`, and one supported bounded capture appended fresh deduplicated sidecars. At the proof epoch,
the newest accepted headline timestamp was `2026-08-27T20:24:23Z` and the rolling 24-hour universe
contained 1,298 candidates. A same-production-day 17:00 Bangkok scheduler tick supplied 32 current
candidates per slot to the canonical Simple operation. Both independent slots truthfully ended
`ALL_ADMITTED_CANDIDATES_SOURCE_RETRIEVAL_BLOCKED` after one Flash selection and six GETs each; no
article was manufactured. Production publication SQLite SHA-256 remained unchanged. Codex runtime
calls, public writes, provider publication writes, publication-coordinator dispatch, and
`UNKNOWN_WRITE` were all zero.

This closes persistent current-host zero-write runtime only. The next product slice is Simple
Editorial Growth Edge reuse/integration before routine public-write enablement. It must reuse the
existing Institutional Edge editorial contract, `CAPITAL_CHRONICLE_VIEW`,
`WHAT_THE_MARKET_IS_MISSING`, fact/opinion/Core-Analyzer authority separation, native eight-
destination packaging, and compatible existing source discovery/retrieval capabilities. It must
investigate the carried `ALL_ADMITTED_CANDIDATES_SOURCE_RETRIEVAL_BLOCKED` result before adding any
new discovery system. PR #36 does not implement that slice. Separate public-write/readback, real
production-day 5–8 useful published/day acceptance, and explicit `V1_FINAL_PRODUCT_ACCEPTED` remain
later gates in that order.

The selected candidate is always the current article peg. Title/dek must remain led by that event;
older/background highlights in a current document use temporally neutral wording unless exact bytes
prove chronology, and co-location in one document never proves simultaneity. Every non-empty title,
dek, search title, meta description, and social hook requires an exact material-claim binding under
the same fail-closed validator as body claims. Unsupported public terminology inflation, including
calling financing platforms a `fund`, is blocked.
