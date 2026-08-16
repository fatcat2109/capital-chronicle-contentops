"""Fail-closed local translation for governed semantic segments.

Qwen proposes language. The caller-provided semantic contract remains factual authority.
This module never repairs a failed number, direction, entity, unit, chronology, or uncertainty
anchor. A failed segment is rejected and must return to editorial governance.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Mapping, Sequence


class GovernedTranslationError(RuntimeError):
    """A local backend or governed-anchor failure."""


REQUIRED_BACKEND_ID = "Qwen/Qwen3-4B"
REQUIRED_LICENSE = "Apache-2.0"
GOVERNED_FACT_KINDS = {
    "NUMBER",
    "PERCENTAGE",
    "DATE",
    "NAMED_ENTITY",
    "UNIT",
    "SIGN_DIRECTION",
    "CHRONOLOGY",
    "UNCERTAINTY",
}


def _normalized(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = value.replace("−", "-").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", value).strip()


def validate_governed_translation(
    segment: Mapping[str, Any], translated_text: str, target_locale: str
) -> dict[str, Any]:
    """Validate explicit facts on the actual translated segment surface."""

    text = _normalized(translated_text)
    failures: list[dict[str, str]] = []
    results: list[dict[str, str]] = []
    seen: set[str] = set()
    for fact in segment.get("governed_facts", []):
        fact_id = str(fact.get("id", "")).strip()
        kind = str(fact.get("kind", "")).strip()
        if not fact_id or fact_id in seen:
            raise GovernedTranslationError("Governed fact IDs must be non-empty and unique")
        if kind not in GOVERNED_FACT_KINDS:
            raise GovernedTranslationError(f"Unsupported governed fact kind: {kind}")
        seen.add(fact_id)
        accepted = fact.get("accepted_forms", {}).get(target_locale)
        if accepted is None:
            accepted = fact.get("accepted_forms", {}).get("default", [])
        forms = [_normalized(str(item)) for item in accepted if str(item).strip()]
        matched = next((form for form in forms if form in text), None)
        result = "PRESERVED" if matched else "MISSING_OR_CONFLICTING"
        results.append({"id": fact_id, "kind": kind, "result": result, "matched_form": matched or ""})
        if not matched:
            failures.append({"id": fact_id, "kind": kind})
    return {
        "schema": "contentops.v2.governed_translation_validation.v1",
        "segment_id": segment.get("segment_id"),
        "target_locale": target_locale,
        "result": "PASS_GOVERNED_TRANSLATION" if not failures else "FAIL_GOVERNED_TRANSLATION_CLOSED",
        "facts": results,
        "failures": failures,
        "silent_repair_performed": False,
    }


def build_translation_messages(segment: Mapping[str, Any], target_locale: str) -> list[dict[str, str]]:
    facts = [
        {
            "id": fact["id"],
            "kind": fact["kind"],
            "accepted_target_forms": fact.get("accepted_forms", {}).get(target_locale, []),
        }
        for fact in segment.get("governed_facts", [])
    ]
    return [
        {
            "role": "system",
            "content": (
                "You are a local translation component, not factual authority. Translate only "
                "the supplied semantic segment. Preserve every governed fact and uncertainty "
                "marker. Do not add facts, motives, causes, forecasts, or certainty. Return one "
                "JSON object with exactly one key: translated_text."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "target_locale": target_locale,
                    "source_text": segment["source_text"],
                    "governed_facts": facts,
                },
                ensure_ascii=False,
            ),
        },
    ]


class Qwen3LocalTranslator:
    """Optional Transformers adapter that is strictly local-files-only."""

    def __init__(self, model_path: Path, backend_receipt: Mapping[str, Any]):
        self.model_path = model_path.resolve()
        backend = backend_receipt.get("backends", {}).get("qwen3_4b_local", {})
        if backend.get("official_model_id") != REQUIRED_BACKEND_ID:
            raise GovernedTranslationError("Qwen backend identity mismatch")
        if backend.get("license") != REQUIRED_LICENSE:
            raise GovernedTranslationError("Qwen backend must be Apache-2.0")
        if not self.model_path.is_dir():
            raise GovernedTranslationError(
                "Local Qwen3-4B model is not materialized; network fallback is forbidden"
            )

    def translate(self, segment: Mapping[str, Any], target_locale: str) -> dict[str, Any]:
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise GovernedTranslationError(
                "Local transformers runtime is not installed; no external API fallback is allowed"
            ) from exc

        tokenizer = AutoTokenizer.from_pretrained(
            self.model_path, local_files_only=True, trust_remote_code=False
        )
        model = AutoModelForCausalLM.from_pretrained(
            self.model_path, local_files_only=True, trust_remote_code=False, device_map="auto"
        )
        messages = build_translation_messages(segment, target_locale)
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(**inputs, max_new_tokens=1024, do_sample=False)
        generated = outputs[0][inputs.input_ids.shape[-1] :]
        raw = tokenizer.decode(generated, skip_special_tokens=True).strip()
        try:
            translated_text = str(json.loads(raw)["translated_text"]).strip()
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise GovernedTranslationError("Local model did not return the required JSON object") from exc
        validation = validate_governed_translation(segment, translated_text, target_locale)
        if validation["result"] != "PASS_GOVERNED_TRANSLATION":
            raise GovernedTranslationError(json.dumps(validation, ensure_ascii=False))
        return {
            "segment_id": segment["segment_id"],
            "target_locale": target_locale,
            "translated_text": translated_text,
            "validation": validation,
            "backend": REQUIRED_BACKEND_ID,
            "factual_authority": False,
        }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("segment", type=Path)
    validate.add_argument("translation", type=Path)
    validate.add_argument("--locale", required=True)
    translate = sub.add_parser("translate")
    translate.add_argument("segment", type=Path)
    translate.add_argument("--locale", required=True)
    translate.add_argument("--model-path", required=True, type=Path)
    translate.add_argument("--backend-registry", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    segment = json.loads(args.segment.read_text(encoding="utf-8"))
    if args.command == "validate":
        translated_text = args.translation.read_text(encoding="utf-8").strip()
        result = validate_governed_translation(segment, translated_text, args.locale)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["result"] == "PASS_GOVERNED_TRANSLATION" else 1
    registry = json.loads(args.backend_registry.read_text(encoding="utf-8"))
    result = Qwen3LocalTranslator(args.model_path, registry).translate(segment, args.locale)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
