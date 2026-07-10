# Substack-First ContentOps Pipeline

## Product Contract

Substack is the canonical ContentOps publication surface. A full run must create a public article or an externally usable Substack draft/preview, prove its full-body readback, and only then create derivative Telegram and X distribution that links to that canonical URL. Local Markdown and HTML are evidence artifacts, not publication success.

## Current Architecture

1. Load current CDP/headline schedule inputs.
2. Ask the configured LLM to rank the whole candidate set.
3. Apply the grounded support gate, including source/media-family checks and 24-hour duplicate/hotspot policy.
4. Generate a source-backed, topic-specific three-chart media pack.
5. Build the reader-facing article with SEO metadata in its manifest and three visual markers spread through the body.
6. Prepare a supervised Substack browser request containing only title, subtitle, body hash, chart paths, provenance, captions, and alt-text requirements.
7. Create/read back Substack. A draft needs an externally usable preview URL; a private `/publish/` editor URL fails closed.
8. Edit the existing Telegram message for a canonicalization repair, attaching media and the verified Substack URL. Do not create a duplicate post.
9. Prepare the X derivative from the same URL. Record a permalink or an exact blocker.

## Editorial and Media Rules

- The LLM ranks ideas; hardcoded keyword scoring is only a helper.
- A topic cannot repeat within 24 hours unless a material breaking/hotspot condition applies.
- Every canonical article needs at least three source-backed media assets, each with provenance, caption, and alt text.
- Charts must be analytically relevant and positioned at separate points in the body.
- The article must use a financial-news structure: sharp market signal, mechanism, policy context, cross-asset implications, confirmation/falsification, source trail, and a non-advice caveat.
- ContentOps may fetch/build source-backed chart media but must not become the numeric/source authority or mutate the main database.

## How To Run

Prepare a fresh packet:

```powershell
python scripts\run_substack_first_north_star_pipeline_loop_v1.py --prepare --run-id <run_id> --publication-mode draft --llm-provider auto
```

Use the resulting `substack_browser_request_v1.json` to enter the title, subtitle, text segments, and charts in the Substack browser editor. Capture a successful URL/readback only after all three charts appear in body order.

```powershell
python scripts\run_substack_first_north_star_pipeline_loop_v1.py --record-substack-readback --request-path <request_path> --publication-state draft --article-url <external_preview_url> --editor-body-image-count 3 --in-body-visual-asset-ids primary policy_corridor sofr_context
python scripts\run_substack_first_north_star_pipeline_loop_v1.py --complete --context-path <context_path> --substack-readback-path <readback_path> --operator-approved-full-live-run
```

`--complete` fails closed before Telegram whenever the Substack readback is missing, invalid, private-editor-only, not hash-matched, or below three in-body images.

## Audit A Run

Review the run context, browser request, article manifest, media paths/provenance, successful or blocked Substack readback, run evidence, Telegram edit result, Telegram readback, and X result. The required final evidence includes selection rationale, duplicate decision, canonical URL, article metadata, three media paths, and platform identifiers.

## Current Resume Point

Run ID: `substack_first_north_star_live_20260710`.

The current Substack draft is ID `206403125`. It is saved with the correct title, subtitle, and first text segment, but has no body images because Chrome blocked file chooser access to local chart files. No externally usable preview/public URL exists; Telegram message `61` was intentionally not edited.

To enable file upload, go to chrome://extensions in Chrome, click Details under the Codex extension, and enable "Allow access to file URLs." See [here](https://developers.openai.com/codex/app/chrome-extension#upload-files) for details.
