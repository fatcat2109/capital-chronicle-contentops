"""CC-400: the installed composer consumes tested exports and rejects drift before writes."""
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys

import pytest

from live_contentops import plan_status_posts_v1 as posts
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.plan_status_export_contract_v1 import LEGACY_CONTRACT, validate_export_contract
from test_plan_call_cards_cc399 import NOW, call, write
from test_plan_status_posts_cc306 import main_root  # noqa: F401


def export(tmp_path, *, version=None):
    raw = call("contract_call")
    fields = {"contract_version": version} if version is not None else {}
    folder = write(tmp_path / "export", [raw], [{"plan_id": raw["plan_id"], "status": "WAITING",
        "at_utc": raw["registered_at_utc"], "reason_code": "REGISTERED"}], **fields)
    return folder


def queue(store, folder, main_root, **kwargs):
    return posts.queue_posts(store, folder, now=NOW, main_root=main_root, python=sys.executable, **kwargs)


def incident_count(store):
    with store.get_read_only_connection() as conn:
        return conn.execute("SELECT count(*) FROM incidents").fetchone()[0]


def mutate(folder, document, transform):
    path = folder / document
    value = json.loads(path.read_bytes())
    transform(value)
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.mark.parametrize("version", [None, "2.0.0"])
def test_tested_formats_feed_the_live_composer_once(tmp_path, main_root, version):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite")
    folder = export(tmp_path, version=version)
    result = queue(store, folder, main_root)
    assert result["status"] == "OK" and len(result["queued"]) == 2
    expected = version or LEGACY_CONTRACT
    assert result["contract_version"] == expected
    payloads = [json.loads(row["payload"]) for row in store.list_outbox_messages(destination=posts.DESTINATION)]
    assert {p["source_contract_version"] for p in payloads} == {expected}
    assert any(p["kind"] == "setup" and "1.1241" in p["text"] for p in payloads)
    assert queue(store, folder, main_root)["queued"] == []
    assert incident_count(store) == 0


@pytest.mark.parametrize("version", ["9.0.0", "1.0.0", 2, None])
def test_unknown_version_queues_nothing_and_files_one_incident_across_repeats(tmp_path, main_root, version):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite")
    folder = export(tmp_path, version="9.0.0")
    mutate(folder, "plan-status.public.json", lambda value: value.update(contract_version=version))
    for _ in range(2):
        result = queue(store, folder, main_root)
        assert result["status"] == "EXPORT_CONTRACT_REJECTED"
        assert result["failed_field"] == "status.contract_version"
        assert str(version) in result["cause"]
    assert store.list_outbox_messages(destination=posts.DESTINATION) == []
    assert incident_count(store) == 1
    with store.get_read_only_connection() as conn:
        assert str(version) in conn.execute("SELECT description FROM incidents").fetchone()[0]
        assert conn.execute("SELECT count(*) FROM platform_dispatches").fetchone()[0] == 0


@pytest.mark.parametrize("document,transform,field", [
    ("plan-status.public.json", lambda value: value.update(calls=value.pop("plans")), "status.plans"),
    ("plan-status.public.json", lambda value: value["plans"][0].update(entry_zone=value["plans"][0].pop("zone")),
     "status.plans[0].zone"),
    ("plan-transitions.public.json", lambda value: value.update(events=value.pop("transitions")),
     "transitions.transitions"),
    ("plan-transitions.public.json", lambda value: value["transitions"][0].update(
        timestamp=value["transitions"][0].pop("at_utc")), "transitions.transitions[0].at_utc"),
])
def test_renamed_fields_fail_before_the_producer_reader_with_exact_path(tmp_path, main_root, document, transform, field):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite")
    folder = export(tmp_path, version="2.0.0")
    mutate(folder, document, transform)
    result = queue(store, folder, main_root, dry_run=True, render_all=True)
    assert result["status"] == "EXPORT_CONTRACT_REJECTED"
    assert result["failed_field"] == field and field in result["cause"]
    assert incident_count(store) == 0 and store.list_outbox_messages() == []


def test_dry_run_renders_already_queued_posts_and_all_destination_copies_without_store_writes(tmp_path, main_root):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite")
    folder = export(tmp_path, version="2.0.0")
    queue(store, folder, main_root)
    before = store.list_outbox_messages()
    result = queue(store, folder, main_root, dry_run=True, render_all=True)
    assert result["status"] == "OK" and result["rendered_count"] == 2
    assert {r["kind"] for r in result["rendered_posts"]} == {"run", "setup"}
    from live_contentops.plan_call_cards_v1 import DESTINATIONS
    # CC-435 keeps LinkedIn's run index and avoids a duplicate root per card.
    for row in result["rendered_posts"]:
        expected = set(DESTINATIONS) - ({"linkedin"} if row["kind"] == "setup" else set())
        assert set(row["destinations"]) == expected
    assert all(copy["text"] for row in result["rendered_posts"] for copy in row["destinations"].values())
    assert store.list_outbox_messages() == before and incident_count(store) == 0


def test_full_preview_preserves_normal_queue_and_fill_parent_decisions(tmp_path, main_root):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite")
    folder = export(tmp_path, version="2.0.0")
    first = queue(store, folder, main_root)
    setup = next(row for row in first["queued"] if row["kind"] == "setup")
    store.set_outbox_status(setup["key"], "PUBLISHED")
    mutate(folder, "plan-transitions.public.json", lambda value: value["transitions"].append({
        "plan_id": "contract_call", "status": "FILLED", "at_utc": "2026-11-10T07:59:00Z",
        "reason_code": "FILLED"}))
    normal = queue(store, folder, main_root, dry_run=True)
    preview = queue(store, folder, main_root, dry_run=True, render_all=True)
    assert normal["would_queue"] == preview["would_queue"]
    assert [row["kind"] for row in preview["would_queue"]] == ["update"]
    assert {row["key"] for row in preview["rendered_posts"]} == {
        *(row["key"] for row in first["queued"]), preview["would_queue"][0]["key"]}


def cli_module():
    spec = importlib.util.spec_from_file_location("cc400_cli", Path(__file__).parents[1] / "scripts/plan_status_posts.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    return cli


def test_cli_dry_run_enforces_sqlite_read_only_even_with_publish_flag(tmp_path, main_root, monkeypatch, capsys):
    cli = cli_module()
    store = ContentOpsDurableStore(tmp_path / "store.sqlite")
    folder = export(tmp_path, version="2.0.0")
    real_queue = posts.queue_posts
    observed = []

    def check_read_only(view, *args, **kwargs):
        with view.get_connection() as conn:
            with pytest.raises(sqlite3.OperationalError, match="readonly"):
                conn.execute("DELETE FROM incidents")
        observed.append(True)
        return real_queue(view, *args, now=NOW, **kwargs)

    monkeypatch.setattr(cli, "queue_posts", check_read_only)
    monkeypatch.setattr(posts, "publish_ready", lambda *a, **kw: pytest.fail("dry run called the publisher"))
    code = cli.main(["--dry-run", "--publish", "--store", str(store.db_path), "--export-dir", str(folder),
                     "--main-root", str(main_root)])
    result = json.loads(capsys.readouterr().out)
    assert code == 0 and result["validation"] == "PASS" and result["rendered_count"] == 2 and observed
    assert store.list_outbox_messages() == [] and incident_count(store) == 0
    assert not (store.db_path.parent / posts.RUN_RECORD_FOLDER).exists()


def test_cli_unknown_version_prevents_publish_and_reports_fail(tmp_path, main_root, monkeypatch, capsys):
    cli = cli_module()
    store = ContentOpsDurableStore(tmp_path / "store.sqlite")
    folder = export(tmp_path, version="99.0.0")
    monkeypatch.setattr(posts, "publish_ready", lambda *a, **kw: pytest.fail("unknown version reached publisher"))
    code = cli.main(["--publish", "--store", str(store.db_path), "--export-dir", str(folder),
                     "--main-root", str(main_root)])
    result = json.loads(capsys.readouterr().out)
    assert code == 1 and result["contract_version"] == "99.0.0" and result["incident_recorded"]
    assert incident_count(store) == 1 and store.list_outbox_messages() == []


def test_replay_cannot_be_enabled_for_a_writing_queue(tmp_path, main_root):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite")
    with pytest.raises(ValueError, match="REPLAY_REQUIRES_DRY_RUN"):
        queue(store, export(tmp_path), main_root, render_all=True)
    assert store.list_outbox_messages() == []


def test_explicit_unavailable_records_do_not_suppress_available_calls(tmp_path, main_root):
    folder = export(tmp_path)
    def add_unavailable(value):
        value["plans"][0].update(status=None, data_state="UNAVAILABLE", first_cause="OWNER_STATE_REASON_UNMAPPED")
        value["plans"].append({"plan_id": "unreadable", "asset_id": None, "status": None,
                               "data_state": "UNAVAILABLE", "first_cause": "INVALID_ARM"})
    mutate(folder, "plan-status.public.json", add_unavailable)
    store = ContentOpsDurableStore(tmp_path / "store.sqlite")
    result = queue(store, folder, main_root)
    assert result["status"] == "OK" and len(result["queued"]) == 2
    assert incident_count(store) == 0


def test_malformed_status_has_a_field_error_instead_of_an_attribute_error():
    from live_contentops.plan_status_export_contract_v1 import PlanExportContractError
    with pytest.raises(PlanExportContractError, match="FIELD_INVALID: status"):
        validate_export_contract({"status": [1], "transitions": {}})
