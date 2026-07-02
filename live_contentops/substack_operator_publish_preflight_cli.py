"""Substack publish preflight CLI. Detects publish controls without publishing."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from live_contentops import cli_safety
from live_contentops import operator_browser_lab

DEFAULT_TASK_ID = "0000"
REQUEST_BUDGET_MAX = 1
RETRY_BUDGET_MAX = 0


def _count(locator: Any) -> int:
    try:
        return int(locator.count())
    except Exception:
        return 0


def _visible_count(page: Any, label: str) -> int:
    return _count(page.get_by_role("button", name=label)) + _count(page.get_by_text(label, exact=False))


def collect_ui_signals(page: Any) -> dict[str, bool]:
    publish_signal = _visible_count(page, "Publish") > 0
    continue_signal = _visible_count(page, "Continue") > 0
    schedule_signal = _count(page.get_by_text("Schedule", exact=False)) > 0
    email_signal = (_count(page.get_by_text("Email", exact=False)) + _count(page.get_by_text("Send email", exact=False))) > 0
    login_signal = (_visible_count(page, "Sign in") + _visible_count(page, "Log in") + _visible_count(page, "Login")) > 0
    editor_signal = (_count(page.locator("[contenteditable='true']")) + _count(page.get_by_text("Untitled", exact=False))) > 0
    dashboard_signal = (_visible_count(page, "Dashboard") + _visible_count(page, "Create") + _visible_count(page, "New post")) > 0
    return {
        "editor_signal_detected": editor_signal,
        "publish_signal_detected": publish_signal,
        "continue_signal_detected": continue_signal,
        "schedule_signal_detected": schedule_signal,
        "email_signal_detected": email_signal,
        "login_signal_detected": login_signal,
        "dashboard_signal_detected": dashboard_signal,
    }


def classify_current_page(signals: dict[str, bool]) -> tuple[str, str]:
    if signals["login_signal_detected"]:
        return "login", "login_ui_signal"
    if signals["publish_signal_detected"] or signals["continue_signal_detected"] or signals["editor_signal_detected"]:
        return "editor_or_draft_candidate", "editor_ui_signal"
    if signals["dashboard_signal_detected"]:
        return "dashboard", "dashboard_ui_signal"
    return "unknown", "ui_signals_inconclusive"


def _assist_hint(page_class: str, signals: dict[str, bool]) -> str:
    if page_class == "login":
        return "login_required"
    if page_class == "dashboard":
        return "open_draft_editor"
    if page_class == "editor_or_draft_candidate" and signals["publish_signal_detected"]:
        return "publish_control_detected_no_click"
    if page_class == "editor_or_draft_candidate":
        return "editor_detected_publish_control_missing"
    if page_class == "unknown":
        return "unknown_ui_state"
    return "unknown_ui_state"


def _base_preflight(result_status: str, blocker: str | None, diagnostic: str, attempted: int, page_class: str = "unknown", page_reason: str = "ui_signals_inconclusive", signals: dict[str, bool] | None = None) -> dict[str, Any]:
    safe_signals = signals or {
        "editor_signal_detected": False,
        "publish_signal_detected": False,
        "continue_signal_detected": False,
        "schedule_signal_detected": False,
        "email_signal_detected": False,
        "login_signal_detected": False,
        "dashboard_signal_detected": False,
    }
    return {
        "result_status": result_status,
        "blocker": blocker,
        "diagnostic": diagnostic,
        "attempted": attempted,
        "current_page_class": page_class,
        "current_page_reason": page_reason,
        "assist_hint": _assist_hint(page_class, safe_signals),
        **safe_signals,
    }


def run_cdp_preflight(*, draft_url: str | None, use_current_draft: bool, cdp_port: int) -> dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return _base_preflight("BLOCKED", "missing_cdp", "playwright_not_installed", 0, page_reason="playwright_not_installed")

    try:
        with sync_playwright() as p:
            try:
                try:
                    browser = p.chromium.connect_over_cdp(f"http://localhost:{cdp_port}")
                except Exception:
                    browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{cdp_port}")
            except Exception as exc:
                return _base_preflight("BLOCKED", "missing_cdp", f"cdp_connection_failed: {str(exc)}", 0, page_reason="cdp_connection_failed")

            if not browser.contexts:
                return _base_preflight("BLOCKED", "missing_cdp", "no_active_contexts", 1, page_reason="no_active_contexts")

            context = browser.contexts[0]
            page = None
            if use_current_draft:
                pages = list(getattr(context, "pages", []) or [])
                if not pages:
                    return _base_preflight("BLOCKED", "current_draft_not_active", "no_active_pages", 1, page_reason="no_active_pages")
                page = pages[-1]
                signals = collect_ui_signals(page)
                current_page_class, current_page_reason = classify_current_page(signals)
                if current_page_class != "editor_or_draft_candidate":
                    return _base_preflight("BLOCKED", "current_draft_not_active", "current_page_not_editor_or_draft_candidate", 1, current_page_class, current_page_reason, signals)
            if page is None:
                page = context.new_page()
                current_page_class, current_page_reason = "unknown", "navigation_target_not_recorded"
                signals = None
                if not draft_url:
                    return _base_preflight("BLOCKED", "missing_draft_url", "draft_url_required_without_current_page", 0, current_page_class, current_page_reason)
                try:
                    page.goto(draft_url, timeout=15000)
                    page.wait_for_load_state("load", timeout=15000)
                    signals = collect_ui_signals(page)
                    current_page_class, current_page_reason = classify_current_page(signals)
                except Exception as exc:
                    page.close()
                    return _base_preflight("BLOCKED", "ui_uncertainty", f"navigation_failed: {str(exc)}", 1, page_reason="navigation_failed")

            if current_page_class == "login":
                if not use_current_draft:
                    page.close()
                return _base_preflight("BLOCKED", "login_or_account_mismatch", "redirected_to_login", 1, current_page_class, current_page_reason, signals)

            if not use_current_draft:
                page.close()
            if not signals["publish_signal_detected"]:
                return _base_preflight("BLOCKED", "ui_uncertainty", "publish_controls_not_detected", 1, current_page_class, current_page_reason, signals)
            return {
                **_base_preflight("PASS", None, "publish_preflight_controls_detected", 1, current_page_class, current_page_reason, signals),
                "publish_controls_detected": True,
                "continue_controls_detected": signals["continue_signal_detected"],
                "schedule_risk_detected": signals["schedule_signal_detected"],
                "email_send_risk_detected": signals["email_signal_detected"],
            }
    except Exception as exc:
        return _base_preflight("FAIL", "execution_failed", f"unhandled_error: {str(exc)}", 1, page_reason="execution_failed")


def build_evidence(*, draft_url: str | None, use_current_draft: bool, execute: bool, task_id: str, secrets: list[str] | None = None) -> dict[str, Any]:
    if not execute:
        res = _base_preflight("DRY_RUN", None, "dry_run_no_browser_action", 0, page_reason="dry_run_no_browser_action")
    else:
        res = run_cdp_preflight(draft_url=draft_url, use_current_draft=use_current_draft, cdp_port=operator_browser_lab.resolve_cdp_port(os.environ))
    evidence = {
        "task_label": f"TASK_{task_id}",
        "mode": "execute" if execute else "dry_run",
        "result_status": res["result_status"],
        "platform": "substack",
        "method": "publishPreflight",
        "request_budget_max": REQUEST_BUDGET_MAX,
        "request_count_attempted": res["attempted"],
        "retry_budget_max": RETRY_BUDGET_MAX,
        "retry_count_attempted": 0,
        "diagnostic_interpretation": res["diagnostic"],
        "current_page_class": res.get("current_page_class", "unknown"),
        "current_page_reason": res.get("current_page_reason", "no_safe_page_hint"),
        "assist_hint": res.get("assist_hint", "unknown_ui_state"),
        "editor_signal_detected": bool(res.get("editor_signal_detected", False)),
        "publish_signal_detected": bool(res.get("publish_signal_detected", False)),
        "continue_signal_detected": bool(res.get("continue_signal_detected", False)),
        "schedule_signal_detected": bool(res.get("schedule_signal_detected", False)),
        "email_signal_detected": bool(res.get("email_signal_detected", False)),
        "publish_preflight_completed": res["result_status"] == "PASS",
        "publish_controls_detected": bool(res.get("publish_controls_detected", res.get("publish_signal_detected", False))),
        "continue_controls_detected": bool(res.get("continue_controls_detected", res.get("continue_signal_detected", False))),
        "schedule_risk_detected": bool(res.get("schedule_risk_detected", res.get("schedule_signal_detected", False))),
        "email_send_risk_detected": bool(res.get("email_send_risk_detected", res.get("email_signal_detected", False))),
        "publish_attempted": False,
        "schedule_attempted": False,
        "email_send_attempted": False,
        "draft_created": False,
        "sent": False,
        "live_send_happened": False,
        "blocker": res["blocker"],
        "browser_cdp_used": execute,
        "raw_secret_output": False,
        "secret_derived_metadata_recorded": False,
        "response_body_recorded": False,
        "response_headers_recorded": False,
        "http_status_code_recorded": False,
        "scheduler_created": False,
        "queue_created": False,
        "autonomous_dispatch_created": False,
        "dm_comment_reaction_created": False,
        "scraping_used": False,
    }
    if secrets:
        cli_safety.assert_clean_of_secrets(evidence, secrets)
    return evidence


def write_evidence(evidence: dict[str, Any], output: str | None) -> None:
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect Substack publish controls without publishing.")
    parser.add_argument("--draft-url")
    parser.add_argument("--use-current-draft", action="store_true")
    parser.add_argument("--task-id", default=DEFAULT_TASK_ID)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--output")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, secrets: list[str] | None = None) -> int:
    args = parse_args(argv)
    evidence = build_evidence(draft_url=args.draft_url, use_current_draft=args.use_current_draft, execute=args.execute, task_id=args.task_id, secrets=secrets)
    write_evidence(evidence, args.output)
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if evidence["result_status"] in {"DRY_RUN", "PASS"} else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
