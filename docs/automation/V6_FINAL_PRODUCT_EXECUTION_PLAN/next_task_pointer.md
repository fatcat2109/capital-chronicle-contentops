# V6 Next Task Pointer

Latest accepted release task: `TASK_CONTENTOPS_V1_0_FINAL_AUCTION_LOGIC_REPAIR_ACCEPTANCE_AND_TAG_V1`.

Completed task: `TASK_CONTENTOPS_FAST_SHIP_CAPABILITY_POLICY_GENERICITY_AND_READINESS_RECEIPT_REPAIR_V1`

Classification: `PASS_CAPABILITY_POLICY_GENERICITY_AND_READINESS_RECEIPT_REPAIR_V1_AWAITING_CHATGPT_AUDIT`.

Evidence: `live_contentops/source_capability_registry_v2.py`, `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/source_evidence_capability_registry_v2.json`, `ui/contentops_v5/src/data/operatorPackageReviewAdapter.ts`, `ui/contentops_v5/src/views/CanonicalPackageReviewConsole.tsx`, focused Python/Vitest/build/browser validation, and `docs/automation/CONTENTOPS_FAST_SHIP_CAPABILITY_POLICY_GENERICITY_AND_READINESS_RECEIPT_REPAIR_V1/final_manifest.json`.

The capability resolver now requires an explicit registry mode or a valid caller-provided mode, and fails closed on absence or mismatch. Platform visual policy matches exact platform, surface, and variant mode so only current text-only variants receive the zero-visual waiver. Readiness and visual hashes bind effective capability policy, and the 18 deterministic receipt records preserve unchanged canonical evidence, `HOLD`, and false publication/dispatch authority.

## Required Next Action

`INDEPENDENT_CHATGPT_AUDIT_CAPABILITY_POLICY_GENERICITY_AND_READINESS_RECEIPT_REPAIR_V1`

Independently verify explicit/caller-preserved mode resolution and fail-closed mismatches, independent sensitivity/snapshot policy, exact platform/surface/variant visual matching, policy-bound hash mutation, the committed receipt and deterministic replay, responsive state separation, status consistency, and no-execution invariants. Do not approve, publish, dispatch, read credentials, access provider platforms, mutate upstream, run scheduler actions, or perform public writes.
