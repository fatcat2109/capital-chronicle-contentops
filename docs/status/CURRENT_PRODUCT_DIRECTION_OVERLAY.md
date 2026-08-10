# Capital Chronicle ContentOps — Current Product Direction Overlay

Authority date: 2026-08-10

Current product-direction classification:

`CONTENTOPS_FINAL_DAILY_APP_V1_OWNER_DIRECTION`

Current North Star:

`docs/automation/CONTENTOPS_FINAL_DAILY_APP_V1_NORTH_STAR.md`

Current execution master plan:

`docs/automation/CONTENTOPS_FINAL_DAILY_APP_V1_MASTER_PLAN.md`

Future video direction retained but deferred:

`CONTENTOPS_TIER2_PRO_VIDEO_FACTORY_OWNER_DIRECTION_V1`

GitHub remote refs/commits/diffs/exact fetched bytes remain repo-state authority. Jim's latest explicit instruction remains product-direction authority. This overlay supersedes conflicting sequencing/scope text in older Daily Live, Tier-1, V6, status, ledger, and Tier-2 gating documents while preserving verified historical evidence and safety invariants.

## 1. Current owner decision

The final Tier-1 product is no longer defined as a narrow Daily Live probation followed by early parallel V2 work.

The owner now requires one complete autonomous Daily App that can remain running 24/7 and own the routine ContentOps operating loop:

```text
always-on low-cost supervision
→ learned / configured editorial windows + material-event wakeups
→ current newsroom decision
→ exact evidence
→ grounded article / SEO / source-backed media
→ review / bounded revision
→ platform-native packages
→ autonomous publication to every currently READY configured Tier-1 destination
→ strict readback / reconciliation / post management
→ real performance + search/subscriber observations where available
→ bounded learning of timing / SEO / content / packaging policy
→ next window
```

`NO_PUBLICATION` remains valid and no publication quota is introduced.

The historical Daily Live North Star and accelerated plan remain useful precursor evidence, but they no longer control final V1 sequencing where they conflict with this overlay.

## 2. Product boundary

Capital Chronicle main owns analytical and numeric authority:

- economic/market analysis;
- micro/macro/global-macro reports;
- deterministic model calculations;
- scenarios and probabilistic views;
- Bayesian cases/updates;
- forecasts and regimes;
- numeric truth and realized-outcome attribution.

ContentOps owns the autonomous newsroom/distribution/learning product:

- headline/current-event discovery;
- clustering/update chains;
- evidence/permission/freshness/material-delta gates;
- ranking/select/hold/no-publication;
- factual reporting from authoritative evidence;
- faithful Capital Chronicle transformation;
- writing/editing/SEO/source-backed visuals and deterministic charts;
- platform-native packages;
- publication/readback/reconciliation/incidents;
- public-object lifecycle and performance observations;
- bounded timing/editorial/SEO/package learning.

Engagement and learning may never alter evidence truth, permissions, Capital Chronicle analytical output, or numeric authority.

## 3. Verified baseline at the direction change

Remote master at the direction change:

`7a04932a67df1af4c3dd10e9cc435dff140e23c8`

This baseline includes the canonical rolling-X grounded article/media builder and policy-decision evidence profile, but the latest fresh canary legitimately ended `NO_PUBLICATION / ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED` before article generation.

The controlled zero-write vertical slice demonstrated article + three media assets + semantic review + package/readiness compatibility.

Current known product defects that must be corrected rather than ignored:

1. framing/X-derived `entities_topics` can be presented on a fact card as though copied from accepted evidence;
2. deterministic source-backed renders blanket-declare `capital_chronicle_owned`, which may overclaim rights in underlying official source/excerpt content;
3. the current Federal Reserve official-policy locator endpoint returned HTTP 404 in the fresh canary;
4. real fresh end-to-end publishability remains unproven.

## 4. Current execution route

```text
FDA-A publishability provenance / rights / official-policy-source correction   [COMPLETE]
+
FDA-B always-on Daily App runtime vertical slice                               [COMPLETE]
        ↓
FDA-C autonomous multi-platform publication + post lifecycle                   [COMPLETE]
        ↓
FDA-D real performance observation                                             [COMPLETE]
        ↓
FDA-E bounded closed-loop timing / SEO / editorial / packaging learning        [COMPLETE]
        ↓
FDA-F final V5 Daily App UI from real states                                   [PASS accepted]
        ↓
FDA-G genuine calendar-time live soak                                          [SOAK ACTIVE]
        ↓
ContentOps V1 Daily App acceptance + v1.1.0
        ↓
freeze V1
        ↓
V2 Pro Video Factory
```

Do not reopen broad horizontal hardening.

Owner decision recorded on 2026-08-10 reprioritizes Tier-2 implementation to proceed
concurrently with the continuing FDA-G genuine calendar-time evidence lane. This supersedes
the earlier "defer all V2 work until after V1 freeze" sequencing text above where it
conflicts. V2 must remain isolated from the live V1 production runtime and this
reprioritization grants V2 NO video public-write authority. FDA-G remains active and this
reprioritization does not declare FDA-G accepted.

## 4A. V1 desktop operating contract (owner decision, 2026-08-10)

Manual one-click morning resume is an accepted V1 desktop operating pattern. Jim does not
want V1 operation to depend on keeping the Windows host awake 24/7.

```text
host available
→ one-click launch/resume (Start_ContentOps_Daily_App.cmd)
→ reconstruct the SAME durable production state
→ continue autonomous operation
→ planned host sleep/shutdown is recorded truthfully
→ next morning resume safely
→ never reset or manufacture state merely because the host was offline
```

Restart/recovery/idempotency are product requirements of the launcher:

- exactly one canonical supervisor;
- no duplicate editorial cycles or public objects;
- the canonical production store is reused, never recreated or reset;
- the canonical Edge 9223 bootstrap and KILL_SWITCH state are preserved;
- pending UNKNOWN_WRITE/reconciliation state is left for canonical recovery logic;
- missed editorial windows are handled by canonical supervisor/freshness logic, never
  blindly replayed by the launcher;
- ambiguous port ownership fails closed.

Canonical one-click entry: `Start_ContentOps_Daily_App.cmd` → `scripts/Start-ContentOpsDailyApp.ps1`
→ `python -m live_contentops.daily_app_launcher_v1` → canonical
`python -m live_contentops.cli daily-app start ...` delegation. The one-click flow also safely
bootstraps the exact existing Chrome `CapitalChronicleBot` CDP 9222 ingestion profile when
absent (no profile clone/reset, no login automation; REAUTH_REQUIRED is reported truthfully).

An operator `Run editorial cycle now` control (V5 Today +
`POST /api/daily-app/control/run-now`) requests one governed editorial evaluation through a
durable, restart-safe, append-only `OPERATOR_REQUESTED` trigger (schema v9). It bypasses ONLY
the wait for the scheduled window; every evidence, review, freshness, permission, readiness,
and publication gate remains unchanged; it never changes operating mode and never clears
KILL_SWITCH; it never claims publication. The quarantined `POST /api/run-pipeline` stays locked.

## 5. Always-on runtime doctrine

Always-on does not mean always calling models.

Idle behavior should be deterministic/cheap where possible: durable-state health, intake freshness, next-window calculation, material-event checks, readback/reconciliation, due performance observations, learning evaluation, and incident handling.

Expensive newsroom/model work should wake only when a due editorial decision or material-event trigger warrants it.

The always-on supervisor must route actual newsroom/publication work through the existing canonical production orchestrator and durable store. It must not become a second production pipeline or second state authority.

## 6. Scheduling and learning

The historical one-decision-per-day cadence becomes a safe bootstrap policy, not final product truth.

The final app must maintain a versioned editorial-window policy and may improve it from real qualified engagement while preserving freshness, materiality, anti-spam spacing, platform constraints, and no-publication freedom.

Learning may update bounded policy for:

- decision/publication windows;
- editorial-priority weights;
- headline/framing preferences;
- SEO intent/structure/refresh strategy;
- content depth/mode preference;
- visual/package strategy;
- destination-native packaging;
- concentration penalties.

Learning may not change evidence, factual truth, permissions, account identity, Capital Chronicle authority, or safety gates.

Small samples must produce observations/no-op decisions rather than large automatic changes.

## 7. Distribution and performance

Tier-1 configured text/image destinations remain Substack, Telegram, Discord, X, LinkedIn, Facebook Page, Instagram Business, Threads, and YouTube Community.

At runtime, publish only to exact current `READY_AUTHENTICATED` / `READY_NON_BROWSER_BINDING` destinations.

The final app must manage each known public object through readback, reconciliation, performance observation, and learning identity.

The current manual/offline performance paths are useful foundations but are not the final production metrics loop. Real safe collectors must be wired for available configured destinations, with missing metrics remaining unavailable rather than zero.

## 8. Canonical UI

`ui/contentops_v5/` remains the canonical UI.

Final V1 UI should act as the Daily App control surface for Today, Queue, Published, Performance, Learning, Platforms, Incidents, and operating controls.

Do not rebuild it before enough real runtime state exists to ground the final design.

## 9. Protected release and browser authority

Historical `v1.0` remains immutable at release commit `6983bfb3ef300414b744f3f8f97ca81ff699348b`.

Persistent browser roles remain:

- Chrome `CapitalChronicleBot`, CDP `9222`: X/headline ingestion only;
- Edge `contentops-social-main`, CDP `9223`: publication/media management/readback and explicitly supported read-only performance observation only.

Never inspect/export cookies, storage, tokens, credentials, or session databases.

Canonical ingestion continuity lock (owner decision, permanent): the canonical X ingestion
binding is the existing operator-owned `CapitalChronicleBot` persistent profile on Chrome CDP
`9222` (user-data-dir `%LOCALAPPDATA%\Google\Chrome\User Data\CapitalChronicleBot`, canonical
route `https://x.com/i/lists/1843870469143048642`). ContentOps must always reuse it and must
never create, clone, reset, migrate, clean, replace, rename, delete, or silently fall back
from it. There is no alternate path, no fallback profile, no Default/personal Chrome fallback,
and no Edge fallback for ingestion. Missing/unusable binding fails closed
(`PROFILE_BINDING_MISSING` / `PORT_OWNER_UNPROVEN`) and never creates a replacement.
Provider-side session expiration may require operator reauthentication in that same profile
only; profile continuity is not provider authentication lifetime.

Unknown public writes remain:

`STOP RETRY → READ BACK → RECONCILE`

## 10. Router/runtime authority

Keep `CONTENTOPS_9ROUTER_ORDERED_MODEL_AUTHORITY_V2` and current role-specific routing/fallback budgets.

Do not redesign the provider pool because of transient availability.

The always-on supervisor must avoid continuous provider probes while idle.

## 10A. Continuous intelligence architecture (owner decision, 2026-08-10 realignment)

Jim's 2026-08-10 realignment supersedes the older "wait for an editorial window, then discover
whether fresh headlines exist" cadence/intake assumptions:

1. headline ingestion is continuous/cheap while the Daily App host is available (zero LLM
   calls; a housekeeping lane inside the canonical supervisor; no second scheduler);
2. editorial windows do not own headline ingestion; Run Now does not own ingestion;
3. every editorial decision (scheduled, material-event, or Run Now) reconstructs the complete
   rolling 24-hour unique headline universe — not only the latest capture delta;
4. previously published canonical article content is part of editorial novelty/update-chain
   context (published corpus derived from existing durable publication truth; no second store);
5. ContentOps uses the current Capital Chronicle data estate through a direct READ-ONLY
   catalog/query boundary (`capital_chronicle_data_catalog_v1`), preserving CC authority
   semantics: CC remains analytical/numeric authority where exact article contracts require it;
   database rows are never promoted to public truth merely because they exist (DQR, freshness,
   exact/proxy, permission, lineage, and limitations all preserved);
6. the initial desired publication target band is 5–8 high-quality articles per active day,
   served by ~8 configured core decision opportunities/day plus material-event wakeups; exact
   times are versioned configuration, never claimed universal truth;
7. follow-up publication requires material delta; story clusters are explicitly classified
   BREAKING_NEW_STORY / MATERIAL_FOLLOW_UP / DEEPEN_EXISTING_STORY / LOW_DELTA_REPEAT / HOLD;
8. breaking material news may wake the newsroom outside normal windows via the existing
   material-event seam (no second breaking-news engine);
9. 5–8 is a target band, NOT permission to fabricate filler or weaken factual/numeric
   authority; NO_PUBLICATION remains technically valid when nothing useful/grounded exists,
   but data starvation and tiny decision counts must not be the routine reason for low output;
10. Run Now uses the SAME canonical newsroom authority as scheduled/material-event cycles:
    "make an editorial decision now using the continuously maintained current intelligence
    universe" — no second newsroom, no special bypass pipeline, no weakened evidence/review
    authority. The bounded x-list capture survives only as an emergency freshness-sync fallback
    when continuous intake is stale.

One canonical headline store: `headline_ingestion/data/intake/headline_sidecars/`, one file per
day, fixed `step1_headline_sidecar_<YYYY>_<MM>_<DD>.jsonl` naming, append-only, deduplicated by
stable post/tweet identity, restart-safe. No timestamp-per-capture files, no parallel ALL_DATA
truth, no new legacy-format files; historical files remain read-only history.

## 11. Exact current routing

FDA-G genuine calendar-time live soak:

`TASK_CONTENTOPS_FINAL_DAILY_APP_GENUINE_CALENDAR_TIME_LIVE_SOAK_V1`

Status: `SOAK_ACTIVE_AWAITING_GENUINE_CALENDAR_TIME_EVIDENCE`. This is launch-session
success only, not FDA-G final acceptance. Do not create `v1.1.0` until the genuine 5–10
operating-day release evidence is complete and independently audited.

Completed operator-infrastructure task (owner priority override, 2026-08-10):

`TASK_CONTENTOPS_V1_ONE_CLICK_MORNING_LAUNCH_AND_RESUME_V1`

Delivered `Start_ContentOps_Daily_App.cmd` one-click launch/resume with the idempotent
start contract in section 4A. It did NOT declare FDA-G accepted and did NOT start Tier-2
implementation.

Next owner-approved builder lane (proceeds concurrently with the continuing FDA-G lane):

`TIER2-A LOCAL LONG-FORM + SHORT-FORM PROGRAMMABLE VERTICAL SLICE`

Tier-2 implementation stays isolated from the live V1 production runtime and has NO video
public-write authority under this reprioritization.