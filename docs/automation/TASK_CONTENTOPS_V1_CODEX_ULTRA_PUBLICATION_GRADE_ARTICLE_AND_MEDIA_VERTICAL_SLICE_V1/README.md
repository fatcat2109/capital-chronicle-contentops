# V1 Codex Ultra publication-grade article and media vertical slice

## Owner-review artifact

- **Headline:** “The consumer didn’t fall off a cliff. The refund bridge just ended.”
- **Dateline:** August 15, 2026
- **Story:** July 2026 U.S. retail sales and the end of the unusually large tax-refund impulse
- **Classification ceiling:** `PASS_IMPLEMENTATION_PUBLICATION_GRADE_ARTICLE_READY_FOR_JIM_CHATGPT_REVIEW`
- **Public-write authority:** none; no publication action was attempted

This package contains the canonical Markdown article, a self-contained publication-style HTML treatment, four source-bound editorial graphics, two rights-safe documentary/authority photographs, complete desktop-width renders, source data, reproducible build scripts, and claim/rights/validation evidence.

## Review entry points

1. `article/article.html` — canonical publication treatment
2. `render/article-desktop-full.png` — complete 1440px-wide rendered page
3. `article/article.md` — portable editorial source
4. `factual_source_manifest.json` — claim-to-source binding
5. `media_provenance_rights_manifest.json` — visual provenance, rights, and editorial-use constraints
6. `evidence/validation_report.md` — QA result and known editorial judgment boundary

## Reproduction

From the repository root:

```powershell
python docs/automation/TASK_CONTENTOPS_V1_CODEX_ULTRA_PUBLICATION_GRADE_ARTICLE_AND_MEDIA_VERTICAL_SLICE_V1/scripts/build_charts.py
$env:NODE_PATH='C:\Users\bullw\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules'
& 'C:\Users\bullw\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' docs/automation/TASK_CONTENTOPS_V1_CODEX_ULTRA_PUBLICATION_GRADE_ARTICLE_AND_MEDIA_VERTICAL_SLICE_V1/scripts/render_article.mjs
python docs/automation/TASK_CONTENTOPS_V1_CODEX_ULTRA_PUBLICATION_GRADE_ARTICLE_AND_MEDIA_VERTICAL_SLICE_V1/scripts/validate_package.py
```

The render script launches a fresh headless Chrome process with Playwright. It does not use either operator-owned browser profile and performs no network or public action.

## Authority boundary

This is implementation evidence, not owner acceptance. Jim/ChatGPT alone may accept, revise, publish, or promote it. The article deliberately labels interpretation as Capital Chronicle analysis; it does not treat nominal retail sales as real consumption, and its charts are bound to the included official-source extracts.
