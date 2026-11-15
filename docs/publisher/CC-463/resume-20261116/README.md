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

The build passes 39 targeted tests in 12.13 seconds, in one pytest process with
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
