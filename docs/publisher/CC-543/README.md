# CC-543: plan alerts before analysis

**Live timing acceptance passed on 17 November.** Main registered USD/JPY at **13:28:43.661312 GMT+7**; [Telegram post 188](https://t.me/CapitalChronicle/188) was published at **13:30:01 GMT+7**, a gap of **77.338688 seconds**, within the 600-second limit. The existing installed consumer sent it with its TradingView chart while the analysis page remained unavailable. [Exact readback and bindings](live-plan-readback-20261117.json).

The existing minute consumer composes each new plan-state post from Main's frozen public fields. Its first publication pass sends Telegram and Discord through the existing coordinator before private reply work, page writing, browser publication, scorecards or other destinations. The same outbox identity goes to the other destinations afterwards. No schedule, second publisher or store is added.

The post carries the supplied market, direction, entry zone, invalidation, target, entry deadline and time exit. Public clocks are ET. It preserves the notices and decision 117's position wording. A source-bound TradingView chart is required, with CC-463's identity, scale, rights and attribution checks. This fast path uses the plain TradingView chart rather than CC-465's model-reviewed template, so image review cannot silently reintroduce a model dependency. Missing charts produce no write. Existing issued requests and public objects retain their payloads and recovery paths.

The Substack analysis remains required and uses the existing editorial roles. Once its page is confirmed, the existing link distributor sends its long summary and canonical link as a reply to each confirmed alert. No published post is edited. Discord uses the existing bot reply/thread transport; unavailable bot access is a destination-local cause rather than a second channel-root post.

## The 12 November delay

The gold plan was registered at **20:19:23 GMT+7** (13:19:23.123369Z). The first retained page-writer call ran **20:24:06–20:24:09 GMT+7** and returned exit 1 with an observed usage-limit error. That error occurred earlier than the Web stream limit quoted in the item. `text_call` cached the failed return; the ordinary `run_due` caller did not request an explicit retry. `prepare_social_row` then waited for the unconfirmed page. Seventeen retained status-run records show that same wait from **20:22:20 through 21:27:43 GMT+7**. The two independent causes were a failed, cached page call and the canonical-before-alert dependency. Another stream's available allowance did not establish availability for this page call.

[The bounded diagnosis](delay-cause.json) records the exact source artifact paths, hashes, call clocks and matching ticks. The retained writer later returned at 22:39:33 GMT+7 after an explicit resume, then performed another revision. These observations do not backdate a confirmed page or an alert.

## Verification and operating evidence

- [Original failing replay](replay-red.xml): the retained gold plan produced empty alert text.
- [First passing replay](replay-green.xml): both API destinations confirmed at simulated registration plus one minute, chart attached, with model calls and page/browser publication unavailable; a repeated run created no duplicate.
- [Alert/CLI checks](alerts-and-entry.xml): eight passed. [Reply and distribution checks](replies-and-distribution.xml): 41 passed, including unchanged alert payloads, delayed native portrait, filled/closed updates and the existing per-channel link consumers. A prior broad run had 53 passes and one test-only destination-order assertion; that assertion was corrected and the complete reply check passed in the 41-check run. The original failed run is retained in `consumer-regressions.xml`.
- Top-level launch arguments observed on the resumed process: `gpt-6.1-sol`, effort `max`, **CONFIGURED_NOT_OBSERVED**. The change makes no editorial model call; test transports and page confirmation are controlled fixtures.

The existing minute task has a five-minute execution limit and ignores a second instance. Sending alerts first therefore removes both quota dependence and the old ordering delay within that existing task. This timing argument is distinct from an observed next-plan publication. The code was fast-forwarded into the operating root at **04:52:46 GMT+7 on 13 November** (`d8eea92c63458e896753c07d66a71134b62ad222`). [Installed consumer checks](installed-consumer.xml) passed 24 tests; [boundary and CLI checks](boundaries-and-cli.xml) passed 33. [Integration evidence](integration.json) records all five installed source blob identities and exact file hashes, live tag `contentops-live-20261113-cc543`, and rollback tag `contentops-rollback-20261113-cc543`. Existing unrelated working changes were preserved. No new Main registration or live latency is inferred from a replay.

## Installed tick and remaining live acceptance

The first observed installed `IMMEDIATE_ALERTS` tick was **04:57:40 GMT+7 on 13 November**. At **06:15 GMT+7**, 29 such ticks had completed through the existing scheduled consumer. [Runtime readback](runtime-readback.json) shows no plan registered after integration. The latest Main registration was **00:40:00 GMT+7**, before installation, and is not a valid post-installation latency sample.

The [installed read-only export check](installed-export-read.json) passed the current `2.0.0` export and rendered 78 retained rows, with zero publication or model calls. The [public Telegram readback](telegram-public-readback.json), observed through BrowserOS Neo at **06:16:23 GMT+7**, reaches object 182; those older objects do not prove the new path. Only the public `t.me/s/CapitalChronicle` page was read.

At that 13 November observation, the remaining cause was `NEXT_MAIN_PLAN_NOT_REGISTERED`. The next natural registration and its public clock are now observed below; the corresponding `next_live_*` fields in [integration evidence](integration.json) are populated. The earlier replay and installation records retain their original clocks.

## Live acceptance: 17 November

The source is Main's public export, plan `plan_30f3365059e996b2f0d1d79a`, bound to registration hash `da7f960b2bf777324e08158cff7e9691d401b6296f17c6482e520492f71bb575`. Its frozen alert uses `CC543_V1`. The installed code commit remains an ancestor of the operating root.

| Observation | Time on 17 November, GMT+7 | Gap from registration |
|---|---|---|
| Main `registered_at_utc` | 13:28:43.661312 | — |
| Telegram public `<time datetime>` for post 188 | 13:30:01 | 77.338688 seconds |
| Discord coordinator reconciliation | 13:29:56.943867 | At most 73.282555 seconds |
| Immediate-alert tick, both destinations confirmed | 13:30:02.317785 | 78.656473 seconds |

Telegram's public page was read through BrowserOS Neo at **14:01:26.202 GMT+7**, only at `https://t.me/s/CapitalChronicle?before=189`. Its exact object, text and photo attachment match the stored intent. Browser pixels show the USD/JPY TradingView chart and retained attribution. Both API intents name the same chart asset; its local bytes match the delivery manifest's SHA256. Discord's evidence is the stored coordinator readback, rather than a new browser observation. Dispatch start, reconciliation and public publication clocks remain distinct.

The next recorded page pass returned `ValueError:PLAN_ANALYSIS_RUN_NOT_FOUND`; it did not delay either API alert. A confirmed analysis page and its later reply have not been observed for this plan. The replay covers confirmation followed by replies without editing the first alert. That outstanding page work remains with CC-432 and does not negate this item's live Telegram timing proof.

The [repeated targeted replay](live-readback-replay-20261117-green.xml) passed **7 tests**. Its [first run](live-readback-replay-20261117.xml) had 6 passes and one fixture failure: CC-468's newly added daily Note path was not mocked and reached a temporary store without a `leases` table. The CC-543 test now isolates that unrelated path; publication code is unchanged. Only this test file was run, in one pytest process without workers.

The second Publisher stream pushed the test fix and evidence from operating HEAD `3e73c3151f8594191188573b3591c7c49b17677c` for integration by the first stream. Its readback used no editorial model and made no public, runtime or schedule changes. Its launch arguments were `gpt-6.1-sol` / `max` (`CONFIGURED_NOT_OBSERVED`).

## 18 November operating integration

The first stream merged delivery `5a3770d3c788b3f538407fb3019e415ad94b4783` onto operating HEAD `2712e10669c0ae05733ea5ecb05d6fb22366e986`. The operating fixture already isolates the daily Note path and covers additional ending and recovery cases, so the merge retains it. The [integration replay](integration-replay-20261118.xml) passed 10 checks, including the minute entry point, both API alerts with their chart, and analysis replies after page confirmation. The production alert code was installed on 13 November.

The release refs are `contentops-live-20261118-cc543-live-readback` and `contentops-rollback-20261118-cc543-live-readback`. This run's launch arguments were `gpt-6.2-sol` / `max` (`CONFIGURED_NOT_OBSERVED`).
