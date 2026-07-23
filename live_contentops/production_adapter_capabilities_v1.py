"""Versioned, adapter-owned capability bindings for production conformance.

These bindings describe what an already accepted adapter can truthfully
represent.  They do not grant evidence authority, numeric truth, permission,
or publication eligibility.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from live_contentops import content_intelligence_contracts_v2 as contracts


SCHEMA_VERSION = "contentops.production_adapter_capability_binding.v1"
CONTRACT_VERSION = "contentops.production_adapter_capabilities.v1.0.0"


class ObservationTimeKind(str, Enum):
    EVENT_TIME = "event_time"
    PERIOD_OBSERVATION = "period_observation"
    POINT_IN_TIME_OBSERVATION = "point_in_time_observation"
    REVISION_TIME = "revision_time"
    MIXED_OBSERVATION_AND_EVENT = "mixed_observation_and_event"


@dataclass(frozen=True)
class ProductionAdapterCapabilityBindingV1:
    adapter_id: str
    dimensions: contracts.CapabilityDimensionsV1
    observation_time_kind: ObservationTimeKind
    physical_geographic_capability: bool = False
    numeric_truth_quarantined: bool = False
    schema_version: str = SCHEMA_VERSION
    contract_version: str = CONTRACT_VERSION

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = list(self.dimensions.validate())
        if self.schema_version != SCHEMA_VERSION:
            blockers.append("capability_binding_schema_version_mismatch")
        if self.contract_version != CONTRACT_VERSION:
            blockers.append("capability_binding_contract_version_mismatch")
        if not self.adapter_id.strip():
            blockers.append("capability_binding_adapter_id_missing")
        if not self.dimensions.evidence_modalities:
            blockers.append("capability_binding_evidence_modality_missing")
        if not self.dimensions.temporal_characters:
            blockers.append("capability_binding_temporal_character_missing")
        if not self.dimensions.story_modes:
            blockers.append("capability_binding_story_mode_missing")
        if not self.dimensions.source_authority_classes:
            blockers.append("capability_binding_source_authority_missing")
        if self.dimensions.numeric_evidence_present is None:
            blockers.append("capability_binding_numeric_state_missing")
        if self.dimensions.nonnumeric_evidence_present is None:
            blockers.append("capability_binding_nonnumeric_state_missing")
        if self.dimensions.scheduled_event_state is None:
            blockers.append("capability_binding_schedule_state_missing")

        temporal = set(self.dimensions.temporal_characters)
        if self.observation_time_kind == ObservationTimeKind.PERIOD_OBSERVATION and contracts.TemporalCharacter.PERIOD_OBSERVATION not in temporal:
            blockers.append("capability_binding_period_observation_character_missing")
        if self.observation_time_kind == ObservationTimeKind.EVENT_TIME and contracts.TemporalCharacter.POINT_IN_TIME not in temporal:
            blockers.append("capability_binding_event_time_character_missing")
        if self.observation_time_kind == ObservationTimeKind.POINT_IN_TIME_OBSERVATION and contracts.TemporalCharacter.POINT_IN_TIME not in temporal:
            blockers.append("capability_binding_point_in_time_character_missing")
        if self.observation_time_kind == ObservationTimeKind.REVISION_TIME and contracts.TemporalCharacter.REVISED_RELEASE not in temporal:
            blockers.append("capability_binding_revision_character_missing")
        if self.observation_time_kind == ObservationTimeKind.MIXED_OBSERVATION_AND_EVENT and not {
            contracts.TemporalCharacter.PERIOD_OBSERVATION,
            contracts.TemporalCharacter.POINT_IN_TIME,
        }.issubset(temporal):
            blockers.append("capability_binding_mixed_time_characters_missing")

        physical_modality = contracts.EvidenceModality.GEOSPATIAL_OR_PHYSICAL_OBSERVATION
        if self.physical_geographic_capability:
            if physical_modality not in self.dimensions.evidence_modalities:
                blockers.append("physical_capability_modality_missing")
            if not self.dimensions.geography_ids:
                blockers.append("physical_capability_geography_missing")
        elif physical_modality in self.dimensions.evidence_modalities:
            blockers.append("physical_modality_capability_flag_missing")
        if self.numeric_truth_quarantined and self.dimensions.numeric_evidence_present:
            blockers.append("quarantined_numeric_truth_marked_present")
        return tuple(dict.fromkeys(blockers))

    def as_dict(self) -> Mapping[str, Any]:
        return {
            "schema_version": self.schema_version,
            "contract_version": self.contract_version,
            "adapter_id": self.adapter_id,
            "evidence_modalities": [value.value for value in self.dimensions.evidence_modalities],
            "temporal_characters": [value.value for value in self.dimensions.temporal_characters],
            "story_modes": [value.value for value in self.dimensions.story_modes],
            "scheduled_event_state": self.dimensions.scheduled_event_state,
            "observation_time_kind": self.observation_time_kind.value,
            "numeric_evidence_present": self.dimensions.numeric_evidence_present,
            "nonnumeric_evidence_present": self.dimensions.nonnumeric_evidence_present,
            "geography_ids": list(self.dimensions.geography_ids),
            "entity_ids": list(self.dimensions.entity_ids),
            "affected_economic_domains": list(self.dimensions.affected_economic_domains),
            "affected_asset_classes": list(self.dimensions.affected_asset_classes),
            "source_family_ids": list(self.dimensions.source_family_ids),
            "source_authority_classes": list(self.dimensions.source_authority_classes),
            "physical_geographic_capability": self.physical_geographic_capability,
            "numeric_truth_quarantined": self.numeric_truth_quarantined,
        }


def binding(
    adapter_id: str,
    *,
    modalities: tuple[contracts.EvidenceModality, ...],
    temporal: tuple[contracts.TemporalCharacter, ...],
    story_modes: tuple[contracts.StoryMode, ...],
    scheduled: bool,
    time_kind: ObservationTimeKind,
    source_family: str,
    numeric: bool,
    nonnumeric: bool,
    source_authority: str = "official_public_data",
    geography_ids: tuple[str, ...] = (),
    entity_ids: tuple[str, ...] = (),
    economic_domains: tuple[str, ...] = (),
    asset_classes: tuple[str, ...] = (),
    physical_geographic: bool = False,
    numeric_truth_quarantined: bool = False,
) -> ProductionAdapterCapabilityBindingV1:
    """Construct a complete binding without inferring topic semantics."""
    return ProductionAdapterCapabilityBindingV1(
        adapter_id=adapter_id,
        dimensions=contracts.CapabilityDimensionsV1(
            evidence_modalities=modalities,
            temporal_characters=temporal,
            story_modes=story_modes,
            geography_ids=geography_ids,
            entity_ids=entity_ids,
            affected_economic_domains=economic_domains,
            affected_asset_classes=asset_classes,
            source_family_ids=(source_family,),
            source_authority_classes=(source_authority,),
            numeric_evidence_present=numeric,
            nonnumeric_evidence_present=nonnumeric,
            scheduled_event_state=scheduled,
        ),
        observation_time_kind=time_kind,
        physical_geographic_capability=physical_geographic,
        numeric_truth_quarantined=numeric_truth_quarantined,
    )
