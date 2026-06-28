from live_contentops import platform_thread_continuation_v6 as thread_continuation

def test_long_content_becomes_ordered_manual_thread_segments():
    text = "A" * 500
    segments = thread_continuation.segment_text_by_limits(
        text=text,
        max_length=280,
        platform_family="x_manual_thread",
        required_caveats=["Unverified source check"]
    )
    
    # Text length 500 should split into at least 2 segments
    assert len(segments) > 1
    for seg in segments:
        assert "segment_index" in seg
        assert "total_segments" in seg
        assert "sequence_label" in seg
        assert "segment_text" in seg
        assert "segment_hash" in seg
        assert seg["review_only"] is True
        assert seg["public_postable"] is False
        assert seg["dispatch_allowed_now"] is False
        assert len(seg["segment_text"]) <= 280
        
    assert segments[0]["segment_index"] == 1
    assert "(1/" in segments[0]["sequence_label"]
    assert "Unverified source check" in segments[0]["segment_text"]

def test_continuation_preserves_caveats():
    text = "Short text"
    segments = thread_continuation.segment_text_by_limits(
        text=text,
        max_length=280,
        platform_family="x_manual_thread",
        required_caveats=["Source unverified"]
    )
    assert len(segments) == 1
    assert "Source unverified" in segments[0]["segment_text"]
