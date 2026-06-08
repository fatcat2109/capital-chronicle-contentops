"""Local-only deterministic review packet bundle manifest (v0).

Builds a safe, Project Sources-ready manifest listing which local docs/reports
are recommended for upload and which categories must be excluded, with a reason
and authority role for each. Prepares local manifest artifacts ONLY; it does NOT
upload anything.

Performs NO network, provider, LLM, search, or platform calls. Nothing in the
manifest is public-postable or grants publishing authority.
"""

from . import status

ACCEPTED_HEAD = "68b041c"

# Local-only accepted chain summary (advisory continuation context).
ACCEPTED_CHAIN_SUMMARY = [
    "0056 selected the local-only Option A editorial-quality lane.",
    "0057 created deterministic editorial QA scoring.",
    "0058 created deterministic editorial variant preview with no-public-post enforcement.",
    "0059 created manual editorial selection packets (auto-selection/approval disabled).",
    "0060 created GroundedResearchContext + SEO/hashtag metadata contracts.",
    "0061 created grounded LLM prompt packet injection + citation guardrail.",
    "0062 created local grounded editorial packet export.",
    "0063 created local packet audit + operator review queue.",
    "0064 created operator decision capture + review history.",
    "0065 created review history ledger + packet registry.",
    "0066 created packet registry query + operator dashboard summary.",
    "0067 created packet dashboard export + operator handoff.",
    "0068 created review packet bundle manifest + Project Sources export.",
]

HARD_BOUNDARIES = [
    "No network.",
    "No provider API.",
    "No LLM API.",
    "No search API.",
    "No credentials/env reads.",
    "No platform API.",
    "No vidIQ/TubeBuddy/Google Trends/YouTube/X/LinkedIn integration.",
    "No live posting.",
    "No scheduling implementation.",
    "No autonomous replies/DMs.",
    "No scraping/browser automation.",
    "No public-postable fake content.",
    "No auto-selection of final public copy.",
    "No auto-approval or real approval-to-post.",
    "No financial advice or buy/sell/hold/execution language.",
    "No claiming Capital Chronicle is Bloomberg replacement, AI trading bot, "
    "signal service, execution engine, or guaranteed forecasting system.",
    "No modifying cc-contentops or core Capital Chronicle repo.",
    "Do not touch operator-owned .gitignore.",
]

KNOWN_CAVEATS = [
    ".gitignore is modified in the working tree, unstaged, and outside task "
    "commit scope. Do not edit, stage, clean, revert, normalize, or commit it.",
]

PROJECT_SOURCES_CLEANUP_GUIDANCE = [
    "Remove older stale TASK_CONTENTOPS source bundles before uploading this one.",
    "This 0068 bundle supersedes older continuation/source bundles.",
    "Upload only the recommended docs listed in this manifest.",
    "Never upload .env, credentials, raw logs, provider outputs, or platform IDs.",
    "Never upload __pycache__ or compiled files.",
    "Keep uploads small and reviewable; do not upload large fixture dumps.",
]


# Categories of files that MUST be excluded from any upload bundle.
EXCLUDED_CATEGORIES = [
    {"category": "env_files", "reason": ".env/.env.* may contain secrets."},
    {"category": "credentials_tokens_secrets", "reason": "Credential/token/secret material."},
    {"category": "raw_logs", "reason": "Raw logs may leak internal/runtime detail."},
    {"category": "provider_outputs", "reason": "Provider/LLM outputs are not source-of-truth."},
    {"category": "platform_ids", "reason": "Live platform IDs must never be uploaded."},
    {"category": "private_memory_files",
     "reason": "Browser/brain/IDE private memory files are out of scope."},
    {"category": "pycache_compiled", "reason": "__pycache__/compiled files are noise."},
    {"category": "full_output_history", "reason": "Full output history is large and unsafe."},
    {"category": "large_fixture_dumps", "reason": "Large fixture dumps bloat the bundle."},
    {"category": "raw_vendor_data", "reason": "Raw vendor data is not safe to upload."},
    {"category": "public_postable_fake_content",
     "reason": "No public-postable fake content may be uploaded."},
    {"category": "sibling_or_core_repo_files",
     "reason": "cc-contentops/core repo files are out of scope."},
    {"category": "gitignore_operator_drift",
     "reason": "Operator-owned .gitignore drift must not be bundled."},
]


def _included_file(path, artifact_type, reason, authority_role, upload=True):
    return {
        "path": path,
        "artifact_type": artifact_type,
        "reason_for_inclusion": reason,
        "authority_role": authority_role,
        "safety_status": "SAFE_FOR_PROJECT_SOURCES",
        "contains_secrets": False,
        "contains_live_ids": False,
        "contains_raw_logs": False,
        "contains_provider_outputs": False,
        "contains_public_postable_content": False,
        "upload_recommended": upload,
    }


def build_manifest() -> dict:
    """Build a deterministic Project Sources upload manifest."""
    included = [
        _included_file(
            "docs/NEW_CHAT_CONTINUATION_AFTER_0068.md", "continuation_packet",
            "Current accepted state + next task brief for a fresh chat.",
            "ADVISORY_CONTINUATION_CONTEXT"),
        _included_file(
            "docs/UPLOAD_BUNDLE_MANIFEST_AFTER_0068.md", "upload_manifest",
            "Lists which files to upload/exclude and why.",
            "ADVISORY_UPLOAD_GUIDANCE"),
        _included_file(
            "docs/PROJECT_SOURCE_EXPORT_AFTER_0068.md", "project_source_export",
            "Project Sources cleanup guidance and bundle supersession note.",
            "ADVISORY_CLEANUP_GUIDANCE"),
        _included_file(
            "docs/TASK_CONTENTOPS_0068_LOCAL_REVIEW_PACKET_BUNDLE_MANIFEST_AND_"
            "PROJECT_SOURCE_EXPORT_V0.md", "completed_task_summary",
            "Completed-task summary for 0068.",
            "ADVISORY_TASK_RECORD"),
        _included_file(
            "docs/TASK_CONTENTOPS_0067_LOCAL_PACKET_DASHBOARD_EXPORT_AND_"
            "OPERATOR_HANDOFF_V0.md", "dashboard_handoff_report",
            "Prior dashboard/handoff report for review context.",
            "ADVISORY_TASK_RECORD"),
    ]
    return {
        "manifest_id": "review_bundle_manifest_after_0068",
        "generated_at": "DETERMINISTIC_TIMESTAMP",
        "accepted_head": ACCEPTED_HEAD,
        "next_task": status.get_status().get("next_task"),
        "accepted_chain_summary": list(ACCEPTED_CHAIN_SUMMARY),
        "hard_boundaries": list(HARD_BOUNDARIES),
        "known_caveats": list(KNOWN_CAVEATS),
        "project_sources_cleanup_guidance": list(PROJECT_SOURCES_CLEANUP_GUIDANCE),
        "included_files": included,
        "excluded_categories": list(EXCLUDED_CATEGORIES),
        "supersedes_older_source_bundles": True,
        "advisory_only": True,
        "local_only": True,
        "human_review_required": True,
        "approval_granted": False,
        "publish_ready": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
        "all_exports_safe_for_project_sources": True,
        "contains_secrets": False,
        "contains_live_ids": False,
        "contains_public_postable_content": False,
    }



# Path fragments that should never appear in a recommended upload.
_UNSAFE_PATH_FRAGMENTS = [
    ".env", "credential", "secret", "token", "/logs/", "\\logs\\",
    "provider_output", "platform_id", "__pycache__", ".pyc",
    "output_history", "cc-contentops", ".gitignore",
]


def validate_manifest(manifest: dict) -> dict:
    """Block/warn if the manifest would bundle anything unsafe."""
    warnings = []
    blockers = []

    if not manifest.get("accepted_head"):
        blockers.append("Manifest missing accepted_head.")
    if not manifest.get("next_task"):
        blockers.append("Manifest missing next_task pointer.")
    if not manifest.get("hard_boundaries"):
        blockers.append("Manifest missing hard_boundaries.")

    for f in manifest.get("included_files", []):
        if not f.get("upload_recommended"):
            continue
        path = str(f.get("path", "")).lower()
        for frag in _UNSAFE_PATH_FRAGMENTS:
            if frag.lower() in path:
                blockers.append(f"Recommended upload includes unsafe path fragment "
                                f"'{frag}': {f.get('path')}")
        if f.get("contains_secrets") or f.get("contains_live_ids") \
                or f.get("contains_raw_logs") or f.get("contains_provider_outputs"):
            blockers.append(f"Recommended upload flagged unsafe content: {f.get('path')}")
        if f.get("contains_public_postable_content"):
            blockers.append(f"Recommended upload includes public-postable content: "
                            f"{f.get('path')}")
        role = str(f.get("authority_role", ""))
        if "APPROVAL" in role.upper() or "PUBLISH" in role.upper() \
                or "PLATFORM" in role.upper():
            blockers.append(f"Included artifact claims publish/approval/platform "
                            f"authority: {f.get('path')}")

    if manifest.get("approval_granted") or manifest.get("publish_ready"):
        blockers.append("Manifest grants approval/publish authority.")
    if manifest.get("platform_action_allowed") or manifest.get("provider_call_allowed") \
            or manifest.get("search_call_allowed"):
        blockers.append("Manifest grants provider/search/platform authority.")
    if not manifest.get("all_exports_safe_for_project_sources"):
        blockers.append("Manifest does not affirm Project Sources safety.")

    # Required exclusion categories must be present.
    excluded = {c.get("category") for c in manifest.get("excluded_categories", [])}
    for required in ("env_files", "credentials_tokens_secrets", "raw_logs",
                     "provider_outputs", "platform_ids", "pycache_compiled",
                     "full_output_history", "gitignore_operator_drift",
                     "sibling_or_core_repo_files"):
        if required not in excluded:
            blockers.append(f"Manifest missing required exclusion category: {required}")

    status_str = "BLOCKED" if blockers else ("WARNING" if warnings else "PASS")
    return {"status": status_str, "warnings": warnings, "blockers": blockers}


def build_summary() -> dict:
    """Deterministic CLI summary describing the bundle/export posture."""
    manifest = build_manifest()
    return {
        "status": "deterministic local review bundle manifest and Project Sources export active",
        "local_only": True,
        "advisory_only": True,
        "project_source_export_enabled": True,
        "upload_manifest_enabled": True,
        "new_chat_continuation_enabled": True,
        "recommended_upload_count": sum(
            1 for f in manifest["included_files"] if f.get("upload_recommended")),
        "excluded_category_count": len(manifest["excluded_categories"]),
        "accepted_head": manifest["accepted_head"],
        "next_task": manifest["next_task"],
        "contains_secrets": False,
        "contains_live_ids": False,
        "contains_public_postable_content": False,
        "all_exports_safe_for_project_sources": True,
        "validation_rules_enabled": True,
    }

