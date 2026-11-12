# CC-543: plan alerts before analysis

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

**Remaining cause: NEXT_MAIN_PLAN_NOT_REGISTERED.** The build is installed and wired; the only unfinished acceptance is outside Publisher: Main must naturally register its next plan. Publisher then reads that exact plan's `registered_at_utc`, its coordinator-confirmed Telegram object and the public channel's publication time, writes both clocks here and marks DONE if the observed gap is at most 600 seconds. The new fields in `integration.json` remain null until that observation. No test plan, backdated clock, replacement schedule or old post is used to satisfy it.
