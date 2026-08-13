"""Final bounded creative revision for narration-to-authored-timing fit."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.llm_cost_governor_v1 import llm_cycle_budget_scope
from live_contentops.nine_router_llm_seam_v2 import (
    ROLE_V2_CREATIVE_REVISION_AUTHOR,
    routed_llm_invocation,
)
from live_contentops.nine_router_ordered_model_router_v2 import (
    RetryBudget,
    V2_CREATIVE_HIGH_MODEL,
    V2_CREATIVE_MEDIUM_MODEL,
    V2_CREATIVE_MODEL,
)
from live_contentops.nine_router_provider_adapter_v2 import call_nine_router
from live_contentops.retention_native_motion_author_v2 import _parse_object, logical_hash

SCHEMA_VERSION = "contentops.retention_native.narration_timing_revision.v2"
PROMPT_TEMPLATE = "retention_native_narration_timing_revision"
PROMPT_VERSION = "v2.1-owner-xhigh-first"


def _numeric_tokens(text: str) -> set[str]:
    return {
        token.lstrip("$")
        for token in re.findall(r"(?:\$)?\d+(?:\.\d+)?(?:%|st|nd|rd|th)?", text.lower())
    }


def narration_revision_validator(source_rows: Sequence[Mapping[str, Any]]):
    ids = tuple(str(row["shot_id"]) for row in source_rows)
    originals = {str(row["shot_id"]): str(row["narration_text"]) for row in source_rows}

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
        rows = value.get("narration_revisions")
        if not isinstance(rows, list) or tuple(
            row.get("shot_id") if isinstance(row, Mapping) else None for row in rows
        ) != ids:
            return False, "structured_output_schema_invalid", None, "shot_coverage_invalid"
        for row in rows:
            shot_id = str(row["shot_id"])
            revised = row.get("narration_text")
            if (
                not isinstance(revised, str)
                or not 2 <= len(revised.split()) <= 10
                or not 8 <= len(revised) <= 100
                or _numeric_tokens(revised) - _numeric_tokens(originals[shot_id])
            ):
                return False, "structured_output_schema_invalid", None, "narration_scope_invalid"
        if not isinstance(value.get("revision_rationale"), str):
            return False, "structured_output_schema_invalid", None, "rationale_required"
        return True, None, value, None

    return validate


def measured_short_rows(*, director: Mapping[str, Any], failed_output_root: Path) -> list[dict[str, Any]]:
    request = json.loads(
        (failed_output_root / "contracts" / "kokoro_batch_request_v2.json").read_text(
            encoding="utf-8"
        )
    )
    audio_by_id = {str(row["beat_id"]): Path(str(row["output_path"])) for row in request["segments"]}
    variant = next(row for row in director["variants"] if row["variant_id"] == "short_9x16")
    result: list[dict[str, Any]] = []
    for beat in variant["beats"]:
        shot_id = str(beat["beat_id"])
        completed = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(audio_by_id[shot_id]),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        result.append({
            "shot_id": shot_id,
            "narration_text": str(beat["narration_text"]),
            "target_duration_seconds": float(beat["target_duration_seconds"]),
            "measured_audio_seconds": round(float(completed.stdout.strip()), 6),
            "max_words": 10,
            "claim_ids": list(beat.get("claim_ids") or ()),
            "evidence_ids": list(beat.get("evidence_ids") or ()),
            "viewer_takeaway": beat.get("viewer_takeaway"),
        })
    return result


def _prompt(rows: Sequence[Mapping[str, Any]]) -> str:
    return f"""ROLE: V2_CREATIVE_REVISION_AUTHOR. This is the second and final bounded
revision. Condense ONLY the spoken narration of the 14 accepted short-video shots so each line
fits its 4.0-second authored beat at natural professional pace. Preserve each shot's factual
meaning, evidence boundary, hook/payoff logic, and visual intent. Do not change timing, order,
claims, numbers, assets, shot code, or transitions. Do not add any fact, number, forecast,
certainty, or causal claim. Prefer crisp broadcast phrasing, 5-9 words; hard maximum 10 words.
Avoid fragments that sound robotic, repeated sentence openings, and breathless compression.
For numeric-dense shots, you MAY omit numeric values already displayed by the accepted visual;
summarize the direction or relationship instead. Never introduce shorthand such as Q3 if its
digit is not already present in the original narration.

Return ONE JSON object only:
{{"schema_version":"{SCHEMA_VERSION}","narration_revisions":[
{{"shot_id":"exact in supplied order","narration_text":"2-10 words"}}],
"revision_rationale":"brief","public_write":false,"publication_authority":false,
"factual_authority":false}}

GOVERNED MEASURED ROWS:
{json.dumps(list(rows), ensure_ascii=False, separators=(',', ':'))}
"""


def _repair_prompt(original_prompt: str, _invalid_output: str, diagnostic: str | None) -> str:
    return (
        original_prompt
        + "\n\nSTRUCTURED REPAIR REQUIRED. The prior response was rejected with safe diagnostic: "
        + str(diagnostic or "schema_invalid")
        + ". Return only a corrected JSON object with the exact requested shot order, 2-10 "
        "words per narration_text, no new numeric token, and all three authority flags false. "
        "If the source is numeric-dense, omit displayed values and state only its governed direction."
    )


def apply_narration_revision(
    *, director: dict[str, Any], blueprint: dict[str, Any], packet: Mapping[str, Any],
    selected_model: str | None, receipt_sha256: str, packet_sha256: str,
    selected_models_by_batch: Mapping[str, str] | None = None,
) -> None:
    revised = {
        str(row["shot_id"]): str(row["narration_text"])
        for row in packet["narration_revisions"]
    }
    short_blueprint = blueprint["variants"]["short_9x16"]["shots"]
    short_director = next(
        row for row in director["variants"] if row["variant_id"] == "short_9x16"
    )["beats"]
    if tuple(revised) != tuple(str(row["id"]) for row in short_blueprint):
        raise RuntimeError("narration_revision_blueprint_binding_invalid")
    if tuple(revised) != tuple(str(row["beat_id"]) for row in short_director):
        raise RuntimeError("narration_revision_director_binding_invalid")
    for row in short_blueprint:
        row["narration_excerpt"] = revised[str(row["id"])]
    for row in short_director:
        row["narration_text"] = revised[str(row["beat_id"])]
    if selected_model is not None:
        director["director_identity"]["narration_revision_author_model"] = selected_model
    if selected_models_by_batch:
        director["director_identity"]["narration_revision_author_models_by_batch"] = dict(
            selected_models_by_batch
        )
    revision = {
        "revision_number": 2,
        "kind": "MODEL_AUTHORED_NARRATION_TIMING_REVISION",
        "variant_id": "short_9x16",
        "shot_ids": list(revised),
        "issue_resolved": "authored_narration_exceeded_authored_short_duration",
        "revision_packet_sha256": packet_sha256,
        "revision_receipt_sha256": receipt_sha256,
        "public_write": False,
        "publication_authority": False,
        "factual_authority": False,
    }
    if selected_model is not None:
        revision["selected_model"] = selected_model
    if selected_models_by_batch:
        revision["selected_models_by_batch"] = dict(selected_models_by_batch)
    director["revision_history"].append(revision)


def run(
    *, director_path: Path, blueprint_path: Path, failed_output_root: Path,
    evidence_root: Path, control_root: Path, resume_receipt: Path | None = None,
) -> dict[str, Any]:
    director = json.loads(director_path.read_text(encoding="utf-8"))
    blueprint = json.loads(blueprint_path.read_text(encoding="utf-8"))
    if len(director.get("revision_history") or ()) != 1:
        raise RuntimeError("narration_revision_requires_exactly_one_prior_revision")
    rows = measured_short_rows(director=director, failed_output_root=failed_output_root)
    governed_input = {
        "variant_id": "short_9x16",
        "rows": rows,
        "director_sha256": hashlib.sha256(director_path.read_bytes()).hexdigest(),
        "blueprint_sha256": hashlib.sha256(blueprint_path.read_bytes()).hexdigest(),
        "maximum_structural_revisions": 2,
        "revision_number": 2,
    }
    model_pool_override = None
    receipt_name = "narration_revision_receipt_v2.json"
    prior_receipt_sha256 = None
    if resume_receipt is not None:
        prior = json.loads(resume_receipt.read_text(encoding="utf-8"))
        attempts = prior.get("attempts") or ()
        if (
            not attempts
            or attempts[0].get("requested_model") != V2_CREATIVE_MODEL
            or attempts[0].get("failure_class") != "http_502_bad_gateway"
            or prior.get("terminal_disposition") != "LLM_TERMINAL_NON_RETRYABLE_FAILURE"
        ):
            raise RuntimeError("narration_revision_resume_receipt_invalid")
        prior_receipt_sha256 = hashlib.sha256(resume_receipt.read_bytes()).hexdigest()
        governed_input["prior_blocked_receipt_sha256"] = prior_receipt_sha256
        governed_input["prior_xhigh_failure_class"] = "http_502_bad_gateway"
        invocation_id = "v2-creative-revision-short-narration-timing-resume-high-v1"
        model_pool_override = (V2_CREATIVE_HIGH_MODEL, V2_CREATIVE_MEDIUM_MODEL)
        receipt_name = "narration_revision_resume_receipt_v2.json"
    else:
        invocation_id = "v2-creative-revision-short-narration-timing-v1"
    budget = RetryBudget(
        logical_invocation_id=invocation_id,
        max_total_provider_attempts=2 if model_pool_override else 3,
        max_fallback_transitions=1 if model_pool_override else 2,
        max_same_model_retries=0,
        max_structured_output_repair_attempts=0,
        wall_clock_budget_seconds=900.0,
        per_model_max_attempts=(1, 1) if model_pool_override else (1, 1, 1),
    )

    def provider(prompt_text: str, model: str, timeout: float):
        return call_nine_router(
            prompt_text, model, timeout, max_tokens=4000, temperature=0.1, stream=True
        )

    with llm_cycle_budget_scope(invocation_id, control_root=control_root):
        summary = routed_llm_invocation(
            prompt=_prompt(rows),
            role_task_id=ROLE_V2_CREATIVE_REVISION_AUTHOR,
            logical_invocation_id=invocation_id,
            work_item_id="short_9x16:narration-timing:all-14-shots",
            timeout_seconds=300.0,
            validator=narration_revision_validator(rows),
            provider_call=provider,
            governed_input=governed_input,
            prompt_template=PROMPT_TEMPLATE,
            prompt_version=PROMPT_VERSION,
            budget=budget,
            model_pool_override=model_pool_override,
        )
    evidence_root.mkdir(parents=True, exist_ok=True)
    receipt = {key: value for key, value in summary.items() if key != "output"}
    receipt.update({
        "schema_version": "contentops.retention_native.narration_revision_receipt.v2",
        "status": summary["terminal_disposition"],
        "governed_input_hash": logical_hash(governed_input),
        "public_write": False,
        "publication_authority": False,
        "factual_authority": False,
    })
    receipt["prior_blocked_receipt_sha256"] = prior_receipt_sha256
    receipt_path = evidence_root / receipt_name
    receipt_path.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    if summary["terminal_disposition"] != "ACCEPTED":
        raise RuntimeError(f"narration_revision_blocked:{summary['terminal_disposition']}")
    packet = summary["output"]
    packet_path = evidence_root / "narration_revision_packet_v2.json"
    packet_path.write_text(
        json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    receipt_sha = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
    apply_narration_revision(
        director=director,
        blueprint=blueprint,
        packet=packet,
        selected_model=str(summary["selected_model"]),
        receipt_sha256=receipt_sha,
        packet_sha256=packet_sha,
    )
    director_path.write_text(
        json.dumps(director, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    blueprint_path.write_text(
        json.dumps(blueprint, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    result = {
        "schema_version": "contentops.retention_native.narration_revision_application.v2",
        "status": "PASS",
        "revision_number": 2,
        "selected_model": summary["selected_model"],
        "attempted_models": [row["requested_model"] for row in summary["attempts"]],
        "shot_ids": [row["shot_id"] for row in rows],
        "before_word_count": sum(len(str(row["narration_text"]).split()) for row in rows),
        "after_word_count": sum(
            len(str(row["narration_text"]).split()) for row in packet["narration_revisions"]
        ),
        "director_sha256": hashlib.sha256(director_path.read_bytes()).hexdigest(),
        "blueprint_sha256": hashlib.sha256(blueprint_path.read_bytes()).hexdigest(),
        "receipt_sha256": receipt_sha,
        "packet_sha256": packet_sha,
        "public_write": False,
        "uploads": 0,
        "browser_or_cdp_actions": 0,
        "publication_authority": False,
        "factual_authority": False,
    }
    result_path = evidence_root / "narration_revision_application_v2.json"
    result_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return result


def run_batched(
    *, director_path: Path, blueprint_path: Path, failed_output_root: Path,
    evidence_root: Path, control_root: Path, batch_size: int,
) -> dict[str, Any]:
    if not 1 <= batch_size <= 5:
        raise ValueError("narration_revision_batch_size_invalid")
    director = json.loads(director_path.read_text(encoding="utf-8"))
    blueprint = json.loads(blueprint_path.read_text(encoding="utf-8"))
    if len(director.get("revision_history") or ()) != 1:
        raise RuntimeError("narration_revision_requires_exactly_one_prior_revision")
    rows = measured_short_rows(director=director, failed_output_root=failed_output_root)
    prior_receipts = []
    for name in ("narration_revision_receipt_v2.json", "narration_revision_resume_receipt_v2.json"):
        path = evidence_root / name
        if path.is_file():
            prior_receipts.append({
                "path": str(path.resolve()),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
    evidence_root.mkdir(parents=True, exist_ok=True)
    accepted_rows: list[dict[str, Any]] = []
    batch_receipts: list[dict[str, Any]] = []
    selected_models_by_batch: dict[str, str] = {}
    for offset in range(0, len(rows), batch_size):
        batch_number = offset // batch_size + 1
        batch_id = f"batch_{batch_number:02d}"
        batch = rows[offset:offset + batch_size]
        receipt_path = evidence_root / f"narration_revision_{batch_id}_receipt_v2.json"
        batch_packet_path = evidence_root / f"narration_revision_{batch_id}_packet_v2.json"
        if receipt_path.is_file() and batch_packet_path.is_file():
            prior_batch_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            prior_batch_packet = json.loads(batch_packet_path.read_text(encoding="utf-8"))
            ok, _, _, _ = narration_revision_validator(batch)(
                json.dumps(prior_batch_packet, ensure_ascii=False)
            )
            if prior_batch_receipt.get("terminal_disposition") != "ACCEPTED" or not ok:
                raise RuntimeError(f"narration_revision_persisted_batch_invalid:{batch_id}")
            accepted_rows.extend(prior_batch_packet["narration_revisions"])
            selected_models_by_batch[batch_id] = str(prior_batch_receipt["selected_model"])
            batch_receipts.append({
                "batch_id": batch_id,
                "path": str(receipt_path.resolve()),
                "sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
                "packet_path": str(batch_packet_path.resolve()),
                "packet_sha256": hashlib.sha256(batch_packet_path.read_bytes()).hexdigest(),
                "selected_model": prior_batch_receipt["selected_model"],
                "attempted_models": [
                    row["requested_model"] for row in prior_batch_receipt["attempts"]
                ],
                "resumed_from_persisted_acceptance": True,
            })
            continue
        governed_input = {
            "variant_id": "short_9x16",
            "revision_number": 2,
            "batch_id": batch_id,
            "batch_count": (len(rows) + batch_size - 1) // batch_size,
            "rows": batch,
            "prior_whole_packet_blocker_receipts": prior_receipts,
        }
        invocation_id = f"v2-creative-revision-short-narration-timing-{batch_id}-v1"
        budget = RetryBudget(
            logical_invocation_id=invocation_id,
            max_total_provider_attempts=6,
            max_fallback_transitions=2,
            max_same_model_retries=1,
            max_structured_output_repair_attempts=1,
            wall_clock_budget_seconds=900.0,
            per_model_max_attempts=(2, 2, 2),
        )

        def provider(prompt_text: str, model: str, timeout: float):
            return call_nine_router(
                prompt_text, model, timeout, max_tokens=2200, temperature=0.1, stream=True
            )

        with llm_cycle_budget_scope(invocation_id, control_root=control_root):
            summary = routed_llm_invocation(
                prompt=_prompt(batch),
                role_task_id=ROLE_V2_CREATIVE_REVISION_AUTHOR,
                logical_invocation_id=invocation_id,
                work_item_id=f"short_9x16:narration-timing:{batch_id}",
                timeout_seconds=300.0,
                validator=narration_revision_validator(batch),
                provider_call=provider,
                governed_input=governed_input,
                prompt_template=PROMPT_TEMPLATE,
                prompt_version=PROMPT_VERSION,
                budget=budget,
                repair_prompt_builder=_repair_prompt,
            )
        receipt = {key: value for key, value in summary.items() if key != "output"}
        receipt.update({
            "schema_version": "contentops.retention_native.narration_revision_batch_receipt.v2",
            "status": summary["terminal_disposition"],
            "batch_id": batch_id,
            "shot_ids": [row["shot_id"] for row in batch],
            "governed_input_hash": logical_hash(governed_input),
            "public_write": False,
            "publication_authority": False,
            "factual_authority": False,
        })
        receipt_path.write_text(
            json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        if summary["terminal_disposition"] != "ACCEPTED":
            raise RuntimeError(
                f"narration_revision_batch_blocked:{batch_id}:{summary['terminal_disposition']}"
            )
        batch_packet = summary["output"]
        batch_packet_path.write_text(
            json.dumps(batch_packet, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        accepted_rows.extend(batch_packet["narration_revisions"])
        selected_models_by_batch[batch_id] = str(summary["selected_model"])
        batch_receipts.append({
            "batch_id": batch_id,
            "path": str(receipt_path.resolve()),
            "sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
            "packet_path": str(batch_packet_path.resolve()),
            "packet_sha256": hashlib.sha256(batch_packet_path.read_bytes()).hexdigest(),
            "selected_model": summary["selected_model"],
            "attempted_models": [row["requested_model"] for row in summary["attempts"]],
        })
    packet = {
        "schema_version": SCHEMA_VERSION,
        "narration_revisions": accepted_rows,
        "revision_rationale": "Three bounded contiguous model-authored batches preserve natural pace within the accepted 56-second short.",
        "public_write": False,
        "publication_authority": False,
        "factual_authority": False,
    }
    ok, failure, _, diagnostic = narration_revision_validator(rows)(
        json.dumps(packet, ensure_ascii=False)
    )
    if not ok:
        raise RuntimeError(f"narration_revision_aggregate_invalid:{failure}:{diagnostic}")
    packet_path = evidence_root / "narration_revision_packet_v2.json"
    packet_path.write_text(
        json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    aggregate_receipt = {
        "schema_version": "contentops.retention_native.narration_revision_aggregate_receipt.v2",
        "status": "PASS",
        "revision_number": 2,
        "batch_size": batch_size,
        "batch_receipts": batch_receipts,
        "prior_whole_packet_blocker_receipts": prior_receipts,
        "public_write": False,
        "publication_authority": False,
        "factual_authority": False,
    }
    aggregate_path = evidence_root / "narration_revision_aggregate_receipt_v2.json"
    aggregate_path.write_text(
        json.dumps(aggregate_receipt, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    aggregate_sha = hashlib.sha256(aggregate_path.read_bytes()).hexdigest()
    packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
    unique_models = tuple(dict.fromkeys(selected_models_by_batch.values()))
    apply_narration_revision(
        director=director,
        blueprint=blueprint,
        packet=packet,
        selected_model=unique_models[0] if len(unique_models) == 1 else None,
        selected_models_by_batch=selected_models_by_batch,
        receipt_sha256=aggregate_sha,
        packet_sha256=packet_sha,
    )
    director_path.write_text(
        json.dumps(director, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    blueprint_path.write_text(
        json.dumps(blueprint, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    result = {
        "schema_version": "contentops.retention_native.narration_revision_application.v2",
        "status": "PASS",
        "revision_number": 2,
        "execution_shape": "SMALL_CONTIGUOUS_BATCHES",
        "selected_models_by_batch": selected_models_by_batch,
        "batch_receipts": batch_receipts,
        "shot_ids": [row["shot_id"] for row in rows],
        "before_word_count": sum(len(str(row["narration_text"]).split()) for row in rows),
        "after_word_count": sum(len(str(row["narration_text"]).split()) for row in accepted_rows),
        "director_sha256": hashlib.sha256(director_path.read_bytes()).hexdigest(),
        "blueprint_sha256": hashlib.sha256(blueprint_path.read_bytes()).hexdigest(),
        "aggregate_receipt_sha256": aggregate_sha,
        "packet_sha256": packet_sha,
        "public_write": False,
        "uploads": 0,
        "browser_or_cdp_actions": 0,
        "publication_authority": False,
        "factual_authority": False,
    }
    result_path = evidence_root / "narration_revision_application_v2.json"
    result_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--director", type=Path, required=True)
    parser.add_argument("--blueprint", type=Path, required=True)
    parser.add_argument("--failed-output-root", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--control-root", type=Path, required=True)
    parser.add_argument("--resume-receipt", type=Path)
    parser.add_argument("--batch-size", type=int)
    args = parser.parse_args(argv)
    call = run_batched if args.batch_size else run
    kwargs = {
        "director_path": args.director.resolve(),
        "blueprint_path": args.blueprint.resolve(),
        "failed_output_root": args.failed_output_root.resolve(),
        "evidence_root": args.evidence_root.resolve(),
        "control_root": args.control_root.resolve(),
    }
    if args.batch_size:
        kwargs["batch_size"] = args.batch_size
    else:
        kwargs["resume_receipt"] = (
            args.resume_receipt.resolve() if args.resume_receipt else None
        )
    print(json.dumps(call(**kwargs), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
