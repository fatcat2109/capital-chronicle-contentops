# V6 Variant Preview/Hash Approval to Discord Outbox Runbook

This runbook covers the deterministic dry-run bridge from the AI research
canonical article packet into platform-native variants, exact preview hashes,
pending operator approvals, and the Discord dry-run outbox spine.

## Scope

- Local deterministic dry-run only.
- No AI provider calls.
- No Discord provider calls.
- No network or browser use.
- No env reads or credential hydration.
- No executable request artifacts.
- No live sends.

## Inputs

The bridge accepts an AI article packet shaped like
`sample_article_packet()` from
`live_contentops.ai_research_canonical_article_engine_v6`.

Required downstream field:

- `discord_summary_seed`
  - `title`
  - `canonical_url`
  - `summary`
  - `key_points`
  - `call_to_action`
  - `source_article_id`
  - `content_hash`
  - `created_at`

## Command

```powershell
python -m live_contentops.variant_preview_hash_approval_to_discord_outbox_v6 --output fixtures/v6/variant_preview_hash_approval_to_discord_outbox_sample_v6.json
```

To bridge a previously emitted article packet:

```powershell
python -m live_contentops.variant_preview_hash_approval_to_discord_outbox_v6 --input path/to/article_packet.json --output path/to/variant_bridge_packet.json
```

## Outputs

- `variants`: Discord, Telegram operator checkpoint, and Substack preview records.
- `preview_hash_records`: Exact deterministic preview hashes.
- `approval_records`: Pending operator approval records with live dispatch disabled.
- `discord_dry_run_outbox_packet`: Existing Discord outbox spine packet built from the Discord summary seed.
- `redacted_audit_packet`: Safety flags proving dry-run/no-secret/no-live behavior.

## Operator Gate

The output is not a live authorization. The next milestone should provide an
operator approval queue and evidence vault UI that lets Jim/operator review the
exact preview text and hash before any future scoped live lane.
