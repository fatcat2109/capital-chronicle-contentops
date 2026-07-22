"""Bounded no-write adapters for wave-2 official committed artifacts.

Only exact bytes already present in a reachable upstream Git commit are read.
The adapters perform no fetch, credential access, publication, or authority
mutation and cap external evidence at OFFICIAL_VERIFIED / CONTEXT_ONLY /
FEATURE_SUPPORT.
"""
from __future__ import annotations

import calendar
from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from fnmatch import fnmatch
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Mapping, Sequence

from live_contentops import content_intelligence_contracts_v2 as contracts


UPSTREAM_REPOSITORY = "fatcat2109/Headline-Raw-data-json"
UPSTREAM_BRANCH = "main"
OBSERVED_UPSTREAM_HEAD = "aed2e64c76a264862bc44006a13ffaf41883af75"
VERIFIER_ID = "contentops.production_external_exact_git_verifier_wave2"
VERIFIER_VERSION = "v1"
EXTRACTOR_VERSION = "v2"

TREASURY_SCHEMA = "external.us_treasury_debt_to_penny_response.v1"
BLS_SCHEMA = "external.bls_unemployment_series_response.v1"
FOMC_SCHEMA = "external.federal_reserve_fomc_calendar_html.v1"
TREASURY_EXTRACTOR_ID = "contentops.treasury_debt_to_penny_extractor"
BLS_EXTRACTOR_ID = "contentops.bls_unemployment_series_extractor"
FOMC_EXTRACTOR_ID = "contentops.fomc_calendar_html_extractor"

TREASURY_PATH = "data/archive/official_sources/us_treasury_fiscaldata_api/us_treasury_fiscaldata_api_live_20260603_121640_28d55402e421/raw_response.json"
BLS_PATH = "data/audit/data_sufficiency/task_244aa_248z/raw_archive/bls_beyond_cpi/capture_bls_beyond_cpi_20260605T152047Z_763dd2aa.body"
FOMC_PATH = "data/audit/raw_archive/task_calendar_event_spine_batch_a2_page_only_controlled_live_capture/fomc_calendar_statements_2026-06-09T02_57_12Z.html"

PINNED_ARTIFACTS: Mapping[str, Mapping[str, Any]] = {
    TREASURY_EXTRACTOR_ID: {
        "producer_commit": "788c86f8a71528683789581af4e77b529d92a97e",
        "path": TREASURY_PATH, "git_blob_sha1": "263e213836403661f0bfe8248c42410d3859506e",
        "byte_sha256": "28d55402e421cd437727d7f280d2c0da9dba45ea25ba122059a7f55f24ef51ee", "byte_length": 1791,
    },
    BLS_EXTRACTOR_ID: {
        "producer_commit": "7cae8aa1727f8d78e5801b76702fb928b92476fc",
        "path": BLS_PATH, "git_blob_sha1": "17a19353e038ff33ac9f9584314af91a1908d0cc",
        "byte_sha256": "254b1137dfcc482a9c37581463b0ea393b90cd110c88ae5b7d5c91c06be2acc6", "byte_length": 2817,
    },
    FOMC_EXTRACTOR_ID: {
        "producer_commit": "94c0482f40e764c6ad34707ab28ffe36df57c202",
        "path": FOMC_PATH, "git_blob_sha1": "d036fec5666b38c8cbb5bc1079f820f4db5571f1",
        "byte_sha256": "8c6cd522e52a3847683dc74bafc32589bd22c67cd1908f88a2fe0807253e7621", "byte_length": 159529,
    },
}

_EXTRACTOR_IDS = frozenset(PINNED_ARTIFACTS)
_MONTHS = {name: index for index, name in enumerate(calendar.month_name) if name}
_FOMC_MEETING = re.compile(
    r'fomc-meeting__month[^>]*><strong>([A-Za-z]+)</strong></div>\s*'
    r'<div class="[^"]*fomc-meeting__date[^"]*">([^<]+)</div>', re.IGNORECASE,
)

_TREASURY_DATA_TYPES = {
    "record_date": "DATE",
    "debt_held_public_amt": "CURRENCY",
    "intragov_hold_amt": "CURRENCY",
    "tot_pub_debt_out_amt": "CURRENCY",
    "src_line_nbr": "INTEGER",
    "record_fiscal_year": "YEAR",
    "record_fiscal_quarter": "QUARTER",
    "record_calendar_year": "YEAR",
    "record_calendar_quarter": "QUARTER",
    "record_calendar_month": "MONTH",
    "record_calendar_day": "DAY",
}

IMPLEMENTATION_CONTRACT_COVERAGE: Mapping[tuple[str, str], Mapping[str, Any]] = {
    (TREASURY_EXTRACTOR_ID, EXTRACTOR_VERSION): {
        "shape_contract_id": "treasury.fiscaldata.debt_to_penny.external_shape.v2",
        "required_fields": (
            "/data", "/data/*/record_date", "/data/*/debt_held_public_amt",
            "/data/*/intragov_hold_amt", "/data/*/tot_pub_debt_out_amt",
            "/meta/count", "/meta/dataTypes", "/links/self", "/links/first",
            "/links/prev", "/links/next", "/links/last",
        ),
        "timestamp_extraction_rules": {
            "observed_at_utc": "/data/*/record_date@START_OF_UTC_DAY",
            "known_at_utc": "VERIFIED_GIT_RECEIPT_ARTIFACT_CUTOFF",
            "published_at_utc": "UNAVAILABLE_NO_EXPLICIT_ARTIFACT_RELEASE_TIMESTAMP",
            "revision_at_utc": "UNAVAILABLE_NO_EXPLICIT_ARTIFACT_REVISION_TIMESTAMP",
        },
    },
    (BLS_EXTRACTOR_ID, EXTRACTOR_VERSION): {
        "shape_contract_id": "bls.public_data.unemployment_series.external_shape.v2",
        "required_fields": (
            "/status", "/message", "/Results/series", "/Results/series/*/seriesID",
            "/Results/series/*/data/*/year", "/Results/series/*/data/*/period",
            "/Results/series/*/data/*/periodName", "/Results/series/*/data/*/value",
        ),
        "timestamp_extraction_rules": {
            "observed_at_utc": "/Results/series/*/data/*/(year,period)@START_OF_UTC_MONTH",
            "known_at_utc": "VERIFIED_GIT_RECEIPT_ARTIFACT_CUTOFF",
            "published_at_utc": "UNAVAILABLE_NO_EXPLICIT_ARTIFACT_RELEASE_TIMESTAMP",
            "revision_at_utc": "UNAVAILABLE_NO_EXPLICIT_ARTIFACT_REVISION_TIMESTAMP",
        },
    },
    (FOMC_EXTRACTOR_ID, EXTRACTOR_VERSION): {
        "shape_contract_id": "federal_reserve.fomc_calendar.official_html.external_shape.v2",
        "required_fields": (
            "/html/head/meta[@property=og:url]", "/html/body/*/FOMC_Meetings",
            "/meeting/container", "/meeting/month", "/meeting/date",
            "/meeting/dated_document_link",
        ),
        "timestamp_extraction_rules": {
            "observed_at_utc": "/meeting/decision_date@START_OF_UTC_DAY",
            "known_at_utc": "VERIFIED_GIT_RECEIPT_ARTIFACT_CUTOFF",
            "published_at_utc": "/meeting/dated_document_link@DATE_TOKEN_START_OF_UTC_DAY",
            "revision_at_utc": "UNAVAILABLE_NO_EXPLICIT_ARTIFACT_REVISION_TIMESTAMP",
        },
    },
}


def _git_prefix(repository: Path) -> list[str]:
    return ["git", "--git-dir", str(repository)] if repository.is_file() or repository.suffix == ".git" else ["git", "-C", str(repository)]


def build_wave2_git_artifact_receipt(
    *, git_repository: str | Path, registry: contracts.TrustedVerifierRegistryV1,
    commit: str, artifact_path: str, artifact_schema_version: str,
    producer_version: str, artifact_cutoff_utc: str, verification_time_utc: str,
    branch_authority_ref: str, expected_git_blob_sha1: str | None = None,
    expected_byte_sha256: str | None = None,
) -> contracts.VerifiedProducerArtifactReceiptV1:
    """Bind a historical producer commit to a separately observed branch head."""
    repository = Path(git_repository).resolve()
    prefix = _git_prefix(repository)
    try:
        branch_head = subprocess.run(
            [*prefix, "rev-parse", "--verify", branch_authority_ref], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        ).stdout.strip()
        ancestry = subprocess.run(
            [*prefix, "merge-base", "--is-ancestor", commit, branch_head],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if ancestry.returncode != 0:
            raise ValueError("committed_artifact_not_reachable_from_observed_branch")
        consumed = subprocess.run(
            [*prefix, "show", f"{commit}:{artifact_path}"], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout
        blob = subprocess.run(
            [*prefix, "rev-parse", f"{commit}:{artifact_path}"], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        ).stdout.strip()
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
        artifact_cutoff_utc=artifact_cutoff_utc, evidence_refs=(),
        source_authority_class="official_public_data", resolved_repository=UPSTREAM_REPOSITORY,
        resolved_branch=UPSTREAM_BRANCH, resolved_commit=commit, resolved_artifact_path=artifact_path,
        branch_head_observed=branch_head, producer_commit_reachable_from_branch=True,
        verification_time_utc=verification_time_utc,
    )


def _utc_day(value: str, reason: str) -> str:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(reason) from error
    return datetime.combine(parsed, datetime.min.time(), timezone.utc).isoformat().replace("+00:00", "Z")


def _json_object(consumed: bytes, reason: str) -> Mapping[str, Any]:
    try:
        artifact = json.loads(consumed)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(reason) from error
    if not isinstance(artifact, Mapping):
        raise ValueError(reason)
    return artifact


def _decimal(value: Any, reason: str) -> str:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError(reason) from error
    if not parsed.is_finite():
        raise ValueError(reason)
    return str(value)


def _extract_treasury(consumed: bytes, selector: Mapping[str, str]):
    if set(selector) != {"record_date"}:
        raise ValueError("treasury_debt_selector_mismatch")
    artifact = _json_object(consumed, "treasury_debt_json_malformed")
    if not isinstance(artifact.get("data"), list) or not isinstance(artifact.get("meta"), Mapping) or not isinstance(artifact.get("links"), Mapping):
        raise ValueError("treasury_debt_shape_mismatch")
    meta = artifact["meta"]
    if not isinstance(meta.get("count"), int) or meta.get("count") != len(artifact["data"]):
        raise ValueError("treasury_debt_count_mismatch")
    if meta.get("dataTypes") != _TREASURY_DATA_TYPES:
        raise ValueError("treasury_debt_datatype_contract_mismatch")
    links = artifact["links"]
    if set(links) != {"self", "first", "prev", "next", "last"}:
        raise ValueError("treasury_debt_links_shape_mismatch")
    if any(not isinstance(links[key], str) or not links[key] for key in ("self", "first", "last")) or any(
        links[key] is not None and not isinstance(links[key], str) for key in ("prev", "next")
    ):
        raise ValueError("treasury_debt_links_shape_mismatch")
    selected = [row for row in artifact["data"] if isinstance(row, Mapping) and row.get("record_date") == selector["record_date"]]
    if len(selected) != 1:
        raise ValueError("treasury_debt_record_selector_not_unique")
    row = selected[0]
    fields = ("record_date", "debt_held_public_amt", "intragov_hold_amt", "tot_pub_debt_out_amt", "src_line_nbr", "record_fiscal_year", "record_fiscal_quarter", "record_calendar_year", "record_calendar_quarter", "record_calendar_month", "record_calendar_day")
    if any(row.get(field) in (None, "") for field in fields):
        raise ValueError("treasury_debt_required_field_missing")
    for field in ("debt_held_public_amt", "intragov_hold_amt", "tot_pub_debt_out_amt"):
        _decimal(row[field], "treasury_debt_numeric_value_invalid")
    observed = _utc_day(str(row["record_date"]), "treasury_debt_record_date_invalid")
    record = {field: row[field] for field in fields}
    record["meta_data_types"] = dict(meta["dataTypes"])
    record["links"] = dict(links)
    fields = (*fields, "meta_data_types", "links")
    return record, str(row["record_date"]), fields, {"observed_at_utc": observed, "known_at_utc": None, "published_at_utc": None, "revision_at_utc": None}


def _extract_bls(consumed: bytes, selector: Mapping[str, str]):
    if set(selector) != {"series_id", "year", "period"}:
        raise ValueError("bls_unemployment_selector_mismatch")
    artifact = _json_object(consumed, "bls_unemployment_json_malformed")
    if artifact.get("status") != "REQUEST_SUCCEEDED" or not isinstance(artifact.get("message"), list):
        raise ValueError("bls_unemployment_status_or_shape_mismatch")
    series_rows = artifact.get("Results", {}).get("series") if isinstance(artifact.get("Results"), Mapping) else None
    if not isinstance(series_rows, list):
        raise ValueError("bls_unemployment_shape_mismatch")
    series = [row for row in series_rows if isinstance(row, Mapping) and row.get("seriesID") == selector["series_id"]]
    if len(series) != 1 or not isinstance(series[0].get("data"), list):
        raise ValueError("bls_unemployment_series_selector_not_unique")
    rows = [row for row in series[0]["data"] if isinstance(row, Mapping) and row.get("year") == selector["year"] and row.get("period") == selector["period"]]
    if len(rows) != 1:
        raise ValueError("bls_unemployment_period_selector_not_unique")
    row = rows[0]
    match = re.fullmatch(r"M(0[1-9]|1[0-2])", str(row.get("period", "")))
    if not match or not re.fullmatch(r"\d{4}", str(row.get("year", ""))):
        raise ValueError("bls_unemployment_period_invalid")
    month = int(match.group(1))
    if row.get("periodName") != calendar.month_name[month]:
        raise ValueError("bls_unemployment_period_name_mismatch")
    _decimal(row.get("value"), "bls_unemployment_value_invalid")
    fields = ("seriesID", "year", "period", "periodName", "value", "latest", "footnotes")
    record = {"seriesID": series[0]["seriesID"], **{field: row.get(field) for field in fields if field != "seriesID"}}
    observed = _utc_day(f"{row['year']}-{month:02d}-01", "bls_unemployment_period_invalid")
    return record, f"{record['seriesID']}:{row['year']}:{row['period']}", fields, {"observed_at_utc": observed, "known_at_utc": None, "published_at_utc": None, "revision_at_utc": None}


def _extract_fomc(consumed: bytes, selector: Mapping[str, str]):
    if set(selector) != {"year", "month", "meeting_dates"}:
        raise ValueError("fomc_calendar_selector_mismatch")
    try:
        text = consumed.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("fomc_calendar_html_encoding_invalid") from error
    if 'property="og:url" content="https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"' not in text:
        raise ValueError("fomc_calendar_official_shape_mismatch")
    year = selector["year"]
    header = re.search(rf'<a id="\d+">{re.escape(year)} FOMC Meetings</a>', text)
    if header is None:
        raise ValueError("fomc_calendar_year_not_found")
    next_header = re.search(r'<a id="\d+">\d{4} FOMC Meetings</a>', text[header.end():])
    section = text[header.end():header.end() + next_header.start()] if next_header else text[header.end():]
    matches = [match for match in _FOMC_MEETING.finditer(section) if match.group(1) == selector["month"] and match.group(2).strip() == selector["meeting_dates"]]
    if len(matches) != 1 or selector["month"] not in _MONTHS:
        raise ValueError("fomc_calendar_meeting_selector_not_unique")
    day_text = re.sub(r"[^0-9-]", "", selector["meeting_dates"])
    try:
        end_day = int(day_text.split("-")[-1])
        decision_day = date(int(year), _MONTHS[selector["month"]], end_day)
    except ValueError as error:
        raise ValueError("fomc_calendar_meeting_date_invalid") from error
    container_starts = list(re.finditer(
        r'<div\b[^>]*class="[^"]*\bfomc-meeting\b[^"]*"[^>]*>',
        section[:matches[0].start()], re.IGNORECASE,
    ))
    if not container_starts:
        raise ValueError("fomc_calendar_meeting_container_missing")
    container_start = container_starts[-1].start()
    depth = 0
    container_end = None
    for tag in re.finditer(r"</?div\b[^>]*>", section[container_start:], re.IGNORECASE):
        depth += -1 if tag.group(0).startswith("</") else 1
        if depth == 0:
            container_end = container_start + tag.end()
            break
    if container_end is None:
        raise ValueError("fomc_calendar_meeting_container_malformed")
    container = section[container_start:container_end]
    if len(_FOMC_MEETING.findall(container)) != 1:
        raise ValueError("fomc_calendar_meeting_container_ambiguous")
    stamp = decision_day.strftime("%Y%m%d")
    # Bind the selected meeting to its canonical HTML statement.  The same
    # meeting container can legitimately include a statement PDF,
    # implementation note, press conference, longer-run strategy statement,
    # and minutes.  Those siblings must neither make selection ambiguous nor
    # allow a link from the next meeting container to satisfy this contract.
    statement_links = re.findall(
        rf'href="(/newsevents/pressreleases/monetary{stamp}a\.htm)"',
        container,
        re.IGNORECASE,
    )
    link = statement_links[0] if len(statement_links) == 1 else None
    if link is None:
        raise ValueError("fomc_calendar_dated_document_link_missing")
    fields = ("official_url", "year", "month", "meeting_dates", "decision_date", "dated_document_href")
    record = {"official_url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm", "year": year, "month": selector["month"], "meeting_dates": selector["meeting_dates"], "decision_date": decision_day.isoformat(), "dated_document_href": link}
    observed = _utc_day(decision_day.isoformat(), "fomc_calendar_meeting_date_invalid")
    return record, f"{year}:{selector['month']}:{selector['meeting_dates']}", fields, {"observed_at_utc": observed, "known_at_utc": None, "published_at_utc": observed, "revision_at_utc": None}


def _feature_value(feature_id: str, record: Mapping[str, Any], required_fields: Sequence[str], times: Mapping[str, str | None], evidence_ref: str, cutoff: str, rule: str) -> contracts.ExtractedFeatureValueV1:
    if feature_id == "evidence_completeness":
        value: float | None = sum(record.get(field) not in (None, "") for field in required_fields) / len(required_fields)
        availability, reason = (contracts.AvailabilityState.EXPLICIT_ZERO if value == 0.0 else contracts.AvailabilityState.AVAILABLE), None
    elif feature_id == "freshness":
        basis = times.get("published_at_utc") or times.get("known_at_utc") or times.get("revision_at_utc")
        if basis is None:
            value, availability, reason = None, contracts.AvailabilityState.UNAVAILABLE, "artifact_native_timestamp_unavailable"
        else:
            age = max(0.0, (contracts.parse_utc(cutoff) - contracts.parse_utc(basis)).total_seconds() / 3600.0)
            value, reason = max(0.0, 1.0 - age / 24.0), None
            availability = contracts.AvailabilityState.EXPLICIT_ZERO if value == 0.0 else contracts.AvailabilityState.AVAILABLE
    else:
        value, availability, reason = None, contracts.AvailabilityState.UNAVAILABLE, "feature_derivation_not_supported_by_extractor"
    draft = contracts.ExtractedFeatureValueV1(feature_id, availability, value, (evidence_ref,), rule, reason, "")
    result = replace(draft, logical_hash=draft.calculated_logical_hash())
    if result.validate():
        raise ValueError("invalid_wave2_feature_value")
    return result


def _narrow(requested: str | None, derived: str, ranks: Mapping[str, int], kind: str) -> str:
    if requested is None or requested == derived:
        return derived
    if requested not in ranks:
        raise ValueError(f"unknown_requested_{kind}_state")
    if ranks[requested] >= ranks[derived]:
        raise ValueError(f"caller_{kind}_upgrade_forbidden")
    return requested


def extract_wave2_artifact_evidence(
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
        raise ValueError("unsupported_wave2_extractor")
    if sha256(consumed_bytes).hexdigest() != receipt.consumed_byte_sha256:
        raise ValueError("extractor_consumed_bytes_receipt_mismatch")
    if receipt.repository not in extractor.supported_repositories or not any(fnmatch(receipt.artifact_path, pattern) for pattern in extractor.supported_path_patterns):
        raise ValueError("extractor_source_binding_mismatch")
    if receipt.artifact_schema_version not in extractor.supported_artifact_schema_versions or receipt.producer_version != extractor.shape_contract_id:
        raise ValueError("extractor_schema_or_shape_contract_mismatch")
    if evidence_scope not in extractor.supported_evidence_scopes or any(feature not in extractor.supported_feature_ids for feature in feature_targets):
        raise ValueError("extractor_scope_or_feature_unsupported")
    extraction = {TREASURY_EXTRACTOR_ID: _extract_treasury, BLS_EXTRACTOR_ID: _extract_bls, FOMC_EXTRACTOR_ID: _extract_fomc}[extractor_id]
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
        raise ValueError("invalid_wave2_extracted_evidence_record")
    features = tuple(_feature_value(feature, record, fields, times, evidence_ref, decision_cutoff_utc, extractor.value_derivation_rules[feature]) for feature in feature_targets)
    return extracted, features
