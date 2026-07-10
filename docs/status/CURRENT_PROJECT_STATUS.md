# Current Project Status

## Authority

GitHub remote commits and fetched repo files remain runtime authority above this status doc. This file and `current_project_status.json` are the current human and machine handoff surfaces.

`ui/contentops_v5/` is the canonical product UI. `ui/institutional_operator_cockpit_v4/` is fallback/reference only. Do not create or revive another standalone dashboard.

## Current Product Phase

ContentOps V6 has proven the Substack-first supervised text/image distribution loop through real public outputs. The canonical runner is `live_contentops.eight_platform_substack_first_pipeline_v1`; the canonical Microsoft Edge profile is `A:\Capital Chronicle\operator-browser-profiles\contentops-social-main` on the currently verified CDP port `9223`.

Canonical flow:

```text
headlines/CDP -> LLM selection -> grounded article + three charts
-> Substack publication/readback -> native derivatives
-> exact media manifest -> ordered reply chains
-> platform adapters -> strict public readback -> evidence
```

## Current Live Run

Run: `eight_platform_live_20260710_recovery1`

Classification: `PASS_SUBSTACK_FIRST_TEXT_IMAGE_DISTRIBUTION_V1`

Canonical article: `https://capitalchronicle.substack.com/p/effective-fed-funds-rate-holds-at`

The article “Effective Fed Funds Rate Holds at 3.62% as Policy Calibration Continues” is public, frozen, and contains three distributed source-backed FRED charts. Primary derivative media is asset `primary`, SHA-256 `b83584745931f60d976bde11b383ef3ca75c5cfed254c2c59af7a7513572a7af`.

## Platform Matrix

| Destination | Status | Public evidence |
| --- | --- | --- |
| Substack | SUCCESS, frozen | `https://capitalchronicle.substack.com/p/effective-fed-funds-rate-holds-at` |
| Telegram | SUCCESS, frozen | `https://t.me/CapitalChronicle/61` |
| Discord | SUCCESS, frozen | message `1525069505905037414` |
| X | SUCCESS | root `2075510632770875841` plus six ordered replies |
| Threads | SUCCESS | root `18093784043216614` plus three ordered replies |
| LinkedIn | SUCCESS | activity `7481289145206644736` |
| Facebook Page | SUCCESS | post `1342374731414277` |
| Instagram Business | SUCCESS | media `18014355884711904` |
| YouTube | SUCCESS | Community post `UgkxLF5TJ6zbW1-3_at3PdfBr8wlbkFbko60` |
| TikTok | BLOCKED | `BLOCKED_TIKTOK_CANONICAL_PROFILE_NOT_AUTHENTICATED` |

Wrong-logo Facebook and Instagram originals remain `SUPERSEDED_WRONG_MEDIA`. LinkedIn activity `7481311616265895936` remains `SUPERSEDED_IMAGE_ONLY`. The prior YouTube Short remains `WRONG_SURFACE_EXECUTION_NOT_ACCEPTED`. None was deleted.

Discord’s publication-logo rich preview is accepted for this run as a minor future preview enhancement.

## Product Rules

- Substack is canonical; every derivative links back to it.
- Generated media-manifest identity and SHA-256 are derivative media authority.
- Hard truncation is forbidden; overflow becomes ordered replies/comments.
- YouTube defaults to Community text + image + link. Video/Short mode is separate and non-default.
- A click, upload, or API response is not success. Stable public identity plus text/media/link/account readback is required.
- Derivative resume cannot touch Substack or already successful destinations.
- Malformed posts are reconciled, repaired, or superseded without silent duplication.

## Evidence

- Run evidence: `docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/eight_platform_live_20260710_recovery1/run_evidence_v1.json`
- Final matrix: `docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/eight_platform_live_20260710_recovery1/final_platform_matrix_v1.json`
- Platform contract: `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/platform_delivery_contract_v1.json`
- Master plan: `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md`

## Last Updated By Task

`TASK_CONTENTOPS_HEAVY_NORTH_STAR_MASTER_PLAN_REBUILD_AND_MULTI_PLATFORM_LIVE_OUTPUT_REPAIR_V2`

## Current Next Recommended Task

`TASK_CONTENTOPS_V6_PLATFORM_DELIVERY_READBACK_DASHBOARD_AND_TIKTOK_AUTH_HANDOFF_V1`

Expose the final matrix, reply chains, media hashes, supersession links, and blockers in V5. Keep every current public output read-only and guide TikTok authentication in the canonical Edge profile without persisting session secrets.
