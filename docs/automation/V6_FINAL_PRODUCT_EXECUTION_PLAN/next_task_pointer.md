# V6 Next Task Pointer

Current task just completed: `TASK_CONTENTOPS_CC_ARTIFACT_PACKET_INTAKE_TO_REHEARSAL_BRIDGE_HEAVY_BATCH_V0`.

Result:
- Classification: `PASS_WITH_CAVEAT_CONTENTOPS_CC_PACKET_INTAKE_V0`.
- ContentOps now has a V0 intake adapter for pinned Capital Chronicle `CC_CONTENT_ARTIFACT_PACKET` exports.
- The adapter validates schema and ContentOps guard rules, renders an internal/manual-review draft, computes component and approval hashes, writes deterministic local dry-run artifacts, and emits a local rehearsal intent.
- Approval queue integration is caveated: existing queue/outbox modules are lane-specific or side-effectful for this V0 packet shape, so this task writes deterministic local artifacts only.
- No public dispatch, platform API call, browser/CDP action, network/source fetch, scheduler, retry, credential/session read, or main-repo/database mutation occurred.

Evidence:
- Intake evidence: `docs/automation/CC_ARTIFACT_PACKET_INTAKE_ADAPTER_V0/intake_adapter_evidence_v0.json`.
- Internal draft: `docs/automation/CC_ARTIFACT_PACKET_INTAKE_ADAPTER_V0/internal_draft_v0.json`.
- Dry-run summary: `docs/automation/CC_ARTIFACT_PACKET_INTAKE_ADAPTER_V0/intake_dry_run_summary_v0.json`.
- Approval hash: `docs/automation/CC_ARTIFACT_PACKET_INTAKE_ADAPTER_V0/approval_hash_v0.txt`.
- Local rehearsal intent: `docs/automation/CC_ARTIFACT_PACKET_INTAKE_ADAPTER_V0/rehearsal_intent_v0.json`.
- ContentOps schema copy: `schemas/cc_content_artifact_packet_v0.schema.json`.
- Pinned sample fixture: `tests/fixtures/cc_artifact_packet_v0/sample_internal_draft_packet_v0.json`.
- Contract README: `docs/automation/V6_CC_ARTIFACT_PACKET_CONTRACT/README.md`.

Architecture boundary:
- CDP ingestion = fresh catalyst/headline/event discovery.
- Capital Chronicle local database/exporter = numeric/source/context authority.
- The local database remains in `A:\Capital Chronicle\Headline Raw data local json\capital-chronicle-ingestion`.
- ContentOps = content production, platform adaptation, approval, dispatch gating, and readback.
- Capital Chronicle Analysis Alpha = later core value/intelligence layer, not part of this task.
- ContentOps must not become a second macro database, source fetcher/parser, numeric truth authority, or source-brain.
- The Fed/FRED/NY Fed/Treasury rates path remains `TEMPORARY_CONTENTOPS_FALLBACK_FIXTURE` only.

Pinned authority:
- Main repo: `fatcat2109/Headline-Raw-data-json`.
- Handoff commit: `74ccf071ac8558d54e6a3c9d7d2a05ecbf42a2f2`.
- Sample packet `main_repo_head`: `69301f0fceee24ba1fa7e6c181ad190b3a4e306a` preserved as packet metadata.
- Schema SHA-256: `428e56667f313553501bda9d8be07d565c9f74eea00ab7a03082d442d0d16478`.
- Sample SHA-256: `5bea02bd6bfe68c75634c4f824af156cf5f2f19251e92c5298d76388d0e8f16f`.

Recommended next task:
```text
TASK_CONTENTOPS_CC_ARTIFACT_PACKET_OPERATOR_DECISION_AND_CONTROLLED_PUBLIC_CANDIDATE_REHEARSAL_V1
```

Purpose: Decide how ContentOps should treat DQR-blocked/candidate CC packets after intake. If the operator supplies a future approved packet/schema with public eligibility, run only a controlled no-public-write rehearsal first. Any public/live candidate still requires a separate explicit operator-GO task and current platform/readback gates.

Out of scope for the next task unless explicitly approved:
- Public dispatch.
- Platform API calls.
- Browser/CDP readback.
- Macro source fetching/parsing.
- Main repo/database writes.
- Analysis Alpha.
- New ContentOps source-family fixtures.
