# V6 Scoped Network Policy Governance

This document codifies the ContentOps network policy. Under V6, the absolute ban on remote networking is replaced with a scoped network policy.

## 1. Action Class Matrix
The following action classes partition the repository's network capabilities:
1. `passive_static_resource`: Passive assets (fonts, icons, stylesheets) loaded client-side with no state tracking.
2. `active_read_api`: Read-only queries to external public databases.
3. `provider_generation_api`: Requests to generative models.
4. `browser_cdp_readonly`: Headless browser reads and DOM checks.
5. `browser_cdp_supervised_write`: Supervised browser action sequences.
6. `platform_api_supervised_write`: Supervised platform writes (Substack, Discord).
7. `live_dispatch_write`: Direct production publication.
8. `credential_presence_check`: Checks for local token structure without reading values.
9. `credential_hydration`: Injecting tokens securely.
10. `forbidden_session_or_secret_extraction`: Unauthorized extraction of secrets (Strict Ban).

## 2. Permitted Passive Resource Rules
Passive static resources are allowed only if:
- No credentials are required.
- No cookies, localStorage, or sessionStorage are read or written.
- No auth headers are passed.
- No user accounts are bound.
- No analytics or tracking pixels are included.
- No remote executable scripts are loaded.
- No platform writes are made.
- No user data is exfiltrated.
- The domain and purpose are explicitly documented in `network_resource_allowlist.json`.

## 3. Allowed Domain Details
- **Resource**: Google Fonts
  - **Domains**: `fonts.googleapis.com`, `fonts.gstatic.com`
  - **Purpose**: Cosmetic typography only.
  - **Fallback**: System font stack (offline-ready).
