# Goal26 — usable native newsroom and source-backed edition

State: **NATIVE_EDITION_REVIEWED_PREPARED / PAUSED_NOT_DEPLOYED**.
Continues PR90 from verified Goal25 head `39193247b7206f1c8aa21aa5802032b8b84314c7`.
Classification: `PARTIAL_CAPABILITY_REUSE_COMPONENTS`. Reuses Goal25's filter/native/Neo proof.

## What Jim can use

Say **“Chuẩn bị ấn bản ContentOps”**, ask for an article from the accepted public Main report,
or ask to resume the current article. The installed `contentops-newsroom` skill resolves
`config/native_desktop_operator_profile_v1.json`, then handles native request/return, tools,
review and CLI details. Repo skill: `.agents/skills/contentops-newsroom/SKILL.md`.
This uses the same supported native protocol/prompt as the four prepared task identities.
It does not claim an unsupported Python-to-chat invocation bridge.

Readable desk:
`C:/Users/bullw/AppData/Local/CapitalChronicle/ContentOps/editorial-previews/desk/index.html`.
It renders the canonical React `ReportEditorialWorkspace` from the **existing reviewed Goal24
editorial store**, including its six KEEP/two HOLD decisions and article history. No empty
replacement store, scheduler or publisher. The saved desk is read-only; the existing Daily App
component also consumes this edition projection. No production runtime was restarted.

## Finite outcome

| Deliverable | Usable / required | Evidence / remaining state |
| --- | --- | --- |
| Ordinary-language operation | **1 / 1** | Profile → same frozen binding → roles/tools → review → coordinator plan |
| Original explainer | **1 / 1** | “Being right about gold does not verify what you own”; CFTC educational source, publication date unknown |
| Public-safe Main analysis | **1 / 1** | “Capital Chronicle's oil report separates tighter stocks from stronger demand”; exact USOIL v4 |
| Material retained-source follow-up | **1 / 1** | “Tồn kho gas tháng 10: dư theo mùa vụ, thiếu so với năm trước”; January archive versus October9 observation/October15 release and unpublished prior story |
| Platform previews | **24 / 24** | Eight per article, source dates and conditional analysis preserved |
| Relevant inspected media | **3 / 3** | Two reviewed source cards reused; one relevant original EIA excerpt rendered |
| Review / prepared handoff | **3 / 3** | Revision-bound KEEP; sole coordinator plans, **0 dispatches** |
| Edition restart | **1 / 1** | Same artifact/stage/review bytes; **0 new role/source work** |
| X mismatch assessment | **2 / 2 assessed** | **2 definite unresolved content/binding gaps**; no post/edit/retry |
| Delivery | **PR90** | Scoped source/CodeGraph push and exact-head CI readback recorded in PR90's Goal26 section and final delivery receipt |

The two X gaps are explicit limitations, as permitted by the owner request. A root's existence
or a different compiler's reconstruction cannot make strict content readback green.
Main/Control Tower synchronization is **PENDING_OWNER_RECEIVER**: this durable discoverable
checkpoint is the handoff; no Main/DB/builder message or receiver mutation was authorized.

## Editorial provenance

`native_edition_proof.json` retains exact source packs, dates, rights/claim lineage, native role
observations, review IDs, plan hashes and restart comparison. `artifacts/` contains the real
selector/writer returns, canonical articles, qualified records, eight packages and media.

- Actual `gpt-6.1-sol / low` selections/evidence plans for all three. An additional oil selection
  detected a USOIL/UKOIL identity collision and remains mismatch history; corrected USOIL v4
  was selected separately. No wrong-asset prose was substituted.
- Actual `gpt-6.1-sol / max` canonical/SEO writers received the exact institutional edge,
  humor and SEO packet. A complete oil response survived a lost handle and its exact bytes
  were submitted. Gas used its own supported MAX invocation. No repair was needed.
  Six accepted semantic returns do not imply six API calls; token usage and dollar cost are unknown.
- Explicit report/research triggers had **no new X intake and no Luna call**. Ordinary requests
  use current canonical intake/cached filter decisions; `--report-only` freezes report/research
  input. Every opportunity had <=32 candidates, one admission, zero new resolver GETs plus one
  actual Neo source request, below the shared six-request limit.
- Original EIA petroleum text was read through Neo, corroborating the dated Main source and
  supporting the oil excerpt media. It was not silently promoted into Main analysis or added
  to the already frozen writer pack. CFTC's fresh page showed a security challenge and the gas
  URL returned Access Forbidden; exact admitted source/policy bytes remained available, with
  no bypass or fresh-content claim. See `neo_source_observation.json` and `eia_media_source.json`.
- Gas is a change of observation vintage, not a same-week statistical revision or correction
  of a published article. Seasonal comparability, the above-five-year-average countercase,
  missing weather/LNG/price/expectation evidence and invalidation remain explicit.

## Connected repairs and review

`newsroom` resolves owner requests into the existing binding; `desk` renders that same store.
Owner questions are metadata, never evidence or permission. Main reports with the same first
source fact keep distinct report/version identities. Verified agency text permissions reach
the existing epistemic gate; same-URL documents keep their exact source IDs.

Frozen selections survive implementation changes. Failed source attempts remain history while
the same unanswered opportunity resumes. `recover-sources` joins exact already-admitted IDs
to an unanswered writer packet, archives the former request and preserves selection; completed
writers cannot be replaced. New writer packets omit unselected duplicate research/media while
retaining selected evidence, exact style and relevant prior story.

Media binding before review checks article identity, source, rights and bytes and preserves
package history. The same store projects reviewed prepared previews; no second publisher.
Short roots/replies preserve dates, duplicate Watch labels are removed, and the internal
“Source-bound brief” label becomes a reader-facing article link.

All three articles and 24 native copies were read. Three actual media plus alt/captions and
the React desktop/mobile views were inspected. `visual/inspection.json` retains the actual
rendered copies and widths: **430px mobile frame / 415px client / 415px scroll**, no overflow.
Two English articles and one Vietnamese article preserve writer language; compiler labels
remain English. This is saved rendered-preview evidence, not deployment.
Focused local check scope is recorded in `verification.json`; it is not a full-suite claim.

## Next operation and boundaries

Read the edition: `python scripts/run_native_desktop_editorial.py desk`.
Resume: `newsroom --operation-id goal26-original-explainer` (or
`goal26-main-oil-analysis-v2`, `goal26-gas-follow-up`). It returns completed output without
repeating models/sources. A new question uses a new stable ID and `--request-file <UTF-8
question>`; use `--report-only` only for a Main/research-only trigger. The agent handles the
native roles; Jim does not assemble request/claim JSON.

Production pause and all four old PAUSED host TOMLs are verified byte-identical to Goal25.
No account/DNS change, paid model/media, Main/database edit/message, platform post/draft,
activation, deploy, self-merge or actual Neo publish-click. Git/CI, prepared handoff, public
release and natural 5–8/day reliability remain separate claims.
