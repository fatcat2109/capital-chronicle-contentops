from copy import deepcopy
from functools import partial
import json
import subprocess
import sys

import pytest

from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_reader_copy_v1 as reader
from live_contentops import plan_reader_editorial_v1 as editorial
from live_contentops import plan_state_alerts_v1 as alerts
from live_contentops import plan_status_posts_v1 as posts
from live_contentops.light_model_caller_v1 import call_light
from test_plan_state_alerts_cc543 import event, main_root, replay, rows, write  # noqa: F401


LAYERS = {
    "macro": {"text": "Real yields rose after the data release.", "evidence_ids": ["rates"]},
    "fundamentals": {"text": "Physical demand slowed in Asia.", "evidence_ids": ["demand"]},
    "positioning_sentiment": {"text": "Longs are crowded after a week of inflows.", "evidence_ids": ["cot"]},
    "options_gamma": {"text": "Gamma data is stale.", "status": "STALE"},
    "technical": {"text": "Price failed to recover last week's range.", "evidence_ids": ["price"]},
}
LINK = "https://capitalchronicle.substack.com/p/controlled-gold-analysis"


def test_only_frozen_quotes_pass_and_failed_gy_drafts_fall_back_per_line(tmp_path):
    plan = {"analysis_layers": LAYERS}
    expected = {"macro", "fundamental", "positioning_sentiment", "technical"}
    assert set(reader.analysis_layer_options(plan)) == expected
    with pytest.raises(ValueError, match="CC688_LAYER_NOT_QUOTED_FROM_PLAN:macro"):
        reader.validate_analysis_line(reader.analysis_layer_options(plan), "macro", "Real yields fell after the data release.")

    def draft(_prompt, **kwargs):
        assert kwargs["callers"] == ("antigravity",)
        return json.dumps({"macro": "Real yields fell after the data release.",
                           "technical": LAYERS["technical"]["text"]}).encode(), {"status": "RETURNED"}

    quotes = editorial.prepare_plan_layers(plan, output_dir=tmp_path, call=draft)
    assert quotes["macro"] == LAYERS["macro"]["text"]
    assert set(quotes) == expected
    record = json.loads(next(tmp_path.glob("*/light-call.json")).read_bytes())
    assert (record["lines_passed"], record["lines_expected"], record["fallback"]) == (1, 4, "frozen_plan")
    assert reader.verified_analysis_lines(plan, quotes)[0] == "Macro: " + LAYERS["macro"]["text"]


def test_timeout_uses_the_frozen_quote_without_a_second_caller(tmp_path):
    seen = []

    def time_out(args, *, cwd, timeout, input):
        seen.append((args[0], timeout))
        raise subprocess.TimeoutExpired(args, timeout)

    plan = {"analysis_layers": LAYERS}
    quotes = editorial.prepare_plan_layers(plan, output_dir=tmp_path, call=partial(call_light, runner=time_out))
    assert len(quotes) == 4
    assert len(seen) == 1 and seen[0][1] == 65 and seen[0][0].endswith("agy.exe")
    record = json.loads(next(tmp_path.glob("*/light-call.json")).read_bytes())
    assert record["job"] == "plan_layer_lines"
    assert record["result"] == "FALLBACK" and record["cause"] == "AGY_PLAN_LAYER_TIMEOUT_65S"


@pytest.mark.parametrize("confirmed", [True, False])
def test_minute_queue_and_all_status_payloads_use_the_same_frozen_lines(replay, main_root, monkeypatch, confirmed):
    store, folder, raw, now = replay
    raw["analysis_layers"] = deepcopy(LAYERS)
    raw["analysis_layers"]["options_gamma"] = {"text": "Dealer gamma turns positive above the nearest strike."}
    write(folder, [raw], [event(raw["plan_id"], "WAITING", raw["registered_at_utc"])],
          generated_at_utc=now.isoformat())
    monkeypatch.setattr(pages, "confirmed_publication", lambda *_: {
        "plan_id": raw["plan_id"], "registration_hash": raw["registration_hash"],
        "canonical_url": LINK, "summary": {"macro": "Real yields rose."},
    } if confirmed else None)
    result = posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)
    assert result["status"] == "OK"
    row, = rows(store)
    assert row["analysis_copy_contract"] == reader.ANALYSIS_COPY
    alerts.validate(row, store=store)
    rendered = cards.destination_payloads(row, card_id="fixture-chart", chart_credit=True, complete_levels=True)
    assert set(rendered) == set(cards.DESTINATIONS)
    layer_lines = reader.verified_analysis_lines(raw, row["analysis_layer_quotes"])
    assert len(layer_lines) == 5
    for destination, copy in rendered.items():
        assert copy["text"].startswith(layer_lines[0]), destination
        assert all(line in copy["full_text"] for line in layer_lines), destination
        assert (LINK in copy["full_text"]) == confirmed, destination
        assert "Target level:" in copy["full_text"], destination
        assert copy["media_asset_ids"] == ["fixture-chart"]
    if confirmed:
        assert LINK in rendered["x"]["reply_texts"][0]
    assert all(posts._x_length(part["text"]) <= 280 for part in rendered["x"]["posts"])
    assert all(len(part) <= 500 for part in [rendered["threads"]["text"], *rendered["threads"]["reply_texts"]])
    row["analysis_layer_quotes"]["macro"] = "Real yields fell after the data release."
    with pytest.raises(ValueError, match="CC688_LAYER_NOT_QUOTED_FROM_PLAN"):
        alerts.validate(row, store=store)
