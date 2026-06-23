"""Symbolic endpoint-family contracts for future ContentOps live gates.

Pure value contracts only. No env reads, network calls, credential hydration, or live writes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_LIVE_GATE_STATE_MACHINE_AND_ERROR_CLASSIFIER_CORE_V0"
MODEL = "contentops.live_gate_endpoint_contract"
MODEL_VERSION = "0175_LIVE_GATE_ENDPOINT_CONTRACT_V0"


@dataclass(frozen=True)
class LiveGateEndpointContractRow:
    platform_id: str
    endpoint_family: str
    host_family_symbolic: str
    method_symbolic: str
    endpoint_path_family_symbolic: str
    request_budget_max: int = 1
    auto_retry_allowed: bool = False
    read_only_probe_allowed_in_this_task: bool = False
    live_write_allowed_in_this_task: bool = False
    official_docs_required_before_live: bool = True
    credential_hydration_allowed_in_this_task: bool = False
    raw_request_persisted: bool = False
    raw_response_persisted: bool = False
    token_logged: bool = False
    headers_logged: bool = False
    manual_fallback_required: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


ENDPOINT_ROWS: tuple[LiveGateEndpointContractRow, ...] = (
    LiveGateEndpointContractRow("telegram_remote_operator_inbox", "telegram_getMe_readonly_future", "telegram_bot_api_symbolic", "GET_SYMBOLIC", "getMe_symbolic"),
    LiveGateEndpointContractRow("telegram_channel_destination", "telegram_getChat_readonly_future", "telegram_bot_api_symbolic", "GET_SYMBOLIC", "getChat_symbolic"),
    LiveGateEndpointContractRow("telegram_channel_destination", "telegram_sendMessage_supervised_future", "telegram_bot_api_symbolic", "POST_SYMBOLIC", "sendMessage_symbolic"),
    LiveGateEndpointContractRow("x_profile", "x_user_lookup_readonly_future", "x_api_symbolic", "GET_SYMBOLIC", "users_lookup_symbolic"),
    LiveGateEndpointContractRow("x_profile", "x_create_post_supervised_future", "x_api_symbolic", "POST_SYMBOLIC", "tweets_create_symbolic"),
    LiveGateEndpointContractRow("linkedin_member_profile", "linkedin_member_lookup_readonly_future", "linkedin_api_symbolic", "GET_SYMBOLIC", "member_lookup_symbolic"),
    LiveGateEndpointContractRow("linkedin_member_profile", "linkedin_member_post_supervised_future", "linkedin_api_symbolic", "POST_SYMBOLIC", "member_post_symbolic"),
    LiveGateEndpointContractRow("linkedin_organization_page", "linkedin_org_lookup_readonly_future", "linkedin_api_symbolic", "GET_SYMBOLIC", "organization_lookup_symbolic"),
    LiveGateEndpointContractRow("linkedin_organization_page", "linkedin_org_post_supervised_future", "linkedin_api_symbolic", "POST_SYMBOLIC", "organization_post_symbolic"),
    LiveGateEndpointContractRow("threads_profile", "meta_identity_readonly_future", "meta_graph_symbolic", "GET_SYMBOLIC", "identity_symbolic"),
    LiveGateEndpointContractRow("threads_profile", "threads_publish_supervised_future", "threads_api_symbolic", "POST_SYMBOLIC", "threads_publish_symbolic"),
    LiveGateEndpointContractRow("instagram_professional_account", "instagram_media_container_supervised_future", "instagram_graph_symbolic", "POST_SYMBOLIC", "media_container_symbolic"),
    LiveGateEndpointContractRow("facebook_page", "facebook_page_post_supervised_future", "facebook_graph_symbolic", "POST_SYMBOLIC", "page_feed_symbolic"),
    LiveGateEndpointContractRow("tiktok_account", "tiktok_creator_info_readonly_future", "tiktok_api_symbolic", "GET_SYMBOLIC", "creator_info_symbolic"),
    LiveGateEndpointContractRow("tiktok_account", "tiktok_video_publish_supervised_future", "tiktok_api_symbolic", "POST_SYMBOLIC", "video_publish_symbolic"),
    LiveGateEndpointContractRow("youtube_channel", "youtube_channel_lookup_readonly_future", "youtube_data_api_symbolic", "GET_SYMBOLIC", "channel_lookup_symbolic"),
    LiveGateEndpointContractRow("youtube_channel", "youtube_video_insert_supervised_future", "youtube_data_api_symbolic", "POST_SYMBOLIC", "video_insert_symbolic"),
    LiveGateEndpointContractRow("substack_newsletter", "substack_manual_export_no_api", "no_api_manual_export_symbolic", "MANUAL_EXPORT_SYMBOLIC", "no_api_manual_export_symbolic", official_docs_required_before_live=True),
)


class EndpointContractError(ValueError):
    """Raised when endpoint contract fails closed."""


def build_live_gate_endpoint_contracts() -> tuple[LiveGateEndpointContractRow, ...]:
    rows = ENDPOINT_ROWS
    for row in rows:
        validate_endpoint_contract(row)
    return rows


def endpoint_contracts_by_platform_id() -> dict[str, tuple[LiveGateEndpointContractRow, ...]]:
    grouped: dict[str, list[LiveGateEndpointContractRow]] = {}
    for row in build_live_gate_endpoint_contracts():
        grouped.setdefault(row.platform_id, []).append(row)
    return {key: tuple(value) for key, value in grouped.items()}


def validate_endpoint_contract(row: LiveGateEndpointContractRow | dict[str, Any]) -> LiveGateEndpointContractRow:
    contract = row if isinstance(row, LiveGateEndpointContractRow) else LiveGateEndpointContractRow(**row)
    if contract.request_budget_max != 1:
        raise EndpointContractError("request_budget_max_must_equal_1")
    forbidden_true_flags = (
        "auto_retry_allowed",
        "read_only_probe_allowed_in_this_task",
        "live_write_allowed_in_this_task",
        "credential_hydration_allowed_in_this_task",
        "raw_request_persisted",
        "raw_response_persisted",
        "token_logged",
        "headers_logged",
    )
    for field in forbidden_true_flags:
        if getattr(contract, field) is not False:
            raise EndpointContractError(f"{field}_must_be_false")
    if contract.manual_fallback_required is not True:
        raise EndpointContractError("manual_fallback_required_must_be_true")
    if "http" in contract.host_family_symbolic.lower() or "://" in contract.host_family_symbolic:
        raise EndpointContractError("host_family_must_be_symbolic_not_url")
    if "http" in contract.endpoint_path_family_symbolic.lower() or "://" in contract.endpoint_path_family_symbolic:
        raise EndpointContractError("endpoint_path_must_be_symbolic_not_url")
    return contract


def live_gate_endpoint_contract_packet() -> dict[str, Any]:
    rows = [row.as_dict() for row in build_live_gate_endpoint_contracts()]
    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "endpoint_family_count": len(rows),
        "platform_ids": sorted(endpoint_contracts_by_platform_id()),
        "endpoint_families": [row["endpoint_family"] for row in rows],
        "request_budget_max_all_1": all(row["request_budget_max"] == 1 for row in rows),
        "auto_retry_allowed_any": any(row["auto_retry_allowed"] for row in rows),
        "read_only_probe_allowed_in_this_task_any": any(row["read_only_probe_allowed_in_this_task"] for row in rows),
        "live_write_allowed_in_this_task_any": any(row["live_write_allowed_in_this_task"] for row in rows),
        "credential_hydration_allowed_in_this_task_any": any(row["credential_hydration_allowed_in_this_task"] for row in rows),
        "raw_response_persisted_any": any(row["raw_response_persisted"] for row in rows),
        "token_logged_any": any(row["token_logged"] for row in rows),
        "headers_logged_any": any(row["headers_logged"] for row in rows),
        "substack_manual_export_no_api": any(row["endpoint_family"] == "substack_manual_export_no_api" for row in rows),
        "rows": rows,
    }
