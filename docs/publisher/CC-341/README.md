# CC-341 — weekend wrap

The weekend wrap was published on Substack at **9 November 07:41 GMT+7**:
[canonical article](https://capitalchronicle.substack.com/p/tanker-strikes-us-strikes-on-iran),
post `224085585`. The existing draft was resumed and published **web only**, with
email delivery disabled. No email-code prompt appeared. The same operation
`cc341-weekend-wrap-20261109-r2` is now fully reconciled: Substack, all eight
standard social destinations and the additional LinkedIn company copy are
confirmed. The four reboot-interrupted copies were recovered before the revised
17:00 GMT+7 deadline on 9 November.

The reopened item supplied the dated Main scenario revision. The existing source
review admitted it and bound the three model estimates (55%, 25%, 20%) to their
source excerpts. The original public-ready paragraphs, sourced Nvidia addition,
ET dateline and required notices survive in
[the prepared R2 body](resume-20261109/prepared-body-r2.md). The retained
[MAX editorial assessment](resume-20261109/editorial-assessment-r2.json) and
[final editor check](resume-20261109/final-editor-check.json) record the editorial
work. The writer configured `gpt-6.1-sol/max`; this exec launch's process arguments
configured `gpt-6.1-sol/high` (PID 4796, started 9 November 07:36 GMT+7).
Model and effort are `CONFIGURED_NOT_OBSERVED`, because runtime telemetry was
unavailable. No new editorial model call was made during publication recovery.

The fresh CC-316 TradingView USOIL snapshot captured at **9 November 07:15 GMT+7**
is the canonical image. Its original attribution remains intact. Browser readback
verified its caption, alt text, successful load and dimensions. The existing media
owner verified exact original-byte SHA256 continuity:
`7af80bd55b91edf4d55c30c512319d5dd2ff1caa9db7c81363f030a1aeeff327`.
[Media verification](resume-20261109/canonical-media-verification.json) uses only
the approved canonical image; the excluded facts card is not required on the page.
Image bytes remain binary in this operation's own Runtime media folder.

The readback comparison incorrectly expected Markdown list markers in Substack's
rendered body. The bounded fix strips list syntax for this destination while
preserving all words, values, numeric minus signs and item order. Its
[88 targeted passing tests](resume-20261109/list-readback-tests.txt) include changed
numbers, removed minus signs, omitted items and reordered items. Commit `00058c40`
is pushed on `backlog/cc-341-weekend-wrap` and fast-forwarded into
`A:\Capital Chronicle\ContentOps`; both inherited builder ledgers and the six
modified operating-root files were preserved outside the commit.

The first text approval remains **9 November 07:18:51 GMT+7**. Canonical publication
therefore missed decision 53's 15-minute dispatch target. The revised item deadline
is **9 November 17:00 GMT+7**. The earlier pre-reopen deadline was already missed;
none of these clocks has been reset. No schedule or other chat was changed.

## Reboot recovery — 9 November

The four remaining feeds were read before sending. Their newest visible posts
were from 6 November; the weekend wrap was absent. Each existing coordinator
request was then claimed and published once, with the approved text and image:

| Destination | Sent, GMT+7 | Exact public object |
| --- | --- | --- |
| LinkedIn company | 15:20:11 | [7525472297776889856](https://www.linkedin.com/feed/update/urn:li:activity:7525472297776889856/) |
| LinkedIn personal | 15:23:44 | [7525473196028940288](https://www.linkedin.com/feed/update/urn:li:activity:7525473196028940288/) |
| YouTube | 15:26:18 | [Ugkx3BwUEE0-5jRxPKxmJxG5a2DnbMFAhNK2](https://www.youtube.com/post/Ugkx3BwUEE0-5jRxPKxmJxG5a2DnbMFAhNK2) |
| X, five posts | 15:29:18 | [2119708899410645394](https://x.com/Capitalnicle/status/2119708899410645394) |

Readback verified every approved paragraph, all five X posts in order, both
LinkedIn short-link targets and the X link target. LinkedIn uses the canonical
article's chart thumbnail; its full source image and credit remain on the linked
article. X and YouTube carry the uploaded original chart; YouTube's post detail
shows the full chart although its channel feed uses a square crop. Original and
platform binary images were inspected and compared through the existing media
owner. No image bytes or base64 are stored in Git.

Interrupted X recovery exposed an existing readback bug: before the coordinator
knew the public ID, shortened-link and transcoded-image comparisons used an empty
object URL. The fix binds the observed, account-valid object before those checks
and retires obsolete unclaimed reads after verification. Known IDs stay pinned;
wrong account, ID, numbers, link targets and source images still fail. Commit
`2964bc92` passed 116 targeted tests; cleanup commit `ad5556b5` passed the 43
affected discovery/media cases. Both are pushed and integrated into the operating
root. The original source, media and editorial operation were reused.

The [final operating-root status](reboot-recovery-20261109/final-operating-status.json)
records `RECONCILED`, eight confirmed standard derivatives, one confirmed company
copy, zero unknown writes and no pending native requests. The
[acceptance check](reboot-recovery-20261109/final-acceptance.json) binds this result
to the installed consumer and the preserved modified files. This recovery launch
configured `gpt-6.1-sol/high` (PID 36308); model/effort remain
`CONFIGURED_NOT_OBSERVED`. No new editorial model call was made.
