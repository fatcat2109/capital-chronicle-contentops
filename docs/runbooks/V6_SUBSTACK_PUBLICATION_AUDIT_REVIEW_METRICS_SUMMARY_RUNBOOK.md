# V6 Substack Publication Audit Review & Manual Metrics Summary Runbook

Use the canonical V5 dashboard only: `ui/contentops_v5/`.

## Purpose

This lane reviews the operator-supplied publication URL audit and ingests deterministic manually-entered metrics. All metrics are local fixtures and manual entries for review/compliance purposes only.

## Required operator review steps

1. Confirm the source publication URL audit packet remains pending review.
2. Verify that manual metrics (views, opens, likes, comments, shares, restacks, subscribers delta) are input as manual stubs by the operator.
3. Confirm `metrics_source = operator_supplied_manual_entry`.
4. Confirm `metrics_network_verified = false`, `metrics_provider_api_used = false`, and `url_network_verified = false`.

## Prohibited actions

- Do not use Substack API to fetch metrics.
- Do not scrape or crawl the publication URL.
- Do not browse or fetch any live metric counts.
- Do not publish, dispatch, send, approve, or schedule.
- Do not read credentials, env values, browser session data, cookies, localStorage, tokens, provider keys, or webhook URLs.

## Provenance flags

- `url_network_verified = false`
- `substack_api_used = false`
- `provider_call_made = false`
- `network_call_made = false`
- `credential_read_made = false`
- `env_value_read_made = false`
- `browser_session_used = false`
- `live_publish_performed_by_contentops = false`
- `manual_publication_claim_operator_supplied = true`
- `manual_metrics_claim_operator_supplied = true`
- `enabled_publish_send_dispatch_approve_controls = false`

No live provider metrics APIs are called. The metrics summary is local fixture evidence only.
