from live_contentops.platform_native_variant_generator_live_v6 import summarize_validation, validate_platform_variants


def test_validate_platform_variants_blocks_stub_payloads():
    variants = {
        "substack": "Substack scaffold stub" * 100,
        "linkedin": "LinkedIn variant scaffold stub",
        "facebook": "Facebook variant scaffold stub",
        "discord": "Discord variant scaffold stub",
        "telegram": "Telegram scaffold stub",
        "threads": "Threads scaffold stub",
        "instagram_caption": "Instagram scaffold stub",
    }
    failures = validate_platform_variants(variants, {"x": ["X scaffold stub"], "threads": ["Threads scaffold stub"]})
    assert "linkedin_placeholder_detected" in failures
    assert "x_thread_placeholder_detected" in failures


def test_validate_platform_variants_accepts_real_payloads():
    base = (
        "Capital Chronicle examines how shipping lanes, policy calendars, and liquidity conditions "
        "interact across macro cycles. The note cites data, reported ranges, and historical context "
        "without giving investment advice. "
    )
    variants = {
        "substack": base * 10,
        "linkedin": base,
        "facebook": base,
        "discord": base,
        "telegram": base,
        "threads": base,
        "instagram_caption": base,
    }
    threads = {"x": ["1/ Macro policy data and shipping context shape the latest Capital Chronicle briefing."], "threads": [base]}
    assert validate_platform_variants(variants, threads) == []


def test_validate_platform_variants_blocks_financial_advice_phrases():
    text = "Capital Chronicle macro liquidity context. This is educational, but you should buy now."
    variants = {
        "substack": text * 30,
        "linkedin": text * 2,
        "facebook": text * 2,
        "discord": text * 2,
        "telegram": text,
        "threads": text,
        "instagram_caption": text * 2,
    }
    threads = {"x": ["Macro data says buy now."], "threads": [text]}
    failures = validate_platform_variants(variants, threads)
    assert "linkedin_financial_advice_phrase_detected" in failures
    assert "x_thread_financial_advice_phrase_detected" in failures


def test_summarize_validation_returns_ready_and_blocked_platforms():
    summary = summarize_validation(["linkedin_too_short:0<120", "x_thread_missing"])
    assert summary == {"failure_count": 2, "blocked_platforms": ["linkedin", "x"], "ready": False}

