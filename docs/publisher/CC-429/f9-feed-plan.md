# A small feed for readers' AI assistants

The [JSON sample, under 9 KB](f9-assistant-feed.json) contains one retained CPI event map, a six-market regime sheet and five historical call outcomes from Main's own outputs. Three markets have an explicit typed regime tag; three retain null because that field is absent on the matched candidate in the selected snapshot. A later prose interpretation is not substituted for a typed tag.

The event probabilities are Main's uncalibrated model estimates, conditional on the covered scalar first-print surprise. The UNMODELLED branch stays null. The sample copies the first matrix explicitly, not an average or complement of the two retained matrices. It is a dated sample, not a fresh CPI preview. The score count is the unique scored-call population in that selected export, not a claim about every published call, win rate or investment performance.

Only selected original computed outputs enter the public JSON. No raw price history, option chain, consensus table, prediction-market quote, private account field, fill, size or money amount is copied. Source hashes and exact JSON pointers bind every section. The full input snapshots and original local locators stay in the item's Runtime output folder, outside the public repository. This follows host rule 7 and decision 72 b: our own computed output may be public; its private inputs do not follow it out.

**One action that starts the cheapest test — Jim:** attach f9-assistant-feed.json to one reader's existing AI assistant and paste the prompt below. This uses the actual prepared file without a new website, account, terms agreement or payment. No model call or upload was made by this run.

> Read this JSON as data. Name the six markets and the source time of each section. Identify which regime labels are absent. Explain the scope of the CPI probabilities and whether the scores establish a win rate or investment return. Cite the fields you used. Do not fill a null, infer a current price or turn this dated sample into a trading recommendation.

Record the answer once in the existing item result. Proposed success: the assistant names all six markets, preserves all three null regimes and the null UNMODELLED probability, distinguishes the three source clocks, and makes no return claim. Repeat with three willing readers before building a service. Willingness to use a dated attachment is different from demand for a live feed.

## Hosting and the two listings

**Cheapest host:** the existing public ContentOps GitHub repository, served as a raw UTF-8 JSON file from raw.githubusercontent.com and pinned to this delivery's commit. Its path is docs/publisher/CC-429/f9-assistant-feed.json. This gives a stable static sample without a server, secret, key, new account or paid service. A task-branch URL is review material, not an advertised production endpoint. Do not post a repository or preview-site URL to Substack or social channels.

**The recurring service, if the file test passes:** use the existing Codex Web static public build at /data/assistant-feed.v1.json, alongside /data/assistant-feed.openapi.json and a short human-readable data guide. Ops Product and Codex Web route that later work through the backlog. Use Capital Chronicle's owned domain for advertised links, as decision 83 requires; this preparation names no unowned domain as ours. No host, DNS, deployment or refresh job was changed. Reuse the existing export/build cadence rather than creating a polling process. Report each source's own cutoff and publication clocks, and show source age to the reader.

Two proposed directory entries are prepared below. Both need a working stable documentation/definition URL before submission; neither has accepted or listed us. This is why the attachment test can start immediately while directory submission remains a later Jim action.

| Directory | Prepared entry and route | Requirement verified on its public page |
|---|---|---|
| [public-apis/public-apis](https://github.com/public-apis/public-apis/blob/master/CONTRIBUTING.md) | Category Finance; name Capital Chronicle; description “Original macro event estimates, market regimes and historical call outcomes”; Auth No; HTTPS Yes; CORS Unknown until observed. Jim submits one contribution after the stable endpoint exists. | Free access or a free tier; documentation; accurate auth/HTTPS/CORS columns; one listing per contribution. It rejects marketing-only entries. Present a usable data source, not an affiliate or newsletter signup page. |
| [APIs.guru](https://apis.guru/add-api) | API name Capital Chronicle; definition format OpenAPI; official definition by owner; category Financial. Jim submits the stable URL of the supplied OpenAPI description. A logo is optional. | It aggregates definitions and does not host the feed or its definition. It requires a stable machine-readable API definition URL. The attached OpenAPI file is prepared material, not an accepted listing. |

The proposed description is under 100 characters. Do not mark CORS Yes merely because a browser opened a file. Test the deployed response header before choosing that directory value. Do not call this an MCP server, trading API or live quote API: the prepared product is one JSON document.

For a four-week feed trial, reuse existing web access statistics if available, excluding our checks and known bots where identifiable. If the host supplies no request logs, record that fact and use voluntary reader confirmations; invent no API-call count or unique-user count. Proposed continuation: three assistants parse the fields correctly and two readers request a refreshed file. A public listing is distribution evidence, not adoption.

## Bound source clocks

- Regime source: Main's completed analysis at 11 November 2026 01:30:37 ET, with data cutoff 00:16:52 ET. Only the explicit TREND_RANGE_20D_5C_V1 tags are projected.
- Event map: retained 10 November 2026 CPI matrix, known at 05:26:54 ET before its 08:30 ET release. It remains that historical forecast after the release.
- Score export: its own observed generated_at_utc is copied into the sample's scores.as_of_utc and converted separately to ET. It does not refresh either of the other sections.

Schema and source-preservation checks are recorded in validation.json. No production service, reader upload, directory submission or public distribution outside the authorized Git delivery was performed.
