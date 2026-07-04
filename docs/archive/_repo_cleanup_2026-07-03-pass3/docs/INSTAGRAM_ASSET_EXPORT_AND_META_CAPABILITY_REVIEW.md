# Instagram Asset Export and Meta Capability Review

The local Instagram asset export planner (`cc-live-contentops/live_contentops/adapters/instagram.py`) simulates Instagram planning (captions, carousel stubs, stories, reels) without actual Meta/Graph APIs, tokens, network requests, or image/video uploads.

### Purpose
- Converts upstream provider simulator results into platform-shaped export packages.
- Strictly offline, enforces `safe_for_publish = False` and `upload_enabled = False`.
- Evaluates policy bounds again.
- Demands Meta capability verification logic for any future Graph API work.

### Safety Rules
- **No App Secrets/OAuth:** Adapter explicitly scans for and rejects values shaped like app secrets, client secrets, bearer tokens, API keys, app ids, or oauth tokens.
- **No Live Instagram/Facebook URLs/IDs:** Attempts to send to strings resembling real Instagram/Meta URLs (`instagram.com/`, `facebook.com/`) or 15+ digit Meta Graph IDs are rejected unless marked explicitly as a placeholder.
- **No Image/Video Uploads:** The simulator creates manifest stubs only. Upload flags are strictly blocked.

### Meta Capability Review Checklist
`build_meta_capability_review_checklist()` defines the absolute prerequisites for verifying Meta API permissions. It asserts that real Meta capabilities (like `instagram_basic`, `pages_show_list`) are **not known** and must not be invented by an LLM. They require explicit future online Meta App Dashboard verification.

### Staging Contract
`build_instagram_staging_contract()` defines the absolute checklist (credential acquisition, approval gating, quarantine rules) that must be true before this adapter is ever converted into a real HTTP executor.
