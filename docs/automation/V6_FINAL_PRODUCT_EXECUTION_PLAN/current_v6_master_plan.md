# ContentOps V6 Current Master Plan

Completed architecture task: `TASK_CONTENTOPS_GENERIC_EVIDENCE_FRESHNESS_VISUAL_EDITORIAL_FABRIC_V2`.

Canonical supervised publishing uses Microsoft Edge profile `A:\Capital Chronicle\operator-browser-profiles\contentops-social-main`. Substack is canonical, and YouTube Community is the default YouTube article-distribution surface; video and Shorts are separate explicit non-default modes.

Authority date: 2026-07-11

Current classification: `PASS_GENERIC_EVIDENCE_FRESHNESS_VISUAL_EDITORIAL_FABRIC_V2`.

## Product State

The July 11 RC proved Substack-first transport, but operator audit classified it `MANUAL_AUDIT_PARTIAL_PASS_BLOCKED_FOR_TARGETED_REPAIR`. Transport evidence is historical proof, not generalized release acceptance. Public outputs are frozen and no `v1.0` tag exists.

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

Generic local mode: `--prepare-generic-fabric` with exactly one of `--capital-chronicle-root` or `--cc-evidence-packet`.

## Evidence Authority

Numeric truth comes from approved Capital Chronicle evidence claims, never LLM prose. Every claim carries observation, release, ingestion, and revision timestamps where available; source ID; authority; freshness; artifact reference; citation map; hash lineage; and public-claim permission.

ContentOps reads committed ingestion artifacts and does not create a second direct MT5 truth path. DQR can block publication. SourceHealth and InputStateManifest provide health and lineage but cannot override DQR.

The current ingestion repo does not yet emit `CapitalChronicleContentEvidencePacketV2` directly. ContentOps therefore provides a read-only resolver over documented current-state artifacts plus the producer handoff in `generic_evidence_freshness_visual_editorial_fabric_v2.md`.

## Freshness

Duplicate protection and freshness are separate gates. Straight news normally requires an event or source update inside 24 hours. Analysis requires a fresh material delta, updated source, or current market reaction. Explainers may be older but cannot use current/breaking framing without fresh evidence. Market-sensitive stories require a current or latest-session snapshot and current ingest under configurable cadence thresholds.

## Visual Fabric

Long-form articles normally require three useful visuals, at least two evidence dimensions or modalities, and no more than two assets from one underlying series. Physical, geopolitical, infrastructure, and supply-chain stories normally require a grounded contextual image, official photo, map, or equivalent non-price visual.

Google Image Search grounding is discovery-only. The provider contract uses the current Gemini Interactions API `google_search` tool with `web_search` and `image_search`. Search rank is neither provenance nor reuse permission. The containing source page, owner, date, context, rights, dimensions, relevance, recency, duplicate hash, and manipulation/branding flags must pass independently.

Chart metadata must state metric definition, units, frequency, sample window, transformation owner, calculation, annualization where relevant, and partial-period status. Average absolute moves cannot be labelled realized volatility. Incomplete annual periods must say `YTD`, `through <date>`, or `partial`.

## Editorial And Identity

Deterministic blockers remain authoritative over model review. The writer cannot self-certify. The independent final reviewer has no publication authority and malformed/unavailable output fails closed. Final rendered output is reviewed for source-calibrated headlines, internal vocabulary, awkward templates, causal certainty, unsupported cross-asset prose, mode/as-of consistency, advice language, and formulaic repetition.

Distribution identity is registry-driven. `The Macro Pigeon` is an approved Discord community persona. LinkedIn is founder-led personal distribution. A fresh LinkedIn story cannot edit a historical activity, and a Threads reply cannot dispatch without a parent ID.

## Current Evidence And Next Route

Generic rehearsal: `docs/automation/V6_GENERIC_EVIDENCE_FABRIC/generic_fabric_v2_real_rehearsal_20260711/`.

RC operator audit: `docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/contentops_v1_0_rc_20260711_1/operator_manual_audit_findings_v2.json`.

Next task is separately authorized targeted live repair and re-audit. It must restore historical LinkedIn integrity, create one fresh oil post, repair article/copy/chart/visual defects, resolve malformed Threads disposition, and reassess `v1.0`. It must not become a broad rerun.
