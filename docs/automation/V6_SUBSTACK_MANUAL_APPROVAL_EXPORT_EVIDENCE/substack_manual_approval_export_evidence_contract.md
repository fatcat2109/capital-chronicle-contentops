# V6 Substack Manual Approval Export Evidence Contract

This contract defines the deterministic, fixture-only approval/export evidence packet for the canonical V5 dashboard.

## Input

- Committed `sample_substack_manual_export_article_studio_packet.json` only.
- Required bindings: `export_packet_id`, `source_article_packet_id`, `source_canonical_hash`, `manual_copy_payload`, and `exact_payload_hash`.

## Output

- `approval_export_evidence_packet_id`
- `approval_export_evidence_hash`
- `source_export_packet_id`
- `exact_payload_hash`
- `operator_review_status=pending_review`
- `approval_status=pending`
- `manual_export_status=ready_for_manual_copy`
- evidence cards for article source, export packet, approval checkpoint, manual copy checklist, and blocked live publish state

## Safety invariant

- Manual copy only.
- Substack API not used.
- Live publish disabled.
- No approve/send/publish/dispatch control is enabled.
- No provider call, network call, credential read, env value read, or browser session use.
- Fixture evidence only: `sample_scope=sample_fixture_only`.
