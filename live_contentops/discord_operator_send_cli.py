"""One-shot Discord operator-send CLI around the proven dispatch adapter path.

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
import sys
from pathlib import Path
from typing import Any, Callable

from live_contentops import cli_safety
from live_contentops.discord_dispatch_adapter import DiscordDispatchAdapter, TARGET_CONFIGS

DEFAULT_TASK_ID = "0000"
DEFAULT_TARGET = "announcements"
DEFAULT_PAYLOAD_ID = "operator_send_cli_message"



def build_evidence(
    *,
    message: str,
    target: str,
    execute: bool,
    task_id: str,
    adapter_factory: Callable[[], DiscordDispatchAdapter],
) -> dict[str, Any]:
    config = TARGET_CONFIGS[target]
    message_hash = hashlib.sha256(message.encode("utf-8")).hexdigest()
    payload = {"payload_id": DEFAULT_PAYLOAD_ID, "content": message}
    adapter = adapter_factory()
    result = adapter.dispatch(
        payload,
        target_name=target,
        destination_binding_id=config.destination_binding_id,
        credential_handle_id=config.credential_handle_id,
        payload_hash=message_hash,
        execute=execute,
    )
    evidence = {
        "task_label": f"TASK_{task_id}",
        "mode": "execute" if execute else "dry_run",
        "result_status": result["result_status"],
        "platform": result["platform"],
        "target_name": result["target_name"],
        "destination_binding_id": result["destination_binding_id"],
        "credential_handle_id": result["credential_handle_id"],
        "env_key_name": result["env_key_name"],
        "message_sha256": message_hash,
        "message_length": len(message),
        "request_budget_max": result["request_budget_max"],
        "request_count_attempted": result["request_count_attempted"],
        "retry_budget_max": result["retry_budget_max"],
        "retry_count_attempted": result["retry_count_attempted"],
        "status_code_class": result["status_code_class"],
        "diagnostic_interpretation": result["diagnostic_interpretation"],
        "sent": result["live_write_completed"],
        "live_send_happened": result["live_write_completed"],
        "blocker": result.get("blocker"),
        "webhook_url_printed": False,
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
    for cfg in TARGET_CONFIGS.values():
        val = adapter.environ.get(cfg.env_key_name)
        if val:
            secrets.append(val)
    for k, val in adapter.environ.items():
        if "WEBHOOK" in k.upper() or "TOKEN" in k.upper():
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
    parser = argparse.ArgumentParser(description="Send one operator-approved Discord message via existing adapter.")
    parser.add_argument("--message", required=True, help="Exact message text to dry-run or send.")
    parser.add_argument("--task-id", default=DEFAULT_TASK_ID, help="Task id for evidence label, e.g. 0007 -> TASK_0007.")
    parser.add_argument("--target", default=DEFAULT_TARGET, choices=sorted(TARGET_CONFIGS), help="Discord target route.")
    parser.add_argument("--execute", action="store_true", help="Send exactly one POST. Omit for dry-run.")
    parser.add_argument("--output", help="Optional path for redacted evidence JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, *, adapter_factory: Callable[[], DiscordDispatchAdapter] = DiscordDispatchAdapter) -> int:
    args = parse_args(argv)
    evidence = build_evidence(
        message=args.message,
        target=args.target,
        execute=args.execute,
        task_id=args.task_id,
        adapter_factory=adapter_factory,
    )
    write_evidence(evidence, args.output)
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if evidence["result_status"] in {"DRY_RUN", "PASS"} else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
