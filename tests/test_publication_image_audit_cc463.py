"""Day/week acceptance reads the existing image register without changing it."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import runpy

import pytest


AUDITOR = runpy.run_path(str(Path(__file__).parents[1] / "scripts/audit_publication_images_cc463.py"))
audit = AUDITOR["audit"]
audit_window = AUDITOR["audit_window"]
NOW = datetime(2026, 11, 12, 16, tzinfo=timezone.utc)
POLICY = "CC463_TRADINGVIEW_FIRST_V1"


def register(tmp_path, *, kind="TRADINGVIEW_MARKET_CHART", market="XAUUSD", fallback=None,
             destination="telegram", size=(1088, 1360), count=1):
    rows = []
    for i in range(count):
        rows.append({"schema_version": "contentops.published_images.v1",
            "record_id": str(i), "piece_id": str(i), "state": "PUBLISHED",
            "day": (NOW + timedelta(days=i)).date().isoformat(),
            "published_at_utc": (NOW + timedelta(days=i)).isoformat(),
            "publication_clock_basis": "OBSERVED_PUBLICATION_CLOCK", "market": market,
            "image_contract": POLICY, "text_fallback": fallback, "destination": destination,
            "lead_asset_id": "lead" if not fallback else None,
            "images": [] if fallback else [{"asset_id": "lead", "image_type": kind,
                "sha256": "a" * 64, "width": size[0], "height": size[1]}]})
    path = tmp_path / "published_images_v1.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return path


def test_allowed_text_fallback_does_not_certify_a_chart_on_every_market_post(tmp_path):
    path = register(tmp_path)
    row = json.loads(path.read_text(encoding="utf-8"))
    row.update(record_id="fallback", piece_id="fallback", images=[], lead_asset_id=None,
               text_fallback={"policy": POLICY, "first_causes": ["CAPTURE_EXHAUSTED"]})
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")
    result = audit(path, "2026-11-12", now=NOW + timedelta(days=1))
    assert result["status"] == "PASS"  # The bounded fallback remains permitted.
    assert result["text_fallback_posts"] == 1
    assert not result["all_market_posts_have_chart"]
    assert not result["chart_first_day_complete"]
    assert audit_window(path, "2026-11-12", now=NOW + timedelta(days=9))["status"] == "BASELINE_DAY_INCOMPLETE"


def test_an_observed_violation_fails_before_the_day_finishes(tmp_path):
    path = register(tmp_path, kind="DRAWN_CARD")
    result = audit(path, "2026-11-12", now=NOW)
    assert result["status"] == "FAIL" and not result["whole_day_elapsed"]
    assert audit_window(path, "2026-11-12", now=NOW)["status"] == "FAIL"


def test_following_week_cannot_pass_before_its_actual_end(tmp_path):
    path = register(tmp_path, count=8)
    # Baseline 12 Nov plus seven following days ends 20 Nov at 02:00 GMT+7.
    end = datetime(2026, 11, 19, 19, tzinfo=timezone.utc)
    early = audit_window(path, "2026-11-12", now=end - timedelta(seconds=1))
    assert early["status"] == "OBSERVATION_PENDING"
    assert early["completed_following_days"] == 6
    before = path.read_bytes()
    complete = audit_window(path, "2026-11-12", now=end)
    assert complete["status"] == "PASS"
    assert complete["completed_following_days"] == 7
    assert complete["window_end_utc"] == end.isoformat()
    assert path.read_bytes() == before


def test_no_post_days_remain_explicit_and_cannot_supply_the_baseline(tmp_path):
    path = register(tmp_path)
    result = audit_window(path, "2026-11-12", now=NOW + timedelta(days=9))
    assert result["status"] == "PASS"
    assert len(result["days_without_market_posts"]) == 7
    assert audit_window(path, "2026-11-13", now=NOW + timedelta(days=10))["status"] == "BASELINE_DAY_INCOMPLETE"


def test_illustrative_chart_does_not_become_market_scope_or_a_portrait_proof(tmp_path):
    path = register(tmp_path, market=None, destination="instagram_business", size=(1400, 1343))
    result = audit(path, "2026-11-12", now=NOW + timedelta(days=1))
    assert result["status"] == "NO_MARKET_POST_OBSERVED"
    assert result["counts_by_type"] == {"TRADINGVIEW_MARKET_CHART": 1}
    assert result["unscoped_chart_records"] == ["0"]
    assert not result["instagram_4x5_dimension_candidates"]
    assert not result["chart_first_day_complete"]


@pytest.mark.parametrize("size,candidate", [((1088, 1360), True), ((1524, 858), False), ((None, 1360), False)])
def test_portrait_dimensions_identify_a_candidate_not_a_visual_review(tmp_path, size, candidate):
    path = register(tmp_path, destination="instagram_business", size=size)
    result = audit(path, "2026-11-12", now=NOW + timedelta(days=1))
    assert bool(result["instagram_4x5_dimension_candidates"]) == candidate
    assert result["observed_posts"][0]["lead_image"]["sha256"] == "a" * 64


def test_unknown_historical_image_types_do_not_certify_the_week(tmp_path):
    path = register(tmp_path, kind="UNKNOWN", market=None)
    result = audit_window(path, "2026-11-12", now=NOW + timedelta(days=9))
    assert result["status"] == "INCOMPLETE_IMAGE_TYPES"


@pytest.mark.parametrize("days", [0, 32])
def test_window_is_bounded(tmp_path, days):
    with pytest.raises(ValueError, match="FOLLOWING_DAYS_MUST_BE_1_TO_31"):
        audit_window(tmp_path / "missing.jsonl", "2026-11-12", following_days=days)
