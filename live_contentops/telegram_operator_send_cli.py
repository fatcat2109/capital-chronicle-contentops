"""One-shot Telegram operator-send CLI around the existing supervised send path.

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
from typing import Any, Callable

from live_contentops import cli_safety
from tools import telegram_run_single_supervised_sendmessage as telegram_runner


DEFAULT_TASK_ID = "0000"
REQUEST_BUDGET_MAX = 1
RETRY_BUDGET_MAX = 0

EnvProvider = Callable[[], dict[str, str]]
Transport = Callable[[], tuple[bool, int | None, dict[str, bool]]]


def _status_code_class(provider_class: str) -> str | None:
    if provider_class == telegram_runner.adapter.PROVIDER_CODE_SUCCESS_CLASS:
        return "2xx"
    if provider_class == telegram_runner.adapter.PROVIDER_CODE_CLIENT_ERROR_CLASS:
        return "4xx"
    if provider_class == telegram_runner.adapter.PROVIDER_CODE_SERVER_ERROR_CLASS:
        return "5xx"
    return None


def build_evidence(
    *,
    message: str,
    execute: bool,
    task_id: str,
    env_provider: EnvProvider = lambda: os.environ,
    http_transport: Transport | None = None,
) -> dict[str, Any]:
    env = env_provider()
    token = env.get(telegram_runner.DOTENV_TOKEN_KEY)
    destination = env.get(telegram_runner.DOTENV_DESTINATION_KEY) or env.get("TELEGRAM_CHANNEL_ID")
    _rendered, _enforcer, _one_request, result = telegram_runner.run_single_supervised_send(
        operator_live_send_enabled=execute,
        token=token,
        destination=destination,
        message_text=message,
        http_transport=http_transport,
    )
    attempted = int(bool(result["send_attempted"]))
    sent = bool(result["send_succeeded"])
    blocked_reasons = result.get("blocked_reasons") or []
    if not execute:
        status = "DRY_RUN"
        blocker = None
    elif sent:
        status = "PASS"
        blocker = None
    else:
        status = "BLOCKED" if blocked_reasons else "FAIL"
        blocker = "telegram_env_missing" if any(
            reason in blocked_reasons
            for reason in {telegram_runner.BLOCK_CREDENTIAL_MISSING, telegram_runner.BLOCK_DESTINATION_MISSING}
        ) else (blocked_reasons[0] if blocked_reasons else result["outcome_class"])

    evidence = {
        "task_label": f"TASK_{task_id}",
        "mode": "execute" if execute else "dry_run",
        "result_status": status,
        "platform": "telegram",
        "method": telegram_runner.adapter.METHOD_SUPERVISED_SEND,
        "message_sha256": hashlib.sha256(message.encode("utf-8")).hexdigest(),
        "message_length": len(message),
        "request_budget_max": REQUEST_BUDGET_MAX,
        "request_count_attempted": attempted,
        "retry_budget_max": RETRY_BUDGET_MAX,
        "retry_count_attempted": 0,
        "status_code_class": _status_code_class(result["provider_status_code_class"]),
        "diagnostic_interpretation": result["outcome_class"],
        "sent": sent,
        "live_send_happened": sent,
        "blocker": blocker,
        "raw_secret_output": False,
        "secret_derived_metadata_recorded": False,
        "response_body_recorded": False,
        "response_headers_recorded": False,
        "http_status_code_recorded": False,
        "scheduler_created": False,
        "queue_created": False,
        "browser_cdp_used": False,
        "autonomous_dispatch_created": False,
        "dm_comment_reaction_created": False,
        "scraping_used": False,
    }

    # Run the safety/redaction assertion check
    secrets = []
    if token:
        secrets.append(token)
    if destination:
        secrets.append(destination)
    for k, val in env.items():
        if "TOKEN" in k.upper() or "CHANNEL" in k.upper() or "WEBHOOK" in k.upper():
            if val:
                secrets.append(val)
    cli_safety.assert_clean_of_secrets(evidence, secrets)

    return evidence



def write_evidence(evidence: dict[str, Any], output: str | None) -> None:
    if not output:
        return
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send one operator-approved Telegram message via existing supervised path.")
    parser.add_argument("--message", required=True, help="Exact message text to dry-run or send.")
    parser.add_argument("--task-id", default=DEFAULT_TASK_ID, help="Task id for evidence label, e.g. 0009 -> TASK_0009.")
    parser.add_argument("--execute", action="store_true", help="Send exactly one Telegram message. Omit for dry-run.")
    parser.add_argument("--output", help="Optional path for redacted evidence JSON.")
    return parser.parse_args(argv)


def main(
    argv: list[str] | None = None,
    *,
    env_provider: EnvProvider = lambda: os.environ,
    http_transport: Transport | None = None,
) -> int:
    args = parse_args(argv)
    evidence = build_evidence(
        message=args.message,
        execute=args.execute,
        task_id=args.task_id,
        env_provider=env_provider,
        http_transport=http_transport,
    )
    write_evidence(evidence, args.output)
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if evidence["result_status"] in {"DRY_RUN", "PASS"} else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
