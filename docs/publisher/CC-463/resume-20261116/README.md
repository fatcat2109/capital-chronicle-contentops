# CC-463 continuation, 16 November 2026

The implementation remains live. This continuation repairs its read-only acceptance
audit: a day with permitted text fallback no longer certifies the stronger claim
that every market post carried a chart. A measured violation fails immediately,
even before the day ends. One baseline day and its seven following days use the
existing production-day boundary, 02:00 GMT+7; no new watcher or schedule is added.
Empty follow-up days remain explicit. They provide no image or visual proof.

The existing image-register read method now exposes the lead image hash and
size, canonical URL, publication clock and clock basis. These values come from
the existing rows. Neither the rows nor historical objects are rewritten.
A chart without structured market scope is listed separately; its title or
asset ID cannot create market scope. Instagram dimension candidates remain
candidates and never count as a native-capture or visual-review observation.

The final build passes 39 targeted tests in 39.59 seconds, in one pytest process with
no workers. The actual coordinator accepts a valid chart, records its type and
exposes the same image hash to the audit. Wrong-type and off-scale charts are
refused before a transport call. The new cases cover bounded text fallback,
a partial day, seven-day timing, empty days, illustrative charts, missing image
sizes and unknown historical types. See [validation.json](validation.json) and
[image-acceptance-tests.xml](image-acceptance-tests.xml).

The first new audit fixtures omitted the register schema_version; they were
corrected. No test touched the production store. The top-level configured launch
is gpt-6.1-sol/max, CONFIGURED_NOT_OBSERVED. No editorial model call was made.

Read-only live evidence, integration and remaining public proof follow below.

## Actual image observations

[The read-only register audit](live-image-window.json) reports:

| Production day | Market post observations | TradingView first images | Text fallbacks | Full chart-first day |
| --- | ---: | ---: | ---: | --- |
| 11 November | 7 | 1 | 6 | No; 75 earlier post records also lack image types |
| 12 November | 10 | 8 | 2 | No; permitted fallback is explicit |
| 13 November | 0 | 0 | 0 | No market post |
| 14 November | 0 | 0 | 0 | No market-scoped post |
| 15 November | 0 | 0 | 0 | No market post |
| 16 November, incomplete | 4 | 4 | 0 | Day still running |

These are retained coordinator observations, not fresh public page readbacks.
Counts are destination/image records, not distinct articles. The eight
TradingView images on 14 November belong to CC-536's method illustration;
its source has no structured market scope. The two drawn images that day
belong to daily digest indexes. Neither is relabelled as a market post.
The 12 November mixed day now says TEXT_FALLBACK_OBSERVED rather than PASS.

[Exact retained dispatches and original image bytes](retained-public-image-evidence.json)
bind Telegram post 182, the later gold status alert, and Instagram post
17979008508135876 / DftqP-ikncx. The original Instagram-bound Bitcoin chart
was opened locally and inspected: candles, both moving averages, axes and
TradingView attribution are whole, with no padding. It is 1400 x 1343 and is
not 4:5. It supplies no CC-463 portrait proof. This run opened no native
application or desktop screenshot and created no public object.

Neo initialize at 03:50:12 GMT+7 on 16 November returns
NEO_ENDPOINT_CONNECTIONERROR; see [neo-availability.json](neo-availability.json).
No browser tool is exposed in this run either. No other browser was substituted.
Ops Product restores the existing Neo endpoint. Publisher then reads back the
exact existing objects and inspects the next live native 4:5 market chart.

The first currently eligible baseline is 16 November, provided the rest of
that production day retains charts on every market post. That day ends at
02:00 GMT+7 on 17 November. Its following seven days end at **02:00 GMT+7 on
24 November**, not at the time of a test or code install. The audit reports
OBSERVATION_PENDING at the actual collection clock. No replay, new post,
backdated record or passing test can complete that elapsed observation.

Repeat the installed read-only audit with:

```powershell
python scripts/audit_publication_images_cc463.py --register "A:\Capital Chronicle\Runtime\ContentOps\published_images_v1.jsonl" --day 2026-11-16 --following-days 7
```
