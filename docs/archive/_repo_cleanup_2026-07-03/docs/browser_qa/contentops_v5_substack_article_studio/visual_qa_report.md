# ContentOps V5 Substack Article Studio Visual QA Report

## Scope

- Target URL: `http://127.0.0.1:5173/`
- Target surface: `ui/contentops_v5/`
- QA date: 2026-07-01 local time
- Browser QA mode: local Vite dev server only

## Safety proof

- V4 was not used as the product target.
- No external site was opened.
- No env values, credentials, cookies, localStorage, sessionStorage, tokens, webhook URLs, provider keys, or browser session data were read.
- No Substack API, provider API, platform API, publish, dispatch, scheduler, live send, or hidden retry was triggered.

## Visible labels verified

Across the required V5 views, the V6 Substack manual export card was visible with mode/safety labels including:

- `sample_fixture_only`
- `manual copy only`
- `Substack API not used`
- `live publish disabled`
- `no runtime proof`

## Screenshots

| View | Screenshot | Visible proof |
|---|---|---|
| Writer Studio | `docs/browser_qa/contentops_v5_substack_article_studio/writer_studio_substack_card.png` | Substack article studio card visible on V5 Writer Studio. |
| AI Writer / SEO Lab | `docs/browser_qa/contentops_v5_substack_article_studio/ai_writer_seo_substack_card.png` | Substack SEO card visible with fixture/manual labels. |
| Platform Payload Preview | `docs/browser_qa/contentops_v5_substack_article_studio/platform_preview_substack_card.png` | Substack preview/hash evidence visible. |
| Manual Export / Pilot Verification | `docs/browser_qa/contentops_v5_substack_article_studio/manual_export_substack_card.png` | Manual-copy payload visible; Substack API not used. |
| Approval Queue | `docs/browser_qa/contentops_v5_substack_article_studio/approval_queue_substack_card.png` | Approval queue lane visible on V5. |
| Evidence Vault | `docs/browser_qa/contentops_v5_substack_article_studio/evidence_vault_substack_card.png` | Evidence vault lane visible on V5. |

## Visual caveats

- Screenshots are viewport captures from the local Vite dev server.
- Evidence is fixture-only UI QA, not runtime publishing proof.
- Manual export remains copy-only and operator-mediated.

## V4 non-target proof

The tested URL was `http://127.0.0.1:5173/`, served from `ui/contentops_v5/`. The authority doc keeps `ui/institutional_operator_cockpit_v4/` as fallback/reference only, and this QA did not open or use V4 as the product target.
