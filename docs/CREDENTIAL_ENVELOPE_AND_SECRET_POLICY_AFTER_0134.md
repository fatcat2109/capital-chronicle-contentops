# Credential Envelope and Secret Policy Design (0134)

## Purpose
This pack records future credential requirements and the redaction policy framework. It is not a credential store.

## Policy Only, Not Credential Storage
- **No `.env` reads**: The system does not access the `.env` file.
- **No secret loading**: No credential values are loaded.
- **No credential presence checks**: The system does not inspect the system environment or disk for secrets.
- **No platform API enabled**: All `platform_api_call_allowed_now` remain `false`.

## Redaction Requirements
All inputs must be verified not to contain plaintext secrets, passwords, or bearer tokens. If anything resembles a secret, it will fail-close validation.

## Fake Secrets Tests Only
Only deterministic fake placeholders are allowed in negative fixtures (e.g., `FAKE_SECRET`).

## Relationships
- Expands upon the platform rules verified in 0133 Official Docs pack.
- Forms the core constraints for the future supervised live gates, specifically the boundary preventing execution without explicit manual approval.
- Prepares for the 0135/0136 UI: the UI may display the states of these envelopes (i.e. 'X API Key required') but must never receive or show secret values directly in plaintext.
- No Project Sources refresh occurs after this task.
