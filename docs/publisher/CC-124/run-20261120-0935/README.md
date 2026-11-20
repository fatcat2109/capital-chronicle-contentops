# CC-124 standing article run, 20 November 2026

**Zero new articles. The standing item is next due at 15:36 GMT+7.**

Main's metals report was timely when the run started. It supported a piece on why silver and gold fell in Asia while the S&P 500 proxy held its range. The live newsroom qualified one article with 35 supported claims and prepared eight social intents. The quote-worker lease stopped release before any public attempt. The article's one-hour window then closed.

| Clock | UTC |
| --- | --- |
| Standing run started | 02:35:44 |
| Main data cutoff | 02:09:04.643687 |
| Main completed its report | 02:33:16.994659 |
| Optional Antigravity assist returned `AGY_TIMEOUT_120S` | 03:06:07 |
| Newsroom qualified the article | 03:08:03 |
| Text approved | 03:08:54.519631 |
| Release returned `NEWSROOM_LEASE_ACTIVE:heavy-news-quotes-minute` | 03:08:56 |
| Substack deadline | 03:09:04.643687 |
| Next standing check | 08:36:00 |

Text approval left about ten seconds in the original publication window. The Antigravity timeout reduced the time available to reach release. Source admission, native returns and the chart proof are in [source-admission.md](source-admission.md). The selection and media plan configured gpt-6.2-sol at low effort. The writer and this Publisher run configured gpt-6.2-sol at max effort. All four configurations are recorded as `CONFIGURED_NOT_OBSERVED`.

## Release fix and readback

Commit `e05ddad2d14220d615d346fa89492e5fefd04732` is pushed and installed in the Publisher operating root. The article release and import checks now let the X quote tick run alongside the newsroom. The quote worker uses its own browser tab group. The coordinator retains exact dispatch identities and recovery checks, and the newsroom still rejects a concurrent editorial window.

The regression reproduced the observed quote-lease error before the fix. Nine focused tests passed on the delivery branch. Twenty-four installed tests passed, including simulated Substack dispatch and readback while the quote lease is active, newsroom-window exclusion and the X quote transport tests. The installed JUnit report is in `Runtime/ContentOps/scratch/cc124-20261120-0935/installed-article-lease-tests.xml`.

The live reader returned `REVIEWED_HANDOFF_REQUIRED` for `cc124-asian-metals-20261120-v1`, with zero dispatches and zero pending native publication requests. The original cutoff now returns `ARTICLE_DATA_CUTOFF_EXPIRED`. The production-day counter showed zero confirmed originals at 03:17 UTC, and Main's latest completed report was still the same metals report. The approved article stays in its original operation for reference.

Installed JUnit SHA-256 df3355b48594bd6136ad1964f16e1b659bef02accaf813d89eb335ba678220eb.
