# V6 AI Research Canonical Article Engine Contract

This contract defines the safety, schema, and processing rules for the V6 AI research + canonical article production engine.

## Scope

- Input: operator idea topic, target audience, editorial angle, source context documents, risk disclaimers, and publish targets.
- Output: structured grounded research grounding packet, canonical Substack-ready article draft, editorial/SEO packets, Discord summary seed, and telegram operator seed.
- Processing Modes:
  - `dry_run_fixture` (Default): Local deterministic generation without network/provider calls.
  - `live_provider_call`: Optional live completion via OpenAI or Anthropic endpoints only if explicit flag and key presence are true.

## Safety Boundaries

- Strict case-insensitive scanner checks for financial advice keywords (`buy`, `sell`, `hold`, `target`, `entry`, `exit`, etc.) on both inputs and final output fields.
- Fabricated citations, fake market numbers, or claims of live public publication are blocked.
- Timeout is finite and no hidden retry is used.
- Provider secrets, key lengths, prefixes, suffixes, or raw environment variables are never serialized or logged.
- The Discord summary seed must be compatible with the Discord dry-run outbox spine payload model.

## Next Task Selection

Recommended next task:

`TASK_CONTENTOPS_V6_VARIANT_PREVIEW_HASH_APPROVAL_TO_DISCORD_OUTBOX_HEAVY_BATCH_V0`
