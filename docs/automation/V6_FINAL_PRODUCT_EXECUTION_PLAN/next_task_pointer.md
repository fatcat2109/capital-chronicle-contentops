# ContentOps — Current Next Task Pointer

Authority date: 2026-08-08

Current product-direction classification:

`CONTENTOPS_DAILY_LIVE_V1_OWNER_DIRECTION`

Current North Star:

`docs/automation/CONTENTOPS_DAILY_LIVE_V1_NORTH_STAR.md`

Current execution master plan:

`docs/automation/CONTENTOPS_DAILY_LIVE_V1_ACCELERATED_LAUNCH_MASTER_PLAN.md`

## Current exact task

`TASK_CONTENTOPS_DAILY_LIVE_CANONICAL_STORY_EVIDENCE_AND_FIRST_FRESH_CANARY_V1`

Mode:

`AUTONOMOUS_DEFAULT`

## Why this is next

The rolling-X newsroom has already advanced through current-X ingestion, hierarchical semantic assignment, global ranking, checkpoint resume, semantic story-type classification, and capability-driven targeted evidence.

The latest frozen six-rank cycle correctly returned governed `NO_PUBLICATION`, but it exposed the remaining canonical launch gap:

1. normal canonical `_run_rolling_x_newsroom_cycle()` still depends on externally supplied `story_type_by_cluster` rather than automatically invoking semantic story routing;
2. its default targeted evidence adapter does not automatically bind bounded official-primary evidence acquisition;
3. evidence contracts still need explicit `story_type + article_mode` resolution so factual reporting is not unnecessarily blocked by analytical requirements that belong only to analysis modes.

Do not reroute backward into leaf/global assignment repair. Do not require a generic Capital Chronicle packet as a discovery prerequisite.

## Required capability

The task must deliver the normal canonical flow:

```text
fresh rolling-X universe
→ hierarchical assignment
→ automatic exact story-type routing
→ article-mode selection
→ mode-aware evidence profile
→ bounded capability/source-family acquisition
→ first evidence-viable ranked story OR explicit abstention
→ article / SEO / visuals
→ semantic review / bounded revision
→ native packages
→ exact READY_* publication gates
→ strict readback/reconciliation
```

## Launch evidence policy

Evidence burden is resolved by:

`story type + article mode → exact evidence profile`

Minimum launch cases:

- `regulatory_fiscal_event + straight_news` → authoritative official document/timeline/affected-entity evidence; no Capital Chronicle market analysis solely because the story is market-sensitive;
- `company_sector_event + straight_news` → authoritative company/SEC facts; no Capital Chronicle analytical model unless analytical claims are made;
- `company_sector_event + analysis` → relevant Capital Chronicle analytical/market authority required;
- `data_release + straight_news` → exact official release values/timestamps/definitions;
- `data_release + analysis` → appropriate Capital Chronicle analytical/market authority required.

ContentOps must not originate analytical/numeric truth.

## Initial source-family priority

Implement/reuse only what directly closes Daily Live:

1. `official_regulatory_fiscal`
2. `company_primary` / `sec_regulatory`
3. `official_macro`
4. existing governed Capital Chronicle authority where genuinely required

Do not build licensed-news breadth or every source family before launch.

## Live authority

Owner live authority remains limited to dynamically verified canonical:

- `READY_AUTHENTICATED`
- `READY_NON_BROWSER_BINDING`

destinations under all existing deterministic gates.

Unknown write:

`STOP RETRY → READ BACK → RECONCILE`

Persistent browser roles remain:

- Chrome `CapitalChronicleBot` CDP `9222`: ingestion only;
- Edge `contentops-social-main` CDP `9223`: publication/readback only.

Never inspect/export session or credential material.

## Fast-ship stop rule

At the first NEW substantive problem, stop immediately.

Do not create blocker-closeout docs, status ceremony, broad test runs, or repeated correction loops merely to close the task.

A correctly blocked ranked story is not an implementation defect; continue cheaply to the next rank. A final governed `NO_PUBLICATION` is valid.

## After this task

If the canary reaches a correct terminal state with no substantive architecture/runtime blocker, the default next action is:

`CONTENTOPS_DAILY_LIVE_PROBATION_5_TO_10_OPERATING_DAYS`

Initial cadence:

- one scheduled core editorial decision/day;
- one optional material-event trigger;
- no mandatory publication quota.

Capital Chronicle social destination attachment proceeds in parallel and does not block Daily Live.

After probation:

```text
minimal final V5 operator UI using real production states
→ Daily Live acceptance
→ new technical release target v1.1.0
→ ContentOps v2.0.0 Pro Video Factory
```

Protected historical `v1.0` remains immutable.