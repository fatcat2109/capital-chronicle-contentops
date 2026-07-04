import os
import json
from dataclasses import dataclass
from typing import Dict, Any, Tuple

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "schemas", "telegram_second_sandbox_dry_run_prep.schema.json")

@dataclass
class SecondSandboxPrepState:
    precheck_passed: bool
    operator_go_present: bool
    wrapper_script_requested: bool
    live_attempt_count: int
    process_env_variables_present: bool

def validate_prep_state(state: SecondSandboxPrepState) -> Tuple[bool, Dict[str, Any]]:
    """
    Validates the local dry run preparation state for the second sandbox test.
    """
    if not state.precheck_passed:
        return False, {
            "error": "Precheck must be explicitly passed before sandbox prep",
            "status": "BLOCKED"
        }
        
    if not state.operator_go_present:
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
    
    return True, {
        "status": "PREP_PASSED",
        "live_attempt_count": state.live_attempt_count,
        "wrapper_script_requested": state.wrapper_script_requested
    }
