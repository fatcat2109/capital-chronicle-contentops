# CC-267: a post with no public fact still publishes, with a title card

From the ContentOps V1 lane (Claude, Opus 5.5), 5 Nov 2026. The item was assigned by Ops Product.

## Outcome

A NEWS or POLICY post whose claims bind no admitted public fact now gets one title card instead of stopping the newsroom run. This is the case when every claim comes from a private survey (ISM, ADP, S&P Global, UMich, Challenger), whose figures decision 44 keeps off cards.

Before this change:
- `build_post_data_card` raised `DATA_CARD_NO_ADMITTED_PUBLIC_VISUAL_FACTS`.
- `complete_post_visuals` passed the error up and stopped `run_v1_simple_gemini_newsroom`.

This was defect T2 of the 5 Nov full regression.

## What changed (`live_contentops/post_visuals_v1.py`)

- **`complete_post_visuals`:** a card that cannot be built never stops the run.
  - A series the owner rejects falls back to the facts alone; the cause is kept in `series_dropped_reason`.
  - Otherwise the post gets the title card; the cause is kept in `title_card_reason`.
  - ANALYSIS keeps its own chart rule.
- **`build_post_title_card`:** the CC-245 design (`fact_card_design_v1`) with the piece's title and dated line.
  - The title is shown without figures (`card_title_without_figures`). Dates, maturities, times, ordinals and named numbers (S&P 500, Section 232) stay.
  - The card draws no fact, figure or source text, so decisions 42 and 44 both hold.
  - Its packet is marked `kind: CC267_TITLE_ONLY_NO_PUBLIC_FACT_V1` with `facts: []`.
  - Its lineage names the post's own sources; it has no source links.
- **`validate_post_data_card`:**
  - A title card must show the current article's figure-free title (otherwise `DATA_CARD_TITLE_CARD_CHANGED`), and its packet and bytes must match.
  - A fact card is checked as before, and cannot pass as a title card.
- **`native_desktop_editorial_v1.validate_release_media`:** unchanged. It accepts the title card as the post's one card, since the card keeps the `source_bound_data_card` modality.
- **`build_post_data_card`:** keeps its contract. It still raises for no admitted fact, as the existing private-survey tests expect.

## Tests

- **`tests/test_post_title_card_cc267.py`: 17 tests.**
  - The title rule on realistic headlines.
  - Every release check for a private-survey post: release media, eight preview packages, the pre-send image check.
  - Tamper checks.
  - The never-stop fallbacks.
  - The acceptance test: an ISM-only NEWS fixture runs through `run_v1_simple_gemini_newsroom` to a post whose one card shows "ISM services index rises as prices paid climb" and the date. The card carries no 52.4, 50.0 or 70.0; the post itself keeps the attributed 52.4.
- **T3:** reads CC-172's `TOOL_OUTPUT_IN_FILE` file.
- **T4:** asserts decision 42's text, as d6116e86 did for T1.
- **T2:** passes with the fix.
- **Focused regression, 25 test files** (post visuals, cards, native editorial, newsroom, publication), 5 Nov 20:40-20:57Z, one process:

  | Commit | Failed | Passed |
  |---|---|---|
  | Live head fd9fcd49 | 23 | 665 |
  | CC-267 on fd9fcd49 | 20 | 685 |

  - No new failure.
  - T2, T3 and T4 are fixed.
  - The 20 remaining failures fail on the live head too. They are listed in `focused-regression/`, and CC-268 takes them.
- **After rebasing onto the live head b9d892e7:** 12 card and newsroom files, 366 passed and 2 failed. Both failures are from before this change: `test_native_photoless_briefs_v1::test_unbound_old_and_analysis_articles_keep_the_photo_rule` and `test_reader_first_data_journalism_v1::test_channel_photo_preview_keeps_archive_context_without_dropping_unknown_rights`.

## Render and rollback

- **Render:** `renders/ism-title-card-1080x1350.png`.
- **Integration:**
  - Live tag: `contentops-live-20261105-cc267-title-card`.
  - Rollback tag: `contentops-rollback-20261105-cc267-title-card`, the live head before this change.

## 5 Nov: the card title never shows a phrase whose meaning changed or whose grammar broke

Ops Product checked nine plausible headlines on the first version. Two read wrong:
- "S&P Global US services PMI 54.8 vs 55.2 expected" became "... PMI expected".
- "US layoffs hit 153,074 in October, highest since 2020, Challenger says" became "US layoffs hit in October, highest since, Challenger says".

`card_title(article)` now removes figures and then checks that the result still reads cleanly:
- A "vs 55.2 expected" comparison goes whole.
- A year after "since" stays, even when a comma follows it.

If removing a figure leaves any of these, the text is not used:
- a verb without its object ("hit", "tops", "add");
- a one-word clause ("wages");
- a dangling "since", "vs" or "than";
- a lone "expected", "forecast" or "consensus".

The card then falls back, in order, to:
1. the clean leading clause;
2. the dek without figures;
3. a neutral release title such as "Challenger job cuts: October report";
4. "Capital Chronicle news brief" when no release is named.

Tests: `tests/test_post_title_card_cc267.py` now holds 23 headline cases, each also checked so that no input figure reaches the card and no "since", "vs" or "than" dangles. They include:
- Ops Product's six named headlines: the two that read wrong, and four that read fine, with inputs rebuilt from their outputs;
- a dek fallback test.

Render: `renders/challenger-fallback-title-card-1080x1350.png`.
