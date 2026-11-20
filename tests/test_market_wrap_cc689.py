from datetime import date, timedelta
from hashlib import sha256
import json

import pytest

from live_contentops import market_wrap_sources_v1 as sources
from live_contentops import market_wrap_editorial_v1 as editorial
from live_contentops import market_wrap_job_v1 as job
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.publication_coordinator_v1 import (
    CanonicalDestinationTransportRuntimeV1, DurablePublicationCoordinator,
)


def at(value):
    return sources.utc(value)


@pytest.fixture
def cash():
    return {"years": {
        "2026": {"closed": ["2026-11-26"], "early_close_13_et": ["2026-11-27"]},
        "2027": {"closed": [], "early_close_13_et": []},
    }}


def test_due_windows_follow_the_cash_open_and_close_calendar(cash):
    assert sources.slot_at(at("2026-11-20T13:00Z"), cash) is None
    assert sources.slot_at(at("2026-11-26T13:00Z"), cash) is None
    assert sources.slot_at(at("2026-11-28T13:00Z"), cash) is None
    monday = sources.slot_at(at("2026-11-23T13:00Z"), cash)
    assert monday["start_utc"] == "2026-11-23T13:00:00+00:00"
    assert monday["deadline_utc"] == "2026-11-23T13:45:00+00:00"
    friday = sources.slot_at(at("2026-11-27T13:00Z"), cash)
    assert friday["id"] == "cc689-daily-2026-11-27"
    sunday = sources.slot_at(at("2026-11-29T15:00Z"), cash)
    assert sunday["start_utc"] == "2026-11-29T15:00:00+00:00"
    assert sunday["deadline_utc"] == "2026-11-29T18:00:00+00:00"
    summer = sources.slot_at(at("2027-07-19T12:00Z"), cash)
    assert summer["deadline_utc"] == "2027-07-19T12:45:00+00:00"


def event(key="US_GDP_20261125", **overrides):
    return {"event_id": key, "title": "Gross Domestic Product", "source_url": "https://www.bea.gov/news",
            "source_timezone": "America/New_York", "scheduled_date": "2026-11-25",
            "scheduled_at_utc": "2026-11-25T13:30:00Z", "retrieved_at_utc": "2026-11-23T00:00Z",
            "public_use_allowed": True, "schedule_status": "PUBLISHER_SCHEDULE_SUBJECT_TO_REVISION",
            **overrides}


def test_calendar_binds_the_exact_et_row_and_keeps_date_only_precision():
    point = at("2026-11-24T14:00Z")
    doc = {"public_use_allowed": True, "built_at_utc": "2026-11-23T00:00Z",
           "events": [event(), event("DATE_ONLY", title="Publication date", scheduled_at_utc=None),
                      event("PRIVATE_EVENT", public_use_allowed=False),
                      event("FUTURE_REVISION", retrieved_at_utc="2026-11-25T00:00Z"),
                      event("INVALID_CLOCK", scheduled_date="2026-11-24")]}
    rows = sources.calendar_events(json.dumps(doc).encode(), point, point + timedelta(days=1), as_of=point)
    assert [(row["id"], row["time"]) for row in rows] == [
        ("DATE_ONLY", "Wed 25 Nov (date only)"), ("US_GDP_20261125", "Wed 25 Nov, 8:30 AM ET")]
    assert rows[-1]["row_sha256"] == sha256_of(event())


def test_latest_main_checks_receipt_and_only_uses_visible_analysis(tmp_path):
    old = tmp_path / "requests" / "complete"
    latest = tmp_path / "requests" / "latest"
    empty = {"native_synthesis": {"summary": [{"text": "Rates fell before the open."}],
             "candidates": [{"candidate_id": "cand_macro_gold", "rationale": "Gold followed yields lower.",
                             "execution_price": 8300}]},
             "primary_analysis": {"claims": [{"candidate_ids": ["cand_macro_gold"], "claim": "Options skew fell."}]}}
    for folder, stamp, digest in ((old, "2026-11-23T12:40Z", sha256_of(empty)),
                                  (latest, "2026-11-23T12:55Z", "wrong")):
        folder.mkdir(parents=True)
        (folder / "analysis-native.json").write_text(json.dumps(empty))
        (folder / "capture.json").write_text(json.dumps({"known_at_utc": stamp}))
        (folder / "analysis-end.json").write_text(json.dumps({"completed_at_utc": stamp, "output_sha256": digest}))
    result = sources.latest_main(at("2026-11-23T13:00Z"), tmp_path)
    assert result["run_id"] == "complete"
    assert result["layers"]["XAUUSD"]["Options"] == "Options skew fell."
    assert "8300" not in json.dumps(result)
    assert result["sha256"] == sha256((old / "analysis-native.json").read_bytes()).hexdigest()


def test_plan_projection_keeps_waiting_and_unknown_status_and_excludes_closed():
    now = at("2026-11-23T13:00Z")
    common = {"asset_id": "EURUSD", "registered_at_utc": "2026-11-23T12:00Z",
              "entry_deadline_utc": "2026-11-23T16:00Z", "horizon_lane": "SHORT"}
    rows = [{**common, "plan_id": key, "status": status}
            for key, status in (("a", "WAITING"), ("b", None), ("c", "CLOSED"), ("d", "FILLED"))]
    result = sources.project_plans({"status": {"generated_at_utc": now.isoformat(),
                                    "content_hash": "source", "plans": rows}}, now)
    assert {r["id"] for r in result["rows"]} == {"a", "b", "d"}
    assert "Status unavailable" in result["rows"][1]["text"]
    assert "7:00 AM ET" in result["rows"][1]["text"]


def test_normal_day_is_measured_on_its_own_instrument():
    first = date(2026, 11, 1)
    bars = {first + timedelta(days=i): (104 + i, 100 + i, 102 + i) for i in range(15)}
    assert sources.normal_day(bars, first + timedelta(days=14)) == 4
    start, end = {"symbol": "GC=F", "value": 100}, {"symbol": "GC=F", "value": 90}
    assert sources.move("XAUUSD", end, start, basis="since the last wrap", normal_day=4)["normal_days"] == -2.5
    with pytest.raises(ValueError, match="INSTRUMENT_MISMATCH"):
        sources.move("XAUUSD", {**end, "symbol": "XAU="}, start, basis="since the last wrap")


@pytest.fixture
def pack(cash):
    now = at("2026-11-23T13:00Z")
    first = {"symbol": "GC=F", "value": 100, "date": "2026-11-20"}
    quote = {"symbol": "GC=F", "value": 99, "observed_at_utc": now.isoformat()}
    return {
        "slot": sources.slot_at(now, cash),
        "markets": {"XAUUSD": sources.move("XAUUSD", quote, first, basis="since the last wrap", normal_day=4)},
        "analysis": {"at_utc": "2026-11-23T12:00Z", "layers": {
            "XAUUSD": {"Macro and catalysts": "Higher yields weighed on gold.", "Options": "Skew rose."}},
            "outlooks": {}},
        "data_cutoff_utc": now.isoformat(), "snapshots": {"XAUUSD": quote},
        "events": [{"id": "US_GDP_20261123", "name": "Gross Domestic Product", "time": "Mon 23 Nov, 8:30 AM ET",
                    "qualifier": "", "source_url": "https://www.bea.gov/news"}],
        "weekend_events": [], "plans": {"rows": [{"id": "plan_1", "text": "Gold, Waiting for entry."}]},
        "gaps": {"quote:US500": "unavailable"}, "weekly_calls": None,
    }


def select_first(prompt, **kwargs):
    options = json.loads(prompt.split("\n", 1)[1])
    result = {section: [{"id": key, "text": lines[0]} for key, lines in rows.items()]
              for section, rows in options.items()}
    return json.dumps(result).encode(), {"answered_by": kwargs["callers"][0]}


def test_edition_writer_binds_moves_and_events_to_exact_rows(tmp_path, pack):
    def wrong(prompt, **kwargs):
        answer, record = select_first(prompt, **kwargs)
        if kwargs["callers"] == ("codex",):
            return answer, record
        value = json.loads(answer)
        value["changes"][0]["text"] = value["changes"][0]["text"].replace("-1.00%", "+1.00%")
        value["events"][0]["text"] = value["events"][0]["text"].replace("8:30", "9:30")
        return json.dumps(value).encode(), record

    manuscript = editorial.draft(pack, tmp_path, call=wrong)
    article, markets = editorial.article_for(pack, manuscript)
    assert not markets
    assert "9:30" not in article["substack_body_markdown"]
    assert "+1.00%" not in article["substack_body_markdown"]
    assert "Gold, Waiting for entry." in article["substack_body_markdown"]
    assert json.loads((tmp_path / "wrap-changes/light-call.json").read_bytes())["result"] == "FAIL"


def test_codex_capacity_returns_desk_sections_to_antigravity(tmp_path, pack):
    callers = []

    def call(prompt, **kwargs):
        callers.extend(kwargs["callers"])
        if kwargs["callers"] == ("codex",):
            assert kwargs["codex_effort"] == "max"
            return b"", {"cause": "CODEX_QUOTA"}
        return select_first(prompt, **kwargs)

    manuscript = editorial.draft(pack, tmp_path, call=call)
    article, markets = editorial.article_for(pack, manuscript)
    assert callers == ["antigravity", "codex", "antigravity"]
    assert "Gross Domestic Product" in article["substack_body_markdown"]
    assert "Higher yields weighed on gold." in article["substack_body_markdown"]
    hit = article["substack_body_markdown"].count("Higher yields weighed on gold.")
    assert hit == 1
    asset = editorial.chart_for(pack, markets, tmp_path)
    assert (asset["width"], asset["height"]) == (1080, 1350)
    assert "Gold -0.25" in asset["alt_text"]
    link = "https://capitalchronicle.substack.com/p/pre-us-wrap"
    for route in ("x", "substack_notes", "instagram_business", "linkedin_company", "discord"):
        payload = editorial.derivative_payload(article, asset, link, route)
        assert link in payload["text"]
        assert payload["media_asset_ids"] == [asset["asset_id"]]


class LocalTransport(CanonicalDestinationTransportRuntimeV1):
    """Use the real canonical-link compiler; no external transport is called."""

    def __init__(self):
        super().__init__()
        self.writes = []
        self.reads = []

    def prepare_delivery_media(self, **_):
        return {"status": "CLOUDINARY_DELIVERY_MEDIA_READY"}

    def publish(self, *, destination, intent, authorization_context):
        self.writes.append((destination, intent))
        url = ("https://capitalchronicle.substack.com/p/pre-us-wrap-20261123" if destination == "substack"
               else None if destination == "discord" else f"https://example.test/{destination}/1")
        object_id = "12345" if destination == "discord" else f"{destination}-object-1"
        return {"status": "SUCCESS", "id": object_id, "public_url": url}

    def readback(self, *, destination, public_object_id, public_object_url, intent):
        self.reads.append(destination)
        return {"status": "SUCCESS", "verified": True, "public_object_id": public_object_id,
                "public_object_url": public_object_url,
                "published_at_utc": "2026-11-23T13:09:00Z"}


def test_normal_job_publishes_via_real_coordinator_and_reuses_retained_bytes(tmp_path, pack, cash, monkeypatch):
    from live_contentops import llm_operator_control_v1 as controls
    from live_contentops import publication_coordinator_v1 as publisher

    monkeypatch.setattr(controls, "llm_operator_pause_active", lambda *args, **kwargs: False)
    monkeypatch.setattr(publisher, "barred_browser_destinations", lambda: {})
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    transport = LocalTransport()
    now = at("2026-11-23T13:10Z")
    def factory(store, plan, **kwargs):
        coordinator = DurablePublicationCoordinator(store=store, transport_runtime=transport,
            readiness_provider=lambda _: {"readiness_state": "READY_NON_BROWSER_BINDING"},
            clock=lambda: now, published_content_path=tmp_path / "published.jsonl")
        coordinator.recovery_scope = {"work_item_id": plan["market_wrap"], "plan": plan, "exact_work_item_only": True}
        coordinator.allow_prior_confirmed_distribution = True
        return coordinator

    def publish(store, packet, *, clock):
        return job.continue_wrap(store, packet, clock=clock, factory=factory)

    def write(pack, root):
        return editorial.draft(pack, root, call=select_first)

    rollout = {"editorial_output_root": str(tmp_path)}
    out = job.run_due(store, rollout=rollout, now=now, clock=lambda: now, cash_calendar=cash,
        gather=lambda *_a, **_kw: pack, writer=write, publish=publish)
    publication = out["publication"]
    assert publication["canonical_url"] == "https://capitalchronicle.substack.com/p/pre-us-wrap-20261123", publication
    assert list(transport.writes)[0][0] == "substack"
    assert {destination for destination, _ in transport.writes} == {*job.ROUTES, "linkedin_company"}
    assert set(transport.reads) == {*job.ROUTES, "linkedin_company"}
    for destination, intent in transport.writes[1:]:
        assert publication["canonical_url"] in intent["native_payload"]["text"]
        assert len(intent["native_payload"]["media_asset_ids"]) == 1
    assert publication["per_destination"]["substack_notes"]["status"] == "DISPATCH_CONFIRMED"
    record, = (tmp_path / "published.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(record)["title"].startswith("Pre-US Market Wrap")
    retained = (job.output_path(rollout, pack["slot"]) / "article_manifest_v1.json").read_bytes()
    def unexpected(*args, **kwargs):
        pytest.fail("Re-entry must not recollect or rewrite a staged edition")
    repeated = job.run_due(store, rollout=rollout, now=now, clock=lambda: now, cash_calendar=cash,
        gather=unexpected, writer=unexpected, publish=publish)
    assert repeated["plan_hash"] == out["plan_hash"]
    assert len(transport.writes) == len(job.ROUTES) + 1
    assert (job.output_path(rollout, pack["slot"]) / "article_manifest_v1.json").read_bytes() == retained


def test_expired_job_cannot_start_new_drafts(tmp_path, cash):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    def unexpected(*args, **kwargs):
        pytest.fail("The cutoff precedes collection or any transport")
    now = at("2026-11-23T13:45Z")
    result = job.run_due(store, rollout={"editorial_output_root": str(tmp_path)}, now=now,
        clock=lambda: now, cash_calendar=cash, gather=unexpected, writer=unexpected, publish=unexpected)
    assert result["state"] == "WRAP_WINDOW_ELAPSED_WITHOUT_PACKET"
