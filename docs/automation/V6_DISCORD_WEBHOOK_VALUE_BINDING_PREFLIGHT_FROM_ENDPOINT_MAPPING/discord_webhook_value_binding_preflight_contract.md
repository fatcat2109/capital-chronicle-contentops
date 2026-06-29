# V6 Discord Webhook Value Binding Preflight Gate - Technical Contract

## Purpose

The Discord webhook value binding preflight gate consumes a valid Discord endpoint mapping preflight packet and an operator Discord webhook value-binding declaration to emit a deterministic Discord webhook value binding preflight packet.

## Core Rules

1. **Create Local Discord Webhook Value Binding Preflight Packet Only**: This contract creates a local Discord webhook value binding preflight packet only.
2. **Not Live Dispatch Approval**: This contract does not authorize live dispatching.
3. **Not Publication Approval**: This contract does not authorize canonical article publication.
4. **No Env or .env Reading**: This contract does not read environment variables, process env, or repo env/.env files, except for exact process-environment key membership checks when explicitly requested.
5. **No Key-Value Retrieval/Inspection**: This contract does not read, print, persist, hash, compare, validate, measure, prefix/suffix, or transform webhook values.
6. **Strict Process Env membership Check**: Environment checks, if enabled, are exact-key membership only and do not use `.get()`, `__getitem__`, `.items()`, `.values()`, `.keys()`, `dict(os.environ)`, or arbitrary env iteration.
7. **No Platform API or Webhook Calls**: This contract does not call Substack, Discord, or any platform APIs or webhooks.
8. **No Request Artifacts**: This contract does not create endpoint, webhook, API, or browser request artifacts.
9. **No Persistence of Sensitive Secrets**: This contract does not persist or store full webhook URLs, webhook tokens, channel IDs, account/workspace/app IDs, HTTP bodies, or public URLs.
10. **Substack Fallback Restriction**: Substack remains routed to manual/browser fallback until official API publishing docs are verified in a future separate task.
11. **Banned States**:
    - `live_send_request_created` must remain `false`.
    - `approval_for_live_dispatch` must remain `false`.
    - `dispatch_allowed` must remain `false`.
    - `approval_for_publication` must remain `false`.
    - `platform_variant_generation_allowed` must remain `false`.
    - `outbox_creation_allowed` must remain `false`.
    - `publication_ready` must remain `false`.
    - `approved_canonical_article_available` must remain `false`.
    - `generated_citations_allowed` must remain `false`.
    - `citations_verified` must remain `false`.
    - `public_url` must remain `null`.
    - `public_metrics` must remain `null`.
    - `review_only` must remain `true`.
    - `human_review_required` must remain `true`.
    - `kill_switch_active` must remain `true`.
    - `runtime_truth` must remain `false`.
    - `webhook_value_observed` must remain `false`.
    - `webhook_value_persisted` must remain `false`.
    - `webhook_value_hash_observed` must remain `false`.
    - `webhook_value_length_observed` must remain `false`.
    - `webhook_value_prefix_suffix_observed` must remain `false`.
    - `webhook_url_shape_validated` must remain `false`.
    - `discord_api_validated` must remain `false`.
    - `webhook_send_test_performed` must remain `false`.
