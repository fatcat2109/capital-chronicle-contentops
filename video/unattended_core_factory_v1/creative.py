from __future__ import annotations

import json
import re
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


SOURCE_FILES = frozenset({"src/index.tsx", "src/Root.tsx", "src/Short.tsx"})
FORBIDDEN_SOURCE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bprocess\s*\.\s*env\b", "env_read"),
    (r"\bimport\s*\(\s*[^'\"]", "dynamic_import"),
    (r"\brequire\s*\(", "commonjs_require"),
    (r"\bfetch\s*\(", "network_fetch"),
    (r"\bXMLHttpRequest\b", "network_xhr"),
    (r"\bWebSocket\b", "network_websocket"),
    (r"\bchild_process\b", "child_process"),
    (r"\bnode:fs\b|\bfrom\s+['\"]fs['\"]", "filesystem"),
    (r"\bnode:os\b|\bfrom\s+['\"]os['\"]", "os_access"),
    (r"\bnode:path\b|\bfrom\s+['\"]path['\"]", "path_access"),
    (r"\bexec(?:File|Sync)?\s*\(|\bspawn(?:Sync)?\s*\(", "shell_execution"),
    (r"https?://", "render_time_network_literal"),
    (r"\bnpm\b|\byarn\b|\bpnpm\b", "package_install"),
    (r"\bselenium\b|\bplaywright\b|\bpuppeteer\b", "browser_access"),
    (r"\btiktok\b|\byoutube\b|\binstagram\b|\bfacebook\b", "platform_operation"),
)
ALLOWED_IMPORTS = frozenset({"react", "remotion"})


class CreativeContractError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def hash_value(value: Any) -> str:
    if isinstance(value, bytes):
        return sha256(value).hexdigest()
    if isinstance(value, str):
        return sha256(value.encode("utf-8")).hexdigest()
    return sha256(canonical_bytes(value)).hexdigest()


def hash_file(path: str | Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json_text(raw: str) -> Any:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def _anchor_map(packet: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {str(item["anchor_id"]): item for item in packet.get("anchors", [])}


def _analysis_map(packet: Mapping[str, Any]) -> dict[str, str]:
    return {
        str(item["analysis_id"]): str(item["statement"])
        for item in packet.get("permitted_analysis", [])
    }


def validate_input_packet(packet: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "schema",
        "story_id",
        "authority_version",
        "anchors",
        "permitted_analysis",
        "forbidden_claims",
        "rights_assets",
        "hard_boundaries",
    }
    missing = sorted(required - set(packet))
    if missing:
        raise CreativeContractError(f"input_packet_missing:{','.join(missing)}")
    boundaries = packet["hard_boundaries"]
    for key in (
        "public_write_authority",
        "v1_read_authority",
        "v1_mutation_authority",
        "scheduler_mutation_authority",
    ):
        if boundaries.get(key) is not False:
            raise CreativeContractError(f"hard_boundary_must_be_false:{key}")
    anchors = _anchor_map(packet)
    if not anchors or len(anchors) != len(packet["anchors"]):
        raise CreativeContractError("anchor_identity_invalid")
    for anchor_id, anchor in anchors.items():
        if not anchor.get("statement") or not anchor.get("source_ref"):
            raise CreativeContractError(f"anchor_incomplete:{anchor_id}")
    for asset in packet["rights_assets"]:
        if not re.fullmatch(r"[0-9a-f]{64}", str(asset.get("sha256", ""))):
            raise CreativeContractError(f"asset_hash_invalid:{asset.get('asset_id')}")
        path = PurePosixPath(str(asset.get("relative_path", "")))
        if path.is_absolute() or ".." in path.parts:
            raise CreativeContractError(f"asset_path_invalid:{asset.get('asset_id')}")
    return {
        "result": "PASS_GOVERNED_INPUT",
        "anchor_count": len(anchors),
        "asset_count": len(packet["rights_assets"]),
        "input_packet_hash": hash_value(packet),
    }


def validate_editor_artifact(
    artifact: Mapping[str, Any], packet: Mapping[str, Any]
) -> dict[str, Any]:
    if artifact.get("schema") != "contentops.v2.codex_job_editorial.v1":
        raise CreativeContractError("editor_schema_invalid")
    duration = float(artifact.get("duration_seconds", 0))
    if not 30 <= duration <= 60:
        raise CreativeContractError("editor_duration_outside_short_contract")
    anchors = _anchor_map(packet)
    analysis = _analysis_map(packet)
    segments = artifact.get("narration_segments")
    if not isinstance(segments, list) or not segments:
        raise CreativeContractError("editor_narration_segments_invalid")
    seen: set[str] = set()
    fact_count = 0
    for segment in segments:
        segment_id = str(segment.get("segment_id", ""))
        if not segment_id or segment_id in seen:
            raise CreativeContractError("editor_segment_identity_invalid")
        seen.add(segment_id)
        kind = str(segment.get("kind", ""))
        text = str(segment.get("text", "")).strip()
        anchor_ids = [str(value) for value in segment.get("anchor_ids", [])]
        analysis_id = str(segment.get("analysis_id", ""))
        if not text:
            raise CreativeContractError(f"editor_empty_segment:{segment_id}")
        if kind == "FACT":
            fact_count += 1
            if len(anchor_ids) != 1 or anchor_ids[0] not in anchors:
                raise CreativeContractError(f"editor_fact_binding_invalid:{segment_id}")
            if text != str(anchors[anchor_ids[0]]["statement"]):
                raise CreativeContractError(f"editor_fact_not_exact_anchor:{segment_id}")
        elif kind == "ANALYSIS":
            if anchor_ids or analysis.get(analysis_id) != text:
                raise CreativeContractError(f"editor_analysis_not_authorized:{segment_id}")
        elif kind == "ENGAGEMENT":
            if anchor_ids or analysis_id or re.search(r"\d", text):
                raise CreativeContractError(f"editor_engagement_claim_like:{segment_id}")
            if len(text.split()) > 24:
                raise CreativeContractError(f"editor_engagement_too_long:{segment_id}")
        else:
            raise CreativeContractError(f"editor_segment_kind_invalid:{segment_id}")
    word_count = sum(len(str(item["text"]).split()) for item in segments)
    minimum_duration = word_count / 2.25 + len(segments) * 0.16 + 0.75
    if duration < minimum_duration:
        raise CreativeContractError("editor_duration_too_short_for_locked_narration")
    forbidden = [str(item).lower() for item in packet.get("forbidden_claims", [])]
    full_text = " ".join(str(item.get("text", "")) for item in segments).lower()
    for phrase in forbidden:
        if phrase and phrase in full_text:
            raise CreativeContractError("editor_forbidden_claim_present")
    shots = artifact.get("shots") or []
    if not isinstance(shots, list):
        raise CreativeContractError("editor_shots_invalid")
    valid_assets = {str(item["asset_id"]) for item in packet["rights_assets"]}
    prior_end = 0.0
    for shot in shots:
        start = float(shot.get("start_seconds", -1))
        end = float(shot.get("end_seconds", -1))
        if abs(start - prior_end) > 0.05 or end <= start or end > duration + 0.001:
            raise CreativeContractError("editor_shot_timing_invalid")
        prior_end = end
        if not set(map(str, shot.get("narration_segment_ids", []))).issubset(seen):
            raise CreativeContractError("editor_shot_segment_binding_invalid")
        if not set(map(str, shot.get("asset_ids", []))).issubset(valid_assets):
            raise CreativeContractError("editor_shot_asset_binding_invalid")
    if shots and abs(prior_end - duration) > 0.05:
        raise CreativeContractError("editor_shots_do_not_cover_duration")
    return {
        "result": "PASS_FACTUAL_ANCHORS",
        "duration_seconds": duration,
        "fact_segment_count": fact_count,
        "narration_segment_count": len(segments),
        "shot_count": len(shots),
    }


def validate_motion_artifact(
    artifact: Mapping[str, Any],
    packet: Mapping[str, Any],
    editor: Mapping[str, Any],
) -> dict[str, Any]:
    if artifact.get("schema") != "contentops.v2.codex_job_motion_source.v1":
        raise CreativeContractError("motion_schema_invalid")
    if artifact.get("composition_id") != "FWBUnattendedShort":
        raise CreativeContractError("motion_composition_id_invalid")
    if abs(float(artifact.get("duration_seconds", 0)) - float(editor["duration_seconds"])) > 0.001:
        raise CreativeContractError("motion_duration_changed")
    files = artifact.get("files")
    if not isinstance(files, Mapping) or set(files) != SOURCE_FILES:
        raise CreativeContractError("motion_source_file_set_invalid")
    if not all(isinstance(value, str) and value.strip() for value in files.values()):
        raise CreativeContractError("motion_source_file_empty")
    editor_segments = {
        str(item["segment_id"]): str(item["text"])
        for item in editor["narration_segments"]
    }
    bindings = artifact.get("source_claim_bindings")
    if not isinstance(bindings, list):
        raise CreativeContractError("motion_claim_bindings_missing")
    bound_display_text: set[str] = set()
    for binding in bindings:
        segment_id = str(binding.get("segment_id", ""))
        display_text = str(binding.get("text", ""))
        if not display_text or display_text not in editor_segments.get(segment_id, ""):
            raise CreativeContractError("motion_claim_not_bound_to_editor")
        bound_display_text.add(display_text)
    valid_assets = {str(item["asset_id"]) for item in packet["rights_assets"]}
    if not set(map(str, artifact.get("asset_ids", []))).issubset(valid_assets):
        raise CreativeContractError("motion_asset_not_governed")
    source = "\n".join(str(value) for value in files.values())
    for display_text in bound_display_text:
        if display_text not in source:
            raise CreativeContractError("motion_bound_claim_missing_from_source")
    allowed_paths = {
        str(item["relative_path"]): str(item["asset_id"])
        for item in packet["rights_assets"]
    }
    referenced_paths = set(
        re.findall(r"staticFile\(\s*['\"]([^'\"]+)['\"]\s*\)", source)
    )
    if not referenced_paths or not referenced_paths.issubset(allowed_paths):
        raise CreativeContractError("motion_static_asset_binding_invalid")
    expected_asset_ids = {allowed_paths[path] for path in referenced_paths}
    if expected_asset_ids != set(map(str, artifact.get("asset_ids", []))):
        raise CreativeContractError("motion_asset_ids_do_not_match_source")
    allowed_numeric_strings = set(bound_display_text) | referenced_paths
    literals = []
    for match in re.finditer(
        r"'((?:\\.|[^'\\\r\n])*)'|\"((?:\\.|[^\"\\\r\n])*)\"",
        source,
    ):
        literals.append(match.group(1) if match.group(1) is not None else match.group(2))
    for literal in (value for value in literals if re.search(r"\d", value)):
        if re.fullmatch(r"#[0-9A-Fa-f]{3,8}", literal):
            continue
        if literal not in allowed_numeric_strings:
            raise CreativeContractError(f"motion_unbound_numeric_string:{literal[:80]}")
    sandbox = validate_source_files(files)
    return {
        "result": "PASS_MOTION_SOURCE_CONTRACT",
        "source_file_count": len(files),
        "claim_binding_count": len(bindings),
        "sandbox": sandbox,
    }


def validate_revision_artifact(
    artifact: Mapping[str, Any],
    packet: Mapping[str, Any],
    editor: Mapping[str, Any],
    motion: Mapping[str, Any],
) -> dict[str, Any]:
    if artifact.get("schema") != "contentops.v2.codex_actual_media_review.v1":
        raise CreativeContractError("revision_schema_invalid")
    decision = str(artifact.get("decision", ""))
    if decision not in {"NO_MATERIAL_REVISION", "MATERIAL_REVISION_REQUIRED"}:
        raise CreativeContractError("revision_decision_invalid")
    files = artifact.get("replacement_files") or {}
    if decision == "MATERIAL_REVISION_REQUIRED":
        if not isinstance(files, Mapping) or set(files) != SOURCE_FILES:
            raise CreativeContractError("revision_replacement_file_set_invalid")
        revised_motion = dict(motion)
        revised_motion["files"] = dict(files)
        revised_motion["source_claim_bindings"] = list(
            artifact.get("source_claim_bindings", [])
        )
        validate_motion_artifact(revised_motion, packet, editor)
    elif files:
        raise CreativeContractError("revision_files_without_material_decision")
    allowed_segments = {
        str(item["segment_id"]): str(item["text"])
        for item in editor["narration_segments"]
    }
    for binding in artifact.get("source_claim_bindings", []):
        display_text = str(binding.get("text", ""))
        if not display_text or display_text not in allowed_segments.get(
            str(binding.get("segment_id", "")), ""
        ):
            raise CreativeContractError("revision_claim_not_bound")
    return {
        "result": "PASS_ACTUAL_MEDIA_REVIEW_CONTRACT",
        "decision": decision,
        "defect_count": len(artifact.get("defects", [])),
    }


def validate_source_files(files: Mapping[str, str]) -> dict[str, Any]:
    violations: list[str] = []
    for relative, source in files.items():
        if relative not in SOURCE_FILES:
            violations.append(f"path:{relative}")
            continue
        for pattern, code in FORBIDDEN_SOURCE_PATTERNS:
            if re.search(pattern, source, flags=re.I | re.M):
                violations.append(f"{relative}:{code}")
        for match in re.finditer(
            r"(?:from\s+|import\s*)['\"]([^'\"]+)['\"]", source
        ):
            imported = match.group(1)
            if not imported.startswith("./") and imported not in ALLOWED_IMPORTS:
                violations.append(f"{relative}:import:{imported}")
    if violations:
        raise CreativeContractError("sandbox_violation:" + ",".join(sorted(set(violations))))
    return {
        "result": "PASS_CREATIVE_CODE_SANDBOX",
        "allowed_imports": sorted(ALLOWED_IMPORTS),
        "source_file_count": len(files),
    }


def materialize_source(files: Mapping[str, str], project_root: Path) -> list[dict[str, Any]]:
    validate_source_files(files)
    artifacts: list[dict[str, Any]] = []
    for relative, source in sorted(files.items()):
        destination = (project_root / PurePosixPath(relative)).resolve()
        if project_root.resolve() not in destination.parents:
            raise CreativeContractError(f"source_destination_escape:{relative}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source.rstrip() + "\n", encoding="utf-8")
        artifacts.append(
            {
                "path": str(destination),
                "sha256": hash_file(destination),
                "size_bytes": destination.stat().st_size,
            }
        )
    return artifacts
