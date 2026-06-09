"""Tests for the local mock publish flow + metrics capture dry-run (0080).

No network/credential/platform access. Mock transport only. Live publishing is
impossible here.
"""

import json
import os

import live_contentops.mock_publish_flow as f
import live_contentops.approval_audit_contracts as aac

ROOT = os.path.join(os.path.dirname(__file__), "..")
FIX = os.path.join(ROOT, "fixtures", "mock_publish_flow")


def _load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_fix(name):
    return _load(os.path.join(FIX, name))


def _valid_post():
    return _load(os.path.join(
        ROOT, "fixtures", "platform_dry_runs", "valid_canonical_social_post.json"
    ))


def _valid_approval():
    return _load(os.path.join(
        ROOT, "fixtures", "approval_audit", "valid_approval_for_mock_publish.json"
    ))


def _permissive_kill_switch():
    ks = aac.default_kill_switch_state()
    ks["enabled"] = True
    ks["blocks_mock_publish"] = False
    return ks


# --- schemas load -----------------------------------------------------------

def test_schemas_load():
    assert f.load_request_schema()["title"] == "MockPublishRequest"
    assert f.load_result_schema()["title"] == "MockPublishResult"
    assert f.load_metrics_schema()["title"] == "MockMetricsPlaceholder"


# --- positive flow ----------------------------------------------------------

def test_all_six_platforms_run_dry_run():
    post = _valid_post()
    out = f.run_mock_publish_flow(post, _valid_approval(), _permissive_kill_switch())
    attempted = out["run_summary"]["platforms_attempted"]
    assert set(attempted) == set(f.summary()["supported_platforms"])
    assert len(attempted) == 6
    # Every platform produced a request, result, metrics, and audit event.
    for pid, res in out["per_platform"].items():
        assert res["request"]["mock_only"] is True
        assert res["request"]["dry_run"] is True
        assert res["result"]["live_posting_enabled"] is False
        assert res["result"]["network_accessed"] is False
        assert res["result"]["credential_accessed"] is False
        assert res["metrics"]["fetched_from_platform"] is False
        assert res["metrics"]["scraped"] is False
        assert res["audit_event"]["live_posting_enabled"] is False


def test_text_capable_platforms_mock_publish():
    post = _valid_post()
    out = f.run_mock_publish_flow(post, _valid_approval(), _permissive_kill_switch())
    passed = out["run_summary"]["platforms_mock_passed"]
    # Text-only post should pass on text-capable platforms.
    assert "x" in passed
    assert "linkedin" in passed
    assert "telegram" in passed


def test_mock_url_is_fake_scheme():
    post = _valid_post()
    out = f.run_mock_publish_flow(post, _valid_approval(), _permissive_kill_switch())
    for pid in out["run_summary"]["platforms_mock_passed"]:
        url = out["per_platform"][pid]["result"]["mock_post_url"]
        assert url.startswith("mock://")
        assert "http://" not in url and "https://" not in url


def test_run_summary_flags():
    post = _valid_post()
    out = f.run_mock_publish_flow(post, _valid_approval(), _permissive_kill_switch())
    rs = out["run_summary"]
    assert rs["all_live_disabled"] is True
    assert rs["all_network_disabled"] is True
    assert rs["all_credentials_disabled"] is True
    assert len(rs["audit_event_ids"]) == 6


def test_metrics_are_placeholder_only():
    post = _valid_post()
    out = f.run_mock_publish_flow(post, _valid_approval(), _permissive_kill_switch())
    for pid, res in out["per_platform"].items():
        m = res["metrics"]
        assert m["metrics_source"] in ("simulated_placeholder", "manual_placeholder")
        assert m["values"] is None
        assert m["network_accessed"] is False



# --- negative flow (fail closed) -------------------------------------------

def test_missing_approval_blocks_all_platforms():
    post = _valid_post()
    out = f.run_mock_publish_flow(post, None, _permissive_kill_switch())
    assert out["run_summary"]["platforms_mock_passed"] == []
    for pid, res in out["per_platform"].items():
        assert res["result"]["status"] == "blocked"
        assert res["result"]["mock_post_url"] is None
        assert any("gate:" in e for e in res["result"]["blocking_errors"])


def test_default_kill_switch_blocks_all_platforms():
    post = _valid_post()
    ks = aac.default_kill_switch_state()  # disabled, blocks mock
    out = f.run_mock_publish_flow(post, _valid_approval(), ks)
    assert out["run_summary"]["platforms_mock_passed"] == []
    for pid, res in out["per_platform"].items():
        assert res["result"]["status"] == "blocked"
        assert any("blocks_mock_publish" in e for e in res["result"]["blocking_errors"])


def test_revoked_approval_blocks():
    post = _valid_post()
    appr = _valid_approval()
    appr["approval_state"] = "revoked"
    appr["revocation_of"] = "appr_0001"
    out = f.run_mock_publish_flow(post, appr, _permissive_kill_switch())
    assert out["run_summary"]["platforms_mock_passed"] == []


def test_live_publish_remains_impossible():
    # Even with a live-intent approval and a kill switch that tries to unblock
    # live, the live proceed-check is always denied, and the mock flow never
    # enables live posting.
    fix = _load_fix("invalid_live_enabled_rejected.json")
    appr = fix["approval_record"]
    ks = fix["kill_switch"]
    # The kill switch fixture is invalid (tries to unblock live); validator rejects.
    assert aac.validate_kill_switch_state(ks)["valid"] is False
    assert aac.can_proceed_to_live_publish_later(appr, ks)["allowed"] is False
    post = _valid_post()
    out = f.run_mock_publish_flow(post, appr, ks)
    for pid, res in out["per_platform"].items():
        assert res["result"]["live_posting_enabled"] is False
        assert res["request"]["live_posting_enabled"] is False


def test_secret_in_audit_event_is_rejected():
    fix = _load_fix("invalid_secret_in_audit_rejected.json")
    res = aac.validate_audit_event(fix["audit_event"])
    assert res["valid"] is False
    assert any("unredacted_secret_in" in e for e in res["errors"])


def test_generated_audit_events_contain_no_secret():
    post = _valid_post()
    out = f.run_mock_publish_flow(post, _valid_approval(), _permissive_kill_switch())
    for pid, res in out["per_platform"].items():
        assert aac.validate_audit_event(res["audit_event"])["valid"] is True


# --- summary / posture ------------------------------------------------------

def test_summary_posture():
    s = f.summary()
    assert s["live_publish_possible_now"] is False
    assert s["metrics_fetched_or_scraped"] is False
    assert s["credential_read_allowed_now"] is False
    assert s["network_accessed"] is False
    assert s["scheduling_allowed_now"] is False
    assert s["replies_or_dms_allowed_now"] is False
    assert s["all_outputs_not_public_postable"] is True
    assert len(s["supported_platforms"]) == 6

    assert f.load_run_schema()["title"] == "MockPublishFlowRun"
