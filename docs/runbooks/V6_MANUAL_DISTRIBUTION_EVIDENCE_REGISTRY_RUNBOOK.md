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
