"""Discord real-content source artifact intake verifier.

Creates deterministic, non-live packet describing whether operator supplied one
real Capital Chronicle source artifact suitable for later filled-intake work.
No env reads, no network calls, no dispatch, no approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_REAL_CONTENT_OPERATOR_SOURCE_ARTIFACT_V0"
PLATFORM = "discord"
SOURCE_DIR = Path("docs/automation/DISCORD_REAL_CONTENT_SOURCE_ARTIFACT")
DEFAULT_OUTPUT = SOURCE_DIR / "source_artifact_packet.json"
DEFAULT_SCHEMA = SOURCE_DIR / "source_artifact_schema.json"
DEFAULT_INBOX = SOURCE_DIR / "inbox"
ALLOWED_EXTENSIONS = {".md": "markdown", ".txt": "text", ".json": "json"}
TARGET_TO_CONTENT_TYPE = {
    "announcements": "announcement",
    "substack_drops": "substack_drop",
    "product_updates": "product_update",
}
DISALLOWED_PATH_MARKERS = (
    "template",
    "dryrun",
    "dry_run",
    "sample",
    "fixture",
    "test_message",
    "test-payload",
    "framework_packet",
    "implementation_report",
    "walkthrough",
    "task.md",
)
IGNORED_INBOX_FILENAMES = {"readme.md"}
PLACEHOLDER_TEXT_RE = re.compile(
    r"\[(?:viết nội dung thật ở đây|đường dẫn tới artifact/source nếu có)\]"
    r"|\btarget candidate:\b"
    r"|\bcontent type candidate:\b",
    re.IGNORECASE,
)
TRADING_SIGNAL_RE = re.compile(r"\b(buy|sell|hold|long|short|entry|exit|take profit|stop loss)\b", re.IGNORECASE)
POSITION_SIZING_RE = re.compile(r"\b(position size|size your position|allocate(?:\s+\w+){0,3}\s+\d+%|risk\s+\d+%|portfolio weight)", re.IGNORECASE)
GUARANTEED_PREDICTION_RE = re.compile(r"\b(guaranteed|will definitely|certain to|risk[- ]free|cannot lose|sure thing)\b", re.IGNORECASE)
FINANCIAL_ADVICE_RE = re.compile(r"\b(financial advice|investment advice|not financial advice|alpha call|conviction trade)\b", re.IGNORECASE)
SECRETISH_RE = re.compile(r"https://(?:discord(?:app)?\.com)/api/webhooks/|webhooks/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+|\b(?:token|cookie|sessionid|authorization|bearer)\b", re.IGNORECASE)
NUMERIC_CLAIMS_RE = re.compile(r"\b\d+(?:\.\d+)?%?\b")
ANNOUNCEMENT_HINT_RE = re.compile(r"\b(announcement|launch|launching|today we|now live|rollout|release)\b", re.IGNORECASE)
SUBSTACK_HINT_RE = re.compile(r"\b(substack|newsletter|issue|edition|subscribe|publication)\b", re.IGNORECASE)
PRODUCT_UPDATE_HINT_RE = re.compile(r"\b(product update|changelog|release notes|feature update|shipped|updated)\b", re.IGNORECASE)


def path_text(path: str | Path | None) -> str | None:
    if path is None:
        return None
    return str(path).replace("\\", "/")


def is_candidate_inbox_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS and path.name.lower() not in IGNORED_INBOX_FILENAMES


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def validation_base() -> dict[str, Any]:
    return {
        "real_artifact_present": False,
        "source_path_allowed": False,
        "content_nonempty": False,
        "not_template": False,
        "not_dryrun": False,
        "not_sample": False,
        "not_test_message": False,
        "no_placeholder_fillers": False,
        "no_webhook_or_secret_like_text": False,
        "no_financial_advice_language": False,
        "no_trading_signal_language": False,
        "no_position_sizing_language": False,
        "no_guaranteed_prediction_language": False,
        "numeric_claims_require_evidence": False,
    }


def blocked_packet() -> dict[str, Any]:
    return {
        "task_label": TASK_LABEL,
        "source_artifact_status": "BLOCKED_AWAITING_OPERATOR_ARTIFACT",
        "platform": PLATFORM,
        "source_artifact_path": None,
        "source_artifact_sha256": None,
        "source_artifact_kind": None,
        "source_artifact_bytes": None,
        "content_title_detected": None,
        "content_preview_redacted_or_excerpt": None,
        "recommended_target_name": None,
        "recommended_content_type": None,
        "source_evidence_paths_detected": [],
        "numeric_claims_detected": False,
        "source_evidence_required": False,
        "not_approved": True,
        "not_dispatchable": True,
        "not_public_postable": True,
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "raw_secret_output": False,
        "webhook_url_printed": False,
        "validation": validation_base(),
        "block_reason": "operator_artifact_missing",
    }


def kind_for_path(path: Path) -> str:
    return ALLOWED_EXTENSIONS.get(path.suffix.lower(), "unknown")


def detect_title(text: str, path: Path) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None
    heading = next((line.lstrip("# ").strip() for line in lines if line.startswith("#")), None)
    return heading or lines[0][:120] or path.stem


def preview(text: str) -> str | None:
    clean = " ".join(part.strip() for part in text.splitlines() if part.strip())
    return clean[:240] or None


def infer_target_and_type(text: str, path: Path) -> tuple[str | None, str | None]:
    combined = f"{path.name}\n{text}"
    if SUBSTACK_HINT_RE.search(combined):
        return "substack_drops", "substack_drop"
    if PRODUCT_UPDATE_HINT_RE.search(combined):
        return "product_updates", "product_update"
    if ANNOUNCEMENT_HINT_RE.search(combined):
        return "announcements", "announcement"
    return None, None


def numeric_claims_detected(text: str) -> bool:
    return bool(NUMERIC_CLAIMS_RE.search(text))


def path_validation_flags(path: Path) -> dict[str, bool]:
    lowered = path_text(path).lower()
    return {
        "not_template": "template" not in lowered,
        "not_dryrun": "dryrun" not in lowered and "dry_run" not in lowered,
        "not_sample": "sample" not in lowered,
        "not_test_message": "test_message" not in lowered and "test-payload" not in lowered and "fixture" not in lowered,
    }


def source_path_allowed(path: Path) -> bool:
    lowered = path_text(path).lower()
    if any(marker in lowered for marker in DISALLOWED_PATH_MARKERS):
        return False
    return path.suffix.lower() in ALLOWED_EXTENSIONS


def find_single_source_artifact(inbox: str | Path) -> tuple[Path | None, list[str]]:
    inbox_path = Path(inbox)
    if not inbox_path.exists():
        return None, []
    files = [p for p in sorted(inbox_path.iterdir()) if is_candidate_inbox_file(p)]
    return (files[0], [path_text(p) for p in files]) if len(files) == 1 else (None, [path_text(p) for p in files])


def fail_packet(source_artifact: str | Path | None, errors: list[str], text: str | None = None) -> dict[str, Any]:
    path = Path(source_artifact) if source_artifact else None
    packet = blocked_packet()
    packet["source_artifact_status"] = "FAIL_VALIDATION"
    packet["source_artifact_path"] = path_text(source_artifact)
    packet["source_artifact_kind"] = kind_for_path(path) if path else None
    packet["source_artifact_bytes"] = len(text.encode("utf-8")) if text is not None else None
    packet["content_title_detected"] = detect_title(text, path) if (text and path) else None
    packet["content_preview_redacted_or_excerpt"] = preview(text) if text else None
    packet["numeric_claims_detected"] = numeric_claims_detected(text or "")
    packet["source_evidence_required"] = packet["numeric_claims_detected"]
    packet["validation_errors"] = errors
    packet["block_reason"] = "validation_failed"
    flags = path_validation_flags(path) if path else {"not_template": False, "not_dryrun": False, "not_sample": False, "not_test_message": False}
    packet["validation"] = {
        "real_artifact_present": bool(path and path.exists()),
        "source_path_allowed": bool(path and source_path_allowed(path)),
        "content_nonempty": bool(text and text.strip()),
        "not_template": flags["not_template"],
        "not_dryrun": flags["not_dryrun"],
        "not_sample": flags["not_sample"],
        "not_test_message": flags["not_test_message"],
        "no_placeholder_fillers": not bool(text and PLACEHOLDER_TEXT_RE.search(text)),
        "no_webhook_or_secret_like_text": not bool(text and SECRETISH_RE.search(text)),
        "no_financial_advice_language": not bool(text and FINANCIAL_ADVICE_RE.search(text)),
        "no_trading_signal_language": not bool(text and TRADING_SIGNAL_RE.search(text)),
        "no_position_sizing_language": not bool(text and POSITION_SIZING_RE.search(text)),
        "no_guaranteed_prediction_language": not bool(text and GUARANTEED_PREDICTION_RE.search(text)),
        "numeric_claims_require_evidence": numeric_claims_detected(text or ""),
    }
    return packet


def materialize_source_artifact(source_artifact: str | Path | None = None, *, inbox: str | Path = DEFAULT_INBOX) -> dict[str, Any]:
    if source_artifact is None:
        found, candidates = find_single_source_artifact(inbox)
        if len(candidates) > 1:
            return fail_packet(None, ["multiple_source_artifacts_in_inbox"]) | {"candidate_source_artifact_paths": candidates}
        if found is None:
            return blocked_packet()
        source_artifact = found
    path = Path(source_artifact)
    if not source_path_allowed(path):
        return fail_packet(path, ["source_path_disallowed"])
    try:
        text = load_text(path)
    except (FileNotFoundError, OSError) as exc:
        return fail_packet(path, [f"source_artifact_unreadable:{exc.__class__.__name__}"])
    if not text.strip():
        return fail_packet(path, ["source_artifact_empty"], text)
    errors: list[str] = []
    flags = path_validation_flags(path)
    if not flags["not_template"]:
        errors.append("template_source_rejected")
    if not flags["not_dryrun"]:
        errors.append("dryrun_source_rejected")
    if not flags["not_sample"]:
        errors.append("sample_source_rejected")
    if not flags["not_test_message"]:
        errors.append("test_message_or_fixture_source_rejected")
    if SECRETISH_RE.search(text):
        errors.append("webhook_or_secret_like_text_blocked")
    if PLACEHOLDER_TEXT_RE.search(text):
        errors.append("placeholder_source_rejected")
    if FINANCIAL_ADVICE_RE.search(text):
        errors.append("financial_advice_language_blocked")
    if TRADING_SIGNAL_RE.search(text):
        errors.append("trading_signal_language_blocked")
    if POSITION_SIZING_RE.search(text):
        errors.append("position_sizing_language_blocked")
    if GUARANTEED_PREDICTION_RE.search(text):
        errors.append("guaranteed_prediction_language_blocked")
    if errors:
        return fail_packet(path, errors, text)
    target, content_type = infer_target_and_type(text, path)
    claims = numeric_claims_detected(text)
    return {
        "task_label": TASK_LABEL,
        "source_artifact_status": "READY_FOR_FILLED_INTAKE",
        "platform": PLATFORM,
        "source_artifact_path": path_text(path),
        "source_artifact_sha256": sha256_text(text),
        "source_artifact_kind": kind_for_path(path),
        "source_artifact_bytes": len(text.encode("utf-8")),
        "content_title_detected": detect_title(text, path),
        "content_preview_redacted_or_excerpt": preview(text),
        "recommended_target_name": target,
        "recommended_content_type": content_type,
        "source_evidence_paths_detected": [],
        "numeric_claims_detected": claims,
        "source_evidence_required": claims,
        "not_approved": True,
        "not_dispatchable": True,
        "not_public_postable": True,
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "raw_secret_output": False,
        "webhook_url_printed": False,
        "validation": {
            "real_artifact_present": True,
            "source_path_allowed": True,
            "content_nonempty": True,
            "not_template": True,
            "not_dryrun": True,
            "not_sample": True,
            "not_test_message": True,
            "no_placeholder_fillers": True,
            "no_webhook_or_secret_like_text": True,
            "no_financial_advice_language": True,
            "no_trading_signal_language": True,
            "no_position_sizing_language": True,
            "no_guaranteed_prediction_language": True,
            "numeric_claims_require_evidence": claims,
        },
    }


def source_artifact_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Discord Real Content Source Artifact Packet",
        "type": "object",
        "required": [
            "task_label",
            "source_artifact_status",
            "platform",
            "source_artifact_path",
            "source_artifact_sha256",
            "source_artifact_kind",
            "source_artifact_bytes",
            "content_title_detected",
            "content_preview_redacted_or_excerpt",
            "recommended_target_name",
            "recommended_content_type",
            "source_evidence_paths_detected",
            "numeric_claims_detected",
            "source_evidence_required",
            "not_approved",
            "not_dispatchable",
            "not_public_postable",
            "no_live_request_in_this_task",
            "no_env_read_in_this_task",
            "raw_secret_output",
            "webhook_url_printed",
            "validation",
        ],
        "properties": {
            "task_label": {"const": TASK_LABEL},
            "source_artifact_status": {"enum": ["READY_FOR_FILLED_INTAKE", "BLOCKED_AWAITING_OPERATOR_ARTIFACT", "FAIL_VALIDATION"]},
            "platform": {"const": PLATFORM},
            "not_approved": {"const": True},
            "not_dispatchable": {"const": True},
            "not_public_postable": {"const": True},
            "no_live_request_in_this_task": {"const": True},
            "no_env_read_in_this_task": {"const": True},
            "raw_secret_output": {"const": False},
            "webhook_url_printed": {"const": False},
        },
    }


def operator_source_artifact_instructions() -> str:
    return """# Discord Real Content Source Artifact Instructions\n\nJim supplies exactly one real Capital Chronicle source artifact for later filled-intake work.\n\n## Dropzone\n\nPut one real source artifact in:\n\n`docs/automation/DISCORD_REAL_CONTENT_SOURCE_ARTIFACT/inbox/`\n\nAllowed formats:\n\n- `.md`\n- `.txt`\n- `.json`\n\n## Rules\n\n- Use real Capital Chronicle content only.\n- Do not paste secrets, webhook URLs, cookies, tokens, or private session data.\n- Include evidence paths for numeric claims.\n- Avoid buy/sell/hold language.\n- Avoid position sizing guidance.\n- Avoid guaranteed predictions.\n- Choose target later unless source artifact clearly indicates announcement, Substack drop, or product update.\n- This task does not approve or dispatch anything.\n\n## CLI\n\nBlocked framework packet, no real artifact yet:\n\n```powershell\npython -m live_contentops.discord_real_content_source_artifact --output docs/automation/DISCORD_REAL_CONTENT_SOURCE_ARTIFACT/source_artifact_packet.json\n```\n\nOptional future explicit artifact path:\n\n```powershell\npython -m live_contentops.discord_real_content_source_artifact --source-artifact docs/automation/DISCORD_REAL_CONTENT_SOURCE_ARTIFACT/inbox/<real_file.md> --output docs/automation/DISCORD_REAL_CONTENT_SOURCE_ARTIFACT/source_artifact_packet.json\n```\n"""


def inbox_readme() -> str:
    return """# Discord Real Content Source Artifact Inbox\n\nDrop exactly one real Capital Chronicle source artifact here for Discord filled-intake preparation.\n\nAllowed file types:\n\n- `.md`\n- `.txt`\n- `.json`\n\nDo not place templates, dry-run payloads, samples, test fixtures, framework packets, implementation reports, walkthroughs, task logs, secrets, webhook URLs, cookies, or tokens here.\n"""


def implementation_report(packet: dict[str, Any]) -> str:
    return f"""# Discord Real Content Source Artifact Intake\n\nStatus: `PASS`\n\nSource artifact status: `{packet.get('source_artifact_status')}`\n\n- No live request in this task: `true`\n- No env read in this task: `true`\n- Fake public-postable content created: `false`\n- Auto-approval performed: `false`\n- Auto-dispatch performed: `false`\n\nIf no source artifact exists, framework remains blocked awaiting operator artifact.\n"""


def next_task_pointer(packet: dict[str, Any]) -> str:
    if packet.get("source_artifact_status") == "READY_FOR_FILLED_INTAKE":
        task = "TASK_CONTENTOPS_V6_DISCORD_REAL_CONTENT_FILLED_INTAKE_FROM_SOURCE_ARTIFACT_V0"
        goal = "materialize filled-intake packet from verified source artifact."
    else:
        task = "TASK_CONTENTOPS_V6_DISCORD_REAL_CONTENT_FILLED_INTAKE_PACKET_V0"
        goal = "wait for Jim to place one real source artifact into inbox and then bridge into filled intake."
    return f"# Next Task Pointer\n\nRecommended next task:\n\n`{task}`\n\nGoal: {goal}\n"


def write_all_outputs(output: str | Path, packet: dict[str, Any]) -> None:
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    inbox = out.parent / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    write_json(out, packet)
    write_json(out.parent / DEFAULT_SCHEMA.name, source_artifact_schema())
    (out.parent / "operator_source_artifact_instructions.md").write_text(operator_source_artifact_instructions(), encoding="utf-8")
    (inbox / "README.md").write_text(inbox_readme(), encoding="utf-8")
    (out.parent / "implementation_report.md").write_text(implementation_report(packet), encoding="utf-8")
    (out.parent / "next_task_pointer.md").write_text(next_task_pointer(packet), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize Discord real-content source artifact packet")
    parser.add_argument("--source-artifact", default=None)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--inbox", default=str(DEFAULT_INBOX))
    args = parser.parse_args(argv)
    packet = materialize_source_artifact(args.source_artifact, inbox=args.inbox)
    write_all_outputs(args.output, packet)
    print(json.dumps({
        "task_label": packet.get("task_label"),
        "source_artifact_status": packet.get("source_artifact_status"),
        "source_artifact_path": packet.get("source_artifact_path"),
        "recommended_target_name": packet.get("recommended_target_name"),
        "recommended_content_type": packet.get("recommended_content_type"),
        "no_live_request_in_this_task": packet.get("no_live_request_in_this_task"),
        "no_env_read_in_this_task": packet.get("no_env_read_in_this_task"),
        "not_approved": packet.get("not_approved"),
        "not_dispatchable": packet.get("not_dispatchable"),
        "not_public_postable": packet.get("not_public_postable"),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
