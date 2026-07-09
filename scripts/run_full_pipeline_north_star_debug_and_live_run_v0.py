#!/usr/bin/env python
"""Run the full north-star debug and live Telegram photo repair."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from live_contentops.full_pipeline_north_star_debug_and_live_run_v0 import (
    TASK_LABEL,
    run_full_pipeline_north_star_debug_and_live_run,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=TASK_LABEL)
    parser.add_argument("--operator-approved-full-live-run", action="store_true")
    parser.add_argument("--repair-previous-telegram-message-id", required=True)
    parser.add_argument("--max-send-attempts-per-platform", type=int, default=1)
    args = parser.parse_args()

    result = run_full_pipeline_north_star_debug_and_live_run(
        operator_approved_full_live_run=args.operator_approved_full_live_run,
        repair_previous_telegram_message_id=args.repair_previous_telegram_message_id,
        max_send_attempts_per_platform=args.max_send_attempts_per_platform,
    )
    dispatch = result["full_live_dispatch_results"]
    summary = {
        "classification": result["classification"],
        "media_generated": dispatch["media_generated"],
        "article_export_created": dispatch["article_export_created"],
        "telegram_repair_status": dispatch["telegram_repair_status"],
        "telegram_new_message_id": dispatch["telegram_new_message_id"],
        "telegram_image_attached": dispatch["telegram_image_attached"],
        "telegram_link_or_article_fallback_included": dispatch["telegram_link_or_article_fallback_included"],
        "substack_status": dispatch["substack_status"],
        "x_status": dispatch["x_status"],
        "duplicate_guard_result": dispatch["duplicate_guard_result"],
        "all_secret_values_redacted": dispatch["all_secret_values_redacted"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if result["classification"].startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
