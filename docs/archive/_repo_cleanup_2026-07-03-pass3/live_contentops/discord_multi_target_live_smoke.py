"""Multi-target Discord live webhook smoke runner.

Dry-run is default and performs no network. Live mode performs exactly one POST per
configured target, with zero retries and redacted audit output.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_MULTI_TARGET_LIVE_WEBHOOK_SMOKE_V0"
PLATFORM = "discord"
ENDPOINT_FAMILY = "discord_execute_webhook"
METHOD = "POST"
REQUEST_BUDGET_MAX = 2
RETRY_BUDGET_MAX = 0
TIMEOUT_SECONDS = 10
USER_AGENT = "CapitalChronicleContentOps/1.0"
WAIT_QUERY_PARAM = False
PAYLOAD_MODE = "minimal_content_only"
FORBIDDEN_FINANCE_PHRASES = ("buy", "sell", "hold", "price target", "position sizing", "financial advice", "signal")


class DiscordSmokeBlocked(RuntimeError):
    """Raised when smoke preconditions fail before network attempt."""


@dataclass(frozen=True)
class DiscordSmokeTarget:
    target_name: str
    env_key_name: str
    destination_binding_id: str
    credential_handle_id: str
    content: str


TARGETS: tuple[DiscordSmokeTarget, ...] = (
    DiscordSmokeTarget(
        target_name="substack_drops",
        env_key_name="DISCORD_SUBSTACK_DROPS_WEBHOOK_URL",
        destination_binding_id="discord_substack_drops_capital_chronicle_01",
        credential_handle_id="discord_substack_drops_webhook_01",
        content="Capital Chronicle Discord live smoke test — Substack drops webhook connectivity check.",
    ),
    DiscordSmokeTarget(
        target_name="product_updates",
        env_key_name="DISCORD_PRODUCT_UPDATES_WEBHOOK_URL",
        destination_binding_id="discord_product_updates_capital_chronicle_01",
        credential_handle_id="discord_product_updates_webhook_01",
        content="Capital Chronicle Discord live smoke test — product updates webhook connectivity check.",
    ),
)


@dataclass
class RequestBudgetGuard:
    remaining_requests: int = REQUEST_BUDGET_MAX
    attempted_requests: int = 0
    per_target_attempts: dict[str, int] | None = None

    def __post_init__(self) -> None:
        if self.per_target_attempts is None:
            self.per_target_attempts = {}

    def spend_before_post(self, target_name: str) -> None:
        assert self.per_target_attempts is not None
        if self.remaining_requests <= 0:
            raise DiscordSmokeBlocked("request_budget_exhausted")
        if self.per_target_attempts.get(target_name, 0) >= 1:
            raise DiscordSmokeBlocked(f"per_target_budget_exhausted_{target_name}")
        self.remaining_requests -= 1
        self.attempted_requests += 1
        self.per_target_attempts[target_name] = self.per_target_attempts.get(target_name, 0) + 1


def build_minimal_content_body(target: DiscordSmokeTarget) -> dict[str, Any]:
    text = target.content.lower()
    for phrase in FORBIDDEN_FINANCE_PHRASES:
        if phrase in text:
            raise DiscordSmokeBlocked("forbidden_finance_language")
    return {"content": target.content, "allowed_mentions": {"parse": []}}


def with_wait_false(raw_url: str) -> str:
    url_parse = __import__("urllib.parse", fromlist=["parse"])
    parts = url_parse.urlsplit(raw_url)
    query = url_parse.parse_qsl(parts.query, keep_blank_values=True)
    query = [(k, v) for k, v in query if k != "wait"]
    query.append(("wait", "false"))
    return url_parse.urlunsplit((parts.scheme, parts.netloc, parts.path, url_parse.urlencode(query), parts.fragment))


def validate_discord_webhook_url(raw_url: str) -> None:
    url_parse = __import__("urllib.parse", fromlist=["parse"])
    parts = url_parse.urlsplit(raw_url)
    segments = parts.path.strip("/").split("/")
    if parts.scheme != "https":
        raise DiscordSmokeBlocked("webhook_url_invalid_scheme")
    if parts.netloc not in {"discord.com", "discordapp.com"}:
        raise DiscordSmokeBlocked("webhook_url_invalid_host")
    if len(segments) < 4 or segments[0] != "api" or segments[1] != "webhooks":
        raise DiscordSmokeBlocked("webhook_url_invalid_path")
    if not segments[2] or not segments[3]:
        raise DiscordSmokeBlocked("webhook_url_missing_id_or_token")


def status_code_class(status_code: int | None) -> str:
    if status_code is None:
        return "not_attempted"
    if 200 <= status_code <= 299:
        return "2xx"
    if 400 <= status_code <= 499:
        return "4xx"
    if 500 <= status_code <= 599:
        return "5xx"
    return "other"


def diagnostic_interpretation(status_code: int | None) -> str:
    if status_code is None:
        return "network_exception_before_response"
    if 200 <= status_code <= 299:
        return "success_2xx"
    if status_code == 400:
        return "payload_rejected_or_bad_request"
    if status_code in {401, 403}:
        return "credential_unauthorized"
    if status_code == 404:
        return "webhook_not_found_or_deleted"
    if status_code == 429:
        return "rate_limited"
    if 500 <= status_code <= 599:
        return "discord_server_error"
    return "unknown_http_status"


def execute_post_once(raw_url: str, target: DiscordSmokeTarget, guard: RequestBudgetGuard, opener: Callable[..., Any] | None = None) -> tuple[int | None, str | None]:
    guard.spend_before_post(target.target_name)
    url_request = __import__("urllib.request", fromlist=["request"])
    url_error = __import__("urllib.error", fromlist=["error"])
    post_url = with_wait_false(raw_url)
    data = json.dumps(build_minimal_content_body(target), separators=(",", ":")).encode("utf-8")
    req = url_request.Request(
        post_url,
        data=data,
        method=METHOD,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
    )
    opener = opener or url_request.urlopen
    try:
        response = opener(req, timeout=TIMEOUT_SECONDS)
        return int(getattr(response, "status", getattr(response, "code", 0))), None
    except url_error.HTTPError as exc:
        return int(exc.code), exc.__class__.__name__
    except Exception as exc:
        return None, exc.__class__.__name__


def empty_target_packet(target: DiscordSmokeTarget) -> dict[str, Any]:
    return {
        "target_name": target.target_name,
        "env_key_name": target.env_key_name,
        "destination_binding_id": target.destination_binding_id,
        "credential_handle_id": target.credential_handle_id,
        "request_count_attempted": 0,
        "http_status_code": None,
        "status_code_class": "not_attempted",
        "diagnostic_interpretation": "not_attempted",
        "live_write_completed": False,
        "response_body_recorded": False,
        "response_headers_recorded": False,
        "raw_secret_output": False,
    }


def make_packet(result_status: str, target_packets: list[dict[str, Any]], request_count_attempted: int) -> dict[str, Any]:
    targets_attempted = sum(1 for target in target_packets if target["request_count_attempted"] > 0)
    targets_passed = sum(1 for target in target_packets if target["live_write_completed"] is True)
    targets_failed = sum(1 for target in target_packets if target["request_count_attempted"] > 0 and target["live_write_completed"] is False)
    return {
        "task_label": TASK_LABEL,
        "platform": PLATFORM,
        "endpoint_family": ENDPOINT_FAMILY,
        "method": METHOD,
        "payload_mode": PAYLOAD_MODE,
        "result_status": result_status,
        "request_budget_max": REQUEST_BUDGET_MAX,
        "request_count_attempted": request_count_attempted,
        "retry_budget_max": RETRY_BUDGET_MAX,
        "retry_count_attempted": 0,
        "timeout_seconds": TIMEOUT_SECONDS,
        "wait_query_param": WAIT_QUERY_PARAM,
        "user_agent_set": True,
        "webhook_url_printed": False,
        "raw_secret_output": False,
        "response_body_recorded": False,
        "response_headers_recorded": False,
        "targets": target_packets,
        "summary": {
            "targets_planned": len(target_packets),
            "targets_attempted": targets_attempted,
            "targets_passed": targets_passed,
            "targets_failed": targets_failed,
        },
    }


def classify_result(target_packets: list[dict[str, Any]], *, execute: bool) -> str:
    if not execute:
        return "BLOCKED"
    passed = sum(1 for target in target_packets if target["live_write_completed"] is True)
    if passed == len(target_packets):
        return "PASS"
    if passed > 0:
        return "PARTIAL"
    return "FAIL"


def run_smoke(output_path: str | Path, *, execute: bool = False, environ: Any | None = None, opener: Callable[..., Any] | None = None) -> dict[str, Any]:
    guard = RequestBudgetGuard()
    target_packets = [empty_target_packet(target) for target in TARGETS]
    if execute:
        env = environ if environ is not None else getattr(__import__("os"), "environ")
        raw_urls: dict[str, str] = {}
        for target in TARGETS:
            raw_url = env.get(target.env_key_name)
            if not raw_url:
                raise DiscordSmokeBlocked(f"env_key_missing_{target.env_key_name}")
            validate_discord_webhook_url(raw_url)
            raw_urls[target.target_name] = raw_url
        for index, target in enumerate(TARGETS):
            status_code, _error_class = execute_post_once(raw_urls[target.target_name], target, guard, opener)
            status_class = status_code_class(status_code)
            target_packets[index].update(
                {
                    "request_count_attempted": 1,
                    "http_status_code": status_code,
                    "status_code_class": status_class,
                    "diagnostic_interpretation": diagnostic_interpretation(status_code),
                    "live_write_completed": status_class == "2xx",
                }
            )
    result_status = classify_result(target_packets, execute=execute)
    packet = make_packet(result_status, target_packets, guard.attempted_requests)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Discord multi-target webhook smoke")
    parser.add_argument("--output", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    try:
        packet = run_smoke(args.output, execute=args.execute)
    except DiscordSmokeBlocked as exc:
        target_packets = [empty_target_packet(target) for target in TARGETS]
        packet = make_packet("BLOCKED", target_packets, 0)
        packet["blocker"] = str(exc)
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "task_label": packet["task_label"],
        "result_status": packet["result_status"],
        "request_count_attempted": packet["request_count_attempted"],
        "retry_count_attempted": packet["retry_count_attempted"],
        "targets": [
            {
                "target_name": target["target_name"],
                "env_key_name": target["env_key_name"],
                "request_count_attempted": target["request_count_attempted"],
                "http_status_code": target["http_status_code"],
                "status_code_class": target["status_code_class"],
                "diagnostic_interpretation": target["diagnostic_interpretation"],
                "live_write_completed": target["live_write_completed"],
            }
            for target in packet["targets"]
        ],
        "summary": packet["summary"],
        "user_agent_set": packet["user_agent_set"],
        "webhook_url_printed": False,
        "raw_secret_output": False,
        "response_body_recorded": False,
        "response_headers_recorded": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
