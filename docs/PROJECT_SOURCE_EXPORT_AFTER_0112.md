# Project Source Export - After TASK_CONTENTOPS_0112

LOCAL ONLY | SAFE CONTEXT EXPORT GUIDANCE | NO SECRETS

## Purpose
This doc explains how to refresh the ChatGPT Project Sources for Capital
Chronicle ContentOps after accepted task 0112. It supersedes AFTER_0108 and all
older export guidance.

## Accepted baseline
- Repo: A:\Capital Chronicle\tools\cc-live-contentops
- Branch: master
- Accepted HEAD: 35adc4a
- Accepted chain: 0095-0112 (local-only, deterministic, manual/supervised).

## What to upload
Upload only the curated AFTER_0112 bundle. Its contents are listed in
`UPLOAD_BUNDLE_MANIFEST_AFTER_0112.md`. Every file is a markdown context doc or
a JSON schema. None contain secrets, tokens, channel IDs, raw logs, vendor data,
provider outputs, or public-postable content.

External bundle location (untracked, outside the repo working tree):
`A:\Capital Chronicle\tools\project_sources_bundle_AFTER_0112`

## What NOT to upload
- `.env`, `.env.*`, credentials, secrets, tokens, channel IDs
- raw Telegram/API responses, raw logs with secrets
- vendor/raw data, caches, `__pycache__/`, `.pytest_cache/`, `.git/`
- binary artifacts, large generated files
- stale `project_sources_bundle_AFTER_0074/`
- stale `project_sources_bundle_AFTER_0108/`
- any file with a real token or private channel ID

## Stale bundle cleanup
Before uploading the AFTER_0112 set, remove the older Project Sources bundles
from the ChatGPT project to prevent stale-authority drift:
- AFTER_0073, AFTER_0074
- AFTER_0099, AFTER_0101
- AFTER_0108

The AFTER_0112 bundle is the single current source of truth.

## Hard boundaries carried forward
Local-only; manual/supervised only; no network/provider/LLM/web/search; no
platform API/posting/scheduling/replies/DMs/scraping; no automatic metrics
ingestion; no credential/`.env` reads; no fake alpha output; no public-postable
default; no auto-approval; no financial advice/signal language; no sibling/core
repo mutation. Telegram lane remains STOPPED.

## Next recommended product task
TASK_CONTENTOPS_0114_PRE_ALPHA_WORKFLOW_AUDIT_AND_SIMPLIFICATION_MAP_V0
