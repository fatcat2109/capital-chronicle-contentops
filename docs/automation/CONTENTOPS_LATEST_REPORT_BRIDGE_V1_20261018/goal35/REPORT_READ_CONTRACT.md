# Existing newsroom read contract for Desks

This exposes existing content; it adds no API, database owner or execution path.

## Producer and selection

- Producer: `live_contentops.capital_chronicle_report_editorial_workspace_v1.report_workspace_projection`.
- Schema: `contentops.cc_report_editorial_workspace.v1`.
- Existing read-only generation: `python scripts/run_native_desktop_editorial.py desk`.
- Local snapshot: `%LOCALAPPDATA%/CapitalChronicle/ContentOps/editorial-previews/desk/workspace.json`.
- Readable actual component: the adjacent `index.html`, `ReportEditorialWorkspace`.
- Select a precise `native_edition[]` item by both `run_id` and `article_identity`.
  The grouping is `owner_edition`; its ready/held/missing counts have different meanings
  from qualified drafts or actual publications. An absent unfinished article is not empty prose.

For this checkpoint, the exact available item is:

`run_id=goal35-oil`

`article_identity=dc676e03091e454b6c79037bee64f4b6c0a6a61b24c689f277202e215c1a7fd1`

## Fields already exposed

| Purpose | Existing item fields |
| --- | --- |
| Canonical prose | `article.title`, `article.dek`, `article.substack_body_markdown` |
| SEO and reader question | `article.search_title`, `article.meta_description`, `article.canonical_slug_candidate`, `reader_question`, `angle`, `mode` |
| Exact source context | `evidence[]`: source ID, original publisher, URL/relay, source date, canonical text hash and source reuse constraints where supplied |
| Revision/review | `article_identity`, `prior_story`, `source_review`, `review.review_id`, `review.decision`, `review.rationale`, `prepared_state` |
| Media | `media_assets[]`, with inspected bound hashes; an empty list is a media gap |
| Eight native packages | `previews[]`: `destination`, `preview_id`, `article_identity`, full `payload`, claim lineage where supplied |
| Publication | `publication.state`, operation scope, next operation, dispatch boundary, destination status/readback fields |

Read full payload `full_text` or its ordered `posts` for X/Threads. A root post alone
does not contain the whole package. Pending canonical URLs are placeholders; the Desk
labels them as pending. `PREPARED` is not a public object, and a local KEEP is not a send.
Preserve reporting/confirmation distinctions, source precision, rights, and revision identity.

The owner-manual store in the existing profile is the producer's operating store; the
canonical published-memory store is read-only. Consumers should use this projection
instead of inventing another queue/store. No Desks code, thread, runtime or schedule was
changed or contacted. Receiver integration and receiver consumption are not claimed.
