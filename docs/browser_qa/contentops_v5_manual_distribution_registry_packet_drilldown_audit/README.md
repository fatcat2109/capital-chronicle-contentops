# ContentOps V5 Manual Distribution Registry Packet Drilldown Audit QA

## Canonical target

- Canonical UI target: `ui/contentops_v5/`
- Local QA URL: `http://127.0.0.1:5173/`
- No V4 or standalone dashboard was targeted.

## Packet drilldown visibility

Packet drilldown is visible in:

- Manual Export / Pilot Verification
- Approval Queue
- Evidence Vault

## Registry evidence visible

- Platforms visible: Substack, LinkedIn, X
- Five packet roles visible per platform: export, approval, handoff, url, metrics
- Packet IDs visible on wrapped monospace lines
- Short packet hashes visible
- Registry hash visible
- Controls blocked/enabled=false

## Safety invariants

No platform API, network/public URL verification, env read, credential read,
browser-session read, cookie/localStorage/sessionStorage inspection, or live action occurred.
No post, reply, DM, like, repost, quote-post, schedule, approve, send, publish, or dispatch occurred.

## Screenshots

- `manual_export_registry_packet_drilldown.png`
- `approval_queue_registry_packet_drilldown.png`
- `evidence_vault_registry_packet_drilldown.png`
