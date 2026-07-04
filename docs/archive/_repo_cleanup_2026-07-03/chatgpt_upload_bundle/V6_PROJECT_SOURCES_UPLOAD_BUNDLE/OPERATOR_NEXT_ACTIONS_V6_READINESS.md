# Operator Next Actions (V6 Readiness)

This document describes next manual and supervised actions required to resolve the source blockers and progress toward future publication.

## 1. Evidence Submission
- The operator must gather and submit factual evidence matching the required source references (specifically `operator_idea_source_ref`).
- Evidence must be submitted by writing to the intake submission packet without including any sensitive data or credentials.

## 2. Staging and Dispatch Gates
- Once evidence is submitted, run the operator source evidence submission validator task to check and verify the facts.
- Evaluate the operator approval gate to confirm compliance.
- Confirm supervised dispatch readiness and generate the final payload hashes.
- Destination bindings must occur in a later, separate task. No live channel IDs or webhooks may be written.

## 3. Webhook and Secret Rules
> [!WARNING]
> **No Webhook Pattern Disclosure**: Under no circumstances should webhook URLs, endpoint hostnames, or specific path patterns be printed or written to public documentation or source code.
> **Zero Credential Exposure**: No tokens, cookies, auth headers, environment variables, or private key lengths may be exposed in evidence submissions.
