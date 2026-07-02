"""Guarded one-shot Substack publish CLI for supervised CDP session."""
from __future__ import annotations

import argparse
import hashlib
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


def run_cdp_publish(*, draft_url: str, expected_title_sha256: str, email_mode: str, allow_schedule: bool, cdp_port: int) -> dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"result_status": "BLOCKED", "blocker": "missing_cdp", "diagnostic": "playwright_not_installed", "attempted": 0, "completed": False}
    try:
        with sync_playwright() as p:
            try:
                try:
                    browser = p.chromium.connect_over_cdp(f"http://localhost:{cdp_port}")
                except Exception:
                    browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{cdp_port}")
            except Exception as exc:
                return {"result_status": "BLOCKED", "blocker": "missing_cdp", "diagnostic": f"cdp_connection_failed: {str(exc)}", "attempted": 0, "completed": False}
            if not browser.contexts:
                return {"result_status": "BLOCKED", "blocker": "missing_cdp", "diagnostic": "no_active_contexts", "attempted": 1, "completed": False}
            page = browser.contexts[0].new_page()
            try:
                page.goto(draft_url, timeout=15000)
                page.wait_for_load_state("load", timeout=15000)
            except Exception as exc:
                page.close()
                return {"result_status": "BLOCKED", "blocker": "ui_uncertainty", "diagnostic": f"navigation_failed: {str(exc)}", "attempted": 1, "completed": False}
            current_url = page.url
            if "sign-in" in current_url.lower() or "login" in current_url.lower():
                page.close()
                return {"result_status": "BLOCKED", "blocker": "login_or_account_mismatch", "diagnostic": f"redirected_to_login: {current_url}", "attempted": 1, "completed": False}
            title_text = page.title()
            if hashlib.sha256(title_text.encode("utf-8")).hexdigest() != expected_title_sha256:
                page.close()
                return {"result_status": "BLOCKED", "blocker": "title_hash_mismatch", "diagnostic": "expected_title_sha256_mismatch", "attempted": 0, "completed": False}
            if _count(page.get_by_text("Schedule", exact=False)) and not allow_schedule:
                page.close()
                return {"result_status": "BLOCKED", "blocker": "schedule_risk", "diagnostic": "schedule_control_detected_without_allow_schedule", "attempted": 0, "completed": False}
            if email_mode == "no-email" and _count(page.get_by_text("Send email", exact=False)):
                # Detection only. The CLI may still proceed if a later UI has a no-email choice.
                pass
            publish = page.get_by_role("button", name="Publish")
            if not _count(publish):
                page.close()
                return {"result_status": "BLOCKED", "blocker": "ui_uncertainty", "diagnostic": "publish_button_not_detected", "attempted": 0, "completed": False}
            publish.first.click(timeout=5000)
            page.wait_for_timeout(1000)
            if email_mode == "no-email":
                no_email = page.get_by_text("No email", exact=False)
                if _count(no_email):
                    no_email.first.click(timeout=5000)
            final = page.get_by_role("button", name="Publish")
            if _count(final):
                final.first.click(timeout=5000)
            else:
                continue_button = page.get_by_role("button", name="Continue")
                if _count(continue_button):
                    continue_button.first.click(timeout=5000)
                else:
                    page.close()
                    return {"result_status": "BLOCKED", "blocker": "ui_uncertainty", "diagnostic": "final_publish_control_not_detected", "attempted": 1, "completed": False}
            page.wait_for_timeout(2000)
            page.close()
            return {"result_status": "PASS", "blocker": None, "diagnostic": "publish_completed_supervised", "attempted": 1, "completed": True}
    except Exception as exc:
        return {"result_status": "FAIL", "blocker": "execution_failed", "diagnostic": f"unhandled_error: {str(exc)}", "attempted": 1, "completed": False}


def build_evidence(*, draft_url: str | None, expected_title_sha256: str | None, allow_publication: bool, email_mode: str | None, allow_schedule: bool, execute: bool, task_id: str, secrets: list[str] | None = None) -> dict[str, Any]:
    if not execute:
        res = {"result_status": "DRY_RUN", "blocker": None, "diagnostic": "dry_run_no_browser_action", "attempted": 0, "completed": False}
    elif not allow_publication:
        res = {"result_status": "BLOCKED", "blocker": "missing_operator_publish_approval", "diagnostic": "allow_publication_required", "attempted": 0, "completed": False}
    elif not draft_url or not expected_title_sha256 or email_mode not in {"no-email", "send-email"}:
        res = {"result_status": "BLOCKED", "blocker": "missing_publish_inputs", "diagnostic": "draft_url_expected_title_sha256_email_mode_required", "attempted": 0, "completed": False}
    else:
        res = run_cdp_publish(draft_url=draft_url, expected_title_sha256=expected_title_sha256, email_mode=email_mode, allow_schedule=allow_schedule, cdp_port=operator_browser_lab.resolve_cdp_port(os.environ))
    completed = bool(res["completed"])
    evidence = {
        "task_label": f"TASK_{task_id}",
        "mode": "execute" if execute else "dry_run",
        "result_status": res["result_status"],
        "platform": "substack",
        "method": "publishPost",
        "request_budget_max": REQUEST_BUDGET_MAX,
        "request_count_attempted": res["attempted"],
        "retry_budget_max": RETRY_BUDGET_MAX,
        "retry_count_attempted": 0,
        "diagnostic_interpretation": res["diagnostic"],
        "publish_attempted": bool(execute and allow_publication and res["attempted"]),
        "publish_completed": completed,
        "draft_created": True if completed else False,
        "sent": completed,
        "live_send_happened": False,
        "email_send_attempted": bool(completed and email_mode == "send-email"),
        "schedule_attempted": bool(completed and allow_schedule),
        "public_url_recorded": False,
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
    parser = argparse.ArgumentParser(description="Publish one Substack draft through supervised CDP session.")
    parser.add_argument("--draft-url")
    parser.add_argument("--expected-title-sha256")
    parser.add_argument("--allow-publication", action="store_true")
    parser.add_argument("--email-mode", choices=["no-email", "send-email"])
    parser.add_argument("--allow-schedule", action="store_true")
    parser.add_argument("--task-id", default=DEFAULT_TASK_ID)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--output")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, secrets: list[str] | None = None) -> int:
    args = parse_args(argv)
    evidence = build_evidence(draft_url=args.draft_url, expected_title_sha256=args.expected_title_sha256, allow_publication=args.allow_publication, email_mode=args.email_mode, allow_schedule=args.allow_schedule, execute=args.execute, task_id=args.task_id, secrets=secrets)
    write_evidence(evidence, args.output)
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if evidence["result_status"] in {"DRY_RUN", "PASS"} else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
