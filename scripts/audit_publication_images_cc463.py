"""Read CC-463's daily counts from the existing image register. No writes/jobs."""
from __future__ import annotations

import argparse
from datetime import datetime, time, timedelta, timezone
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from live_contentops.publication_image_contract_v1 import POLICY
from live_contentops.published_images_v1 import PublishedImages


def audit(path, day, *, now=None):
    report = PublishedImages(path).daily_image_counts(day)
    end = datetime.combine(datetime.fromisoformat(day).date() + timedelta(days=1),
                           time(2), ZoneInfo("Asia/Bangkok"))
    complete = (now or datetime.now(timezone.utc)) >= end
    posts = report["observed_posts"]
    market_posts = [p for p in posts if p.get("market")]
    violations = [p["record_id"] for p in market_posts if not p.get("text_fallback") and (
        p.get("image_contract") != POLICY or p.get("lead_image_type") != "TRADINGVIEW_MARKET_CHART")]
    unknown = [p["record_id"] for p in posts if p.get("lead_image_type") == "UNKNOWN"]
    return {**report, "status": "OBSERVATION_PENDING" if not complete else
        "FAIL" if violations else "NO_MARKET_POST_OBSERVED" if not market_posts else
        "INCOMPLETE_IMAGE_TYPES" if unknown else "PASS",
        "whole_day_elapsed": complete, "market_posts": len(market_posts),
        "violations": violations, "unknown_type_records": unknown,
        "text_fallback_posts": sum(bool(p.get("text_fallback")) for p in market_posts),
        "public_write_performed": False, "schedule_changed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", required=True, type=Path)
    parser.add_argument("--day", required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.register, args.day), indent=2))
