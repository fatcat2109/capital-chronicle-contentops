"""GPT-5.6 Motion Code Author and mechanical blueprint-to-render contract compiler.

The model owns every viewer-visible shot component.  Python only validates the bounded
code envelope, assembles exact accepted source, and translates the accepted Creative
Editor blueprint into the existing renderer-neutral factory contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.llm_cost_governor_v1 import llm_cycle_budget_scope
from live_contentops.nine_router_llm_seam_v2 import (
    ROLE_V2_MOTION_CODE_AUTHOR,
    routed_llm_invocation,
)
from live_contentops.nine_router_ordered_model_router_v2 import RetryBudget
from live_contentops.nine_router_provider_adapter_v2 import call_nine_router

SCHEMA_VERSION = "contentops.retention_native.motion_code_batch.v2"
SELECTED_MODEL = "new/gpt-5.6-sol-medium"
UNSAFE_SOURCE_MARKERS = (
    "fetch(", "xmlhttprequest", "websocket", "document.", "window.", "process.",
    "require(", "import(", "eval(", "new function", "dangerouslysetinnerhtml",
    "http://", "https://", "data:", "localstorage", "sessionstorage",
)
CLAIM_ID_MAP = {
    "eia:global_output_near_pre_conflict_by_year_end": "eia:pre_conflict_year_end",
    "eia:most_shut_in_output_restored_by": "eia:shut_in_2027_q1",
    "eia:brent_june_average_usd_per_barrel": "eia:brent_june_85",
    "eia:brent_q3_2026_forecast_usd_per_barrel": "eia:brent_q3_74",
    "eia:brent_2027_forecast_usd_per_barrel": "eia:brent_2027_65",
    "eia:gasoline_q3_2026_forecast_usd_per_gallon": "eia:gasoline_q3_3_80",
    "eia:gasoline_q4_2026_forecast_usd_per_gallon": "eia:gasoline_q4_3_40",
    "eia:next_weekly_petroleum_status_report_date": "eia:named_catalysts",
    "eia:next_steo_release_date": "eia:named_catalysts",
}
ASSET_ID_MAP = {
    "primary": "wti-current-volatility-chart",
    "recent_price": "wti-recent-price-chart",
    "multi_year_range": "wti-multi-year-range-chart",
}


def logical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()).hexdigest()


def _parse_object(text: str) -> Mapping[str, Any] | None:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.I)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, Mapping) else None


def batch_validator(expected_ids: Sequence[str]):
    exact = tuple(expected_ids)

    def validate(text: str) -> tuple[bool, str | None, Any, str | None]:
        value = _parse_object(text)
        if value is None:
            return False, "structured_output_malformed", None, "json_object_required"
        if (
            value.get("schema_version") != SCHEMA_VERSION
            or value.get("public_write") is not False
            or value.get("publication_authority") is not False
            or value.get("factual_authority") is not False
        ):
            return False, "structured_output_schema_invalid", None, "authority_or_schema_invalid"
        rows = value.get("shots")
        if not isinstance(rows, list) or tuple(
            row.get("shot_id") if isinstance(row, Mapping) else None for row in rows
        ) != exact:
            return False, "structured_output_schema_invalid", None, "shot_coverage_invalid"
        for row in rows:
            source = row.get("component_source")
            component = row.get("component_name")
            if (
                not isinstance(component, str)
                or not re.fullmatch(r"Shot_[A-Za-z0-9_]+", component)
                or not isinstance(source, str)
                or len(source) < 120
                or len(source) > 14000
                or "AuthoredShotProps" not in source
                or "return" not in source
                or any(marker in source.lower() for marker in UNSAFE_SOURCE_MARKERS)
            ):
                return False, "structured_output_schema_invalid", None, "unsafe_or_invalid_component"
        return True, None, value, None

    return validate


def _prompt(
    *, variant_id: str, shots: Sequence[Mapping[str, Any]], neighbors: Sequence[Mapping[str, Any]],
    blueprint_hash: str,
) -> str:
    payload = {
        "variant_id": variant_id,
        "shots": list(shots),
        "neighboring_shot_context": list(neighbors),
        "blueprint_sha256": blueprint_hash,
    }
    return f"""ROLE: V2_MOTION_CODE_AUTHOR. Author premium production Remotion React/TypeScript
for this SMALL CONTIGUOUS SHOT BATCH. The accepted Creative Editor plan is binding. Do not
rewrite narration, timing, hierarchy, asset choice, or transition intent. Avoid slides/cards,
repeated same-speed motion, universal zooms, chart crawls, collisions, tiny text, caption
dependency, and decorative motion. Each shot needs scene-specific visual storytelling.

Return ONE JSON object only:
{{"schema_version":"{SCHEMA_VERSION}","shots":[{{"shot_id":"exact", 
"component_name":"Shot_exact","component_source":"complete const component declaration"}}],
"public_write":false,"publication_authority":false,"factual_authority":false}}

For every row, component_source MUST be exactly a declaration shaped like:
const Shot_exact: React.FC<AuthoredShotProps> = ({{frame,fps,width,height,progress,
assetPath,assetClass,narration,sourceLabel}}) => {{ ... return <AbsoluteFill>...</AbsoluteFill>; }};

Available identifiers without imports: React, AbsoluteFill, Img, interpolate, spring,
staticFile, Easing, Sequence, AuthoredShotProps. Use only deterministic frame math and
inline SVG/HTML/CSS. Use staticFile(assetPath.replaceAll('\\\\','/')) only when assetPath
exists. No network, timers, random, DOM APIs, imports, external packages, scripts, raw HTML,
or factual additions. Keep primary information inside 8% horizontal and 10% vertical safe
margins. Source labels belong in the deterministic outer chrome; do not duplicate them.

GOVERNED BATCH:
{json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}
"""


def _assemble_source(rows: Sequence[Mapping[str, Any]]) -> str:
    components = "\n\n".join(str(row["component_source"]).strip() for row in rows)
    registry = "\n".join(
        f"  {json.dumps(str(row['shot_id']))}: {row['component_name']}," for row in rows
    )
    return f"""import React from 'react';
import {{AbsoluteFill, Img, interpolate, spring, staticFile, Easing, Sequence}} from 'remotion';

export type AuthoredShotProps = {{
  frame: number; fps: number; width: number; height: number; progress: number;
  assetPath?: string; assetClass?: string; narration: string; sourceLabel: string;
}};

{components}

export const authoredShots: Record<string, React.FC<AuthoredShotProps>> = {{
{registry}
}};
"""


def _asset_ids_for_shot(shot: Mapping[str, Any]) -> list[str]:
    authored = [ASSET_ID_MAP.get(str(value), str(value)) for value in shot.get("asset_ids") or ()]
    text = " ".join(str(shot.get(key) or "") for key in ("visual", "motion", "purpose")).lower()
    inferred: list[str] = []
    if any(word in text for word in ("channel", "hormuz", "route", "tanker", "map")):
        inferred.append("hormuz-context-map")
    if any(word in text for word in ("document", "release", "source excerpt", "eia page")):
        inferred.append("eia-release-press590-document")
    if any(word in text for word in ("timeline", "milestone", "calendar", "year-end")):
        inferred.append("recovery-timeline")
    if any(word in text for word in ("forecast", "compare", "versus", "gasoline")):
        inferred.append("forecast-comparison")
    if any(word in text for word in ("mechanism", "inventory", "demand", "supply", "flow")):
        inferred.append("supply-recovery-mechanism")
    if any(word in text for word in ("gulf", "satellite", "orbital", "geography")):
        inferred.append("nasa-persian-gulf-iss069-e-92132")
    result = list(dict.fromkeys(authored + inferred))
    return result or ["supply-recovery-mechanism"]


def compile_director_source(
    blueprint: Mapping[str, Any], base: Mapping[str, Any], *, blueprint_hash: str
) -> dict[str, Any]:
    source = json.loads(json.dumps(base))
    source["director_identity"] = {
        "kind": "canonical_9router_gpt56_creative_code",
        "creative_editor_model": SELECTED_MODEL,
        "motion_code_author_model": SELECTED_MODEL,
        "creative_blueprint_sha256": blueprint_hash,
        "authority": "presentation_only",
        "facts_may_be_added": False,
        "renderer_may_invent_edits": False,
        "public_write": False,
    }
    source["revision_history"] = []
    source["engagement_brief"]["core_promise"] = blueprint["viewer_promise"]
    loops = source["engagement_brief"].get("open_loops") or []
    loop_id = str(loops[0]["loop_id"]) if loops else "loop-primary"
    for variant in source["variants"]:
        variant_id = str(variant["variant_id"])
        authored_variant = blueprint["variants"][variant_id]
        variant["min_duration_seconds"] = 45.0 if variant_id == "short_9x16" else 90.0
        variant["max_duration_seconds"] = 60.0 if variant_id == "short_9x16" else 150.0
        variant["hook_copy"] = authored_variant["hook"]
        payoff = float(authored_variant["payoff_seconds"])
        beats = []
        for index, shot in enumerate(authored_variant["shots"]):
            shot_id = str(shot["id"])
            assets = _asset_ids_for_shot(shot)
            claims = [CLAIM_ID_MAP.get(str(value), str(value)) for value in shot.get("claim_ids") or ()]
            if not claims:
                claims = ["article:mechanism"]
            evidence_ids = list(dict.fromkeys(shot.get("evidence_ids") or ()))
            if not evidence_ids:
                evidence_ids = ["governed-article"]
            covers_payoff = float(shot["t0"]) <= payoff < float(shot["t1"])
            beat = {
                "beat_id": shot_id,
                "scene_id": f"{variant_id}-scene-{index // 3 + 1:02d}",
                "chapter_id": f"{variant_id}-chapter-{index // 5 + 1:02d}",
                "narrative_role": "hook" if index == 0 else ("payoff" if covers_payoff else "evidence"),
                "narration_text": shot["narration_excerpt"],
                "claim_ids": list(dict.fromkeys(claims)),
                "evidence_ids": evidence_ids,
                "viewer_takeaway": shot["purpose"],
                "visual_purpose": shot["visual"],
                "asset_ids": assets,
                "audio_state": "cold_open" if index == 0 else ("resolution" if covers_payoff else "evidence"),
                "transition_intent": shot["transition"],
                "target_duration_seconds": float(shot["t1"]) - float(shot["t0"]),
                "edits": [{
                    "operation": "KINETIC_TEXT",
                    "asset_id": assets[0],
                    "at_seconds": 0.0,
                    "narrative_purpose": shot["purpose"],
                    "parameters": {"authored_motion_code": True, "shot_id": shot_id},
                }],
            }
            if index == 0:
                beat["open_loop_id"] = loop_id
            if covers_payoff:
                beat["payoff_for"] = [loop_id]
            beats.append(beat)
        variant["beats"] = beats
    all_ids = {beat["beat_id"] for variant in source["variants"] for beat in variant["beats"]}
    cues = []
    for variant in source["variants"]:
        for index, beat in enumerate(variant["beats"]):
            if index in {1, len(variant["beats"]) // 2, len(variant["beats"]) - 2}:
                cues.append({
                    "cue_id": f"sfx-{beat['beat_id']}", "beat_id": beat["beat_id"],
                    "kind": ("whoosh", "data_tick", "hit")[len(cues) % 3],
                })
    source["audio_plan"]["sfx_cues"] = [row for row in cues if row["beat_id"] in all_ids]
    return source


def run(
    *, blueprint_path: Path, base_source_path: Path, renderer_root: Path,
    evidence_root: Path, control_root: Path, batch_size: int = 5,
) -> dict[str, Any]:
    blueprint = json.loads(blueprint_path.read_text(encoding="utf-8"))
    base = json.loads(base_source_path.read_text(encoding="utf-8"))
    blueprint_hash = hashlib.sha256(blueprint_path.read_bytes()).hexdigest()
    accepted_rows: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    evidence_root.mkdir(parents=True, exist_ok=True)
    invocation_index = 0
    for variant_id in ("short_9x16", "midform_16x9"):
        shots = list(blueprint["variants"][variant_id]["shots"])
        for offset in range(0, len(shots), batch_size):
            invocation_index += 1
            batch = shots[offset:offset + batch_size]
            neighbors = shots[max(0, offset - 1):offset] + shots[offset + len(batch):offset + len(batch) + 1]
            ids = [str(row["id"]) for row in batch]
            prompt = _prompt(
                variant_id=variant_id, shots=batch, neighbors=neighbors,
                blueprint_hash=blueprint_hash,
            )
            iid = f"v2-motion-author-{variant_id}-batch-{offset // batch_size + 1:02d}"
            budget = RetryBudget(
                logical_invocation_id=iid, max_total_provider_attempts=2,
                max_fallback_transitions=0, max_same_model_retries=1,
                max_structured_output_repair_attempts=1,
                wall_clock_budget_seconds=600.0, per_model_max_attempts=(2,),
            )

            def provider(p: str, model: str, timeout: float):
                return call_nine_router(
                    p, model, timeout, max_tokens=7000, temperature=0.2, stream=True
                )

            with llm_cycle_budget_scope(iid, control_root=control_root):
                summary = routed_llm_invocation(
                    prompt=prompt, role_task_id=ROLE_V2_MOTION_CODE_AUTHOR,
                    logical_invocation_id=iid, work_item_id=f"{variant_id}:{','.join(ids)}",
                    timeout_seconds=600.0, validator=batch_validator(ids), provider_call=provider,
                    governed_input={"blueprint_sha256": blueprint_hash, "shots": batch, "neighbors": neighbors},
                    prompt_template="retention_native_motion_code_small_batch",
                    prompt_version="v2.0", budget=budget,
                    model_pool_override=(SELECTED_MODEL,),
                )
            receipt = {key: value for key, value in summary.items() if key != "output"}
            receipt.update({
                "schema_version": "contentops.retention_native.motion_code_receipt.v2",
                "status": summary["terminal_disposition"], "variant_id": variant_id,
                "shot_ids": ids, "creative_blueprint_sha256": blueprint_hash,
                "public_write": False, "publication_authority": False,
                "factual_authority": False,
            })
            receipt_path = evidence_root / f"motion_code_{variant_id}_batch_{offset // batch_size + 1:02d}_receipt_v2.json"
            receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            if summary["terminal_disposition"] != "ACCEPTED":
                raise RuntimeError(f"motion_code_batch_blocked:{iid}:{summary['terminal_disposition']}")
            rows = list(summary["output"]["shots"])
            accepted_rows.extend(rows)
            receipts.append({
                "path": str(receipt_path.resolve()),
                "sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
                "shot_ids": ids,
                "selected_model": summary["selected_model"],
            })
    source_text = _assemble_source(accepted_rows)
    authored_path = renderer_root / "src/generated/authored_shots.tsx"
    authored_path.parent.mkdir(parents=True, exist_ok=True)
    authored_path.write_text(source_text, encoding="utf-8")
    director = compile_director_source(blueprint, base, blueprint_hash=blueprint_hash)
    director_path = evidence_root / "director_source_from_accepted_blueprint_v2.json"
    director_path.write_text(json.dumps(director, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    result = {
        "schema_version": "contentops.retention_native.motion_code_authorship.v2",
        "status": "PASS",
        "selected_model": SELECTED_MODEL,
        "creative_blueprint_path": str(blueprint_path.resolve()),
        "creative_blueprint_sha256": blueprint_hash,
        "authored_shot_count": len(accepted_rows),
        "authored_source_path": str(authored_path.resolve()),
        "authored_source_sha256": hashlib.sha256(authored_path.read_bytes()).hexdigest(),
        "director_source_path": str(director_path.resolve()),
        "director_source_sha256": hashlib.sha256(director_path.read_bytes()).hexdigest(),
        "receipts": receipts,
        "browser_or_cdp_actions": 0, "uploads": 0, "public_writes": 0,
        "publication_authority": False, "factual_authority": False,
    }
    result_path = evidence_root / "motion_code_authorship_v2.json"
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blueprint", type=Path, required=True)
    parser.add_argument("--base-source", type=Path, required=True)
    parser.add_argument("--renderer-root", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--control-root", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=5)
    args = parser.parse_args(argv)
    result = run(
        blueprint_path=args.blueprint.resolve(), base_source_path=args.base_source.resolve(),
        renderer_root=args.renderer_root.resolve(), evidence_root=args.evidence_root.resolve(),
        control_root=args.control_root.resolve(), batch_size=args.batch_size,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
