import os
import json
from dataclasses import dataclass
from typing import Dict, Any, Tuple

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "schemas", "telegram_live_precheck.schema.json")

@dataclass
class PrecheckState:
    exact_operator_go_present: bool
    process_env_variables_present: bool
    untracked_env_file_present: bool
    wrapper_script_requested: bool
    live_attempt_count: int

def validate_precheck_state(state: PrecheckState) -> Tuple[bool, Dict[str, Any]]:
    """
    Validates the local live run precheck state according to strict safety rules.
    """
    if not state.exact_operator_go_present:
        return False, {
            "error": "Missing exact OPERATOR_GO approval phrase",
            "status": "BLOCKED"
        }
    
    if not state.process_env_variables_present:
        return False, {
            "error": "Missing required process environment variables",
            "status": "BLOCKED"
        }
    
    if state.wrapper_script_requested:
        return False, {
            "error": "Wrapper script execution is forbidden",
            "status": "BLOCKED"
        }
    
    if state.live_attempt_count > 0:
        return False, {
            "error": "Live attempt count greater than zero; retries require reset",
            "status": "BLOCKED"
        }
    
    # Check untracked_env_file_present for logging purposes
    caveat = "OPERATOR_OWNED_UNTRACKED_SECRET_FILE_PRESENT" if state.untracked_env_file_present else "TRACKED_TREE_CLEAN"
    
    return True, {
        "status": "PRECHECK_PASSED",
        "env_caveat": caveat,
        "live_attempt_count": state.live_attempt_count,
        "wrapper_script_requested": state.wrapper_script_requested
    }
