# V6 Substack Manual Export Article Studio Contract

This contract defines the local-only Substack manual export packet for the canonical V5 dashboard.

## Input

- Committed canonical article packet only.
- Required fields: `packet_id`, `canonical_article_draft`, `seo_packet`, and `research_grounding_packet`.

## Output

- `export_packet_id`
- `source_article_packet_id`
- `source_canonical_hash`
- `manual_copy_payload`
- `exact_payload_hash`
- `approval_status=pending`
- `live_publish_allowed=false`
- `sample_scope=sample_fixture_only`

## Safety invariant

- Manual copy only.
- Substack API not used.
- Live publish disabled.
- No runtime proof.
- No provider call.
- No credential/env/browser session read.
- No raw secrets, env lines, webhook URLs, response bodies, value lengths, prefixes, suffixes, hashes, digests, or browser session data.

## Failure posture

The builder fails closed if required packet fields are missing or if unsafe publication claims, invented citations/URLs, financial-advice terms, or credential/session-like material are detected.
