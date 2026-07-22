"""Bounded, no-write production adapters for three official public artifacts.

The adapters consume bytes already bound to portable historical Git receipts.
They do not fetch, publish, dispatch, inspect credentials, or grant authority.
"""
from __future__ import annotations

import csv
from dataclasses import replace
from datetime import date, datetime, timezone
from fnmatch import fnmatch
from hashlib import sha256
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
from typing import Any, Mapping, Sequence
from xml.etree import ElementTree as ET
import zipfile

from live_contentops import content_intelligence_contracts_v2 as contracts


UPSTREAM_REPOSITORY = "fatcat2109/Headline-Raw-data-json"
UPSTREAM_BRANCH = "main"
UPSTREAM_PINNED_COMMIT = "251ba1804c5d495884343adad6be0d0e6ba8c121"
VERIFIER_ID = "contentops.production_external_exact_git_verifier"
VERIFIER_VERSION = "v1"
CFTC_LAYOUT_REL_PATH = Path("live_contentops/cftc_legacy_futures_only_column_layout_v1.json")

TREASURY_SCHEMA = "external.us_treasury_daily_yield_curve_atom.v1"
CFTC_SCHEMA = "external.cftc_legacy_futures_only_cot.v1"
H41_SCHEMA = "external.federal_reserve_h41_zip.v1"

TREASURY_EXTRACTOR_ID = "contentops.treasury_daily_yield_curve_atom_extractor"
CFTC_EXTRACTOR_ID = "contentops.cftc_legacy_futures_only_cot_extractor"
H41_EXTRACTOR_ID = "contentops.federal_reserve_h41_zip_structure_extractor"

TREASURY_PATH = "data/audit/data_sufficiency/task_300aa_304z/raw_archive/treasury_daily_yield_curve/batch_e_treasury_daily_yield_curve_20260606T154421Z_e34b3214/raw_response.bin"
CFTC_PATH = "data/audit/data_sufficiency/task_392aa_396z/raw_archive/cftc_cot/cftc_cot_20260607T140054Z/raw_response.bin"
H41_PATH = "data/audit/data_sufficiency/task_404sidea_408sidea/raw_archive/fed_board_h41/h41_4f35601dfa72.zip"

PINNED_ARTIFACTS: Mapping[str, Mapping[str, Any]] = {
    TREASURY_EXTRACTOR_ID: {"path": TREASURY_PATH, "git_blob_sha1": "4c6cb14c58b3e16422eca115fecb1d883a98d79f", "byte_sha256": "b2eebbbe396380fb3872e031e8b759088bb41c746ce716773800506c94c9908f", "byte_length": 385873},
    CFTC_EXTRACTOR_ID: {"path": CFTC_PATH, "git_blob_sha1": "d76fafa828839ce774626ee2654b6477904e5260", "byte_sha256": "286bda7d111c7d7eb3756a919a6489ddf310d42a108b2c154408093e706aa02e", "byte_length": 415757},
    H41_EXTRACTOR_ID: {"path": H41_PATH, "git_blob_sha1": "fd52a7682725d15aa5d997201c52ebae4e291cce", "byte_sha256": "4f35601dfa72aaed42c6584f538a613392fa7f03f1f79e953e7aec3a37c15f7f", "byte_length": 8952712},
}

ATOM_NS = "http://www.w3.org/2005/Atom"
ODATA_METADATA_NS = "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"
ODATA_DATA_NS = "http://schemas.microsoft.com/ado/2007/08/dataservices"
XSD_NS = "http://www.w3.org/2001/XMLSchema"
SDMX_MESSAGE_NS = "http://www.SDMX.org/resources/SDMXML/schemas/v1_0/message"
H41_SERIES_NS = "http://www.federalreserve.gov/structure/compact/H41_H41"
H41_COMMON_NS = "http://www.federalreserve.gov/structure/compact/common"
TREASURY_MATURITIES = (
    "BC_3MONTH", "BC_6MONTH", "BC_1YEAR", "BC_2YEAR", "BC_3YEAR",
    "BC_5YEAR", "BC_7YEAR", "BC_10YEAR", "BC_30YEAR", "BC_30YEARDISPLAY",
)
H41_ALLOWED_MEMBERS = {
    "H41_H41.xsd": 1 * 1024 * 1024,
    "H41_data.xml": 125 * 1024 * 1024,
    "H41_struct.xml": 1 * 1024 * 1024,
    "frb_common.xsd": 1 * 1024 * 1024,
}
H41_MAX_ENTRIES = 8
H41_MAX_COMPRESSED_TOTAL = 16 * 1024 * 1024
H41_MAX_UNCOMPRESSED_TOTAL = 128 * 1024 * 1024
H41_MAX_COMPRESSION_RATIO = 25.0
STREAM_CHUNK_BYTES = 1024 * 1024
_FORBIDDEN_XML = re.compile(br"<!\s*(?:DOCTYPE|ENTITY)\b", re.IGNORECASE)


def _git_prefix(repository: Path) -> list[str]:
    return ["git", "--git-dir", str(repository)] if repository.is_file() or repository.suffix == ".git" else ["git", "-C", str(repository)]


def build_production_git_artifact_receipt(
    *, git_repository: str | Path, registry: contracts.TrustedVerifierRegistryV1,
    commit: str, artifact_path: str, artifact_schema_version: str,
    producer_version: str, artifact_cutoff_utc: str, verification_time_utc: str,
    branch_authority_ref: str = "refs/remotes/origin/main",
    expected_git_blob_sha1: str | None = None, expected_byte_sha256: str | None = None,
) -> contracts.VerifiedProducerArtifactReceiptV1:
    """Resolve a reachable historical object and bind its exact bytes and blob."""
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
            raise ValueError("committed_artifact_not_reachable_from_branch")
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


def load_cftc_layout_contract(repo_root: str | Path) -> Mapping[str, Any]:
    path = Path(repo_root).resolve() / CFTC_LAYOUT_REL_PATH
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("cftc_layout_contract_unavailable") from error
    expected = contracts.logical_hash({key: value for key, value in raw.items() if key != "contract_logical_hash"})
    if raw.get("contract_logical_hash") != expected:
        raise ValueError("cftc_layout_contract_logical_hash_mismatch")
    columns = raw.get("ordered_columns")
    if (
        raw.get("schema_version") != "contentops.cftc_legacy_futures_only_column_layout.v1"
        or raw.get("contract_version") != "contentops.cftc_legacy_futures_only_column_layout.v1.0.0"
        or raw.get("upstream_commit") != UPSTREAM_PINNED_COMMIT
        or not isinstance(columns, list) or len(columns) != 129 or len(set(columns)) != 129
        or raw.get("field_count") != 129
        or raw.get("numeric_truth_granted") is not False
        or raw.get("authority_upgrade_granted") is not False
        or raw.get("permission_upgrade_granted") is not False
    ):
        raise ValueError("cftc_layout_contract_invalid")
    return raw


def _reject_forbidden_xml(data: bytes, *, allowed_doctype: bytes | None = None) -> None:
    inspected = data
    if allowed_doctype is not None:
        if data.count(allowed_doctype) > 1:
            raise ValueError("xml_dtd_or_entity_forbidden")
        inspected = data.replace(allowed_doctype, b"", 1)
    if _FORBIDDEN_XML.search(inspected):
        raise ValueError("xml_dtd_or_entity_forbidden")


def _parse_xml(data: bytes, error_code: str, *, allowed_doctype: bytes | None = None) -> ET.Element:
    _reject_forbidden_xml(data, allowed_doctype=allowed_doctype)
    try:
        return ET.fromstring(data)
    except ET.ParseError as error:
        raise ValueError(error_code) from error


def _utc_from_day(value: str, error_code: str) -> str:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(error_code) from error
    return datetime.combine(parsed, datetime.min.time(), timezone.utc).isoformat().replace("+00:00", "Z")


def _extract_treasury(consumed: bytes, selector: Mapping[str, str]) -> tuple[Mapping[str, Any], str, tuple[str, ...], Mapping[str, str | None]]:
    if set(selector) != {"record_date", "maturity"}:
        raise ValueError("treasury_selector_mismatch")
    maturity = selector["maturity"]
    if maturity not in TREASURY_MATURITIES:
        raise ValueError("treasury_maturity_selector_unsupported")
    root = _parse_xml(consumed, "treasury_xml_malformed")
    if root.tag != f"{{{ATOM_NS}}}feed":
        raise ValueError("treasury_atom_feed_namespace_mismatch")
    updated = root.findtext(f"{{{ATOM_NS}}}updated")
    try:
        contracts.parse_utc(str(updated), field_name="treasury_feed_updated")
    except ValueError as error:
        raise ValueError("treasury_feed_updated_invalid") from error
    selected: list[Mapping[str, str | None]] = []
    seen_keys: set[tuple[str, str]] = set()
    entries = root.findall(f"{{{ATOM_NS}}}entry")
    if not entries:
        raise ValueError("treasury_atom_feed_empty")
    for entry in entries:
        props = entry.find(f"{{{ATOM_NS}}}content/{{{ODATA_METADATA_NS}}}properties")
        if props is None:
            raise ValueError("treasury_odata_properties_missing")
        values = {child.tag.removeprefix(f"{{{ODATA_DATA_NS}}}"): child.text for child in props}
        if any(not child.tag.startswith(f"{{{ODATA_DATA_NS}}}") for child in props):
            raise ValueError("treasury_odata_property_namespace_mismatch")
        if values.get("Id") in (None, "") or values.get("NEW_DATE") in (None, ""):
            raise ValueError("treasury_required_field_missing")
        try:
            native = datetime.strptime(str(values["NEW_DATE"]), "%Y-%m-%dT%H:%M:%S")
        except ValueError as error:
            raise ValueError("treasury_record_date_invalid") from error
        key = (str(values["NEW_DATE"]), str(values["Id"]))
        if key in seen_keys:
            raise ValueError("treasury_duplicate_record_identity")
        seen_keys.add(key)
        if native.date().isoformat() == selector["record_date"]:
            if values.get(maturity) in (None, ""):
                raise ValueError("treasury_selected_maturity_missing")
            selected.append({
                "Id": values["Id"], "NEW_DATE": values["NEW_DATE"],
                "maturity": maturity, "yield_value": values[maturity],
                "feed_updated_utc": updated,
            })
    if len(selected) != 1:
        raise ValueError("treasury_record_selector_not_unique")
    record = selected[0]
    observed = _utc_from_day(selector["record_date"], "treasury_record_date_invalid")
    fields = ("Id", "NEW_DATE", "maturity", "yield_value", "feed_updated_utc")
    return record, f"{selector['record_date']}:{maturity}", fields, {
        "observed_at_utc": observed, "known_at_utc": str(updated),
        "published_at_utc": str(updated), "revision_at_utc": None,
    }


def _extract_cftc(consumed: bytes, selector: Mapping[str, str], repo_root: str | Path) -> tuple[Mapping[str, Any], str, tuple[str, ...], Mapping[str, str | None]]:
    if set(selector) != {"contract_market_code", "report_date"}:
        raise ValueError("cftc_selector_mismatch")
    layout = load_cftc_layout_contract(repo_root)
    columns = tuple(layout["ordered_columns"])
    try:
        text = consumed.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(text), strict=True))
    except (UnicodeDecodeError, csv.Error) as error:
        raise ValueError("cftc_csv_malformed") from error
    if not rows:
        raise ValueError("cftc_csv_empty")
    selected: list[Mapping[str, str]] = []
    for index, row in enumerate(rows):
        if len(row) != len(columns):
            raise ValueError(f"cftc_row_width_mismatch:{index}")
        mapped = dict(zip(columns, row, strict=True))
        full_date = mapped["as_of_date_in_form_yyyy_mm_dd"].strip()
        compact = mapped["as_of_date_in_form_yymmdd"].strip()
        try:
            parsed = date.fromisoformat(full_date)
        except ValueError as error:
            raise ValueError(f"cftc_report_date_invalid:{index}") from error
        if parsed.strftime("%y%m%d") != compact:
            raise ValueError(f"cftc_compact_date_mismatch:{index}")
        if (
            mapped["cftc_contract_market_code"].strip() == selector["contract_market_code"]
            and full_date == selector["report_date"]
        ):
            selected.append(mapped)
    if len(selected) != 1:
        raise ValueError("cftc_record_selector_not_unique")
    record = selected[0]
    fields = (
        "market_and_exchange_names", "as_of_date_in_form_yymmdd",
        "as_of_date_in_form_yyyy_mm_dd", "cftc_contract_market_code",
        "cftc_market_code_in_initials", "cftc_region_code", "cftc_commodity_code",
        "open_interest_all",
    )
    observed = _utc_from_day(selector["report_date"], "cftc_report_date_invalid")
    return record, f"{selector['contract_market_code']}:{selector['report_date']}", fields, {
        "observed_at_utc": observed, "known_at_utc": None,
        "published_at_utc": None, "revision_at_utc": None,
    }


def _safe_zip_infos(archive: zipfile.ZipFile) -> Mapping[str, zipfile.ZipInfo]:
    infos = archive.infolist()
    if len(infos) > H41_MAX_ENTRIES:
        raise ValueError("h41_zip_entry_count_exceeded")
    normalized: dict[str, zipfile.ZipInfo] = {}
    compressed_total = 0
    uncompressed_total = 0
    for info in infos:
        name = info.filename
        path = PurePosixPath(name)
        mode = (info.external_attr >> 16) & 0xFFFF
        if (
            not name or "\\" in name or name.startswith(("/", "\\"))
            or ":" in name or path.is_absolute() or ".." in path.parts
            or str(path) != name or info.is_dir() or stat.S_ISLNK(mode)
        ):
            raise ValueError("h41_zip_unsafe_member_path")
        if name in normalized:
            raise ValueError("h41_zip_duplicate_member")
        if name not in H41_ALLOWED_MEMBERS:
            raise ValueError("h41_zip_member_not_allowlisted")
        if info.flag_bits & 0x1:
            raise ValueError("h41_zip_encrypted_member_forbidden")
        if info.file_size > H41_ALLOWED_MEMBERS[name]:
            raise ValueError("h41_zip_member_uncompressed_limit_exceeded")
        ratio = info.file_size / max(1, info.compress_size)
        if ratio > H41_MAX_COMPRESSION_RATIO:
            raise ValueError("h41_zip_compression_ratio_exceeded")
        compressed_total += info.compress_size
        uncompressed_total += info.file_size
        normalized[name] = info
    if set(normalized) != set(H41_ALLOWED_MEMBERS):
        raise ValueError("h41_zip_member_allowlist_mismatch")
    if compressed_total > H41_MAX_COMPRESSED_TOTAL:
        raise ValueError("h41_zip_compressed_total_exceeded")
    if uncompressed_total > H41_MAX_UNCOMPRESSED_TOTAL:
        raise ValueError("h41_zip_uncompressed_total_exceeded")
    return normalized


def _read_bounded_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo, total: list[int]) -> bytes:
    chunks: list[bytes] = []
    size = 0
    try:
        with archive.open(info, "r") as stream:
            while True:
                chunk = stream.read(STREAM_CHUNK_BYTES)
                if not chunk:
                    break
                size += len(chunk)
                total[0] += len(chunk)
                if size > H41_ALLOWED_MEMBERS[info.filename]:
                    raise ValueError("h41_zip_stream_member_limit_exceeded")
                if total[0] > H41_MAX_UNCOMPRESSED_TOTAL:
                    raise ValueError("h41_zip_stream_total_limit_exceeded")
                chunks.append(chunk)
    except (RuntimeError, zipfile.BadZipFile) as error:
        raise ValueError("h41_zip_member_integrity_failure") from error
    if size != info.file_size:
        raise ValueError("h41_zip_member_size_mismatch")
    return b"".join(chunks)


def _validate_xsd(data: bytes, target_namespace: str, required_names: set[str]) -> Mapping[str, Any]:
    root = _parse_xml(data, "h41_xsd_malformed", allowed_doctype=b"<!DOCTYPE xs:schema>")
    if root.tag != f"{{{XSD_NS}}}schema" or root.attrib.get("targetNamespace") != target_namespace:
        raise ValueError("h41_xsd_namespace_mismatch")
    names = {
        element.attrib["name"] for element in root.iter()
        if element.tag in {f"{{{XSD_NS}}}element", f"{{{XSD_NS}}}attribute"} and "name" in element.attrib
    }
    if not required_names <= names:
        raise ValueError("h41_xsd_required_declaration_missing")
    return {"target_namespace": target_namespace, "declaration_names": sorted(names), "byte_sha256": sha256(data).hexdigest()}


def _extract_h41(consumed: bytes, selector: Mapping[str, str]) -> tuple[Mapping[str, Any], str, tuple[str, ...], Mapping[str, str | None]]:
    if selector != {"dataset_id": "H41"}:
        raise ValueError("h41_selector_mismatch")
    try:
        archive = zipfile.ZipFile(io.BytesIO(consumed))
    except zipfile.BadZipFile as error:
        raise ValueError("h41_zip_malformed") from error
    with archive:
        infos = _safe_zip_infos(archive)
        total = [0]
        members = {name: _read_bounded_member(archive, infos[name], total) for name in sorted(infos)}
    h41_xsd = _validate_xsd(members["H41_H41.xsd"], H41_SERIES_NS, {"Series", "CATEGORY", "COMPONENT", "DISTRIBUTION", "SERIESTYPE", "SUBCATEGORY"})
    common_xsd = _validate_xsd(members["frb_common.xsd"], H41_COMMON_NS, {"DataSet", "Obs", "OBS_STATUS", "OBS_VALUE", "TIME_PERIOD", "Series"})
    structure = _parse_xml(members["H41_struct.xml"], "h41_structure_xml_malformed")
    if structure.tag != f"{{{SDMX_MESSAGE_NS}}}Structure":
        raise ValueError("h41_structure_root_mismatch")
    structure_text = {node.tag.rsplit("}", 1)[-1]: (node.text or "").strip() for node in structure.iter()}
    if structure_text.get("ID") != "H41":
        raise ValueError("h41_structure_dataset_id_mismatch")
    data_bytes = members["H41_data.xml"]
    _reject_forbidden_xml(data_bytes)
    series_count = 0
    observation_count = 0
    latest_day: date | None = None
    first_root: str | None = None
    try:
        for event, element in ET.iterparse(io.BytesIO(data_bytes), events=("start", "end")):
            if first_root is None:
                first_root = element.tag
            local = element.tag.rsplit("}", 1)[-1]
            if event == "start" and local == "Series":
                series_count += 1
                required = {"SERIES_NAME", "FREQ", "CATEGORY", "COMPONENT", "UNIT", "UNIT_MULT"}
                if not required <= set(element.attrib) or any(element.attrib[name] == "" for name in required):
                    raise ValueError("h41_series_structure_malformed")
            elif event == "start" and local == "Obs":
                observation_count += 1
                if not {"OBS_STATUS", "OBS_VALUE", "TIME_PERIOD"} <= set(element.attrib):
                    raise ValueError("h41_observation_structure_malformed")
                try:
                    current_day = date.fromisoformat(element.attrib["TIME_PERIOD"])
                except ValueError as error:
                    raise ValueError("h41_observation_time_invalid") from error
                if latest_day is None or current_day > latest_day:
                    latest_day = current_day
            if event == "end":
                element.clear()
    except ET.ParseError as error:
        raise ValueError("h41_data_xml_malformed") from error
    if first_root != f"{{{SDMX_MESSAGE_NS}}}MessageGroup" or not series_count or not observation_count or latest_day is None:
        raise ValueError("h41_data_structure_incomplete")
    member_inventory = {
        name: {
            "compressed_size": infos[name].compress_size,
            "uncompressed_size": infos[name].file_size,
            "crc32": f"{infos[name].CRC:08x}",
            "byte_sha256": sha256(members[name]).hexdigest(),
        }
        for name in sorted(infos)
    }
    record = {
        "dataset_id": "H41", "message_root": first_root,
        "structure_name": structure_text.get("Name"),
        "series_count": series_count, "observation_count": observation_count,
        "latest_time_period": latest_day.isoformat(), "member_inventory": member_inventory,
        "h41_xsd_target_namespace": h41_xsd["target_namespace"],
        "common_xsd_target_namespace": common_xsd["target_namespace"],
        "numeric_observation_values_quarantined": True,
        "numeric_truth_granted": False,
    }
    fields = (
        "dataset_id", "message_root", "series_count", "observation_count",
        "latest_time_period", "member_inventory", "numeric_observation_values_quarantined",
        "numeric_truth_granted",
    )
    observed = _utc_from_day(latest_day.isoformat(), "h41_observation_time_invalid")
    return record, f"H41:{latest_day.isoformat()}:STRUCTURE_ONLY", fields, {
        "observed_at_utc": observed, "known_at_utc": None,
        "published_at_utc": None, "revision_at_utc": None,
    }


def _narrow_state(requested: str | None, derived: str, ranks: Mapping[str, int], kind: str) -> str:
    if requested is None or requested == derived:
        return derived
    if requested not in ranks:
        raise ValueError(f"unknown_requested_{kind}_state")
    if ranks[requested] >= ranks[derived]:
        raise ValueError(f"caller_{kind}_upgrade_forbidden")
    return requested


def _feature_value(
    feature_id: str, record: Mapping[str, Any], required_fields: Sequence[str],
    times: Mapping[str, str | None], evidence_ref: str, decision_cutoff_utc: str,
    derivation_contract: str,
) -> contracts.ExtractedFeatureValueV1:
    if feature_id == "evidence_completeness":
        present = sum(record.get(field) not in (None, "") for field in required_fields)
        value: float | None = present / len(required_fields)
        availability = contracts.AvailabilityState.EXPLICIT_ZERO if value == 0.0 else contracts.AvailabilityState.AVAILABLE
        reason = None
    elif feature_id == "freshness":
        basis = times.get("known_at_utc") or times.get("published_at_utc") or times.get("observed_at_utc")
        if basis is None:
            value, availability, reason = None, contracts.AvailabilityState.UNAVAILABLE, "artifact_native_timestamp_unavailable"
        else:
            age = max(0.0, (contracts.parse_utc(decision_cutoff_utc) - contracts.parse_utc(basis)).total_seconds() / 3600.0)
            value = max(0.0, 1.0 - age / 24.0)
            availability = contracts.AvailabilityState.EXPLICIT_ZERO if value == 0.0 else contracts.AvailabilityState.AVAILABLE
            reason = None
    else:
        value, availability, reason = None, contracts.AvailabilityState.UNAVAILABLE, "feature_derivation_not_supported_by_extractor"
    values = {
        "feature_id": feature_id, "availability": availability, "value": value,
        "evidence_refs": (evidence_ref,), "derivation_contract": derivation_contract,
        "reason_code": reason, "logical_hash": "",
    }
    draft = contracts.ExtractedFeatureValueV1(**values)
    result = replace(draft, logical_hash=draft.calculated_logical_hash())
    blockers = result.validate()
    if blockers:
        raise ValueError("invalid_extracted_feature_value:" + ",".join(blockers))
    return result


def extract_production_artifact_evidence(
    consumed_bytes: bytes, *, receipt: contracts.VerifiedProducerArtifactReceiptV1,
    registry: contracts.ArtifactEvidenceExtractorRegistryV1, extractor_id: str,
    extractor_version: str, selector: Mapping[str, str], feature_targets: Sequence[str],
    decision_cutoff_utc: str, repo_root: str | Path,
    evidence_roles: Sequence[contracts.EvidenceRole] | None = None,
    evidence_scope: contracts.EvidenceScope = contracts.EvidenceScope.FEATURE_SPECIFIC,
    authority_state: str | None = None, permission_state: str | None = None,
) -> tuple[contracts.ExtractedEvidenceRecordV1, tuple[contracts.ExtractedFeatureValueV1, ...]]:
    """Validate source shape and emit byte-derived context-only evidence."""
    if registry.validate():
        raise ValueError("invalid_evidence_extractor_registry")
    extractor = registry.resolve(extractor_id, extractor_version)
    if extractor is None or not extractor.enabled:
        raise ValueError("unsupported_or_disabled_extractor")
    if extractor_id not in {TREASURY_EXTRACTOR_ID, CFTC_EXTRACTOR_ID, H41_EXTRACTOR_ID}:
        raise ValueError("unsupported_production_extractor")
    if sha256(consumed_bytes).hexdigest() != receipt.consumed_byte_sha256:
        raise ValueError("extractor_consumed_bytes_receipt_mismatch")
    if receipt.repository not in extractor.supported_repositories:
        raise ValueError("extractor_repository_mismatch")
    if not any(fnmatch(receipt.artifact_path, pattern) for pattern in extractor.supported_path_patterns):
        raise ValueError("extractor_path_mismatch")
    if receipt.artifact_schema_version not in extractor.supported_artifact_schema_versions:
        raise ValueError("extractor_schema_mismatch")
    if receipt.producer_version != extractor.shape_contract_id:
        raise ValueError("external_shape_contract_producer_mismatch")
    if evidence_scope not in extractor.supported_evidence_scopes:
        raise ValueError("extractor_evidence_scope_unsupported")
    if any(feature not in extractor.supported_feature_ids for feature in feature_targets):
        raise ValueError("extractor_feature_target_unsupported")
    if extractor_id == TREASURY_EXTRACTOR_ID:
        record, record_key, source_fields, times = _extract_treasury(consumed_bytes, selector)
    elif extractor_id == CFTC_EXTRACTOR_ID:
        record, record_key, source_fields, times = _extract_cftc(consumed_bytes, selector, repo_root)
    else:
        record, record_key, source_fields, times = _extract_h41(consumed_bytes, selector)
    cutoff = contracts.parse_utc(decision_cutoff_utc, field_name="decision_cutoff_utc")
    for name, timestamp in times.items():
        if timestamp and contracts.parse_utc(timestamp, field_name=name) > cutoff:
            raise ValueError(f"internal_future_timestamp:{name}")
    derived_roles = (contracts.EvidenceRole.FEATURE_SUPPORT,)
    selected_roles = derived_roles if evidence_roles is None else tuple(evidence_roles)
    if any(role not in derived_roles for role in selected_roles):
        raise ValueError("caller_evidence_role_addition_forbidden")
    selected_authority = _narrow_state(authority_state, "OFFICIAL_VERIFIED", contracts.AUTHORITY_STATE_RANK, "authority")
    selected_permission = _narrow_state(permission_state, "CONTEXT_ONLY", contracts.PERMISSION_STATE_RANK, "permission")
    reasons = ["context_only", "external_official_context_only"]
    if selected_authority != "OFFICIAL_VERIFIED":
        reasons.append("caller_authority_narrowed")
    if selected_permission != "CONTEXT_ONLY":
        reasons.append("caller_permission_narrowed")
    record_hash = contracts.logical_hash(record)
    evidence_material = {
        "producer_receipt_logical_hash": receipt.logical_hash,
        "extractor_id": extractor.extractor_id, "extractor_version": extractor.extractor_version,
        "record_selector": dict(sorted(selector.items())), "record_key": record_key,
        "extracted_record_hash": record_hash, "derivation_rule": extractor.evidence_ref_derivation_rule,
    }
    evidence_ref = "extracted:" + contracts.logical_hash(evidence_material)[:32]
    values = {
        "producer_receipt_id": receipt.receipt_id,
        "producer_receipt_logical_hash": receipt.logical_hash,
        "extractor_id": extractor.extractor_id, "extractor_version": extractor.extractor_version,
        "record_selector": contracts.canonical_json(dict(sorted(selector.items()))),
        "record_key": record_key, "extracted_record_hash": record_hash,
        "evidence_ref": evidence_ref, "source_fields_used": tuple(source_fields),
        "observed_at_utc": times["observed_at_utc"], "known_at_utc": times["known_at_utc"],
        "published_at_utc": times["published_at_utc"], "revision_at_utc": times["revision_at_utc"],
        "cutoff_utc": receipt.artifact_cutoff_utc, "evidence_roles": selected_roles,
        "evidence_scope": evidence_scope, "feature_targets": tuple(feature_targets),
        "derivation_contract": extractor.implementation_contract_id,
        "authority_state": selected_authority, "permission_state": selected_permission,
        "source_authority_class": receipt.source_authority_class,
        "artifact_schema_version": receipt.artifact_schema_version,
        "schema_authority": extractor.schema_authority, "artifact_schema_verified": True,
        "producer_version_verified": True, "internal_logical_hash_verified": None,
        "extraction_logical_hash": "", "authority_derivation_rule": extractor.authority_derivation_rule,
        "permission_derivation_rule": extractor.permission_derivation_rule,
        "role_derivation_rule": extractor.role_derivation_rule,
        "qualification_status": "NOT_QUALIFYING_GOVERNED",
        "qualification_reason_codes": tuple(reasons),
    }
    draft = contracts.ExtractedEvidenceRecordV1(**values)
    extracted = replace(draft, extraction_logical_hash=draft.calculated_logical_hash())
    blockers = extracted.validate()
    if blockers:
        raise ValueError("invalid_extracted_evidence_record:" + ",".join(blockers))
    feature_values = tuple(_feature_value(
        feature, record, source_fields, times, evidence_ref, decision_cutoff_utc,
        extractor.value_derivation_rules[feature],
    ) for feature in feature_targets)
    return extracted, feature_values
