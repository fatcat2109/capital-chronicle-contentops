"""Tests for daily X CDP headline capture packet module."""
from __future__ import annotations

from datetime import timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from live_contentops.daily_x_cdp_headline_capture_packet_v0 import (
    parse_timestamp,
    capture_headlines,
    CLASSIFICATION,
    TASK_LABEL,
)

# Mock headline entries in sidecar JSONL format
MOCK_SIDECAR = [
    {
        "headline_id": "hl_1",
        "tweet_id": "tw_1",
        "source_platform": "x_cdp_list_latest_tweets_timeline",
        "author_handle": "FirstSquawk",
        "candidate_catalyst_tags": ["macro"],
        "captured_at_utc": "2026-07-08T12:00:00Z",
        "headline_timestamp": "2026-07-08 19:00:00 GMT+7",
        "headline_text": "FED TO HOLD RATES STEADY.",
        "tweet_url": "https://x.com/FirstSquawk/status/1"
    },
    {
        "headline_id": "hl_2",
        "tweet_id": "tw_2",
        "source_platform": "x_cdp_list_latest_tweets_timeline",
        "author_handle": "FirstSquawk",
        "candidate_catalyst_tags": ["energy"],
        "captured_at_utc": "2026-07-08T13:00:00Z",
        "headline_timestamp": "2026-07-08 20:00:00 GMT+7",
        "headline_text": "OIL PRICES RISE ON GEOPOLITICAL TENSION.",
        "tweet_url": "https://x.com/FirstSquawk/status/2"
    },
    {
        "headline_id": "hl_2",  # Duplicate ID
        "tweet_id": "tw_2",
        "source_platform": "x_cdp_list_latest_tweets_timeline",
        "author_handle": "FirstSquawk",
        "candidate_catalyst_tags": ["energy"],
        "captured_at_utc": "2026-07-08T13:05:00Z",
        "headline_timestamp": "2026-07-08 20:05:00 GMT+7",
        "headline_text": "OIL PRICES RISE ON GEOPOLITICAL TENSION.",
        "tweet_url": "https://x.com/FirstSquawk/status/2"
    },
    {
        "headline_id": "hl_3",
        "tweet_id": "tw_3",
        "source_platform": "x_cdp_list_latest_tweets_timeline",
        "author_handle": "FirstSquawk",
        "candidate_catalyst_tags": ["macro"],
        "captured_at_utc": "2026-07-08T14:00:00Z",
        "headline_timestamp": "2026-07-08 21:00:00 GMT+7",
        "headline_text": "FED TO HOLD RATES STEADY.",  # Duplicate text
        "tweet_url": "https://x.com/FirstSquawk/status/3"
    },
    {
        "headline_id": "hl_4",
        "tweet_id": "tw_4",
        "source_platform": "x_cdp_list_latest_tweets_timeline",
        "author_handle": "FirstSquawk",
        "candidate_catalyst_tags": ["housing"],
        "captured_at_utc": "2026-07-09T08:00:00Z",
        "headline_timestamp": "2026-07-09 15:00:00 GMT+7",
        "headline_text": "HOUSING STARTS DECLINE.",
        "tweet_url": "https://x.com/FirstSquawk/status/4"
    }
]

@pytest.fixture
def temp_workspace():
    with TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        source_file = tmp_path / "mock_sidecar.jsonl"
        with open(source_file, "w", encoding="utf-8") as f:
            for item in MOCK_SIDECAR:
                f.write(json.dumps(item) + "\n")
        yield tmp_path, source_file

def test_parse_timestamp():
    # GMT+7 parsing
    ts1 = parse_timestamp("2026-07-08 20:21:16 GMT+7")
    assert ts1.tzinfo is timezone.utc
    # 2026-07-08 20:21:16 GMT+7 is 13:21:16 UTC
    assert ts1.hour == 13
    assert ts1.minute == 21
    assert ts1.second == 16

    # ISO parsing
    ts2 = parse_timestamp("2026-07-08T13:21:16Z")
    assert ts2.tzinfo is timezone.utc
    assert ts2.hour == 13
    assert ts2.minute == 21
    assert ts2.second == 16

def test_last_24h_fallback(temp_workspace):
    tmp_path, source_file = temp_workspace
    
    # Run capture with target date 2026-07-09 and no checkpoint
    res = capture_headlines(
        source_file=source_file,
        checkpoint_file=None,
        output_dir=tmp_path,
        target_date="2026-07-09"
    )
    
    # Fallback window is 2026-07-08T00:00:00Z to 2026-07-09T00:00:00Z
    # Mock items inside this:
    # hl_1: 12:00:00Z (observed 12:00:00Z, since GMT+7 19:00:00 is 12:00:00Z)
    # hl_2: 13:00:00Z
    # hl_3: 14:00:00Z (duplicate text of hl_1, should be deduped)
    # hl_4: 08:00:00Z (which is 2026-07-09T08:00:00Z - outside window)
    
    headlines = res["headlines"]
    # Should be Fed rates (hl_1) and Oil prices (hl_2). hl_3 is deduped by text, hl_4 is outside.
    assert len(headlines) == 2
    assert headlines[0]["headline_id"] == "hl_1"
    assert headlines[1]["headline_id"] == "hl_2"

def test_checkpoint_window(temp_workspace):
    tmp_path, source_file = temp_workspace
    
    # Create checkpoint file
    checkpoint_file = tmp_path / "checkpoint_state_v0.json"
    with open(checkpoint_file, "w", encoding="utf-8") as f:
        # Checkpoint is set to 2026-07-08T12:30:00Z
        json.dump({"current_checkpoint": "2026-07-08T12:30:00Z"}, f)

    res = capture_headlines(
        source_file=source_file,
        checkpoint_file=checkpoint_file,
        output_dir=tmp_path,
        target_date="2026-07-09"
    )
    
    headlines = res["headlines"]
    # Window start is 2026-07-08T12:30:00Z.
    # hl_1 is 12:00:00Z (skipped).
    # hl_2 is 13:00:00Z (captured).
    # hl_3 is 14:00:00Z (captured, but text matches hl_1. Wait, hl_1 was skipped, is hl_3 allowed or deduped against skipped?
    # Actually seen_texts remembers texts. hl_1 was skipped but not seen. So hl_3 can be captured if hl_1 was skipped.
    # Let's verify that hl_2 is captured.
    ids = [h["headline_id"] for h in headlines]
    assert "hl_2" in ids
    assert "hl_1" not in ids

def test_normalized_headline_schema(temp_workspace):
    tmp_path, source_file = temp_workspace
    res = capture_headlines(
        source_file=source_file,
        checkpoint_file=None,
        output_dir=tmp_path,
        target_date="2026-07-09"
    )
    
    for h in res["headlines"]:
        assert "headline_id" in h
        assert "source_platform" in h
        assert "source_account_or_list" in h
        assert "captured_at" in h
        assert "observed_at" in h
        assert "url_or_source_ref" in h
        assert "headline_text" in h
        assert "raw_excerpt" in h
        assert "tags" in h
        assert "capture_mode" in h
        
        # Verify no raw secret fields in output
        assert not any(k in h for k in ("secret", "token", "cookie", "password", "env"))

def test_deduplication(temp_workspace):
    tmp_path, source_file = temp_workspace
    res = capture_headlines(
        source_file=source_file,
        checkpoint_file=None,
        output_dir=tmp_path,
        target_date="2026-07-09"
    )
    
    # We should have no duplicate headline_ids and no duplicate headline_texts
    ids = [h["headline_id"] for h in res["headlines"]]
    assert len(ids) == len(set(ids))

    texts = [h["headline_text"] for h in res["headlines"]]
    assert len(texts) == len(set(texts))

def test_no_dispatch_or_platform_write_confirmation(temp_workspace):
    tmp_path, source_file = temp_workspace
    res = capture_headlines(
        source_file=source_file,
        checkpoint_file=None,
        output_dir=tmp_path,
        target_date="2026-07-09"
    )
    
    evidence = res["evidence"]
    assert evidence["no_dispatch_confirmation"] is True
    assert evidence["no_platform_write_confirmation"] is True
    assert evidence["no_raw_secret_read_confirmation"] is True
    assert evidence["classification"] == CLASSIFICATION
    assert evidence["task_label"] == TASK_LABEL
