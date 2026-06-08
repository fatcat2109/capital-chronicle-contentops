"""Live control plane contracts."""
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, Optional

class PlaneOwner(Enum):
    AUTHORING_PLANE = "AUTHORING_PLANE"
    CONTROL_PLANE = "CONTROL_PLANE"
    DELIVERY_PLANE = "DELIVERY_PLANE"

class NetworkReach(Enum):
    NO_NETWORK = "NO_NETWORK"
    PROVIDER_NETWORK_FUTURE_ONLY = "PROVIDER_NETWORK_FUTURE_ONLY"
    PLATFORM_NETWORK_FUTURE_ONLY = "PLATFORM_NETWORK_FUTURE_ONLY"
    INTERNAL_ONLY = "INTERNAL_ONLY"

@dataclass
class SafeBaseContract:
    schema_version: str = "1.0.0"
    network_used: bool = False
    provider_call_used: bool = False
    platform_api_used: bool = False
    publishing_enabled: bool = False
    scheduler_enabled: bool = False
    auto_approved: bool = False
    human_approval_required: bool = True
    secrets_redacted: bool = True
    safe_to_log: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SourceArtifactExport(SafeBaseContract):
    artifact_id: str = ""
    content_zone: str = ""
    source_payload: Dict[str, Any] = None
    approved_by: str = ""
    timestamp: str = ""
    plane_owner: PlaneOwner = PlaneOwner.AUTHORING_PLANE
    network_reach: NetworkReach = NetworkReach.NO_NETWORK

@dataclass
class PromptContract(SafeBaseContract):
    prompt_id: str = ""
    system_instruction: str = ""
    user_context: str = ""
    parameters: Dict[str, Any] = None
    plane_owner: PlaneOwner = PlaneOwner.CONTROL_PLANE
    network_reach: NetworkReach = NetworkReach.NO_NETWORK

@dataclass
class ModelOutputContract(SafeBaseContract):
    output_id: str = ""
    prompt_id: str = ""
    raw_text: str = ""
    model_version: str = ""
    plane_owner: PlaneOwner = PlaneOwner.CONTROL_PLANE
    network_reach: NetworkReach = NetworkReach.NO_NETWORK

@dataclass
class PolicyDecision(SafeBaseContract):
    decision_id: str = ""
    target_id: str = ""
    policy_version: str = ""
    status: str = ""
    plane_owner: PlaneOwner = PlaneOwner.CONTROL_PLANE
    network_reach: NetworkReach = NetworkReach.NO_NETWORK

@dataclass
class HumanApprovalRecord(SafeBaseContract):
    approval_id: str = ""
    target_id: str = ""
    operator_id: str = ""
    timestamp: str = ""
    action: str = ""
    plane_owner: PlaneOwner = PlaneOwner.CONTROL_PLANE
    network_reach: NetworkReach = NetworkReach.NO_NETWORK

@dataclass
class PublishJob(SafeBaseContract):
    job_id: str = ""
    approval_id: str = ""
    platform: str = ""
    payload: Dict[str, Any] = None
    status: str = ""
    plane_owner: PlaneOwner = PlaneOwner.DELIVERY_PLANE
    network_reach: NetworkReach = NetworkReach.NO_NETWORK

@dataclass
class AdapterDryRunResult(SafeBaseContract):
    run_id: str = ""
    platform: str = ""
    payload: Dict[str, Any] = None
    validation_status: str = ""
    plane_owner: PlaneOwner = PlaneOwner.DELIVERY_PLANE
    network_reach: NetworkReach = NetworkReach.NO_NETWORK

@dataclass
class PublishResult(SafeBaseContract):
    result_id: str = ""
    job_id: str = ""
    platform_post_id: str = ""
    timestamp: str = ""
    plane_owner: PlaneOwner = PlaneOwner.DELIVERY_PLANE
    network_reach: NetworkReach = NetworkReach.NO_NETWORK

@dataclass
class PlatformMetricsSnapshot(SafeBaseContract):
    snapshot_id: str = ""
    platform_post_id: str = ""
    metrics_payload: Dict[str, Any] = None
    timestamp: str = ""
    plane_owner: PlaneOwner = PlaneOwner.DELIVERY_PLANE
    network_reach: NetworkReach = NetworkReach.NO_NETWORK

@dataclass
class AuditEvent(SafeBaseContract):
    event_id: str = ""
    event_type: str = ""
    actor: str = ""
    target: str = ""
    timestamp: str = ""
    plane_owner: PlaneOwner = PlaneOwner.CONTROL_PLANE
    network_reach: NetworkReach = NetworkReach.NO_NETWORK

@dataclass
class KillSwitchState(SafeBaseContract):
    state_id: str = ""
    status: str = ""
    triggered_by: str = ""
    timestamp: str = ""
    plane_owner: PlaneOwner = PlaneOwner.CONTROL_PLANE
    network_reach: NetworkReach = NetworkReach.NO_NETWORK

@dataclass
class IncidentReport(SafeBaseContract):
    incident_id: str = ""
    severity: str = ""
    description: str = ""
    mitigation_steps: str = ""
    plane_owner: PlaneOwner = PlaneOwner.CONTROL_PLANE
    network_reach: NetworkReach = NetworkReach.NO_NETWORK
