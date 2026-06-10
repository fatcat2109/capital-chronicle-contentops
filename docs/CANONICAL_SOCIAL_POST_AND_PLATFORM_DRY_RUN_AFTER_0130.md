
# Canonical Social Post and Platform Dry-Run Contract (After 0130)

## Purpose
This document specifies the contract mapping a validated `LLM_ASSISTED_DRAFT_REVIEW_PACKET` (from 0129) into deterministic, offline Platform Dry-Run Payload objects.

## What This Is NOT
- This does **NOT** post, publish, or schedule live content.
- This does **NOT** connect to actual Platform APIs (X, LinkedIn, etc.).
- This does **NOT** read credentials, `.env` variables, or scrape targets.
- This does **NOT** constitute an approval ledger; live execution requires 0131 (Approval Ledger & Kill Switch).

## Rendering
The platform dry-run renderer validates safety constraints (no signal language, no execution words, no alpha emulation) and maps the canonical payload to platform-specific placeholder limits.

Platform definitions in the registry currently use:
- `constraint_source="local_placeholder_until_official_docs_verification"`
- `official_docs_verified=false`

Until an official docs verification run occurs in future milestones, length constraints and media boundaries remain strictly illustrative and block safely if media is entirely missing where required (e.g., Instagram).

## Required Safety Flags
- `public_postable=false`
- `publish_ready=false`
- `live_posting_enabled=false`
- `platform_api_payload_generated=false`
- `manual_review_required=true`
