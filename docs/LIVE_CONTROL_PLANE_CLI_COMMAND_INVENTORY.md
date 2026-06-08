# LIVE CONTROL PLANE CLI COMMAND INVENTORY

This document records the exact boundaries, inputs, outputs, and live-safety posture of the `cc-live-contentops` sidecar commands. All commands are invoked via `python -m live_contentops.cli <command>`.

| Command Name | Purpose | Posture | Live Send Enabled | Live Keys Checked |
|---|---|---|---|---|
| `status` | Checks basic status of the sidecar architecture. | Local-Only | False | False |
| `contracts-summary` | Lists all structured data classes available for handoffs. | Local-Only | False | False |
| `validate-sample-contracts` | Tests JSON schema enforcement. | Local-Only | False | False |
| `policy-summary` | Summarizes policy rules mapping constraints. | Local-Only | False | False |
| `evaluate-sample-policy` | Evaluates mocked violations against policy rules. | Local-Only | False | False |
| `approval-queue-summary` | Explains operator-queue logic boundaries. | Local-Only | False | False |
| `build-sample-approval-queue` | Constructs standard approval queue artifacts. | Local-Only | False | False |
| `audit-log-summary` | Defines audit bounds and data redaction requirements. | Local-Only | False | False |
| `provider-gateway-status` | Defines the LLM simulation boundary limits. | Local-Only | False | False |
| `provider-dry-run` | Executes a simulation of what the provider LLM would reply with. | Local-Only | False | False |
| `validate-provider-dry-run-fixtures` | Validates standard output responses natively. | Local-Only | False | False |
| `telegram-adapter-status` | Defines Telegram API restrictions and states. | Local-Only | False | False |
| `telegram-dry-run` | Local construction of Telegram message payload formats. | Local-Only | False | False |
| `validate-telegram-dry-run-fixtures` | Ensures dry-run matches exact schema standards. | Local-Only | False | False |
| `telegram-staging-contract` | Outputs baseline Telegram interface mapping payload. | Local-Only | False | False |
| `x-adapter-status` | Defines X/Twitter API restrictions and states. | Local-Only | False | False |
| `x-dry-run` | Local thread/character-count mapping validation. | Local-Only | False | False |
| `validate-x-dry-run-fixtures` | Ensures x dry-run matches schema standards. | Local-Only | False | False |
| `x-staging-contract` | Outputs baseline X/Twitter interface mapping payload. | Local-Only | False | False |
| `linkedin-adapter-status` | Defines LinkedIn API restrictions and limits. | Local-Only | False | False |
| `linkedin-dry-run` | Validates scope limits and connection mappings. | Local-Only | False | False |
| `validate-linkedin-dry-run-fixtures` | Validates local JSON fixtures for linkedin payloads. | Local-Only | False | False |
| `linkedin-staging-contract` | Outputs LinkedIn interface mapping parameters. | Local-Only | False | False |
| `linkedin-scope-verification-checklist` | Explains exact API scope barriers and operator needs. | Local-Only | False | False |
| `instagram-asset-export-status` | Explains visual-asset packaging isolation standards. | Local-Only | False | False |
| `instagram-asset-dry-run` | Generates a mapping of expected meta visual elements. | Local-Only | False | False |
| `validate-instagram-asset-fixtures` | Validates mock asset output logic locally. | Local-Only | False | False |
| `instagram-staging-contract` | Outputs standard Meta visual asset parameter map. | Local-Only | False | False |
| `meta-capability-review-checklist` | Specifies what must be proven before Meta APIs unlock. | Local-Only | False | False |
| `pilot-prerequisites-status` | Programmatic blocker matrix output reading NO-GO. | Local-Only | False | False |
| `telegram-private-staging-packet-status` | Local status mapping indicating explicitly that API logic is NO-GO. | Local-Only | False | False |
| `telegram-staging-flow-dry-run` | Tests end-to-end integration of above mocked modules safely. | Local-Only | False | False |
| `telegram-staging-operator-rollback-drill` | Executes the "Reject & Quarantine" simulated emergency stop. | Local-Only | False | False |
| `telegram-live-no-go-status` | Verifies explicitly that NO components enable network routes. | Local-Only | False | False |
| `live-project-sources-bundle` | Packages up project state dynamically for standard ingestion. | Local-Only | False | False |
