"""Pure continuation decisions for native command results, not a second runtime.

The native conversation executes the returned supported action in its own run. This
module starts no model, task, watcher, scheduler, provider or publication operation.
"""
from __future__ import annotations

import json
from typing import Any, Mapping


def consume_advance_result(command: Mapping[str, Any]) -> dict[str, Any]:
    """Consume the actual exec result instead of treating empty initial stdout as final."""
    if command.get("session_id") is not None:
        return {"action": "COLLECT_EXACT_COMMAND_HANDLE", "session_id": command["session_id"],
                "repeat_advance": False, "terminal": False}
    if command.get("exit_code") != 0:
        return {"action": "REPAIR_COMMAND_ERROR", "exit_code": command.get("exit_code"),
                "terminal": False, "repeat_advance": False}
    output = command.get("output", "")
    if not isinstance(output, str):
        raise ValueError("ADVANCE_STDOUT_REQUIRED")
    try:
        result = json.loads(output)
    except json.JSONDecodeError as exc:
        raise ValueError("ADVANCE_COMPLETED_WITHOUT_JSON_RESULT") from exc
    if not isinstance(result, dict):
        raise ValueError("ADVANCE_RESULT_OBJECT_REQUIRED")
    return next_editorial_action(result)


def next_editorial_action(result: Mapping[str, Any]) -> dict[str, Any]:
    """No executable role or unfinished filter population can be a terminal window."""
    if result.get("classification") == "NATIVE_DESKTOP_INPUT_REQUIRED":
        calls = result.get("next_native_calls") or ([result["next_native_call"]] if result.get("next_native_call") else [])
        if not calls:
            raise ValueError("PENDING_NATIVE_ROLE_HAS_NO_DISPATCH")
        if len(calls) > 3 or any(c.get("tool") not in {"collaboration.spawn_agent", "collaboration.followup_task"} for c in calls):
            raise ValueError("BOUNDED_SUPPORTED_NATIVE_CALLS_REQUIRED")
        return {"action": "EXECUTE_AND_COLLECT_NATIVE_ROLES", "calls": calls,
                "after_returns": "SUBMIT_EACH_THEN_ADVANCE_SAME_BINDING", "terminal": False,
                "remaining_unprocessed": result.get("filter_progress", {}).get("remaining_unprocessed")}
    if int(result.get("filter_progress", {}).get("remaining_unprocessed") or 0) > 0:
        raise ValueError("UNASSIGNED_FILTER_BATCHES_REMAIN")
    if result.get("qualified_article_count", 0) > 0:
        return {"action": "REVIEW_EXACT_ARTICLE_AND_RENDERS", "terminal": False,
                "article_path": result.get("article_path"), "publication_performed": False}
    if result.get("classification") in {"NATIVE_PRE_WRITER_EDITION_COMPLETE", "NO_PUBLICATION"}:
        return {"action": "RECORD_TYPED_EDITORIAL_OUTCOME", "terminal": True,
                "reviewed_article_acceptance": False, "publication_performed": False}
    return {"action": "CONTINUE_EXISTING_OPERATION", "terminal": False,
            "classification": result.get("classification")}
