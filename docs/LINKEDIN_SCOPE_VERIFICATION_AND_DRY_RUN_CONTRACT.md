# LinkedIn Scope Verification and Dry-Run Contract

The local LinkedIn dry-run adapter (`cc-live-contentops/live_contentops/adapters/linkedin.py`) simulates LinkedIn posting/article behavior without actual platform APIs, tokens, or network requests.

### Purpose
- Converts upstream provider simulator results into platform-shaped post/article previews.
- Strictly offline, enforces `safe_for_publish = False`.
- Evaluates policy bounds again.
- Demands scope verification logic for any future credential work.

### Safety Rules
- **No OAuth/Client Secrets:** Adapter explicitly scans for and rejects values shaped like client secrets, bearer tokens, API keys, or oauth tokens.
- **No Live LinkedIn URLs/IDs:** Attempts to send to strings resembling real LinkedIn URLs (`linkedin.com/`) or URNs (`urn:li:...`) or 9-digit org IDs are rejected unless marked explicitly as a placeholder.

### Scope Verification Checklist
`build_linkedin_scope_verification_checklist()` defines the absolute prerequisites for verifying LinkedIn API scopes. It asserts that real LinkedIn scopes and capabilities (like `w_member_social`, `rw_organization_admin`) are **not known** and must not be invented by an LLM. They require explicit future online developer portal verification.

### Staging Contract
`build_linkedin_staging_contract()` defines the absolute checklist (credential acquisition, approval gating, quarantine rules) that must be true before this adapter is ever converted into a real HTTP executor.
