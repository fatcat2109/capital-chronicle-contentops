# Pre-Alpha Daily Manual Publish Runbook & Operator Checklist (After 0112)

Task: `TASK_CONTENTOPS_0112_PRE_ALPHA_DAILY_MANUAL_PUBLISH_RUNBOOK_AND_CHECKLIST_V0`

LOCAL ONLY | MANUAL ONLY | SUPERVISED | NO NETWORK | NO PROVIDER | NO PLATFORM
API | NO CREDENTIALS | NO POSTING

This is an operator-facing runbook. It documents how to drive the accepted
0095-0111 local ContentOps workflow for a single daily manual content run. It
adds no automation. Every external publish is done by the operator by hand,
outside this repo, and only after a mandatory final operator check.

---

## 1. Current baseline

- Repo path: `A:\Capital Chronicle\tools\cc-live-contentops`
- Branch: `master`
- Expected HEAD: `0dd3055`
- Accepted workflow chain (all local, deterministic, fixture-driven):

| Task | Stage |
| ---- | ----- |
| 0095 | content engine / editorial packet |
| 0096 | prompt pack / style profile / editorial rubric |
| 0097 | draft renderer / review queue |
| 0098 | manual review workflow / approval packet |
| 0099 | manual export packet / content ledger |
| 0101 | end-to-end local demo packet |
| 0103 | content seed library / editorial calendar |
| 0104 | operator dashboard / control-plane packet |
| 0105 | editorial batch review packet |
| 0106 | manual decision batch packet |
| 0107 | manual export batch packet |
| 0108 | manual publish record packet |
| 0110 | platform-specific manual export templates |
| 0111 | daily operator content run packet |

Nothing in this chain posts, schedules, calls a platform/provider/LLM/network
API, scrapes, ingests metrics automatically, or reads credentials/`.env`.


---

## 2. Daily operator flow

Run this sequence once per manual content run. All commands are read-only
local summaries; none of them publish anything.

1. **Check repo posture.**
   Confirm you are on `master` at the expected HEAD, with no unexpected
   changes beyond known operator drift (`.gitignore`, `.env`,
   `project_sources_bundle_AFTER_0074/`, older 0085-0094 task docs).

2. **Run the daily operator content run summary.**
   This is the single composed workbench summary for the day. Inspect:
   - `packet_status` (must be `pass`)
   - `ready_for_operator_copy_paste_count`
   - `blocked_or_not_ready_count`
   - `unsafe_flag_count` (must be `0`)

3. **Inspect ready vs blocked / not-ready counts.**
   - Ready items are clean platform copy/paste templates.
   - Not-ready items include blocked seeds, revision/rejected decisions,
     unsupported/blocked templates, blocked records, and eligible-but-not-yet
     recorded exports. They are NOT ready to publish.

4. **Inspect the platform manual templates.**
   Review the per-platform copy/paste text and conservative formatting notes.
   These are formatting aids only, not verified current platform specs.

5. **Perform the final operator check (mandatory).**
   Read each ready template in full. Confirm:
   - source attribution / general-process marker is correct
   - limitations and freshness are intact
   - no financial advice / signal / fake-alpha language
   - the content is something you stand behind publishing

6. **Manually copy/paste externally.**
   Only after the final operator check, copy the approved text and post it
   yourself in the platform UI. This repo never posts for you.

7. **Manually record the publish afterward.**
   After you have posted by hand, record the publish URL, timestamp, and any
   hand-observed metrics through the manual publish record stage (fixture /
   manual config). See section 7.

8. **Never infer publication.**
   If you have not recorded an explicit manual publish record, the item stays
   `not_recorded` / `export_prepared`. The system never assumes you published.


---

## 3. Required commands

```
python -m live_contentops.cli status
python -m live_contentops.cli pre-alpha-daily-operator-content-run-summary
python -m live_contentops.cli pre-alpha-platform-manual-templates-summary
python -m live_contentops.cli pre-alpha-manual-publish-record-summary
python -m pytest -q tests/test_security_scans.py
```

- `status` - repo/workflow posture check.
- `pre-alpha-daily-operator-content-run-summary` - the composed daily workbench
  (0111). Start here each day.
- `pre-alpha-platform-manual-templates-summary` - per-platform copy/paste
  templates (0110).
- `pre-alpha-manual-publish-record-summary` - manual publish recordkeeping
  posture (0108).
- `pytest tests/test_security_scans.py` - confirms no forbidden
  network/provider/platform/scheduler/scraping/credential capability slipped in.

All commands are local and read-only. Running them publishes nothing.

---

## 4. Safety checklist (every run)

Before, during, and after a run, confirm all of the following hold:

- [ ] No API posting. Publishing is manual copy/paste in the platform UI only.
- [ ] No scheduler. There is no timed or queued auto-send.
- [ ] No platform credentials. No tokens, app secrets, or channel IDs are used.
- [ ] No `.env` reads. The operator secret file is never opened by this flow.
- [ ] No automatic metrics. Metrics are hand-entered only, and may be null.
- [ ] No fake Capital Chronicle alpha output.
- [ ] No market signal / financial advice / buy-sell-hold / price targets /
      position sizing / guaranteed prediction.
- [ ] Operator final check performed on every ready item before posting.

If any box cannot be checked, stop and do not publish that item.


---

## 5. Platform manual notes

These are manual copy/paste notes only. They do not verify current platform
specifications. Confirm actual current platform rules yourself before posting.

- **X**: manual short-form copy/paste only. Conservative local length guidance
  (~280 chars); verify the current limit yourself.
- **LinkedIn**: manual professional long-form copy/paste only.
- **Threads**: manual conversational short-form copy/paste only.
- **Newsletter / generic**: manual markdown / copy-paste only.
- No current platform spec verification is performed by this system unless a
  separate task is explicitly scoped for it.

Unsupported platform families (for example `tiktok`, `facebook_page`,
`instagram`) are not templated as clean; they are surfaced as
unsupported/not-ready.

---

## 6. Blocked / not-ready handling

The workflow preserves problems instead of hiding them. Treat all of the
following as NOT ready to publish:

- **Blocked seeds** stay blocked, with reasons.
- **Revision / rejected decisions** stay not ready; they are surfaced as
  non-exported, never as clean templates.
- **Unsupported templates** stay not ready.
- **Missing publish record** does not imply publication; the item remains
  `not_recorded` / `export_prepared`.

Never copy/paste or post a blocked or not-ready item. Resolve it upstream
(revise the seed, re-decide, re-export) and re-run the daily summary.

---

## 7. Operator evidence habit

- When a manual publish actually happens, record the publish URL, timestamp,
  and any hand-observed metrics through the manual publish record stage.
- Records are operator-supplied only. The system never fetches or scrapes
  metrics.
- Never paste secrets, tokens, channel IDs, or credentials into the repo, into
  commits, or into chat.
- Do not use auto-scraping for metrics. If you want metrics, enter them by hand
  from what you observed in the platform UI.

---

## 8. What this runbook does NOT authorize

This document is operator guidance only. It does not, and must not be read to,
enable:

- auto-posting or API publishing
- scheduling or queued sends
- automatic metrics ingestion or scraping
- platform / provider / LLM / network / search calls
- credential or `.env` reads
- treating any item as publish-ready without the final operator check

The operator final check remains mandatory before any external manual
publishing.

