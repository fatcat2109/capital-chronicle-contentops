from live_contentops import thread_continuation_quality_v2 as thread_qa

def test_check_mid_word_splits_detected():
    # Test split word case
    segments = [
        {
            "segment_text": "(1/2) Treasury yields volatility reflects macroeconomic a\n\n[Unverified Source: Verification Required]",
            "sequence_label": "(1/2)",
            "segment_hash": "a" * 64
        },
        {
            "segment_text": "(2/2) djustments.\n\n[Unverified Source: Verification Required]",
            "sequence_label": "(2/2)",
            "segment_hash": "b" * 64
        }
    ]
    orig = "Historical volatility reflects macroeconomic adjustments."
    assert thread_qa.check_mid_word_splits(segments, orig) is True

def test_check_mid_word_splits_clean_boundary():
    # Clean boundary at word space boundary
    segments = [
        {
            "segment_text": "(1/2) Treasury yields volatility reflects macroeconomic\n\n[Unverified Source: Verification Required]",
            "sequence_label": "(1/2)",
            "segment_hash": "a" * 64
        },
        {
            "segment_text": "(2/2) adjustments.\n\n[Unverified Source: Verification Required]",
            "sequence_label": "(2/2)",
            "segment_hash": "b" * 64
        }
    ]
    orig = "Historical volatility reflects macroeconomic adjustments."
    assert thread_qa.check_mid_word_splits(segments, orig) is False

def test_inspect_thread_continuation_flags_truncation_and_stub_hash():
    variants = {
        "x_manual_thread": {
            "variant_text": "short",
            "segments": [{
                "segment_text": "some text...",
                "segment_hash": "stub_hash_value"
            }]
        }
    }
    report = thread_qa.inspect_thread_continuation(variants, {"x_manual_thread": 280}, "some text...")
    assert "stub_segment_hash_detected" in report["blockers"]
    assert "segment_truncation_detected" in report["blockers"]
