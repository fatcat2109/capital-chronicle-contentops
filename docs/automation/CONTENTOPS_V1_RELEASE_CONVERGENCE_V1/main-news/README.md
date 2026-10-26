# Retained ContentOps edition for Main News

The producer now delivers the actual selected retained edition through the existing owner projection. This is a **private, dated PREPARED preview**, with seven available retained stories and their media. It is not a fresh edition, a public canonical feed, visual approval, publication, runtime activation or verified Main adoption.

## Use the delivered source

- Producer artifact: [selected-edition.json](selected-edition.json), schema `contentops.cc_report_editorial_workspace.v1`, consumer view `contentops.retained_news.private_preview.v1`.
- Representative existing React reader: [reader.html](reader.html). This offline OS-owner inspection is private; do not expose the file as a subscriber endpoint. Its compiled reading views contain the canonical stories only; no derivative packages were requested or recompiled.
- Implementation: `live_contentops/retained_news_read_v1.py`, fed by `capital_chronicle_report_editorial_workspace_v1.report_workspace_projection`.
- Trusted selection: the existing owner-edition grouping in `data-journalism/edition/workspace.json`. Export resolves that exact configured group in the actual owner read model. Callers cannot change an edition/root/path/profile through a News request. Original photo bytes remain in that existing portable edition; no second photo store is created.

From this ContentOps checkout, an OS-owner can inspect the full actual IBM record:

```powershell
python scripts/run_native_desktop_editorial.py news-read --article-id b39e88587862e50ced7333a61ad27c21546b45690b50a32c2c840799a28d7e13
```

Add `--asset-id ibm-dj-cash-improvement-r2` for its original1120×1760PNG as base64 on stdout. Other supplied article identities are selectable only when they belong to the configured edition and the trusted session grants that exact identity. Unknown membership, missing local input and denied permission return explicit error states; none silently substitutes another story.

The producer operation is `python scripts/run_native_desktop_editorial.py news-export`. It reads the existing profile/selected group and owner SQLite with `mode=ro`, `query_only=ON`, without a store constructor/migration, source acquisition, model, review, preparation, dispatch or runtime start. It writes only this fixed display artifact and reader. Ordinary Main reads use the already exported artifact and never execute `news-export` or the newsroom. Export is an explicit producer operation, not a GET side effect.

## Main adoption

The trusted Main host can instantiate `RetainedNewsReader(session_adapter)` from the accepted ContentOps source, with the producer artifact in its fixed repository-relative location. The constructor accepts no caller path/root. Use Main's existing `SessionAdapter.resolve(opaque_session, read_at_utc=...)` convention and saved verified-session fields: ACTIVE status, exact record IDs, `subscriber:read:private-preview` scope, not-before/verified/expiry UTC times. The adapter and its verified result are server-owned; a URL parameter, JSON role, owner flag or request dictionary grants nothing. This producer adds no login, billing, listener or access platform.

```python
from live_contentops.retained_news_read_v1 import RetainedNewsReader
news = RetainedNewsReader(existing_verified_session_adapter)
article = news.read(article_identity, opaque_session)
image = news.read_asset(article_identity, asset_id, opaque_session)
table = news.read_table(article_identity, asset_id, opaque_session)
```

Read responses carry `status`, private/no-store `headers` and `body`. Every article/image/table access repeats the session check. A granted identity does not clear source rights. The producer artifact is restricted to PRIVATE_PREVIEW_ONLY, and a restricted source produces no prose, source URL, image or table in that member. The artifact must stay behind the trusted host boundary; directly serving a repository file bypasses this adapter. `local_owner_read`/the CLI are OS-owner diagnostics, never HTTP authentication middleware. Main must bind this accepted producer source/artifact in its own trusted configuration; no Main files were changed here.

## Preserved fields and limits

| Existing field path | Meaning |
| --- | --- |
| `run_id`, `article_identity`, `article.title/dek/substack_body_markdown` | Exact selected identity and full public-safe authored copy; source/body identity is not regenerated. SEO and display-date fields are retained from the same allowlist. |
| `clocks.evidence_cutoff_utc/retained_at_utc/analysis_at_utc`, `article.display_date` | Saved source cutoff, durable retained record time and explicit analysis timestamp where supplied. Missing analysis time remains null. The authored display date is unchanged. |
| `evidence[].published_at_source/published_at_utc/publication_precision/observation_time_utc` | Original release spelling and precision. A date-only release has a null precise UTC time; normalized midnight is not supplied timing. Unknown observation time remains null. Chart data context separately retains known source periods. |
| `exported_at_utc` | Artifact retrieval/export clock only; it does not refresh the story, source, market or model. |
| `editorial_execution.observed_models`, `epistemic_state` | Saved actual model/role/effort attribution and original event/reporting/issuer limits, with no invocation IDs, internal native context, new vote or model call. |
| `evidence[].source_reuse_constraints`, `use_permission` | Actual attributed-facts/independent-paraphrase limits, source expression/image restrictions, required credit/terms and private-only use. Export supplies no public release permission. |
| `publication.state/destinations/canonical_url/publication_at_utc`, `review.decision` | Current exported PREPARED/KEEP and actual destination states. The selected63 states are NOT_DISPATCHED. Canonical URL and publication time are null; no pending-publication placeholder is a published URL. Review IDs/rationale/internal proof machinery stay with the owner. |
| `media_assets[]` | Original chart hashes/bytes, alt/caption/source, exact dimensions and semantic table. Original photo hash/rights/date/credit remain; an existing small photo display derivative is labelled by its own hash. Authorized photo-byte reads resolve only the fixed existing portable map. |

IBM is `b39e88587862e50ced7333a61ad27c21546b45690b50a32c2c840799a28d7e13`. Its cash image remains SHA256 `928c7b51662662fd4c49f107da42ef29b51fe8addb3ff0c7b15daf0ee4ce7588`,1120×1760. The three contributions+2638/−1900/−133, reported+606/component sum+605/$1rounding, Q3-only source, GAAP/non-GAAP/consolidated limits and aligned2025/2026table are intact. All seven article/SEO identities, other fifteen charts, photos and source/Light/writer/review/preparation records are preserved. No universal dimensions/chart count, production quota,85% threshold or three-edition gate is introduced.

Private raw source text, X intake, captures, model prompts/returns, host locators, private questions, portfolio/account data and internal proof fields are omitted by explicit field allowlists. Changed/malformed artifact shape fails closed. The reader admits its fixed artifact once, serves that dated snapshot and caches checked asset bytes; a later owner revision requires explicit producer re-export and a new reader instance. It is not a live source/review monitor. Main can pin the delivered artifact through its existing accepted-source configuration; it must not auto-adopt moving producer code.

**Producer delivery is implemented. Main consumption/integration remains NOT_VERIFIED.** No peer message, Main route/host edit, listener, deployment or public publication is performed. Jim's IBM visual verdict remains open; production/four schedules/host prompts/fuse/publication/V2/V3 remain unchanged and paused. The later exact [activation decision](../ACTIVATION.md) must name accepted source, manual/scheduled mode, existing windows/time and any authorized destinations.


Validation at this producer delivery:34 focused real-artifact/selector tests and27 existing owner workspace/export tests PASS; changed-source Ruff, Node syntax and scoped diff checks pass. The actual existing React reader displayed the full IBM body, exact cash image, Q3 source and semantic table. Desktop pixels were inspected; the390px table DOM has no horizontal overflow. The actual local demonstration returned the full5405-character IBM body/229919-byte PNG and explicit ACCESS_DENIED/LOCAL_CONTENT_MISSING controls. Seven current native review/preparation IDs remain unchanged; no dispatch was created. Private demonstrations and readback are at `C:/Users/bullw/AppData/Local/CapitalChronicle/ContentOps/reader-first-review/retained-edition-main-news-20261026/`. Tests use isolated stores; the real producer export uses the existing owner in read-only mode. No Main receiver claim follows from these checks.
