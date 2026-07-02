"""Source Intake Parser for V6 Operator Recovery to Explicit Live Scope Gate & Discord Supervised Live Preflight."""
from __future__ import annotations

import os
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Path configurations
GATE_INBOX_DIR = ROOT / "docs" / "automation" / "V6_OPERATOR_RECOVERY_TO_EXPLICIT_LIVE_SCOPE_GATE_SOURCE_CANDIDATE" / "inbox"
GATE_NORMALIZED_DIR = ROOT / "docs" / "automation" / "V6_OPERATOR_RECOVERY_TO_EXPLICIT_LIVE_SCOPE_GATE_SOURCE_CANDIDATE" / "normalized_candidate"
GATE_NORMALIZED_FILE = GATE_NORMALIZED_DIR / "normalized_dispatch_candidate.json"

PREFLIGHT_INBOX_DIR = ROOT / "docs" / "automation" / "V6_DISCORD_SUPERVISED_LIVE_PREFLIGHT" / "inbox"
PREFLIGHT_NORMALIZED_DIR = ROOT / "docs" / "automation" / "V6_DISCORD_SUPERVISED_LIVE_PREFLIGHT" / "normalized_candidate"
PREFLIGHT_NORMALIZED_FILE = PREFLIGHT_NORMALIZED_DIR / "normalized_discord_payload_candidate.json"
INBOX_DIR = GATE_INBOX_DIR

PLACEHOLDER_WORDS = ["viết nội dung thật ở đây", "todo", "placeholder", "lorem ipsum", "sample only"]
FINANCIAL_WORDS = ["buy", "sell", "hold", "price target", "position sizing", "entry/exit", "trade recommendation", "guaranteed prediction", "signal-service"]

def parse_and_normalize_dir(inbox_dir: Path, normalized_file: Path) -> dict:
    inbox_dir.mkdir(parents=True, exist_ok=True)
    normalized_file.parent.mkdir(parents=True, exist_ok=True)

    # Search for first JSON or MD file in the inbox (excluding .gitkeep)
    files = [f for f in inbox_dir.glob("*") if f.name != ".gitkeep" and f.suffix in [".json", ".md"]]

    if not files:
        # Blocked state: missing source artifact
        res = {
            "candidate_id": "",
            "source_artifact_path": "",
            "source_artifact_hash": "",
            "platform_family": "discord",
            "content_type": "",
            "operator_destination_label": "",
            "normalized_body_text": "",
            "content_length": 0,
            "request_body_hash_preview": None,
            "safety_scan": "pending",
            "blocked_reasons": ["blocked_missing_operator_source_artifact"],
            "dispatchable": False,
            "approval_required": True,
            "live_scope_required": True,
            "no_public_url_claim": True,
            "no_metrics_claim": True,
            "no_secret_material_present": True
        }
        _write_normalized(res, normalized_file)
        return res

    source_path = files[0]
    content = source_path.read_text(encoding="utf-8")
    
    # Calculate sha256 of source content
    source_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    blocked_reasons = []

    # Check placeholder words
    content_lower = content.lower()
    for word in PLACEHOLDER_WORDS:
        if word in content_lower:
            blocked_reasons.append(f"contains_placeholder_word: {word}")

    # Check financial signals
    for word in FINANCIAL_WORDS:
        if word in content_lower:
            blocked_reasons.append(f"contains_forbidden_financial_advice: {word}")

    # Parse details
    body = content
    content_type = "markdown"
    dest_label = "Discord General Webhook"

    if source_path.suffix == ".json":
        content_type = "json"
        try:
            data = json.loads(content)
            body = data.get("body", content)
            dest_label = data.get("destination_label", dest_label)
        except Exception:
            blocked_reasons.append("invalid_json_format")

    # If missing operator source artifact is not a reason but other errors occurred
    if not blocked_reasons:
        safety_scan = "passed"
    else:
        safety_scan = "failed"

    body_hash_preview = hashlib.sha256(body.encode("utf-8")).hexdigest()

    res = {
        "candidate_id": f"discord_candidate_{source_hash[:16]}",
        "source_artifact_path": str(source_path.relative_to(ROOT)).replace("\\", "/"),
        "source_artifact_hash": source_hash,
        "platform_family": "discord",
        "content_type": content_type,
        "operator_destination_label": dest_label,
        "normalized_body_text": body,
        "content_length": len(body),
        "request_body_hash_preview": body_hash_preview,
        "safety_scan": safety_scan,
        "blocked_reasons": blocked_reasons,
        "dispatchable": False,
        "approval_required": True,
        "live_scope_required": True,
        "no_public_url_claim": True,
        "no_metrics_claim": True,
        "no_secret_material_present": True
    }

    _write_normalized(res, normalized_file)
    return res

def _write_normalized(candidate: dict, normalized_file: Path) -> None:
    # Sort keys excluding payload_hash
    clean_dict = {k: v for k, v in candidate.items() if k != "payload_hash"}
    serialized = json.dumps(clean_dict, sort_keys=True, indent=2)
    payload_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    
    candidate["payload_hash"] = payload_hash
    
    # Save back
    normalized_file.write_text(json.dumps(candidate, sort_keys=True, indent=2), encoding="utf-8")

def parse_and_normalize() -> dict:
    # Keep compatibility with previous task which calls parse_and_normalize()
    parse_and_normalize_dir(PREFLIGHT_INBOX_DIR, PREFLIGHT_NORMALIZED_FILE)
    return parse_and_normalize_dir(GATE_INBOX_DIR, GATE_NORMALIZED_FILE)

if __name__ == "__main__":
    parse_and_normalize()
    print("Intake normalization completed for both directories.")
