# ContentOps V6 Current Master Plan

Completed live closure task: `TASK_CONTENTOPS_DATABASE_PUBLICATION_AUTHORITY_AND_CONTENTOPS_FULL_LIVE_CLOSURE_V1`.

Canonical supervised publishing uses Microsoft Edge profile `A:\Capital Chronicle\operator-browser-profiles\contentops-social-main`. Substack is canonical, and YouTube Community is the default YouTube article-distribution surface; video and Shorts are separate explicit non-default modes.

Authority date: 2026-07-14

Current classification: `PASS_CONTENTOPS_V1_0_OPERATOR_ACCEPTED`.

## Product State

The July 11 RC remains historical transport evidence. The July 14 generic Treasury canary is the accepted v1.0 release: it consumed exact story-scoped database publication authority, passed Substack plus eight derivative readback and machine audit, received the exact final auction-logic repair, preserved all derivative identities, and passed operator acceptance. Public outputs remain frozen and annotated tag `v1.0` marks the completing release commit.

## Product North Star

```text
headline/CDP intake
-> capability-driven story assignment
-> CapitalChronicleContentEvidencePacketV2
-> claim permissions, DQR, source health, and lineage
-> article-mode freshness and market-state decision
-> provider-neutral visual discovery and rights review
-> visual diversity and quantitative-method gate
-> assignment editor
-> evidence planner
-> reporter/writer using approved claim IDs only
-> quantitative editor
-> visual editor
-> copy editor
-> platform editor
-> independent adversarial final reviewer
-> canonical Substack publication/readback only after explicit live authorization
-> native derivatives, strict readback, evidence, and operator audit
```

Canonical entrypoint: `live_contentops.eight_platform_substack_first_pipeline_v1`.

Generic local mode: `--prepare-generic-fabric`. Generic live release preparation: `--prepare-generic-live-release`. Both accept `--capital-chronicle-root` or `--cc-evidence-packet`; live dispatch remains in this same canonical runner and requires the locked release artifacts plus explicit operator authorization.

## Evidence Authority

Numeric truth comes from approved Capital Chronicle evidence claims, never LLM prose. Every claim carries observation, release, ingestion, and revision timestamps where available; source ID; authority; freshness; artifact reference; citation map; hash lineage; and public-claim permission.

ContentOps reads committed ingestion artifacts and does not create a second direct MT5 truth path. DQR can block publication. SourceHealth and InputStateManifest provide health and lineage but cannot override DQR.

The current ingestion repo does not yet emit `CapitalChronicleContentEvidencePacketV2` directly. ContentOps first consumes and hash-verifies the accepted analyzer handoff and its point-in-time DuckDB in read-only mode, translating governed rows and consumer permissions into the packet. Legacy current-state artifacts are fallback compatibility only when the governed handoff is absent.

## Freshness

Duplicate protection and freshness are separate gates. Straight news normally requires an event or source update inside 24 hours. Analysis requires a fresh material delta, updated source, or current market reaction. Explainers may be older but cannot use current/breaking framing without fresh evidence. Market-sensitive stories require a current or latest-session snapshot and current ingest under configurable cadence thresholds.

## Visual Fabric

Long-form articles normally require three useful visuals, at least two evidence dimensions or modalities, and no more than two assets from one underlying series. Physical, geopolitical, infrastructure, and supply-chain stories normally require a grounded contextual image, official photo, map, or equivalent non-price visual.

Google Image Search grounding is discovery-only. The provider contract uses the current Gemini Interactions API `google_search` tool with `web_search` and `image_search`. Search rank is neither provenance nor reuse permission. The containing source page, owner, date, context, rights, dimensions, relevance, recency, duplicate hash, and manipulation/branding flags must pass independently.

Chart metadata must state metric definition, units, frequency, sample window, transformation owner, calculation, annualization where relevant, and partial-period status. Average absolute moves cannot be labelled realized volatility. Incomplete annual periods must say `YTD`, `through <date>`, or `partial`.

## Editorial And Identity

Deterministic blockers remain authoritative over model review. The writer cannot self-certify. The independent final reviewer has no publication authority and malformed/unavailable output fails closed. Final rendered output is reviewed for source-calibrated headlines, internal vocabulary, awkward templates, causal certainty, unsupported cross-asset prose, mode/as-of consistency, advice language, and formulaic repetition.

Distribution identity is registry-driven. `The Macro Pigeon` is an approved Discord community persona. LinkedIn is founder-led personal distribution. A fresh LinkedIn story cannot edit a historical activity, and a Threads reply cannot dispatch without a parent ID.

## Current Evidence And Release Gate

Generic rehearsal: `docs/automation/V6_GENERIC_EVIDENCE_FABRIC/generic_fabric_v2_real_rehearsal_20260711/`.

RC operator audit: `docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/contentops_v1_0_rc_20260711_1/operator_manual_audit_findings_v2.json`.

Final-closure evidence: `docs/automation/FINAL_AUTOMATION_PIPELINE_CLOSURE_V1/contentops_final_closure_20260711_1/`.

Bounded repairs restored historical LinkedIn content, corrected Facebook copy, and deleted the two authorized malformed Threads posts. A valid Threads reply had to be recreated after duplicate-text UI ambiguity, leaving an operator-visible order caveat. The oil editorial repair passes locally but is unpublished.

Current generic live evidence: `docs/automation/DATABASE_PUBLICATION_AUTHORITY_AND_CONTENTOPS_FULL_LIVE_CLOSURE_V1/contentops_database_publication_live_20260714_1/`.

Database packet `cc-publication-73ff151c3d3094741b6c` grants story-scoped `contentops_publication`, `reporting_allowed=true`, and `PASS_PUBLICATION_AUTHORIZED` while preserving global `dqr=BLOCKED`. The canonical runner published `Treasury Yield Curve Edges Wider as 30-Year Reaches 5.10%`, then produced eight native derivatives with strict readback. Bounded updates repaired the Substack caption fragment, tightened the RC, and corrected the final auction-confirmation logic without derivative or video writes. Strict readback preserved all three ordered visuals, captions, sources, and numeric claims. Machine QA and the final release verifier pass.

ContentOps v1.0 is operator-accepted. The next route is `TASK_CONTENTOPS_NEWSROOM_CANDIDATE_ASSIGNMENT_AND_FIVE_WINDOW_SCHEDULING_V1`; newsroom implementation was not started during release closure.
