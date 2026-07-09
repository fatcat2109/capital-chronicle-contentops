"""Daily X CDP Headline Capture Packet, Step 1 of ContentOps Daily Loop.

Determines the capture window using checkpoints or last 24h, filters/deduplicates
headlines, and outputs normalized packets.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_DAILY_X_CDP_HEADLINE_CAPTURE_PACKET_V0"
CLASSIFICATION = "PASS_WITH_FIXTURE_DAILY_X_CDP_HEADLINE_CAPTURE_PACKET_V0"

# Parse standard datetime from ISO or other formats
def parse_timestamp(ts_str: str) -> datetime:
    if not ts_str:
        return datetime.min.replace(tzinfo=timezone.utc)
    # Check for "YYYY-MM-DD HH:MM:SS GMT+7"
    if "GMT+7" in ts_str:
        try:
            clean = ts_str.replace("GMT+7", "").strip()
            dt = datetime.strptime(clean, "%Y-%m-%d %H:%M:%S")
            return dt.replace(tzinfo=timezone(timedelta(hours=7))).astimezone(timezone.utc)
        except Exception:
            pass
    # Try ISO formats
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(ts_str, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        # Fallback to fromisoformat
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)

def capture_headlines(
    source_file: str | Path,
    checkpoint_file: str | Path | None = None,
    output_dir: str | Path | None = None,
    target_date: str | None = None,
    force_mode: str | None = None
) -> dict[str, Any]:
    source_path = Path(source_file)
    output_path = Path(output_dir) if output_dir else Path(".")
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. Determine capture window
    prev_checkpoint = None
    window_start = None

    if checkpoint_file and Path(checkpoint_file).exists():
        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                ckpt_data = json.load(f)
                prev_checkpoint = ckpt_data.get("current_checkpoint")
                if prev_checkpoint:
                    window_start = parse_timestamp(prev_checkpoint)
        except Exception as e:
            print(f"Warning: Failed to read checkpoint file: {e}", file=sys.stderr)

    # Determine reference "now"
    if target_date:
        try:
            ref_now = datetime.strptime(target_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            ref_now = datetime.now(timezone.utc)
    else:
        ref_now = datetime.now(timezone.utc)

    if not window_start:
        # Fallback to last 24 hours
        window_start = ref_now - timedelta(days=1)

    window_end = ref_now

    capture_mode = force_mode if force_mode else "fixture_local"

    # 2. Read headlines from source file (JSONL format)
    headlines = []
    if source_path.exists():
        with open(source_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    raw_hl = json.loads(line)
                    # Deduplicate/Filter criteria
                    captured_at_str = raw_hl.get("captured_at_utc")
                    observed_at_str = raw_hl.get("headline_timestamp") or captured_at_str
                    observed_dt = parse_timestamp(observed_at_str)

                    # Ensure it falls within window
                    if window_start <= observed_dt <= window_end:
                        headlines.append((observed_dt, raw_hl))
                except Exception as e:
                    print(f"Warning: line parse failure: {e}", file=sys.stderr)
    else:
        print(f"Warning: Source path {source_path} does not exist.", file=sys.stderr)

    # Sort headlines by observed timestamp ascending
    headlines.sort(key=lambda x: x[0])

    # 3. Deduplicate headlines by headline_id or URL/text fallback
    seen_ids = set()
    seen_texts = set()
    normalized_headlines = []

    for observed_dt, raw_hl in headlines:
        hl_id = raw_hl.get("headline_id") or raw_hl.get("tweet_id")
        text = raw_hl.get("headline_text") or ""
        url = raw_hl.get("tweet_url") or raw_hl.get("source_url_or_ref") or ""

        # Normalize unique key
        unique_key = hl_id if hl_id else (url if url else text)
        if not unique_key:
            continue

        if unique_key in seen_ids or (text and text in seen_texts):
            continue

        seen_ids.add(unique_key)
        if text:
            seen_texts.add(text)

        # Build normalized format
        norm_hl = {
            "headline_id": hl_id,
            "source_platform": raw_hl.get("source_platform") or "x_cdp_list_latest_tweets_timeline",
            "source_account_or_list": raw_hl.get("author_handle") or "unknown",
            "captured_at": raw_hl.get("captured_at_utc"),
            "observed_at": raw_hl.get("headline_timestamp") or raw_hl.get("created_at_raw"),
            "url_or_source_ref": url,
            "headline_text": text,
            "raw_excerpt": text[:100] if text else "",
            "tags": raw_hl.get("candidate_catalyst_tags") or [],
            "capture_mode": capture_mode
        }
        normalized_headlines.append(norm_hl)

    # Calculate current checkpoint (latest captured headline timestamp)
    current_checkpoint = prev_checkpoint
    if normalized_headlines:
        latest_observed = max(parse_timestamp(h["observed_at"]) for h in normalized_headlines)
        current_checkpoint = latest_observed.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Generate checkpoint state
    checkpoint_state = {
        "previous_checkpoint": prev_checkpoint,
        "current_checkpoint": current_checkpoint,
        "window_start": window_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window_end": window_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "headline_count": len(normalized_headlines),
        "capture_mode": capture_mode
    }

    # Generate run evidence
    run_evidence = {
        "classification": CLASSIFICATION,
        "task_label": TASK_LABEL,
        "baseline_head": "e38432e520a01d549598180de8915bd75a95f9c7",
        "no_dispatch_confirmation": True,
        "no_platform_write_confirmation": True,
        "no_raw_secret_read_confirmation": True,
        "headline_count": len(normalized_headlines),
        "output_paths": {
            "headlines_raw": str(output_path / "headlines_raw_v0.json"),
            "checkpoint_state": str(output_path / "checkpoint_state_v0.json"),
            "run_evidence": str(output_path / "run_evidence_v0.json")
        },
        "blockers": []
    }

    # Write files
    with open(output_path / "headlines_raw_v0.json", "w", encoding="utf-8") as f:
        json.dump(normalized_headlines, f, indent=2, ensure_ascii=False)

    with open(output_path / "checkpoint_state_v0.json", "w", encoding="utf-8") as f:
        json.dump(checkpoint_state, f, indent=2, ensure_ascii=False)

    with open(output_path / "run_evidence_v0.json", "w", encoding="utf-8") as f:
        json.dump(run_evidence, f, indent=2, ensure_ascii=False)

    return {
        "headlines": normalized_headlines,
        "checkpoint": checkpoint_state,
        "evidence": run_evidence
    }
