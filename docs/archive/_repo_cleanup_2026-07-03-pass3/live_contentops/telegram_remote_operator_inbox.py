"""Telegram remote operator inbox dry-run (LOCAL, NOT LIVE).

Captures Telegram-origin fixture messages as untrusted inbound operator input.
No Telegram API, network, env, scheduler, posting, attachments, media, or voice.
"""

import copy
import json
import os.path
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174XB_XC_XD_REMOTE_OPERATOR_INBOX_INTENT_INGRESS_DRY_RUN_BATCH_V0"
MODEL = "TELEGRAM_REMOTE_OPERATOR_INBOX_0174XB_XC_XD"
MODEL_VERSION = "0174XB_XC_XD_TELEGRAM_REMOTE_OPERATOR_INBOX_V1"
SOURCE_BASELINE_COMMIT = "24450e8128244c0fb02e2948e78f32c0ffc9e86a"
DOC_REL_DIR = os.path.join("docs", "automation", "0174XB_XC_XD")
PACKET_FILENAME = "telegram_remote_operator_inbox_packet.json"
DOC_FILENAME = "telegram_remote_operator_inbox.md"
FIXTURE_FILENAME = "remote_inbox_fixture_messages.json"
SUPPORTED_MESSAGE_CLASSES = [
    "idea_message", "revision_instruction", "approval_response", "rejection_response",
    "hold_response", "status_query", "source_note", "manual_metric_note", "unknown",
]
ALLOWED_USE = ["intent_parsing", "idea_capture", "review_response_candidate"]
FORBIDDEN_USE = ["direct_dispatch", "credential_access", "approval_without_challenge", "live_send", "platform_api_call"]
VERIFIED_SENDER_BINDING = "operator_binding_jim_verified_symbolic"
VERIFIED_CHAT_BINDING = "telegram_remote_inbox_chat_binding_symbolic"


def safety_flags():
    return {
        "is_local_only": True,
        "network_performed": False,
        "telegram_api_called": False,
        "platform_api_called": False,
        "provider_api_called": False,
        "llm_provider_api_called": False,
        "credential_read": False,
        "env_read": False,
        "dotenv_read": False,
        "scheduler_enabled": False,
        "live_post_performed": False,
        "autonomous_replies_or_dms": False,
        "scraping_performed": False,
        "public_ready_content_generated": False,
        "approval_ledger_mutated": False,
        "dispatch_outbox_mutated": False,
        "attachments_ingested": False,
        "voice_notes_ingested": False,
        "media_ingested": False,
    }


def default_fixture_messages():
    return [
        {"message_id": "msg_001", "sender_binding_id": VERIFIED_SENDER_BINDING, "chat_binding_id": VERIFIED_CHAT_BINDING, "raw_text": "Idea: write a Substack issue about why one CPI print is not enough to call a macro regime shift", "received_at_order": 1},
        {"message_id": "msg_002", "sender_binding_id": VERIFIED_SENDER_BINDING, "chat_binding_id": VERIFIED_CHAT_BINDING, "raw_text": "Make the X hook calmer", "received_at_order": 2},
        {"message_id": "msg_003", "sender_binding_id": VERIFIED_SENDER_BINDING, "chat_binding_id": VERIFIED_CHAT_BINDING, "raw_text": "Approve LinkedIn version", "received_at_order": 3},
        {"message_id": "msg_004", "sender_binding_id": VERIFIED_SENDER_BINDING, "chat_binding_id": VERIFIED_CHAT_BINDING, "raw_text": "Reject the Telegram channel update", "received_at_order": 4},
        {"message_id": "msg_005", "sender_binding_id": VERIFIED_SENDER_BINDING, "chat_binding_id": VERIFIED_CHAT_BINDING, "raw_text": "Hold the Substack draft until sources are checked", "received_at_order": 5},
        {"message_id": "msg_006", "sender_binding_id": VERIFIED_SENDER_BINDING, "chat_binding_id": VERIFIED_CHAT_BINDING, "raw_text": "What is current status?", "received_at_order": 6},
        {"message_id": "msg_007", "sender_binding_id": VERIFIED_SENDER_BINDING, "chat_binding_id": VERIFIED_CHAT_BINDING, "raw_text": "Source note: BLS CPI release explains shelter weighting", "received_at_order": 7},
        {"message_id": "msg_008", "sender_binding_id": VERIFIED_SENDER_BINDING, "chat_binding_id": VERIFIED_CHAT_BINDING, "raw_text": "Metric note: X post got 5 bookmarks", "received_at_order": 8},
        {"message_id": "msg_009", "sender_binding_id": "unknown_sender", "chat_binding_id": "unknown_chat", "raw_text": "Unknown inbound note", "received_at_order": 9},
        {"message_id": "msg_010", "sender_binding_id": VERIFIED_SENDER_BINDING, "chat_binding_id": VERIFIED_CHAT_BINDING, "raw_text": "Token abc123SECRETtoken and https://example.com/path and chat_id 123456789", "received_at_order": 10},
        {"message_id": "msg_011", "sender_binding_id": VERIFIED_SENDER_BINDING, "chat_binding_id": VERIFIED_CHAT_BINDING, "raw_text": "Post this now", "received_at_order": 11},
        {"message_id": "msg_012", "sender_binding_id": VERIFIED_SENDER_BINDING, "chat_binding_id": VERIFIED_CHAT_BINDING, "raw_text": "Buy this breakout, long it, target 420, watch this level", "received_at_order": 12},
        {"message_id": "msg_013", "sender_binding_id": VERIFIED_SENDER_BINDING, "chat_binding_id": VERIFIED_CHAT_BINDING, "raw_text": "Preview the X thread before publication", "received_at_order": 13},
        {"message_id": "msg_014", "sender_binding_id": VERIFIED_SENDER_BINDING, "chat_binding_id": VERIFIED_CHAT_BINDING, "raw_text": "Send source links for the Substack issue", "received_at_order": 14},
        {"message_id": "msg_015", "sender_binding_id": VERIFIED_SENDER_BINDING, "chat_binding_id": VERIFIED_CHAT_BINDING, "raw_text": "", "received_at_order": -1},
    ]


def redact_text(text):
    redacted = re.sub(r"https?://\S+", "[REDACTED_URL]", text or "")
    redacted = re.sub(r"(?i)(token|secret|bot)[A-Za-z0-9_:-]*", "[REDACTED_TOKEN_LIKE]", redacted)
    redacted = re.sub(r"(?i)chat[_ -]?id\s*[:=]?\s*\d+", "[REDACTED_CHAT_LIKE]", redacted)
    redacted = re.sub(r"\b\d{8,}\b", "[REDACTED_NUMERIC_ID]", redacted)
    return redacted.strip()


def classify_message(text):
    lowered = (text or "").lower()
    if lowered.startswith("idea:"):
        return "idea_message"
    if lowered.startswith("make ") or "revise" in lowered or "calmer" in lowered:
        return "revision_instruction"
    if lowered.startswith("approve"):
        return "approval_response"
    if lowered.startswith("reject"):
        return "rejection_response"
    if lowered.startswith("hold"):
        return "hold_response"
    if "status" in lowered and "?" in lowered:
        return "status_query"
    if lowered.startswith("source note") or "source links" in lowered:
        return "source_note"
    if lowered.startswith("metric note"):
        return "manual_metric_note"
    return "unknown"


def build_inbound_packets(messages=None, stale_order_before=0):
    messages = messages or default_fixture_messages()
    seen = set()
    packets = []
    for item in messages:
        redacted = redact_text(item.get("raw_text", ""))
        msg_hash = adapter.compute_checksum({"transport": "telegram", "text": redacted})
        verified = item.get("sender_binding_id") == VERIFIED_SENDER_BINDING and item.get("chat_binding_id") == VERIFIED_CHAT_BINDING
        replay_status = "stale" if item.get("received_at_order", 0) <= stale_order_before else "duplicate" if msg_hash in seen else "fresh"
        seen.add(msg_hash)
        packets.append({
            "message_id": item["message_id"],
            "transport": "telegram",
            "sender_class": "verified_operator" if verified else "blocked",
            "sender_binding_id": item.get("sender_binding_id"),
            "chat_binding_id": item.get("chat_binding_id"),
            "raw_text_redacted": redacted,
            "transport_message_hash": msg_hash,
            "replay_status": replay_status,
            "trust_status": "untrusted_input",
            "message_class": classify_message(item.get("raw_text", "")) if verified else "unknown",
            "allowed_use": ALLOWED_USE,
            "forbidden_use": FORBIDDEN_USE,
            **safety_flags(),
        })
    return packets


def build_inbox_packet(messages=None):
    inbound = build_inbound_packets(messages)
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **safety_flags(),
        "telegram_surface": "remote_operator_inbox",
        "telegram_channel_dispatch_surface_status": "proven_frozen_distinct_surface",
        "supported_message_classes": SUPPORTED_MESSAGE_CLASSES,
        "inbound_messages": inbound,
        "unknown_sender_blocked": any(m["sender_class"] == "blocked" for m in inbound),
        "all_messages_untrusted_input": all(m["trust_status"] == "untrusted_input" for m in inbound),
        "no_attachments_voice_or_media": True,
        "status": "pass",
    }
    packet["fixture_messages_checksum"] = adapter.compute_checksum(default_fixture_messages())
    packet["inbox_packet_checksum"] = adapter.compute_checksum(packet)
    return packet


def _assert_safe_output(repo_root, output_dir):
    root = pathlib.Path(repo_root).resolve()
    out = pathlib.Path(output_dir).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    if out != allowed:
        raise ValueError("unsafe_output_path_refused")
    return out


def render_doc(packet):
    lines = ["# Telegram Remote Operator Inbox", ""]
    for key in sorted(packet):
        value = packet[key]
        if isinstance(value, (dict, list)):
            value = json.dumps(value, sort_keys=True)
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def write_artifacts(repo_root=".", output_dir=None):
    output_dir = output_dir or (pathlib.Path(repo_root) / DOC_REL_DIR)
    out = _assert_safe_output(repo_root, output_dir)
    out.mkdir(parents=True, exist_ok=True)
    packet = build_inbox_packet()
    (out / PACKET_FILENAME).write_text(adapter.serialize(packet), encoding="utf-8", newline="\n")
    (out / DOC_FILENAME).write_text(render_doc(packet), encoding="utf-8", newline="\n")
    (out / FIXTURE_FILENAME).write_text(adapter.serialize(default_fixture_messages()), encoding="utf-8", newline="\n")
    return copy.deepcopy(packet)


if __name__ == "__main__":
    result = write_artifacts(".")
    print("INBOX_PACKET_CHECKSUM", result["inbox_packet_checksum"])
    print("FIXTURE_MESSAGES_CHECKSUM", result["fixture_messages_checksum"])
    print("SUPPORTED_MESSAGE_CLASSES", ",".join(result["supported_message_classes"]))
