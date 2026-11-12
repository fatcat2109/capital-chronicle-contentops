"""CC-515: the actual minute consumer isolates rows and settles dead destinations."""
from datetime import timedelta
import json
from pathlib import Path
import sys
import textwrap

import pytest

from live_contentops import plan_status_posts_v1 as posts
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.plan_status_export_contract_v1 import CONTRACT
from test_plan_call_cards_cc399 import NOW, call


@pytest.fixture
def sealed_reader(tmp_path):
    """An isolated producer with real seals, schemas and snapshot joins."""
    root = tmp_path / "main"
    module = root / "tools/product/plan_status_export_v1.py"
    module.parent.mkdir(parents=True)
    module.write_text(textwrap.dedent('''
        import hashlib, json
        from pathlib import Path
        from jsonschema import Draft202012Validator
        class PlanStatusError(ValueError):
            pass
        def sha256(value):
            return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
        def _seal(value):
            if value.get('content_hash') != sha256({k:v for k,v in value.items() if k != 'content_hash'}):
                raise PlanStatusError('OWNER_SEAL_INVALID')
            return value
        def validate_public_status(value, *, as_of):
            value = _seal(value)
            schema = json.loads((Path(__file__).parents[2]/'schemas/publication/CapitalChroniclePlanStatusV1.schema.json').read_bytes())
            if list(Draft202012Validator(schema).iter_errors(value)):
                raise PlanStatusError('PUBLIC_PLAN_STATUS_SCHEMA_INVALID')
            return value
        def read_public_status(path, *, as_of):
            return validate_public_status(json.loads(Path(path).read_bytes()),as_of=as_of)
        def read_public_transitions(path, *, status):
            value = _seal(json.loads(Path(path).read_bytes()))
            if value['status_content_hash'] != status['content_hash'] or value['generated_at_utc'] != status['generated_at_utc']:
                raise PlanStatusError('PUBLIC_PLAN_SNAPSHOT_MISMATCH')
            if any(row['plan_id'] not in {p['plan_id'] for p in status['plans']} for row in value['transitions']):
                raise PlanStatusError('PUBLIC_PLAN_TRANSITION_CONFLICT')
            return value
    '''), encoding="utf-8")
    for document, name in (("status", "CapitalChroniclePlanStatusV1"),
                           ("transitions", "CapitalChroniclePlanTransitionsV1")):
        path = root / "schemas/publication" / (name + ".schema.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(CONTRACT["properties"][document]), encoding="utf-8")
    return root


def sealed_export(tmp_path, plans, events=None):
    folder = tmp_path / "export"
    folder.mkdir()
    status = {"schema": "CapitalChroniclePlanStatusV1", "schema_version": "1.0.0",
        "contract_version": "2.0.0", "generated_at_utc": NOW.isoformat(), "plans": plans,
        "record_summary": {"judged_count": 0}}
    status["content_hash"] = posts._sha(status)
    transitions = {"schema": "CapitalChroniclePlanTransitionsV1", "schema_version": "1.0.0",
        "generated_at_utc": status["generated_at_utc"], "status_content_hash": status["content_hash"],
        "transitions": events if events is not None else [
            {"plan_id": p["plan_id"], "status": "WAITING", "at_utc": p["registered_at_utc"],
             "reason_code": "REGISTERED"} for p in plans]}
    transitions["content_hash"] = posts._sha(transitions)
    for name, value in (("plan-status.public.json", status), ("plan-transitions.public.json", transitions)):
        (folder / name).write_text(json.dumps(value), encoding="utf-8")
    return folder, status, transitions


def queue(store, folder, reader, **kwargs):
    return posts.queue_posts(store, folder, now=NOW, main_root=reader, python=sys.executable, **kwargs)


@pytest.mark.parametrize("bad", [
    {"status": "NEW_STATE"}, {"direction": "SIDEWAYS"}, {"zone": {}}, {"entries": [{"kind": "NEW_ENTRY"}]},
])
def test_unknown_row_is_set_aside_but_good_plan_reaches_live_queue_and_incident(tmp_path, sealed_reader, bad):
    folder, status, _ = sealed_export(tmp_path, [call("good"), call("bad", **bad)])
    before = {p.name: p.read_bytes() for p in folder.iterdir()}
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    for _ in range(2):
        result = queue(store, folder, sealed_reader)
        assert result["status"] == "OK"
        rejected = result["quarantined_rows"]
        assert rejected[0]["plan_id"] == "bad" and rejected[0]["incident_recorded"]
        assert "PLAN_EXPORT_CONTRACT_ROW_INVALID" in rejected[0]["cause"]
    rows = [json.loads(r["payload"]) for r in store.list_outbox_messages(destination=posts.DESTINATION)]
    assert any(r.get("plan_id") == "good" and r["kind"] == "setup" for r in rows)
    assert not any(r.get("plan_id") == "bad" for r in rows)
    assert all(r.get("source_content_hash") == status["content_hash"] for r in rows)
    with store.get_read_only_connection() as conn:
        assert conn.execute("SELECT count(*) FROM incidents").fetchone()[0] == len(rejected)
    assert {p.name: p.read_bytes() for p in folder.iterdir()} == before
    record = posts.record_run(result, tmp_path / "runs", now=NOW)
    assert json.loads(record.read_text())["quarantined_rows"] == rejected


def test_unknown_transition_sets_aside_its_plan_and_preserves_other_plans(tmp_path, sealed_reader):
    good, bad = call("good"), call("bad")
    folder, _, _ = sealed_export(tmp_path, [good, bad], [
        {"plan_id": p["plan_id"], "status": "WAITING" if p is good else "NEW_STATE",
         "at_utc": p["registered_at_utc"], "reason_code": "REGISTERED"} for p in (good, bad)])
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    result = queue(store, folder, sealed_reader)
    assert result["status"] == "OK" and result["quarantined_rows"][0]["plan_id"] == "bad"
    assert set(result["latest_states"]) == {"good"}


@pytest.mark.parametrize("failure", ["hash", "schema", "join", "duplicates", "unreadable"])
def test_bad_whole_file_is_refused_even_with_unknown_row(tmp_path, sealed_reader, failure):
    plans = [call("good"), call("bad", status="NEW_STATE")]
    if failure == "duplicates":
        plans[1]["plan_id"] = "good"
    folder, status, transitions = sealed_export(tmp_path, plans)
    if failure == "unreadable":
        (folder / "plan-status.public.json").write_text("{", encoding="utf-8")
    elif failure != "duplicates":
        if failure == "hash":
            status["content_hash"] = "0" * 64
        elif failure == "schema":
            status["schema"] = "UnknownSchema"
        else:
            transitions["status_content_hash"] = "0" * 64
            transitions["content_hash"] = posts._sha({k:v for k,v in transitions.items() if k != "content_hash"})
        (folder / "plan-status.public.json").write_text(json.dumps(status), encoding="utf-8")
        (folder / "plan-transitions.public.json").write_text(json.dumps(transitions), encoding="utf-8")
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    result = queue(store, folder, sealed_reader)
    assert result["status"] in {"EXPORT_UNREADABLE", "EXPORT_CONTRACT_REJECTED"}
    assert store.list_outbox_messages(destination=posts.DESTINATION) == []


def test_dry_run_reports_quarantine_without_recording_an_incident(tmp_path, sealed_reader):
    folder, _, _ = sealed_export(tmp_path, [call("good"), call("bad", status="NEW_STATE")])
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    result = queue(store, folder, sealed_reader, dry_run=True)
    assert result["status"] == "OK" and not result["quarantined_rows"][0]["incident_recorded"]
    assert any(r["kind"] == "setup" for r in result["would_queue"])
    with store.get_read_only_connection() as conn:
        assert conn.execute("SELECT count(*) FROM incidents").fetchone()[0] == 0

