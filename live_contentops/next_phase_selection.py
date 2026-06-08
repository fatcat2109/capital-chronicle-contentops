"""Local-only deterministic bundle refresh and next-phase selection (v0).

Refreshes the Project Sources continuation bundle after the 0068R accepted-head
repair and records a deterministic next-phase decision. Prepares local docs and
decision records ONLY; it uploads nothing.

Performs NO network, provider, LLM, search, or platform calls. Nothing here is
public-postable or grants publishing authority.
"""

from . import status
from . import review_bundle_manifest as rbm

# Head lineage (advisory continuation context).
BUNDLE_BASE_HEAD = "68b041c"          # pre-0068 base / previous completed head
TASK_0068_COMPLETED_HEAD = "cd72ee4"  # 0068 functional completion
REPAIR_ACCEPTED_HEAD = "77ecb27"      # 0068R repair; actual repo start for 0069

SELECTED_NEXT_TASK = (
    "TASK_CONTENTOPS_0070_LOCAL_REAL_ARTIFACT_INTAKE_CONTRACT_AND_READINESS_GATE_V0")

# Deterministic next-phase option evaluation.
NEXT_PHASE_OPTIONS = [
    {
        "option": "A",
        "title": "Continue local-only polish of dashboard/review/report UX.",
        "status": "ACCEPTABLE",
        "note": "Acceptable for polish, but must not become endless local-only busywork.",
        "local_only": True,
    },
    {
        "option": "B",
        "title": "Pause live-control-plane work until real alpha artifacts exist.",
        "status": "ACCEPTABLE_IF_SUFFICIENT",
        "note": "Acceptable only if the system is already sufficient and no bridge "
                "task is useful.",
        "local_only": True,
    },
    {
        "option": "C",
        "title": "Build local-only real-artifact intake contract with fixture-only "
                 "placeholders until alpha artifacts exist.",
        "status": "SELECTED",
        "note": "Preferred: stays local-only and prepares for real Capital Chronicle "
                "alpha artifacts without needing actual alpha content.",
        "local_only": True,
    },
    {
        "option": "D",
        "title": "Start live credential/search/provider/platform work.",
        "status": "BLOCKED",
        "note": "Out of scope. Live credential/search/provider/platform work is "
                "permanently blocked for this local-first sidecar.",
        "local_only": False,
    },
]

SELECTED_OPTION = "C"
BLOCKED_OPTIONS = ["D"]

# Local-only/fixture-only boundary for the selected 0070 task.
REAL_ARTIFACT_INTAKE_BOUNDARY = [
    "No dependency on real alpha artifacts yet.",
    "No live repo mutation outside cc-live-contentops.",
    "No current-state authority.",
    "No Capital Chronicle core repo modification.",
    "No claims of real market readiness.",
    "Creates intake schema/contracts/readiness gates only (fixture-only).",
]


# Refreshed 0069 recommended upload docs (minimal safe bundle).
_REFRESH_UPLOAD_DOCS = [
    ("docs/NEW_CHAT_CONTINUATION_AFTER_0069.md", "continuation_packet",
     "Current accepted state + next task brief for a fresh chat.",
     "ADVISORY_CONTINUATION_CONTEXT"),
    ("docs/UPLOAD_BUNDLE_MANIFEST_AFTER_0069.md", "upload_manifest",
     "Lists which files to upload/exclude and why.",
     "ADVISORY_UPLOAD_GUIDANCE"),
    ("docs/PROJECT_SOURCE_EXPORT_AFTER_0069.md", "project_source_export",
     "Project Sources cleanup guidance and bundle supersession note.",
     "ADVISORY_CLEANUP_GUIDANCE"),
    ("docs/TASK_CONTENTOPS_0069_LOCAL_BUNDLE_REFRESH_AND_NEXT_PHASE_SELECTION_V0.md",
     "completed_task_summary", "Completed-task summary for 0069.",
     "ADVISORY_TASK_RECORD"),
    ("docs/TASK_CONTENTOPS_0068_LOCAL_REVIEW_PACKET_BUNDLE_MANIFEST_AND_"
     "PROJECT_SOURCE_EXPORT_V0.md", "completed_task_summary",
     "Prior 0068 task summary for context.", "ADVISORY_TASK_RECORD"),
]


def _included_file(path, artifact_type, reason, authority_role):
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
        "upload_recommended": True,
    }


def build_next_phase_record() -> dict:
    """Deterministic next-phase decision record."""
    return {
        "decision_id": "next_phase_selection_after_0069",
        "options": list(NEXT_PHASE_OPTIONS),
        "selected_option": SELECTED_OPTION,
        "selected_next_task": SELECTED_NEXT_TASK,
        "blocked_options": list(BLOCKED_OPTIONS),
        "real_artifact_intake_boundary": list(REAL_ARTIFACT_INTAKE_BOUNDARY),
        "rationale": "Strong local editorial/review infrastructure exists; the next "
                     "useful layer is a local-only, fixture-only contract for future "
                     "approved real Capital Chronicle alpha artifacts, so the system "
                     "can distinguish synthetic/demo content from future real approved "
                     "artifacts without live APIs or actual posting.",
        "advisory_only": True,
        "local_only": True,
        "approval_granted": False,
        "publish_ready": False,
    }


def build_refresh_bundle() -> dict:
    """Deterministic refreshed 0069 Project Sources bundle."""
    included = [_included_file(*d) for d in _REFRESH_UPLOAD_DOCS]
    return {
        "bundle_id": "review_bundle_refresh_after_0069",
        "generated_at": "DETERMINISTIC_TIMESTAMP",
        "repo_path": "A:\\Capital Chronicle\\tools\\cc-live-contentops",
        "bundle_base_head": BUNDLE_BASE_HEAD,
        "task_0068_completed_head": TASK_0068_COMPLETED_HEAD,
        "repair_accepted_head": REPAIR_ACCEPTED_HEAD,
        "starting_head_for_0069": REPAIR_ACCEPTED_HEAD,
        "current_next_task": status.get_status().get("next_task"),
        "selected_next_task": SELECTED_NEXT_TASK,
        "next_phase_record": build_next_phase_record(),
        "included_files": included,
        "excluded_categories": list(rbm.EXCLUDED_CATEGORIES),
        "hard_boundaries": list(rbm.HARD_BOUNDARIES),
        "known_caveats": list(rbm.KNOWN_CAVEATS),
        "project_sources_cleanup_guidance": list(rbm.PROJECT_SOURCES_CLEANUP_GUIDANCE),
        "supersedes_older_source_bundles": True,
        "supersedes_0068_bundle": True,
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



_UNSAFE_PATH_FRAGMENTS = [
    ".env", "credential", "secret", "token", "/logs/", "\\logs\\",
    "provider_output", "platform_id", "__pycache__", ".pyc",
    "output_history", "cc-contentops", ".gitignore",
]


def validate_refresh_bundle(bundle: dict) -> dict:
    """Block/warn if the refreshed bundle weakens guardrail posture."""
    import os
    warnings = []
    blockers = []

    # Head semantics must be present and unambiguous.
    for field in ("bundle_base_head", "task_0068_completed_head",
                  "repair_accepted_head", "starting_head_for_0069"):
        if not bundle.get(field):
            blockers.append(f"Refreshed bundle missing head field: {field}")

    # Must not point future chats to a stale pre-repair head as the start.
    if bundle.get("starting_head_for_0069") != REPAIR_ACCEPTED_HEAD:
        blockers.append("Refreshed bundle does not start future chats from repair head.")
    if bundle.get("starting_head_for_0069") in (BUNDLE_BASE_HEAD, TASK_0068_COMPLETED_HEAD):
        blockers.append("Refreshed bundle points future chats to a stale pre-repair head.")

    if not bundle.get("selected_next_task"):
        blockers.append("Refreshed bundle missing selected next task.")
    if not bundle.get("hard_boundaries"):
        blockers.append("Refreshed bundle missing local-only hard boundaries.")
    if not bundle.get("supersedes_0068_bundle"):
        blockers.append("Refreshed bundle does not supersede 0068 bundle.")

    # Next-phase selection rules.
    record = bundle.get("next_phase_record", {})
    if record.get("selected_option") == "D" or "D" not in record.get("blocked_options", []):
        blockers.append("Option D (live work) must remain blocked.")
    # Real-artifact intake must be fixture-only, not require real alpha artifacts now.
    boundary = " ".join(record.get("real_artifact_intake_boundary", []))
    if "No dependency on real alpha artifacts yet" not in boundary:
        blockers.append("Real-artifact intake described as requiring real alpha artifacts now.")

    repo_root = os.path.join(os.path.dirname(__file__), "..")
    seen = set()
    for f in bundle.get("included_files", []):
        if not f.get("upload_recommended"):
            continue
        path = str(f.get("path", ""))
        low = path.lower()
        for frag in _UNSAFE_PATH_FRAGMENTS:
            if frag.lower() in low:
                blockers.append(f"Recommended upload includes unsafe path fragment "
                                f"'{frag}': {path}")
        if path in seen:
            blockers.append(f"Duplicate stale doc in recommended upload set: {path}")
        seen.add(path)
        if f.get("contains_secrets") or f.get("contains_live_ids") \
                or f.get("contains_public_postable_content"):
            blockers.append(f"Recommended upload flagged unsafe content: {path}")
        if not os.path.isfile(os.path.join(repo_root, path)):
            warnings.append(f"Recommended upload path not found yet: {path}")

    if bundle.get("approval_granted") or bundle.get("publish_ready"):
        blockers.append("Refreshed bundle grants approval/publish authority.")
    if bundle.get("platform_action_allowed") or bundle.get("provider_call_allowed") \
            or bundle.get("search_call_allowed"):
        blockers.append("Refreshed bundle grants provider/search/platform authority.")

    status_str = "BLOCKED" if blockers else ("WARNING" if warnings else "PASS")
    return {"status": status_str, "warnings": warnings, "blockers": blockers}


def build_summary() -> dict:
    """Deterministic CLI summary for the bundle refresh / next-phase selection."""
    bundle = build_refresh_bundle()
    return {
        "status": "deterministic local bundle refresh and next-phase selection active",
        "local_only": True,
        "advisory_only": True,
        "bundle_refresh_enabled": True,
        "next_phase_selection_enabled": True,
        "previous_bundle_superseded": True,
        "starting_head_for_0069": REPAIR_ACCEPTED_HEAD,
        "selected_next_task": SELECTED_NEXT_TASK,
        "selected_option": SELECTED_OPTION,
        "blocked_options": list(BLOCKED_OPTIONS),
        "recommended_upload_count": sum(
            1 for f in bundle["included_files"] if f.get("upload_recommended")),
        "excluded_category_count": len(bundle["excluded_categories"]),
        "contains_secrets": False,
        "contains_live_ids": False,
        "contains_public_postable_content": False,
        "all_exports_safe_for_project_sources": True,
        "validation_rules_enabled": True,
    }

