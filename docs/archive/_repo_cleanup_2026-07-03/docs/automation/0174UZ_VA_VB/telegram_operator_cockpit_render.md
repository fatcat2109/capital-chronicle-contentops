# 0174UZ/VA/VB Telegram Operator Cockpit HTML Render + Manual Gate Handoff

Task: `TASK_CONTENTOPS_0174UZ_VA_VB_TELEGRAM_OPERATOR_COCKPIT_HTML_RENDER_AND_MANUAL_GATE_HANDOFF_BATCH_V0`

Model: `TELEGRAM_OPERATOR_COCKPIT_HTML_RENDER_0174UZ_VA_VB` version `0174UZ_VA_VB_TELEGRAM_OPERATOR_COCKPIT_HTML_RENDER_V1`

## Purpose

First operator cockpit rendering layer for the supervised Telegram loop. Renders the accepted 0174UW read model into a calm, institutional, evidence-grade STATIC HTML surface plus a redacted manual-gate handoff contract. No live dispatch, no network, no API, no env or credential read, and no external frontend dependency.

## Cockpit sections

- `CommandHero`
- `OperationalTruthRail`
- `ReplayGuardPanel`
- `NextSendPrecheckPanel`
- `EvidenceChainPanel`
- `ForbiddenAffordancePanel`
- `ManualGateHandoffPanel`

## Source / render references

- Source baseline commit: `125e286ecc5f80a269ecee8011de5c889566d8af`
- Source read model checksum: `3268b95cae278bf761b7bcf6a1b904a960898fdd1491d32a8db1b987db409948`
- Source cockpit packet checksum: `da2a7e4debbbded17dc3be6e2fb67c38f463fe442d8c016f75aa170cf473c9fe`
- Render model checksum: `47e73ad8ee22c826876af15ee3e61e88723f60630239a827925efb09a8ed7425`
- HTML checksum: `8fbb5a89eb49a4002d2c0362713cea085e327315ca949d4f7088507458e0e89f`
- Handoff contract checksum: `2eb3637c3e40bdd1cf88ad024778d4f386ff48b68632bf55a65e04ceb7e0d978`
- Render packet checksum: `1db05dc04159648ca5f871db3f6893bf61c5207a332f5554def90f01c0d80a87`

## State summary

- Reconciliation: `ledger_reconciliation_ok_count_incremented`
- Current ledger count: `2`
- Default next allowed action: `blocked_invalid_candidate`
- Handoff status: `manual_gate_handoff_waiting_for_candidate`

## Manual gate handoff CTAs (inert)

- `Prepare manual gate packet`
- `Open evidence packet`
- `Copy precheck summary`

## Safety proofs

- Network performed: `False`
- Telegram API called: `False`
- Credential read: `False`
- sendMessage executed: `False`
- Static render: `True`
- No external dependency: `True`
- Live ready: `False`
- Valid for live execution: `False`

## Next recommended task

`TASK_CONTENTOPS_0174VC_VD_VE_TELEGRAM_MANUAL_GATE_PACKET_BUILDER_AND_OPERATOR_APPROVAL_CAPTURE_BATCH_V0`
