"""Local-only read-only IDE/CLI document bundle summary (v0).

Docs-only orientation summary for future local IDE/CLI workers. Adds no runtime
pipeline capability. No network/provider/LLM/search/platform/credential access.
Preserves the terminal alpha wait-state.
"""

import os

_DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")

RECOMMENDED_DOCS = [
    "docs/IDE_CLI_DOCUMENT_BUNDLE_AFTER_0074.md",
    "docs/IDE_CLI_QUICKSTART_AFTER_0074.md",
    "docs/IDE_CLI_EVIDENCE_PACKET_TEMPLATE_AFTER_0074.md",
    "docs/IDE_CLI_ALLOWED_MAINTENANCE_TASKS_AFTER_0074.md",
    "docs/TASK_CONTENTOPS_0074_LOCAL_IDE_CLI_DOCUMENT_BUNDLE_FOR_ALPHA_WAIT_STATE_V0.md",
]


def build_summary() -> dict:
    """Deterministic read-only summary for the IDE/CLI document bundle."""
    return {
        "status": "deterministic local IDE/CLI document bundle active",
        "local_only": True,
        "advisory_only": True,
        "document_bundle_enabled": True,
        "runtime_capability_added": False,
        "wait_state_preserved": True,
        "recommended_doc_count": len(RECOMMENDED_DOCS),
        "contains_secrets": False,
        "contains_live_ids": False,
        "contains_public_postable_content": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
        "approval_granted": False,
        "publish_ready": False,
        "validation_rules_enabled": True,
    }


def validate_bundle() -> dict:
    """Block/warn if any recommended doc is missing or duplicated."""
    blockers = []
    seen = set()
    for path in RECOMMENDED_DOCS:
        if path in seen:
            blockers.append("duplicate recommended doc: %s" % path)
        seen.add(path)
        abs_path = os.path.join(_DOCS_DIR, os.path.basename(path))
        if not os.path.isfile(abs_path):
            blockers.append("recommended doc does not exist: %s" % path)
        if ".gitignore" in path:
            blockers.append("bundle includes .gitignore: %s" % path)
    return {"status": "BLOCKED" if blockers else "PASS", "blockers": blockers}
