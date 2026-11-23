"""Read CC-463's daily counts from the existing image register. No writes/jobs."""
from __future__ import annotations

import argparse
from datetime import datetime, time, timedelta, timezone
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from live_contentops.publication_image_contract_v1 import ARTICLE_CARD_FALLBACK, POLICY
from live_contentops.published_images_v1 import PublishedImages


def audit(path, day, *, now=None):
    report = PublishedImages(path).daily_image_counts(day)
    end = datetime.combine(datetime.fromisoformat(day).date() + timedelta(days=1),
                           time(2), ZoneInfo("Asia/Bangkok"))
    complete = (now or datetime.now(timezone.utc)) >= end
    posts = report["observed_posts"]
    market_posts = [p for p in posts if p.get("market")]
    # CC-777 (decision 82): a post led by the article's own bound card after a failed capture is allowed, like
    # the bounded text fallback, and likewise never proves a chart on every market post.
    cards = [p for p in market_posts if p.get("lead_image_type") == ARTICLE_CARD_FALLBACK and not p.get("text_fallback")]
    violations = [p["record_id"] for p in market_posts if not p.get("text_fallback") and p not in cards and (
        p.get("image_contract") != POLICY or p.get("lead_image_type") != "TRADINGVIEW_MARKET_CHART")]
    unknown = [p["record_id"] for p in posts if p.get("lead_image_type") == "UNKNOWN"]
    charts = [p for p in market_posts if p.get("lead_image_type") == "TRADINGVIEW_MARKET_CHART"]
    all_charts = bool(market_posts) and len(charts) == len(market_posts) and not violations
    return {**report, "status": "FAIL" if violations else "OBSERVATION_PENDING" if not complete else
        "NO_MARKET_POST_OBSERVED" if not market_posts else
        "NO_MARKET_CHART_OBSERVED" if not charts else "INCOMPLETE_IMAGE_TYPES" if unknown else
        "TEXT_FALLBACK_OBSERVED" if any(p.get("text_fallback") for p in market_posts) else
        "FACT_CARD_FALLBACK_OBSERVED" if cards else "PASS",
        "whole_day_elapsed": complete, "market_posts": len(market_posts), "market_chart_posts": len(charts),
        # Bounded text fallback is allowed. It still cannot prove the item's
        # stronger full-day claim that every market post carried a chart.
        "all_market_posts_have_chart": all_charts,
        "chart_first_day_complete": bool(complete and all_charts and not unknown),
        # An illustrative chart does not establish structured market scope.
        # Expose it without guessing a market from its title or asset ID.
        "unscoped_chart_records": [p["record_id"] for p in posts
            if p.get("lead_image_type") == "TRADINGVIEW_MARKET_CHART" and not p.get("market")],
        "instagram_4x5_dimension_candidates": [p["record_id"] for p in charts
            if p.get("destination") == "instagram_business"
            and (p.get("lead_image") or {}).get("width")
            and (p.get("lead_image") or {}).get("height")
            and abs(p["lead_image"]["width"] / p["lead_image"]["height"] - .8) <= .003],
        "violations": violations, "unknown_type_records": unknown,
        "text_fallback_posts": sum(bool(p.get("text_fallback")) for p in market_posts),
        "fact_card_fallback_posts": len(cards),
        "public_write_performed": False, "schedule_changed": False}


def audit_window(path, day, *, following_days=7, now=None):
    """Read one baseline day and the following days from the same register.

    A completed empty follow-up day has no observed violation; its inactivity
    remains explicit and supplies no chart or Instagram visual proof.
    """
    if not 1 <= following_days <= 31:
        raise ValueError("FOLLOWING_DAYS_MUST_BE_1_TO_31")
    now = now or datetime.now(timezone.utc)
    start = datetime.fromisoformat(day).date()
    reports = [audit(path, (start + timedelta(days=i)).isoformat(), now=now)
               for i in range(following_days + 1)]
    end = datetime.combine(start + timedelta(days=following_days + 1),
                           time(2), ZoneInfo("Asia/Bangkok"))
    violations = {r["day"]: r["violations"] for r in reports if r["violations"]}
    unknown = {r["day"]: r["unknown_type_records"] for r in reports if r["unknown_type_records"]}
    baseline = reports[0]
    return {"start_day": day, "following_days_required": following_days,
        "window_end_utc": end.astimezone(timezone.utc).isoformat(),
        "observed_at_utc": now.astimezone(timezone.utc).isoformat(),
        "whole_window_elapsed": now >= end,
        "baseline_chart_first_day_complete": baseline["chart_first_day_complete"],
        "completed_following_days": sum(r["whole_day_elapsed"] for r in reports[1:]),
        "days_without_market_posts": [r["day"] for r in reports
            if r["whole_day_elapsed"] and not r["market_posts"]],
        "violations_by_day": violations, "unknown_type_records_by_day": unknown,
        "status": "FAIL" if violations else "INCOMPLETE_IMAGE_TYPES" if unknown else
            "OBSERVATION_PENDING" if not baseline["whole_day_elapsed"] else
            "BASELINE_DAY_INCOMPLETE" if not baseline["chart_first_day_complete"] else
            "OBSERVATION_PENDING" if now < end else "PASS",
        "days": reports, "public_write_performed": False, "schedule_changed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", required=True, type=Path)
    parser.add_argument("--day", required=True)
    parser.add_argument("--following-days", type=int,
                        help="Also audit this many days after the baseline day (CC-463 requires seven).")
    args = parser.parse_args()
    result = (audit(args.register, args.day) if args.following_days is None else
              audit_window(args.register, args.day, following_days=args.following_days))
    print(json.dumps(result, indent=2))
