# 0174U3 Substack Newsletter Manual Export Contract

- task_label: `TASK_CONTENTOPS_0174U3_SUBSTACK_NEWSLETTER_AND_MANUAL_EXPORT_CONTRACT_V0`
- model_version: `0174U3_SUBSTACK_NEWSLETTER_MANUAL_EXPORT_CONTRACT_V1`
- source_baseline_commit: `70c81b97164a30a3266e475af43321c6e799890c`
- registry_checksum: `de586ffd70646e253c2ef7689705311058009e8d3f5ce66c1dadd83f568c52ff`
- preview_contract_checksum: `f3a756428517a6cb9b1d9c542743b540afb98b72ef0885f420ecbd47c6886780`
- substack_manual_export_contract_checksum: `2f7bd68c21d2cd5d30e63278ce7d84447def62575c82822efb3345ac9302a314`
- next_heavy_batch_recommendation: `TASK_CONTENTOPS_0174U4_CONTENT_IDEA_PACKET_AND_LOCAL_INTENT_PARSER_CONTRACT_V0`

## Scope

Manual markdown export only. No Substack API, browser session, cookie, credential hydration, env read, network, scheduler, scraping, DM, or live dispatch behavior.

## Models

- `SubstackNewsletterIssue`: source preview, issue content, citations, limitations, SEO, export hash, no-live defaults.
- `SubstackManualExportPackage`: markdown body/hash, SEO fields, manual checklist, symbolic destination/credential refs.
- `SubstackExportValidationResult`: source hash match, payload allow-list, markdown/citation/limitation/SEO/checklist/no-live gates.

## Hash rules

Export hash includes source hash, title/subtitle/hook/thesis, body sections, citations, limitations, SEO, cross-platform refs, destination binding, and manual export status.
Markdown hash is SHA-256 over rendered markdown.

## Manual publish checklist

- copy markdown manually
- verify title/subtitle
- verify citations
- verify limitations
- verify no-advice/no-signal disclaimer
- verify destination publication manually
- record final URL manually after publish
- record timestamp/operator ref manually
- record metrics manually later

## Safety flags forced false

- `substack_api_called=false`
- `browser_session_used=false`
- `session_cookie_used=false`
- `platform_api_called=false`
- `provider_api_called=false`
- `credential_hydrated=false`
- `env_read=false`
- `network_performed=false`
- `scheduler_enabled=false`
- `autonomous_posting_allowed=false`
- `scraping_performed=false`
- `dm_or_reply_automation_allowed=false`
- `live_dispatch_enabled=false`
- `dispatch_ready=false`
- `public_postable=false`

## Scope confirmations

- No UI/dashboard work.
- No ingestion repo mutation.
- No live/API/credential/provider/session/browser/scheduler/scraping/DM behavior.
- Artifact writer is locked to `docs/automation/0174U3`.
