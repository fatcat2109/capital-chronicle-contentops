"""Primary platform variant dry-run (LOCAL, NOT LIVE).

Converts accepted editorial brief fixtures into review-only payload previews for
X, Telegram, and Substack. No public-ready content, approval, or dispatch.
"""

import copy
import json
import os.path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import platform_payload_preview_contract as contract
from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174XH_XI_XJ_IDEA_TO_PRIMARY_PLATFORM_VARIANTS_DRY_RUN_V0"
MODEL = "PRIMARY_PLATFORM_VARIANT_DRY_RUN_0174XH_XI_XJ"
MODEL_VERSION = "0174XH_XI_XJ_PRIMARY_PLATFORM_VARIANT_DRY_RUN_V1"
SOURCE_BASELINE_COMMIT = "e77acd9f74b9ce2e65e569b6bf576e3896c1333e"
DOC_REL_DIR = os.path.join("docs", "automation", "0174XH_XI_XJ")
SOURCE_FIXTURE = os.path.join("docs", "automation", "0174XE_XF_XG", "editorial_brief_fixture_outputs.json")
RUN_PACKET = "primary_platform_variant_dry_run_packet.json"
RUN_DOC = "primary_platform_variant_dry_run.md"
FIXTURE_OUTPUTS = "platform_variant_fixture_outputs.json"
NEXT_PACKET = "next_approval_challenge_candidate_contract_packet.json"
NEXT_DOC = "next_approval_challenge_candidate_contract.md"
NEXT_BATCH_PROMPT = "TASK_CONTENTOPS_0174XK_XL_XM_APPROVAL_CHALLENGE_CANDIDATE_CONTRACT_V0"
NO_SIGNAL_DISCLAIMER = "Review-only context. No financial advice, trade signal, price target, or recommendation."
PRIMARY_PLATFORMS = ["x", "telegram", "substack"]
EXPANSION_PLACEHOLDERS = ["threads", "instagram", "facebook_page"]
LATER_PLACEHOLDERS = ["tiktok", "youtube"]


def _safe_slug(value):
    return str(value).replace(" ", "_").lower()


def load_briefs(repo_root="."):
    path = pathlib.Path(repo_root) / SOURCE_FIXTURE
    return json.loads(path.read_text(encoding="utf-8"))


def is_blocked_brief(brief):
    return bool(brief.get("blocked_reasons"))


def _base_payload(brief, platform, payload_class, suffix):
    return {
        "payload_id": f"payload_{_safe_slug(brief['brief_id'])}_{suffix}",
        "source_brief_id": brief["brief_id"],
        "source_intent_id": brief["source_intent_id"],
        "platform": platform,
        "payload_class": payload_class,
        "body": "",
        "title": "",
        "subtitle": "",
        "thread_parts": [],
        "source_notes": [
            f"source_requirement_status={brief.get('source_requirement_status', 'unknown')}",
            f"content_lane={brief.get('content_lane', 'unknown')}",
        ],
        "limitations": list(brief.get("required_limitations", [])) + ["review_only_preview", "not_public_ready"],
        "seo_metadata": {},
        "manual_export": {},
        "visibility_class": "review_only_payload_preview",
        "platform_constraints_status": "dry_run_constraints_applied",
        "platform_warnings": ["not_dispatch_ready", "human_review_required", "no_signal_language"],
        "evidence_refs": list(brief.get("evidence_refs", [])),
        "platform_formatting_metadata": {
            "primary_platform_only": True,
            "deterministic_fixture_preview": True,
            "expansion_placeholders_not_generated": EXPANSION_PLACEHOLDERS,
            "later_placeholders_not_generated": LATER_PLACEHOLDERS,
        },
    }


def _topic(brief):
    return brief.get("topic_summary") or "Editorial review topic"


def build_x_variants(brief):
    topic = _topic(brief)
    short = _base_payload(brief, "x", "x_short_post", "x_short")
    short["body"] = f"Review draft preview: {topic}. Context only; no market call, signal, or price target."
    short["platform_formatting_metadata"].update({"max_chars_preview": 280, "surface": "x_short_preview"})
    thread = _base_payload(brief, "x", "x_thread", "x_thread")
    thread["thread_parts"] = [
        f"Context frame: {topic}.",
        "Keep claims bounded to source notes and human review.",
        "No financial advice, signal framing, price target, or posting readiness.",
    ]
    thread["body"] = "\n\n".join(thread["thread_parts"])
    thread["platform_formatting_metadata"].update({"surface": "x_thread_preview", "thread_part_count": 3})
    return [contract.finalize_payload(short), contract.finalize_payload(thread)]


def build_telegram_variants(brief):
    topic = _topic(brief)
    channel = _base_payload(brief, "telegram", "telegram_channel_update", "channel_update")
    channel["body"] = f"Channel update preview: {topic}. Local review only. No financial advice or signal language."
    channel["platform_warnings"].append("telegram_dispatch_proven_frozen_no_send")
    channel["platform_formatting_metadata"].update({"surface": "telegram_channel_preview", "dispatch_status": "proven_frozen_no_send"})
    review = _base_payload(brief, "telegram", "telegram_operator_review_message", "operator_review")
    review["body"] = f"Operator review message preview: Please review topic '{topic}' before any future approval challenge."
    review["platform_warnings"].append("remote_operator_inbox_distinct_from_channel_dispatch")
    review["platform_formatting_metadata"].update({"surface": "telegram_operator_review", "remote_inbox_distinct": True})
    return [contract.finalize_payload(channel), contract.finalize_payload(review)]


def build_substack_variants(brief):
    topic = _topic(brief)
    newsletter = _base_payload(brief, "substack", "substack_newsletter_issue", "newsletter")
    newsletter["title"] = f"Review draft: {topic}"
    newsletter["subtitle"] = "Owned-media manual export candidate; not public-ready."
    markdown = "\n\n".join([
        f"# {newsletter['title']}",
        newsletter["subtitle"],
        f"## Context\n{topic}",
        "## Source Notes\n- Human source review required before any public use.",
        "## Limitations\n- Not public-ready.\n- No financial advice.\n- No signal language.",
        f"## Disclaimer\n{NO_SIGNAL_DISCLAIMER}",
    ])
    newsletter["body"] = markdown
    newsletter["source_notes"].append("manual_markdown_export_first")
    newsletter["limitations"].append("source_notes_required_before_publication")
    newsletter["seo_metadata"] = {"title": newsletter["title"], "description": newsletter["subtitle"], "robots": "noindex_review_only"}
    newsletter["manual_export"] = {"format": "markdown", "markdown_body": markdown, "no_signal_disclaimer": NO_SIGNAL_DISCLAIMER, "export_status": "ready_for_manual_review"}
    newsletter["platform_formatting_metadata"].update({"surface": "substack_newsletter_manual_export"})
    longform = _base_payload(brief, "substack", "substack_longform_post", "longform")
    longform["title"] = f"Longform review note: {topic}"
    longform["subtitle"] = "Manual longform draft structure for review only."
    longform["body"] = markdown.replace("# Review draft", "# Longform review note")
    longform["source_notes"] = list(newsletter["source_notes"])
    longform["limitations"] = list(newsletter["limitations"])
    longform["seo_metadata"] = {"title": longform["title"], "description": longform["subtitle"], "robots": "noindex_review_only"}
    longform["manual_export"] = {"format": "markdown", "markdown_body": longform["body"], "no_signal_disclaimer": NO_SIGNAL_DISCLAIMER, "export_status": "ready_for_manual_review"}
    longform["platform_formatting_metadata"].update({"surface": "substack_longform_manual_export"})
    return [contract.finalize_payload(newsletter), contract.finalize_payload(longform)]


def variants_for_brief(brief):
    if is_blocked_brief(brief):
        return []
    if not brief.get("human_review_required") or brief.get("can_dispatch") or brief.get("can_create_approval"):
        return []
    out = []
    platforms = brief.get("primary_brand_channel_fit", [])
    if "substack" in platforms and brief.get("content_lane") == "grounded_news_context":
        out.extend(build_substack_variants(brief))
    if "x" in platforms and "short_form_or_thread_preview_only" in brief.get("source_requirements", []):
        out.extend(build_x_variants(brief))
    if "telegram" in platforms and "telegram_channel_update_distinct_from_remote_inbox" in brief.get("source_requirements", []):
        out.extend(build_telegram_variants(brief))
    return out


def build_all_variants(briefs):
    variants = []
    blocked_proofs = {"direct_dispatch": [], "approval_candidate": [], "signal_advice": [], "future_artifact": []}
    for brief in briefs:
        reasons = set(brief.get("blocked_reasons", []))
        if any("direct_dispatch" in r for r in reasons):
            blocked_proofs["direct_dispatch"].append(brief)
        if any("approval" in r for r in reasons):
            blocked_proofs["approval_candidate"].append(brief)
        if any("signal" in r or "advice" in r for r in reasons):
            blocked_proofs["signal_advice"].append(brief)
        if any("future_artifact" in r for r in reasons):
            blocked_proofs["future_artifact"].append(brief)
        variants.extend(variants_for_brief(brief))
    return variants, blocked_proofs


def _brief_ids(items):
    return [item["brief_id"] for item in items]


def _payload_hash_determinism_proof(variants):
    first = variants[0]
    same_hash = contract.compute_payload_hash(first) == first["payload_hash"]
    changed = copy.deepcopy(first)
    changed["body"] = changed["body"] + " changed"
    body_changed = contract.compute_payload_hash(changed) != first["payload_hash"]
    changed = copy.deepcopy(first)
    changed["platform"] = "telegram" if first["platform"] != "telegram" else "x"
    platform_changed = contract.compute_payload_hash(changed) != first["payload_hash"]
    changed = copy.deepcopy(first)
    changed["payload_class"] = "telegram_operator_review_message"
    class_changed = contract.compute_payload_hash(changed) != first["payload_hash"]
    return {
        "same_payload_same_hash": same_hash,
        "body_change_changes_hash": body_changed,
        "platform_change_changes_hash": platform_changed,
        "class_change_changes_hash": class_changed,
    }


def build_run_packet(briefs, variants, blocked_proofs):
    payload_classes = sorted({item["payload_class"] for item in variants})
    platforms = sorted({item["platform"] for item in variants})
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **contract.safety_flags(),
        "platforms_generated": platforms,
        "payload_classes_generated": payload_classes,
        "primary_platforms": PRIMARY_PLATFORMS,
        "secondary_fit_metadata_only": ["linkedin"],
        "expansion_placeholders_not_generated": EXPANSION_PLACEHOLDERS,
        "later_placeholders_not_generated": LATER_PLACEHOLDERS,
        "payload_count": len(variants),
        "source_brief_count": len(briefs),
        "blocked_direct_dispatch_proof": _brief_ids(blocked_proofs["direct_dispatch"]),
        "blocked_approval_candidate_proof": _brief_ids(blocked_proofs["approval_candidate"]),
        "blocked_signal_advice_proof": _brief_ids(blocked_proofs["signal_advice"]),
        "blocked_future_artifact_proof": _brief_ids(blocked_proofs["future_artifact"]),
        "payload_hash_determinism_proof": _payload_hash_determinism_proof(variants),
        "all_approval_required": all(item["approval_required"] is True for item in variants),
        "all_dispatch_ready_false": all(item["dispatch_ready"] is False for item in variants),
        "all_public_postable_false": all(item["public_postable"] is False for item in variants),
        "all_human_review_required": all(item["human_review_required"] is True for item in variants),
        "all_no_financial_advice": all(item["no_financial_advice"] is True for item in variants),
        "all_no_signal_language": all(item["no_signal_language"] is True for item in variants),
        "telegram_dispatch_status": "proven_frozen_no_send",
        "status": "pass",
    }
    packet["platform_variant_fixture_outputs_checksum"] = adapter.compute_checksum(variants)
    packet["primary_variant_dry_run_checksum"] = adapter.compute_checksum(packet)
    return packet


def build_next_packet(run_packet):
    packet = {
        "task_label": "TASK_CONTENTOPS_0174XK_XL_XM_APPROVAL_CHALLENGE_CANDIDATE_CONTRACT_V0",
        "model": "NEXT_APPROVAL_CHALLENGE_CANDIDATE_CONTRACT_0174XH_XI_XJ",
        "model_version": "0174XH_XI_XJ_NEXT_APPROVAL_CHALLENGE_CANDIDATE_CONTRACT_V1",
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **contract.safety_flags(),
        "next_batch_prompt": NEXT_BATCH_PROMPT,
        "next_scope": "approval_challenge_candidate_contract_local_only",
        "allowed_inputs": ["review_only_payload_preview", "payload_hash", "source_brief_id", "human_review_gate"],
        "forbidden_outputs": ["approval", "dispatch", "public_post", "credential_access", "platform_api_call"],
        "primary_variant_dry_run_checksum": run_packet["primary_variant_dry_run_checksum"],
        "platform_variant_fixture_outputs_checksum": run_packet["platform_variant_fixture_outputs_checksum"],
    }
    packet["next_approval_challenge_candidate_checksum"] = adapter.compute_checksum(packet)
    return packet


def render_doc(title, packet):
    lines = [f"# {title}", ""]
    lines.append("> [!IMPORTANT]")
    lines.append("> Local dry-run only. No approval, dispatch, live post, API call, network, or credential/env read.")
    lines.append("")
    for key in sorted(packet):
        value = packet[key]
        if isinstance(value, (dict, list)):
            value = json.dumps(value, sort_keys=True)
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def _assert_safe_output(repo_root, output_dir):
    root = pathlib.Path(repo_root).resolve()
    out = pathlib.Path(output_dir).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    if out != allowed:
        raise ValueError("unsafe_output_path_refused")
    return out


def write_artifacts(repo_root=".", output_dir=None):
    output_dir = output_dir or (pathlib.Path(repo_root) / DOC_REL_DIR)
    out = _assert_safe_output(repo_root, output_dir)
    out.mkdir(parents=True, exist_ok=True)
    briefs = load_briefs(repo_root)
    variants, blocked_proofs = build_all_variants(briefs)
    run_packet = build_run_packet(briefs, variants, blocked_proofs)
    next_packet = build_next_packet(run_packet)
    (out / FIXTURE_OUTPUTS).write_text(adapter.serialize(variants), encoding="utf-8", newline="\n")
    (out / RUN_PACKET).write_text(adapter.serialize(run_packet), encoding="utf-8", newline="\n")
    (out / RUN_DOC).write_text(render_doc("Primary Platform Variant Dry-Run", run_packet), encoding="utf-8", newline="\n")
    (out / NEXT_PACKET).write_text(adapter.serialize(next_packet), encoding="utf-8", newline="\n")
    (out / NEXT_DOC).write_text(render_doc("Next Approval Challenge Candidate Contract", next_packet), encoding="utf-8", newline="\n")
    return copy.deepcopy({"variants": variants, "run_packet": run_packet, "next_packet": next_packet})


if __name__ == "__main__":
    result = write_artifacts(".")
    print("PRIMARY_VARIANT_DRY_RUN_CHECKSUM", result["run_packet"]["primary_variant_dry_run_checksum"])
    print("PLATFORM_VARIANT_FIXTURE_OUTPUTS_CHECKSUM", result["run_packet"]["platform_variant_fixture_outputs_checksum"])
    print("NEXT_APPROVAL_CHALLENGE_CANDIDATE_CHECKSUM", result["next_packet"]["next_approval_challenge_candidate_checksum"])
