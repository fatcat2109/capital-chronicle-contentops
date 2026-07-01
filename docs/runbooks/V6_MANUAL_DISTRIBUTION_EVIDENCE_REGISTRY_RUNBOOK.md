# V6 Manual Distribution Evidence Registry Runbook

## Scope

Consolidates accepted Substack, LinkedIn, and X manual publication evidence loops into a local read-only registry.

## Operator rules

- Use canonical V5 UI only: `ui/contentops_v5/`.
- Treat all lanes as fixture/manual/operator-supplied.
- Do not call platform APIs.
- Do not read env values, credentials, browser sessions, cookies, localStorage, or sessionStorage.
- Do not fetch, scrape, or verify public URLs.
- Do not post, reply, DM, like, repost, quote-post, schedule, approve, send, publish, or dispatch.

## Evidence

- Registry packet: `docs/automation/V6_MANUAL_DISTRIBUTION_EVIDENCE_REGISTRY/manual_distribution_evidence_registry_packet.json`
- Audit note: `docs/automation/V6_MANUAL_DISTRIBUTION_EVIDENCE_REGISTRY/manual_distribution_registry_audit_note.md`
- Builder: `live_contentops/manual_distribution_evidence_registry_v6.py`

## Source-path audit

- Audit packet: `docs/automation/V6_MANUAL_DISTRIBUTION_EVIDENCE_REGISTRY/manual_distribution_registry_source_path_audit_packet.json`
- Builder: `live_contentops/manual_distribution_evidence_registry_source_path_audit_v6.py`
- Semantics: deterministic local file verification only.
- Confirms each registry source packet path exists under `docs/automation/`.
- Confirms each bound packet ID and hash matches the expected source packet field.
- Does not fetch URLs, verify public URLs, call providers, read env or credentials, inspect browser sessions, or perform live platform actions.

## Audit index/readiness summary

- Audit index packet: `docs/automation/V6_MANUAL_DISTRIBUTION_EVIDENCE_REGISTRY/manual_distribution_registry_audit_index_packet.json`
- Builder: `live_contentops/manual_distribution_registry_audit_index_v6.py`
- Use only for local operator review readiness.
- It binds the registry packet and source-path audit packet into one deterministic local readiness summary.
- It is not live dispatch readiness and does not enable approve/send/publish/dispatch/schedule controls.
- It does not prove public URL reachability, platform authentication readiness, or platform-side state.
