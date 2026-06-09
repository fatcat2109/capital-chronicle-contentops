"""Tests for the local-only pre-alpha manual decision batch packet (Task 0106)."""

import copy
import json
import os

from live_contentops import pre_alpha_manual_decision_batch as mdb

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODULE_PATH = os.path.join(
    REPO_ROOT, "live_contentops", "pre_alpha_manual_decision_batch.py"
)


def _packet():
    return mdb.build_from_config_file()


def test_schema_loads():
    schema = mdb.load_batch_schema()
    assert schema["title"] == "PreAlphaManualDecisionBatchPacket"
    assert "decision_records" in schema["required"]


def test_pass_path_generation():
    p = _packet()
    assert p["packet_status"] == "pass"
    assert p["review_queue_item_count"] == 3
    assert p["blocked_reasons"] == []


def test_every_review_item_maps_to_one_decision_record():
    p = _packet()
    assert len(p["decision_records"]) == p["review_queue_item_count"]
    rqids = [r["review_queue_item_id"] for r in p["decision_records"]]
    assert len(rqids) == len(set(rqids))


def test_no_auto_approval_flag():
    p = _packet()
    assert p["hard_boundary_flags"]["auto_approval"] is False
    for r in p["decision_records"]:
        assert r["auto_approval"] is False
        assert r["reviewer_required"] is True


def test_approve_revision_reject_paths():
    p = _packet()
    s = p["operator_decision_summary"]
    assert s["approved_count"] == 1
    assert s["revision_requested_count"] == 1
    assert s["rejected_count"] == 1
    assert s["blocked_count"] == 0
    assert len(p["approval_packets"]) == 1
    ap = p["approval_packets"][0]
    assert ap["approval_status"] == "approved_manual_publish_prep"
    assert ap["manual_publish_prep_ready"] is True
    assert ap["public_postable"] is False


def test_missing_decision_becomes_blocked_not_approved():
    config = copy.deepcopy(mdb.load_config())
    config["decisions"] = [
        d for d in config["decisions"]
        if d["review_queue_item_id"] != "rendered_packet_seed_macro_edu_001_rqi_0"
    ]
    p = mdb.build_from_config(config)
    assert p["packet_status"] == "blocked"
    rec = next(
        r for r in p["decision_records"]
        if r["review_queue_item_id"] == "rendered_packet_seed_macro_edu_001_rqi_0"
    )
    assert rec["decision_status"] == "blocked"
    assert rec["proposed_decision"] == "none"
    assert "no_manual_decision_supplied" in rec["blocked_reasons"]


def test_unresolved_findings_cannot_be_approved():
    config = copy.deepcopy(mdb.load_config())
    item = config["batch_review_packet"]["review_queue_items"][0]
    item["body"] = "You should buy this asset now, target price doubles."
    p = mdb.build_from_config(config)
    rec = p["decision_records"][0]
    assert rec["decision_status"] == "blocked"
    assert p["operator_decision_summary"]["approved_count"] == 0
    assert p["packet_status"] == "blocked"


def test_invalid_decision_preserved_as_blocked():
    config = copy.deepcopy(mdb.load_config())
    config["decisions"][0]["decision"] = "publish_now"
    p = mdb.build_from_config(config)
    blocked = p["blocked_decision_records"]
    assert len(blocked) >= 1
    assert any(b["decision_status"] == "blocked" for b in blocked)
    assert p["packet_status"] == "blocked"



def test_no_manual_export_or_ledger_objects():
    p = _packet()
    keys = set(p.keys())
    assert "manual_export_packets" not in keys
    assert "content_ledger_entries" not in keys
    assert p["hard_boundary_flags"]["manual_export_packet_created"] is False
    assert p["hard_boundary_flags"]["content_ledger_created"] is False
    assert p["hard_boundary_flags"]["content_ledger_publish_status_changed"] is False


def test_hard_boundary_flags_pinned():
    p = _packet()
    flags = p["hard_boundary_flags"]
    expected = {
        "local_only": True,
        "fixture_only": True,
        "manual_review_required": True,
        "reviewer_required": True,
        "auto_approval": False,
        "public_postable": False,
        "manual_export_packet_created": False,
        "content_ledger_created": False,
        "content_ledger_publish_status_changed": False,
        "provider_call_allowed_now": False,
        "network_call_allowed_now": False,
        "platform_api_call_allowed_now": False,
        "scheduler_allowed": False,
        "metrics_ingestion_allowed": False,
        "live_execution_allowed_now": False,
        "credential_or_env_read_allowed": False,
    }
    for k, v in expected.items():
        assert flags[k] is v, "flag %s should be %r" % (k, v)
    assert p["safety_audit"]["unsafe_flag_count"] == 0


def test_fail_closed_on_source_packet_blocked():
    config = copy.deepcopy(mdb.load_config())
    config["batch_review_packet"]["packet_status"] = "blocked"
    p = mdb.build_from_config(config)
    assert p["packet_status"] == "blocked"
    assert "source_batch_review_packet_blocked" in p["blocked_reasons"]


def test_deterministic_output():
    a = json.dumps(_packet(), sort_keys=True)
    b = json.dumps(_packet(), sort_keys=True)
    assert a == b


def test_summary_valid_json_shape():
    out = mdb.summary()
    assert out["packet_status"] == "pass"
    assert out["review_queue_item_count"] == 3
    assert out["decision_record_count"] == 3
    assert out["approval_packet_count"] == 1
    assert out["blocked_decision_count"] == 0
    assert out["revision_requested_count"] == 1
    assert out["rejected_count"] == 1
    assert out["unsafe_flag_count"] == 0
    for k in (
        "auto_approval", "manual_export_packet_created", "content_ledger_created",
        "provider_call_made", "network_call_made", "credential_read",
        "public_postable_output", "live_execution_allowed_now", "scheduler_allowed",
        "metrics_ingestion_allowed",
    ):
        assert out[k] is False
    json.dumps(out)


def test_static_scan_no_forbidden_capability():
    with open(MODULE_PATH, "r", encoding="utf-8") as f:
        src = f.read()
    forbidden = [
        "import requests", "import httpx", "import aiohttp", "import urllib",
        "import socket", "import subprocess", "import openai", "import anthropic",
        "load_dotenv", "os.environ", "os.getenv", "getenv(",
        "requests.", "httpx.", "aiohttp.", "urlopen", "socket.", "subprocess.",
        "smtplib.", "webbrowser.",
    ]
    for token in forbidden:
        assert token not in src, "forbidden capability token present: %s" % token
