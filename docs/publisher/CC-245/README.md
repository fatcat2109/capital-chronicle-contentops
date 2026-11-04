# CC-245: fact cards that look like the release, not a blank page

Jim read the 4 Nov SEC image as a wrong picture on every platform. It was the approved
facts card, but it was mostly blank and showed the SEC's own 19 Oct date as
"Announcement: 2026-10-19". Every typographic card now renders in the site's design
language (public-desk tokens: paper `#F5F5F2`, ink `#111111`, yellow `#FDCF09`, dark field,
rules `#D6D6CF`; Segoe UI in place of Public Sans, which is not installed here).

## What a card shows

- Masthead: the Capital Chronicle mark with the yellow block, and the source as kicker.
- The release or event name, large.
- The key date, figure or decision, largest, in a dark block. It is always an exact
  substring of an admitted fact (a labelled date row first, else the first figure with
  its unit); the renderer refuses any other key.
- The verbatim admitted facts with their labels, sized to fill the rest.
- Footer: the source with its own date labelled ("announced October 19, 2026"), then the
  piece's date from its `display_date` ("Capital Chronicle · November 3, 2026") and the notice.
- No large empty area: fonts are fitted to the content; a title alone fills the body.

## Where it applies

`live_contentops/fact_card_design_v1.py` is the one renderer. `_render_text_card` routes
through it, so every caller gets the design: the source facts card (`build_source_fact_card`),
the post facts card (`build_post_image_card`, whose binding now records the design and the
piece date), the Instagram delivery card (`build_delivery_only_editorial_card`, now
1080x1350 portrait) and the daily digest card. Sent files are never overwritten: new
renders take content-bound names (`-cc245`/`-facts-`/`-card-` plus a hash).
A reviewed LinkedIn company copy now supersedes an unsent routine one, so SEC's company
page can get the reviewed copy with the new card instead of the held old-card copy.

## Renders (old vs new)

- `renders/compare-x-1600x900.png`: SEC, CPI and the 4 Nov digest at X size.
- `renders/compare-instagram-1080x1350.png`: the same at Instagram size.
- New SEC card from the approved packet: `renders/sec-si-roundtable-event-facts-20261109-cc245.png`.
The old digest image is the 800x450 copy read from Substack.

## Tests

`tests/test_fact_card_design_cc245.py` (key must be admitted text; key choice; no empty
gap over about a fifth of the body at both sizes, with a check that the measure catches the
old blank half; too much text is cut, never raised; reader dates; the source card labels
the source date and never overwrites a sent file; deterministic post card with design and
piece date; Instagram-size delivery card that keeps sent bytes), plus the reviewed company
copy test in `tests/test_linkedin_neo_recovery_v1.py`. Updated pinned assertions in
`test_media_manifest_authority_v1.py` and `test_post_image_policy_v1.py`.
Regression set (18 files): the same 17 failures as live 24e067d3; 410 passed.
