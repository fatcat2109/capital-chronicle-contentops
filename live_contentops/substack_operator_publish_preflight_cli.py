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


def _safe_page_text(page: Any) -> str:
    try:
        return str(getattr(page, "url", "") or "").lower()
    except Exception:
        return ""


def classify_current_page(page: Any) -> tuple[str, str]:
    safe_hint = _safe_page_text(page)
    if not safe_hint:
        return "unknown", "no_safe_page_hint"
    if "sign-in" in safe_hint or "login" in safe_hint:
        return "login", "login_path_hint"
    if "new-post" in safe_hint or "/publish" in safe_hint or "/p/" in safe_hint or "draft" in safe_hint or "post" in safe_hint:
        return "editor_or_draft_candidate", "editor_path_hint"
    if "dashboard" in safe_hint:
        return "dashboard", "dashboard_path_hint"
    if safe_hint.rstrip("/").endswith("substack.com") or safe_hint == "about:blank":
        return "substack_home", "home_path_hint"
    return "other", "other_path_hint"


def run_cdp_preflight(*, draft_url: str | None, use_current_draft: bool, cdp_port: int) -> dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"result_status": "BLOCKED", "blocker": "missing_cdp", "diagnostic": "playwright_not_installed", "attempted": 0, "current_page_class": "unknown", "current_page_reason": "playwright_not_installed"}

    try:
        with sync_playwright() as p:
            try:
                try:
                    browser = p.chromium.connect_over_cdp(f"http://localhost:{cdp_port}")
                except Exception:
                    browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{cdp_port}")
            except Exception as exc:
                return {"result_status": "BLOCKED", "blocker": "missing_cdp", "diagnostic": f"cdp_connection_failed: {str(exc)}", "attempted": 0, "current_page_class": "unknown", "current_page_reason": "cdp_connection_failed"}

            if not browser.contexts:
                return {"result_status": "BLOCKED", "blocker": "missing_cdp", "diagnostic": "no_active_contexts", "attempted": 1, "current_page_class": "unknown", "current_page_reason": "no_active_contexts"}

            context = browser.contexts[0]
            page = None
            if use_current_draft:
                pages = list(getattr(context, "pages", []) or [])
                if not pages:
                    return {"result_status": "BLOCKED", "blocker": "current_draft_not_active", "diagnostic": "no_active_pages", "attempted": 1, "current_page_class": "unknown", "current_page_reason": "no_active_pages"}
                page = pages[-1]
                current_page_class, current_page_reason = classify_current_page(page)
                if current_page_class != "editor_or_draft_candidate":
                    return {"result_status": "BLOCKED", "blocker": "current_draft_not_active", "diagnostic": "current_page_not_editor_or_draft_candidate", "attempted": 1, "current_page_class": current_page_class, "current_page_reason": current_page_reason}
            if page is None:
                page = context.new_page()
                current_page_class, current_page_reason = "unknown", "navigation_target_not_recorded"
                if not draft_url:
                    return {"result_status": "BLOCKED", "blocker": "missing_draft_url", "diagnostic": "draft_url_required_without_current_page", "attempted": 0, "current_page_class": current_page_class, "current_page_reason": current_page_reason}
                try:
                    page.goto(draft_url, timeout=15000)
                    page.wait_for_load_state("load", timeout=15000)
                    current_page_class, current_page_reason = classify_current_page(page)
                except Exception as exc:
                    page.close()
                    return {"result_status": "BLOCKED", "blocker": "ui_uncertainty", "diagnostic": f"navigation_failed: {str(exc)}", "attempted": 1, "current_page_class": "unknown", "current_page_reason": "navigation_failed"}

            if current_page_class == "login":
                if not use_current_draft:
                    page.close()
                return {"result_status": "BLOCKED", "blocker": "login_or_account_mismatch", "diagnostic": "redirected_to_login", "attempted": 1, "current_page_class": current_page_class, "current_page_reason": current_page_reason}

            publish_controls = _count(page.get_by_role("button", name="Publish")) + _count(page.get_by_text("Publish", exact=False))
            continue_controls = _count(page.get_by_role("button", name="Continue")) + _count(page.get_by_text("Continue", exact=False))
            schedule_controls = _count(page.get_by_text("Schedule", exact=False))
            email_controls = _count(page.get_by_text("Email", exact=False)) + _count(page.get_by_text("Send email", exact=False))
            if not use_current_draft:
                page.close()
            if publish_controls <= 0:
                return {"result_status": "BLOCKED", "blocker": "ui_uncertainty", "diagnostic": "publish_controls_not_detected", "attempted": 1, "current_page_class": current_page_class, "current_page_reason": current_page_reason}
            return {
                "result_status": "PASS",
                "blocker": None,
                "diagnostic": "publish_preflight_controls_detected",
                "attempted": 1,
                "current_page_class": current_page_class,
                "current_page_reason": current_page_reason,
                "publish_controls_detected": True,
                "continue_controls_detected": continue_controls > 0,
                "schedule_risk_detected": schedule_controls > 0,
                "email_send_risk_detected": email_controls > 0,
            }
    except Exception as exc:
        return {"result_status": "FAIL", "blocker": "execution_failed", "diagnostic": f"unhandled_error: {str(exc)}", "attempted": 1, "current_page_class": "unknown", "current_page_reason": "execution_failed"}


def build_evidence(*, draft_url: str | None, use_current_draft: bool, execute: bool, task_id: str, secrets: list[str] | None = None) -> dict[str, Any]:
    if not execute:
        res = {"result_status": "DRY_RUN", "blocker": None, "diagnostic": "dry_run_no_browser_action", "attempted": 0, "current_page_class": "unknown", "current_page_reason": "dry_run_no_browser_action"}
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
        "publish_preflight_completed": res["result_status"] == "PASS",
        "publish_controls_detected": bool(res.get("publish_controls_detected", False)),
        "continue_controls_detected": bool(res.get("continue_controls_detected", False)),
        "schedule_risk_detected": bool(res.get("schedule_risk_detected", False)),
        "email_send_risk_detected": bool(res.get("email_send_risk_detected", False)),
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
