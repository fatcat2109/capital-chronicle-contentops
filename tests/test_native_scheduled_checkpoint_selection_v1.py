"""Mixed outbox startup regressions in disposable stores, never live windows."""
# ruff: noqa: F811
import json
from pathlib import Path

import pytest

import live_contentops.native_desktop_schedule_binding_v1 as schedule
from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import DESTINATION
from test_native_scheduled_continuity_v1 import AUTO, at, rollout, start  # noqa: F401 - pytest fixture


def save_dispositions(store):
    work = "controlled-expired-window"
    store.create_work_item(story_id=work, work_item_id=work, title="Controlled closure", target_surface="TEST")
    for index in range(4):
        run_id = f"controlled-expired-slot-{index}"
        store.register_outbox_message(message_id="native-window-disposition-" + sha256_of(run_id),
            work_item_id=work, destination=DESTINATION, status="EDITORIAL_INTERNAL",
            payload=canonical_bytes({"classification": "NATIVE_WINDOW_PROCESS_DISPOSITION", "run_id": run_id,
                "outcome": "PROCESS_FAILURE", "first_cause": "CONTROLLED_STOPPED_WINDOW",
                "qualified_article_count": 0, "public_write_performed": False}).decode())


@pytest.mark.parametrize("automation_id,hour", [
    ("v1-newsroom-brief-asia-0900", 2),
    ("v1-newsroom-brief-europe-1500", 8),
    ("v1-newsroom-london-1700", 10),
    ("v1-newsroom-brief-us-1900", 12),
    ("v1-newsroom-new-york-2100", 14),
    ("v1-newsroom-new-york-2300", 16),
    ("v1-newsroom-new-york-0100", 18),
])
def test_scheduled_cli_starts_and_replays_with_four_saved_dispositions(
        rollout, monkeypatch, tmp_path, capsys, automation_id, hour):
    from scripts import run_native_desktop_editorial as cli

    _, _, old_path = start(rollout)
    old_bytes = old_path.read_bytes()
    store = ContentOpsDurableStore(rollout["store_path"], auto_migrate=False)
    save_dispositions(store)
    before = {row["message_id"]: row for row in store.list_outbox_messages()}
    moment = at(f"2026-11-02T{hour:02d}:00:00Z")
    original = schedule.scheduled_binding
    monkeypatch.setattr(schedule, "scheduled_binding", lambda *args, **kwargs: original(*args, **kwargs, now=moment))
    monkeypatch.setattr(cli, "operation", lambda *_args, **_kwargs: pytest.fail("startup advanced editorial work"))
    config = tmp_path / "rollout.json"
    config.write_bytes(canonical_bytes(rollout))
    argv = ["scheduled", "--automation-id", automation_id, "--rollout", str(config)]

    exit_code = cli.main(argv)
    first = json.loads(capsys.readouterr().out)
    assert exit_code == 0, first
    assert first["classification"] == "NATIVE_WINDOW_SLOT_READY"
    assert first["resumed_existing_binding"] is False and first["public_write_performed"] is False
    path = Path(first["binding_path"])
    binding_bytes = path.read_bytes()
    binding = json.loads(binding_bytes)
    assert binding["automation_id"] == automation_id
    assert binding["cutoff_utc"] == f"2026-11-02T{hour:02d}:00:00Z"
    after_start = store.list_outbox_messages()
    assert all(row == before[row["message_id"]] for row in after_start if row["message_id"] in before)

    monkeypatch.setattr(schedule, "load_canonical_published_memory_read_only",
        lambda **_: pytest.fail("duplicate startup read fresh source context"))
    assert cli.main(argv) == 0
    replay = json.loads(capsys.readouterr().out)
    assert replay["binding_path"] == str(path) and replay["resumed_existing_binding"] is True
    assert replay["model_invocations"] == replay["source_requests"] == 0
    assert path.read_bytes() == binding_bytes and old_path.read_bytes() == old_bytes
    assert store.list_outbox_messages() == after_start
    assert store.list_platform_dispatches() == []


def test_latest_checkpoint_keeps_session_and_opportunity_selection_read_only(rollout):
    old, _, _ = start(rollout)
    latest, _, _ = start(rollout, "2026-10-27T14:05:00Z")
    london = schedule.scheduled_binding(rollout, "v1-newsroom-london-1700", now=at("2026-10-28T10:00:00Z"))
    store = ContentOpsDurableStore(rollout["store_path"], auto_migrate=False)
    save_dispositions(store)
    before = store.list_outbox_messages()

    assert schedule._latest_window(store, "new_york_2100_bangkok")["window"]["opportunity_id"] == latest["window_id"]
    assert schedule._latest_window(store, "new_york_2100_bangkok",
        opportunity_id=old["window_id"])["window"]["opportunity_id"] == old["window_id"]
    assert schedule._latest_window(store, "london_1700_bangkok")["window"]["opportunity_id"] == london["window_id"]
    assert schedule._latest_window(store, "new_york_2100_bangkok", opportunity_id="controlled-absent") is None
    assert store.list_outbox_messages() == before


def test_disposition_only_store_is_not_a_checkpoint_even_if_its_payload_is_malformed(rollout):
    store = ContentOpsDurableStore(rollout["store_path"])
    save_dispositions(store)
    with store.get_connection() as conn:
        conn.execute("UPDATE outbox_messages SET payload=? WHERE message_id=?",
            ("{malformed-non-checkpoint", "native-window-disposition-" + sha256_of("controlled-expired-slot-0")))
    before = store.list_outbox_messages()
    assert schedule._latest_window(store, "new_york_2100_bangkok") is None
    assert store.list_outbox_messages() == before


@pytest.mark.parametrize("damage", [
    "invalid_json", "not_object", "missing_window", "window_not_object", "missing_session",
    "missing_opportunity", "missing_start", "invalid_start", "changed_id", "short_id", "nonhex_id", "changed_day",
])
def test_malformed_checkpoint_is_rejected_without_replacement(rollout, damage):
    _, binding, path = start(rollout)
    binding_bytes = path.read_bytes()
    store = ContentOpsDurableStore(rollout["store_path"], auto_migrate=False)
    key = "native-window-" + sha256_of(binding["window_id"])
    checkpoint = json.loads(store.get_outbox_message(key)["payload"])
    changed_key = key
    if damage == "changed_id":
        changed_key = "native-window-" + "0" * 64
    elif damage == "short_id":
        changed_key = "native-window-controlled-changed-key"
    elif damage == "nonhex_id":
        changed_key = "native-window-" + "g" * 64
    elif damage == "changed_day":
        checkpoint["production_day_id"] = "newsroom-production-day-1900-01-01-bangkok"
    elif damage == "missing_window":
        checkpoint.pop("window")
    elif damage == "window_not_object":
        checkpoint["window"] = []
    elif damage in {"missing_session", "missing_opportunity", "missing_start"}:
        checkpoint["window"].pop({"missing_session": "session", "missing_opportunity": "opportunity_id",
            "missing_start": "start_utc"}[damage])
    elif damage == "invalid_start":
        checkpoint["window"]["start_utc"] = "controlled-invalid-time"
    payload = "{broken" if damage == "invalid_json" else "[]" if damage == "not_object" else json.dumps(checkpoint)
    with store.get_connection() as conn:
        conn.execute("UPDATE outbox_messages SET message_id=?,payload=? WHERE message_id=?", (changed_key, payload, key))
    before = store.list_outbox_messages()

    with pytest.raises(ValueError, match="^NATIVE_SCHEDULE_WINDOW_BINDING_CHANGED$"):
        schedule.scheduled_binding(rollout, AUTO, now=at("2026-10-26T14:05:00Z"))
    assert store.list_outbox_messages() == before and path.read_bytes() == binding_bytes
    assert len(list(Path(rollout["editorial_output_root"]).glob("**/native_operation_binding.json"))) == 1
