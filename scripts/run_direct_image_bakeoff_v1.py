"""Run the resumable, no-retry Tier2 direct-image diagnostic bakeoff."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from PIL import Image, ImageDraw, ImageOps

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from live_contentops.direct_image_api_v1 import (  # noqa: E402
    ENV_API_KEY,
    IMAGE_PATH,
    MAX_CALLS,
    MAX_WALL_SECONDS,
    OWNER_MODELS,
    ImageGenerationResult,
    credential_presence,
    generate_image,
    resolve_base_url,
)

SMOKE_PROMPT = (
    "Premium institutional editorial illustration for a financial-news publication: "
    "global central-bank policy uncertainty represented through architecture, light, "
    "paper documents and abstract market geometry; dark restrained palette; sophisticated "
    "magazine art direction; no logos; no text; no numbers; no identifiable real person."
)

ARCHETYPES = {
    "macro_central_bank": (
        "Premium institutional financial-news editorial illustration about central-bank "
        "policy uncertainty, expressed through monumental civic architecture, restrained "
        "light, paper textures and abstract market geometry. Reserve generous clean negative "
        "space for a headline and chart overlay. Dark restrained palette, sophisticated "
        "magazine art direction, no logos, no text, no numbers, no documents, no real people."
    ),
    "corporate_earnings": (
        "Premium institutional financial-news editorial illustration about corporate earnings "
        "and operating leverage, expressed through modern structural forms, controlled light, "
        "material textures and abstract business geometry. Reserve generous clean negative "
        "space for a headline and chart overlay. Restrained editorial palette, no logos, no "
        "text, no numbers, no documents, no screenshots, no real people."
    ),
    "geopolitical_trade": (
        "Premium institutional financial-news editorial illustration about geopolitical trade "
        "friction, expressed through ports, modular routes, layered borders and abstract global "
        "commerce geometry. Reserve generous clean negative space for a headline and chart "
        "overlay. Restrained sophisticated magazine palette, no flags, no logos, no text, no "
        "numbers, no documents, no documentary simulation, no real people."
    ),
}

ASPECTS = {"landscape": (1536, 864), "vertical": (864, 1536)}
JOURNAL_NAME = "attempt_journal.json"
JOURNAL_SCHEMA = "contentops.tier2_direct_image_attempt_journal.v1"


@dataclass(frozen=True)
class Cell:
    key: str
    model: str
    phase: str
    archetype: str | None
    aspect: str
    width: int
    height: int
    prompt: str
    output_path: Path


Generate = Callable[..., ImageGenerationResult]


def _model_slug(model: str) -> str:
    return model.replace("/", "_").replace(".", "_")


def _cells(output_root: Path, models: tuple[str, ...]) -> list[Cell]:
    cells: list[Cell] = []
    for model in models:
        slug = _model_slug(model)
        cells.append(
            Cell(
                key=f"smoke:{model}",
                model=model,
                phase="smoke",
                archetype=None,
                aspect="square",
                width=1024,
                height=1024,
                prompt=SMOKE_PROMPT,
                output_path=output_root / "smoke" / f"{slug}.png",
            )
        )
        for archetype, base_prompt in ARCHETYPES.items():
            for aspect, (width, height) in ASPECTS.items():
                suffix = (
                    " Compose natively for a cinematic 16:9 frame."
                    if aspect == "landscape"
                    else " Compose natively for a vertical 9:16 frame."
                )
                cells.append(
                    Cell(
                        key=f"bakeoff:{model}:{archetype}:{aspect}",
                        model=model,
                        phase="bakeoff",
                        archetype=archetype,
                        aspect=aspect,
                        width=width,
                        height=height,
                        prompt=base_prompt + suffix,
                        output_path=(
                            output_root / aspect / f"{slug}__{archetype}.png"
                        ),
                    )
                )
    return cells


def _artifact(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        content = path.read_bytes()
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            width, height = image.size
            content_type = Image.MIME.get(image.format or "", "")
    except Exception:
        return None
    if width < 1 or height < 1 or not content_type.startswith("image/"):
        return None
    return {
        "output_file": str(path),
        "output_sha256": hashlib.sha256(content).hexdigest(),
        "width": int(width),
        "height": int(height),
        "content_type": content_type,
        "bytes": len(content),
    }


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _load_journal(output_root: Path) -> dict[str, Any]:
    path = output_root / JOURNAL_NAME
    if not path.exists():
        return {"schema_version": JOURNAL_SCHEMA, "records": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("attempt_journal_malformed_no_provider_calls_allowed") from exc
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != JOURNAL_SCHEMA
        or not isinstance(payload.get("records"), dict)
    ):
        raise RuntimeError("attempt_journal_malformed_no_provider_calls_allowed")
    return payload


def _cell_fields(cell: Cell) -> dict[str, Any]:
    return {
        "cell_key": cell.key,
        "requested_model": cell.model,
        "phase": cell.phase,
        "archetype": cell.archetype,
        "aspect": cell.aspect,
        "requested_width": cell.width,
        "requested_height": cell.height,
        "prompt_hash": hashlib.sha256(cell.prompt.encode("utf-8")).hexdigest(),
    }


def _reconciled_result(cell: Cell, artifact: dict[str, Any]) -> dict[str, Any]:
    return _cell_fields(cell) | {
        "effective_model": None,
        "provider": "ai.api-cheap.site",
        "invocation_id": None,
        "status": "SUCCESS",
        "protocol_mode": "reconciled_existing_artifact",
        "width": artifact["width"],
        "height": artifact["height"],
        "content_type": artifact["content_type"],
        "output_file": artifact["output_file"],
        "output_sha256": artifact["output_sha256"],
        "output_bytes": artifact["bytes"],
        "latency_ms": None,
        "usage": None,
        "cost": None,
        "error_class": None,
        "http_status": None,
        "call_count": 1,
        "retry_state": "NO_RETRY",
        "request_outcome": "RECONCILED_VALID_ARTIFACT",
        "response_schema": None,
        "source_url_redacted": None,
    }


def _ambiguous_process_loss(cell: Cell) -> dict[str, Any]:
    return _cell_fields(cell) | {
        "effective_model": None,
        "provider": "ai.api-cheap.site",
        "invocation_id": None,
        "status": "AMBIGUOUS",
        "protocol_mode": "sync",
        "width": None,
        "height": None,
        "content_type": None,
        "output_file": None,
        "output_sha256": None,
        "latency_ms": None,
        "usage": None,
        "cost": None,
        "error_class": "WORKER_LOSS",
        "http_status": None,
        "call_count": 1,
        "retry_state": "NO_RETRY",
        "request_outcome": "AMBIGUOUS_PROVIDER_OUTCOME",
        "response_schema": "unfinished_dispatch_journal_record",
        "source_url_redacted": None,
    }


def _reconcile(
    output_root: Path, cells: list[Cell], journal: dict[str, Any]
) -> dict[str, Any]:
    records: dict[str, Any] = journal["records"]
    report: dict[str, Any] = {
        "valid_existing_artifacts": [],
        "unfinished_dispatches_marked_no_retry": [],
        "invalid_existing_artifacts_marked_no_retry": [],
    }
    for cell in cells:
        artifact = _artifact(cell.output_path)
        record = records.get(cell.key)
        if artifact:
            result = _reconciled_result(cell, artifact)
            if isinstance(record, dict) and isinstance(record.get("result"), dict):
                result = record["result"] | _cell_fields(cell) | {
                    "status": "SUCCESS",
                    "output_file": artifact["output_file"],
                    "output_sha256": artifact["output_sha256"],
                    "output_bytes": artifact["bytes"],
                    "width": artifact["width"],
                    "height": artifact["height"],
                    "content_type": artifact["content_type"],
                    "retry_state": "NO_RETRY",
                }
            records[cell.key] = {"state": "FINAL", "result": result}
            report["valid_existing_artifacts"].append(
                {"cell_key": cell.key} | artifact
            )
        elif isinstance(record, dict) and record.get("state") == "DISPATCH_STARTED":
            result = _ambiguous_process_loss(cell)
            records[cell.key] = {"state": "FINAL", "result": result}
            report["unfinished_dispatches_marked_no_retry"].append(cell.key)
        elif cell.output_path.exists() and record is None:
            result = _ambiguous_process_loss(cell) | {
                "status": "FAILED",
                "error_class": "MALFORMED_RESPONSE",
                "request_outcome": "RECONCILED_INVALID_ARTIFACT",
                "response_schema": "invalid_existing_image_file",
            }
            records[cell.key] = {"state": "FINAL", "result": result}
            report["invalid_existing_artifacts_marked_no_retry"].append(cell.key)
    _atomic_json(output_root / JOURNAL_NAME, journal)
    _atomic_json(output_root / "artifact_reconciliation.json", report)
    return report


def _result_for(journal: dict[str, Any], key: str) -> dict[str, Any] | None:
    record = journal["records"].get(key)
    if isinstance(record, dict) and isinstance(record.get("result"), dict):
        return record["result"]
    return None


def _call_count(journal: dict[str, Any]) -> int:
    total = 0
    for record in journal["records"].values():
        if not isinstance(record, dict):
            continue
        result = record.get("result")
        if isinstance(result, dict):
            total += int(result.get("call_count") or 0)
        elif record.get("state") == "DISPATCH_STARTED":
            total += 1
    return total


def _attempt_once(
    *,
    cell: Cell,
    output_root: Path,
    journal: dict[str, Any],
    generate: Generate,
    timeout_seconds: float,
) -> dict[str, Any]:
    if _result_for(journal, cell.key) is not None:
        return _result_for(journal, cell.key) or {}
    journal["records"][cell.key] = {
        "state": "DISPATCH_STARTED",
        "dispatch_policy": "ONE_ATTEMPT_NO_AUTOMATIC_RETRY",
        "cell": _cell_fields(cell),
    }
    _atomic_json(output_root / JOURNAL_NAME, journal)
    try:
        generated = generate(
            model=cell.model,
            prompt=cell.prompt,
            width=cell.width,
            height=cell.height,
            output_file=cell.output_path,
            timeout_seconds=timeout_seconds,
            max_calls=1,
        )
        result = generated.to_dict() | _cell_fields(cell)
    except BaseException as exc:
        result = _ambiguous_process_loss(cell) | {"response_schema": type(exc).__name__}
    journal["records"][cell.key] = {"state": "FINAL", "result": result}
    _atomic_json(output_root / JOURNAL_NAME, journal)
    return result


def _contact_sheet(paths: list[Path], output: Path, title: str, columns: int = 3) -> str | None:
    existing = [path for path in paths if _artifact(path)]
    if not existing:
        return None
    cell_width, cell_height, label_height = 480, 320, 42
    rows = (len(existing) + columns - 1) // columns
    canvas = Image.new("RGB", (columns * cell_width, 72 + rows * (cell_height + label_height)), "#11151b")
    draw = ImageDraw.Draw(canvas)
    draw.text((20, 22), title, fill="#f2f4f8")
    for index, path in enumerate(existing):
        row, column = divmod(index, columns)
        left, top = column * cell_width, 72 + row * (cell_height + label_height)
        with Image.open(path) as source:
            tile = ImageOps.contain(source.convert("RGB"), (cell_width - 20, cell_height - 20))
        canvas.paste(tile, (left + (cell_width - tile.width) // 2, top + (cell_height - tile.height) // 2))
        draw.text((left + 10, top + cell_height + 10), path.stem[:68], fill="#cbd2dc")
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="JPEG", quality=88, optimize=True)
    return str(output)


def _write_review_package(output_root: Path, manifest: dict[str, Any]) -> None:
    serialized = json.dumps(manifest, indent=2, sort_keys=True)
    if "Bearer " in serialized or "authorization" in serialized.lower():
        raise RuntimeError("sanitized_manifest_secret_guard_failed")
    (output_root / "generation_manifest.json").write_text(serialized + "\n", encoding="utf-8")
    protocol = {
        "provider": manifest["provider"],
        "base_url": manifest["base_url"],
        "path": manifest["path"],
        "credential_presence": manifest["credential_presence"],
        "dispatch_policy": manifest["dispatch_policy"],
        "total_generation_calls": manifest["total_generation_calls"],
        "status": manifest["status"],
    }
    _atomic_json(output_root / "sanitized_protocol_evidence.json", protocol)
    review = f"""# Tier2 Direct Image Bakeoff Review

Status: `{manifest['status']}`

Review authority: `PROVISIONAL_IMAGE_BAKEOFF_AWAITING_JIM_CHATGPT_VISUAL_REVIEW`

These images are illustrative creative assets only. They are not factual evidence,
documentary depictions, charts, documents, screenshots, or real-person imagery.

Provider: `ai.api-cheap.site` through the task-only direct diagnostic boundary.
Generation calls reconciled/attempted: `{manifest['total_generation_calls']}` / `{manifest['maximum_generation_calls']}`.
Dispatch policy: `ONE_ATTEMPT_NO_AUTOMATIC_RETRY`.

No model is automatically declared the winner. Owner/ChatGPT visual review is required.
"""
    (output_root / "REVIEW_README.md").write_text(review, encoding="utf-8")


def run(
    output_root: Path,
    *,
    models: tuple[str, ...] = OWNER_MODELS,
    run_smoke: bool = True,
    generate: Generate = generate_image,
    timeout_seconds: float = MAX_WALL_SECONDS,
) -> dict[str, Any]:
    for name in ("smoke", "landscape", "vertical", "contact_sheets"):
        (output_root / name).mkdir(parents=True, exist_ok=True)
    cells = _cells(output_root, models)
    by_key = {cell.key: cell for cell in cells}
    journal = _load_journal(output_root)
    reconciliation = _reconcile(output_root, cells, journal)
    has_credential = credential_presence()[ENV_API_KEY] == "PRESENT"

    if run_smoke and has_credential:
        for model in models:
            cell = by_key[f"smoke:{model}"]
            if _result_for(journal, cell.key) is None and _call_count(journal) < MAX_CALLS:
                _attempt_once(cell=cell, output_root=output_root, journal=journal, generate=generate, timeout_seconds=timeout_seconds)

    successful_models = [
        model
        for model in models
        if (_result_for(journal, f"smoke:{model}") or {}).get("status") == "SUCCESS"
    ]
    if has_credential:
        for model in successful_models:
            for cell in cells:
                if cell.model != model or cell.phase != "bakeoff":
                    continue
                if _result_for(journal, cell.key) is None and _call_count(journal) < MAX_CALLS:
                    _attempt_once(cell=cell, output_root=output_root, journal=journal, generate=generate, timeout_seconds=timeout_seconds)

    results = [result for cell in cells if (result := _result_for(journal, cell.key)) is not None]
    artifacts = [
        {"cell_key": cell.key, "model": cell.model, "phase": cell.phase, "archetype": cell.archetype, "aspect": cell.aspect} | artifact
        for cell in cells
        if (artifact := _artifact(cell.output_path)) is not None
    ]
    sheets: dict[str, str] = {}
    for model in successful_models:
        paths = [cell.output_path for cell in cells if cell.model == model]
        sheet = _contact_sheet(paths, output_root / "contact_sheets" / f"{_model_slug(model)}__contact_sheet.jpg", f"{model} - illustrative Tier2 bakeoff")
        if sheet:
            sheets[f"model:{model}"] = sheet
    for aspect in ASPECTS:
        paths = [cell.output_path for cell in cells if cell.aspect == aspect and cell.model in successful_models]
        sheet = _contact_sheet(paths, output_root / "contact_sheets" / f"all_models__{aspect}.jpg", f"All successful models - {aspect} comparison")
        if sheet:
            sheets[f"all_models:{aspect}"] = sheet
    contact_sheet_artifacts = {
        key: metadata
        for key, path in sheets.items()
        if (metadata := _artifact(Path(path))) is not None
    }

    ambiguous = any(row.get("status") == "AMBIGUOUS" for row in results)
    expected_success_cells = [cell for cell in cells if cell.model in successful_models]
    bakeoff_complete = bool(successful_models) and all(
        (_result_for(journal, cell.key) or {}).get("status") == "SUCCESS"
        for cell in expected_success_cells
    )
    if not has_credential:
        status = "BLOCKED_CREDENTIAL_MISSING"
    elif ambiguous:
        status = "COMPLETE_WITH_AMBIGUOUS_PROVIDER_OUTCOME"
    elif bakeoff_complete:
        status = "BAKEOFF_COMPLETE_FOR_SUCCESSFUL_MODELS"
    elif successful_models:
        status = "PARTIAL_BAKEOFF"
    else:
        status = "NO_MODEL_GENERATION_SUCCESS"

    manifest = {
        "schema_version": "contentops.tier2_direct_image_bakeoff.v1",
        "status": status,
        "credential_presence": credential_presence(),
        "credential_isolation": "AI_API_CHEAP_API_KEY_ONLY; NINE_ROUTER_API_KEY_NOT_READ",
        "provider": "ai.api-cheap.site",
        "base_url": resolve_base_url(),
        "path": IMAGE_PATH,
        "request_content_type": "application/json",
        "request_schema": ["model", "prompt", "size", "n", "response_format"],
        "dispatch_policy": "ONE_ATTEMPT_NO_AUTOMATIC_RETRY",
        "hard_wall_seconds": min(float(timeout_seconds), MAX_WALL_SECONDS),
        "total_generation_calls": _call_count(journal),
        "maximum_generation_calls": MAX_CALLS,
        "successful_models": successful_models,
        "model_outcomes": {
            model: _result_for(journal, f"smoke:{model}") for model in models
        },
        "results": results,
        "artifacts": artifacts,
        "artifact_reconciliation": reconciliation,
        "contact_sheets": sheets,
        "contact_sheet_artifacts": contact_sheet_artifacts,
        "review_status": "PROVISIONAL_IMAGE_BAKEOFF_AWAITING_JIM_CHATGPT_VISUAL_REVIEW",
        "output_root": str(output_root),
    }
    _write_review_package(output_root, manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path(tempfile.gettempdir()) / "tier2-direct-image-api-real-smoke-bakeoff-v1")
    parser.add_argument("--model", action="append", choices=OWNER_MODELS, dest="models")
    parser.add_argument("--skip-smoke", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, default=MAX_WALL_SECONDS)
    args = parser.parse_args()
    manifest = run(args.output_dir.resolve(), models=tuple(args.models or OWNER_MODELS), run_smoke=not args.skip_smoke, timeout_seconds=args.timeout_seconds)
    print(json.dumps({"status": manifest["status"], "output_root": manifest["output_root"], "total_generation_calls": manifest["total_generation_calls"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
