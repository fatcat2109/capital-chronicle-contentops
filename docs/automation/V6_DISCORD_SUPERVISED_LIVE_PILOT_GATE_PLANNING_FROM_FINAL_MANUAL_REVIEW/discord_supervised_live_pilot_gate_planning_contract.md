# V6 Discord Supervised Live Pilot Gate Planning - Technical Contract

## Purpose

The Discord supervised live pilot gate planning layer consumes a valid Discord final manual execution review packet and an operator Discord supervised live pilot planning declaration to emit a deterministic Discord supervised live pilot planning packet.

## Core Rules

1. **Create Local Discord Supervised Live Pilot Planning Packet Only**: This contract creates a local Discord supervised live pilot planning packet only.
2. **Not Live Dispatch Approval**: This contract does not authorize live dispatching or live sending.
3. **Not Publication Approval**: This contract does not authorize canonical article publication.
4. **No Env or .env Reading**: This contract does not read environment variables, process env, or repo env/.env files.
5. **No Key-Value Retrieval/Inspection**: This contract does not read, print, persist, hash, compare, validate, measure, prefix/suffix, or transform webhook values.
6. **No Platform API or Webhook Calls**: This contract does not call Substack, Discord, or any platform APIs or webhooks.
7. **No Request Artifacts**: This contract does not create endpoint, webhook, API, or browser request artifacts.
8. **No Persistence of Sensitive Secrets**: This contract does not persist or store full webhook URLs, webhook tokens, channel IDs, account/workspace/app IDs, HTTP bodies, or public URLs.
9. **Substack Fallback Restriction**: Substack remains routed to manual/browser fallback until official API publishing docs are verified in a future separate task.
10. **Banned States**:
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
    - `webhook_value_read_allowed` must remain `false`.
    - `discord_api_call_allowed` must remain `false`.
    - `webhook_send_test_allowed` must remain `false`.
    - `endpoint_url_value_allowed` must remain `false`.
    - `channel_identity_value_allowed` must remain `false`.
    - `http_headers_included` must remain `false`.
    - `http_body_included` must remain `false`.
    - `curl_command_included` must remain `false`.
    - `browser_instruction_included` must remain `false`.
    - `public_url_included` must remain `false`.
    - `metrics_included` must remain `false`.
    - `executable_request_artifact_creation_allowed` must remain `false`.
    - `live_dispatch_approval_granted` must remain `false`.
    - `publication_approval_granted` must remain `false`.
    - `planned_hidden_retry_allowed` must remain `false`.
    - `planned_max_request_count` must remain 1.
    - `planned_max_retries` must remain 0.
