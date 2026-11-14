"""The existing minute consumer maintains one complete, source-bound public record."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import urllib.error

import pytest

from live_contentops import pinned_result_scorecard_v1 as scorecard
from live_contentops import plan_status_posts_v1 as posts
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
from test_publication_coordinator_v1 import _set_mode

NOW = datetime(2026, 11, 10, 9, tzinfo=timezone.utc)


def call(ident, result="HIT", *, at="2026-11-10T08:50:00Z", state="SCORED"):
    p = {"plan_id": ident, "asset_id": "US500", "direction": "BULLISH", "status": "EXPIRED",
         "zone": {"minimum": 6000.5, "maximum": 6005.5}, "expires_at_utc": at,
         "invalidation_conditions": [{"field": "close", "operator": "LT", "threshold": 5990}],
         "public_instrument": {"name": "S&P 500", "symbol": "ES", "kind": "FUT", "contract_month": "2026-12"}}
    outcome = "outcome-" + ident
    score = {"plan_id": ident, "asset_id": "US500", "direction": "BULLISH", "result": result,
             "outcome_id": outcome, "content_hash": "score-" + ident, "resolved_at_utc": at,
             "scored_at_utc": at}
    p["outcome"] = {"state": state, "result": result if state == "SCORED" else None,
                    "outcome_id": outcome if state == "SCORED" else None,
                    "score": score if state == "SCORED" else None}
    return p


def export(*plans):
    return {"status": {"schema": "CapitalChroniclePlanStatusV1", "schema_version": "1.0.0",
            "generated_at_utc": (NOW - timedelta(seconds=10)).isoformat(), "content_hash": "source-hash",
            "scored_call_count": sum(p["outcome"]["state"] == "SCORED" for p in plans), "plans": list(plans)},
            "transitions": {"schema": "CapitalChroniclePlanTransitionsV1", "schema_version": "1.0.0",
            "generated_at_utc": NOW.isoformat(), "status_content_hash": "source-hash", "transitions": [
                {"plan_id": p["plan_id"], "status": "EXPIRED", "at_utc": p["expires_at_utc"],
                 "reason_code": "EXPIRED"} for p in plans]}}


class Bot:
    def __init__(self):
        self.calls, self.messages, self.pinned = [], {}, None
        self.username = "CapitalChronicle"
        self.lose_create = self.lose_edit = self.fail_pin = False
        self.fail_edit_before_write = False

    def message(self, ident, text):
        return {"message_id": ident, "text": text,
                "chat": {"username": self.username, "type": "channel"}}

    def call(self, method, **fields):
        self.calls.append((method, deepcopy(fields)))
        if method == "getChat":
            return {"username": self.username, "type": "channel",
                    "pinned_message": deepcopy(self.messages.get(self.pinned))}
        if method == "sendMessage":
            ident = 100 + len(self.messages)
            self.messages[ident] = self.message(ident, fields["text"])
            if self.lose_create:
                raise scorecard.TelegramScorecardError("TELEGRAM_SCORECARD_TRANSPORT_UNCERTAIN")
            return deepcopy(self.messages[ident])
        if method == "editMessageText":
            ident = fields["message_id"]
            if self.fail_edit_before_write:
                self.fail_edit_before_write = False
                raise scorecard.TelegramScorecardError("TELEGRAM_SCORECARD_TRANSPORT_UNCERTAIN")
            if self.messages[ident]["text"] == fields["text"]:
                return {"not_modified": True}
            self.messages[ident] = self.message(ident, fields["text"])
            if self.lose_edit:
                raise scorecard.TelegramScorecardError("TELEGRAM_SCORECARD_TRANSPORT_UNCERTAIN")
            return deepcopy(self.messages[ident])
        if method == "pinChatMessage":
            if self.fail_pin:
                self.fail_pin = False
                raise scorecard.TelegramScorecardError("TELEGRAM_SCORECARD_HTTP_429", definite=True)
            self.pinned = fields["message_id"]
            return True
        raise AssertionError(method)

    def count(self, method):
        return sum(m == method for m, _ in self.calls)


@pytest.fixture
def live(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite")
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    return store, DurablePublicationCoordinator(store=store, transport_runtime=None), Bot()


def update(live, value):
    _, coordinator, bot = live
    return coordinator.update_pinned_result_scorecard(value, now=NOW, api=bot)


def test_win_and_loss_have_identical_fields_in_one_message():
    result = scorecard.project(export(call("win"), call("loss", "STOPPED")), now=NOW)
    assert result["counts"] == {"HIT": 1, "STOPPED": 1, "EXPIRED": 0, "NOT_TRIGGERED": 0, "total": 2, "scored": 2}
    lines = [r["line"].split(" | ") for r in result["rows"]]
    assert len(lines[0]) == len(lines[1]) == 5
    assert lines[0][:4] == lines[1][:4]
    assert "2026-11-10 ET" in result["text"] and "ES futures, Dec 2026" in result["text"]
    assert "(plan levels)" in result["text"] and scorecard.PUBLIC_NOTICE in result["text"]


def test_limit_keeps_whole_newest_rows_and_counts_all_outcomes():
    plans = [call(f"call-{i:03}", "HIT" if i % 2 else "STOPPED",
                  at=f"2026-11-{5 + i // 30:02}T08:{i % 30:02}:00Z") for i in range(120)]
    record = scorecard.project(export(*plans), now=NOW)
    assert record["counts"]["total"] == 120 and record["counts"]["HIT"] == record["counts"]["STOPPED"] == 60
    assert 1 < record["shown"] < 120 and scorecard.text_length(record["text"]) <= 4096
    assert all(r["line"] in record["text"] for r in record["rows"][:record["shown"]])
    assert record["text"].count("\n2026-") == record["shown"]


def test_no_free_text_execution_data_or_inferred_end_direction():
    plan = call("account-123456789")
    plan.update(balance=999999, lots=20, fill_price=6123.45)
    plan["outcome"]["score"].update(comment="private ticket 123456789 profit 999999", pnl=999999)
    record = scorecard.project(export(plan), now=NOW)
    assert "end direction:" not in record["text"]
    assert record["rows"][0]["direction_at_window_end"] is None
    assert not any(value in record["text"] for value in ("123456789", "999999", "6123.45", "private ticket", "lots"))
    plan["outcome"]["score"]["direction_at_window_end"] = "BEARISH"
    assert "end direction: bearish" in scorecard.project(export(plan), now=NOW)["text"]


def test_mapped_instrument_zone_uses_one_complete_price_basis():
    # CC-583 (decision 40): the record prints only the plan's own levels, never a mapped conversion.
    plan = call("mapped")
    plan["public_instrument"].update(zone_low=6010, zone_high=6015, invalidation_level=5995, direction="BULLISH")
    text = scorecard.project(export(plan), now=NOW)["text"]
    assert "entry zone 6,000.5–6,005.5 (plan levels)" in text and "6,010" not in text


def test_legacy_expiry_is_unscored_until_main_supplies_not_triggered():
    plan = call("unfilled", state="NOT_SCORED_UNTRIGGERED")
    record = scorecard.project(export(plan), now=NOW)
    assert "EXPIRED (untriggered; not scored)" in record["text"] and record["counts"]["scored"] == 0
    plan = call("unfilled", "NOT_TRIGGERED")
    record = scorecard.project(export(plan), now=NOW)
    assert "| NOT TRIGGERED\n" in record["text"] and record["counts"]["NOT_TRIGGERED"] == 1
    assert posts.result_rows_from_export(export(plan)) == []  # Feed cadence stays selective.


@pytest.mark.parametrize("change, cause", [
    (lambda e: e["status"].update(generated_at_utc="2026-11-10T08:00:00Z"), "EXPORT_STALE"),
    (lambda e: e["status"]["plans"][0]["outcome"]["score"].update(result="STOPPED"), "BINDING_INVALID"),
    (lambda e: e["status"]["plans"][0]["outcome"]["score"].update(scored_at_utc="2026-11-11T08:00:00Z"), "FROM_FUTURE"),
])
def test_bad_source_never_reaches_api(live, change, cause):
    value = export(call("test"))
    change(value)
    with pytest.raises(ValueError, match=cause):
        update(live, value)
    assert live[2].calls == []


def test_minute_updates_one_public_object_and_creates_no_result_feed_posts(live):
    first = update(live, export(call("win")))
    second = update(live, export(call("win"), call("loss", "STOPPED")))
    repeat = update(live, export(call("win"), call("loss", "STOPPED")))
    store, _, bot = live
    assert first["status"] == second["status"] == repeat["status"] == "CONFIRMED"
    assert first["message_id"] == second["message_id"] == "100"
    assert bot.count("sendMessage") == bot.count("editMessageText") == 1
    assert repeat["created_messages"] == repeat["edited_messages"] == 0
    assert second["extra_result_feed_posts"] == 0
    assert store.list_outbox_messages(destination=posts.DESTINATION) == []
    readbacks = store.list_outbox_messages(destination=scorecard.DESTINATION + "-readback")
    assert len(readbacks) == 2 and all(json.loads(r["payload"])["pinned"] for r in readbacks)


def test_refresh_clock_alone_does_not_edit_or_create_revisions(live):
    value = export(call("win"))
    first = update(live, value)
    count = len(live[0].list_outbox_messages())
    value["status"].update(generated_at_utc=NOW.isoformat(), content_hash="next-snapshot")
    second = update(live, value)
    assert first["revision"] == second["revision"] and live[2].count("editMessageText") == 0
    assert len(live[0].list_outbox_messages()) == count


def test_totals_keep_held_rows_when_new_export_omits_an_old_plan(live):
    update(live, export(call("old", "STOPPED")))
    result = update(live, export(call("new", "HIT")))
    assert result["counts"]["total"] == 2 and result["counts"]["STOPPED"] == 1


def test_main_correction_replaces_result_without_a_second_denominator(live):
    plan = call("corrected", "STOPPED")
    update(live, export(plan))
    plan["outcome"]["result"] = "HIT"
    plan["outcome"]["outcome_id"] = "corrected-outcome"
    plan["outcome"]["score"].update(result="HIT", outcome_id="corrected-outcome",
        corrects_outcome_id="outcome-corrected", scored_at_utc="2026-11-10T08:55:00Z")
    result = update(live, export(plan))
    assert result["counts"]["total"] == result["counts"]["HIT"] == 1 and result["counts"]["STOPPED"] == 0
    assert "HIT (correction)" in live[2].messages[100]["text"]
    assert len(live[0].list_outbox_messages(destination=scorecard.DESTINATION)) == 2


def test_uncertain_creation_never_sends_another_message(live):
    live[2].lose_create = True
    assert update(live, export(call("win")))["status"] == "UNKNOWN_WRITE"
    assert update(live, export(call("win")))["status"] == "UNKNOWN_WRITE"
    assert live[2].count("sendMessage") == 1


def test_lost_edit_return_is_read_back_before_any_further_write(live):
    update(live, export(call("win")))
    live[2].lose_edit = True
    value = export(call("win"), call("loss", "STOPPED"))
    assert update(live, value)["status"] == "UNKNOWN_WRITE"
    assert update(live, value)["status"] == "CONFIRMED"
    assert live[2].count("editMessageText") == 1


def test_exact_old_text_reconciles_a_failed_edit_before_safe_retry(live):
    update(live, export(call("win")))
    live[2].fail_edit_before_write = True
    value = export(call("win"), call("loss", "STOPPED"))
    assert update(live, value)["status"] == "UNKNOWN_WRITE"
    at = len(live[2].calls)
    assert update(live, value)["status"] == "CONFIRMED"
    assert live[2].calls[at][0] == "getChat" and live[2].count("sendMessage") == 1


def test_unknown_manual_text_does_not_authorize_another_edit(live):
    update(live, export(call("win")))
    live[2].lose_edit = True
    value = export(call("win"), call("loss", "STOPPED"))
    update(live, value)
    live[2].messages[100]["text"] = "A different, unrecognized edit"
    assert update(live, value)["status"] == "UNKNOWN_WRITE"
    assert live[2].count("editMessageText") == 1


def test_interrupted_pin_keeps_the_created_message(live):
    live[2].fail_pin = True
    assert update(live, export(call("win")))["status"] == "NOT_CONFIRMED"
    assert update(live, export(call("win")))["status"] == "CONFIRMED"
    assert live[2].count("sendMessage") == 1


def test_kill_switch_and_wrong_channel_prevent_public_writes(live):
    _set_mode(live[0], "KILL_SWITCH")
    assert update(live, export(call("win")))["status"] == "CONTROLLED_NO_PUBLIC_WRITE"
    assert live[2].calls == []
    _set_mode(live[0], "AUTONOMOUS_DEFAULT")
    live[2].username = "OtherChannel"
    assert update(live, export(call("win")))["status"] == "NOT_CONFIRMED"
    assert live[2].count("sendMessage") == 0


def test_an_active_exact_object_lease_prevents_duplicate_creation(live):
    live[0].acquire_lease(scorecard.WORK, "other-owner", ttl_seconds=180)
    assert update(live, export(call("win")))["status"] == "IN_PROGRESS"
    assert live[2].calls == []


def cli_module():
    spec = importlib.util.spec_from_file_location("cc394_cli", Path(__file__).parents[1] / "scripts/plan_status_posts.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_existing_publish_tick_consumes_main_rows_through_coordinator(live, monkeypatch, capsys):
    cli = cli_module()
    value = export(call("win"), call("loss", "STOPPED"))
    value["status"]["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    monkeypatch.setattr(scorecard, "read_export", lambda *a, **kw: value)
    monkeypatch.setattr(scorecard, "TelegramScorecardAPI", lambda: live[2])
    monkeypatch.setattr(cli, "queue_posts", lambda *a, **kw: {"status": "OK", "queued": []})
    monkeypatch.setattr(posts, "publish_ready", lambda *a, **kw: {"status": "OK", "posts": []})
    assert cli.main(["--publish", "--store", str(live[0].db_path)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["scorecard"]["counts"]["total"] == 2 and result["scorecard"]["status"] == "CONFIRMED"
    assert result["publication"]["posts"] == [] and live[2].count("sendMessage") == 1


def test_scorecard_preview_does_not_queue_or_touch_api(live, monkeypatch, capsys):
    cli = cli_module()
    value = export(call("win"))
    value["status"]["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    monkeypatch.setattr(scorecard, "read_export", lambda *a, **kw: value)
    monkeypatch.setattr(cli, "queue_posts", lambda *a, **kw: pytest.fail("scorecard-only queued feed posts"))
    monkeypatch.setattr(scorecard, "TelegramScorecardAPI", lambda: pytest.fail("preview touched the API"))
    assert cli.main(["--scorecard-only", "--dry-run", "--publish", "--store", str(live[0].db_path)]) == 0
    assert json.loads(capsys.readouterr().out)["scorecard"]["status"] == "PREVIEW"
    assert live[0].list_outbox_messages() == []


def test_transport_errors_never_expose_a_token_url(monkeypatch):
    from live_contentops import secret_store_v1
    monkeypatch.setattr(secret_store_v1, "read_secret", lambda name: "not-a-real-token")
    def fail(request, **kw):
        raise urllib.error.URLError(request.full_url)
    monkeypatch.setattr(scorecard.urllib.request, "urlopen", fail)
    with pytest.raises(scorecard.TelegramScorecardError) as caught:
        scorecard.TelegramScorecardAPI().call("getChat")
    assert str(caught.value) == "TELEGRAM_SCORECARD_TRANSPORT_UNCERTAIN"
    assert "not-a-real-token" not in str(caught.value)


@pytest.mark.parametrize("change", [
    lambda text: text.replace("| HIT", "| waiting"),
    lambda text: text.replace("2026-11-10 ET |", "Today |"),
    lambda text: text.replace("entry zone", "suggested entry"),
    lambda text: text + "\nThe market is bullish.",
])
def test_result_grammar_never_exempts_a_new_unconditional_call(change):
    text = scorecard.project(export(call("win")), now=NOW)["text"]
    with pytest.raises(ValueError, match="UNCONDITIONAL_CALL_FORBIDDEN"):
        scorecard.check_publication_copy({"body": change(text)})


def test_crash_after_saved_readback_preserves_the_first_observation(live, monkeypatch):
    real_status = live[0].set_outbox_status
    def interrupted(key, status):
        if status == "CONFIRMED":
            raise RuntimeError("simulated process interruption")
        return real_status(key, status)
    monkeypatch.setattr(live[0], "set_outbox_status", interrupted)
    with pytest.raises(RuntimeError, match="process interruption"):
        update(live, export(call("win")))
    before = live[0].list_outbox_messages(destination=scorecard.DESTINATION + "-readback")
    monkeypatch.setattr(live[0], "set_outbox_status", real_status)
    assert update(live, export(call("win")))["status"] == "CONFIRMED"
    assert live[0].list_outbox_messages(destination=scorecard.DESTINATION + "-readback") == before
    assert live[2].count("sendMessage") == 1 and live[2].count("editMessageText") == 0


def test_readback_clock_is_observation_time_separate_from_source_cutoff(live):
    observed = NOW + timedelta(seconds=17)
    live[1]._clock = lambda: observed
    result = update(live, export(call("win")))
    readback = live[0].get_outbox_message(result["revision"] + "-readback")
    assert json.loads(readback["payload"])["observed_at_utc"] == observed.isoformat()


@pytest.mark.parametrize("switch_after", ["getChat", "sendMessage"])
def test_kill_switch_changed_during_network_io_is_checked_before_next_write(live, switch_after, monkeypatch):
    original = live[2].call
    def switch(method, **fields):
        result = original(method, **fields)
        if method == switch_after:
            _set_mode(live[0], "KILL_SWITCH")
        return result
    monkeypatch.setattr(live[2], "call", switch)
    result = update(live, export(call("win")))
    assert result["cause"] == "SCORECARD_KILL_SWITCH"
    assert live[2].count("sendMessage") == int(switch_after == "sendMessage")
    assert live[2].count("pinChatMessage") == 0
