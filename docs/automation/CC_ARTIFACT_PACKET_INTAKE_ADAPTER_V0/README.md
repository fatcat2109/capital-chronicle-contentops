# CC Artifact Packet Intake Adapter V0

Task: `TASK_CONTENTOPS_CC_ARTIFACT_PACKET_INTAKE_TO_REHEARSAL_BRIDGE_HEAVY_BATCH_V0`

Classification: `PASS_WITH_CAVEAT_CONTENTOPS_CC_PACKET_INTAKE_V0`

## What This Adds

- Copies the pinned V0 schema from main repo commit `74ccf071ac8558d54e6a3c9d7d2a05ecbf42a2f2`.
- Copies the pinned sample packet from that same commit.
- Validates V0 packet schema and ContentOps guard rules.
- Renders an internal/manual-review draft preserving DQR, candidate-only, source-quality, limitation, and forbidden-use caveats.
- Builds component hashes and an approval hash.
- Emits a local-only rehearsal intent.
- Provides a dry-run CLI.

## What This Does Not Add

- No public dispatch.
- No platform API/provider call.
- No browser/CDP/readback path.
- No scheduler, retry, or outbox execution.
- No credential, env, token, cookie, localStorage, sessionStorage, webhook, or provider-key reads.
- No macro source fetcher/parser.
- No numeric truth verification inside ContentOps.
- No mutation of the Capital Chronicle main repo/database.
- No new ContentOps macro source-brain or source-family fixture.

## Caveat

The existing approval/draft/outbox modules are lane-specific and not stable enough for direct V0 packet queue integration in this task. This adapter therefore writes deterministic local dry-run artifacts only:

- `internal_draft_v0.json`
- `intake_dry_run_summary_v0.json`
- `approval_hash_v0.txt`
- `rehearsal_intent_v0.json`

Public candidate work requires a separate explicit operator-GO task and future packet/gate approval.
