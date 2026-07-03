import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED_PACKET = ROOT / "docs/automation/V6_FINAL_PRODUCT_READINESS/final_product_readiness_packet.json"
STATIC_PACKET = ROOT / "ui/contentops_v5/src/data/finalProductReadinessPacket.ts"
STATUS_JSON = ROOT / "docs/status/current_project_status.json"
STATUS_MD = ROOT / "docs/status/CURRENT_PROJECT_STATUS.md"
STALE_SUBSTACK_TEXT = "Substack publish hard-locked/not proven"
CURRENT_SUBSTACK_TEXT = (
    "Substack live publish success accepted by committed TASK_0055/TASK_0056 evidence; "
    "public URL not verified"
)


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _static_packet_id() -> str:
    text = STATIC_PACKET.read_text(encoding="utf-8")
    match = re.search(r'packet_id:\s*"([^"]+)"', text)
    assert match, "static finalProductReadinessPacket.ts packet_id missing"
    return match.group(1)


def test_static_final_readiness_packet_id_matches_generated_json():
    assert _static_packet_id() == _read_json(GENERATED_PACKET)["packet_id"]


def test_status_blocks_stale_substack_not_proven_current_authority_text():
    status_text = STATUS_JSON.read_text(encoding="utf-8")
    status = _read_json(STATUS_JSON)

    assert STALE_SUBSTACK_TEXT not in status_text
    assert CURRENT_SUBSTACK_TEXT in status["current_loop_components"]


def test_status_last_updated_and_accepted_task_are_consistent_after_metadata_repair():
    status = _read_json(STATUS_JSON)
    md_text = STATUS_MD.read_text(encoding="utf-8")

    assert status["last_updated_by_task"] == "TASK_0069"
    assert "## last_updated_by_task\nTASK_0069" in md_text
    assert status["latest_accepted_task"] == "TASK_0059"
    assert status["current_product_phase"] == "TASK 0059 Final Product Readiness panel and packet implemented"
    assert "## latest accepted task\nTASK_0059" in md_text
    assert status["last_updated_by_task"] != status["latest_accepted_task"]


def test_public_url_verification_remains_unclaimed_and_locked():
    packet = _read_json(GENERATED_PACKET)
    status = _read_json(STATUS_JSON)
    status_text = json.dumps(status, sort_keys=True)

    assert packet["substack_public_url_verified"] is False
    assert packet["dispatch_allowed_now"] is False
    assert packet["live_write_allowed_now"] is False
    assert "Public URL verification is not claimed" in status["dispatch_live_status"]
    assert "Substack public URL verification is not claimed" in status_text


def test_task_0069_status_includes_v5_final_readiness_ui_hardening_entries():
    status = _read_json(STATUS_JSON)
    components = status["current_loop_components"]

    assert "V5 Final Readiness verdict strip" in components
    assert "V5 Final Readiness evidence trail" in components
    assert "V5 Final Readiness remaining blockers panel" in components
    assert "V5 Final Readiness operator handoff checklist" in components


def test_task_0069_status_preserves_public_url_and_dispatch_locks():
    status = _read_json(STATUS_JSON)
    status_text = json.dumps(status, sort_keys=True).lower()

    assert "substack_public_url_verified=false" in status["latest_evidence_summary"]
    assert "dispatch_allowed_now=false" in status["latest_evidence_summary"]
    assert "live_write_allowed_now=false" in status["latest_evidence_summary"]
    assert "public url remains unverified" in STATUS_MD.read_text(encoding="utf-8").lower()
    forbidden_claims = [
        "public url verified",
        "dispatch allowed",
        "live write allowed",
        "task_0069 browser",
        "task_0069 cdp",
        "task_0069 live action",
        "task_0069 live publish",
        "task_0069 platform action",
        "task_0069 network",
        "task_0069 env",
        "task_0069 credential",
    ]
    for claim in forbidden_claims:
        assert claim not in status_text


def test_ui_status_hardening_after_task_0059_is_non_semantic():
    status = _read_json(STATUS_JSON)
    status_text = json.dumps(status, sort_keys=True).lower()
    md_text = STATUS_MD.read_text(encoding="utf-8").lower()
    guardrail = (
        "ui/status hardening tasks after task_0059 are non-semantic unless explicitly promoted; "
        "task_0059 remains latest accepted product baseline"
    )

    assert status["latest_accepted_task"] == "TASK_0059"
    assert status["current_product_phase"] == "TASK 0059 Final Product Readiness panel and packet implemented"
    assert status["last_updated_by_task"] >= "TASK_0069"
    assert status["last_updated_by_task"] != status["latest_accepted_task"]
    assert guardrail in status_text
    assert guardrail in md_text

    forbidden_fragments = [
        "task_0060 public url verified",
        "task_0061 public url verified",
        "task_0062 public url verified",
        "task_0063 public url verified",
        "task_0064 public url verified",
        "task_0065 public url verified",
        "task_0066 public url verified",
        "task_0067 public url verified",
        "task_0068 public url verified",
        "task_0069 public url verified",
        "dispatch clearance",
        "live write clearance",
        "browser/cdp execution",
        "platform action performed",
        "network/api action",
        "env/credential access",
        "generated packet semantic change",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in status_text


def test_status_never_calls_v5_final_readiness_dispatch_or_publish_ready():
    status = _read_json(STATUS_JSON)
    scoped_status = "\n".join([
        status["current_product_phase"],
        status["current_product_lane"],
        status["accepted_baseline_summary"],
        status["latest_evidence_summary"],
        status["next_recommended_task"],
        "\n".join(status["current_loop_components"][-8:]),
    ])
    md_text = STATUS_MD.read_text(encoding="utf-8")
    md_scoped = "\n".join([
        md_text.split("## current_product_phase", 1)[1].split("## status_sha_model", 1)[0],
        md_text.split("## current next recommended task", 1)[1].split("## next-task safety notes", 1)[0],
    ])
    combined = f"{scoped_status}\n{md_scoped}".lower()

    forbidden_wording = [
        "dispatch-ready",
        "dispatch ready",
        "publish-ready",
        "publish ready",
        "ready for dispatch",
        "ready for publishing",
        "ready to publish",
        "ready to dispatch",
        "dispatch clearance",
        "publish clearance",
    ]
    for wording in forbidden_wording:
        assert wording not in combined

    assert "local operator review" in combined
    assert (
        "public url not verified" in combined
        or "public url verification is not claimed" in combined
    )
    assert (
        "live actions locked" in combined
        or "dispatch/live write stays locked" in combined
    )
    assert status["latest_accepted_task"] == "TASK_0059"
    assert status["current_product_phase"] == "TASK 0059 Final Product Readiness panel and packet implemented"


def test_final_readiness_public_url_audit_remains_operator_supplied_only():
    packet = _read_json(GENERATED_PACKET)
    status = _read_json(STATUS_JSON)
    md_text = STATUS_MD.read_text(encoding="utf-8")
    scoped_status = "\n".join([
        status["current_product_phase"],
        status["current_product_lane"],
        status["accepted_baseline_summary"],
        status["dispatch_live_status"],
        status["latest_evidence_summary"],
        status["next_recommended_task"],
    ])
    md_scoped = "\n".join([
        md_text.split("## current_product_phase", 1)[1].split("## status_sha_model", 1)[0],
        md_text.split("## dispatch/live status", 1)[1].split("## provider/env/credential status", 1)[0],
        md_text.split("## current next recommended task", 1)[1].split("## next-task safety notes", 1)[0],
    ])
    combined = f"{scoped_status}\n{md_scoped}".lower()

    assert packet["substack_public_url_verified"] is False
    assert "substack_public_url_verified=false" in status["latest_evidence_summary"]
    assert (
        "public url not verified" in combined
        or "public url verification is not claimed" in combined
    )
    assert "operator-supplied public url" in combined

    normalized = combined.replace("substack_public_url_verified=false", "")
    forbidden_url_claims = [
        "public_url",
        "publicurl",
        "http://",
        "https://",
        "substack.com/p/",
        "verified public url",
        "public url verified",
        "url fetch",
        "scrape",
        "browser verification",
    ]
    for claim in forbidden_url_claims:
        assert claim not in normalized


def test_final_readiness_hardening_tasks_do_not_imply_network_or_api_activity():
    packet = _read_json(GENERATED_PACKET)
    status = _read_json(STATUS_JSON)
    md_text = STATUS_MD.read_text(encoding="utf-8")
    scoped_status = "\n".join([
        status["current_product_phase"],
        status["current_product_lane"],
        status["accepted_baseline_summary"],
        status["latest_evidence_summary"],
        status["next_recommended_task"],
    ])
    md_scoped = "\n".join([
        md_text.split("## current_product_phase", 1)[1].split("## status_sha_model", 1)[0],
        md_text.split("## current next recommended task", 1)[1].split("## next-task safety notes", 1)[0],
    ])
    combined = f"{scoped_status}\n{md_scoped}".lower()

    assert packet["network_call_performed"] is False
    assert "network_call_performed=false" in status["latest_evidence_summary"]
    assert "no browser/cdp/live/network/env/credential action" in combined
    assert "ui/status hardening tasks after task_0059 are non-semantic" in combined

    forbidden_network_claims = [
        "task_0060 network",
        "task_0061 network",
        "task_0062 network",
        "task_0063 network",
        "task_0064 network",
        "task_0065 network",
        "task_0066 network",
        "task_0067 network",
        "task_0068 network",
        "task_0069 network",
        "task_0070 network",
        "task_0071 network",
        "task_0072 network",
        "network performed",
        "network call performed=true",
        "api action performed",
        "api call performed",
        "platform api call",
        "provider call",
        "fetch performed",
        "remote fetch",
        "http request",
    ]
    for claim in forbidden_network_claims:
        assert claim not in combined


def test_final_readiness_hardening_tasks_do_not_imply_env_or_credential_access():
    packet = _read_json(GENERATED_PACKET)
    status = _read_json(STATUS_JSON)
    md_text = STATUS_MD.read_text(encoding="utf-8")
    scoped_status = "\n".join([
        status["current_product_phase"],
        status["current_product_lane"],
        status["accepted_baseline_summary"],
        status["latest_evidence_summary"],
        status["next_recommended_task"],
    ])
    md_scoped = "\n".join([
        md_text.split("## current_product_phase", 1)[1].split("## status_sha_model", 1)[0],
        md_text.split("## provider/env/credential status", 1)[1].split("## active blockers", 1)[0],
        md_text.split("## current next recommended task", 1)[1].split("## next-task safety notes", 1)[0],
    ])
    combined = f"{scoped_status}\n{md_scoped}".lower()

    assert packet["env_or_credential_read_performed"] is False
    assert "env_or_credential_read_performed=false" in status["latest_evidence_summary"]
    assert "no browser/cdp/live/network/env/credential action" in combined
    assert "ui/status hardening tasks after task_0059 are non-semantic" in combined

    forbidden_env_claims = [
        "task_0060 env",
        "task_0061 env",
        "task_0062 env",
        "task_0063 env",
        "task_0064 env",
        "task_0065 env",
        "task_0066 env",
        "task_0067 env",
        "task_0068 env",
        "task_0069 env",
        "task_0070 env",
        "task_0071 env",
        "task_0072 env",
        "task_0073 env",
        "task_0060 credential",
        "task_0061 credential",
        "task_0062 credential",
        "task_0063 credential",
        "task_0064 credential",
        "task_0065 credential",
        "task_0066 credential",
        "task_0067 credential",
        "task_0068 credential",
        "task_0069 credential",
        "task_0070 credential",
        "task_0071 credential",
        "task_0072 credential",
        "task_0073 credential",
        "env read performed",
        "credential read performed",
        "env_or_credential_read_performed=true",
        "env values read",
        "credential values read",
        "secret read",
        "token read",
        "provider key read",
    ]
    for claim in forbidden_env_claims:
        assert claim not in combined


def test_final_readiness_hardening_tasks_do_not_imply_browser_or_cdp_activity():
    packet = _read_json(GENERATED_PACKET)
    status = _read_json(STATUS_JSON)
    md_text = STATUS_MD.read_text(encoding="utf-8")
    scoped_status = "\n".join([
        status["current_product_phase"],
        status["current_product_lane"],
        status["accepted_baseline_summary"],
        status["latest_evidence_summary"],
        status["next_recommended_task"],
    ])
    md_scoped = "\n".join([
        md_text.split("## current_product_phase", 1)[1].split("## status_sha_model", 1)[0],
        md_text.split("## current next recommended task", 1)[1].split("## next-task safety notes", 1)[0],
    ])
    combined = f"{scoped_status}\n{md_scoped}".lower()

    assert packet["browser_or_cdp_action_performed"] is False
    assert "browser_or_cdp_action_performed=false" in status["latest_evidence_summary"]
    assert "no browser/cdp/live/network/env/credential action" in combined
    assert "ui/status hardening tasks after task_0059 are non-semantic" in combined

    forbidden_browser_claims = [
        "task_0060 browser",
        "task_0061 browser",
        "task_0062 browser",
        "task_0063 browser",
        "task_0064 browser",
        "task_0065 browser",
        "task_0066 browser",
        "task_0067 browser",
        "task_0068 browser",
        "task_0069 browser",
        "task_0070 browser",
        "task_0071 browser",
        "task_0072 browser",
        "task_0073 browser",
        "task_0074 browser",
        "task_0060 cdp",
        "task_0061 cdp",
        "task_0062 cdp",
        "task_0063 cdp",
        "task_0064 cdp",
        "task_0065 cdp",
        "task_0066 cdp",
        "task_0067 cdp",
        "task_0068 cdp",
        "task_0069 cdp",
        "task_0070 cdp",
        "task_0071 cdp",
        "task_0072 cdp",
        "task_0073 cdp",
        "task_0074 cdp",
        "browser action performed",
        "cdp action performed",
        "browser_or_cdp_action_performed=true",
        "dom captured",
        "screenshot captured",
        "cookie captured",
        "storage captured",
    ]
    for claim in forbidden_browser_claims:
        assert claim not in combined


def test_final_readiness_hardening_tasks_do_not_imply_live_or_platform_action():
    packet = _read_json(GENERATED_PACKET)
    status = _read_json(STATUS_JSON)
    md_text = STATUS_MD.read_text(encoding="utf-8")
    scoped_status = "\n".join([
        status["current_product_phase"],
        status["current_product_lane"],
        status["accepted_baseline_summary"],
        status["latest_evidence_summary"],
        status["next_recommended_task"],
    ])
    md_scoped = "\n".join([
        md_text.split("## current_product_phase", 1)[1].split("## status_sha_model", 1)[0],
        md_text.split("## dispatch/live status", 1)[1].split("## provider/env/credential status", 1)[0],
        md_text.split("## current next recommended task", 1)[1].split("## next-task safety notes", 1)[0],
    ])
    combined = f"{scoped_status}\n{md_scoped}".lower()

    assert packet["dispatch_allowed_now"] is False
    assert packet["live_write_allowed_now"] is False
    assert "dispatch_allowed_now=false" in status["latest_evidence_summary"]
    assert "live_write_allowed_now=false" in status["latest_evidence_summary"]
    assert "live actions locked" in combined or "dispatch/live write stays locked" in combined
    assert "ui/status hardening tasks after task_0059 are non-semantic" in combined

    forbidden_live_claims = [
        "task_0060 live action",
        "task_0061 live action",
        "task_0062 live action",
        "task_0063 live action",
        "task_0064 live action",
        "task_0065 live action",
        "task_0066 live action",
        "task_0067 live action",
        "task_0068 live action",
        "task_0069 live action",
        "task_0070 live action",
        "task_0071 live action",
        "task_0072 live action",
        "task_0073 live action",
        "task_0074 live action",
        "task_0075 live action",
        "task_0060 platform action",
        "task_0061 platform action",
        "task_0062 platform action",
        "task_0063 platform action",
        "task_0064 platform action",
        "task_0065 platform action",
        "task_0066 platform action",
        "task_0067 platform action",
        "task_0068 platform action",
        "task_0069 platform action",
        "task_0070 platform action",
        "task_0071 platform action",
        "task_0072 platform action",
        "task_0073 platform action",
        "task_0074 platform action",
        "task_0075 platform action",
        "dispatch_allowed_now=true",
        "live_write_allowed_now=true",
        "live action performed",
        "platform action performed",
        "live dispatch performed",
        "publish performed",
        "send performed",
    ]
    for claim in forbidden_live_claims:
        assert claim not in combined
