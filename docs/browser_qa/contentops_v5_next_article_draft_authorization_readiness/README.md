# ContentOps V5 Next Article Draft Authorization and Readiness UI QA

This folder contains the committed local browser QA visual screenshots for `TASK_CONTENTOPS_V6_NEXT_ARTICLE_SOURCE_PACK_TO_DRAFT_AUTHORIZATION_AND_LOCAL_DRAFT_READINESS_HEAVY_BATCH_V0`.

## Committed Screenshots
* [manual_export_draft_authorization_readiness_surface.png](manual_export_draft_authorization_readiness_surface.png) - Shows the card rendered in the V5 Manual Export view.
* [approval_queue_draft_authorization_readiness_surface.png](approval_queue_draft_authorization_readiness_surface.png) - Shows the card integrated into the V5 Approval & Dispatch view.
* [evidence_vault_draft_authorization_readiness_surface.png](evidence_vault_draft_authorization_readiness_surface.png) - Shows the dark mode card inside the Evidence Vault view.

## Verification Details
* **Canonical UI Target**: Only `ui/contentops_v5/` was targeted and verified. No legacy V4 pages or standalone custom pages are used.
* **Local QA URL**: Verified locally at `http://127.0.0.1:5173/`.
* **Readiness Scope**:
  * The cards state `ready_for_local_canonical_draft_workflow=true` indicating that local canonical drafting is authorized.
  * They state `ready_for_llm_drafting=false` and `ready_for_provider_drafting=false` proving no automated drafting is supported.
  * They explicitly declare `canonical_draft_created=false` and `article_body_created=false` to prove that no draft body copy was constructed during this authorization batch.
  * They state `ready_for_auto_publish=false` and `ready_for_dispatch=false` showing all live publishing is locked.
  * Screenshots are visual QA evidence of display visibility and alignment, not live-readiness evidence.
* **Verification Constraints**: No LLM/provider/API/network/env/credential/browser-session/public URL/live action occurred.
