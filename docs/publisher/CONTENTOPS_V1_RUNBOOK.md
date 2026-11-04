# ContentOps V1 runbook: a finished piece to every destination

Written by the ContentOps V1 lane on 4 Nov 2026 for Codex Publisher. Live code:
tag `contentops-live-20261104-cc199-v1-lane-c` (rollback: `contentops-live-20261104-cc173-draft-scope`).
Times for Jim are GMT+7; records stay UTC.

## 1. How a finished piece goes out

1. The piece's operation has a `binding.json` under
   `A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\<run_id>\`.
2. From `A:\Capital Chronicle\ContentOps` run, with your real invocation id:

   ```
   python scripts/run_native_desktop_editorial.py publication-resume --binding "<binding.json>" --rollout config/native_desktop_rollout_v1.json --native-invocation-id "<your turn id>"
   ```

3. The coordinator sends Substack first, then every derivative in one pass:
   Telegram, Discord, Facebook, Instagram and Threads through their APIs; X, YouTube,
   the LinkedIn company page and Substack through Neo. Jim's member profile goes through
   the LinkedIn member API. A Neo step comes back as `native_tool_request`: run
   `publication-tool-begin --request-hash <h>`, do exactly that step in BrowserOS Neo
   (one window, your task's tab group; upload only with Neo's upload tool), then
   `publication-tool-submit` with the observed result, then `publication-resume` again.
4. Check with `publication-status --binding "<binding.json>"` (read-only).

What the code now guarantees (4 Nov fixes):
- Every derivative carries an image. An empty per-platform choice takes the first
  reviewed image; a copy frozen without one gets the run's first reviewed chart or card
  at finalization (the same image as the canonical), or an owned facts card if the run
  has none. An image failure never blocks the post: it goes with its link and
  `post_image_floor_failure` records the cause.
- Instagram is never left unregistered for want of an image.
- Each LinkedIn post also goes to the Capital Chronicle company page (`linkedin_company`).
- Substack requests carry each image's `placement_after`, caption and alt text; place
  the image where `placement_after` says, never above the first paragraph unless it says so.
- One destination's recovery (Threads `AUTH_INVALID`, a LinkedIn `UNKNOWN_WRITE`) no
  longer holds the article's other destinations once its canonical is confirmed.
- Daily digest: day label "November 4, 2026", every live article (the store's confirmed
  canonicals as well as the feed), a one-line standfirst each, a titles card at the top;
  a web-confirmed digest never holds the next day's.

## 2. What proves it

For each destination, `publication-status` shows `DISPATCH_CONFIRMED` with
`RECONCILED_CONFIRMED` and a public URL. Then read the public page through Neo and check
the image is the reviewed one (the run's `media/` file). `published_content_v1.jsonl`
gets the piece once its canonical is confirmed. Record each piece's result in its
BACKLOG Result line: `+1: <title>, <Substack URL>, <destinations confirmed>`.

## 3. Named failures and what to do

| Status or cause | Meaning | Action |
|---|---|---|
| `UNKNOWN_WRITE` | The send may or may not have landed. | Read the destination's page through Neo at least 10 minutes after the attempt. Present: confirmed. Absent: one retry, then a readback. Never resend blind. |
| `AUTH_INVALID` / `THREADS_AUTH_INVALID` | The account token expired. | Jim re-authorizes; never retry a login or read secret files. Other destinations continue. |
| `NATIVE_NEO_TOOL_PENDING` / `PENDING_NATIVE` | A Neo step is waiting. | Do the step (begin, act, submit, resume). |
| `VERIFY_IDENTITY linkedin_company` | First company-page send in a session. | Open the company admin page in Neo, confirm "Capital Chronicle" (143198922), submit. |
| `PENDING_JIM_EMAIL_CODE` | Substack asked for the email code. | Leave that tab on the code screen; Jim types it; continue in other tabs (decision 54). |
| `DERIVATIVE_EXPIRED_STALE_NO_WRITE` | The copy aged out unsent. | Do not repost a stale copy; the newest piece goes instead (CC-186). |
| `RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE` on Substack | Live page differs from the bound copy, often after a credit edit. | The page is live: check it by eye. CLD-C7 (open) is to stop this holding derivatives. |
| `FAILED_BEFORE_WRITE` (Instagram, unhosted image) | The selected image has no hosted URL. | Re-run the resume; the delivery step hosts the selected image. Never use an old hosted card. |
| `post_image_floor_failure` on an intent | No image could be built. | The post went with its link; fix the cause named there. |
| `NATIVE_FILE_DIALOG_OPEN` | A native file dialog opened. | Stop that step; Jim closes it. Upload only through Neo's upload tool. |

## 4. Still open after 4 Nov

- Threads: token invalid until Jim re-authorizes; a Neo path for Threads would remove
  the token dependency (the web session is signed in).
- CC-199 CLD-C7 (canonical marked incomplete after an edit) and CLD-C11 (derivative
  expiry counts from the outbox row, not the canonical's publication).
- Text-first briefs still skip Facebook, YouTube and Instagram (decision 37 B2); CC-199
  asks for every destination.
- 17 tests that already failed on 24e067d3 (listed in
  `CC-199/contentops-v1-lane-20261104/regression-15-files-summary.txt`).
</content>
</invoke>
<invoke name="Bash">
<parameter name="command">cd "A:/Capital Chronicle/ContentOps" && python - <<'EOF'
import json, hashlib
from pathlib import Path
S = Path(r"C:\Users\bullw\AppData\Local\Temp\claude\00ea073e99648066\7e6d9e4c-70b1-4f8d-a990-2f964934227e\scratchpad")
before = {l.split(" ", 1)[1].strip(): l.split(" ", 1)[0] for l in (S / "dirty_before_sha.txt").read_text().splitlines() if l.strip()}
out = {
 "operating_root": r"A:\Capital Chronicle\ContentOps",
 "branch": "codex/contentops-local-publisher-20261030",
 "method": "git merge --ff-only from a non-live worktree; no operating-root file edits, branch switch, app restart or schedule change",
 "integrations": [
  {"at_utc": "2026-11-04T13:36:30Z", "previous_head": "24e067d3cc6498cb8a222f4f02aaa451cf13d7fd", "integrated_commit": "e0edefe4e54b6bd345721d09c1fa40188b81b473", "tag": "contentops-live-20261104-cc199-v1-lane"},
  {"at_utc": "2026-11-04T13:44:30Z", "previous_head": "e0edefe4e54b6bd345721d09c1fa40188b81b473", "integrated_commit": "a415445bbd05bda71bc64ba95bc02a6167084393", "tag": "contentops-live-20261104-cc199-v1-lane-b"},
  {"at_utc": "2026-11-04T13:52:40Z", "previous_head": "a415445bbd05bda71bc64ba95bc02a6167084393", "integrated_commit": "a23cc3b11eff71d6b7c4fd65ba8aca9c09a18154", "tag": "contentops-live-20261104-cc199-v1-lane-c"}],
 "rollback_tag": "contentops-live-20261104-cc173-draft-scope",
 "contentops_process_running_at_integration": False,
 "live_code_matches_commit": True,
 "preserved_unrelated_dirty_file_sha256": before,
 "dirty_files_unchanged_after_each_integration": True,
 "public_objects_changed": ["instagram_business https://www.instagram.com/p/DfUm_VegXht/ (SEC piece, new post, reviewed SEC card, DISPATCH_CONFIRMED + RECONCILED_CONFIRMED)"],
 "schedules_changed": False, "apps_restarted": False}
path = Path(r"A:\Capital Chronicle\Worktrees\contentops-v1-lane-20261104\docs\publisher\CC-199\contentops-v1-lane-20261104\operating-root-integration.json")
path.write_text(json.dumps(out, indent=1), encoding="utf-8")
print("written", path)
EOF