"""Reusable Discord dispatch adapter for approved/outbox payload packets.

Default mode is dry-run and performs no network. Execute mode exists for future
explicit live-dispatch tasks and is covered here only through mocked opener tests.
"""
from __future__ import annotations

import argparse
import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_DISPATCH_ADAPTER_FROM_OUTBOX_V0"
PLATFORM = "discord"
ENDPOINT_FAMILY = "discord_execute_webhook"
METHOD = "POST"
REQUEST_BUDGET_MAX = 1
RETRY_BUDGET_MAX = 0
TIMEOUT_SECONDS = 10
USER_AGENT = "CapitalChronicleContentOps/1.0"
WAIT_QUERY_PARAM = False
FORBIDDEN_REQUEST_FIELDS = {
    "attachments",
    "files",
    "components",
    "poll",
    "thread_id",
    "thread_name",
    "applied_tags",
}


class DiscordDispatchBlocked(RuntimeError):
    """Raised when dispatch validation blocks before network attempt."""


@dataclass(frozen=True)
class DiscordTargetConfig:
    target_name: str
    env_key_name: str
    destination_binding_id: str
    credential_handle_id: str


TARGET_CONFIGS: dict[str, DiscordTargetConfig] = {
    "announcements": DiscordTargetConfig(
        target_name="announcements",
        env_key_name="DISCORD_ANNOUNCEMENTS_WEBHOOK_URL",
        destination_binding_id="discord_announcements_capital_chronicle_01",
        credential_handle_id="discord_announcements_webhook_01",
    ),
    "substack_drops": DiscordTargetConfig(
        target_name="substack_drops",
        env_key_name="DISCORD_SUBSTACK_DROPS_WEBHOOK_URL",
        destination_binding_id="discord_substack_drops_capital_chronicle_01",
        credential_handle_id="discord_substack_drops_webhook_01",
    ),
    "product_updates": DiscordTargetConfig(
        target_name="product_updates",
        env_key_name="DISCORD_PRODUCT_UPDATES_WEBHOOK_URL",
        destination_binding_id="discord_product_updates_capital_chronicle_01",
        credential_handle_id="discord_product_updates_webhook_01",
    ),
}


@dataclass
class DispatchBudgetGuard:
    remaining_requests: int = REQUEST_BUDGET_MAX
    attempted_requests: int = 0

    def spend_before_post(self) -> None:
        if self.remaining_requests <= 0:
            raise DiscordDispatchBlocked("request_budget_exhausted")
        self.remaining_requests -= 1
        self.attempted_requests += 1


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
        raise DiscordDispatchBlocked("webhook_url_invalid_scheme")
    if parts.netloc not in {"discord.com", "discordapp.com"}:
        raise DiscordDispatchBlocked("webhook_url_invalid_host")
    if len(segments) < 4 or segments[0] != "api" or segments[1] != "webhooks":
        raise DiscordDispatchBlocked("webhook_url_invalid_path")
    if not segments[2] or not segments[3]:
        raise DiscordDispatchBlocked("webhook_url_missing_id_or_token")


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


def load_payload_packet(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def payloads_from_packet(packet: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(packet.get("payloads"), list):
        return [payload for payload in packet["payloads"] if isinstance(payload, dict)]
    return [packet]


def select_payload(packet: dict[str, Any], payload_id: str) -> dict[str, Any]:
    for payload in payloads_from_packet(packet):
        if payload.get("payload_id") == payload_id:
            return payload
    raise DiscordDispatchBlocked(f"payload_id_not_found_{payload_id}")


def normalize_payload_body(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise DiscordDispatchBlocked("payload_not_object")
    if isinstance(payload.get("redacted_webhook_json_preview"), dict):
        candidate = dict(payload["redacted_webhook_json_preview"])
    elif any(key in payload for key in ("content", "embeds")):
        candidate = dict(payload)
    elif isinstance(payload.get("body"), str) and payload["body"].strip():
        candidate = {"content": payload["body"].strip()}
    else:
        raise DiscordDispatchBlocked("payload_body_empty")

    forbidden = sorted(FORBIDDEN_REQUEST_FIELDS.intersection(candidate))
    if forbidden:
        raise DiscordDispatchBlocked("payload_forbidden_fields_" + "_".join(forbidden))

    content = candidate.get("content")
    embeds = candidate.get("embeds")
    has_content = isinstance(content, str) and bool(content.strip())
    has_embeds = isinstance(embeds, list) and len(embeds) > 0
    if not has_content and not has_embeds:
        raise DiscordDispatchBlocked("payload_body_empty")

    normalized: dict[str, Any] = {}
    for key in ("content", "embeds", "username", "avatar_url", "tts"):
        if key in candidate:
            normalized[key] = candidate[key]
    normalized["allowed_mentions"] = {"parse": []}
    return normalized


def make_dispatch_result(
    *,
    result_status: str,
    target_config: DiscordTargetConfig,
    payload_id: str | None,
    payload_hash: str | None,
    request_count_attempted: int,
    http_status_code: int | None,
    blocker: str | None = None,
) -> dict[str, Any]:
    status_class = status_code_class(http_status_code)
    result = {
        "dispatch_result_id": "discord_dispatch_" + uuid.uuid4().hex,
        "task_label": TASK_LABEL,
        "result_status": result_status,
        "platform": PLATFORM,
        "endpoint_family": ENDPOINT_FAMILY,
        "method": METHOD,
        "target_name": target_config.target_name,
        "destination_binding_id": target_config.destination_binding_id,
        "credential_handle_id": target_config.credential_handle_id,
        "env_key_name": target_config.env_key_name,
        "payload_id": payload_id,
        "payload_hash": payload_hash,
        "request_budget_max": REQUEST_BUDGET_MAX,
        "request_count_attempted": request_count_attempted,
        "retry_budget_max": RETRY_BUDGET_MAX,
        "retry_count_attempted": 0,
        "timeout_seconds": TIMEOUT_SECONDS,
        "http_status_code": http_status_code,
        "status_code_class": status_class,
        "diagnostic_interpretation": diagnostic_interpretation(http_status_code) if http_status_code is not None else "not_attempted",
        "live_write_completed": result_status == "PASS",
        "public_url": None,
        "webhook_message_id": None,
        "response_body_recorded": False,
        "response_headers_recorded": False,
        "raw_secret_output": False,
        "user_agent_set": True,
        "wait_query_param": WAIT_QUERY_PARAM,
        "webhook_url_printed": False,
    }
    if blocker is not None:
        result["blocker"] = blocker
    return result


class DiscordDispatchAdapter:
    def __init__(self, environ: Any | None = None, opener: Callable[..., Any] | None = None) -> None:
        self.environ = environ if environ is not None else getattr(__import__("os"), "environ")
        self.opener = opener
        self.guard = DispatchBudgetGuard()

    def target_config(self, target_name: str) -> DiscordTargetConfig:
        try:
            return TARGET_CONFIGS[target_name]
        except KeyError as exc:
            raise DiscordDispatchBlocked(f"unknown_target_{target_name}") from exc

    def validate_route(self, target_name: str, destination_binding_id: str, credential_handle_id: str) -> DiscordTargetConfig:
        config = self.target_config(target_name)
        if destination_binding_id != config.destination_binding_id:
            raise DiscordDispatchBlocked("destination_binding_mismatch")
        if credential_handle_id != config.credential_handle_id:
            raise DiscordDispatchBlocked("credential_handle_mismatch")
        return config

    def execute_post_once(self, raw_url: str, body: dict[str, Any]) -> tuple[int | None, str | None]:
        self.guard.spend_before_post()
        url_request = __import__("urllib.request", fromlist=["request"])
        url_error = __import__("urllib.error", fromlist=["error"])
        req = url_request.Request(
            with_wait_false(raw_url),
            data=json.dumps(body, separators=(",", ":")).encode("utf-8"),
            method=METHOD,
            headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        )
        opener = self.opener or url_request.urlopen
        try:
            response = opener(req, timeout=TIMEOUT_SECONDS)
            return int(getattr(response, "status", getattr(response, "code", 0))), None
        except url_error.HTTPError as exc:
            return int(exc.code), exc.__class__.__name__
        except Exception as exc:
            return None, exc.__class__.__name__

    def dispatch(
        self,
        payload: dict[str, Any],
        *,
        target_name: str,
        destination_binding_id: str,
        credential_handle_id: str,
        payload_hash: str | None = None,
        execute: bool = False,
    ) -> dict[str, Any]:
        payload_id = payload.get("payload_id") if isinstance(payload, dict) else None
        config = self.validate_route(target_name, destination_binding_id, credential_handle_id)
        body = normalize_payload_body(payload)
        if not execute:
            return make_dispatch_result(
                result_status="DRY_RUN",
                target_config=config,
                payload_id=payload_id,
                payload_hash=payload_hash,
                request_count_attempted=0,
                http_status_code=None,
            )
        raw_url = self.environ.get(config.env_key_name)
        if not raw_url:
            return make_dispatch_result(
                result_status="BLOCKED",
                target_config=config,
                payload_id=payload_id,
                payload_hash=payload_hash,
                request_count_attempted=0,
                http_status_code=None,
                blocker=f"env_key_missing_{config.env_key_name}",
            )
        validate_discord_webhook_url(raw_url)
        status_code, _error_class = self.execute_post_once(raw_url, body)
        return make_dispatch_result(
            result_status="PASS" if status_code_class(status_code) == "2xx" else "FAIL",
            target_config=config,
            payload_id=payload_id,
            payload_hash=payload_hash,
            request_count_attempted=self.guard.attempted_requests,
            http_status_code=status_code,
        )


def generate_dry_run_packet(payload_packet_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    packet = load_payload_packet(payload_packet_path)
    adapter = DiscordDispatchAdapter()
    results: list[dict[str, Any]] = []
    for target_name in ("announcements", "substack_drops", "product_updates"):
        payload = next((item for item in payloads_from_packet(packet) if item.get("target_name") == target_name), None)
        if payload is None:
            raise DiscordDispatchBlocked(f"payload_for_target_not_found_{target_name}")
        results.append(
            adapter.dispatch(
                payload,
                target_name=target_name,
                destination_binding_id=str(payload.get("destination_binding_id")),
                credential_handle_id=str(payload.get("credential_handle_id")),
                payload_hash=payload.get("payload_hash"),
                execute=False,
            )
        )
    out_packet = {
        "task_label": TASK_LABEL,
        "result_status": "PASS",
        "mode": "dry_run_generation",
        "platform": PLATFORM,
        "request_count_attempted": sum(item["request_count_attempted"] for item in results),
        "retry_count_attempted": sum(item["retry_count_attempted"] for item in results),
        "webhook_url_printed": False,
        "raw_secret_output": False,
        "dispatch_results": results,
        "summary": {
            "targets_planned": 3,
            "targets_generated": len(results),
            "dry_run_results": sum(1 for item in results if item["result_status"] == "DRY_RUN"),
        },
    }
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(out_packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out_packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Discord dispatch adapter dry-run generator")
    parser.add_argument("--payload-packet", required=True)
    parser.add_argument("--target", required=True, choices=sorted(TARGET_CONFIGS))
    parser.add_argument("--payload-id", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--execute", action="store_true", help="Future explicit live dispatch only; do not use in dry-run tasks.")
    args = parser.parse_args(argv)
    if args.execute:
        raise DiscordDispatchBlocked("execute_not_allowed_for_packet_generation_cli")
    source_packet = load_payload_packet(args.payload_packet)
    selected = select_payload(source_packet, args.payload_id)
    if selected.get("target_name") != args.target:
        raise DiscordDispatchBlocked("cli_target_payload_mismatch")
    out_packet = generate_dry_run_packet(args.payload_packet, args.output)
    print(json.dumps({
        "task_label": out_packet["task_label"],
        "result_status": out_packet["result_status"],
        "request_count_attempted": out_packet["request_count_attempted"],
        "retry_count_attempted": out_packet["retry_count_attempted"],
        "targets": [item["target_name"] for item in out_packet["dispatch_results"]],
        "webhook_url_printed": False,
        "raw_secret_output": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
