# New Chat Continuation - After TASK_CONTENTOPS_0099

Paste this into a new ChatGPT/IDE session to resume with clean authority.

## Repo
- Path: A:\Capital Chronicle\tools\cc-live-contentops
- Branch: master
- Accepted HEAD: 965f7f5 (TASK_CONTENTOPS_0099)

## Project intent
Local-first ContentOps control-plane sidecar for Capital Chronicle. Prepares
safe offline editorial/research artifacts for human review. Not a live posting
engine. Never markets Capital Chronicle as a Bloomberg replacement, AI trading
bot, signal service, execution engine, or guaranteed forecast system.

## Accepted local chain (0095-0099)
- 0095 content engine + editorial packet
- 0096 prompt pack + style profile + editorial rubric
- 0097 draft renderer + review queue
- 0098 manual review workflow + approval packet
- 0099 manual export packet + content ledger

The pipeline is end-to-end local and deterministic: seed -> editorial packet ->
rendered draft / review queue -> manual review / approval -> manual export
packet / content ledger. Every stage is fixture-driven with no external calls.

## Hard boundaries (still active)
- No network/provider/LLM/web/search calls.
- No platform API/posting/scheduling/replies/DMs/scraping/metrics ingestion.
- No credential or `.env` reads.
- No fake alpha output, no public-postable content, no auto-approval.
- No financial advice, buy/sell/hold, position sizing, targets, signal language.
- No sibling/core repo mutation.

## Telegram lane: STOPPED
Do not reopen. 0094B is NOT a successful second live proof. Any future final
proof requires the operator to directly set `TEST_TELEGRAM_CHANNEL` plus a new
explicit task. No alias, remap, wrapper, or retry.

## Known caveats (do not touch)
- `.gitignore` operator-owned drift.
- 15 older task docs carry HEAD-hash/LF-CRLF drift.
- `.env` untracked operator secret - never read/stage/commit.
- `project_sources_bundle_AFTER_0074/` untracked - do not stage/clean.

## Project Sources
The 0099 bundle (`project_sources_bundle_AFTER_0099`) supersedes the older 0073
/0074 bundles. Upload only the AFTER_0099 safe docs/schemas listed in
`UPLOAD_BUNDLE_MANIFEST_AFTER_0099.md`. Never upload `.env`, secrets, raw logs,
or vendor data.

## Next recommended task
TASK_CONTENTOPS_0101_PRE_ALPHA_END_TO_END_LOCAL_DEMO_PACKET_FROM_SEED_TO_LEDGER_V0
