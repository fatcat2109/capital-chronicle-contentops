"""Scoped Neo native request/readback adapter used only by the durable coordinator.

No login, browser storage access, selector guessing or publication is performed by preparing
requests. A supported native MCP executor can be supplied by the active Desktop operation;
absence is a definite pre-write block. This is not an alternate publication coordinator.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of, _private

SCHEMA = "contentops.neo_destination_handoff.v1"
IDENTITIES = {"substack": "capitalchronicle.substack.com", "x": "@Capitalnicle",
              "youtube": "@CapitalChronicleYouTube"}
ROOTS = {"substack": "https://capitalchronicle.substack.com/", "x": "https://x.com/Capitalnicle",
         "youtube": "https://www.youtube.com/@CapitalChronicleYouTube/posts"}


def _canonical(url):
    p = urlsplit(str(url or ""))
    return p.scheme == "https" and p.hostname == IDENTITIES["substack"] and p.path.startswith("/p/") and not p.query and not p.fragment


class NeoDestinationHandoff:
    """Coordinator-injected adapter. Every actual write requires exact authorization."""

    def __init__(self, *, native_executor=None):
        self.native_executor = native_executor

    def request(self, *, destination, action, intent, authorization_context=None,
                public_object_id=None, public_object_url=None):
        if destination not in IDENTITIES or action not in {"PUBLISH", "READBACK"}:
            raise ValueError("NEO_DESTINATION_ACTION_UNSUPPORTED")
        if _private(intent):
            raise ValueError("PRIVATE_NEO_INTENT_EXCLUDED")
        auth = dict(authorization_context or {})
        if action == "PUBLISH":
            if (auth.get("schema_version") != "contentops.canonical_machine_authorization.v1"
                    or auth.get("operating_mode") != "AUTONOMOUS_DEFAULT"
                    or auth.get("destination") != destination or not auth.get("dispatch_attempt_identity")
                    or auth.get("work_item_id") != intent.get("work_item_id")
                    or auth.get("payload_hash") != intent.get("destination_plan", {}).get("payload_hash")):
                raise ValueError("SOLE_COORDINATOR_AUTHORIZATION_REQUIRED")
            if destination != "substack" and not _canonical(intent.get("canonical_url")):
                raise ValueError("RECONCILED_SUBSTACK_URL_REQUIRED")
        value = {"schema_version": SCHEMA, "destination": destination, "action": action,
            "expected_identity": IDENTITIES[destination], "entry_url": ROOTS[destination],
            "intent_sha256": sha256_of(intent), "work_item_id": intent.get("work_item_id"),
            "package_identity": intent.get("package_identity"),
            "payload_hash": intent.get("destination_plan", {}).get("payload_hash"),
            "dispatch_attempt_identity": auth.get("dispatch_attempt_identity"),
            "canonical_url": intent.get("canonical_url"),
            "public_object_id": public_object_id, "public_object_url": public_object_url,
            "native_payload": intent.get("native_payload"), "payload": intent.get("payload"),
            "steps": ["name_session; list tabs, open a task-owned tab",
                "snapshot; verify current signed-in publishing identity exactly; login is an owner action",
                "bind exact approved payload/media and reconciled canonical URL; use snapshot refs only",
                "PUBLISH only under this sole-coordinator authorization; READBACK never submits or retries",
                "read back stable public object ID, exact public URL, identity and content; preserve ambiguity"],
            "forbidden": ["login", "reauthorize", "account_switch", "cookies", "storage", "blind_retry", "bulk_x_ingestion"]}
        value["request_sha256"] = sha256_of(value)
        return value

    def publish(self, *, destination, intent, authorization_context):
        request = self.request(destination=destination, action="PUBLISH", intent=intent,
                               authorization_context=authorization_context)
        if self.native_executor is None:
            return {"status": "FAILED_BEFORE_WRITE", "definite_no_write": True,
                    "reason_code": "NEO_NATIVE_EXECUTOR_NOT_BOUND", "request": request,
                    "public_write_performed": False}
        result = dict(self.native_executor(request))
        if (result.get("request_sha256") != request["request_sha256"]
                or result.get("observed_identity") != IDENTITIES[destination]):
            return {"status": "UNKNOWN_WRITE", "reason_code": "NEO_RETURN_BINDING_OR_IDENTITY_MISMATCH"}
        # Identity/readback ambiguity is left to the sole coordinator. Never retry here.
        return result

    def readback(self, *, destination, intent, public_object_id, public_object_url):
        request = self.request(destination=destination, action="READBACK", intent=intent,
            public_object_id=public_object_id, public_object_url=public_object_url)
        if self.native_executor is None:
            return {"status": "BLOCKED", "verified": False, "request": request,
                    "reason_code": "NEO_NATIVE_READBACK_EXECUTOR_NOT_BOUND"}
        result = dict(self.native_executor(request))
        verified = (result.get("request_sha256") == request["request_sha256"]
            and result.get("observed_identity") == IDENTITIES[destination]
            and result.get("public_object_id") == public_object_id
            and result.get("content_verified") is True)
        if destination == "substack":
            verified = verified and _canonical(result.get("public_object_url"))
        return {**result, "verified": verified, "status": "SUCCESS" if verified else "BLOCKED"}


def destination_setup_projection(*, env=None, now=None, linkedin_root=None):
    """Presence only, with non-secret expiry metadata. Never decrypt or probe tokens."""
    env = os.environ if env is None else env
    now = now or datetime.now(timezone.utc)
    keys = {
        "telegram": (("TELEGRAM_BOT_TOKEN",), ("TELEGRAM_TARGET_CHAT_ID", "TELEGRAM_CHANNEL_ID", "TELEGRAM_CHAT_ID")),
        "discord": (("DISCORD_ANNOUNCEMENTS_WEBHOOK_URL", "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK"),),
        "facebook_page": (("FACEBOOK_PAGE_ACCESS_TOKEN", "META_ACCESS_TOKEN"), ("FACEBOOK_PAGE_ID",)),
        "instagram_business": (("INSTAGRAM_ACCESS_TOKEN", "META_ACCESS_TOKEN"), ("INSTAGRAM_BUSINESS_ACCOUNT_ID",)),
        "threads": (("THREADS_USER_ACCESS_TOKEN",), ("THREADS_USER_ID",)),
        "linkedin": (("LINKEDIN_CLIENT_ID",), ("LINKEDIN_CLIENT_SECRET",)),
    }
    transports = {"telegram": "BOT_API", "discord": "WEBHOOK_API", "facebook_page": "META_GRAPH_API",
                  "instagram_business": "META_GRAPH_API", "threads": "THREADS_API", "linkedin": "OFFICIAL_MEMBER_API"}
    result = {}
    for destination, groups in keys.items():
        present = all(any(bool(env.get(k)) for k in group) for group in groups)
        result[destination] = {"chosen_transport": transports[destination], "configuration_present": present,
            "validity": "NOT_VERIFIED", "identity_state": "NOT_VERIFIED",
            "browser_login_needed": False,
            "owner_action": "Xác minh token và quyền bằng kiểm tra chỉ đọc khi cần dùng." if present else "Bổ sung cấu hình API cho đích này."}
    auth_root = Path(linkedin_root or r"A:\Capital Chronicle\Runtime\ContentOps\linkedin_official_member_api")
    try:
        metadata = json.loads((auth_root / "auth_metadata_v1.json").read_bytes())
        expiry = next((metadata[k] for k in ("expires_at_utc", "token_expires_at_utc", "access_token_expires_at_utc") if metadata.get(k)), None)
        if expiry and datetime.fromisoformat(expiry.replace("Z", "+00:00")) <= now:
            result["linkedin"].update(validity="EXPIRED", owner_action="Cấp lại quyền LinkedIn OAuth; đăng nhập tab đơn thuần không làm mới token.")
        result["linkedin"]["auth_expiry_at_utc"] = expiry
        result["linkedin"]["encrypted_auth_store_present"] = (auth_root / "linkedin_member_credentials.dpapi").is_file()
    except (OSError, ValueError, TypeError):
        result["linkedin"]["owner_action"] = "Kiểm tra/cấp lại LinkedIn OAuth qua luồng hiện có."
    for destination in IDENTITIES:
        result[destination] = {"chosen_transport": "BROWSEROS_NEO_MCP", "configuration_present": True,
            "validity": "NOT_VERIFIED", "identity_state": "NOT_VERIFIED", "browser_login_needed": True,
            "expected_identity": IDENTITIES[destination],
            "owner_action": "Xác minh phiên Neo đúng tài khoản; nếu thiếu, chủ tài khoản đăng nhập.",
            "integration_state": "PREPARED_NATIVE_REQUEST_READBACK_EXECUTOR_NOT_BOUND"}
    result["youtube"]["api_oauth_does_not_authorize_community"] = True
    return result
