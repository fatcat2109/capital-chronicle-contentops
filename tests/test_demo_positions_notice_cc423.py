"""CC-423: the live composers render Jim's exact demo-position disclosure."""
from pathlib import Path

import pytest

from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_status_posts_v1 as posts
from live_contentops.event_article_guard_v1 import (
    CONFLICTS_NOTICE, LEGACY_CONFLICTS_NOTICE, PUBLIC_NOTICE,
    check_publication_copy, public_execution_copy_forbidden,
)
from test_plan_analysis_pages_cc432 import source  # noqa: F401
from test_plan_call_cards_cc399 import five, queue, rows  # noqa: F401
from test_plan_status_posts_cc306 import export, main_root, rows_by  # noqa: F401
from test_event_public_record_v1 import frozen_file, source as frozen_source


EXPECTED = "Positions we mention are model positions on a demo account."


def test_status_post_and_each_destination_use_the_exact_notice(export, main_root):
    row = rows_by(export, main_root)[("XAUUSD", "WAITING")]
    row.update(posts.compose(row))
    assert CONFLICTS_NOTICE == EXPECTED
    assert row["text"].endswith(EXPECTED)
    for destination, payload in posts.destination_payloads(row, card_id="controlled-card").items():
        parts = payload.get("posts") or [{"text": payload["text"]}]
        assert EXPECTED in "\n\n".join(p["text"] for p in parts), destination
        assert all(len(p["text"]) <= posts.LIMITS[destination] for p in parts)


def test_call_card_draws_notice_and_all_social_copies_keep_it(five, main_root, tmp_path, monkeypatch):
    from PIL import Image, ImageDraw
    from live_contentops.plan_call_card_media_v1 import render

    store, folder, _, _ = five
    queue(store, folder, main_root)
    row = next(r for r in rows(store) if r["kind"] == "setup")
    drawn = []
    original = ImageDraw.ImageDraw.text

    def draw_text(self, xy, text, *args, **kwargs):
        drawn.append((xy, text))
        return original(self, xy, text, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", draw_text)
    asset = render(row, tmp_path / "card")
    assert any(text == EXPECTED and 1324 < xy[1] < 1410 for xy, text in drawn)
    assert asset["data_card_packet"]["notices"] == [PUBLIC_NOTICE, EXPECTED]
    with Image.open(asset["path"]) as image:
        assert image.size == (1440, 1440)
        assert image.crop((72, 1383, 1368, 1420)).getextrema() != ((255, 255),) * 3
    limits = {"telegram": 1024, "discord": 2000, "threads": 500, "x": 280,
              "facebook_page": 60000, "instagram_business": 2200, "substack_notes": 10000}
    for destination, payload in cards.destination_payloads(row, card_id=asset["asset_id"]).items():
        parts = payload.get("posts") or [{"text": payload["text"]}]
        assert EXPECTED in "\n\n".join(p["text"] for p in parts), destination
        length = posts._x_length if destination == "x" else len
        assert all(length(p["text"]) <= limits[destination] for p in parts)


def test_article_footer_is_rendered_into_markdown_html_and_live_payload(source, tmp_path):
    root, _, plan, manuscript = source
    folder = tmp_path / "article"
    packet = pages.render(plan, manuscript, run_root=root, output_dir=folder)
    assert packet["native_payload"]["body_markdown"].endswith(EXPECTED)
    for filename in ("article.md", "article.html"):
        assert EXPECTED in (folder / filename).read_text(encoding="utf-8")
    assert pages.public_filter(EXPECTED)["status"] == "PASS"
    assert check_publication_copy({"body": PUBLIC_NOTICE + " " + EXPECTED})["status"] == "PASS"


@pytest.mark.parametrize("private", [
    "Demo account 279805139.", "Exness-MT5Trial8", "The account balance is $100000.",
    "Position size: 0.05 lots.", "Demo account: another account.",
])
def test_exact_disclosure_never_exempts_adjacent_private_details(private):
    text = EXPECTED + " " + private
    assert public_execution_copy_forbidden(text)
    with pytest.raises(ValueError):
        check_publication_copy({"body": PUBLIC_NOTICE + " " + text})
    with pytest.raises(ValueError, match="PRIVATE_ACCOUNT_OR_SIZE"):
        pages.public_filter(text)


def test_derivative_notice_overflow_keeps_complete_sentences_within_limits(monkeypatch):
    payloads = {d: {"text": "A source-qualified report. " + LEGACY_CONFLICTS_NOTICE, "platform_limit": 1000}
                for d in pipeline.EXPECTED_DESTINATIONS}
    for destination, limit in (("x", 280), ("threads", 500)):
        body = "The report is source-qualified. " * 8
        payloads[destination] = {"text": body, "posts": [{"text": body, "order": 0,
            "role": "root", "media_asset_ids": []}], "platform_limit": limit}
    monkeypatch.setattr(pipeline, "_build_native_derivative_payloads", lambda **_: payloads)
    result = pipeline.build_native_derivative_payloads(article={"title": "A report"}, selection={},
        canonical_url="https://capitalchronicle.substack.com/p/exact", media_asset_ids=[])
    for destination, payload in result.items():
        parts = payload.get("posts") or [{"text": payload["text"]}]
        assert EXPECTED in "\n\n".join(p["text"] for p in parts)
        assert LEGACY_CONFLICTS_NOTICE not in "\n\n".join(p["text"] for p in parts)
        assert all(len(p["text"]) <= payload["platform_limit"] for p in parts)
        assert all(p["text"].rstrip().endswith(".") for p in parts)


def test_frozen_public_source_keeps_its_original_notice_and_exact_bytes(tmp_path):
    spec, _ = frozen_file(tmp_path, conflicts_notice=LEGACY_CONFLICTS_NOTICE)
    before = Path(spec["path"]).read_bytes()
    assert frozen_source(spec)["frozen_public_record"]["sha256"] == spec["sha256"]
    assert Path(spec["path"]).read_bytes() == before
    text = "A frozen post.\n\n" + PUBLIC_NOTICE + " " + LEGACY_CONFLICTS_NOTICE
    assert posts._split(text)[1].endswith(LEGACY_CONFLICTS_NOTICE)


def test_new_frozen_source_notice_does_not_hide_private_source_text(tmp_path):
    spec, _ = frozen_file(tmp_path, resolution_rule=EXPECTED + " Account number 279805139.")
    with pytest.raises(ValueError):
        frozen_source(spec)


def test_held_scenario_article_accepts_both_dated_and_current_disclosures():
    from test_article_publication_quality_cc333 import scenario_article
    from live_contentops.article_scenarios_v1 import validate_article_scenarios
    article, documents = scenario_article()
    assert validate_article_scenarios(article, documents) == article["social_scenarios"]
    article["substack_body_markdown"] = article["substack_body_markdown"].replace(CONFLICTS_NOTICE, LEGACY_CONFLICTS_NOTICE)
    assert validate_article_scenarios(article, documents) == article["social_scenarios"]


def test_plan_geometry_draws_and_binds_the_same_notice(tmp_path, monkeypatch):
    from matplotlib.figure import Figure
    from live_contentops.plan_analysis_media_v1 import render
    drawn = []
    original = Figure.text
    def figure_text(self, x, y, text, *args, **kwargs):
        drawn.append(text)
        return original(self, x, y, text, *args, **kwargs)
    monkeypatch.setattr(Figure, "text", figure_text)
    leg = {"entry_bounds": {"minimum": 1.12, "maximum": 1.13}, "stop_level": 1.10, "target_level": 1.15}
    asset = render({"plan_id": "controlled", "registration_hash": "f" * 64, "asset_id": "EURUSD"},
                   {"directional_entries": {"pullback": leg, "breakout": leg}}, tmp_path / "geometry",
                   frozen_at="2026-11-10T01:34:00Z")
    assert EXPECTED in drawn
    assert asset["chart_spec"]["notices"] == [PUBLIC_NOTICE, EXPECTED]
    assert Path(asset["path"]).is_file()
