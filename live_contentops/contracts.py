"""Contract placeholders."""
from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class SourceArtifactExport:
    artifact_id: str
    content_zone: str
    source_payload: Dict[str, Any]
    approved_by: str
    timestamp: str

@dataclass
class PromptContract:
    prompt_id: str
    system_instruction: str
    user_context: str
    parameters: Dict[str, Any]

@dataclass
class ModelOutputContract:
    output_id: str
    prompt_id: str
    raw_text: str
    model_version: str

@dataclass
class PolicyDecision:
    decision_id: str
    target_id: str
    policy_version: str
    status: str

@dataclass
class HumanApprovalRecord:
    approval_id: str
    target_id: str
    operator_id: str
    timestamp: str
    action: str

@dataclass
class PublishJob:
    job_id: str
    approval_id: str
    platform: str
    payload: Dict[str, Any]
    status: str

@dataclass
class AdapterDryRunResult:
    run_id: str
    platform: str
    payload: Dict[str, Any]
    validation_status: str

@dataclass
class PublishResult:
    result_id: str
    job_id: str
    platform_post_id: str
    timestamp: str

@dataclass
class PlatformMetricsSnapshot:
    snapshot_id: str
    platform_post_id: str
    metrics_payload: Dict[str, Any]
    timestamp: str

@dataclass
class AuditEvent:
    event_id: str
    event_type: str
    actor: str
    target: str
    timestamp: str

@dataclass
class KillSwitchState:
    state_id: str
    status: str
    triggered_by: str
    timestamp: str

@dataclass
class IncidentReport:
    incident_id: str
    severity: str
    description: str
    mitigation_steps: str
