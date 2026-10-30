import json

import pytest

from live_contentops.native_editorial_continuation_v1 import consume_advance_result, next_editorial_action


def pending():
    return {"classification": "NATIVE_DESKTOP_INPUT_REQUIRED", "filter_progress": {"remaining_unprocessed": 131},
            "next_native_calls": [{"tool": "collaboration.spawn_agent", "arguments": {"task_name": "filter-a"}}]}


def test_initial_empty_exec_is_collected_by_its_actual_handle_not_reissued():
    result = consume_advance_result({"session_id": 125, "output": ""})
    assert result == {"action": "COLLECT_EXACT_COMMAND_HANDLE", "session_id": 125, "repeat_advance": False, "terminal": False}
    completed = consume_advance_result({"exit_code": 0, "output": json.dumps(pending())})
    assert completed["action"] == "EXECUTE_AND_COLLECT_NATIVE_ROLES" and not completed["terminal"]


def test_completed_handle_json_is_consumed_even_when_initial_stdout_was_empty():
    result = consume_advance_result({"exit_code": 0, "output": json.dumps({"classification": "PASS_NATIVE_DESKTOP_ZERO_WRITE_ARTICLE", "qualified_article_count": 1, "article_path": "local.md"})})
    assert result["action"] == "REVIEW_EXACT_ARTICLE_AND_RENDERS" and not result["terminal"]


def test_pending_role_without_actual_call_is_a_process_defect():
    result = pending(); result.pop("next_native_calls")
    with pytest.raises(ValueError, match="NO_DISPATCH"):
        next_editorial_action(result)


def test_unassigned_population_never_passes_as_a_complete_window():
    with pytest.raises(ValueError, match="UNASSIGNED_FILTER"):
        next_editorial_action({"classification": "NO_PUBLICATION", "filter_progress": {"remaining_unprocessed": 25}})


def test_typed_hold_is_not_reviewed_article_acceptance():
    result = next_editorial_action({"classification": "NATIVE_PRE_WRITER_EDITION_COMPLETE"})
    assert result["terminal"] and not result["reviewed_article_acceptance"]


def test_native_role_is_collected_in_same_operation_not_ancestor_chat():
    result = next_editorial_action(pending())
    assert result["after_returns"] == "SUBMIT_EACH_THEN_ADVANCE_SAME_BINDING"
    assert result["remaining_unprocessed"] == 131


def test_command_error_preserves_failure_instead_of_editorial_hold():
    assert consume_advance_result({"exit_code": 1, "output": "exception"})["action"] == "REPAIR_COMMAND_ERROR"
    with pytest.raises(ValueError, match="WITHOUT_JSON"):
        consume_advance_result({"exit_code": 0, "output": ""})
