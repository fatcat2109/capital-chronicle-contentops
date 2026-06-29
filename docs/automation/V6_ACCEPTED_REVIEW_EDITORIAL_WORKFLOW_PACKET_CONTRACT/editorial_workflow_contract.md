# Accepted Review Editorial Workflow Packet Contract

## Purpose

This creates one local editorial workflow packet from one accepted review-decision packet.

## Not Approval

This is not canonical article approval. It does not create approved canonical articles and does not mark content publication-ready.

## Eligibility

Input is eligible only when the review decision packet:

- Has the V6 human-review decision task label.
- Uses `decision: accept_for_editorial_workflow`.
- Has `accepted_for_editorial_workflow: true`.
- Has `rejected: false` and `deferred: false`.
- Has empty blockers.
- Keeps approval, publication, dispatch, variant, outbox, public URL, and metrics fields false or null.
- Has `review_only: true`.
- Has `kill_switch_active: true`.
- Has `runtime_truth: false`.
- Includes `source_candidate_id` and `source_candidate_sha256`.
- Contains no raw secret-like markers.

## Output

Output contains:

- Edit checklist.
- Factual-review queue.
- Source-grounding requirements.
- Required operator actions.
- Sanitized blockers and warnings.
- Source decision ID, source decision hash, and source candidate ID.

## Default Required Work

Edit checklist includes structure, clarity, source grounding, no-financial-advice review, and later publication approval requirements.

Factual-review queue requires claim verification against operator sources, missing source identification, unsupported number/date flagging, and market advice language flagging.

Source grounding requires an operator source pack, later citation evidence, and no generated citations.

## Hard Prohibitions

This contract does not enable:

- Canonical article approval.
- Publication readiness.
- Platform variants.
- Outbox entries.
- Dispatch records.
- Public URLs.
- Metrics.
- Comments.
- Citations.
- Fake runtime truth.

## Source Grounding

Source grounding is required before any future article approval. Generated or fake citations are prohibited.

## Runtime Boundary

Local-only and browserless. No env, provider, live API, webhook, network, scraping, dispatch, or credential validation behavior is allowed.