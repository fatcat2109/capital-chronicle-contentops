import json

from live_contentops.daily_editorial_scheduler_v6 import build_daily_editorial_schedule


def test_scheduler_ranks_official_current_news_and_marks_sidecars_catalyst_only(tmp_path):
    sidecar_dir = tmp_path / "headline_sidecars"
    sidecar_dir.mkdir()
    path = sidecar_dir / "step1_headline_sidecar_2026_07_08.jsonl"
    rows = [
        {
            "headline_id": "energy-1",
            "headline": "EIA oil inventory release moves crude volatility focus",
            "text": "EIA oil inventory release puts crude volatility and Hormuz supply risk back in focus.",
            "timestamp_gmt7": "2026-07-08T09:05:00+07:00",
            "tags": ["energy", "volatility", "geopolitics"],
            "numeric_truth_authority": False,
            "forecast_readiness_authority": False,
        },
        {
            "headline_id": "evergreen-1",
            "headline": "Why macro investors watch liquidity cycles",
            "text": "Long-run explainer about liquidity cycles.",
            "timestamp_gmt7": "2026-07-08T08:55:00+07:00",
            "tags": ["rates"],
        },
    ]
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    schedule = build_daily_editorial_schedule(
        schedule_date="2026-07-08",
        sidecar_glob=str(sidecar_dir / "*.jsonl"),
        output_dir=tmp_path / "schedule",
        slot_count=2,
    )

    assert schedule["headline_sidecar_count"] == 2
    assert schedule["headline_sidecars_are_catalyst_only"] is True
    assert schedule["slots"][0]["topic"].startswith("EIA oil inventory")
    assert schedule["slots"][0]["readiness"] == "READY_FOR_PIPELINE"
    assert schedule["slots"][0]["numeric_truth_authority"] is False
    assert "market_price_truth" in schedule["forbidden_uses"]
    assert (tmp_path / "schedule" / "daily_schedule_2026_07_08.json").exists()


def test_scheduler_writes_fallback_watchlist_when_no_sidecars(tmp_path):
    schedule = build_daily_editorial_schedule(
        schedule_date="2026-07-08",
        sidecar_glob=str(tmp_path / "missing" / "*.jsonl"),
        output_dir=tmp_path / "schedule",
        slot_count=6,
    )

    assert schedule["headline_sidecar_count"] == 0
    assert len(schedule["slots"]) == 6
    assert all(slot["readiness"] == "NEEDS_SOURCE_REVIEW" for slot in schedule["slots"])
    assert all(slot["headline_sidecar_context_only"] is True for slot in schedule["slots"])


def test_scheduler_ingests_current_step1_headline_sidecar_schema(tmp_path):
    sidecar_dir = tmp_path / "headline_sidecars"
    sidecar_dir.mkdir()
    path = sidecar_dir / "step1_headline_sidecar_2026_07_08.jsonl"
    row = {
        "headline_id": "step1-current-schema-1",
        "headline_text": "US power use to beat record highs in 2026 and 2027: EIA",
        "headline_timestamp": "2026-07-08 20:21:16 GMT+7",
        "author_handle": "@Newsdesk",
        "candidate_catalyst_tags": ["energy"],
        "follow_up_data_need_candidates": ["eia"],
        "headline_quality_flags": {"material_macro_or_market_relevance": True},
        "numeric_truth_authority": False,
        "forecast_readiness_authority": False,
    }
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    schedule = build_daily_editorial_schedule(
        schedule_date="2026-07-08",
        sidecar_glob=str(sidecar_dir / "*.jsonl"),
        output_dir=tmp_path / "schedule",
        slot_count=1,
    )

    slot = schedule["slots"][0]
    assert schedule["headline_sidecar_count"] == 1
    assert slot["topic"].startswith("US power use")
    assert slot["readiness"] == "READY_FOR_PIPELINE"
    assert slot["source_headline_author"] == "@Newsdesk"
    assert slot["source_headline_timestamp"] == "2026-07-08 20:21:16 GMT+7"
    assert "energy" in slot["tags"]
