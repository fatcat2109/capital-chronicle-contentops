# Institutional Browser QA Evidence Handoff To Project Sources Refresh (After 0170)

Task label context: TASK_CONTENTOPS_0170_BROWSER_QA_EVIDENCE_PACKET_AND_GLOBAL_HEADER_METADATA_RECONCILIATION_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master

This doc defines the handoff state for a future Project Sources refresh. 0170 does
NOT refresh Project Sources. A refresh may only occur after an explicit operator/
ChatGPT audit of 0170 evidence.

## What 0170 Produced

- Persisted 0169 browser QA evidence (PASS_WITH_MINOR_EVIDENCE_GAP) into the repo.
- Recorded all minor evidence gaps.
- Recorded the screenshot-review stale-metadata caveat.
- Reconciled the institutional shell global header so stale `15b87ff` and the
  Telegram official-docs gate are no longer presented as current global state.
- Labeled older per-screen HEADs as historical provenance.
- Updated Evidence Vault wording and README to reflect current evidence baseline.

## What 0170 Did NOT Do

- No browser opened, no Antigravity, no screenshots, no export/image/PDF files.
- No env reads, no API/network calls, no live posting/scheduling/scraping.
- No evidence mutation controls.
- No Project Sources refresh bundle created.

## Handoff State

- Current accepted code baseline reflected in shell header: `444ef2c`
  (note: the repo HEAD at 0170 build time was a harmless documentation-only
  descendant; the institutional shell presents `444ef2c` as the accepted code
  baseline per task authority).
- Latest browser QA evidence: `0169 PASS_WITH_MINOR_EVIDENCE_GAP`.
- Next allowed action:
  AWAIT OPERATOR/CHATGPT_AUDIT_OF_0170_EVIDENCE_BEFORE_PROJECT_SOURCES_REFRESH_OR_ANY_NEXT_TASK

## Future Project Sources Refresh Preconditions

A future refresh task must:
- Start only after explicit operator/ChatGPT audit of 0170 evidence.
- Carry the reconciled accepted baseline and 0169/0170 lineage.
- Preserve secret-safety: no tokens, chat IDs, env paths, request URLs, or raw
  platform responses.
- Not enable any live/API/posting/scheduling/export behavior.
