# Capital Chronicle ContentOps — Final Product North Star V3

Authority date: 2026-08-20
Status: `CURRENT_ROOT_PRODUCT_NORTH_STAR`

## Product role

Capital Chronicle/Core Analyzer is the intelligence and decision-product engine. ContentOps is Capital Chronicle's evidence-governed publishing, media-production, audience-acquisition, distribution-observation, and bounded-learning engine.

The final product is one coherent system:

`Capital Chronicle/Core Analyzer intelligence and decision authority -> explicit publication-safe handoff + contextual discovery -> ContentOps intelligence fusion -> V1 publishing + V2 video/media -> observation -> bounded ContentOps learning -> audience/business utility`.

V1 and V2 are isolated execution lanes inside the same product architecture, not philosophically separate products.

## Final user value

ContentOps should turn current public evidence plus the best relevant **publication-approved** Capital Chronicle intelligence into useful, trustworthy, high-quality public content with minimal operator burden, while preserving exact truth, rights, publication identity, recovery, and measurement.

The product wins when it:

- consistently identifies genuinely useful stories and abstains from filler;
- uses relevant Capital Chronicle/Core Analyzer public-authorized intelligence when it materially improves the story;
- uses non-public CC context only to improve investigation, never to create public authority;
- publishes strong text and media reliably under exact authority;
- measures what audiences actually consume and value;
- lowers the cost of acquiring, educating, converting, and retaining Capital Chronicle users;
- learns packaging and prioritization without corrupting analytical truth.

## Capital Chronicle / Core Analyzer boundary

Capital Chronicle/Core Analyzer owns proprietary analytical and numeric truth, including model calculations, scenarios, probabilities, forecasts, regimes, cross-asset conclusions, decision briefs, decision/watch/abstain outputs, paper expressions, realized-outcome comparisons, and analytical error attribution.

ContentOps may read approved upstream artifacts and may faithfully transform only material whose contract permits the intended ContentOps use. ContentOps must never invent missing CC numbers, infer public permission from an internally governed artifact, or promote a model assertion into CC authority.

Three authority classes are mandatory:

1. **Context/discovery only** — arbitrary database rows, historical/entity/event/document matches, Step-1/headline catalyst context, sidecar/lab output, candidate snapshots, and dataset pointers. Useful for investigation; zero factual/numeric publication authority by themselves.
2. **Core Analyzer governed internal authority** — point-in-time Analyzer/database handoffs, validated internal outputs, decision/forecast/scenario/paper records, candidate-only governed snapshots, and other internally authoritative artifacts that do not explicitly grant ContentOps public reporting. Internal governance is not public publication permission.
3. **ContentOps publication-authorized CC authority** — an exact story-scoped upstream publication artifact, currently exemplified by `CapitalChroniclePublicationEvidencePacketV1.json`, or a compatible successor, that explicitly grants the intended ContentOps consumer/use and preserves exact story binding, permissions, lineage, time semantics, source health/freshness, blockers, and `llm_numeric_authority=false`.

A validated Analyzer handoff or a `governed` label alone is never enough to publish proprietary numbers or analysis.

The current bridge implementation intentionally keeps a governed Analyzer closed-loop handoff publication-blocked unless a separate story-scoped publication contract grants public use. Conversely, a story-scoped publication packet may authorize a precise claim even while unrelated/global DQR remains blocked; ContentOps must preserve that scope rather than upgrading or downgrading it globally.

Goal: maximum useful **publication-authorized** intelligence plus bounded useful context, not maximum database scanning.

## V1 — Final Daily App / live newsroom

V1 is the canonical always-on newsroom and publication runtime.

It owns continuous intake, clustering/update chains, ranking/selection/abstention, latest-web grounded evidence, bounded CC context, explicit publication-authorized CC intelligence fusion, one strong editorial worker when warranted, factual/safety/reader-value validation, purposeful rights-safe article media, canonical Substack publication, eight V1 derivatives, exact destination identity, readback/reconciliation/recovery, supported observation, and bounded learning.

No-publication is valid. Zero images is valid. Unsupported metrics remain unavailable rather than fabricated.

V1 final acceptance requires current real canary proof plus unattended/cold-start evidence under the canonical runtime and exact public-object reconciliation.

## V2 — retention-native video/media factory

V2 converts only qualified governed stories into platform-native media when story value, evidence, rights-safe visual supply, and production economics justify it.

Canonical creative doctrine:

- `CONCRETE_FIRST_ABSTRACT_SECOND`;
- real/contextual media, primary documents, native maps/charts/data before abstract geometry;
- narration-linked beats and story-specific composition;
- rights-safe assets with professional visual fitness, not rights alone;
- Remotion as editing/render infrastructure, not a substitute for editorial material;
- professional audio;
- final-audio-bound transcript/SEO/package truth;
- deterministic hard-boundary QA plus actual-media owner review;
- bounded revision and recovery.

Generated media is illustrative, never documentary/factual authority. Real-person documentary imagery must be real and rights-cleared.

V2 must never mutate V1 runtime, store, scheduler, browser, or publication authority. Zero video production is valid. Current root authority grants zero video public-write authority.

## Shared CC chart/data interface

V1 and V2 should consume the same **publication-authorized CC chart/data projection** rather than building separate analytical databases or authority engines.

This interface is a lossless ContentOps projection of an upstream publication-safe packet, not a place to calculate missing Core Analyzer truth or upgrade private/internal outputs.

A public-use chart/data packet should preserve, where applicable:

- upstream packet and exact story/consumer binding;
- series/calculation identity;
- `known_at`, `as_of`, observation/source/revision time;
- observed vs forecast/scenario classification;
- units and transformations;
- exact lineage/provenance;
- DQR/quality/freshness/source health;
- display-safe values and explicit public permission;
- blockers/limitations;
- `llm_numeric_authority=false`.

If upstream has not granted public display/reporting for a value, V1/V2 may not recover that permission by rendering a chart. No model may synthesize a missing governed value.

## Evidence and source authority

Latest-web research must resolve current accessible primary sources where possible and strong professional secondary evidence where needed. A blocked embedded URL is not proof that the underlying event is unverifiable.

No paywall/login/anti-bot bypass. Every public claim must remain bound to accepted source records or exact publication-authorized CC authority.

Degraded, proxy-backed, candidate-only, stale, blocked, incompatible, and missing upstream states remain visible. ContentOps must not smooth them into a usable value or false zero.

## Media and publication

Publication quality is story-dependent. Zero images or zero video is valid when media does not improve the product.

For every public write, preserve destination/account identity, package identity, sufficient content identity, permission, readback, and reconciliation. `UNKNOWN_WRITE` means `STOP RETRY -> READ BACK -> RECONCILE`.

## Observation and learning

Observation includes supported readership, search, conversion, engagement, retention/completion, reliability, publication-authorized CC utilization, contextual CC utilization, source health, and cost.

Learning may affect ContentOps timing recommendations, priority, packaging, SEO, hooks, asset selection, and bounded creative policy. It may never change facts, evidence permissions, Capital Chronicle/Core Analyzer analysis, numeric authority, scenarios, probabilities, forecasts, regimes, private decision/paper records, realized-outcome attribution, rights, destination identity, or public-write scope.

Engagement may cause ContentOps to request a fresh upstream analysis or prioritize a story; it cannot rewrite upstream analytical truth.

## Business utility

ContentOps is successful when it improves the Capital Chronicle business funnel, not when it maximizes repository complexity, database scans, or content volume.

Long-run attribution should connect, where supportable:

`article/video -> signup -> returning user -> beta/product use -> paid -> retained`.

Engagement and conversion are product-learning inputs, not factual or analytical authority.

## Main execution framework

Canonical engineering execution is `CAPABILITY_ROUTED_HYBRID`, governed by `docs/automation/CONTENTOPS_CAPABILITY_ROUTED_HYBRID_EXECUTION_POLICY_V1.md`.

- `WEB_STATIC` handles repository-static reasoning, review, bounded edits, and GitHub operations when fresh repository bytes are sufficient evidence.
- `WEB_CI` adds safe deterministic GitHub Actions when machine validation can prove the required mechanics without secrets, public writes, or production mutation.
- `CODEX_EXECUTION` is used when correctness materially requires a real execution environment, interactive runtime/debug feedback, browser/runtime inspection, current network behavior not reproducible in CI, performance work, or rendered mechanics.
- `OWNER_GATED_EXTERNAL` remains mandatory for secrets/session boundaries, live/public writes, destructive canonical changes, provider/browser publication expansion, rights/legal release boundaries, material Core Analyzer numeric-authority changes, or equivalent irreversible external actions.
- Fresh owner-authorized `GPT-5.6 Sol / XHIGH` workers may own consequential editorial/creative judgment where current lane authority requires it.
- Approved 9Router models may perform bounded low-cost filtering/research/classification roles only where already authorized.

Use the cheapest execution lane that can produce evidence strong enough for the actual correctness claim. Execution routing never grants factual, numeric, permission, rights, credential, destination-identity, or public-write authority, and no alternate execution framework may bypass those boundaries.

## Hard safety rules

Never:

- expose secrets/session material;
- fabricate facts or CC/Core Analyzer numeric/analytical truth;
- widen permissions through model judgment or a ContentOps adapter;
- promote internal/candidate Analyzer material into public authority without an explicit publication-safe handoff;
- write to the wrong public account/object;
- mutate upstream Capital Chronicle data, models, decisions, paper records, or realized-outcome truth;
- destructively alter V1 production state from V2;
- force a publication/video quota;
- retry an ambiguous write before readback/reconciliation;
- retarget or rewrite protected `v1.0` history.

## Final definition of done

The final ContentOps product is accepted when:

1. relevant Capital Chronicle/Core Analyzer **publication-authorized** intelligence is measurably consumed when available and useful, while internal/context/candidate-only material remains correctly non-public;
2. bounded CC context is semantically activated when useful, with truthful zero-use reasons and no database-scan KPI gaming;
3. latest-web evidence acquisition reliably finds trustworthy current source records without unsafe bypasses;
4. V1 completes real canary, exact nine-surface publication/readback/reconciliation, and unattended/cold-start proof with safe abstention;
5. canonical UI exposes truthful current state, source/evidence health, upstream authority class, CC utilization, publication/recovery, and supported learning;
6. V2 repeatedly produces owner-accepted short and justified longform media from qualified stories, using publication-authorized numeric/chart material where required, with rights, audio, transcript/package truth, recovery, and bounded TCO;
7. any later V2 publication authority is exact, destination-bound, read back, and reconciled;
8. real audience/search/retention/business observations feed bounded ContentOps learning without changing Core Analyzer truth;
9. operators can understand current authority from the short repository spine without following superseded plans.
