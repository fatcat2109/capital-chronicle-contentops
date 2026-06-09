# Automation Policy Modes (After 0086)

## Purpose
This document outlines the policy-gated automation capability model that upgrades the previous hard-coded safety posture. The goal is to make future automation possible when explicitly authorized, without weakening safety. This model defines automation modes, capability flags, platform scopes, approval requirements, credential boundaries, and fail-closed validation.

## Required Automation Modes

1. **local_dry_run**
   * `env_read_allowed`: False
   * `network_allowed`: False
   * `live_post_allowed`: False
   * `scheduler_allowed`: False
   * `autonomous_allowed`: False

2. **mock_publish**
   * `env_read_allowed`: False
   * `network_allowed`: False
   * `live_post_allowed`: False
   * `mock_publish_allowed`: True
   * `approval_required`: True

3. **sandbox_one_shot_live**
   * `env_read_allowed`: True (only from process env)
   * `env_file_read_allowed`: False
   * `network_allowed`: True (only for one scoped platform adapter)
   * `live_post_allowed`: True (only for one attempt)
   * `scheduler_allowed`: False
   * `autonomous_allowed`: False
   * `exact_go_phrase_required`: True
   * `private_sandbox_required`: True
   * `redaction_required`: True
   * `audit_required`: True
   * `kill_switch_required`: True
   * `approval_required`: True

4. **supervised_live**
   * `env_read_allowed`: True (only from process env or approved secret manager later)
   * `env_file_read_allowed`: False (by default)
   * `network_allowed`: True (only for scoped platform adapter)
   * `live_post_allowed`: True (only for approved queue item)
   * `scheduler_allowed`: False
   * `autonomous_allowed`: False
   * `approval_ledger_required`: True
   * `idempotency_required`: True
   * `kill_switch_required`: True
   * `redaction_required`: True

5. **approved_batch_live** (Design-only)
   * Not allowed yet. Requires future queue, idempotency, per-item approval, batch cap, rollback.

6. **scheduled_approved_live** (Design-only)
   * Not allowed yet. Requires future scheduling policy and operator approval.

7. **autonomous_live** (Permanently forbidden)
   * Autonomous replies/DMs permanently forbidden.
   * Scraping platform metrics permanently forbidden unless a future read-only metrics API task explicitly approves API-based metrics.

## Platform Capability Gates
* **Telegram**: May support `sandbox_one_shot_live`. `supervised_live` remains design-only until queue/idempotency exists.
* **X, LinkedIn, Facebook Page, Instagram, TikTok**: Must remain `local_dry_run`/mock/design-only until platform-specific gates exist.

## Capability Escalation
Automation can progress from `local_dry_run` up to `supervised_live` or `approved_batch_live` ONLY when explicit structural requirements are met (e.g., idempotency, queueing). The validation framework guarantees that capabilities cannot be enabled without their corresponding safety checks.
