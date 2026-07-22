"""Bounded no-write adapters for three committed official Wave-3 artifacts."""
from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timezone
from fnmatch import fnmatch
from hashlib import sha256
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

from live_contentops import content_intelligence_contracts_v2 as contracts


UPSTREAM_REPOSITORY = "fatcat2109/Headline-Raw-data-json"
UPSTREAM_BRANCH = "main"
OBSERVED_UPSTREAM_HEAD = "631ea29c5388d52d4353810b6d8b2a50d677bb44"
VERIFIER_ID = "contentops.production_external_exact_git_verifier_wave3"
VERIFIER_VERSION = "v1"
EXTRACTOR_VERSION = "v1"

TIC_SCHEMA = "external.us_treasury_tic_official_html.v1"
USGS_SCHEMA = "external.usgs_earthquake_geojson.v1"
FHFA_SCHEMA = "external.fhfa_hpi_official_html.v1"
TIC_EXTRACTOR_ID = "contentops.treasury_tic_html_extractor"
USGS_EXTRACTOR_ID = "contentops.usgs_earthquake_geojson_extractor"
FHFA_EXTRACTOR_ID = "contentops.fhfa_hpi_html_extractor"

TIC_PATH = "data/raw/new_sources_capture_v1/source_52_repaired_evidence.bin"
USGS_PATH = "data/raw/new_sources_capture_v1/source_48_raw_evidence.bin"
FHFA_PATH = "data/raw/new_sources_capture_v1/source_53_repaired_evidence.bin"

PINNED_ARTIFACTS: Mapping[str, Mapping[str, Any]] = {
    TIC_EXTRACTOR_ID: {
        "producer_commit": "04e2efe669ecd874301f24eb66dc6e68b58b9f2d", "path": TIC_PATH,
        "git_blob_sha1": "affd19cea196614ad650b36ca7a8a50dd119bbf4",
        "byte_sha256": "fdfe780d622e0dcc2586496bba179a36d8571103071fe1dc5294d78cc40ff615", "byte_length": 125185,
    },
    USGS_EXTRACTOR_ID: {
        "producer_commit": "0eb73c46c0c9f43b810d4f4ff30ba6695f3a3257", "path": USGS_PATH,
        "git_blob_sha1": "6a6f19e18320f5cc05c68b27d09da9adafc514d4",
        "byte_sha256": "9754c1372e9973982abac470ab9d91738a346ecbdb76d56e119b7f460405d506", "byte_length": 942,
    },
    FHFA_EXTRACTOR_ID: {
        "producer_commit": "04e2efe669ecd874301f24eb66dc6e68b58b9f2d", "path": FHFA_PATH,
        "git_blob_sha1": "79d67fda002276cf743a64630d6a445e271febaa",
        "byte_sha256": "6f91af6847f89310b70df3213995808187c8af147ac34ff96ef8130c8285c1e2", "byte_length": 87277,
    },
}

IMPLEMENTATION_CONTRACT_COVERAGE: Mapping[tuple[str, str], Mapping[str, Any]] = {
    (TIC_EXTRACTOR_ID, EXTRACTOR_VERSION): {
        "shape_contract_id": "treasury.tic.official_html.external_shape.v1",
        "required_fields": ("/html/head/title", "/html/head/link[@rel=canonical]", "/html/head/meta[@property=og:site_name]", "/html/head/meta[@property=og:url]", "/html/head/meta[@property=og:updated_time]"),
        "timestamp_extraction_rules": {"observed_at_utc": "UNAVAILABLE_PAGE_HAS_NO_DISTINCT_OBSERVATION_TIMESTAMP", "known_at_utc": "VERIFIED_GIT_RECEIPT_ARTIFACT_CUTOFF", "published_at_utc": "UNAVAILABLE_NO_EXPLICIT_ARTIFACT_RELEASE_TIMESTAMP", "revision_at_utc": "/html/head/meta[@property=og:updated_time]@START_OF_UTC_DAY"},
    },
    (USGS_EXTRACTOR_ID, EXTRACTOR_VERSION): {
        "shape_contract_id": "usgs.earthquake.feature_collection.geojson.external_shape.v1",
        "required_fields": ("/type", "/metadata/generated", "/metadata/url", "/metadata/status", "/features/*/id", "/features/*/properties/mag", "/features/*/properties/time", "/features/*/properties/updated", "/features/*/geometry/type", "/features/*/geometry/coordinates"),
        "timestamp_extraction_rules": {"observed_at_utc": "/features/*/properties/time@EPOCH_MILLISECONDS", "known_at_utc": "/metadata/generated@EPOCH_MILLISECONDS", "published_at_utc": "UNAVAILABLE_NO_EXPLICIT_ARTIFACT_RELEASE_TIMESTAMP", "revision_at_utc": "/features/*/properties/updated@EPOCH_MILLISECONDS"},
    },
    (FHFA_EXTRACTOR_ID, EXTRACTOR_VERSION): {
        "shape_contract_id": "fhfa.hpi.official_html.external_shape.v1",
        "required_fields": ("/html/head/title", "/html/head/link[@rel=canonical]", "/html/head/meta[@name=author]", "/html/head/meta[@property=article:modified_time]"),
        "timestamp_extraction_rules": {"observed_at_utc": "UNAVAILABLE_PAGE_HAS_NO_DISTINCT_OBSERVATION_TIMESTAMP", "known_at_utc": "VERIFIED_GIT_RECEIPT_ARTIFACT_CUTOFF", "published_at_utc": "UNAVAILABLE_NO_EXPLICIT_ARTIFACT_RELEASE_TIMESTAMP", "revision_at_utc": "/html/head/meta[@property=article:modified_time]@START_OF_UTC_DAY"},
    },
}

_EXTRACTOR_IDS = frozenset(PINNED_ARTIFACTS)


def _git_prefix(repository: Path) -> list[str]:
    return ["git", "--git-dir", str(repository)] if repository.is_file() or repository.suffix == ".git" else ["git", "-C", str(repository)]


def build_wave3_git_artifact_receipt(
    *, git_repository: str | Path, registry: contracts.TrustedVerifierRegistryV1,
    commit: str, artifact_path: str, artifact_schema_version: str,
    producer_version: str, artifact_cutoff_utc: str, verification_time_utc: str,
    branch_authority_ref: str, expected_git_blob_sha1: str | None = None,
    expected_byte_sha256: str | None = None,
) -> contracts.VerifiedProducerArtifactReceiptV1:
    repository = Path(git_repository).resolve()
    prefix = _git_prefix(repository)
    try:
        branch_head = subprocess.run([*prefix, "rev-parse", "--verify", branch_authority_ref], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip()
        if subprocess.run([*prefix, "merge-base", "--is-ancestor", commit, branch_head], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode:
            raise ValueError("committed_artifact_not_reachable_from_observed_branch")
        consumed = subprocess.run([*prefix, "show", f"{commit}:{artifact_path}"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
        blob = subprocess.run([*prefix, "rev-parse", f"{commit}:{artifact_path}"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip()
    except subprocess.CalledProcessError as error:
        raise ValueError("committed_artifact_resolution_failed") from error
    byte_hash = sha256(consumed).hexdigest()
    if expected_git_blob_sha1 is not None and blob != expected_git_blob_sha1:
        raise ValueError("pinned_git_blob_mismatch")
    if expected_byte_sha256 is not None and byte_hash != expected_byte_sha256:
        raise ValueError("pinned_byte_sha256_mismatch")
    return contracts.build_verified_producer_artifact_receipt_v1(
        consumed, registry=registry, verifier_id=VERIFIER_ID, verifier_version=VERIFIER_VERSION,
        repository=UPSTREAM_REPOSITORY, branch=UPSTREAM_BRANCH, producer_commit=commit,
        artifact_path=artifact_path, expected_git_blob_sha1=blob,
        artifact_schema_version=artifact_schema_version, producer_version=producer_version,
        artifact_cutoff_utc=artifact_cutoff_utc, evidence_refs=(), source_authority_class="official_public_data",
        resolved_repository=UPSTREAM_REPOSITORY, resolved_branch=UPSTREAM_BRANCH, resolved_commit=commit,
        resolved_artifact_path=artifact_path, branch_head_observed=branch_head,
        producer_commit_reachable_from_branch=True, verification_time_utc=verification_time_utc,
    )


def _utc_day(value: str, pattern: str, reason: str) -> str:
    try:
        parsed = datetime.strptime(value, pattern).date()
    except ValueError as error:
        raise ValueError(reason) from error
    return datetime.combine(parsed, datetime.min.time(), timezone.utc).isoformat().replace("+00:00", "Z")


def _epoch_millis(value: Any, reason: str) -> str:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(reason)
    try:
        parsed = datetime.fromtimestamp(value / 1000, timezone.utc)
    except (OverflowError, OSError, ValueError) as error:
        raise ValueError(reason) from error
    return parsed.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _extract_tic(consumed: bytes, selector: Mapping[str, str]):
    canonical = "https://home.treasury.gov/data/treasury-international-capital-tic-system"
    if set(selector) != {"canonical_url"} or selector["canonical_url"] != canonical:
        raise ValueError("treasury_tic_selector_mismatch")
    if len(consumed) > 1_000_000:
        raise ValueError("treasury_tic_html_too_large")
    try:
        text = consumed.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("treasury_tic_html_encoding_invalid") from error
    parser = _HeadFacts()
    parser.feed(text)
    titles = [value.strip() for value in parser.titles if value.strip()]
    site = parser.meta.get(("property", "og:site_name"), [])
    og_url = parser.meta.get(("property", "og:url"), [])
    updated = parser.meta.get(("property", "og:updated_time"), [])
    if titles != ["Treasury International Capital (TIC) System | U.S. Department of the Treasury"] or parser.canonicals != [canonical] or site != ["U.S. Department of the Treasury"] or og_url != [canonical] or len(updated) != 1:
        raise ValueError("treasury_tic_official_shape_mismatch")
    revision = _utc_day(updated[0], "%Y-%m-%d", "treasury_tic_updated_date_invalid")
    record = {"title": titles[0], "canonical_url": canonical, "site_name": site[0], "updated_date": updated[0]}
    return record, canonical, tuple(record), {"observed_at_utc": None, "known_at_utc": None, "published_at_utc": None, "revision_at_utc": revision}


def _extract_usgs(consumed: bytes, selector: Mapping[str, str]):
    if set(selector) != {"event_id"} or not selector["event_id"]:
        raise ValueError("usgs_earthquake_selector_mismatch")
    if len(consumed) > 1_000_000:
        raise ValueError("usgs_earthquake_artifact_too_large")
    try:
        artifact = json.loads(consumed)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("usgs_earthquake_geojson_malformed") from error
    if not isinstance(artifact, Mapping) or artifact.get("type") != "FeatureCollection" or not isinstance(artifact.get("metadata"), Mapping) or not isinstance(artifact.get("features"), list):
        raise ValueError("usgs_earthquake_shape_mismatch")
    metadata = artifact["metadata"]
    if metadata.get("status") != 200 or not str(metadata.get("url", "")).startswith("https://earthquake.usgs.gov/fdsnws/event/1/query?") or metadata.get("limit") != len(artifact["features"]):
        raise ValueError("usgs_earthquake_metadata_mismatch")
    selected = [row for row in artifact["features"] if isinstance(row, Mapping) and row.get("id") == selector["event_id"]]
    if len(selected) != 1:
        raise ValueError("usgs_earthquake_selector_not_unique")
    row = selected[0]
    props, geometry = row.get("properties"), row.get("geometry")
    if row.get("type") != "Feature" or not isinstance(props, Mapping) or not isinstance(geometry, Mapping) or geometry.get("type") != "Point":
        raise ValueError("usgs_earthquake_feature_shape_mismatch")
    coordinates = geometry.get("coordinates")
    mag = props.get("mag")
    if not isinstance(mag, (int, float)) or isinstance(mag, bool) or not math.isfinite(float(mag)):
        raise ValueError("usgs_earthquake_magnitude_invalid")
    if not isinstance(coordinates, list) or len(coordinates) != 3 or any(not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(float(v)) for v in coordinates):
        raise ValueError("usgs_earthquake_coordinates_invalid")
    observed = _epoch_millis(props.get("time"), "usgs_earthquake_event_time_invalid")
    revision = _epoch_millis(props.get("updated"), "usgs_earthquake_revision_time_invalid")
    known = _epoch_millis(metadata.get("generated"), "usgs_earthquake_generated_time_invalid")
    if not (contracts.parse_utc(observed) <= contracts.parse_utc(revision) <= contracts.parse_utc(known)):
        raise ValueError("usgs_earthquake_timestamp_order_invalid")
    record = {"event_id": selector["event_id"], "magnitude": mag, "place": props.get("place"), "event_status": props.get("status"), "coordinates": coordinates, "tsunami": props.get("tsunami")}
    if any(record[key] in (None, "") for key in ("place", "event_status", "tsunami")):
        raise ValueError("usgs_earthquake_required_field_missing")
    return record, selector["event_id"], tuple(record), {"observed_at_utc": observed, "known_at_utc": known, "published_at_utc": None, "revision_at_utc": revision}


class _HeadFacts(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_head = False
        self.in_title = False
        self.titles: list[str] = []
        self.canonicals: list[str] = []
        self.meta: dict[tuple[str, str], list[str]] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "head":
            self.in_head = True
        elif self.in_head and tag.lower() == "title":
            self.in_title = True
            self.titles.append("")
        elif self.in_head and tag.lower() == "link" and values.get("rel", "").lower() == "canonical":
            self.canonicals.append(values.get("href", ""))
        elif self.in_head and tag.lower() == "meta":
            for kind in ("name", "property"):
                if values.get(kind):
                    self.meta.setdefault((kind, values[kind]), []).append(values.get("content", ""))

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False
        elif tag.lower() == "head":
            self.in_head = False

    def handle_data(self, data: str) -> None:
        if self.in_title and self.titles:
            self.titles[-1] += data


def _extract_fhfa(consumed: bytes, selector: Mapping[str, str]):
    if set(selector) != {"canonical_url"} or selector["canonical_url"] != "https://www.fhfa.gov/data/hpi":
        raise ValueError("fhfa_hpi_selector_mismatch")
    if len(consumed) > 1_000_000:
        raise ValueError("fhfa_hpi_html_too_large")
    try:
        text = consumed.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("fhfa_hpi_html_encoding_invalid") from error
    parser = _HeadFacts()
    parser.feed(text)
    titles = [value.strip() for value in parser.titles if value.strip()]
    author = parser.meta.get(("name", "author"), [])
    modified = parser.meta.get(("property", "article:modified_time"), [])
    if titles != ["FHFA House Price Index® | FHFA"] or parser.canonicals != [selector["canonical_url"]] or author != ["FHFA"] or len(modified) != 1:
        raise ValueError("fhfa_hpi_official_shape_mismatch")
    revision = _utc_day(modified[0], "%Y-%m-%d", "fhfa_hpi_modified_date_invalid")
    record = {"title": titles[0], "canonical_url": parser.canonicals[0], "author": author[0], "modified_date": modified[0]}
    return record, selector["canonical_url"], tuple(record), {"observed_at_utc": None, "known_at_utc": None, "published_at_utc": None, "revision_at_utc": revision}


def _feature_value(feature_id: str, record: Mapping[str, Any], fields: Sequence[str], times: Mapping[str, str | None], evidence_ref: str, cutoff: str, rule: str) -> contracts.ExtractedFeatureValueV1:
    if feature_id == "evidence_completeness":
        value: float | None = sum(record.get(field) not in (None, "") for field in fields) / len(fields)
        availability, reason = (contracts.AvailabilityState.EXPLICIT_ZERO if value == 0.0 else contracts.AvailabilityState.AVAILABLE), None
    elif feature_id == "freshness":
        basis = times.get("published_at_utc") or times.get("known_at_utc") or times.get("revision_at_utc")
        if basis is None:
            value, availability, reason = None, contracts.AvailabilityState.UNAVAILABLE, "release_capture_or_revision_timestamp_unavailable"
        else:
            age = max(0.0, (contracts.parse_utc(cutoff) - contracts.parse_utc(basis)).total_seconds() / 3600)
            value, reason = max(0.0, 1.0 - age / 24.0), None
            availability = contracts.AvailabilityState.EXPLICIT_ZERO if value == 0.0 else contracts.AvailabilityState.AVAILABLE
    else:
        value, availability, reason = None, contracts.AvailabilityState.UNAVAILABLE, "feature_derivation_not_supported_by_extractor"
    draft = contracts.ExtractedFeatureValueV1(feature_id, availability, value, (evidence_ref,), rule, reason, "")
    result = replace(draft, logical_hash=draft.calculated_logical_hash())
    if result.validate():
        raise ValueError("invalid_wave3_feature_value")
    return result


def _narrow(requested: str | None, derived: str, ranks: Mapping[str, int], kind: str) -> str:
    if requested is None or requested == derived:
        return derived
    if requested not in ranks:
        raise ValueError(f"unknown_requested_{kind}_state")
    if ranks[requested] >= ranks[derived]:
        raise ValueError(f"caller_{kind}_upgrade_forbidden")
    return requested


def extract_wave3_artifact_evidence(
    consumed_bytes: bytes, *, receipt: contracts.VerifiedProducerArtifactReceiptV1,
    registry: contracts.ArtifactEvidenceExtractorRegistryV1, extractor_id: str,
    extractor_version: str, selector: Mapping[str, str], feature_targets: Sequence[str],
    decision_cutoff_utc: str, evidence_roles: Sequence[contracts.EvidenceRole] | None = None,
    evidence_scope: contracts.EvidenceScope = contracts.EvidenceScope.FEATURE_SPECIFIC,
    authority_state: str | None = None, permission_state: str | None = None,
) -> tuple[contracts.ExtractedEvidenceRecordV1, tuple[contracts.ExtractedFeatureValueV1, ...]]:
    if registry.validate():
        raise ValueError("invalid_evidence_extractor_registry")
    extractor = registry.resolve(extractor_id, extractor_version)
    if extractor is None or not extractor.enabled or extractor_id not in _EXTRACTOR_IDS:
        raise ValueError("unsupported_wave3_extractor")
    if sha256(consumed_bytes).hexdigest() != receipt.consumed_byte_sha256:
        raise ValueError("extractor_consumed_bytes_receipt_mismatch")
    if receipt.repository not in extractor.supported_repositories or not any(fnmatch(receipt.artifact_path, pattern) for pattern in extractor.supported_path_patterns):
        raise ValueError("extractor_source_binding_mismatch")
    if receipt.artifact_schema_version not in extractor.supported_artifact_schema_versions or receipt.producer_version != extractor.shape_contract_id:
        raise ValueError("extractor_schema_or_shape_contract_mismatch")
    if evidence_scope not in extractor.supported_evidence_scopes or any(feature not in extractor.supported_feature_ids for feature in feature_targets):
        raise ValueError("extractor_scope_or_feature_unsupported")
    extraction = {TIC_EXTRACTOR_ID: _extract_tic, USGS_EXTRACTOR_ID: _extract_usgs, FHFA_EXTRACTOR_ID: _extract_fhfa}[extractor_id]
    record, record_key, fields, times = extraction(consumed_bytes, selector)
    if times.get("known_at_utc") is None:
        times = {**times, "known_at_utc": receipt.artifact_cutoff_utc}
    cutoff = contracts.parse_utc(decision_cutoff_utc, field_name="decision_cutoff_utc")
    for name, timestamp in times.items():
        if timestamp and contracts.parse_utc(timestamp, field_name=name) > cutoff:
            raise ValueError(f"internal_future_timestamp:{name}")
    roles = (contracts.EvidenceRole.FEATURE_SUPPORT,) if evidence_roles is None else tuple(evidence_roles)
    if any(role != contracts.EvidenceRole.FEATURE_SUPPORT for role in roles):
        raise ValueError("caller_evidence_role_addition_forbidden")
    selected_authority = _narrow(authority_state, "OFFICIAL_VERIFIED", contracts.AUTHORITY_STATE_RANK, "authority")
    selected_permission = _narrow(permission_state, "CONTEXT_ONLY", contracts.PERMISSION_STATE_RANK, "permission")
    reasons = ["context_only", "external_official_context_only"]
    if selected_authority != "OFFICIAL_VERIFIED": reasons.append("caller_authority_narrowed")
    if selected_permission != "CONTEXT_ONLY": reasons.append("caller_permission_narrowed")
    record_hash = contracts.logical_hash(record)
    evidence_ref = "extracted:" + contracts.logical_hash({"producer_receipt_logical_hash": receipt.logical_hash, "extractor_id": extractor_id, "extractor_version": extractor_version, "record_selector": dict(sorted(selector.items())), "record_key": record_key, "extracted_record_hash": record_hash, "derivation_rule": extractor.evidence_ref_derivation_rule})[:32]
    draft = contracts.ExtractedEvidenceRecordV1(
        receipt.receipt_id, receipt.logical_hash, extractor_id, extractor_version,
        contracts.canonical_json(dict(sorted(selector.items()))), record_key, record_hash, evidence_ref,
        tuple(fields), times["observed_at_utc"], times["known_at_utc"], times["published_at_utc"], times["revision_at_utc"],
        receipt.artifact_cutoff_utc, roles, evidence_scope, tuple(feature_targets), extractor.implementation_contract_id,
        selected_authority, selected_permission, receipt.source_authority_class, receipt.artifact_schema_version,
        extractor.schema_authority, True, True, None, "", extractor.authority_derivation_rule,
        extractor.permission_derivation_rule, extractor.role_derivation_rule, "NOT_QUALIFYING_GOVERNED", tuple(reasons),
    )
    extracted = replace(draft, extraction_logical_hash=draft.calculated_logical_hash())
    if extracted.validate():
        raise ValueError("invalid_wave3_extracted_evidence_record")
    features = tuple(_feature_value(feature, record, fields, times, evidence_ref, decision_cutoff_utc, extractor.value_derivation_rules[feature]) for feature in feature_targets)
    return extracted, features
