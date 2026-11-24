from copy import deepcopy
from datetime import timedelta
from hashlib import sha256
import json
import sys

import pytest

from live_contentops import plan_reader_copy_v1 as reader
from live_contentops import plan_reader_editorial_v1 as editorial
from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_state_alerts_v1 as alerts
from live_contentops import plan_status_posts_v1 as posts
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
from test_plan_analysis_distribution_cc435 import confirm
from test_plan_call_cards_cc399 import controlled_tradingview  # noqa: F401
from test_plan_state_alerts_cc543 import event, main_root, replay, rows, write  # noqa: F401
from test_plan_status_publication_cc306 import fake_host
from test_public_decision_checks_cc690 import checks, published
from test_publication_coordinator_v1 import FixtureTransport


def frozen_layers():
    exported = {
        "macro": "Real yields rose after the data release.",
        "event_and_cause": "The inflation release lifted Treasury yields and put pressure on metals.",
        "fundamental": "Physical demand slowed in Asia.",
        "positioning_and_sentiment": "Long positions are crowded after a week of inflows.",
        "options_and_gamma": "Dealer gamma turns positive above the nearest strike.",
        "cross_asset_and_contagion": "A stronger dollar would transmit the move to emerging markets.",
        "technical": "Price failed to recover last week's range.",
    }
    return {
        "layers": [{"layer": name, "state": "USED", "text": text, "first_cause": None}
                   for name, text in exported.items()],
        "scenario_analysis": {
            "priced": "Gold already reflects some of the rise in yields.",
            "base_case": {"probability_pct": 57, "market_move": "Real yields stay firm."},
            "main_alternative": {"probability_pct": 31, "market_move": "A softer dollar eases pressure on metals."},
        },
    }


def test_ordered_export_has_nine_layers_and_preserves_both_explicit_chances():
    plan = frozen_layers()
    _, gaps = reader.plan_layer_candidates(plan)
    quotes = editorial.prepare_plan_layers(plan, contract=reader.NINE_LAYER_COPY)
    lines = reader.verified_analysis_lines(plan, quotes, contract=reader.NINE_LAYER_COPY)
    assert not gaps
    assert [line.split(":", 1)[0] for line in lines] == [label for _, label in reader.PLAN_LAYER_ORDER]
    assert lines[-1] == "Scenarios: Main (57%): Real yields stay firm. Alternative (31%): A softer dollar eases pressure on metals."
    del plan["scenario_analysis"]["main_alternative"]["probability_pct"]
    lines = reader.verified_analysis_lines(plan, quotes, contract=reader.NINE_LAYER_COPY)
    assert "Alternative: A softer dollar" in lines[-1]
    assert "43%" not in lines[-1]


def test_three_gaps_distinguish_absence_and_the_exporters_cause():
    plan = frozen_layers()
    plan["layers"] = [row for row in plan["layers"] if row["layer"] != "event_and_cause"]
    gamma = next(row for row in plan["layers"] if row["layer"] == "options_and_gamma")
    gamma.update(state="UNAVAILABLE", text=None, first_cause="GAMMA_SNAPSHOT_STALE")
    plan["analysis_layers"] = {"options_and_gamma": {"state": "USED", "text": "A prior gamma reading was positive."}}
    del plan["scenario_analysis"]["priced"]
    _, gaps = reader.plan_layer_candidates(plan)
    assert gaps == {"event_and_cause": "EXPORT_FIELD_ABSENT", "priced_in": "EXPORT_FIELD_ABSENT",
                    "options_gamma": "GAMMA_SNAPSHOT_STALE"}
    quotes = editorial.prepare_plan_layers(plan, contract=reader.NINE_LAYER_COPY)
    assert len(reader.verified_analysis_lines(plan, quotes, contract=reader.NINE_LAYER_COPY)) == 6


def test_light_model_rewrites_only_verified_source_notation_and_falls_back_per_line(tmp_path):
    plan = frozen_layers()
    plan["time_exit_utc"] = "2026-11-21T20:00:00Z"
    plan["layers"][0]["text"] = "CC-730: Treasury yields rose 5 basis points while channel MIXED."
    technical = next(layer for layer in plan["layers"] if layer["layer"] == "technical")
    technical["text"] = "TREND DOWN: the close broke the 20-session low."
    plan["scenario_analysis"]["priced"] = (
        "The December hike was at 100% on Thursday (cc442), partly unpriced late on Friday. "
        "Implied volatility fell to 17% (cc415, one day old, before the break)."
    )
    plan["scenario_analysis"]["main_alternative"]["market_move"] = (
        "Gold could recover at 20:00Z after the jim_weekly_minimum_20261117 starter."
    )
    expected = "Treasury yields rose 5 basis points while signals are mixed."
    seen = []

    def draft(prompt, **kwargs):
        # Since 24 Nov 2026 the layer lines run on Codex at low effort, never Antigravity.
        assert kwargs["callers"] == ("codex",) and kwargs["codex_effort"] == "low"
        options = json.loads(prompt.split("\n", 1)[1])
        assert options["macro"][0] == {"quote": plan["layers"][0]["text"], "text": expected}
        seen.append(kwargs["job"])
        answer = {key: "0" for key in options}
        answer["macro"] = expected
        answer["main_alternative"] = "Gold could recover at 2:00 PM ET after the initial entry."
        return json.dumps(answer).encode(), {"status": "RETURNED"}

    quotes = editorial.prepare_plan_layers(plan, output_dir=tmp_path, call=draft, contract=reader.NINE_LAYER_COPY)
    assert seen == ["plan_layer_lines"]
    assert quotes["macro"] == expected
    assert quotes["technical"] == "The trend is down. The close broke the 20-session low."
    assert quotes["priced_in"] == "Implied volatility fell to 17% (one day old, before the break)."
    assert quotes["main_alternative"] == "Gold could recover at Sat 21 Nov, 3:00 PM ET after the initial entry."
    assert editorial.prepare_plan_layers(plan, output_dir=tmp_path, call=draft, contract=reader.NINE_LAYER_COPY) == quotes
    assert len(seen) == 1
    receipt = json.loads(next(tmp_path.glob("*/light-call.json")).read_bytes())
    assert receipt["findings"] == {"main_alternative": "CC688_LAYER_NOT_QUOTED_FROM_PLAN:main_alternative"}
    tampered = {**quotes, "macro": expected.replace("rose 5", "fell 6")}
    with pytest.raises(ValueError, match="CC688_LAYER_NOT_QUOTED_FROM_PLAN:macro"):
        reader.verified_analysis_lines(deepcopy(plan), tampered, contract=reader.NINE_LAYER_COPY)


@pytest.mark.parametrize("with_gaps", [False, True])
def test_minute_queue_renders_the_frozen_layers_on_the_setup_fill_and_result(replay, main_root, with_gaps):
    store, folder, raw, now = replay
    raw.update(frozen_layers())
    if with_gaps:
        missing = {"event_and_cause", "cross_asset_and_contagion", "technical"}
        raw["layers"] = [entry for entry in raw["layers"] if entry["layer"] not in missing]
    transitions = [event(raw["plan_id"], "WAITING", raw["registered_at_utc"])]
    write(folder, [raw], transitions, generated_at_utc=now.isoformat())
    assert posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)["status"] == "OK"
    setup, = rows(store)
    frozen = store.get_outbox_message(setup["key"])["payload"]
    key = setup["key"]
    store.create_work_item(story_id=key, title="Fixture setup", target_surface="MULTI_PLATFORM", work_item_id=key)
    confirm(store, key, sha256(("plan-status-post:" + key).encode()).hexdigest(), "telegram", "700",
            "https://t.me/CapitalChronicle/700")
    store.set_outbox_status(key, "PUBLISHED")

    fill_at = now + timedelta(minutes=1)
    transitions.append(event(raw["plan_id"], "FILLED", fill_at.isoformat()))
    update = {**raw, "status": "FILLED"}
    write(folder, [update], transitions, generated_at_utc=fill_at.isoformat())
    assert posts.queue_posts(store, folder, now=fill_at, main_root=main_root, python=sys.executable)["status"] == "OK"

    close_at = fill_at + timedelta(minutes=1)
    transitions.append(event(raw["plan_id"], "CLOSED", close_at.isoformat()))
    update = {**raw, "status": "CLOSED", "outcome": {"state": "SCORED", "result": "HIT",
        "outcome_id": "fixture-result", "score": {"plan_id": raw["plan_id"], "asset_id": raw["asset_id"],
        "outcome_id": "fixture-result", "result": "HIT", "resolved_at_utc": close_at.isoformat()}}}
    write(folder, [update], transitions, generated_at_utc=close_at.isoformat())
    assert posts.queue_posts(store, folder, now=close_at, main_root=main_root, python=sys.executable)["status"] == "OK"
    stored = rows(store)
    assert {row["kind"] for row in stored} >= {"setup", "update", "result"}
    for row in stored:
        assert row["analysis_copy_contract"] == reader.NINE_LAYER_COPY
        assert row["analysis_layer_gaps"] == (dict.fromkeys(missing, "EXPORT_FIELD_ABSENT") if with_gaps else {})
        alerts.validate(row, store=store)
        lines = alerts.analysis_lines(row)
        labels = [line.split(":", 1)[0] + ":" for line in lines]
        assert len(lines) == (6 if with_gaps else 9)
        payloads = cards.destination_payloads(row, card_id="chart", chart_credit=True, complete_levels=True)
        assert set(payloads) == set(cards.DESTINATIONS)
        for payload in payloads.values():
            rendered = payload["full_text"]
            assert [rendered.index(label) for label in labels] == sorted(rendered.index(label) for label in labels)
            assert all(rendered.count(line) == 1 for line in lines)
            assert rendered.count(posts.PUBLIC_NOTICE) == rendered.count(posts.CONFLICTS_NOTICE) == 1
    assert store.get_outbox_message(key)["payload"] == frozen


def test_long_export_reaches_the_durable_discord_thread_as_an_exact_reply(replay, main_root, tmp_path, monkeypatch):
    store, folder, raw, now = replay
    raw.update(frozen_layers())
    for line in raw["layers"]:
        line["text"] = line["text"].rstrip(".") + " as " + 14 * "liquidity moved through the market and " + "volatility fell."
    write(folder, [raw], [event(raw["plan_id"], "WAITING", raw["registered_at_utc"])], generated_at_utc=now.isoformat())
    queued = posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)
    assert queued["status"] == "OK"
    row, = rows(store)

    class Recorded(FixtureTransport):
        def __init__(self):
            super().__init__()
            self.intents = []
            self.replies_readable = False

        def publish(self, *, destination, intent, authorization_context):
            self.intents.append(deepcopy(intent))
            if intent.get("plan_status_part") == cards.ANALYSIS_FIRST_PART:
                raise TimeoutError("Fixture accepted a reply before losing its response")
            return {"status": "SUCCESS", "id": str(len(self.intents)),
                    "public_url": f"https://example.test/{destination}/{len(self.intents)}"}

        def readback(self, *, destination, public_object_id, public_object_url, intent):
            match = next((index for index, sent in enumerate(self.intents, start=1)
                          if sent["work_item_id"] == intent["work_item_id"]), None)
            if match is None or (intent.get("plan_status_part") and not self.replies_readable):
                return {"status": "READBACK_UNAVAILABLE", "verified": False}
            return {"status": "SUCCESS", "verified": True, "public_object_id": str(match),
                    "public_object_url": f"https://example.test/{destination}/{match}"}

    transport = Recorded()

    def coordinator_for(*_):
        return DurablePublicationCoordinator(store=store, transport_runtime=transport, clock=lambda: now,
            readiness_provider=lambda _: {"readiness_state": "READY_NON_BROWSER_BINDING"})

    payloads = cards.destination_payloads(row, card_id="chart", chart_credit=True)
    for route, limit in (("telegram", 4096), ("instagram_business", 2200), ("discord", 2000)):
        assert len(payloads[route]["parts"]) > 1
        assert all(len(part) <= limit for part in payloads[route]["parts"])
    assert all(posts._x_length(part["text"]) <= 280 for part in payloads["x"]["posts"])
    assert all(len(part) <= 500 for part in [payloads["threads"]["text"], *payloads["threads"]["reply_texts"]])
    assert len(payloads["linkedin"]["text"]) <= 3000

    ready = cards._ready_destinations
    monkeypatch.setattr(cards, "_ready_destinations", lambda *a, **kw: [
        route for route in ready(*a, **kw) if route == "discord"])

    def publish(*, immediate=False):
        return cards.publish_ready(store, now=now, latest_states=queued["latest_states"], root=tmp_path / "posts",
            host=fake_host, coordinator_for=coordinator_for, destinations=("discord",) if immediate else None,
            alert_filter=True)

    immediate = publish(immediate=True)
    child_key = f"{row['key']}-part-{cards.ANALYSIS_FIRST_PART}"
    child = cards._dispatch(store, child_key, "discord")
    assert child and child["status"] == "UNKNOWN_WRITE", immediate
    transport.replies_readable = True
    result = publish()
    assert cards._dispatch(store, child_key, "discord")["status"] == "DISPATCH_CONFIRMED"
    discord = [intent for intent in transport.intents if intent["destination_plan"]["destination"] == "discord"]
    assert len(discord) > 1, result
    root, *replies = discord
    assert all(reply["native_payload"]["discord_thread_parent_id"] == "1" for reply in replies)
    assert all(not reply["native_payload"]["media_asset_ids"] for reply in replies)
    assert root["native_payload"]["media_asset_ids"]
    assert len({intent["work_item_id"] for intent in discord}) == len(discord)
    texts = [intent["native_payload"]["text"] for intent in discord]
    assert all(len(text) <= 2000 for text in texts)
    assert all("\n".join(texts).count(line) == 1 for line in alerts.analysis_lines(row))


def test_evening_audit_counts_export_gaps_once_and_reads_the_confirmed_continuations(tmp_path):
    raw = frozen_layers()
    raw["layers"] = [line for line in raw["layers"] if line["layer"] != "technical"]
    source = {"kind": "result", "key": "gold-result", "plan_id": "plan_gold",
              "analysis_copy_contract": reader.NINE_LAYER_COPY, "source_plan": raw,
              "analysis_layer_quotes": editorial.prepare_plan_layers(raw, contract=reader.NINE_LAYER_COPY),
              "analysis_layer_gaps": reader.plan_layer_candidates(raw)[1]}
    page = "https://capitalchronicle.substack.com/p/gold-analysis"
    lines = alerts.analysis_lines(source)
    audit = checks(tmp_path)
    published(audit, "gold-result", "telegram", source=source, text="\n".join([*lines[:5], page]))
    published(audit, "gold-result-part-2", "telegram", source=source, text="\n".join(lines[5:]),
              intent={"plan_status_part": cards.ANALYSIS_FIRST_PART})
    published(audit, "gold-result", "threads", source=source, text="\n".join([*lines[:-1], page]))
    output = audit.finish({}, {"plan_gold": page})
    assert output["analysis_layer_gaps"] == [{"layer": "technical", "first_cause": "EXPORT_FIELD_ABSENT", "count": 1}]
    copies = {item["platform"]: item for item in output["plan_analysis"]}
    assert copies["telegram"]["layers"]["technical"] == {"state": "UNAVAILABLE", "cause": "EXPORT_FIELD_ABSENT"}
    assert copies["telegram"]["layers"]["scenarios"] == {"state": "PRINTED"}
    analysis_issues = [issue for issue in output["issues"] if issue["decision"] == "113"]
    assert [(issue["platform"], issue["first_cause"], issue["missing_layers"]) for issue in analysis_issues] == [
        ("threads", "PLAN_ANALYSIS_LAYERS_MISSING", {"scenarios": "EXPORTED_LAYER_NOT_PRINTED"})]


def test_threads_root_only_observation_uses_only_a_verified_reply_chain(tmp_path):
    raw = frozen_layers()
    source = {"kind": "setup", "key": "gold-setup", "plan_id": "plan_gold",
              "analysis_copy_contract": reader.NINE_LAYER_COPY, "source_plan": raw,
              "analysis_layer_quotes": editorial.prepare_plan_layers(raw, contract=reader.NINE_LAYER_COPY),
              "analysis_layer_gaps": {}}
    lines = alerts.analysis_lines(source)
    page = "https://capitalchronicle.substack.com/p/gold-analysis"
    for verified in (True, False):
        audit = checks(tmp_path)
        root = "\n".join([*lines[:4], page])
        copy = published(audit, "gold-setup", "threads", source=source, text=root,
            native={"reply_texts": lines[4:]}, mutations=[("2026-11-19T14:00:00Z", {"readback": {
                "verified": True, "identity_match": True, "observed_public_object_id": "object-1",
                "content_binding_checks": {"thread_match": verified},
            }})])
        copy.public_text = root
        issues = [item for item in audit.finish({}, {"plan_gold": page})["issues"] if item["decision"] == "113"]
        assert bool(issues) != verified
