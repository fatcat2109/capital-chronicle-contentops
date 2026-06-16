# 0174TJ/TK/TL Editorial + Preview Set + Supervised Dry-Run Contract

Task: `TASK_CONTENTOPS_0174TJ_TK_TL_EDITORIAL_PREVIEW_AND_SUPERVISED_DRY_RUN_CONTRACT_BATCH_V0`

Model: `EDITORIAL_PREVIEW_SUPERVISED_DRY_RUN_CONTRACT_0174TJ_TK_TL` version `0174TJ_TK_TL_EDITORIAL_PREVIEW_DRY_RUN_V2_R1`

Baseline commit: `9e06c325f64e3dd1d4aa95c44c8e5224b061be17`

## Role

This batch is LOCAL and deterministic. It performs NO live platform API call, NO Telegram send, NO LLM/provider call, NO network, NO env/credential read, NO credential hydration, NO scheduler, and NO auto retry. Provider rendering remains UNVERIFIED.

## 0174TJ Editorial agent

Consumes a genuine `remote_review_approved_not_dispatched` result and the exact 0174EE outbox entry. Fails closed on forbidden material or financial-advice framing. Allowed content lanes:

  * `grounded_explainer`
  * `grounded_macro_context`
  * `grounded_news_context`
  * `market_structure_education`
  * `neutral_market_recap`

## 0174TK Platform preview SET

Builds one preview artifact per required surface; a single record can NEVER satisfy the dry run. Required surfaces:

  * `telegram_channel_preview` -> `telegram`
  * `x_post_preview` -> `x`
  * `linkedin_post_preview` -> `linkedin`
  * `manual_publish_packet_preview` -> `manual_publish_packet`

## 0174TL Supervised dry run

Re-verifies the full review -> outbox -> editorial -> preview-set hierarchy and every deep binding. Even when complete, the outcome is `supervised_dry_run_complete_not_dispatched` -- never dispatch.

## Next required gate

kill switch contract, rate/spend policy contract, and a one-request/no-auto-retry supervised dispatch gate with redacted immutable audit, all still local until an explicit operator-owned live gate; credential hydration and live platform/Telegram dispatch remain separate future operator-owned gates and are NOT enabled here

Exact next task: `TASK_CONTENTOPS_0174TM_TN_TO_KILL_SWITCH_RATE_POLICY_AND_ONE_REQUEST_SUPERVISED_DISPATCH_GATE_BATCH_V0`

Packet checksum: `3e0b5158ea56714e4cca4ac6fe01fe4adb87d8d1ec9bdef343287da11aa3c567`
