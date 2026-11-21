import json

from live_contentops.public_draft_claims_v1 import check_draft


def test_checks_wrong_level_reversed_direction_and_unfounded_cause(tmp_path):
    source = "Gold is bullish above 3,900."
    passages = [
        {"text": "Gold is bullish above 3,800.", "origin": "antigravity", "fallback": source},
        {"text": "Gold is bearish above 3,900.", "origin": "antigravity", "fallback": source},
        {"text": "Gold rose because of an emergency rate cut.", "origin": "antigravity"},
        {"text": "The analyst said gold would rise above 3,800.", "origin": "analyst_quote"},
    ]

    def caller(prompt, **kwargs):
        assert prompt.startswith("Do not call any tool.")
        assert kwargs["timeout_seconds"] == 65
        return json.dumps({"claims": [{"passage": 2, "kind": "cause",
            "draft_span": "because of an emergency rate cut", "source_line_ids": [],
            "source_quote": "", "flag": "NO_CAUSAL_SOURCE"}]}).encode(), {"answered_by": "antigravity"}

    result = check_draft("gold", "plan_post", passages, {"plan": [source]}, output_dir=tmp_path, call=caller)
    assert result["corrected"] == [source, source, "", passages[3]["text"]]
    assert [(flag["cause"], flag["action"]) for flag in result["flags"]] == [
        ("SOURCE_VALUE_UNMATCHED", "SOURCE_TEXT_RESTORED"),
        ("SOURCE_DIRECTION_REVERSED", "SOURCE_TEXT_RESTORED"),
        ("SOURCE_CAUSE_UNMATCHED", "SENTENCE_DROPPED"),
        ("SOURCE_VALUE_UNMATCHED", "QUOTED_ANALYST_RECORDED"),
    ]
    assert check_draft("gold", "plan_post", passages, {"plan": [source]}, output_dir=tmp_path,
                       call=lambda *args, **kwargs: None) == result


def test_timeout_still_checks_numbers_and_preserves_supported_text(tmp_path):
    data = [{"text": "The index fell 2%."}, {"text": "The index fell 5%."}]
    result = check_draft("wrap", "daily_wrap", data, {"quote": "The index fell 2%."}, output_dir=tmp_path,
                         call=lambda *args, **kwargs: (b"", {"cause": "AGY_CLAIM_TIMEOUT_65S"}))
    assert result["status"] == "AGY_UNAVAILABLE"
    assert result["corrected"] == [data[0]["text"], ""]
    assert result["flags"][0]["action"] == "SENTENCE_DROPPED"
