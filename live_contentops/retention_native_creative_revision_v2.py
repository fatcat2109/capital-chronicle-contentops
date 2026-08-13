"""Bounded GPT-5.6 creative revision author for accepted retention-native shots.

The model authors the viewer-visible replacement and the exact source-label policy.  This
module only validates that bounded packet, replaces the named component byte-for-byte, and
writes renderer plumbing that keeps canonical attribution in the deterministic outer chrome.
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
    ROLE_V2_CREATIVE_REVISION_AUTHOR,
    routed_llm_invocation,
)
from live_contentops.nine_router_ordered_model_router_v2 import RetryBudget
from live_contentops.nine_router_provider_adapter_v2 import call_nine_router
from live_contentops.retention_native_motion_author_v2 import (
    UNSAFE_SOURCE_MARKERS,
    _parse_object,
    logical_hash,
)

SCHEMA_VERSION = "contentops.retention_native.creative_revision_packet.v2"
PROMPT_TEMPLATE = "retention_native_localized_preview_revision"
PROMPT_VERSION = "v2.1-owner-xhigh-first"
TARGET_SHOT_ID = "s08"
RETAIN_INTERNAL_SOURCE_LABEL_IDS = ("s04",)


def _component_pattern(shot_id: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?ms)^const Shot_{re.escape(shot_id)}: React\.FC<AuthoredShotProps> = .*?"
        rf"(?=^const Shot_[sm]\d+: React\.FC<AuthoredShotProps> = |^export const authoredShots)"
    )


def extract_component(source: str, shot_id: str) -> str:
    match = _component_pattern(shot_id).search(source)
    if match is None:
        raise RuntimeError(f"authored_component_missing:{shot_id}")
    return match.group(0).rstrip()


def internal_source_label_ids(source: str) -> tuple[str, ...]:
    ids: list[str] = []
    for match in re.finditer(
        r"(?ms)^const Shot_(?P<id>[sm]\d+): React\.FC<AuthoredShotProps> = .*?"
        r"(?=^const Shot_[sm]\d+: React\.FC<AuthoredShotProps> = |^export const authoredShots)",
        source,
    ):
        component = match.group(0)
        # Every generated declaration necessarily names the prop once. More references mean
        # the component consumes or renders it internally.
        if component.count("sourceLabel") > 1:
            ids.append(match.group("id"))
    return tuple(ids)


def revision_validator(
    *, suppress_ids: Sequence[str], retain_ids: Sequence[str]
):
    exact_suppress = tuple(suppress_ids)
    exact_retain = tuple(retain_ids)

    def validate(text: str) -> tuple[bool, str | None, Any, str | None]:
        value = _parse_object(text)
        if value is None:
            return False, "structured_output_malformed", None, "json_object_required"
        if (
            value.get("schema_version") != SCHEMA_VERSION
            or value.get("public_write") is not False
            or value.get("publication_authority") is not False
            or value.get("factual_authority") is not False
            or tuple(value.get("suppress_internal_source_label_shot_ids") or ())
            != exact_suppress
            or tuple(value.get("retain_internal_source_label_shot_ids") or ())
            != exact_retain
        ):
            return False, "structured_output_schema_invalid", None, "authority_or_scope_invalid"
        replacements = value.get("shot_replacements")
        if not isinstance(replacements, list) or len(replacements) != 1:
            return False, "structured_output_schema_invalid", None, "replacement_count_invalid"
        row = replacements[0]
        if not isinstance(row, Mapping) or row.get("shot_id") != TARGET_SHOT_ID:
            return False, "structured_output_schema_invalid", None, "replacement_target_invalid"
        component = row.get("component_source")
        if (
            row.get("component_name") != f"Shot_{TARGET_SHOT_ID}"
            or not isinstance(component, str)
            or len(component) < 500
            or len(component) > 14000
            or not component.lstrip().startswith(
                f"const Shot_{TARGET_SHOT_ID}: React.FC<AuthoredShotProps>"
            )
            or "return" not in component
            or any(marker in component.lower() for marker in UNSAFE_SOURCE_MARKERS)
            or component.count("sourceLabel") > 1
            or not all(label in component for label in ("SUPPLY", "INVENTORIES", "DEMAND"))
        ):
            return False, "structured_output_schema_invalid", None, "replacement_source_invalid"
        if not isinstance(value.get("revision_rationale"), str):
            return False, "structured_output_schema_invalid", None, "rationale_required"
        return True, None, value, None

    return validate


def apply_revision_packet(source: str, packet: Mapping[str, Any]) -> str:
    replacement = str(packet["shot_replacements"][0]["component_source"]).strip()
    pattern = _component_pattern(TARGET_SHOT_ID)
    if len(pattern.findall(source)) != 1:
        raise RuntimeError("revision_target_cardinality_invalid")
    revised = pattern.sub(replacement + "\n\n", source, count=1)
    revised = re.sub(
        r"\nexport const internalSourceLabelShotIds = new Set<string>\([^\n]*\);\s*$",
        "",
        revised,
    ).rstrip()
    retain = list(packet["retain_internal_source_label_shot_ids"])
    revised += (
        "\n\nexport const internalSourceLabelShotIds = new Set<string>("
        + json.dumps(retain, ensure_ascii=True, separators=(",", ":"))
        + ");\n"
    )
    return revised


def _prompt(
    *, component: str, suppress_ids: Sequence[str], source_sha256: str,
    preview_observation: Mapping[str, Any],
) -> str:
    governed = {
        "target_shot_id": TARGET_SHOT_ID,
        "current_component_source": component,
        "authored_source_sha256": source_sha256,
        "suppress_internal_source_label_shot_ids": list(suppress_ids),
        "retain_internal_source_label_shot_ids": list(RETAIN_INTERNAL_SOURCE_LABEL_IDS),
        "preview_observation": dict(preview_observation),
    }
    return f"""ROLE: V2_CREATIVE_REVISION_AUTHOR. Perform one localized, model-authored
revision of the accepted Remotion shot. Preserve the accepted narration, duration, purpose,
asset selection, visual metaphor, and transition intent. Repair the observed collision with
professional native 9:16 typography. SUPPLY, INVENTORIES, and DEMAND must never overlap at
any animation phase; use clearly separated vertical rows/zones or another robust composition.

Canonical outer chrome already renders attribution. Authorize the exact governed suppression
list below so deterministic plumbing passes an empty sourceLabel to those components. Keep
s04 because its source text is substantive evidence content. The replacement s08 component
must not render sourceLabel internally (the prop may remain in its argument destructuring).

Return ONE JSON object only:
{{"schema_version":"{SCHEMA_VERSION}","shot_replacements":[{{"shot_id":"s08",
"component_name":"Shot_s08","component_source":"complete const declaration"}}],
"suppress_internal_source_label_shot_ids":["exact ordered ids"],
"retain_internal_source_label_shot_ids":["s04"],"revision_rationale":"brief",
"public_write":false,"publication_authority":false,"factual_authority":false}}

Available identifiers: React, AbsoluteFill, Img, interpolate, spring, staticFile, Easing,
Sequence, AuthoredShotProps. Deterministic frame math and inline SVG/HTML/CSS only. No imports,
network, timers, random, DOM APIs, scripts, raw HTML, or factual additions. Keep primary
information inside 8% horizontal and 10% vertical safe margins.

GOVERNED REVISION PACKET:
{json.dumps(governed, ensure_ascii=False, separators=(',', ':'))}
"""


def run(
    *, authored_source: Path, evidence_root: Path, control_root: Path,
    preview_observation: Mapping[str, Any],
) -> dict[str, Any]:
    source = authored_source.read_text(encoding="utf-8")
    source_before_sha = hashlib.sha256(authored_source.read_bytes()).hexdigest()
    internal_ids = internal_source_label_ids(source)
    retain = set(RETAIN_INTERNAL_SOURCE_LABEL_IDS)
    suppress_ids = tuple(shot_id for shot_id in internal_ids if shot_id not in retain)
    if TARGET_SHOT_ID not in suppress_ids:
        raise RuntimeError("revision_target_not_in_source_label_suppression_scope")
    governed_input = {
        "target_shot_id": TARGET_SHOT_ID,
        "authored_source_sha256": source_before_sha,
        "suppress_internal_source_label_shot_ids": list(suppress_ids),
        "retain_internal_source_label_shot_ids": list(RETAIN_INTERNAL_SOURCE_LABEL_IDS),
        "preview_observation": dict(preview_observation),
    }
    prompt = _prompt(
        component=extract_component(source, TARGET_SHOT_ID),
        suppress_ids=suppress_ids,
        source_sha256=source_before_sha,
        preview_observation=preview_observation,
    )
    invocation_id = "v2-creative-revision-preview-s08-source-label-v1"
    budget = RetryBudget(
        logical_invocation_id=invocation_id,
        max_total_provider_attempts=3,
        max_fallback_transitions=2,
        max_same_model_retries=0,
        max_structured_output_repair_attempts=0,
        wall_clock_budget_seconds=900.0,
        per_model_max_attempts=(1, 1, 1),
    )

    def provider(prompt_text: str, model: str, timeout: float):
        return call_nine_router(
            prompt_text, model, timeout, max_tokens=7000, temperature=0.15, stream=True
        )

    with llm_cycle_budget_scope(invocation_id, control_root=control_root):
        summary = routed_llm_invocation(
            prompt=prompt,
            role_task_id=ROLE_V2_CREATIVE_REVISION_AUTHOR,
            logical_invocation_id=invocation_id,
            work_item_id="short_9x16:s08:typography-and-source-label",
            timeout_seconds=300.0,
            validator=revision_validator(
                suppress_ids=suppress_ids, retain_ids=RETAIN_INTERNAL_SOURCE_LABEL_IDS
            ),
            provider_call=provider,
            governed_input=governed_input,
            prompt_template=PROMPT_TEMPLATE,
            prompt_version=PROMPT_VERSION,
            budget=budget,
        )
    evidence_root.mkdir(parents=True, exist_ok=True)
    receipt = {key: value for key, value in summary.items() if key != "output"}
    receipt.update({
        "schema_version": "contentops.retention_native.creative_revision_receipt.v2",
        "status": summary["terminal_disposition"],
        "source_before_sha256": source_before_sha,
        "governed_input_hash": logical_hash(governed_input),
        "public_write": False,
        "publication_authority": False,
        "factual_authority": False,
    })
    receipt_path = evidence_root / "creative_revision_s08_receipt_v2.json"
    receipt_path.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    if summary["terminal_disposition"] != "ACCEPTED":
        raise RuntimeError(
            f"creative_revision_blocked:{summary['terminal_disposition']}"
        )
    packet = summary["output"]
    packet_path = evidence_root / "creative_revision_s08_packet_v2.json"
    packet_path.write_text(
        json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    revised = apply_revision_packet(source, packet)
    authored_source.write_text(revised, encoding="utf-8")
    result = {
        "schema_version": "contentops.retention_native.creative_revision_application.v2",
        "status": "PASS",
        "revision_number": 1,
        "target_shot_ids": [TARGET_SHOT_ID],
        "selected_model": summary["selected_model"],
        "attempted_models": [row["requested_model"] for row in summary["attempts"]],
        "source_before_sha256": source_before_sha,
        "source_after_sha256": hashlib.sha256(authored_source.read_bytes()).hexdigest(),
        "packet_path": str(packet_path.resolve()),
        "packet_sha256": hashlib.sha256(packet_path.read_bytes()).hexdigest(),
        "receipt_path": str(receipt_path.resolve()),
        "receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
        "source_label_suppressed_shot_ids": list(suppress_ids),
        "source_label_retained_shot_ids": list(RETAIN_INTERNAL_SOURCE_LABEL_IDS),
        "public_write": False,
        "uploads": 0,
        "browser_or_cdp_actions": 0,
        "publication_authority": False,
        "factual_authority": False,
    }
    result_path = evidence_root / "creative_revision_application_v2.json"
    result_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authored-source", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--control-root", type=Path, required=True)
    parser.add_argument("--preview-observation", type=Path, required=True)
    args = parser.parse_args(argv)
    observation = json.loads(args.preview_observation.read_text(encoding="utf-8"))
    print(json.dumps(run(
        authored_source=args.authored_source.resolve(),
        evidence_root=args.evidence_root.resolve(),
        control_root=args.control_root.resolve(),
        preview_observation=observation,
    ), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
