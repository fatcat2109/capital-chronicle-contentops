from scripts.run_v1_current_yield_shadow_opportunities import (
    _release_payloads,
    _taxonomy,
)


def test_shadow_runner_counts_nine_prepared_payloads_as_article_ready():
    payloads = {
        name: {"text": "prepared"}
        for name in (
            "discord",
            "facebook_page",
            "instagram_business",
            "linkedin",
            "telegram",
            "threads",
            "tiktok",
            "x",
            "youtube",
        )
    }
    evidence = {
        "classification": "NO_PUBLICATION",
        "exact_next_blocker": "destination_not_ready:substack",
        "editorial_cycle": {"status": "PASS"},
        "release_candidate_preparation": {"payloads": payloads},
        "intake": {"counts": {"accepted": 1}},
    }

    assert _release_payloads(evidence) == payloads
    assert _taxonomy(evidence) == "ELIGIBLE_ARTICLE_READY"


def test_shadow_runner_does_not_label_thin_article_ready():
    evidence = {
        "classification": "NO_PUBLICATION",
        "exact_next_blocker": "INSUFFICIENT_READER_VALUE",
        "editorial_cycle": {"status": "NO_PUBLICATION"},
        "release_candidate_preparation": {"payloads": {}},
        "intake": {"counts": {"accepted": 1}},
    }

    assert _taxonomy(evidence) == "INSUFFICIENT_READER_VALUE"
