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
