# V6 Endpoint Allowlist Gate Contract

## Purpose

This gate consumes accepted official provider docs scope records and emits sanitized non-executable endpoint operation allowlist records for a later runtime authority gate.

## Sanitized Mapping

- `discord_developer_docs_webhook_execute` maps to `discord_execute_webhook_operation_required_later`.
- `telegram_bot_api_core_docs` maps to `telegram_send_message_operation_required_later`, `telegram_send_photo_operation_required_later`, `telegram_send_document_operation_required_later`, and `telegram_send_media_group_operation_required_later`.

These are operation labels only. They are not method/path tuples and are not executable.

## Eligibility

Provider runtime authority gate eligibility may become true only when the upstream official docs scope bundle is valid, every docs source maps to sanitized labels, every allowlist record is symbolic and non-executable, raw values are absent, required future gates are marked required, and unsafe flags remain false.

## Prohibited

No raw addresses, raw paths, method tuples, headers, request bodies, destination values, credential values, env values, payload bodies, public links, telemetry, provider configs, browser profiles, retry settings, budget settings, timer settings, SDK dependencies, adapters, queues, schedulers, live controls, or executable commands.
