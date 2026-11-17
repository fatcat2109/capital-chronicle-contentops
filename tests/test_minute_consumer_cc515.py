"""CC-515: the actual minute consumer isolates rows and settles dead destinations."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import sys
import textwrap

import pytest

from live_contentops import plan_status_posts_v1 as posts
from live_contentops import plan_call_cards_v1 as cards
from live_contentops import neo_endpoint_executor_v1 as neo
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.plan_status_export_contract_v1 import CONTRACT
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
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


def test_producer_only_row_validation_is_isolated_with_original_source_hashes(tmp_path, sealed_reader):
    path=sealed_reader / "schemas/publication/CapitalChroniclePlanStatusV1.schema.json"
    schema=json.loads(path.read_bytes())
    schema["properties"]["plans"]["items"]["else"]["properties"]["status_label"]={"enum":["Waiting"]}
    path.write_text(json.dumps(schema),encoding="utf-8")
    folder,source,_=sealed_export(tmp_path,[call("good"),call("bad",status_label="Unknown label")])
    store=ContentOpsDurableStore(tmp_path / "store.sqlite3")
    result=queue(store,folder,sealed_reader)
    assert result["status"]=="OK" and set(result["latest_states"])=={"good"}
    failure=result["quarantined_rows"][0]
    assert failure["plan_id"]=="bad" and failure["field"]=="status.plans[1].status_label"
    export=posts.read_export(folder,main_root=sealed_reader,python=sys.executable)
    assert export["status"]["content_hash"]==source["content_hash"]
    assert export["consumer_projection"]["status_content_hash"]!=source["content_hash"]


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


def retained(store, key, *, hours=1, status=posts.READY, kind="update", **fields):
    row = {"schema_version": posts.SCHEMA, "key": key, "format": 4, "kind": kind,
        "plan_id": "plan-" + key, "at_utc": (NOW - timedelta(hours=hours)).isoformat(), **fields}
    store.create_work_item(story_id=key, work_item_id=key,
        title="Call run" if kind == "run" else "Call card", target_surface="MULTI_PLATFORM")
    store.register_outbox_message(message_id=key, work_item_id=key, destination=posts.DESTINATION,
        status=status, payload=json.dumps(row))
    return row


def dispatch(store, row, destination, status, *, public_id=None):
    ids = DurablePublicationCoordinator._ids(row["key"],
        sha256(("plan-status-post:" + row["key"]).encode()).hexdigest(), destination)
    intent = {"work_item_id": row["key"], "plan_hash": sha256(
        ("plan-status-post:" + row["key"]).encode()).hexdigest(), "plan_status_post": row["key"]}
    store.register_outbox_message(message_id=ids["message_id"], work_item_id=row["key"],
        destination=destination, payload=json.dumps(intent), status=status)
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
        platform=destination, status=status, public_object_id=public_id)
    return ids


def test_child_of_definite_no_write_parent_settles_only_that_destination(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    parent = retained(store, "parent", kind="setup")
    child = retained(store, "child", parent_key=parent["key"])
    dispatch(store, parent, "x", "DEFINITE_NO_WRITE")
    dispatch(store, parent, "discord", "DISPATCH_CONFIRMED", public_id="123")
    before = store.get_outbox_message(child["key"])["payload"]
    assert cards.settle_pending(store, store.get_outbox_message(child["key"]), child, now=NOW) is None
    settled = cards.settled_destinations(store, child)
    assert set(settled) == {"x"} and settled["x"]["cause"] == "CARD_PARENT_DEFINITE_NO_WRITE"
    assert cards._ready_destinations(store, child) == ["discord"]
    assert store.get_outbox_message(child["key"])["payload"] == before
    assert store.get_outbox_message(child["key"])["status"] == posts.READY


def test_child_of_live_parent_is_left_alone(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    parent = retained(store, "parent", kind="setup")
    child = retained(store, "child", parent_key=parent["key"])
    dispatch(store, parent, "x", "DISPATCH_CONFIRMED", public_id="123")
    before = store.get_outbox_message(child["key"])
    assert cards.settle_pending(store, before, child, now=NOW) is None
    assert not cards.settled_destinations(store, child)
    assert "x" in cards._ready_destinations(store, child)
    assert store.get_outbox_message(child["key"]) == before


def test_recent_child_of_parent_past_late_limit_closes_without_waiting_another_day(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    parent = retained(store, "parent", hours=25, kind="setup")
    child = retained(store, "child", parent_key=parent["key"])
    result = cards.settle_pending(store,store.get_outbox_message(child["key"]),child,now=NOW)
    assert result["status"] == "SETTLED"
    assert set(result["destination_causes"].values()) == {"CARD_PARENT_NOT_CONFIRMED"}


@pytest.mark.parametrize("hours,closed", [(24, False), (24.001, True)])
def test_unconfirmed_parent_obeys_existing_late_state_limit(tmp_path, hours, closed):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    child = retained(store, "child", hours=hours, parent_key="unwritten")
    result = cards.settle_pending(store, store.get_outbox_message(child["key"]), child, now=NOW)
    assert bool(result) is closed
    if closed:
        assert result["status"] == "SETTLED"
        assert set(result["destination_causes"].values()) == {"CARD_PARENT_NOT_CONFIRMED"}


def test_late_publishing_settles_work_but_preserves_confirmed_and_uncertain_dispatches(tmp_path, monkeypatch):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    row = retained(store, "old", hours=25, status="PUBLISHING")
    confirmed = dispatch(store, row, "discord", "DISPATCH_CONFIRMED", public_id="123")
    uncertain = dispatch(store, row, "x", "UNKNOWN_WRITE")
    original = {k: store.get_platform_dispatch(v["dispatch_id"]) for k,v in
                (("confirmed", confirmed), ("uncertain", uncertain))}
    before = store.get_outbox_message(row["key"])["payload"]
    monkeypatch.setattr(cards, "prepare_post", lambda *a,**kw: pytest.fail("late work must not render or send"))
    first = cards.publish_ready(store, now=NOW, root=tmp_path)
    assert first["posts"][0]["status"] == "SETTLED"
    assert first["posts"][0]["per_destination"]["discord"] == "DISPATCH_CONFIRMED"
    assert first["posts"][0]["destination_causes"]["x"] == "PUBLISHING_OLDER_THAN_24_HOURS"
    assert cards.publish_ready(store, now=NOW, root=tmp_path)["posts"] == []
    assert store.get_platform_dispatch(confirmed["dispatch_id"]) == original["confirmed"]
    assert store.get_platform_dispatch(uncertain["dispatch_id"]) == original["uncertain"]
    assert store.get_outbox_message(uncertain["message_id"])["status"] == cards.SETTLED_COPY
    assert store.get_outbox_message(row["key"])["payload"] == before
    c = DurablePublicationCoordinator(store=store, transport_runtime=object())
    c.recovery_scope = {"work_item_id":row["key"], "exact_work_item_only":True}
    assert uncertain["message_id"] not in {m["message_id"] for m in c._recovery_messages()}
    # An explicitly requested readback still has its original intent and UNKNOWN_WRITE.
    c.recovery_scope = None
    observed = []
    monkeypatch.setattr(c, "_reconcile", lambda dispatch,intent: observed.append(dispatch["dispatch_id"]) or
                        "RECONCILIATION_PENDING")
    result = c.readback_existing_dispatch(uncertain["dispatch_id"])
    assert observed == [uncertain["dispatch_id"]] and result["publish_called"] is False
    assert uncertain["message_id"] not in {m["message_id"] for m in c._recovery_messages()}


def test_each_definite_no_write_keeps_its_own_cause_not_just_the_first_day_incident(tmp_path, monkeypatch):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    row = retained(store, "post")
    ids = dispatch(store,row,"discord","DEFINITE_NO_WRITE")
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=object())
    monkeypatch.setattr(coordinator, "_dispatch_message_once", lambda *a,**kw: {
        "status":"DEFINITE_NO_WRITE", "reason_code":"EXACT_TEST_PREWRITE_CAUSE", "publish_called":False})
    message = store.get_outbox_message(ids["message_id"])
    for _ in range(2):
        assert coordinator._dispatch_message(message,canonical_url=None)["status"] == "DEFINITE_NO_WRITE"
    recorded = store.list_readbacks_for_dispatch(ids["dispatch_id"])
    assert len(recorded) == 1
    assert json.loads(recorded[0]["readback_data"])["reason_code"] == "EXACT_TEST_PREWRITE_CAUSE"


def test_possibly_sent_child_keeps_readback_while_recent(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    parent = retained(store, "parent", kind="setup")
    child = retained(store, "child", parent_key=parent["key"], status="PUBLISHING")
    dispatch(store, parent, "x", "DEFINITE_NO_WRITE")
    ids = dispatch(store, child, "x", "UNKNOWN_WRITE")
    cards.settle_pending(store, store.get_outbox_message(child["key"]), child, now=NOW)
    assert "x" not in cards.settled_destinations(store, child)
    assert "x" in cards._ready_destinations(store, child)
    assert store.get_platform_dispatch(ids["dispatch_id"])["status"] == "UNKNOWN_WRITE"


def test_card_budget_goes_to_newest_live_post_after_dead_work_closes(tmp_path, monkeypatch):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    retained(store, "dead", hours=25, parent_key="never-written")
    old = retained(store, "older", hours=2, kind="setup")
    new = retained(store, "newest", hours=1, kind="setup")
    reached = []
    monkeypatch.setattr(cards, "prepare_post", lambda s,k,**kw: {
        "plan_status_post":k, "destinations":[{"destination":"discord"}],
        "output_dir":str(tmp_path), "deferred_destinations":[]})
    class Coordinator:
        def register_plan(self,*a):
            pass
        def execute_plan(self,key,plan):
            reached.append(key)
            return {"per_destination":{"discord":{"status":"DISPATCH_CONFIRMED"}}}
    result = cards.publish_ready(store, now=NOW, root=tmp_path, limit=1,
                                 coordinator_for=lambda *a: Coordinator())
    assert reached == [new["key"]], result
    assert store.get_outbox_message("dead")["status"] == "SETTLED"
    assert next(r for r in result["posts"] if r["key"] == old["key"])["cause"] == "CARD_WORK_LIMIT_THIS_RUN"


def test_closed_post_cannot_spend_a_stored_browser_slot(tmp_path, monkeypatch):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    row = retained(store, "old", hours=25, status="PUBLISHING")
    ids = dispatch(store,row,"x","UNKNOWN_WRITE")
    from live_contentops.native_neo_executor_v1 import NativeNeoExecutor, SCHEMA, DESTINATION
    executor = NativeNeoExecutor(store,operation_id=row["key"],output_dir=tmp_path,native_invocation_id="fixture")
    request = {"action":"READBACK","destination":"x","request_sha256":"a"*64,
               "work_item_id":row["key"],"dispatch_attempt_identity":ids["dispatch_id"]}
    packet = {"schema_version":SCHEMA,"operation_id":row["key"],"request":request}
    store.register_outbox_message(message_id=executor._key(request["request_sha256"],"request"),
        work_item_id=row["key"],destination=DESTINATION,payload=json.dumps(packet),status="NATIVE_NEO_INTERNAL")
    cards.settle_pending(store,store.get_outbox_message(row["key"]),row,now=NOW)
    monkeypatch.setattr(__import__("live_contentops.native_neo_executor_v1",fromlist=["bind_native_neo_coordinator"]),
        "bind_native_neo_coordinator",lambda *a,**kw: pytest.fail("closed work cannot bind a browser"))
    assert neo.resume_stored_requests(store)["requests"] == []


def test_stored_browser_budget_goes_to_the_newest_live_post(tmp_path, monkeypatch):
    from live_contentops.native_neo_executor_v1 import SCHEMA, DESTINATION
    store=ContentOpsDurableStore(tmp_path / "store.sqlite3")
    for key,hours in (("older",2),("newer",1)):
        row=retained(store,key,hours=hours,status="PUBLISHING",
                     at_utc=(datetime.now(timezone.utc)-timedelta(hours=hours)).isoformat())
        ids=dispatch(store,row,"x","UNKNOWN_WRITE")
        request={"action":"READBACK","destination":"x","request_sha256":key*8,
            "work_item_id":key,"dispatch_attempt_identity":ids["dispatch_id"]}
        packet={"schema_version":SCHEMA,"operation_id":key,"request":request}
        store.register_outbox_message(message_id="request-"+key,work_item_id=key,destination=DESTINATION,
            payload=json.dumps(packet),status="NATIVE_NEO_INTERNAL")
    reached=[]
    class Coordinator:
        _ids=staticmethod(DurablePublicationCoordinator._ids)
        def _effective_message(self,message):
            return message
        def readback_existing_dispatch(self,dispatch_id):
            return {"reconciliation_status":"RECONCILIATION_PENDING"}
    class Executor:
        def __call__(self,request):
            reached.append(request["work_item_id"])
            return {"status":"READBACK_UNAVAILABLE"}
    monkeypatch.setattr(__import__("live_contentops.native_neo_executor_v1",fromlist=["bind_native_neo_coordinator"]),
        "bind_native_neo_coordinator",lambda *a,**kw:(Coordinator(),Executor()))
    result=neo.resume_stored_requests(store,limit=1)
    assert reached==["newer"] and len(result["requests"])==1


def test_minute_record_reports_live_queue_after_settlement_without_losing_recent_work(tmp_path, monkeypatch):
    from live_contentops import plan_analysis_pages_v1 as pages
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    old = retained(store, "old", hours=25, status="PUBLISHING")
    fresh = retained(store, "fresh", hours=1, kind="setup")
    monkeypatch.setattr(pages, "distribute_links", lambda *a, **kw: {"links": []})
    monkeypatch.setattr(cards, "prepare_post", lambda *a, **kw: pytest.fail("zero budget cannot send"))
    result = posts.publish_ready(store, now=NOW, root=tmp_path, limit=0)
    assert store.get_outbox_message(old["key"])["status"] == cards.SETTLED_POST
    assert store.get_outbox_message(fresh["key"])["status"] == posts.READY
    assert result["pending_post_queue"] == {"pending": 1, "older_than_24_hours": 0,
                                            "oldest_age_minutes": 60.0}
    path = posts.record_run({"status": "OK", "publication": result}, tmp_path / "runs", now=NOW)
    assert json.loads(path.read_text())["pending_post_queue"] == result["pending_post_queue"]
