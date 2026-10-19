# ContentOps Capital Chronicle Latest Report Bridge V1

Status: owner-approved additive implementation plan, 2026-10-18.
Authority: ContentOps North Star V3, Master Plan V3 and current authority map.
Upstream contract owner: Main App. This document does not own numeric truth, portfolio state,
Main capability status, publication authority or a new scheduler.

## 1. Product result

ContentOps should turn the latest useful Capital Chronicle report update into source-backed
content: a market explanation, thesis change, contagion mechanism, watch list or correction.
It must consume the real report, not rebuild its own market analyzer or write from a report ID.

The upstream four cases are foundation deep analysis of the full covered-asset catalog; daily
latest-data/headline analysis; daily holdings UNION active-recommendation review; and Jim manual
analysis. ContentOps consumes eligible public-safe results from any case. It does not create its
own daily portfolio job or access Jim's private positions.

## 2. Current implementation and remaining delta

ContentOps PR #82/#83 and #85/#86 are merged at the audited source epoch
139486acd59699d8bfb6a9725d9ef673a5c66bf2. Reuse:

- live_contentops/four_trigger_data_resolution_adapter_v1.py;
- live_contentops/three_trigger_editorial_flow_v1.py;
- live_contentops/browser_rendered_source_recovery_v1.py, including its installed-Neo
  launch-on-unavailable and MCP/read-only source-recovery components;
- existing sidecars, published memory, Simple Gemini input/writer/validator, durable publication
  coordinator and eight-derivative compiler.

Classification: PARTIAL_CAPABILITY_REUSE_COMPONENTS.
The three-trigger flow prepares Simple runner arguments but does not invoke the editorial
operation. The exact delta is a Main-report consumer, durable version/delivery tracking,
wire-format compatibility and substantive source-backed editorial input/draft. An injected
validation PASS, matching contract names or an eight-destination fixture is not that integration.

## 3. Main-owned wire contract

Use CapitalChronicleLatestAnalysisReportEnvelopeV1 exported by the Main producer, without
forking its schema or hash algorithm. Required fields include:

- schema/version, event ID, report ID/version, parent/supersedes reference;
- case, asset IDs/affected symbols, horizon blocks and generated/as-of/known-at clocks;
- run/coverage-snapshot identity and report hash;
- public-safe claim IDs/hashes with exact supporting evidence;
- report/event/CC-analysis/scenario layer, exact/proxy/basis risk and freshness/PIT/public rights;
- public-safe hold/invalidation conditions, limitations and content eligibility;
- change kind: NEW_REPORT, NEW_EVENT, THESIS_DELTA, INVALIDATION, CORRECTION,
  FRESHNESS_REPAIR or NO_MATERIAL_CHANGE; changed claim IDs and materiality rationale.

Main owns the canonical JSON serialization and hash definition. Contract tests consume an exact
producer artifact plus its schema revision/commit/hash. Adapters translate explicitly; equal
contract labels with different field names or self-hashes do not establish interoperability.

The envelope is an input read projection under existing stores and queue conventions. It is not
a second report/portfolio/status ledger.

## 4. Editorial consumer path

    latest eligible Main report envelope
      -> exact schema/hash/source and scope validation
      -> report-version/claim dedupe + correction/invalidation lineage
      -> editorial materiality, audience, angle and mode
      -> bounded ContentOps DataNeedPlan
      -> existing database/report/sidecar semantic reads
      -> BrowserOS Neo research for named unresolved needs
      -> existing Simple input and writer/validator
      -> substantive draft with evidence/claim-to-section mapping
      -> existing Substack/eight-derivative publication owner when separately authorized

Public content should explain what changed, why it matters, causal links, uncertainties and what
to watch. Do not mechanically copy an internal report or turn CC's scenario into an observed fact.
The writer preserves hold/stop-holding conditions as conditional analytical context.

Routine V1 remains SIMPLE_GEMINI_RUNTIME with its existing four windows, ceilings and exactly
eight derivatives. The Codex Desktop research bridge can add admitted context upstream; it does
not replace Simple's writer or add routine Codex model calls to the accepted V1 critical path.
V2 remains isolated. No new scheduler, publisher or store.

## 5. Latest versions, missing data and corrections

Persist the last-seen report version and delivery outcome using existing owner persistence.
Deduplicate by event/report/version/hash/claim hash; resume delivery idempotently after a crash
or quota interruption. An older report cannot displace a newer one. Reject an equal version with
different bytes and record an explicit conflict.

For NEW_REPORT/NEW_EVENT/THESIS_DELTA, assess editorial relevance and select an appropriate mode.
For INVALIDATION/CORRECTION, link the prior report and any affected draft/publication through the
existing update workflow; never erase or silently edit historical evidence. For
NO_MATERIAL_CHANGE, record consumed/no-op without a new model/publication intent.
Do not manufacture content merely because a report arrived.

Query retained, admitted database/report/sidecar evidence first. For a named absent, stale or
contradictory field, reuse the shared DataNeedPlan and read-only BrowserOS Neo MCP recovery.
Reuse the existing installed-Neo startup if needed, then verify actual MCP tool readiness.
Capture source/final URL, times, visible data/hash, rights, epistemic class and why fallback was
needed. A tool observation does not itself establish factual truth or redistribution rights.

Preserve optional missing claims locally instead of blocking every article; essential truth,
identity, rights or attribution gaps remain research-only/abstained with an exact reason.
Do not expose credentials, cookies/tokens, private balances/positions/account IDs or restricted
source bodies. Do not infer public rights from internal analysis permission.

## 6. Content modes and serving

Use the existing modes: follow-up/correction, standard analysis, CC view, what-the-market-is-
missing, data/document lens or week-ahead/watch. The editor chooses the angle; it cannot upgrade
certainty. Direct quotes and quantitative claims retain exact source provenance.

Return research-only, draft-only, validated-for-existing-owner or DATA_BLOCKED state. A draft or
validated envelope is not publication proof. Preserve the four epistemic layers and
source/claim IDs through article sections and eight derivative intents. Public updates remain
under the current owner and UNKNOWN_WRITE stop/readback/reconcile behavior.

## 7. Finite acceptance

The next Builder goal must deliver:

1. an importer of exact Main bytes/schema, not just matching schema-name constants;
2. real existing report/read-model consumption and durable idempotent version tracking;
3. one substantive draft/editorial-input path using existing writer ownership, with report ->
   claim -> evidence -> section -> derivative-intent mapping;
4. correction/invalidation, out-of-order, duplicate, no-change, stale, rights and privacy controls;
5. DB-first named-gap research with the real Neo adapter, distinguishing injected tests from
   tool-backed observations;
6. counts for report events consumed, no-ops, drafts, missing claims and blocked results;
7. focused validation and one durable handoff with exact source/artifact identity and next action.

Main and ContentOps can build concurrently with disjoint files. Main alone owns the wire
contract. The ContentOps Builder may prepare its adapter against the documented contract,
then bind the exact Main producer revision for compatibility proof. Missing producer evidence
is a durable handoff condition, not permission to declare a synthetic consumer integrated.

No repeated full historical audit, provider cycle, public canary or runtime activation is required
to implement and verify this consumer. Actual schedule/publication proof remains separate.

Implementation and exact-source evidence are tracked in
[the Goal 17 checkpoint](CONTENTOPS_CAPITAL_CHRONICLE_LATEST_REPORT_BRIDGE_V1_20261018.md).
That checkpoint distinguishes tested consumer controls, actual rejected/admitted Main bytes,
editorial inputs, writer execution and remote integration; it is not a second status owner.
