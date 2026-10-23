"""Exact producer observation marker; no issuer NLP or new event."""

import copy
import json
from live_contentops.contentops_editorial_desk_v1 import native_story_projection


def test_explicit_observation_separates_conditional_test_and_preserves_history():
    article = dict(
        title="Dated issuer report",
        substack_body_markdown="Retained copy.",
        story_identity="controlled",
    )
    edition = {
        "a": dict(
            article_identity="a",
            article=article,
            evidence=[],
            previews=[
                dict(
                    destination="telegram",
                    payload=dict(
                        text="What to watch: If new deals persist, the thesis strengthens."
                    ),
                )
            ],
        )
    }
    review = dict(
        article_identity="a",
        review_id="review",
        decision="USE_UNCHANGED",
        reader_change_summary="Retain dated report. Next observation: a subsequent dated new-deal disclosure and delayed-deal scope.",
        cutoff_utc="2026-10-23T00:00:00Z",
        source_attempts=[dict(url="https://example.org/report", status="PASS")],
    )
    rows = [
        dict(
            destination="internal:native-story-source-review",
            payload=json.dumps(review),
        )
    ]
    before = copy.deepcopy((edition, rows))
    story = native_story_projection(edition, rows)[0]
    assert story["next_observation"].startswith(
        "a subsequent dated new-deal disclosure"
    )
    assert story["conditional_thesis_test"].startswith("If new deals persist")
    assert story["next_observation_details"]["expected_at_utc"] is None
    assert story["next_observation_details"]["sources"] == [
        "https://example.org/report"
    ]
    assert story["state"] == "KEEP" and story["current_version"]["article"] == article
    assert (edition, rows) == before
    review["reader_change_summary"] = "No new observation was established."
    rows[0]["payload"] = json.dumps(review)
    fallback = native_story_projection(edition, rows)[0]
    assert fallback["next_observation_details"] is None
    assert fallback["next_observation"].startswith("If new deals persist")
