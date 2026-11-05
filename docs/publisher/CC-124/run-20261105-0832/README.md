# CC-124 — Southwest filing article, 5 November 2026

One new article was published through the existing operation
`cc124-next-article-20261105-b`. The earlier PPI article was preserved.
CC-124 remains a standing OPEN item after this run, next due 10:32 GMT+7.

Canonical: [Southwest's 2025 fuel-hedge exit did not end the expense clock](https://capitalchronicle.substack.com/p/southwests-2025-fuel-hedge-exit-did),
Substack object `223564454`, published web-only at 09:16:47 GMT+7.
The title, approved body, source link and selected card were read back.
The original public image bytes match the approved local PNG exactly.

| Channel | Public object | Reconciliation |
|---|---|---|
| Telegram | https://t.me/CapitalChronicle/79 | Confirmed |
| Discord | Message `1567725246025572474` | Confirmed; adapter exposes no public URL |
| X | https://x.com/Capitalnicle/status/2118169951320285473 | Confirmed, all three posts, link and image |
| LinkedIn company | https://www.linkedin.com/feed/update/urn:li:share:7523933028772151297/ | Confirmed, link and image |
| Facebook Page | https://www.facebook.com/1342369584748125/posts/1445224044462678 | Confirmed after the exact absent dispatch's transport correction |
| Instagram | https://www.instagram.com/p/DfWAlMrkwtw/ | Confirmed |
| Threads | https://www.threads.com/@official.capitalchronicle/post/DfV8fzyH7uD | Public two-post thread; strict media reconciliation incomplete |
| YouTube Community | https://www.youtube.com/post/UgkxW1jZvwD2wjn58bHraF_PXxPblw-fKS7E | Confirmed, text and full public card |

The eight channel types have public posts. Seven have strict confirmed
reconciliation for this article. Threads displays a cropped link preview of the
same canonical image, rather than the expected separate full card. Its existing
object is preserved and the incomplete result is retained. It is not counted as
a strict confirmed Threads copy in the digest.

The additional LinkedIn personal API attempt was read back from the exact own
profile after the ten-minute absence interval and reconciled
`RECONCILED_ABSENT_SAFE_TO_RETRY`. No replacement personal post was sent.
The company post supplies the LinkedIn channel. Final UNKNOWN_WRITE and pending
publication-request counts are zero. An obsolete unclaimed readback from before
delivery-manifest binding was retired after the later exact absence observation;
its immutable text and source-card hashes matched (see
`superseded-readback.json`).

The website URL
`https://fatcat2109.github.io/capital-chronicle-preview/articles/da27ccf950d8d3f7d74a76d63328a79d/`
still returned 404 in the final Neo check. Substack is the confirmed canonical;
website deployment is not claimed.

The source is Southwest's Q2 2025 Form 10-Q, filed 24 July 2025. The article
explains the different clocks for approximately $40 million of closure proceeds,
$36 million of quarterly premium expense and $209 million remaining in AOCI at
30 June 2025. It does not add the unlike amounts or assert current hedge policy
from the old filing. Exact source SHA-256:
`c1fee545fb19485fae172d1b23d108df621b346796be75ababf492ea46705128`.
Only attributed, independently worded filing facts are reused. Issuer artwork
and expression are not reused.

The same native MAX writer chose, inspected, wrote, revised and accepted the
actual card and text. Sol 6.1/low performed preparation; Sol 6.1/max performed
the editorial stages. The top-level configured launch is Sol 6.1/max. Supported
runtime telemetry does not expose actual model/effort, recorded as
`CONFIGURED_NOT_OBSERVED` in `launch.json`. No later pixel inspection is relabelled
as a fresh MAX review. The binary card stays in this operation's media folder:
`A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-next-article-20261105-b\media_assets\post-facts-c6d7a73bb1808cefa008.png`,
1080 × 1350, SHA-256
`240c8f6dc5ecea0d75af69517be776603ca3c9f69d0b15d13f120b91671fdec5`.

First text approval remains 09:06:22 GMT+7; its deadline remains 09:21:22.
The canonical met that deadline, but complete distribution did not.
`all_channels_dispatched_within_target=false` is retained. Media work and
interruptions never reset approval.

The source-bound fact card now reaches the existing URL-media service after the
same source, rights and byte validation used by the article path. The narrow
company-document card exception does not remove official-release analysis chart
requirements. The actual selected card survives publication-view binding.
The topic validator recognizes hedge/hedging inflections. URL transports fail
before a write if their selected image cannot be delivered; Discord continues
to upload its verified local card without depending on a hosted URL.

Final targeted verification: **64 passed in 9.01 seconds**, one pytest process,
in `tests/test_cloudinary_delivery_media_v1.py` and `tests/test_post_visuals_v1.py`.
The earlier targeted topic tests passed 4 cases. Changes were committed, pushed
and integrated into `A:\Capital Chronicle\ContentOps` after passing sub-steps.
Validated implementation commit: `5e18ce51b72af56fa43d481948bd23f779a9ecac`.
Concurrent CC-248/CC-283 operating-root commits were preserved by merge.

`check_consumers.py` verifies one exact canonical row in the existing live feed,
the actual production-day record, and the installed Main CC-122 digest reader
without sending a digest or changing its schedule. It reports **2 distinct
articles** for 5 November and `SAVED_RECORD`. The next 07:00 reader selects that
same production-day file. See `live-consumer-acceptance.json` and
`digest-consumer-acceptance.json`; future scheduled delivery is not claimed.
Unrelated worktree changes remain uncommitted and out of this item's commits.
