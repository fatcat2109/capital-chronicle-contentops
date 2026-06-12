# Project Source Export Guide (After 0174AO)

> [!WARNING]
> Project Sources are **context, not repo authority**. Repo files, git history, and
> current HEAD remain the source of truth. Uploading these files into a ChatGPT Project
> helps planning; it does not change what the repo enforces.

## 1. New files to upload (current authority)
Upload these so a new chat has the reconciled strategy:

- `docs/CAPITAL_CHRONICLE_CONTENTOPS_RECONCILED_FINAL_PRODUCT_MASTER_PLAN_AFTER_0174AO.md`
- `docs/CONTENTOPS_FINAL_PRODUCT_ROADMAP_AFTER_0174AO.md`
- `docs/CONTENTOPS_STRATEGY_RECOVERY_INDEX_AFTER_0174AO.md`
- `docs/NEW_CHAT_CONTINUATION_AFTER_0174AO.md`
- `docs/runbooks/TASK_CONTENTOPS_0174AO_RECONCILED_FINAL_PRODUCT_MASTER_PLAN_AND_STRATEGY_RECOVERY_V0.md`

## 2. Keep uploaded as current supporting authority
- `docs/CURRENT_STATE_SUMMARY_AFTER_0174AM.md`
- `docs/CAPITAL_CHRONICLE_CONTENTOPS_INSTITUTIONAL_COCKPIT_MASTER_PLAN.md`
- `docs/CONTENTOPS_OPERATING_RULES_AND_DESIGN_SYSTEM_GOVERNANCE.md`

## 3. Keep only as historical reference (optional in a clean set)
These remain valuable context but are superseded for current product strategy:

- `docs/CONTENTOPS_RECONCILED_ROADMAP_AFTER_0126.md`
- `docs/CONTENTOPS_STRATEGY_RECOVERY_MAP_AFTER_0126.md`
- `docs/FINAL_MASTER_PLAN_PRE_ALPHA_CONTENT_AND_API_AUTOMATION_READINESS_AFTER_0077.md`
- `docs/PRE_ALPHA_GENERAL_PROCESS_AND_GROUNDED_NEWS_MASTER_PLAN_AFTER_0075.md`
- design-reference docs: platform adapter contracts, canonical social post, approval
  ledger / kill switch / redacted audit, credential envelope, mock publish, LLM draft
  review, grounded research brief, SEO/newsletter architecture, Telegram pilot gate.

## 4. Safe to remove from Project Sources if the operator wants a clean set
These are duplicative or superseded handoff/quickstart/bundle docs whose content is now
captured by the 0174AO set and the 0174AM baseline summary:

- older `NEW_CHAT_CONTINUATION_AFTER_00xx/01xx.md` (pre-0174AM)
- older `CURRENT_STATE_SUMMARY_AFTER_00xx/01xx.md` (pre-0174AM)
- older `IDE_CLI_QUICKSTART_AFTER_*.md`
- older `UPLOAD_BUNDLE_MANIFEST_AFTER_*.md` / `PROJECT_SOURCE_EXPORT_AFTER_*.md`
  (pre-0174AO)

> [!NOTE]
> Removing them from Project Sources does **not** delete them from the repo. They stay in
> git history and the working tree as historical record. This task does not delete any
> repo file.

## 5. Do not upload
- Anything containing real credentials or `.env` values (never).
- `qa_evidence_*` screenshot folders (local evidence; not strategy authority).
