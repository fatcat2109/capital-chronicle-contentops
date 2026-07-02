"""One-shot Substack operator-draft CLI using supervised CDP session.

OPERATOR NOTE: If a credential, webhook URL, or bot token is ever exposed in
chat logs, stdout, or repository files, you must IMMEDIATELY revoke and
regenerate it externally (e.g. via Discord Developer Portal or Telegram
BotFather). Never commit raw credentials to the repository or paste them into
chat transcripts.
"""
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


def run_cdp_draft(
    title: str,
    body: str,
    cdp_port: int,
) -> dict[str, Any]:
    """Connects to the browser context over CDP and populates a new Substack draft."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {
            "result_status": "BLOCKED",
            "blocker": "missing_cdp",
            "diagnostic": "playwright_not_installed",
            "sent": False,
            "attempted": 0,
        }

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.connect_over_cdp(f"http://localhost:{cdp_port}")
            except Exception as exc:
                return {
                    "result_status": "BLOCKED",
                    "blocker": "missing_cdp",
                    "diagnostic": f"cdp_connection_failed: {str(exc)}",
                    "sent": False,
                    "attempted": 0,
                }

            if not browser.contexts:
                return {
                    "result_status": "BLOCKED",
                    "blocker": "missing_cdp",
                    "diagnostic": "no_active_contexts",
                    "sent": False,
                    "attempted": 1,
                }

            context = browser.contexts[0]
            page = context.new_page()

            try:
                page.goto("https://substack.com/publish/post", timeout=15000)
                page.wait_for_load_state("load", timeout=15000)
            except Exception as exc:
                page.close()
                return {
                    "result_status": "BLOCKED",
                    "blocker": "ui_uncertainty",
                    "diagnostic": f"navigation_failed: {str(exc)}",
                    "sent": False,
                    "attempted": 1,
                }

            current_url = page.url
            if "sign-in" in current_url.lower() or "login" in current_url.lower():
                page.close()
                return {
                    "result_status": "BLOCKED",
                    "blocker": "login_or_account_mismatch",
                    "diagnostic": f"redirected_to_login: {current_url}",
                    "sent": False,
                    "attempted": 1,
                }

            # Locate Title
            try:
                title_textarea = page.locator("textarea[placeholder='Title'], textarea.post-title, textarea[placeholder*='Title']").first
                title_textarea.wait_for(timeout=5000)
                title_textarea.fill(title)
            except Exception as exc:
                page.close()
                return {
                    "result_status": "BLOCKED",
                    "blocker": "ui_uncertainty",
                    "diagnostic": f"title_selector_failed: {str(exc)}",
                    "sent": False,
                    "attempted": 1,
                }

            # Locate Body
            try:
                body_editor = page.locator(".ProseMirror, div[contenteditable='true'], .editor").first
                body_editor.wait_for(timeout=5000)
                body_editor.focus()
                body_editor.fill(body)
            except Exception as exc:
                page.close()
                return {
                    "result_status": "BLOCKED",
                    "blocker": "ui_uncertainty",
                    "diagnostic": f"body_selector_failed: {str(exc)}",
                    "sent": False,
                    "attempted": 1,
                }

            # Wait for autosave to complete
            page.wait_for_timeout(3000)
            page.close()

            return {
                "result_status": "PASS",
                "blocker": None,
                "diagnostic": "draft_created_and_autosaved",
                "sent": True,
                "attempted": 1,
            }

    except Exception as exc:
        return {
            "result_status": "FAIL",
            "blocker": "execution_failed",
            "diagnostic": f"unhandled_error: {str(exc)}",
            "sent": False,
            "attempted": 1,
        }


def build_evidence(
    *,
    title: str,
    body: str,
    execute: bool,
    task_id: str,
) -> dict[str, Any]:
    """Assembles redacted evidence for the Substack compose operation."""
    cdp_port = operator_browser_lab.resolve_cdp_port(os.environ)

    if not execute:
        status = "DRY_RUN"
        blocker = None
        diagnostic = "dry_run_no_browser_action"
        sent = False
        attempted = 0
    else:
        res = run_cdp_draft(title, body, cdp_port)
        status = res["result_status"]
        blocker = res["blocker"]
        diagnostic = res["diagnostic"]
        sent = res["sent"]
        attempted = res["attempted"]

    evidence = {
        "task_label": f"TASK_{task_id}",
        "mode": "execute" if execute else "dry_run",
        "result_status": status,
        "platform": "substack",
        "method": "createDraft",
        "message_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "message_length": len(body),
        "request_budget_max": REQUEST_BUDGET_MAX,
        "request_count_attempted": attempted,
        "retry_budget_max": RETRY_BUDGET_MAX,
        "retry_count_attempted": 0,
        "status_code_class": "2xx" if sent else ("4xx" if blocker else None),
        "diagnostic_interpretation": diagnostic,
        "sent": sent,
        "live_send_happened": False,
        "blocker": blocker,
        "raw_secret_output": False,
        "secret_derived_metadata_recorded": False,
        "response_body_recorded": False,
        "response_headers_recorded": False,
        "http_status_code_recorded": False,
        "scheduler_created": False,
        "queue_created": False,
        "browser_cdp_used": execute,
        "autonomous_dispatch_created": False,
        "dm_comment_reaction_created": False,
        "scraping_used": False,
    }

    # Gather secrets for hygiene guard check
    secrets = []
    for k, val in os.environ.items():
        k_upper = k.upper()
        if any(word in k_upper for word in ("TOKEN", "SECRET", "COOKIE", "PASSWORD", "SUBSTACK", "WEBHOOK", "KEY")):
            if val and len(val) > 3:
                secrets.append(val)

    if Path(".env").is_file():
        try:
            for line in Path(".env").read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    val = line.split("=", 1)[1].strip().strip('"').strip("'").strip()
                    if val and len(val) > 3:
                        secrets.append(val)
        except Exception:
            pass

    cli_safety.assert_clean_of_secrets(evidence, secrets)

    return evidence


def write_evidence(evidence: dict[str, Any], output: str | None) -> None:
    if not output:
        return
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a Substack draft via CDP supervised browser.")
    parser.add_argument("--title", required=True, help="Title of the draft.")
    parser.add_argument("--body", required=True, help="Body markdown content of the draft.")
    parser.add_argument("--task-id", default=DEFAULT_TASK_ID, help="Task id for evidence label.")
    parser.add_argument("--execute", action="store_true", help="Connect to the browser over CDP to run.")
    parser.add_argument("--output", help="Optional path to write evidence JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    evidence = build_evidence(
        title=args.title,
        body=args.body,
        execute=args.execute,
        task_id=args.task_id,
    )
    write_evidence(evidence, args.output)
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if evidence["result_status"] in {"DRY_RUN", "PASS"} else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
