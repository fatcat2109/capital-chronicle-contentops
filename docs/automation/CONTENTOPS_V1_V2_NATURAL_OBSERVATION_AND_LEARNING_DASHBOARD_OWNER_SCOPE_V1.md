# Capital Chronicle ContentOps — V1/V2 Natural Observation & Closed Learning Dashboard Owner Scope

Authority date: 2026-08-19

## Purpose

Expose all V1 and V2 lanes requiring natural passage-of-time observation, data freshness, real performance evidence, analysis, soak evidence, or closed-loop learning in **ONE canonical read-only ContentOps dashboard** (`ui/contentops_v5`).

Jim keeps this dashboard open and periodically captures clean desktop screenshots for independent longitudinal review with ChatGPT.

This surface is strictly read-only and grants **zero new execution, model, or public-write authority** to either lane.

---

## Architecture and Seams

1. **Canonical UI**: `ui/contentops_v5` is the single dashboard. No secondary backend, daemon, durable store, scheduler, or observation daemon exists.
2. **Read-Only Projection**: `live_contentops/contentops_observation_read_model_v1.py` is called by `daily_app_ui_read_model_v1.py` inside `build_daily_app_snapshot` (`snapshot["observation"]`).
3. **Execution Guardrails**:
   - Zero LLM / provider calls.
   - Zero browser / CDP actions.
   - Zero network fetches.
   - Zero credential / secret inspection.
   - Zero production-store mutations.
4. **Missing Data Policy**: Missing data remains explicit (`None`, `UNAVAILABLE`, `NOT_PRESENT`, `OPERATOR_SETUP_REQUIRED`). Missing data is **NEVER converted to zero or synthetic success**.
5. **V2 Discovery Boundary**: Bounded direct-child discovery under `A:\Capital Chronicle\Runtime\ContentOps` reading only strictly allowlisted safe files (`HANDOFF.json`, `contracts/render_dependency_manifest.json`, `contracts/asset_board.json`, `receipts/master_media.json`, `receipts/automated_visual_qa.json`, `receipts/manual_visual_review.json`, `receipts/recovery_proof.json`, `receipts/zero_public_write.json`). Never recursively ingests arbitrary files.

---

## The 19 Locked Observation Lanes

### Common Lane Contract

Every lane conforms to:
- `lane_contract_version`: `contentops.observation_lane.v1`
- `lane_id`: String identifier
- `group`: `'V1'` | `'V2'` | `'CROSS_LANE'`
- `state`: `'LIVE_OBSERVATION'` | `'SHADOW_READ_ONLY'` | `'WAITING_FOR_REAL_OBJECT'` | `'INSUFFICIENT_SAMPLE'` | `'OPERATOR_SETUP_REQUIRED'` | `'BLOCKED_OWNER_AUTHORITY'` | `'DEGRADED'` | `'UNAVAILABLE'`
- `data_source`: Description of backing source
- `authority_class`: Authority provenance class
- `last_observed_at_utc`: ISO UTC timestamp or null
- `next_due_at_utc`: ISO UTC timestamp or null
- `sample_count`: Integer sample count or null
- `coverage`: Scope description
- `confidence`: Confidence classification
- `freshness`: Freshness state
- `blocker`: Explicit blocker string or null
- `write_authority`: Public-write authority declaration
- `notes`: Operational guidance and constraints
- `metrics`: Key-value payload dictionary

---

### V1 Lanes (1 to 9)

| # | Lane ID | Authority Class | Write Authority | Description |
|---|---|---|---|---|
| 1 | `V1_HEADLINE_INTAKE_FRESHNESS` | `DURABLE_OPERATIONAL_STORE` | `READ_ONLY_INGESTION_SEAM` | Capture status, source-event age, rolling-24h unique count, cadence, CDP/auth state |
| 2 | `V1_CANDIDATE_FUNNEL` | `DURABLE_OPERATIONAL_STORE` | `ZERO_PUBLIC_WRITE_UNLESS_GOVERNED_GATE_PASS` | Candidate universe, prepared count, selected rank, abstain/HOLD reasons, novelty/material-delta |
| 3 | `V1_EVIDENCE_SOURCE_HEALTH` | `GOVERNED_SOURCE_RECORDS` | `READ_ONLY` | Primary source availability (EIA, CFTC, FRB, UST, BLS, SEC), CC catalog readiness, 9Router research ladder |
| 4 | `V1_PUBLICATION_SAFETY_RECOVERY` | `DURABLE_OPERATIONAL_STORE` | `DURABLE_PUBLICATION_COORDINATOR_ONLY` | Nine-surface readiness, dispatch/readback/reconciliation, UNKNOWN_WRITE (0), recovery obligations |
| 5 | `V1_REAL_PERFORMANCE_OBSERVATIONS` | `DURABLE_OPERATIONAL_STORE` | `READ_ONLY_OBSERVATION_COLLECTOR` | EARLY (15m), INTERMEDIATE (2h), DAILY (24h), LONG_TAIL (7d) windows; collected vs scheduled; qualified engagement formula v1 |
| 6 | `V1_PASSIVE_INTERACTION_QUALITY` | `DURABLE_OPERATIONAL_STORE` | `DEFERRED_ZERO_WRITE_AUTHORITY` | Qualified interaction count, 11 categories; zero raw public text; reply write authority is zero |
| 7 | `V1_CLOSED_LOOP_LEARNING` | `DURABLE_OPERATIONAL_STORE` | `READ_ONLY_POLICY_PREFERENCE` | Policy lineage; content, SEO, package, and timing sections; sample count, confidence; owner-locked schedule |
| 8 | `V1_SEARCH_DISCOVERY` | `OPERATOR_CONFIGURATION` | `READ_ONLY` | Search impressions/clicks; truthfully displayed as `OPERATOR_SETUP_REQUIRED / NO_SEARCH_SPECIFIC_SAMPLE` post-canary |
| 9 | `V1_COST_RUNTIME_YIELD` | `DURABLE_OPERATIONAL_STORE` | `READ_ONLY` | Provider token usage (prompt/completion), invocations, cycle durations, publish/abstain yield |

---

### V2 Lanes (10 to 17)

| # | Lane ID | Authority Class | Write Authority | Description |
|---|---|---|---|---|
| 10 | `V2_V1_TO_VIDEO_TRIGGER_SHADOW` | `SHADOW_DERIVED_EVALUATION` | `ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY` | V1 performance signals mapped to video candidacy; shadow evaluation only; 0 jobs auto-claimed |
| 11 | `V2_SOURCE_RIGHTS_ASSET_SUPPLY` | `BOUNDED_LOCAL_ARTIFACT` | `ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY` | Rights-safe asset discovery, ASSET_VISUAL_FIT gate, accepted/rejected counts, rights clearance |
| 12 | `V2_ASSET_DIVERSITY_AND_SCREEN_TIME` | `BOUNDED_LOCAL_ARTIFACT` | `ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY` | Exact-file reuse, visual family concentration, cumulative screen time, real/source share |
| 13 | `V2_PRODUCTION_TCO_RECOVERY_SOAK` | `BOUNDED_LOCAL_ARTIFACT` | `ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY` | Remotion render duration, scale, audio ledger, selective rerender proof, immutable audio resume |
| 14 | `V2_ACTUAL_MEDIA_QUALITY_OWNER_GATE` | `BOUNDED_LOCAL_ARTIFACT` | `ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY` | Automated visual QA diagnostics + Codex actual-media review + Jim/ChatGPT owner acceptance separation |
| 15 | `V2_PUBLICATION_READINESS` | `SHADOW_READ_ONLY_SAFETY_CONTRACT` | `ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY` | Six-surface shadow control plane (YouTube, TikTok, Instagram, FB Reels); public writes = 0; uploads = 0 |
| 16 | `V2_POST_PUBLISH_RETENTION_ATTRIBUTION` | `OWNER_AUTHORITY_GATE` | `ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY` | `BLOCKED_OWNER_AUTHORITY / ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY`; retention fields exist but are not fabricated |
| 17 | `V2_CLOSED_LOOP_VIDEO_LEARNING` | `BOUNDED_LEARNING_CONTRACT` | `ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY` | `WAITING_FOR_REAL_PUBLIC_OBJECT / INSUFFICIENT_SAMPLE`; future learning governs packaging only, never facts |

---

### Cross-Lane Lanes (18 & 19)

| # | Lane ID | Authority Class | Write Authority | Description |
|---|---|---|---|---|
| 18 | `CROSS_LANE_SOURCE_ACCESS_HEALTH` | `GOVERNED_SOURCE_RECORDS` | `READ_ONLY` | Official API, official HTML/PDF, operator-supplied primary, edge-blocked status; no WAF/VPN/proxy bypass |
| 19 | `CROSS_LANE_DATA_FRESHNESS_AND_AUTHORITY` | `UNIFIED_OBSERVATION_CONTRACT` | `READ_ONLY` | Concise freshness summary across all 19 lanes, latest intake/decision timestamps, authority hierarchy |

---

## Report & Screenshot Mode (`?view=observation&report=1`)

Report mode formats the observation control room for desktop screenshots (1440p / 1920):
- Suppresses navigation sidebar, top action bars, and interactive buttons.
- Features a top Audit Report Header with generated UTC timestamp and runtime git SHA.
- Displays a prominent Status Legend (LIVE, SHADOW, WAITING, INSUFFICIENT SAMPLE, OPERATOR SETUP REQUIRED, BLOCKED).
- Visually partitions V1 Canonical, V2 Shadow, and Cross-Lane Governance sections.
- Formats all 19 lanes into responsive 3-column cards with telemetry, metrics, and data provenance.
