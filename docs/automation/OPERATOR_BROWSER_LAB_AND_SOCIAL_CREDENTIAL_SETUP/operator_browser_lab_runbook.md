# ContentOps Edge Publishing Runbook

This is the single current operator browser and supervised publishing runbook.

## Canonical Profile

```text
Browser: Microsoft Edge
Profile: A:\Capital Chronicle\operator-browser-profiles\contentops-social-main
Preferred CDP port: 9223 when 9222 is occupied by Chrome/Antigravity
```

Never publish from Edge built-in profiles, temporary profiles, Antigravity Chrome, or an unknown CDP owner. The profile lives outside the repo and must not be committed.

## Open And Diagnose

```powershell
python -m live_contentops.operator_browser_lab open --platform substack
python -m live_contentops.publishing_profile_registry_v1 doctor
```

The doctor must report `READY_TO_ATTACH`, Microsoft Edge, and the exact profile root. Port `9222` is rejected when owned by noncanonical Chrome; current live evidence uses `9223`.

Safe readiness checks may inspect browser family, CDP reachability, process/profile ownership, destination identity, and visible authenticated UI selectors. They must not read or persist cookies, localStorage, sessionStorage, authorization headers, tokens, webhook values, or raw secret values.

Fast Ship does not relax this boundary. Environment-variable name checks and presence booleans are allowed; raw values are never printed, logged, copied into evidence, or committed.

## Canonical Runner

```powershell
python -m live_contentops.eight_platform_substack_first_pipeline_v1 `
  --run-id <run-id> `
  --output-dir docs\automation\EIGHT_PLATFORM_FULL_PIPELINE_V1\<run-id> `
  --cdp-port 9223 `
  --operator-approved-full-live-run
```

For failed-destination repair, use derivative-only resume:

```powershell
python -m live_contentops.eight_platform_substack_first_pipeline_v1 `
  --run-id <existing-run-id> `
  --output-dir docs\automation\EIGHT_PLATFORM_FULL_PIPELINE_V1\<existing-run-id> `
  --cdp-port 9223 `
  --operator-approved-full-live-run `
  --resume-derivatives `
  --resume-platform <destination>
```

Do not use derivative resume to reopen Substack, Telegram, Discord, or any already successful destination.

## Media Upload

Local browser uploads use Playwright `expect_file_chooser()` and `file_chooser.set_files()` first. If no chooser event is reliable, the adapter selects the newest connected and newly enabled image input and calls `set_input_files()` directly. It never clicks the file input or automates Windows Explorer.

Uploads are sequential. Each insert must show one new in-body image, meaningful natural dimensions, no spinner/placeholder, visible loaded media, intended marker placement, and saved state.

## Product Contracts

- Substack is canonical and requires three distributed source-backed visuals.
- Derivatives use exact media-manifest asset/hash binding.
- X and Threads overflow into ordered replies; hard truncation is forbidden.
- New X and Threads runs require a root plus two sentence-complete replies and `primary`, `policy_corridor`, and `sofr_context` exactly once across the chain.
- Instagram feed URLs are accepted as exact visible caption text with a clear CTA; clickability is optional.
- YouTube uses Community text + image + Substack link. Video/Short is non-default.
- TikTok must report the exact authentication blocker when unavailable.
- A write is successful only after stable public URL/ID and text/media/link/account readback.

## Reconciliation

Before retrying malformed or uncertain output:

1. Identify the exact existing post by account, topic, timestamp, payload, and media fingerprint.
2. Prefer edit, then author comment/reply, then one corrected replacement.
3. Preserve and label the malformed post; never silently delete it.
4. Record the relationship, payload hash, media hash, root/reply IDs, and readback.
5. Unknown write outcomes block automatic retry.

## TikTok Handoff

Open TikTok through the canonical profile and let the operator authenticate manually. Do not inspect or export session storage. After identity is visibly confirmed, rerun safe session readiness and only then enable the reviewed native derivative adapter. Do not substitute YouTube, Instagram, video, or another account.

App Client Key, Client Secret, and App ID presence does not establish TikTok readiness. Callback registration, user OAuth, refresh token, `open_id`, runtime token refresh, native Content Posting adapter, account identity, required scopes, and app audit must all pass first.

## Video Capability Audit

`video_platform_capability_matrix_v1.py` is read-only. It may build a local private YouTube request and classify Short versus long-form metadata, but it must not call an upload endpoint. TikTok native, YouTube long-form, and YouTube Shorts each require a separate explicit mode and public-write approval. The normal article runner can call only YouTube Community.
