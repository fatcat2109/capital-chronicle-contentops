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
-> ordered candidate source walk under one shared deterministic maximum of 6 total GETs
-> one bounded 9Router gemini-3.5-flash(high) article-writing invocation for the first source-qualified candidate
-> deterministic material-claim/source-byte validation
-> at most one bounded 9Router gemini-3.5-flash(high) revision without source expansion
-> one qualified zero-write canonical article record
-> exactly eight UNDISPATCHED derivative intents
-> separate existing DurablePublicationCoordinator only after explicit public-write authority
```

The source walk performs a maximum 6 requests total across the fixed admitted candidate plan.

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

`BoundedPublicSecondaryEvidenceLoader` remains the deterministic source-byte authority for the
fixed admitted candidate walk. 9Router has no native web-search/citation authority. Model-provided source
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
4. Only after that proof, bind the same CLI/runtime operation to a lightweight local scheduler.
5. Public-write enablement/readback remains a separate owner-gated step.

Final target remains 5–8 useful published articles per newsroom production day without filler.
