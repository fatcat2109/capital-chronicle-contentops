# LIVE_CONTROL_PLANE_PROJECT_SOURCES_REFRESH_CHECKLIST_AFTER_0054

## Exact Bundle Path
`A:\Capital Chronicle\tools\cc-live-contentops\outputs\project_sources_bundle\TASK_CONTENTOPS_0053`

## Exact 8 Files to Upload
Upload exactly these 8 files from the bundle directory:
1. `00_UPLOAD_BUNDLE_MANIFEST.md`
2. `01_NEW_CHAT_CONTINUATION_PROMPT_AFTER_0053.md`
3. `02_CURRENT_STATE_SUMMARY_AFTER_0053.md`
4. `03_COMPLETED_TASKS_0035_TO_0053.md`
5. `04_NEXT_TASK_0054_BRIEF.md`
6. `05_SAFETY_BOUNDARIES_AND_KNOWN_CAVEATS.md`
7. `LIVE_CONTROL_PLANE_LOCAL_RELEASE_RECAP_AFTER_0050.md`
8. `LIVE_CONTROL_PLANE_OPERATOR_HANDOFF_AFTER_0050.md`

## Exact Stale Project Sources to Remove
Remove these from the current ChatGPT Project Sources:
- Old live-control-plane continuation prompts.
- Old current state summaries.
- Old handoffs.
- Old upload manifests.
- Pre-0053 bundle copies.
- Stale 0045/0046/0047 standalone state files (superseded by the 0053 bundle).

## What NEVER to Upload
- Secrets, credentials, real platform IDs, `.env` files.
- `__pycache__` or `.pyc` files.
- Raw logs.
- Antigravity brain files or local memory folders.
- Full outputs history.
- Core repo files from `cc-contentops`.
- Large JSON fixture dumps.

## Recommended Operator Steps
1. **Upload only the 8 files** from the `TASK_CONTENTOPS_0053` bundle.
2. **Remove stale old Project Sources** from the ChatGPT project settings.
3. **Open a new ChatGPT project chat**.
4. **Paste the contents** of `01_NEW_CHAT_CONTINUATION_PROMPT_AFTER_0053.md` into the new chat.
5. **Wait** for ChatGPT to audit accepted state before asking for the next prompt.

## Current Accepted Heads
- live-control-plane: `fa9a715`
- cc-contentops: `e57db90`

> [!WARNING]
> NO keys, NO env, NO API, NO live pilot. This is strictly a local-only staging bundle.
