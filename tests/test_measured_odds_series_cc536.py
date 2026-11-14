from copy import deepcopy
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest

from live_contentops import measured_odds_series_v1 as odds
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator

SOURCE = Path(__file__).resolve().parents[1] / "docs/publisher/CC-536"


@pytest.fixture
def piece():
    return json.loads((SOURCE / "piece-1.json").read_bytes())


def test_every_method_numeral_has_exact_main_binding(piece):
    report = odds.validate_piece(piece, SOURCE / "source")
    assert [r["number"] for r in report] == ["54", "2016", "2026", "20", "60", "20", "50", "14", "0.05", "54"]
    assert all(r["table_hash"] == piece["table_hash"] for r in report)


def test_unbound_public_number_is_rejected(piece):
    piece["article"]["social_summary"] += " We found 99 winners."
    with pytest.raises(ValueError, match="ODDS_UNBOUND_PUBLIC_NUMBER"):
        odds.validate_piece(piece, SOURCE / "source")


def test_a_different_value_is_not_blessed_by_a_valid_source_path(piece):
    claim = piece["number_bindings"][0]
    piece["article"][claim["field"]] = piece["article"][claim["field"]].replace("54 market", "55 market")
    claim["span"] = claim["span"].replace("54 market", "55 market")
    with pytest.raises(ValueError, match="ODDS_NUMBER_DIFFERS_FROM_SOURCE:55"):
        odds.number_report(piece, SOURCE / "source")


def test_source_bytes_are_checked_before_use(piece, tmp_path):
    shutil.copytree(SOURCE / "source", tmp_path / "source")
    table = tmp_path / "source/desk_odds_v1.json"
    table.write_bytes(table.read_bytes() + b" ")
    with pytest.raises(ValueError, match="ODDS_SOURCE_BYTES_CHANGED"):
        odds.validate_piece(piece, tmp_path / "source")


def _extra(piece, span, file, pointer, **kw):
    piece["article"]["social_summary"] = span
    piece["number_bindings"].append({"field":"social_summary","span":span,"file":file,"pointer":pointer,**kw})


def test_pooled_row_cannot_be_quoted_for_a_side(piece):
    _extra(piece, "Bitcoin short 0.531R.", "desk_odds_v1.json", "/by_market/BTCUSD/6", side="SHORT")
    with pytest.raises(ValueError, match="ODDS_ONE_SIDE_REQUIRES_SIDE_FILE"):
        odds.number_report(piece, SOURCE / "source")


def test_side_must_match_source_and_table_hash(piece):
    prefix = "/tables/"+piece["table_hash"]+"/markets/BTCUSD/sides/BREAKOUT_WITH_TREND_20/LONG/2"
    _extra(piece, "Bitcoin short 0.1R.", "desk_odds_sides_v1.json", prefix, side="SHORT")
    with pytest.raises(ValueError, match="ODDS_EXACT_SIDE_REQUIRED"):
        odds.number_report(piece, SOURCE / "source")
    piece["number_bindings"][-1]["pointer"] = prefix.replace(piece["table_hash"], "0"*64)
    with pytest.raises(ValueError, match="ODDS_SIDE_TABLE_HASH_REQUIRED"):
        odds.number_report(piece, SOURCE / "source")


def test_fx_result_waits_for_repaired_main_table(piece):
    _extra(piece, "Euro -0.075R.", "desk_odds_v1.json", "/by_market/EURUSD/0/2")
    with pytest.raises(ValueError, match="ODDS_FX_CLOSE_REPAIR_NOT_LIVE:EURUSD"):
        odds.number_report(piece, SOURCE / "source")


def test_construction_result_is_explicitly_pooled(piece):
    _extra(piece, "Mean -0.217R.", "desk_odds_v1.json", "/construction/stop_width/rows/0/2")
    with pytest.raises(ValueError, match="ODDS_CONSTRUCTION_POOLED_LABEL_REQUIRED"):
        odds.number_report(piece, SOURCE / "source")


def test_private_reference_book_cannot_become_a_numeric_source(piece):
    _extra(piece, "Result 450.", "desk_odds_v1.json", "/plain_book/in_sample/summary/trades")
    with pytest.raises(ValueError, match="ODDS_PUBLIC_DERIVED_FIELD_REQUIRED"):
        odds.number_report(piece, SOURCE / "source")


def test_actual_coordinator_registers_and_consumes_the_same_bound_piece(tmp_path, monkeypatch):
    store = ContentOpsDurableStore(tmp_path / "test.sqlite3")
    packet = odds.register(store, SOURCE / "piece-1.json", tmp_path / "article")
    coordinator = DurablePublicationCoordinator(store=store,transport_runtime=SimpleNamespace(),
        published_content_path=tmp_path / "published.jsonl")
    coordinator.register_plan(packet["identity"],packet["plan"])
    rows = store.list_outbox_messages(work_item_id=packet["identity"],destination="substack")
    assert len(rows)==1
    intent=json.loads(rows[0]["payload"])
    assert intent["measured_odds_piece"]==packet["identity"]
    from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _durable_intent_inputs
    assert _durable_intent_inputs(intent)["article"]["measured_odds_series"]==odds.POLICY
    from live_contentops import article_publication_quality_v1 as quality
    calls=[]
    monkeypatch.setattr(quality,"image_register",lambda _:SimpleNamespace(reserve=lambda **kw:calls.append(kw) or {"status":"RESERVED"}))
    assert quality.before_article_write(coordinator,intent,"substack")["status"]=="RESERVED"
    assert calls[0]["enforce_cap"] is True
    assert calls[0]["assets"][0]["sha256"]==packet["piece"]["media_assets"][0]["sha256"]
    assert odds.register(store,SOURCE / "piece-1.json",tmp_path / "article")==packet
    assert len(store.list_outbox_messages(work_item_id=packet["identity"],destination="substack"))==1
    altered=deepcopy(packet["plan"]);altered["plan_hash"]="a"*64
    with pytest.raises(ValueError,match="ODDS_REGISTERED_PLAN_CHANGED"):
        coordinator.register_plan(packet["identity"],altered)


def test_registered_copy_and_source_manifest_are_immutable(tmp_path):
    store=ContentOpsDurableStore(tmp_path / "test.sqlite3")
    packet=odds.register(store,SOURCE / "piece-1.json",tmp_path / "article")
    path=tmp_path / "article/source/manifest.json"
    value=json.loads(path.read_bytes());value["fx_repair_live"]=True
    path.write_text(json.dumps(value),encoding="utf-8")
    with pytest.raises(ValueError,match="ODDS_REGISTERED_ARTIFACT_CHANGED:source/manifest.json"):
        odds.validate_plan(store,packet["identity"],packet["plan"])
