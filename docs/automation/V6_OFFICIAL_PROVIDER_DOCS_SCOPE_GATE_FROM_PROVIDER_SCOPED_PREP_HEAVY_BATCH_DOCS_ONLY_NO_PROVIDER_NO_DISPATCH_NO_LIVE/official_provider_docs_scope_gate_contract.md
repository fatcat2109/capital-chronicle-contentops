# V6 Official Provider Docs Scope Gate Contract

## Purpose

This gate consumes accepted provider-scope prep records plus sanitized official docs authority metadata. It emits non-executable official-docs-backed scope records for a later endpoint allowlist gate.

## Official Sources

- Discord official developer docs source ID: `discord_developer_docs_webhook_execute`.
- Telegram official Bot API source ID: `telegram_bot_api_core_docs`.

Official source labels are sanitized labels, not executable addresses. Unofficial sources are not accepted.

## Accepted Input

The upstream provider-scope prep bundle must use schema version 6.0.0, the exact task label, the ready-for-official-docs status, no unsafe flags, no blockers, human review required, endpoint docs scope eligibility true, and all provider runtime, dispatch, live, publication, and runtime authority eligibility false.

Provider-scope prep records must be symbolic, non-executable, use allowlisted provider family labels, include safe approved hash and preview metadata, symbolic destination and credential handle IDs, allowlisted key names, future gate requirements, and false unsafe flags.

## Output

Docs scope records include sanitized official source IDs, official docs family labels, page labels, symbolic provider family labels, symbolic dispatch method family labels, approved hash IDs, preview IDs, symbolic IDs, key names, and future gate requirements.

They must not include destination endpoint values, destination binding values, channel values, account values, credential values, request bodies, payload bodies, browser profiles, public links, telemetry, retry settings, budgets, timers, SDKs, adapters, or executable request artifacts.
