# CC Content Artifact Packet Contract

This folder documents the ContentOps-side boundary for `CC_CONTENT_ARTIFACT_PACKET`.

## Authority Boundary

- CDP ingestion remains the fresh catalyst/headline/event discovery layer.
- The Capital Chronicle local database remains in `A:\Capital Chronicle\Headline Raw data local json\capital-chronicle-ingestion` and is the numeric/source/context authority layer.
- ContentOps consumes exported packet artifacts in read-only mode; it does not move, copy, vendor, mirror, mutate, or replace the database.
- ContentOps performs content production, platform adaptation, approval, dispatch gating, and readback only after packet/gate approval.
- Capital Chronicle Analysis Alpha remains a later intelligence/value layer and is not implemented here.

## Current V0 Intake Rule

ContentOps V0 intake accepts blocked/candidate packets for internal/manual review only. A packet with `dqr_status=BLOCKED` or `candidate_only=true` cannot become public-publishable by intake alone.

The temporary Fed/FRED/NY Fed/Treasury fallback fixture remains `TEMPORARY_CONTENTOPS_FALLBACK_FIXTURE`. It is not a durable source-truth lane. Future numeric/source authority must come from exported CC artifact packets.

No additional macro source families should be added directly to ContentOps unless explicitly approved.
