# Retained ContentOps edition for Main News

The producer delivers eight selected articles through the existing owner projection: seven retained stories plus the exact current oil/US–Iran article, operation `v1-live-launch-20261027`, identity `8885bd9e945f425731c93f73c51ff0fa70463d7148a088f8ee3482937de3069d`. Its canonical Substack object `222368666` is published and reconciled; remaining channel states are read from that same operation's durable records. This private read artifact grants no publication authority. Main adoption remains unverified.

## Use the delivered source

- Producer artifact: [selected-edition.json](selected-edition.json), schema `contentops.cc_report_editorial_workspace.v1`, consumer view `contentops.retained_news.private_preview.v1`.
- Representative existing React reader: [reader.html](reader.html). This offline OS-owner inspection is private; do not expose the file as a subscriber endpoint. Its compiled reading views contain the canonical stories only; no derivative packages were requested or recompiled.
- Implementation: `live_contentops/retained_news_read_v1.py`, fed by `capital_chronicle_report_editorial_workspace_v1.report_workspace_projection`.
- Trusted selection: the existing owner-edition grouping in `data-journalism/edition/workspace.json`. Export resolves that exact configured group in the actual owner read model. Callers cannot change an edition/root/path/profile through a News request. Original photo bytes remain in that existing portable edition; no second photo store is created.

From this ContentOps checkout, an OS-owner can inspect the exact current article:

```powershell
python scripts/run_native_desktop_editorial.py news-read --article-id 8885bd9e945f425731c93f73c51ff0fa70463d7148a088f8ee3482937de3069d
```

Add `--asset-id documentary_oil` for its retained original photograph. Historical IBM identity `b39e88587862e50ced7333a61ad27c21546b45690b50a32c2c840799a28d7e13` and asset `ibm-dj-cash-improvement-r2` remain selectable. Exact edition membership and the trusted session's record grant are required; missing identities never substitute another story.

The producer operation is `python scripts/run_native_desktop_editorial.py news-export`. It reads the existing profile/selected group and owner SQLite with `mode=ro`, `query_only=ON`. Selected operations absent there are resolved only from the existing configured rollout store, querying those exact operation IDs. It performs no migration, source/model work, review, dispatch or runtime start, and writes the fixed display artifact/reader. Ordinary Main reads never execute the producer or newsroom.

The current relay source is admitted citation metadata only, bound to its already-governed captured hash and report-truth classification. No relay expression or source reuse flag is exported or invented. The independently authored article preserves uncertainty, the frozen `2026-10-27T04:00:52.972454Z` cutoff and its exact `article_revision`; export time is a separate clock.

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
| `run_id`, `article_identity`, `article_revision`, `article.title/dek/substack_body_markdown` | Exact selected operation/article/review revision and full public-safe authored copy. No identity is regenerated; SEO/display-date fields retain their allowlist. |
| `clocks.evidence_cutoff_utc/retained_at_utc/analysis_at_utc`, `article.display_date` | Saved source cutoff, durable retained record time and explicit analysis timestamp where supplied. Missing analysis time remains null. The authored display date is unchanged. |
| `evidence[].published_at_source/published_at_utc/publication_precision/observation_time_utc` | Original release spelling and precision. A date-only release has a null precise UTC time; normalized midnight is not supplied timing. Unknown observation time remains null. Chart data context separately retains known source periods. |
| `exported_at_utc` | Artifact retrieval/export clock only; it does not refresh the story, source, market or model. |
| `editorial_execution.observed_models`, `epistemic_state` | Saved actual model/role/effort attribution and original event/reporting/issuer limits, with no invocation IDs, internal native context, new vote or model call. |
| `evidence[].source_reuse_constraints`, `use_permission` | Actual attributed-facts/independent-paraphrase limits, source expression/image restrictions, required credit/terms and private-only use. Export supplies no public release permission. |
| `publication.state/destinations/canonical_url/publication_at_utc`, `review.decision` | Actual per-operation dispatch/reconciliation state. The current article retains its reconciled canonical URL; an unavailable public timestamp stays null. Historical previews remain PREPARED. Review IDs/rationale/internal proof machinery stay with the owner. |
| `media_assets[]` | Original chart hashes/bytes, alt/caption/source, exact dimensions and semantic table. Original photo hash/rights/date/credit remain; an existing small photo display derivative is labelled by its own hash. Authorized photo-byte reads resolve only the fixed existing portable map. |

IBM is `b39e88587862e50ced7333a61ad27c21546b45690b50a32c2c840799a28d7e13`. Its cash image remains SHA256 `928c7b51662662fd4c49f107da42ef29b51fe8addb3ff0c7b15daf0ee4ce7588`,1120×1760. The three contributions+2638/−1900/−133, reported+606/component sum+605/$1rounding, Q3-only source, GAAP/non-GAAP/consolidated limits and aligned2025/2026table are intact. All seven article/SEO identities, other fifteen charts, photos and source/Light/writer/review/preparation records are preserved. No universal dimensions/chart count, production quota,85% threshold or three-edition gate is introduced.

Private raw source text, X intake, captures, model prompts/returns, host locators, private questions, portfolio/account data and internal proof fields are omitted by explicit field allowlists. Changed/malformed artifact shape fails closed. The reader admits its fixed artifact once, serves that dated snapshot and caches checked asset bytes; a later owner revision requires explicit producer re-export and a new reader instance. It is not a live source/review monitor. Main can pin the delivered artifact through its existing accepted-source configuration; it must not auto-adopt moving producer code.

**Producer delivery is implemented. Main consumption/integration remains NOT_VERIFIED.** No peer message, Main route/host edit or listener is performed here. Current V1 live authority and applied state are recorded in [ACTIVATION.md](../ACTIVATION.md); four existing schedules stay ACTIVE and V2/V3 stay paused. The earlier validation below describes the retained historical delivery.


Validation at this producer delivery:34 focused real-artifact/selector tests and27 existing owner workspace/export tests PASS; changed-source Ruff, Node syntax and scoped diff checks pass. The actual existing React reader displayed the full IBM body, exact cash image, Q3 source and semantic table. Desktop pixels were inspected; the390px table DOM has no horizontal overflow. The actual local demonstration returned the full5405-character IBM body/229919-byte PNG and explicit ACCESS_DENIED/LOCAL_CONTENT_MISSING controls. Seven current native review/preparation IDs remain unchanged; no dispatch was created. Private demonstrations and readback are at `C:/Users/bullw/AppData/Local/CapitalChronicle/ContentOps/reader-first-review/retained-edition-main-news-20261026/`. Tests use isolated stores; the real producer export uses the existing owner in read-only mode. No Main receiver claim follows from these checks.
