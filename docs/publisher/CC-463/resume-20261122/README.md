# CC-463 chart contract readback

The 17 November ledger entry came from an edit to the CPI preview first
published on 10 November. CC-425 appended one reference link to Substack article
`224293572` on its original dispatch
`dispatch_9aab37332626d663aadd8d8a631c300e`. The retained public capture shows a
release facts card followed by the gold TradingView chart. The coordinator's
image row lists the original packet's CPI-history chart first. All five public
images were kept by the link edit. BrowserOS Neo reopened the same public page
and confirmed the release facts card still precedes the gold chart.
[Public article](https://capitalchronicle.substack.com/p/if-october-core-cpi-is-03-or-higher) ·
[Retained public order](../../CC-425/resume-20261117/cpi-crosslink-public-capture.json) ·
[Retained image hashes](../../CC-425/resume-20261117/cpi-crosslink-public-media.json)

The coordinator now records an edit's image event only when the reviewed edit
changes media. Later readbacks of that exact public object retain the first
edit's clock. A first send with a reviewed amendment uses its publication
clock. Media-changing edits use the same image validation as new sends.
Wrong-type and off-scale images return their exact reason before the edit can
reach the transport. A valid chart reaches the transport and the existing image
register. The confirmed article and the historical image row remain available
under their original identities.

The candidate passed 106 targeted tests. The operating root passed 71 installed
checks, including the required Publisher integration tests. The existing
`CapitalChronicle-PlanStatusPosts-V1` task ran from the operating root at
01:16 GMT+7 and reported `OK` with zero newly queued posts. The preflight and
installed file hashes agree for the six delivery paths and the tracked local
work in both checkouts. The launch arguments show `gpt-6.2-sol/max`
(`CONFIGURED_NOT_OBSERVED`). The installed proof links the test reports and the
read-only runtime evidence. [Installed consumer](installed-consumer.json)

The verified 16 November baseline covers 12 market destination records with
TradingView first. The previously opened Instagram image is a full native 4:5
Bitcoin chart at 1080 × 1350. CC-459's retained six-market overlay images bind
their plan levels and source windows. The installed minute run supplies no new
per-destination or price-overlay observation.
[Baseline and Instagram proof](../resume-20261117/README.md) ·
[Six-market overlays](../../CC-459/six-market-scale-proof.json)

The live chart register supplied the following comparisons for 16–21 November
through the time of this readback. The sample counts distinct image hashes.

| Market | Limit | Measured images | Observed absolute gap | `NOT_COMPARED` |
| --- | ---: | ---: | ---: | ---: |
| Gold spot | 0.15% | 17 | 0.002098–0.107985% | 1 |
| S&P 500 cash | 0.15% | 0 | — | 6 |
| EUR/USD | 0.15% | 6 | 0.007297–0.042793% | 2 |
| USD/JPY | 0.15% | 6 | 0.000628–0.026389% | 0 |
| WTI futures | 0.40% | 0 | — | 5 |
| Bitcoin | 0.40% | 19 | 0.001209–0.211676% | 0 |

The US500 and WTI images in this sample lack an eligible paired quote and
supply no measured gap. The earlier held pairs have 34–38 minutes of clock
skew. The existing limits continue to govern. [Original held pairs](../held-price-pairs.json)

The clean observation covers the seven complete production days from
22 November 02:00 to 29 November 02:00 GMT+7. The installed audit currently
reports `OBSERVATION_PENDING`. On or after 29 November 02:00 GMT+7, Publisher
reads that exact window from the existing register. The verified 16 November
full day and Instagram proof are already on record. The live consumer uses
ordinary publications for the new observation window.

```powershell
python -B scripts/audit_publication_images_cc463.py --register "A:\Capital Chronicle\Runtime\ContentOps\published_images_v1.jsonl" --day 2026-11-22 --following-days 6
```
