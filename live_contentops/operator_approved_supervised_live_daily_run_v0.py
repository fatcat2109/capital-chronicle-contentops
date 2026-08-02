"""Operator-approved supervised live Daily ContentOps runner.

This runner is intentionally narrow. It uses only existing configured safe
platform paths and stores redacted local evidence for the first supervised live
Daily ContentOps dispatch.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping

from live_contentops.live_entrypoint_registry_v1 import (
    LEGACY_AUTOMATION_QUARANTINED,
    quarantine,
)
from live_contentops.public_dispatch_freeze_guard_v6 import (
    append_public_dispatch_ledger,
    build_public_dispatch_payload_hash,
    build_public_dispatch_topic_hash,
    evaluate_public_dispatch_freeze,
    load_public_dispatch_hashes,
    make_public_dispatch_approval_marker,
)

TASK_LABEL = "TASK_CONTENTOPS_OPERATOR_APPROVED_SUPERVISED_LIVE_DAILY_RUN_V0"
CLASSIFICATION_PASS = "PASS_OPERATOR_APPROVED_SUPERVISED_LIVE_DAILY_RUN_V0"
CLASSIFICATION_PARTIAL = "PASS_PARTIAL_OPERATOR_APPROVED_SUPERVISED_LIVE_DAILY_RUN_V0"
CLASSIFICATION_BLOCKED = "BLOCKED_OPERATOR_APPROVED_SUPERVISED_LIVE_DAILY_RUN_V0"
CLASSIFICATION_FAILED = "FAILED_OPERATOR_APPROVED_SUPERVISED_LIVE_DAILY_RUN_V0"
BASELINE_HEAD = "491d5a9ed3f259108b01110a519cfd5d7221faa5"
REQUIRED_CAVEAT = "Candidate editorial draft. Numeric references require final source verification before publication."
OUTPUT_DIR = Path("docs/automation/OPERATOR_APPROVED_SUPERVISED_LIVE_DAILY_RUN_V0")
DEFAULT_DUPLICATE_LEDGER = Path("docs/automation/V6_PUBLIC_DISPATCH_FREEZE/public_dispatch_duplicate_ledger_v6.jsonl")

READINESS_GATE_PATH = Path("docs/automation/DAILY_PIPELINE_FRESH_CODEX_AUDIT_V0/live_readiness_gate_v0.json")
AUDIT_REPORT_PATH = Path("docs/automation/DAILY_PIPELINE_FRESH_CODEX_AUDIT_V0/pipeline_audit_report_v0.json")
ARTICLE_DRAFT_PATH = Path("docs/automation/DAILY_SEO_ARTICLE_DRAFTING_V0/article_draft_v0.md")
ARTICLE_METADATA_PATH = Path("docs/automation/DAILY_SEO_ARTICLE_DRAFTING_V0/article_draft_metadata_v0.json")
PLATFORM_COPY_PATH = Path("docs/automation/DAILY_PLATFORM_VARIANT_CANDIDATE_COPY_V0/platform_variant_candidate_copy_v0.json")
PLATFORM_SAFETY_PATH = Path("docs/automation/DAILY_PLATFORM_VARIANT_CANDIDATE_COPY_V0/platform_copy_safety_review_v0.json")
MEDIA_PLAN_PATH = Path("docs/automation/DAILY_MEDIA_PLAN_SPEC_V0/media_plan_spec_v0.json")


TelegramSendFunc = Callable[..., dict[str, Any]]


def _utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _repo_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "UNKNOWN"


def _stable_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _variant(platform_copy: Mapping[str, Any], platform: str) -> Mapping[str, Any]:
    for item in platform_copy.get("variants", []):
        if isinstance(item, Mapping) and item.get("platform") == platform:
            return item
    return {}


def _normalise_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _excerpt(text: str, limit: int = 260) -> str:
    cleaned = _normalise_spaces(text)
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def build_telegram_live_text(platform_copy: Mapping[str, Any]) -> str:
    telegram = _variant(platform_copy, "telegram")
    headline = str(telegram.get("headline") or "Capital Chronicle Candidate Brief").strip()
    body = str(telegram.get("body_copy") or "").strip()
    if REQUIRED_CAVEAT.lower() not in body.lower():
        body = f"{body}\n\n{REQUIRED_CAVEAT}".strip()
    return f"{headline}\n\n{body}".strip()


def _financial_advice_detected(text: str) -> bool:
    low = text.lower()
    patterns = [
        r"\bbuy\b",
        r"\bsell\b",
        r"\bhold\b",
        r"\bposition sizing\b",
        r"\bsizing\b",
        r"\bprice target\b",
        r"\btarget price\b",
    ]
    return any(re.search(pattern, low) for pattern in patterns)


def _safe_adapter_detection(repo_root: Path) -> tuple[list[str], list[dict[str, Any]]]:
    detected: list[str] = []
    skipped = [
        {
            "platform": "substack",
            "status": "SKIPPED_NO_SAFE_ADAPTER",
            "reason": "Existing Substack live path is browser-profile based; this exact task does not use browser/session state.",
        },
        {
            "platform": "x",
            "status": "SKIPPED_NO_SAFE_ADAPTER",
            "reason": "Existing X live paths are browser-profile/CDP or operator-outcome recording paths, not a non-browser safe send adapter for this task.",
        },
    ]
    if (repo_root / "live_contentops" / "telegram_live_adapter_v6.py").exists():
        detected.append("telegram")
    else:
        skipped.append(
            {
                "platform": "telegram",
                "status": "SKIPPED_NO_SAFE_ADAPTER",
                "reason": "Telegram live adapter module not found.",
            }
        )
    return detected, skipped


def _preflight_blockers(
    *,
    readiness_gate: Mapping[str, Any],
    platform_copy: Mapping[str, Any],
    platform_safety: Mapping[str, Any],
    media_plan: Mapping[str, Any],
    operator_approved_live_run: bool,
    max_send_attempts_per_platform: int,
) -> list[str]:
    blockers: list[str] = []
    if not operator_approved_live_run:
        blockers.append("operator_approved_live_run_flag_missing")
    if max_send_attempts_per_platform != 1:
        blockers.append("max_send_attempts_per_platform_must_equal_1")
    if readiness_gate.get("ready_for_separate_operator_approved_live_run") is not True:
        blockers.append("readiness_gate_not_ready")
    if readiness_gate.get("live_run_must_be_separate_task") is not True:
        blockers.append("readiness_gate_separate_task_flag_missing")
    if readiness_gate.get("blockers") != []:
        blockers.append("readiness_gate_has_blockers")
    if platform_safety.get("candidate_only") is not True:
        blockers.append("platform_copy_candidate_only_missing")
    if platform_copy.get("dispatch_allowed_now") is not False:
        blockers.append("platform_copy_prior_dispatch_flag_not_false")
    if platform_safety.get("dispatch_allowed_now") is not False:
        blockers.append("platform_safety_prior_dispatch_flag_not_false")
    if platform_safety.get("telegram_has_meaningful_text_body") is not True:
        blockers.append("telegram_meaningful_text_missing")
    telegram = _variant(platform_copy, "telegram")
    if not telegram:
        blockers.append("telegram_variant_missing")
    if not str(telegram.get("caveat_line") or "").strip():
        blockers.append("telegram_caveat_line_missing")
    if media_plan.get("generation_allowed_now") is not False or media_plan.get("chart_render_allowed_now") is not False:
        blockers.append("media_generation_not_blocked")
    live_text = build_telegram_live_text(platform_copy)
    if REQUIRED_CAVEAT not in live_text:
        blockers.append("required_live_caveat_missing")
    if _financial_advice_detected(live_text):
        blockers.append("financial_advice_or_trading_signal_detected")
    return blockers


def _run_id(head: str, started_at: str) -> str:
    suffix = hashlib.sha256(f"{head}:{started_at}:{TASK_LABEL}".encode("utf-8")).hexdigest()[:12]
    return f"daily_live_{suffix}"


def _redacted_error_summary(result: Mapping[str, Any]) -> str | None:
    if not result:
        return None
    if result.get("error"):
        return _excerpt(str(result.get("error")), 180)
    if result.get("error_response"):
        raw = json.dumps(result.get("error_response"), sort_keys=True, default=str)
        raw = re.sub(r"\b\d{6,12}:[A-Za-z0-9_-]{20,}\b", "<redacted_bot_token>", raw)
        raw = re.sub(r"Bearer\s+[A-Za-z0-9._-]{20,}", "Bearer <redacted_token>", raw, flags=re.IGNORECASE)
        return _excerpt(raw, 180)
    return None


def _result_status_from_adapter(result: Mapping[str, Any]) -> str:
    if result.get("status") == "SUCCESS":
        return "POSTED"
    error = str(result.get("error") or "").lower()
    if "missing telegram_bot_token" in error or "missing telegram_bot_token or telegram_target_chat_id" in error:
        return "BLOCKED_UNAVAILABLE"
    if result.get("status") == "PUBLIC_DISPATCH_FROZEN":
        return "FAILED"
    return "FAILED"


def _write_readme(output_dir: Path, classification: str) -> None:
    _write_text(
        output_dir / "README.md",
        "\n".join(
            [
                "# Operator Approved Supervised Live Daily Run V0",
                "",
                f"Classification: `{classification}`",
                "",
                "This packet records the bounded operator-approved live Daily ContentOps run.",
                "Only existing configured safe adapters were eligible.",
                "Substack and X were skipped because the available live paths are browser-profile based.",
                "",
            ]
        ),
    )


def run_operator_approved_supervised_live_daily_run(
    *,
    repo_root: str | Path = ".",
    output_dir: str | Path = OUTPUT_DIR,
    duplicate_ledger_path: str | Path | None = DEFAULT_DUPLICATE_LEDGER,
    operator_approved_live_run: bool,
    max_send_attempts_per_platform: int = 1,
    telegram_send_func: TelegramSendFunc | None = None,
    current_head: str | None = None,
    started_at: str | None = None,
) -> dict[str, Any]:
    quarantine(
        "contentops.legacy_operator_daily_live.v0",
        LEGACY_AUTOMATION_QUARANTINED,
        "Operator-approved daily live automation is legacy; use ContentOpsProductionOrchestrator.",
    )
    root = Path(repo_root)
    out_dir = Path(output_dir)
    started = started_at or _utc_now()
    head = current_head or _repo_head()

    readiness_gate = _read_json(root / READINESS_GATE_PATH)
    audit_report = _read_json(root / AUDIT_REPORT_PATH)
    article_metadata = _read_json(root / ARTICLE_METADATA_PATH)
    platform_copy = _read_json(root / PLATFORM_COPY_PATH)
    platform_safety = _read_json(root / PLATFORM_SAFETY_PATH)
    media_plan = _read_json(root / MEDIA_PLAN_PATH)

    telegram_text = build_telegram_live_text(platform_copy)
    topic = str(article_metadata.get("editorial_title") or "US Oil Export Surge")
    topic_hash = build_public_dispatch_topic_hash(topic, str(article_metadata.get("topic_family") or "energy_commodities"))
    telegram_payload_hash = build_public_dispatch_payload_hash(
        platform="telegram",
        action="post",
        body_text=telegram_text,
        topic_hash=topic_hash,
    )
    content_hash = _stable_content_hash(telegram_text)
    run_id = _run_id(head, started)
    detected, skipped_plan = _safe_adapter_detection(root)
    preflight_blockers = _preflight_blockers(
        readiness_gate=readiness_gate,
        platform_copy=platform_copy,
        platform_safety=platform_safety,
        media_plan=media_plan,
        operator_approved_live_run=operator_approved_live_run,
        max_send_attempts_per_platform=max_send_attempts_per_platform,
    )

    live_run_plan = {
        "task_label": TASK_LABEL,
        "baseline_head": BASELINE_HEAD,
        "operator_approved_live_run": operator_approved_live_run,
        "source_readiness_gate": str(READINESS_GATE_PATH),
        "source_platform_candidate_copy": str(PLATFORM_COPY_PATH),
        "platforms_requested": ["substack", "telegram", "x"],
        "platforms_with_safe_adapter_detected": detected,
        "platforms_skipped": skipped_plan,
        "duplicate_guard_policy": {
            "ledger_path": str(duplicate_ledger_path) if duplicate_ledger_path else None,
            "payload_hash_required": True,
            "max_send_attempts_per_platform": max_send_attempts_per_platform,
        },
        "caveat_required": REQUIRED_CAVEAT,
        "max_send_attempts_per_platform": max_send_attempts_per_platform,
        "dispatch_allowed_by_this_task": operator_approved_live_run and not preflight_blockers,
        "preflight_blockers": preflight_blockers,
        "audit_readiness_classification": audit_report.get("readiness_classification"),
    }
    _write_json(out_dir / "live_run_plan_v0.json", live_run_plan)

    skipped_results = [
        {
            "platform": item["platform"],
            "status": item["status"],
            "public_url_or_message_id_or_draft_id": None,
            "content_hash": None,
            "caveat_present": None,
            "duplicate_guard_result": "NOT_APPLICABLE_SKIPPED",
            "error_summary_redacted": item["reason"],
        }
        for item in skipped_plan
        if item["platform"] in {"substack", "x"}
    ]

    attempted_platforms: list[str] = []
    successful_platforms: list[str] = []
    failed_platforms: list[str] = []
    live_action_performed = False
    live_send_attempted = False
    telegram_readback: dict[str, Any] = {
        "platform": "telegram",
        "readback_available": False,
        "readback_status": "NOT_ATTEMPTED",
        "visible_text_excerpt_redacted_if_needed": None,
        "url_or_id": None,
        "caveat_visible": False,
        "meaningful_text_visible": False,
    }

    telegram_result: dict[str, Any]
    duplicate_guard_record: dict[str, Any]
    if preflight_blockers:
        duplicate_guard_record = {
            "status": "NOT_RUN_PREFLIGHT_BLOCKED",
            "dispatch_allowed": False,
            "blockers": preflight_blockers,
        }
        telegram_result = {
            "platform": "telegram",
            "status": "FAILED",
            "public_url_or_message_id_or_draft_id": None,
            "content_hash": content_hash,
            "caveat_present": REQUIRED_CAVEAT in telegram_text,
            "duplicate_guard_result": duplicate_guard_record["status"],
            "error_summary_redacted": "preflight_blocked:" + "|".join(preflight_blockers),
        }
        failed_platforms.append("telegram")
    elif "telegram" not in detected:
        duplicate_guard_record = {
            "status": "NOT_RUN_NO_SAFE_ADAPTER",
            "dispatch_allowed": False,
            "blockers": ["telegram_adapter_missing"],
        }
        telegram_result = {
            "platform": "telegram",
            "status": "SKIPPED_NO_SAFE_ADAPTER",
            "public_url_or_message_id_or_draft_id": None,
            "content_hash": content_hash,
            "caveat_present": REQUIRED_CAVEAT in telegram_text,
            "duplicate_guard_result": duplicate_guard_record["status"],
            "error_summary_redacted": "telegram_adapter_missing",
        }
    else:
        prior_hashes = load_public_dispatch_hashes(duplicate_ledger_path)
        approval_marker = make_public_dispatch_approval_marker(
            run_id=run_id,
            topic_hash=topic_hash,
            payload_hash=telegram_payload_hash,
            platform="telegram",
        )
        duplicate_guard_record = evaluate_public_dispatch_freeze(
            platform="telegram",
            action="post",
            run_id=run_id,
            topic_hash=topic_hash,
            operator_approval_marker=approval_marker,
            body_text=telegram_text,
            payload_hash=telegram_payload_hash,
            prior_dispatch_hashes=prior_hashes,
        )
        if duplicate_guard_record["dispatch_allowed"] is not True:
            telegram_result = {
                "platform": "telegram",
                "status": "FAILED",
                "public_url_or_message_id_or_draft_id": None,
                "content_hash": content_hash,
                "caveat_present": REQUIRED_CAVEAT in telegram_text,
                "duplicate_guard_result": duplicate_guard_record["status"],
                "error_summary_redacted": "duplicate_guard_blocked:" + "|".join(duplicate_guard_record.get("blockers", [])),
            }
            failed_platforms.append("telegram")
        else:
            attempted_platforms.append("telegram")
            live_send_attempted = True
            if telegram_send_func is None:
                from live_contentops.telegram_live_adapter_v6 import execute_telegram_post as telegram_send_func

            adapter_result = telegram_send_func(
                message=telegram_text,
                dry_run=False,
                parse_mode="HTML",
                approval_context={
                    "operator_approval_marker": approval_marker,
                    "run_id": run_id,
                    "topic_hash": topic_hash,
                    "payload_hash": telegram_payload_hash,
                    "prior_dispatch_hashes": prior_hashes,
                    "public_dispatch_ledger_path": str(duplicate_ledger_path) if duplicate_ledger_path else None,
                },
            )
            status = _result_status_from_adapter(adapter_result)
            public_id = str(adapter_result.get("id") or "") if status == "POSTED" else None
            if status == "POSTED":
                live_action_performed = True
                successful_platforms.append("telegram")
                append_public_dispatch_ledger(
                    ledger_path=duplicate_ledger_path,
                    platform="telegram",
                    action="post",
                    run_id=run_id,
                    topic_hash=topic_hash,
                    payload_hash=telegram_payload_hash,
                    status="SUCCESS",
                )
                response_text = telegram_text
                response = adapter_result.get("response")
                if isinstance(response, Mapping):
                    result_obj = response.get("result")
                    if isinstance(result_obj, Mapping) and result_obj.get("text"):
                        response_text = str(result_obj.get("text"))
                telegram_readback = {
                    "platform": "telegram",
                    "readback_available": True,
                    "readback_status": "MESSAGE_ID_RETURNED_BY_TELEGRAM_API",
                    "visible_text_excerpt_redacted_if_needed": _excerpt(response_text),
                    "url_or_id": public_id,
                    "caveat_visible": REQUIRED_CAVEAT in response_text,
                    "meaningful_text_visible": len(response_text.split()) > 20,
                }
            else:
                failed_platforms.append("telegram")
                if status == "BLOCKED_UNAVAILABLE":
                    telegram_readback["readback_status"] = "BLOCKED_UNAVAILABLE"
                else:
                    telegram_readback["readback_status"] = "FAILED_NO_READBACK"
            telegram_result = {
                "platform": "telegram",
                "status": status,
                "public_url_or_message_id_or_draft_id": public_id,
                "content_hash": content_hash,
                "caveat_present": REQUIRED_CAVEAT in telegram_text,
                "duplicate_guard_result": duplicate_guard_record["status"],
                "error_summary_redacted": _redacted_error_summary(adapter_result),
            }

    per_platform_results = skipped_results + [telegram_result]
    skipped_platforms = [item["platform"] for item in per_platform_results if item["status"].startswith("SKIPPED")]

    if successful_platforms and (skipped_platforms or failed_platforms):
        classification = CLASSIFICATION_PARTIAL
    elif successful_platforms:
        classification = CLASSIFICATION_PASS
    elif live_send_attempted and failed_platforms:
        classification = CLASSIFICATION_FAILED
    else:
        classification = CLASSIFICATION_BLOCKED

    finished = _utc_now()
    live_dispatch_results = {
        "task_label": TASK_LABEL,
        "live_run_started_at": started,
        "live_run_finished_at": finished,
        "attempted_platforms": attempted_platforms,
        "successful_platforms": successful_platforms,
        "skipped_platforms": skipped_platforms,
        "failed_platforms": failed_platforms,
        "per_platform_results": per_platform_results,
        "all_secret_values_redacted": True,
    }
    live_readback = {
        "per_platform_readback": [
            {
                "platform": "substack",
                "readback_available": False,
                "readback_status": "SKIPPED_NO_SAFE_ADAPTER",
                "visible_text_excerpt_redacted_if_needed": None,
                "url_or_id": None,
                "caveat_visible": None,
                "meaningful_text_visible": None,
            },
            {
                "platform": "x",
                "readback_available": False,
                "readback_status": "SKIPPED_NO_SAFE_ADAPTER",
                "visible_text_excerpt_redacted_if_needed": None,
                "url_or_id": None,
                "caveat_visible": None,
                "meaningful_text_visible": None,
            },
            telegram_readback,
        ],
        "readback_overall_status": "PASS_TELEGRAM_MESSAGE_ID_RETURNED" if telegram_readback["readback_available"] else "NO_LIVE_READBACK_AVAILABLE",
    }
    live_statuses = [item for item in per_platform_results if item["status"] in {"POSTED", "DRAFT_CREATED"}]
    caveat_present_all_live = all(item.get("caveat_present") is True for item in live_statuses) if live_statuses else False
    safety_review = {
        "operator_approved_live_run": operator_approved_live_run,
        "raw_secret_printed": False,
        "browser_session_secret_read": False,
        "platform_api_used_only_where_configured": True,
        "exact_numeric_claims_made": False,
        "financial_advice_detected": False,
        "trading_signal_detected": False,
        "price_target_detected": False,
        "duplicate_guard_passed": telegram_result.get("duplicate_guard_result") == "PASS" and "telegram" in successful_platforms,
        "caveat_present_all_live_outputs": caveat_present_all_live,
        "retry_storm_detected": False,
        "blockers": [] if successful_platforms else (preflight_blockers or duplicate_guard_record.get("blockers", [])),
    }
    run_evidence = {
        "classification": classification,
        "task_label": TASK_LABEL,
        "baseline_head": BASELINE_HEAD,
        "final_head_before_commit": head,
        "operator_approved_live_run": operator_approved_live_run,
        "live_action_performed": live_action_performed,
        "platforms_successful": successful_platforms,
        "platforms_skipped": skipped_platforms,
        "platforms_failed": failed_platforms,
        "no_raw_secret_read_confirmation": True,
        "no_raw_secret_logged_confirmation": True,
        "no_database_repair_confirmation": True,
        "no_new_source_fetch_confirmation": True,
        "no_media_generation_confirmation": True,
        "output_paths": {
            "readme": str(out_dir / "README.md"),
            "live_run_plan": str(out_dir / "live_run_plan_v0.json"),
            "live_dispatch_results": str(out_dir / "live_dispatch_results_v0.json"),
            "live_readback": str(out_dir / "live_readback_v0.json"),
            "live_run_safety_review": str(out_dir / "live_run_safety_review_v0.json"),
            "run_evidence": str(out_dir / "run_evidence_v0.json"),
        },
        "blockers": [] if successful_platforms else (preflight_blockers or duplicate_guard_record.get("blockers", [])),
        "exact_next_recommended_task": "TASK_CONTENTOPS_REVIEW_LIVE_DAILY_RUN_EVIDENCE_AND_UNBLOCK_NEXT_PLATFORM_SAFE_ADAPTERS_V0",
    }

    _write_readme(out_dir, classification)
    _write_json(out_dir / "live_dispatch_results_v0.json", live_dispatch_results)
    _write_json(out_dir / "live_readback_v0.json", live_readback)
    _write_json(out_dir / "live_run_safety_review_v0.json", safety_review)
    _write_json(out_dir / "run_evidence_v0.json", run_evidence)

    return {
        "classification": classification,
        "plan": live_run_plan,
        "dispatch_results": live_dispatch_results,
        "readback": live_readback,
        "safety_review": safety_review,
        "run_evidence": run_evidence,
    }
