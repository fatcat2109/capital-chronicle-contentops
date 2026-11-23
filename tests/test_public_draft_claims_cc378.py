import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from live_contentops.agy_decision_metrics_v1 import daily_metrics, draft_claims
from live_contentops.public_draft_claims_v1 import JOB, check_draft, review_plan_copy


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


def test_plan_starts_one_bounded_worker_without_touching_issued_destinations(tmp_path):
    class Store:
        def get_dispatches_for_work_item(self, key):
            assert key == "plan-gold"
            return [{"platform": "telegram"}]

    row = {"key": "plan-gold", "levels": {"zone_low": 3900, "direction": "bullish",
                                         "account_balance": 100000}}
    plan = {"output_dir": str(tmp_path), "destinations": [
        {"destination": "telegram", "payload": "Already on Telegram."},
        {"destination": "x", "payload": "Gold is bullish above 3,900."},
    ]}
    launched = []
    for _ in range(2):
        review_plan_copy(Store(), row, plan, launch=lambda args, **kwargs: launched.append(args))
    assert len(launched) == 1
    packet = next((tmp_path / "claim-review").glob("*.request.json"))
    data = json.loads(packet.read_bytes())
    assert [passage["text"] for passage in data["passages"]] == [plan["destinations"][1]["payload"]]
    assert data["sources"]["plan"] == {"zone_low": 3900, "direction": "bullish"}


def test_evening_consumer_counts_review_and_prepares_one_exact_correction(tmp_path):
    root = tmp_path / "daily_app_outputs" / "plan-status-posts" / "plan-gold"
    before, after = "Gold is bullish above 3,800.", "Gold is bullish above 3,900."
    answer = {"claims": [{"passage": 0, "kind": "level", "draft_span": before,
                          "source_line_ids": ["L1"], "source_quote": after, "flag": "WRONG_LEVEL"}]}
    now = datetime.now(timezone.utc)
    record = check_draft("plan-gold", "plan_post", [{"text": before}], {"plan": after},
        output_dir=root, call=lambda *args, **kwargs: (json.dumps(answer).encode(),
            {"answered_by": "antigravity", "attempts": [{"caller": "antigravity", "status": "RETURNED"}]}))
    assert record["corrected"] == [after]
    window = {"since_utc": (now - timedelta(minutes=1)).isoformat(), "until_utc": (now + timedelta(minutes=1)).isoformat()}
    copy = SimpleNamespace(piece="plan-gold", platform="threads", url="https://www.threads.com/@cc/post/1",
                           intent={"output_dir": str(root)}, source={"kind": "setup"},
                           confirmed=True, dispatched_at=now, published_at=now, verified_at=now,
                           public_text=before, visible_text=before)
    metrics = daily_metrics(tmp_path, window, {})
    claims = draft_claims(tmp_path, window, [copy, copy], metrics)
    result = next(row for row in metrics["jobs"] if row["job"] == JOB)
    assert (result["posts_due"], result["calls"], result["code_rejects"]) == (1, 1, 1)
    assert claims["drafts"][0]["flag_count"] == 1
    reply, = claims["correcting_replies"]
    assert reply["parent_url"] == copy.url and reply["reply_text"].endswith(after)
