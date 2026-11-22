# CC-378 validation — 22 November 2026

Branch: `backlog/cc-378-public-draft-claims`

The existing CC-378 implementation was rechecked after the widened requirement for every public draft. One pytest process ran the targeted consumer paths only:

```text
python -m pytest -q tests/test_public_draft_claims_cc378.py tests/test_plan_analysis_copy_cc688.py tests/test_plan_status_posts_cc306.py tests/test_substack_daily_note_cc468.py tests/test_call_followups_cc603.py tests/test_x_reply_bot_cc464.py
141 passed in 208.64s (0:03:28)
```

The focused CC-378 files also passed separately:

```text
python -m pytest -q tests/test_public_draft_claims_cc378.py tests/test_agy_editorial_assist_cc378.py
35 passed in 23.10s
```

These tests cover the planted wrong-level, reversed-direction and unsupported-cause flags, timeout fallback, bounded one-worker launch, evening claims output, plan-page and plan-post consumers, Substack daily-note checks, call follow-ups and private X-reply drafts. No live or deploy step ran.

The first live day still needs the evening file to show a claim check for every public draft, including any routes with no qualifying draft during the validation window. That proof is operational and remains for the first stream to read back.
