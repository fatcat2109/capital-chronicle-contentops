# Codex Desktop V1 Newsroom Operator

Authority date: 2026-08-16

Operating mode: `OPERATOR_LIGHT_CODEX_DESKTOP_SCHEDULED_MODE`.

Default editorial brain: native Codex Desktop `gpt-5.6-sol`, reasoning effort `XHIGH`.

This is the reusable instruction for one fresh native Desktop task. It is not a Codex CLI job,
Desktop bridge, UI-automation lane, second scheduler, second newsroom, or persistent chat-memory
system. The historical fully unattended Final Daily App North Star is not rewritten by this
interim owner-authorized mode.

## Exact task prompt

```text
Read docs/automation/CODEX_DESKTOP_V1_NEWSROOM_OPERATOR.md and execute exactly one current V1 editorial opportunity to its truthful terminal result.
```

## One-opportunity contract

1. Work only in V1. Do not read, edit, execute, publish, or update V2.
2. Use the canonical production store, output root, newsroom facade/orchestrator, current evidence
   path, publication plan, and `DurablePublicationCoordinator`. Do not create a database, queue,
   broker, scheduler, publisher, state file, model bridge, or parallel authority.
3. Before story judgment, build a fresh read-only continuity rehearsal with
   `live_contentops.codex_desktop_newsroom_operator_v1.build_live_zero_write_rehearsal`. It must:
   derive the last terminal cutoff from existing durable work-item and cycle evidence; load current
   intake; exclude unchanged evaluated identities; retain late-arriving unseen identity and
   material-update/correction/contradiction/new-phase chains; load reconciled canonical Substack
   publication memory; rediscover the complete current Capital Chronicle estate with cache bypass;
   inspect its exact governed surfaces; and query story-scoped context.
4. If an existing opportunity is active, an unresolved `UNKNOWN_WRITE` exists, or exact public
   identity is ambiguous, do not start another opportunity. Recover/read back/reconcile through
   existing authority or terminate with the exact blocker.
5. Evaluate only the current candidate universe: unseen headline identity since the last terminal
   cutoff plus materially changed existing story chains. Do not use only `timestamp > last_run`.
   Exclude unchanged repeats and already-published stories without a meaningful delta.
6. Choose the strongest useful story or abstain. Exactly one canonical article maximum. No filler,
   arbitrary word ceiling, heading quota, media quota, or fixed article template.
7. Codex Desktop XHIGH owns final story judgment, thesis, headline/dek, depth, structure, prose,
   supported explanation, and chart/media editorial judgment. The task itself must author the
   final editorial packet and bind it to the existing canonical article-builder/release-candidate
   seam; do not route final editorial authorship through Codex CLI, App Server, a bridge, or a new
   broker. Model assertions are never factual or numeric authority.
8. Research current facts on the latest web. Prefer primary official evidence and strong
   professional reporting. One trustworthy source can support an ordinary, non-disputed core
   proposition; enhanced-risk claims retain stronger evidence. Omit, narrow, or abstain on
   unsupported claims.
9. Treat arbitrary read-only Capital Chronicle database matches as `CONTEXT_OR_DISCOVERY_ONLY`.
   They may guide priority, history, questions, or chart ideas and grant zero publication
   authority. Only an exact compatible current governed CC publication/analysis packet may
   authorize proprietary calculations, scenarios, probabilities, forecasts, regimes, or numeric
   conclusions. Reassess `known_at`, `as_of`, source time, run/model identity, lineage, DQR,
   quality, and current story scope before use. Unknown governed schema fails only that capability
   as `CC_GOVERNED_SURFACE_COMPATIBILITY_REQUIRED`; continue unrelated ordinary journalism.
10. Prefer useful governed CC analysis or charts when current, story-relevant, and exactly
    authorized. Preserve packet identity, as-of time, series/calculation identity, and observed
    versus forecast/scenario labels. Never manufacture a number.
11. Media may be zero. When useful, use real rights-cleared documentary/context imagery, real
    authority-person imagery, exact governed charts, or readable primary documents. Generated
    imagery never represents documentary reality.
12. Run deterministic factual, numeric, freshness, rights, destination-identity, KILL_SWITCH,
    content-lock, and publication gates. The newsroom returns one plan and never calls a public
    adapter directly. Only `DurablePublicationCoordinator` may dispatch.
13. Canonical success requires the exact Capital Chronicle Substack destination, a public `/p/...`
    URL, sufficient article/content identity match, strict readback/reconciliation, and
    `UNKNOWN_WRITE=0`. Unknown write means `STOP RETRY -> READ BACK -> RECONCILE`.
14. Derivatives are asynchronous and destination-local. They do not hold a confirmed canonical
    article or the next opportunity.
15. Persist the truthful terminal opportunity through the existing work-item, transition, cycle
    intake/evidence, publication/readback/reconciliation, and published-memory artifacts. The
    terminal intake cutoff becomes the next run's prior cutoff. An abstention is a valid terminal
    result and advances the cutoff; an active, interrupted, or unknown-write opportunity does not.
16. Return one compact terminal report: cutoff before/after, unseen and material-update counts,
    excluded unchanged/published counts, CC catalog fingerprint/change state, governed-authority
    use or non-use, story/publication or abstention result, canonical URL when confirmed,
    reconciliation state, public-write count, and exact blocker/next action.

## Manual `GO`

`GO` means: execute exactly one additional current V1 editorial opportunity now under this same
contract. It uses the existing durable cutoff, evaluated identities, material-update semantics,
published memory, evidence rules, CC authority split, and publication gates. It does not reset or
move the cutoff before a truthful terminal result and bypasses no gate.

Exact manual prompt:

```text
GO — Read docs/automation/CODEX_DESKTOP_V1_NEWSROOM_OPERATOR.md and execute exactly one additional current V1 editorial opportunity now under the same durable cutoff and all existing gates.
```

## Native Desktop scheduled-task configuration

Use standalone fresh scheduled tasks against project
`A:\Capital Chronicle\ContentOps`, timezone `Asia/Bangkok`, model `gpt-5.6-sol`, reasoning effort
`XHIGH`, and the exact task prompt above. Enable only while Jim has opened Codex Desktop for the
active newsroom day. Do not use a persistent heartbeat conversation.

Create these weekday bootstrap opportunities:

| Group | Task name | Bangkok local recurrence |
|---|---|---|
| London | `V1 Newsroom — London 1400` | Monday–Friday at 14:00 |
| London | `V1 Newsroom — London 1700` | Monday–Friday at 17:00 |
| London | `V1 Newsroom — London 2000` | Monday–Friday at 20:00 |
| New York | `V1 Newsroom — New York 2100` | Monday–Friday at 21:00 |
| New York | `V1 Newsroom — New York 2300` | Monday–Friday at 23:00 |
| New York | `V1 Newsroom — New York 0100` | Tuesday–Saturday at 01:00 |
| New York | `V1 Newsroom — New York 0300` | Tuesday–Saturday at 03:00 |

The midnight split preserves the prior New York business day in Bangkok local time. This fixed
bootstrap cadence approximates three-hour London and two-hour New York opportunities, gives New
York four opportunities versus London's three, and does not run routine XHIGH editorial work
throughout the full day. It is not claimed optimal; daylight-saving shifts and real performance
evidence may justify later changes.
