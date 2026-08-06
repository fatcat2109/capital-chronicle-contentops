# Current Product Direction Overlay

Authority date: 2026-08-06

Current product-direction classification:

`CONTENTOPS_NEWSROOM_AND_CONTENT_FACTORY_SCOPE_OWNER_APPROVED`

Jim approved the final ContentOps product plan on 2026-08-06. This overlay is current product-direction authority; no further owner approval is required for the routed next task.

Remote base reconciled onto:

`6b6f8718532a4c3f077b09e14f3ca9a4083d4734`

The plan branch `agent/contentops-final-product-scope-closeout-v1` at `7bacc52b0bdc76d571c5270d912bc5d2bfbe2c7e` was authored over the earlier base `c87e338f25922f4d03454ba199139353ca7198ff`. Wave 02 entered `master` after that base, so current accepted Wave 02 repo facts are preserved and the plan's pre-Wave-02 candidate language is superseded.

## Current owner direction

Capital Chronicle main project owns economic and market analysis, microeconomic/macro/global-macro reports, scenarios, model calculations, Bayesian cases and updates, forecasts, numeric truth, and analytical error attribution.

ContentOps owns news/headline/breaking/business-news intelligence, editorial selection, content diversification, writing, SEO, images, deterministic charts from authorized inputs, platform packages, publishing, readback, reconciliation, and content-performance learning. It consumes governed Capital Chronicle analysis outputs and must not independently originate analytical authority.

## Current product priority

Wave 02 — the durable operational store and canonical state machine — is complete and accepted as the minimum durable prerequisite:

`COMPLETE_ACCEPTED_AND_MERGED_AS_MINIMUM_DURABLE_PREREQUISITE`

Close the final product through a small number of heavy bounded product work packages:

1. dual-lane CORE V0 in `SHADOW_ONLY`;
2. content diversity, SEO, image, and chart closure;
3. repeated shadow soak and recovery;
4. exact authorized live cohort;
5. final product acceptance and new release identity.

Do not resume the older horizontal hardening sequence unless an item directly blocks this product path. The old automatic Wave 03 approval-envelope/transactional-outbox sequence is no longer the next-task authority; it may be revisited only when the CORE V0 vertical slice or a launch gate directly requires it.

## Current detailed authority

- `docs/automation/CONTENTOPS_FULL_AUTOMATION_FINAL_PRODUCT_INSTITUTIONAL_NORTH_STAR_V1/FINAL_PRODUCT_SCOPE_OVERLAY_V2.md`
- `docs/automation/CONTENTOPS_FINAL_PRODUCT_SCOPE_CLOSEOUT_AND_LAUNCH_MASTER_PLAN_V1.md`
- `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md`

## Current next task

`TASK_CONTENTOPS_CORE_V0_REPEATED_SHADOW_SOAK_AND_RECOVERY_V1`

Mode:

`SHADOW_ONLY`

Routed only after Work Package D passes independent audit. Work Package C is
`COMPLETE_ACCEPTED_AND_MERGED_WITH_CAVEAT`; Work Package D is
`DELIVERED_AWAITING_INDEPENDENT_AUDIT_AND_MERGE`.

The final build sequence is:

```text
dual-lane CORE V0 in SHADOW_ONLY   [COMPLETE — ACCEPTED AND MERGED WITH CAVEAT]
→ diversity, SEO, image, and chart closure   [DELIVERED — AWAITING INDEPENDENT AUDIT]
→ repeated shadow soak and recovery   [CURRENT — AFTER WORK PACKAGE D AUDIT]
→ exact authorized live cohort
→ final acceptance and new release identity
```

This task performs a full product cycle with zero public writes. It grants no credential, provider, browser/CDP, network-intake, scheduler/outbox execution, dispatch, publication, or public-write authority.
