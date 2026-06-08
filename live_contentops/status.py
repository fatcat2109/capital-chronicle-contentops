"""Status reporter for the CLI."""
from . import config

def get_status() -> dict:
    return {
        "status": "local skeleton status",
        "network": "disabled" if not config.NETWORK_ENABLED else "enabled",
        "provider_calls": "disabled" if not config.PROVIDER_CALLS_ENABLED else "enabled",
        "platform_apis": "disabled" if not config.PLATFORM_APIS_ENABLED else "enabled",
        "scheduler": "disabled" if not config.SCHEDULER_ENABLED else "enabled",
        "publishing": "disabled" if not config.PUBLISHING_ENABLED else "enabled",
        "autonomous_replies": "disabled" if not config.AUTONOMOUS_REPLIES_ENABLED else "enabled",
        "human_approval": "required" if config.REQUIRE_HUMAN_APPROVAL else "bypassed",
        "kill_switch_halt": "active" if config.KILL_SWITCH_DEFAULT else "inactive",
        "next_task": "TASK_CONTENTOPS_0064_LOCAL_OPERATOR_DECISION_CAPTURE_AND_REVIEW_HISTORY_V0",
    }
