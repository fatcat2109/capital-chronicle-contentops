# 0174U0 Ingestion Repo Recon Notes

## Repo baseline

- Path: `A:\Capital Chronicle\Headline Raw data local json\capital-chronicle-ingestion`
- Exists: yes
- Git repo: yes
- Branch: `main`
- HEAD: `6720a9be3932ce43b097e538e95ba0ccedb0f5d7`
- Mode: read-only context inspection

## Safety handling

- `.env.local` was observed but not read.
- No credential files were opened.
- No files were changed.
- Nothing was staged or committed.
- Ingestion artifacts treated as context, not ContentOps truth.

## Observed repo surfaces

- root strategy/deep research markdown docs;
- `docs/` with archive/project-sources/research/runbooks areas;
- `official_sources/`;
- `schemas/`;
- `tools/`;
- `data/`;
- source-health / DQR / ISM / DataNeedRouter / FieldAuthorityMap concepts in local tooling.

## Useful future ContentOps context inputs

Potential idea/context inputs:

- headline surfaces;
- official source catalogs;
- source family manifests;
- freshness manifests;
- coverage gap reports;
- DQR/data sufficiency summaries;
- forecast readiness summaries;
- candidate official-source surfaces;
- internal alpha readiness reports.

## Non-authority constraints

Do not treat as content authority unless future connector proves:

- source artifact identity;
- lineage;
- freshness;
- DQR/data sufficiency state;
- forecast readiness state;
- missing/degraded/proxy labels;
- content lane eligibility;
- citation refs;
- limitations.

## Proposed future connector

`Capital Chronicle Artifact / Headline Idea Connector`

Purpose:

- read-only local precheck;
- convert ingestion/headline/artifact context into ContentOps idea packet;
- never promote ingestion data to public claims without approved artifact intake;
- preserve blockers and limitations.

Required future fields:

- `source_repo_head`
- `source_artifact_path`
- `source_artifact_id`
- `lineage_ref`
- `freshness_state`
- `authority_level`
- `dqr_state`
- `forecast_readiness_state`
- `missing_degraded_proxy_labels`
- `content_lane_allowed`
- `idea_only_not_authority`

## Current blockers

- no ContentOps schema for ingestion context packet;
- no policy mapping ingestion readiness to content eligibility;
- no stable artifact-hash import boundary;
- no approved artifact intake contract for public-ready claims.
