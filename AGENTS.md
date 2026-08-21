# Capital Chronicle ContentOps — Root Repository Contract

Authority date: 2026-08-21
Status: `CURRENT_ROOT_AUTHORITY`
Repository: `fatcat2109/capital-chronicle-contentops`

## 1. Mandatory current read path

For every current implementation, audit, task framing, or owner decision, read in this order:

1. `AGENTS.md`
2. `docs/codegraph/INDEX.md`
3. `docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md`
4. `docs/automation/CONTENTOPS_CAPABILITY_ROUTED_HYBRID_EXECUTION_POLICY_V1.md`
5. `docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md`
6. `docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md`
7. `docs/codegraph/V1_CONTEXT.md` or `docs/codegraph/V2_CONTEXT.md`
8. current lane pointer
9. nearest scoped `AGENTS.md`
10. exact current implementation/tests/evidence.

Do not route from historical task evidence, stale handoffs, generated status snapshots, task branches, or chat SHAs.

## 2. Authority order

Product authority:

1. Jim's latest explicit instruction;
2. this root contract plus current root North Star/Master Plan;
3. current authority map and lane pointer;
4. older detailed plans/history.

Repository/evidence authority:

1. fresh remote refs/commits/diffs/exact bytes;
2. exact implementation, focused tests, accepted evidence, exact-head CI where applicable;
3. runtime/host/browser evidence for facts that only execution can prove;
4. historical docs/project sources/chat.

Newer owner direction wins.

## 3. Anti-drift fail-closed rule

The following claims are INVALID for current V1 unless they are supported by the current root North Star/Master Plan and exact runtime/host evidence where applicable:

- `no mandatory post count`;
- `publication minimum = 0` as successful whole-day behavior;
- `NO_PUBLICATION` means a whole production day may end healthy below the active output floor;
- `exactly four Codex tasks already exist` without actual Codex host inventory evidence;
- `the four Codex tasks are PAUSED/READY/ENABLED` when that state comes only from repo configuration;
- `FDA-G directly launches Codex` unless an actual supported execution bridge is proven;
- `material-event wake immediately invokes Codex` unless a supported bridge is proven.

If any current-looking subordinate document says one of the above, treat that wording as superseded and do not route from it.

Configured intent is not observed runtime/host truth.

## 4. Current V1 owner output contract

During BUILD/PROOF:

`minimum 4 QUALIFIED ZERO-PUBLIC-WRITE ARTICLES per newsroom production day`

Final V1 operating target:

`5–8 PUBLISHED ARTICLES per newsroom production day`

These are not filler quotas.

Candidate-level abstention is allowed. Whole-day deficit is not healthy success.

If the active production day ends below the build floor without an exact hard external blocker, classify:

`DEGRADED_DAILY_OUTPUT_DEFICIT`

Never weaken factual, evidence, numeric, permission, rights, or identity gates to satisfy the floor.

## 5. Production-day semantics

The intended routine windows are 17:00, 21:00, 23:00, and the following 01:00 Bangkok time. They belong to one deterministic newsroom production day; do not count by naive Bangkok calendar date.

Later routine opportunities must be able to recover earlier deficit through bounded additional candidate/article work. Do not create a fifth routine task merely to chase the floor.

## 6. Current V1 execution architecture

FDA-G is the continuous low-cost intake/state/runtime authority.

Native Codex execution is a separate heavy-editorial layer. Current repo code does not prove that FDA-G directly launches Codex Desktop.

`live_contentops/codex_desktop_newsroom_operator_v1.py` is continuity/routing support, not a scheduler or Desktop/model bridge.

Preferred routine architecture:

`FDA-G -> actual native Codex Automation -> HIGH coordinator -> fresh isolated XHIGH worker at qualified article boundary -> deterministic validation -> zero-write build output or authorized publication`

Do not claim native Codex Automations exist until host evidence proves them.

Do not add an API/access-token Codex bridge without explicit owner authorization.

## 7. ContentOps/Core Analyzer boundary

Capital Chronicle/Core Analyzer owns proprietary calculations, probabilities, scenarios, forecasts, regimes, decisions, paper records, realized-outcome attribution, and other analytical/numeric truth.

ContentOps owns discovery, grounded research, story selection, writing, SEO, media, distribution, readback/reconciliation, observation, growth, and bounded learning.

Three authority classes remain distinct:

1. context/discovery only;
2. governed internal Core Analyzer authority;
3. exact story-scoped publication-authorized CC authority.

Never promote class 1 or 2 into public authority by model judgment or adapter logic.

## 8. Editorial rules

V1 supports the current eight-mode spectrum:

- `BREAKING_BRIEF`
- `FOLLOW_UP_UPDATE`
- `STANDARD_NEWS_ANALYSIS`
- `CAPITAL_CHRONICLE_VIEW`
- `WHAT_THE_MARKET_IS_MISSING`
- `EVERGREEN_EXPLAINER`
- `DATA_OR_DOCUMENT_LENS`
- `WEEK_AHEAD_OR_WATCH`

Quiet day is not silent-day permission. Lower materiality/change mode before giving up. Filler remains forbidden.

One exact current official primary source may support a narrow attributed breaking fact when it directly proves that fact. Broader causal/numeric/market-impact/proprietary claims require stronger evidence/authority.

Strong evidence-backed house view and criticism are allowed. Qualitative ContentOps inference must remain distinguishable from fact and must not be presented as Core Analyzer output.

## 9. Publication/recovery boundaries

Substack is canonical. The eight V1 derivative destinations are Telegram, Discord, X, LinkedIn, Facebook Page, Instagram Business, Threads, and YouTube Community.

`UNKNOWN_WRITE = STOP RETRY -> READ BACK -> RECONCILE`

No execution lane, model, config file, or automation grants public-write authority by implication.

## 10. Execution framework

Use `CAPABILITY_ROUTED_HYBRID`:

- `WEB_STATIC`: repo-static reasoning/authority/docs/GitHub operations;
- `WEB_CI`: bounded deterministic implementation provable by CI;
- `CODEX_EXECUTION`: real runtime/Windows/browser/stateful/debug evidence;
- `OWNER_GATED_EXTERNAL`: secrets/session, live/public writes, destructive canonical mutation, credential/security expansion, material numeric-authority change, or equivalent irreversible action.

Use the cheapest lane that can produce evidence strong enough for the claim.

## 11. Current sequence

P0-G3 and the following V1 daily-yield lineage are accepted on the current task lineage:

1. autonomous newsroom daily-output/native Automation revalidation;
2. candidate continuation and quote repair;
3. current evidence-yield/reachability correction;
4. distinct-story frontier correction;
5. story/update-chain-scoped evidence reuse across mode downgrade.

The four-frontier proof still ends `DEGRADED_DAILY_OUTPUT_DEFICIT` at 0/4 articles and 0/32
derivative intents. The next exact product gate is bounded first-party locator/source-family and
query/publisher-resolution closure for the demonstrated residual story matrix, followed by the same
four-frontier zero-public-write proof. Do not resume P0-G4 canary, enable the four paused Automations,
or create a fifth Automation while the build floor remains unproven.

## 12. Change discipline

Prefer one heavy bounded product slice over ceremony.

Stage explicit paths only. Never `git add .` or `git add -A`. Never force-push. Never merge/push master without explicit owner authorization. Preserve unrelated work and protected history.

## 13. Hard stops

Stop on:

- secret/session/token/cookie/private-key exposure;
- fabricated facts or Core Analyzer truth;
- unauthorized/wrong-account public write;
- destructive production-store/upstream mutation;
- unresolved `UNKNOWN_WRITE`;
- irreconcilable ref conflict;
- unsupported automation mutation mechanism;
- inability to distinguish configured schedule intent from actual host automation state.

Do not stop for historical noise, stale docs, unrelated dirty files, absent CI, pre-existing failures, or reversible mechanics.

## 14. Visual/media acceptance

UI/video/audio PASS requires actual rendered artifact inspection. Tests and worker judgment prove mechanics, not final viewer-facing quality.
