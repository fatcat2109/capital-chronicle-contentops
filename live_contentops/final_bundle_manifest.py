"""Local-only deterministic final Project Sources bundle manifest after 0073 (v0).

Lists the exact recommended upload docs and exclusion categories. References
only exact existing committed paths. Does not upload anything. Supersedes the
0072 and 0069 bundles and older continuation/source bundles.
"""

import os

_DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")

# Recommended upload docs (exact underscore-convention paths, after 0073).
RECOMMENDED_UPLOAD_PATHS = [
    "docs/NEW_CHAT_CONTINUATION_AFTER_0073.md",
    "docs/UPLOAD_BUNDLE_MANIFEST_AFTER_0073.md",
    "docs/PROJECT_SOURCE_EXPORT_AFTER_0073.md",
    "docs/CURRENT_STATE_SUMMARY_AFTER_0073.md",
    "docs/ALPHA_WAIT_STATE_OPERATOR_RUNBOOK_AFTER_0073.md",
    "docs/TASK_CONTENTOPS_0073_EXTREME_LOCAL_ALPHA_WAIT_STATE_OPERATOR_RUNBOOK_FINAL_BUNDLE_AND_PATH_REPAIR_V0.md",
]

EXCLUDED_CATEGORIES = [
    "env_files (.env / .env.*)",
    "credentials_tokens_secrets",
    "raw_logs",
    "provider_outputs",
    "platform_ids",
    "private_memory_files (browser/brain/IDE)",
    "pycache_compiled (__pycache__ / .pyc)",
    "full_output_history",
    "large_fixture_dumps",
    "raw_vendor_data",
    "public_postable_fake_content",
    "sibling_or_core_repo_files (cc-contentops / core repo)",
    "gitignore_operator_drift (operator-owned .gitignore)",
    "stale_0069_0072_bundle_variants_not_in_recommended_list",
]


def _upload_entry(path: str) -> dict:
    return {
        "path": path,
        "reason_for_inclusion": "Safe advisory continuation/runbook context for "
                                "a future ChatGPT session.",
        "authority_role": "ADVISORY_CONTEXT_ONLY",
        "contains_secrets": False,
        "contains_live_ids": False,
        "contains_raw_logs": False,
        "contains_provider_outputs": False,
        "contains_public_postable_content": False,
        "safety_status": "SAFE_FOR_PROJECT_SOURCES",
    }


def build_manifest() -> dict:
    """Deterministic final bundle manifest."""
    return {
        "manifest_id": "final_bundle_manifest_after_0073",
        "supersedes": ["0072 bundle", "0069 bundle", "older source bundles"],
        "recommended_uploads": [_upload_entry(p) for p in RECOMMENDED_UPLOAD_PATHS],
        "excluded_categories": list(EXCLUDED_CATEGORIES),
        "local_only": True,
        "advisory_only": True,
        "all_exports_safe_for_project_sources": True,
        "approval_granted": False,
        "publish_ready": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
    }


def validate_manifest() -> dict:
    """Block/warn if the manifest weakens guardrail posture or is inconsistent."""
    blockers = []
    seen = set()
    for path in RECOMMENDED_UPLOAD_PATHS:
        if path in seen:
            blockers.append("duplicate recommended upload path: %s" % path)
        seen.add(path)
        abs_path = os.path.join(_DOCS_DIR, os.path.basename(path))
        if not os.path.isfile(abs_path):
            abs_path = os.path.join(_DOCS_DIR, "archive", "stale_prelaunch_reset_0174CG", os.path.basename(path))
        if not os.path.isfile(abs_path):
            blockers.append("recommended upload path does not exist: %s" % path)
        if ".gitignore" in path:
            blockers.append("bundle includes .gitignore: %s" % path)
        low = path.lower()
        for bad in (".env", "credential", "secret", "token", "__pycache__"):
            if bad in low:
                blockers.append("recommended upload looks unsafe (%s): %s" % (bad, path))
    status = "BLOCKED" if blockers else "PASS"
    return {"status": status, "blockers": blockers, "warnings": []}
