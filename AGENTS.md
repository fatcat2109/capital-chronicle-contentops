# Capital Chronicle ContentOps — Root Repository Contract

## CPI night — 10 November 2026 (Ops Product; ends 22:30 GMT+7)

Guardian has been BLOCKED since the gold stop (about 17:20 GMT+7), and Ops Live must replay and bind its
fix on this PC before CPI at 20:30 GMT+7. At the release the entry step uses most of its 45 seconds.

- Until 20:45 GMT+7: no test suite, no install into PrivateApp, no desk rebuild by hand, no copied-state replay.
  Read, write code and drafts, and post what the export already says. CC-338 (the CPI preview with its hash)
  is the one exception, and runs only the tests it needs.
- From 20:45 to 22:30 GMT+7: targeted tests only, at most three files, one run at a time.
- Full suites after 22:30 GMT+7.
- Posts say only what the export says. A gold result that Guardian has not yet recognised is not posted.

## X posts again as before — 10 November 2026 (Jim's decision 112)

Jim, 10 Nov 2026: "Cứ đăng X như cũ, không thay đổi gì." (keep posting to X as before, change nothing),
and in Ops Product's chat: "Rủi ro Jim chấp nhận: luật của X cấm đăng tự động qua trình duyệt và
nêu mức phạt là khóa tài khoản vĩnh viễn." He takes the risk that X's rules name.

This overrides, for X only, the X parts of the three sections below: X's place in
`NON_API_AUTOMATION_PROHIBITED`, X's removal from the required set, and the retirement
of X's Neo probes, readbacks, agent requests and the status posts' X flags. CC-431
restores them, tested, as they were before 10 Nov 00:36Z. Until CC-431 is live the code
still records X as not posted; never work around it by hand in a browser.

What stands: replies stay parked (CC-386); LinkedIn company, YouTube Community and
Instagram browser edits stay barred (CC-393). The X list feed (CC-258) keeps running.

## Required derivatives and public notice — 10 November 2026 (CC-395; decision 109)

Ops Product's CC-395 amendment, 10 November 09:11 GMT+7, makes the current required
set six: Telegram, Discord, LinkedIn member, Facebook Page, Instagram Business and
Threads. Derive this set from `NON_API_AUTOMATION_PROHIBITED` and each registered
transport; a browser prohibition never excludes a supported official API.
X and YouTube are each recorded once as not posted with their platform-specific
`NON_API_AUTOMATION_PROHIBITED` cause, without retry or incident. Existing confirmed
identities and uncertain attempts stay preserved. Their Neo probes/readbacks and
agent requests are retired; outstanding uncertainty requires an allowed API or
person readback. The status posts' X agent flags are retired.

New public pieces, cards and pages carrying the notice use: **Capital Chronicle
offers analysis only, not financial advice or recommendations.** Historical posted
objects and frozen requests retain their exact wording and hashes. Bio/about changes
belong to Ops Product; the read-only inventory is `docs/publisher/CC-395/bios.md`.

## Platform automation restrictions — 10 November 2026 (CC-393; decision 109)

The platforms' own rules bind. LinkedIn member/company posts and edits, YouTube
Community posts and edits, and Instagram browser edits now join X in the existing
`NON_API_AUTOMATION_PROHIBITED` map. Never bypass it with direct browser actions,
another browser, a private endpoint or an old queued request. Use the already
authorized official APIs where supported. Company LinkedIn API access and X API
posting are not enabled by this review. An earlier attempted write still requires
exact readback/reconciliation; a new prohibition does not prove it was not sent.

The source review and five rule dimensions for every route are in
`docs/publisher/CC-393/platform-rules.json`. Substack's bounded logged-in publishing
route continues: a blanket posting-automation ban was not found; its scraping and
spam prohibitions remain. Do not treat a searched absence as express permission.

CC-258's specific Ops Product instruction keeps the X browser feed through CPI on
10 November, with its replacement or stop assigned to Ops Product on 11 November.
CC-393 records that method's conflict with X rules and changes no feed process,
Main input or schedule today. Retained archives keep their existing internal use.
Ops Product's candidate-channel pick remains its own backlog decision.

## No posting on X through a browser — 10 November 2026 (Jim's scan answers, item 3)

X's developer guidelines and automation rules say non-API automation, meaning scripting or driving the
website in a browser, "results in permanent suspension" (read 9 Nov 2026; Tower
`fork_weakness_scan_20261110/evidence/W_TERMS_AND_VIETNAM_RULES.md`, section 2, and
`docs/publisher/CC-386/platform-rules.json`). Jim's answer: X's own rules bind, and automated replies are
not used. So no agent posts, replies, quotes, edits, likes or follows on x.com through BrowserOS Neo,
Chrome, CDP or any other browser, for any item. The coordinator records every X write as a definite
no-write, `X_NON_API_AUTOMATION_PROHIBITED`, before any request reaches a browser. Count X as not posted
and go on with the other destinations; never work around it by hand in a browser. X returns only through
X's official API, by a BACKLOG item.

## Temporary weekend load — 7–8 November 2026 (decision 94)

Until 9 November 01:00 GMT+7, CC-124 checks every twelve hours and publishes
at most one article per existing production day, only from a new Main report.
The existing publisher and day read model apply the temporary one-article cap;
the normal decision-93 ceiling of two returns at that reset. No schedule change
is part of CC-333. Status posts keep their separate contract. The retained NFP
operation and frozen native request remain available for the next due CC-124 run.

## Fewer pieces, new images and scenarios — 6 November 2026 (CC-333; decision 93)

At most two articles per existing newsroom production day, including event pieces.
CC-124's standing cadence is six hours; this changes no schedule in an item run.
This supersedes older 5–8/day targets and no-image exceptions for new publication.
The existing coordinator requires a content image never published in another piece,
checking exact SHA256 and perceptual hashes in `published_images_v1.jsonl` beside
the publication feed. The same article distributes its images to its social copies.
Six-market pieces set `article.market_asset` before media binding/registration and
lead with a fresh CC-316 TradingView snapshot; release pieces keep their release
card first and add the relevant snapshot. Other pieces use their own data chart
or an unused lawful photo. Never reuse the Fed building or Capitol photographs.
Use the existing media binding owner to capture/refresh before review; preserve
TradingView's full attribution, free-public-page rights and image bytes.

Every article carries a Scenarios section with 2–3 Main-sourced scenarios: labelled
model-estimate probability, confirmation, six-market implications and invalidation.
Supply `article.scenario_analysis` with exact source bindings and two authored
`article.social_scenarios` lines (base case and main alternative). The existing
eight-channel compiler carries both lines to social copy. Do not invent missing
probabilities or derive an unsupported complement. Search held full Main reports
and dossiers before naming a gap. Decisions 40, 84 and 90 still apply. Status
posts and digest link indexes retain their separate existing contracts. Historical
objects and frozen requests stay immutable; readback/reconciliation stays available.

## Publication speed — 3 November 2026 (CC-172; Jim's decisions 53 and 54)

Dispatch every applicable channel within 15 minutes of approved text. Preserve the first
approval clock for unchanged text; media work never restarts it. Time-sensitive release,
event and market pieces use writer -> one editor check -> publish. After text approval,
per-channel screenshots, draft reviews and visual-repair loops are replaced by one automated
image load/dimension check; log its failures and continue. Long pieces retain their full
visual work before text approval. At most one visual repair round; drop still-failing
assets with an internal note and retain passing visuals. Photo credits come from the media
record at selection. These newer instructions supersede conflicting visual-review wording
below; source, rights, fact, identity, KILL_SWITCH and UNKNOWN_WRITE checks remain.

Keep screenshots binary; never commit or print image base64. Upload only through Neo's
upload tool or file-chooser interception, from the article's own media folder. Never open a
native file dialog; if one opens, record NATIVE_FILE_DIALOG_OPEN and stop that step.
Before Substack Publish, use the one existing Neo window and the task's tab group
(Jim's decisions 63 and 74), with the draft only. Keep the draft tab open and in front. Open Gmail
only when Substack shows "Check your email", never before: a web-only publish that asks for no code leaves Gmail
closed. Agents never read Gmail: no snapshot, read, grep, evaluate or screenshot of it, and nothing from it in any
result or message. On the dialog, record PENDING_JIM_EMAIL_CODE plus page id and URL in the item's Result, then open
Gmail in one new tab of the task's group by a run script that returns only the page id (not tabs action=new, whose
reply carries a snapshot), and wait on the code tab for Jim: no reload, other input or other tab use. Continue readback only when the same tab
reaches /publish/posts/detail/.../share-center. Never close, reuse or navigate the code tab.
Telegram is read only on the public channel page https://t.me/s/CapitalChronicle, with no sign-in, for every
readback (presence or absence). Agents never open, snapshot, read, grep, evaluate or screenshot Telegram Web or any
signed-in Telegram view: BrowserOS is signed in there to Jim's personal account (Ops Product, 5 Nov; same reasoning as
the Gmail rule). Nothing from it goes into any result or message.
No post on social media or Substack links to the preview site or any other host until Capital Chronicle owns its
own domain (Jim's decision 83, 5 Nov; after that, only that domain). Never put fatcat2109.github.io,
capital-chronicle-preview, any *.github.io, pages.dev, workers.dev, netlify.app or vercel.app address, or the word
fatcat2109, in any post text, link, Substack body or profile. A social copy links the confirmed Substack post or
nothing; a status post carries no link. Every write path refuses such a copy with PREVIEW_HOST_LINK_FORBIDDEN
(`live_contentops/preview_link_guard_v1.py`): never work around it.

## Public dates and times — 6 November 2026 (CC-326; Jim's decision 90)

Every new public article, social copy, card, digest and dated line uses New York time
(`America/New_York`, including daylight saving), written **ET**. Convert the supplied
instant before choosing its public date. Date-only source periods stay date-only.
Never put GMT+7, UTC+7, Bangkok time or Vietnam time in public copy. TradingView's own
snapshot header stays as supplied. Already-published posts are not edited for this rule.
Messages to Jim stay GMT+7; records stay UTC and internal schedules do not change.
The final payload checks in `live_contentops/public_time_v1.py` apply before a new write.

## Scheduled terminal-window reporting (CC-238, 5 Nov 2026)

A window runs the newsroom CLI and follows this file. It saves its terminal whole-window result through the existing
window/result outbox and messages no other chat or thread: the L2 ContentOps thread is retired, and the result
store is what Ops and Jim read. A window that cannot reach its terminal result in its turn saves one BLOCKED result
with the stage, the pending request and the first cause. Aggregate eligible candidates and slots first; a candidate
HOLD alone is not window completion. Guarded NOT_YET_EFFECTIVE, stale or duplicate, partial, unfinished-child,
unchanged-progress and quota-interrupted callbacks save no completion result. No retry loop, ledger, notifier,
scheduler or watcher is added. Report the exact identities, outcome, distinct canonicals and channel states,
first cause, artifact and next action, with Jim-facing times in GMT+7. Issued bindings, policies, budgets,
calendars, models, rights, publication semantics and the 30 October brief date guard stay.

## CO-4 private-use permission and scoped runtime application — 29 October 2026

L1 batch L1-B-20261029-07 supersedes the batch06 no-additional-J7 hold for the existing
CapitalChronicle_ContentOps_V1_Daily_App_Runtime only. Necessary restarts use its existing
task/launcher, fresh process identity, no V1 window within 30 minutes, and zero active work,
pending outbox or UNKNOWN_WRITE; read back port 8765, actual source and reconciliation.
The existing rights/export owners apply JIM_X_LIST_PRIVATE_MAIN_RESEARCH_USE_20261029 to
exact retained X-list CDP records captured from 26 October onward, including future rows,
for internal_research and narrative_context only. This is owner-authorized private use,
not an external licence, public/subscriber reuse, training, third-party sharing or event
confirmation. Preserve original identities/clocks and takedowns; one normal intake must
prove the stable export refresh. Tonight's windows and the 30 October policy boundary stay.

## Compatible early installation — L1 batch 06, 29 October 2026

Batch L1-B-20261029-06 supersedes the earlier requirement to wait until 02:00 to install source.
Install compatible source now after the focused old-window comparison; preserve tonight's four
full prompt/calendar/rollout identities, old binding limits and publication semantics. The dated
policy still starts only with the 30 October production day. Resume the three existing brief App
entries with the executable NOT_YET_EFFECTIVE guard before any source/model/public work. Runtime
application follows the later batch07 scope above; no activation watcher is authorized. CO-4 uses the existing intake/export/source-rights
owners and one stable governed projection; list membership never grants rights. Keep actual
installed source, running process source, first real brief and live export cadence separate.

## Dated V1 volume direction — 29 October 2026

The [next-production-day volume amendment](docs/automation/CONTENTOPS_V1_NEXT_PRODUCTION_DAY_VOLUME_V1.md) is current for new operations from production day 30 October. It supersedes earlier three-admission/six-request/one-article and conditional J8/J10 limits only in that dated scope. Tonight's four full windows, old bindings and exhausted editions stay unchanged. Use six admissions, one shared ten-request non-chargeable cap, actual candidate fallback, two canonical articles per full window, photo-less NEWS/POLICY with Instagram skipped, and capped existing-App brief windows. Same native roles, final MAX review, sole publisher, rights and UNKNOWN_WRITE recovery remain. Stage source now; apply at the day boundary. V2/V3 stay paused.

## Native role results and terminal outcomes — 29 October 2026

The native result rule replaces the rejected ancestor-callback route. Follow [the native result rule](docs/automation/CONTENTOPS_BUILDER_SUBAGENT_COMPLETION_HANDOFF_RULE_V1.md). Luna, Light and MAX are roles inside the same operation: collect their supported native final return or saved artifact and continue the active pipeline. Never instruct a child to message its ancestor, pause merely for an own native role, or build a relay, watcher or schedule around platform limits. Preserve true paused/quota state and report any exact unsupported-return gap.
Terminal pre-writer HOLD, SOURCE_BLOCKED, REJECT and NO_STORY require zero media and retain their first source/editorial/rights/staleness/process cause. Instagram media readiness belongs to its destination; it cannot block an editorial refusal or an otherwise compatible channel. Articles proceeding to publication carry a lawful photo when one exists (a missing photo never holds a piece: decisions 41 and 61), the same-MAX final rendered review and the sole canonical-first publisher. Conditional J8/J10 are not active blanket exceptions.

## Reader attribution and public time — 28 October 2026

Jim's [reader policy](docs/automation/CONTENTOPS_V1_READER_ATTRIBUTION_AND_TIMEZONE_POLICY_V1.md) is current: omit discretionary Sources/References lists, repeated citation links and ritual cutoff footers by default. Retain natural claim/relay attribution and uncertainty, actual mandatory quotation/photo/reuse credit and meaningful chart metric/unit/period/context. Useful exact public times use America/New_York with date-correct EDT/EST, or UTC; omit unnecessary exact-time footers. Internal source/claim/rights/UTC/cutoff history and Asia/Bangkok production calendars stay unchanged. Apply through writer/compiler/read owners; the SAME MAX writer inspects affected revisions before a send or exact-object edit. Historical packages/exports remain immutable; formatting never refreshes a story.


## Canonical photo attribution — 28 October 2026

Jim's direct current instruction keeps full photo creator/source/license attribution on
the canonical Substack article. Derivative platforms carry the canonical link and any
material archive/context caption, without repeated photo source/credit blocks where the
actual admitted licence permits linked attribution. Internal source/rights/date/alt and
exact original bytes remain bound; chart sources and factual-report attribution remain.
Apply through existing compiler/renderer/coordinator owners, preserving immutable sent
packages and exact public identities. Already-confirmed objects use exact-message edits,
never reposts. Changed presentation requires the SAME designated MAX writer's affected
desktop/mobile inspection before fresh sends or edits. No additional reuse rights,
publication owner, schedule, store, model/API spending or V2/V3 authority is created.

## Permanent final-media review and direct repair — 27 October 2026

Jim's actual messages01a17b8c-11a4-78b0-8686-d3ca0b1bcb6a,01a17b92-5b16-7a02-92d2-39c33c9df307 and01a17b94-5870-7402-9f46-c736f10052fe were verified via read_thread in assigned L2. The [permanent final-product rule](docs/automation/CONTENTOPS_V1_FINAL_MEDIA_REVIEW_AND_REPAIR_RULE_V1.md) is mandatory for every V1 article and material revision.
After final assembly the SAME actual designated strongest native editor/writer, currently gpt-6.1-sol/max, inspects the exact rendered canonical/channel desktop/mobile pixels and source-bound visual meaning, then directly repairs concrete defects, re-renders affected outputs and checks the correction. Preserve valid article/intake/returns/assets; no discard or restart; at most one repair round, then drop a still-failing asset and keep the passing ones (decision 53, CC-172). Missing external source/rights/access remains an exact resumable affected-article constraint.
Existing native request/return and article-review owners bind actual model/effort/invocation, article/media/render revision and findings. The sole publisher rejects missing/stale/wrong-model acceptance or unresolved material issues before a fresh send; UNKNOWN_WRITE recovery remains readback-first. Planning/settings/tests do not prove inspection. Later approved stronger models may replace the active editorial assignment consistently; the review-and-repair obligation is permanent. V2/V3 remain paused.


## Current V1 execution override — 2 November 2026 (Jim's decision 39)

Jim's decision 39 (Tower `docs/project_control_tower/JIM_DECISIONS_20261030.md`, 2 Nov 2026, 23:10 GMT+7) removes newsroom red tape. It adds to the 27 October grant below and wins where they differ.
- Before this window's own edition, publish the promoted CC-074 FOMC retrospective, operation `cc074-retro-fomc-20261028-v1`, once. Jim authorized its publication (decisions 36, 37 B1 and 39), and Ops integrated and applied its promotion (tag `contentops-live-20261102-cc074`). Run `python scripts/run_native_desktop_editorial.py publication-resume --binding "A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc074-retro-fomc-20261028-v1\binding.json" --rollout config/native_desktop_rollout_v1.json --native-invocation-id "<your actual turn id>"`. Complete each native Neo request it returns (publication-tool-begin, the BrowserOS Neo action, publication-tool-submit), then resume again, until the canonical Substack article and its derivatives are read back. Check with `publication-status`. If it is already published, only read back.
- A confirmed or source-qualified short news brief is never held because it cannot support 2-5 charts or has no image. It goes out with the charts it has, or as text; only a channel that needs an image (Instagram) is skipped.
- Jim's decision 41 (3 Nov 2026) narrows that line to briefs. An analysis piece on a data release or policy decision (CPI, NFP, PPI, GDP, PCE, the Fed and the like) carries charts built from official history: the headline and core trend over at least 24 months, the latest month's change, and a component breakdown where the release has one. It also carries a contextual image when a public-domain or licensed one exists. When the history is missing, fetch it from the official publisher (BLS public data is public domain) or from Main's first-print archives. Never cite decision 39 to drop the charts from analysis.
- Jim's decisions 42 and 44 (3 Nov 2026):
  - Every post carries a visual: charts, or at least a data card of its own facts, plus a lawful photo when one exists.
  - Private surveys (ISM, S&P Global PMI, Conference Board, UMich, ADP) appear only as an attributed headline figure, for example "ISM manufacturing PMI 48.7 (ISM)", never as tables, charts or history.
  - A single consensus figure may be quoted with attribution; there is no systematic consensus display.
  - Charts use public-domain official series (BLS, BEA, the Fed, Treasury) and the desk's own work.
- A window never ends with admitted stories, 0 source requests and 0 posts: request the sources it is allowed, or move to the next admitted story.
- Unchanged: decision 35 (market reactions only, no position calls), the public-output guard, the KILL_SWITCH, identity and readback rules, and UNKNOWN_WRITE recovery.

## Current V1 execution override — 27 October 2026

Jim's direct operator/owner grant in L2 turn `01a17b6b-6a34-7d72-b76b-2b87223edd69`, human message `01a17b6c-ac16-70d0-bea6-d2a6ca82412b`, authorizes actual V1 publication after cleanup and an immediate native run without waiting until17:00. The human grant and completed cleanup turn `01a17b69-2f65-7612-bb69-5c2277f60843` were read through read_thread. No further Jim review is required for this scope.
The previous SHADOW_ONLY/version37/public_write_authority=false state is the pre-application baseline. Apply and read back the existing control/rollout owners; [actual application](docs/automation/CONTENTOPS_V1_RELEASE_CONVERGENCE_V1/ACTIVATION.md) records actual application separately from authorization. The same four App calendars remain ACTIVE, using native Luna MAX filtering, Sol6.1 Light planning and the same Sol6.1 MAX visual editor/writer.
Fresh current owner-manual or scheduled operations may publish through the sole DurablePublicationCoordinator with exact identity, source/media rights, current review and canonical-first readback. Pre-activation private examples and owner-removed historical objects are not a launch sample or retry queue. Cleanup reported both Substack Published lists empty; drafts and Discord pinned guidance remain. Deliberately removed capitalnicle.substack.com Privacy Policy/Terms are not silently restored.
Preserve stable bindings/cutoffs, ordinary source budgets, existing store/outbox/leases and UNKNOWN_WRITE recovery. Missing access is destination-local. No fifth task, replacement scheduler/store/publisher, paid API model, CUA or V2/V3 resumption is authorized. V2/V3 stay paused. One live edition does not prove daily5–8 reliability, SEO or growth.
Older zero-public-write and missing-activation-grant wording below records superseded V1 epochs and cannot block this exact newer grant. Actual applied controls and exact public-object readbacks remain required evidence.

Authority date: 2026-10-20
Status: `CURRENT_ROOT_AUTHORITY`
Repository: `fatcat2109/capital-chronicle-contentops`

## 1. Mandatory current read path

For every current implementation, audit, task framing, or owner decision, read in this order:

1. `AGENTS.md`
2. `docs/codegraph/INDEX.md`
3. `docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md`
4. `docs/automation/CONTENTOPS_CURRENT_STALE_DOCS_MANIFEST_V1.md`
5. `docs/automation/CONTENTOPS_CAPABILITY_ROUTED_HYBRID_EXECUTION_POLICY_V1.md`
6. `docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md`
7. `docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md`
8. `docs/automation/CONTENTOPS_V1_POST_ACCEPTANCE_ACTIVATION_AUTHORITY_V1.md` for current V1 activation
9. `docs/automation/CONTENTOPS_NATIVE_DESKTOP_EDITORIAL_RUNTIME_V1.md` for current editorial mechanics
10. `docs/codegraph/V1_CONTEXT.md` or `docs/codegraph/V2_CONTEXT.md`
11. current lane pointer
12. nearest scoped `AGENTS.md`
13. exact current implementation/tests/evidence.

Do not route from historical task evidence, stale handoffs, generated status snapshots, task branches, or chat SHAs.

## 2. Authority order

Product authority:

1. Jim's latest explicit instruction;
2. this root contract plus the current root North Star/Master Plan and current post-acceptance V1 activation authority;
3. current authority map and lane pointer;
4. older detailed plans/history.

Repository/evidence authority:

1. fresh remote refs/commits/diffs/exact bytes;
2. exact implementation, focused tests, accepted evidence, exact-head CI where applicable;
3. runtime/host/browser evidence for facts only execution can prove;
4. historical docs/project sources/chat.

Newer owner direction wins.

## 3. Current owner state

Jim's current explicit decisions establish:

- `V1_FINAL_PRODUCT_ACCEPTED = TRUE`;
- routine V1 public-write/readback authority is granted for the accepted V1 path;
- pre-migration deployed V1 used `SIMPLE_GEMINI_RUNTIME`; current paused target is `NATIVE_CODEX_DESKTOP` as defined in section 5;
- `DurablePublicationCoordinator` remains the sole public-write/readback owner;
- V2 public-write authority remains zero unless separately granted;
- product progress is `BUILD -> RUN -> OBSERVE REAL FAILURES -> FIX`; ceremony or safety architecture is not a prerequisite unless a real failure or irreversible-risk boundary requires it.

The current protected/deployed V1 epoch before the browser-source architecture detour is PR #53 merge commit:

`1c0354347e51d7b84bd7e41386d7bf428709e4bf`

This epoch includes the accepted PR #51/#52/#53 runtime/intake/sourceability/output-starvation repairs.

Any subordinate current-looking wording that still says routine V1 public-write/readback is ungranted, V1 acceptance is pending, or activation has not happened is superseded.

## 4. Locked V1 product contract

Final operating target:

`5–8 PUBLISHED ARTICLES per newsroom production day`

No filler. Candidate-level abstention is allowed. Whole-day deficit is not healthy success. A below-target live day without an exact hard external blocker is:

`DEGRADED_DAILY_OUTPUT_DEFICIT`

The historical zero-write 4/32 benchmark remains telemetry/economics evidence only:

`4 QUALIFIED ZERO-PUBLIC-WRITE ARTICLES / 32 DERIVATIVE INTENTS`

It is not a prerequisite for advancing one safe article or for the already-granted V1 product acceptance.

Routine windows remain 17:00, 21:00, 23:00, and following 01:00 Asia/Bangkok under one deterministic production day. Do not create a fifth routine task merely to chase quota.

## 5. Current V1 editorial architecture

Routine V1 target ownership is `NATIVE_CODEX_DESKTOP`, with the owner-approved three-stage method:
Luna/Terra MAX filters X headlines; `gpt-6.1-sol / low` (Light) selects content and prepares data;
`gpt-6.1-sol / max` writes the article and SEO/house-style package, including a bounded useful revision.
Read `docs/automation/CONTENTOPS_NATIVE_DESKTOP_EDITORIAL_ROLE_POLICY_V2.md` for exact role,
source/tool, style and checkpoint rules. This target supersedes the earlier Sol-low-only method;
the Goal24 isolated proof remains evidence for its older configuration, not this complete pipeline.
Reuse MainReportFeed/current intake, canonical publication memory, reviewed retained research,
evolving story/revision context, <=32 candidates, <=3 admissions and <=6 source requests.
Existing source/claim/epistemic checks and the native eight-channel compiler remain authoritative.
There is no Gemini/9Router, SDK/App-Server, headless or paid API model fallback.

The existing four App tasks own routine scheduling; existing window/day/slot IDs, bounded
catch-up, store/outbox/lease and sole DurablePublicationCoordinator are reused. Legacy Simple
scheduler/start paths are non-routing in target source. Bulk X CDP ingestion remains unchanged;
Neo is the browser path for research and prepared browser-only destination handoffs. Existing
Telegram/Discord/Meta/Threads/LinkedIn API transports remain channel-specific.

Historical pre-live application: **DEPLOYED_SCHEDULED_ZERO_WRITE**, applied 26 October 2026; superseded for new V1 sends by the27October grant above.
The four existing host tasks are ACTIVE with the native editorial roles; the original production
store is SHADOW_ONLY/version37 and rollout public_write_authority=false. The operator fuse is released.
PR90/PR92/PR93 are merged; the existing Task Scheduler-owned FDA-G runtime uses release cbfa1e8f.
These are dated application facts, not permanent liveness or daily-output proof. Resume an existing
scheduled binding and its frozen requests after interruption; do not recreate its operation or cutoff.
V1 publication follows the27October live grant above; V2/V3 remain paused. See the current execution override above and
`docs/automation/CONTENTOPS_NATIVE_DESKTOP_EDITORIAL_RUNTIME_V1.md` for the existing mechanics.


## 6. Historical accepted foundation (2026-09-01 provenance)

Reuse, do not rebuild:

- accepted PR #37 Editorial Growth Edge and epistemic-state logic;
- current Simple article path and native exactly-eight compiler;
- four-window Simple scheduling mechanics;
- single-owner composition with `SIMPLE_GEMINI_RUNTIME` as sole routine editorial owner;
- durable V1 store;
- destination registry;
- `DurablePublicationCoordinator` as the sole public-write/readback owner;
- canonical Substack-first transports;
- strict readback/reconciliation and UNKNOWN-write recovery;
- persistent scheduler ownership from PR #51;
- production-day distinct SOURCE_BLOCKED candidate walking from PR #52;
- persistent Daily App intake/state/API ownership, governed source-reachability correction, relay attribution normalization, and unconfirmed derivative correction from PR #53.

Current protected/deployed source before the architecture detour:

`1c0354347e51d7b84bd7e41386d7bf428709e4bf`

Confirmed product truth:

- one current V1 lifecycle has already completed canonical Substack plus exactly eight durable-confirmed derivatives;
- routine mode has been activated as `AUTONOMOUS_DEFAULT`;
- one natural production day then reproduced `AUTOMATION_RUNNING_BUT_OUTPUT_STARVED`: 17:00 and 21:00 were missed by the old detached scheduler-liveness defect, while 23:00 and 01:00 executed but produced zero new articles under `ALL_ADMITTED_CANDIDATES_SOURCE_RETRIEVAL_BLOCKED`;
- PR #51 repaired persistent scheduler ownership and source-route health carry-forward;
- PR #52 repaired repeated selection of candidates already proven SOURCE_BLOCKED in the same production day;
- PR #53 proved the continuous intake had been stale, restored durable intake ownership, corrected sourceability around the existing canonical-X zero-GET relay route, improved route-diverse selection, and fixed deterministic downstream relay-attribution / unconfirmed-derivative defects;
- after PR #53, a real current candidate crossed the previously universal source-retrieval blocker, reached `SOURCE_QUALIFIED` with one accepted source and zero GETs, passed deterministic article validation, and compiled exactly 8/8 derivative packages;
- a later stochastic writer replay failed closed at `claim_fields_invalid`; this is not a publication success and was not converted into filler;
- PR #53 exact-head CI and focused/expanded regressions passed;
- current V1 is therefore repaired and healthy-idle, but `5–8/day` reliability is NOT runtime-proven and no natural routine opportunity has yet proven the PR #53 epoch can convert fresh intake into routine public output.

The historical Substack object `213355736` was later reconciled by an external actor to the same object. PR #53 did not retry, publish, or mutate the incident as part of that reconciliation. Historical ambiguity must not be rewritten as ContentOps production proof.

## 7. ContentOps/Core Analyzer boundary

Capital Chronicle/Core Analyzer owns proprietary calculations, probabilities, scenarios, forecasts, regimes, decisions, paper records, realized-outcome attribution, and other analytical/numeric truth.

ContentOps owns discovery, grounded research, story selection, writing, SEO, media, distribution, readback/reconciliation, observation, growth, and bounded learning.

No external report or model output gains Capital Chronicle proprietary numeric/forecast/probability/scenario/regime/valuation/decision authority.

## 8. Editorial and epistemic rules

V1 preserves eight modes:

- `BREAKING_BRIEF`
- `FOLLOW_UP_UPDATE`
- `STANDARD_NEWS_ANALYSIS`
- `CAPITAL_CHRONICLE_VIEW`
- `WHAT_THE_MARKET_IS_MISSING`
- `EVERGREEN_EXPLAINER`
- `DATA_OR_DOCUMENT_LENS`
- `WEEK_AHEAD_OR_WATCH`

Report truth and underlying event truth are separate. Official confirmation is not a universal prerequisite for a narrow attributed reputable report. Reader-visible uncertainty must survive canonical copy and all derivatives. A derivative may compress wording, never certainty.

Strong evidence-backed criticism/contrarian framing is allowed. Fabricated outrage, unsupported allegations, and filler are not.

## 9. Publication/recovery boundaries

Substack is canonical. The eight derivative destinations are Telegram, Discord, X, LinkedIn, Facebook Page, Instagram Business, Threads, and YouTube Community.

A counted published article requires exact canonical identity/readback under the accepted coordinator contract. Derivatives must use the real reconciled canonical `/p/...` URL, never a pending placeholder.

`UNKNOWN_WRITE = STOP RETRY -> READ BACK -> RECONCILE`

Chrome `CapitalChronicleBot` CDP 9222 remains bulk ingestion only. Target browser path is Neo; Edge CDP 9223 is historical deployment provenance, not automatic transport fallback.

Do not replace the current production publication/browser ownership merely because a new browser-agent abstraction is being evaluated. Any later transport change must be justified by product evidence and must preserve exact identity/readback/reconciliation truth.

## 10. Execution framework

Use `CAPABILITY_ROUTED_HYBRID`:

- `WEB_STATIC`: repo-static reasoning/authority/docs/GitHub operations;
- `WEB_CI`: bounded deterministic implementation provable by CI;
- `CODEX_EXECUTION`: real runtime/Windows/browser/stateful/debug evidence;
- `OWNER_GATED_EXTERNAL`: secrets/session, destructive canonical mutation, material numeric-authority change, V2 public-write expansion, or external/legal/rights release decisions.

Jim has already granted routine V1 public-write/readback authority. That grant remains subject to exact account/identity/readiness/reconciliation truth at the live write boundary.

Use the cheapest lane that can produce evidence strong enough for the claim.

## 11. Locked current sequence

1. Reuse merged PR90/PR92/PR93, the applied native runtime and the existing Task Scheduler-owned FDA-G lifetime.
2. Resume existing frozen scheduled requests through Luna MAX filtering, Sol6.1/low selection/preparation and the same Sol6.1/MAX editor/writer; preserve operation identity and cutoff.
3. Keep only the four existing ACTIVE windows, original store/outbox/lease and sole publisher; apply/read back the27October authorized live operating mode and rollout.
4. Complete authorized current editorial work and reviewed live sends without another Jim review. Preserve truthful source/rights/access gaps and actual native-return evidence.
5. Record actual useful/held outcomes, exact public URLs/readbacks and interruptions; daily5–8published reliability remains separately unproven.

No production activation, public write, pause release, self-merge or deployment is part of Goal25.


## 12. Change discipline

Prefer bounded product slices over ceremony. Do not rebuild proven systems simply because they are not freshly revalidated.

Ordinary reversible repository operations inside the accepted roadmap do not require a new per-operation owner authorization after the operator hard-gate audit has passed. They may use task branches/PRs and the normal protected-branch path once required checks pass.

This repository autonomy does not authorize bypassing branch protection, force-push, public/provider writes outside the already-granted V1 scope, destructive production/canonical-store mutation, Capital Chronicle proprietary/numeric-authority expansion, V2 public-write authority expansion, secrets/session exposure, protected-history mutation, or blind duplicate public writes.

Stage explicit paths only. Never `git add .` or `git add -A`.

## 13. Hard stops

Stop on:

- secret/session/token/cookie/private-key exposure;
- fabricated facts or Core Analyzer truth;
- wrong-account or out-of-scope public write;
- destructive production-store/upstream mutation;
- blind duplicate public write under known ambiguity;
- irreconcilable ref conflict;
- silent creation of a second scheduler/store/publisher/coordinator/authority owner.

Do not stop for historical noise, stale docs, unrelated dirty files, absent CI, pre-existing failures, deployment-proof ceremony, or reversible mechanics.

Protected historical `v1.0` remains immutable at `6983bfb3ef300414b744f3f8f97ca81ff699348b`.

## 14. Visual/media acceptance

UI/video/audio PASS requires actual rendered artifact inspection. Tests and worker judgment prove mechanics, not final viewer-facing quality.

## 15. Signal Clips product adoption — 2026-10-23

ContentOps has three product lanes: V1 original newsroom/articles, V2 original analytical
video, and V3 **Capital Chronicle Signal Clips** for authentic speech excerpts. The V3 in
the root North Star/Master Plan filenames is a document revision, not this lane's readiness.
Read their current Signal Clips sections and the existing Lightweight Speech Highlight
Relay pointer/scoped instructions before V3 work. Reuse the existing relay and media
owners. Preserve the frozen retained mode; current-source engineering is a deliberate
compatible extension, not permission to relabel its evidence. Video upload, draft and
public-write authority remain zero. One L2 integrator reserves shared policy/CLI/schema/UI;
Builders own only their admitted paths. V1 zero-write runtime and four windows follow the current execution override above; V2/V3 stay paused.

## Editorial media and data release standard — 2026-10-24

Jim's CONTENTOPS_V1_READER_FIRST_DATA_JOURNALISM_V1 correction supersedes the blanket one-chart rule. Analysis of a data release or policy decision carries charts built from official history (decision 41); other analysis uses the charts the actual native Sol6.1 MAX editor finds useful for the argument, or none, marked analysis_scope OTHER_ANALYSIS with a reason. Use adequate comparable primary data or lawful original-source charts. A genuine news/policy story may use zero charts only when that same editor records a substantive reason internally; never relabel analysis, pad near-identical panels or expose a gap banner. A relevant lawful photograph is used when one exists and never holds a piece; all source/rights/identity/date bindings remain required. Chart count, complexity and model scores certify no explanatory value. Old proofs remain dated history, not current owner acceptance.

Use the existing native flow: story/evidence/data/visual plan -> bounded Neo/source discovery and exact lawful original -> deterministic admitted-data chart -> actual Sol6.1 MAX writing/SEO and bounded same-writer revision -> canonical and eight appropriate previews -> exact revision-bound review/preparation -> sole existing publisher/recovery. Luna MAX filters only genuine X input; Sol6.1 Light plans; Sol6.1 MAX owns prose. Photos have separate source/license/date/attribution/caption/alt and inspected-pixel bindings. Archive context is labelled and never counted as factual corroboration. Charts retain metric/series, unit/currency, period, actual/estimate/forecast, missingness, source and transformation identity. No fabricated history, interpolation, copied proprietary chart or proxy/numeric-authority drift.

An explicitly requested editorial refinement of unchanged retained facts uses the existing source/history owner with EDITORIAL_REVISION, exact prior article/source hashes and no new factual-evidence claim. It does not constitute fresh news or proof of daily throughput. New preparation and public sends must meet the current standard; an old UNKNOWN_WRITE still requires exact readback/reconciliation without retry. Source/copy/media changes invalidate the corresponding prepared review. Actual rendered desktop/mobile canonical and derivative inspection remains required.

V1 is the sole active product priority. V2 and V3 work remain owner-paused until final V1 actually operates live daily; no video/speech dependency or work is authorized by this standard. The four existing Automations remain ACTIVE; V1 live controls/publication follow the27October override above, with actual applied state in ACTIVATION.md. The media standard grants no additional platform draft/upload/post, spending, video resumption or new store/scheduler/publisher authority. Historical acceptance and native daily-live proof remain distinct.

Native Sol6.1 Light prepares exact evidence/data and visual proposals; the same actual native gpt-6.1-sol/MAX writer decides data, chart types/count/placement and any justified exception, then authors/refines the article. Code owns acquisition/computation/rendering/state. No canned menu, copied proprietary chart, fabricated history/expectations or later information passed off as known earlier. Primary company/SEC/central-bank/statistical/energy sources govern data; Reuters remains attributed news, syndication one origin. Internal claim/span/rights/version records stay exact while public copy uses natural necessary attribution without discretionary Sources/Notes or repeated citation links by default; actual mandatory credits and meaningful context remain. Reader/public payloads contain no KEEP/PREPARED/IDs/workflow/revision bureaucracy or ritual source notices; one discreet private-preview notice stays outside the article. Natural accessible zoom and compact lawful photo credit replace repeated instructions. Derivatives use editorially chosen chart subsets. New source/copy/media/preview changes require traceable revision and fresh exact review; no store/publisher/scheduler or production authority is added.
