"""Focused deterministic validation for the Frozen Without Breaking locale proof."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from decimal import Decimal
from pathlib import Path
from typing import Any


def flatten(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return "\n".join(flatten(item) for item in value.values())
    if isinstance(value, list):
        return "\n".join(flatten(item) for item in value)
    return ""


def digits(value: str) -> list[str]:
    return [item.lstrip("0") or "0" for item in re.findall(r"\d+", value)]


def pauses(value: str) -> list[str]:
    return re.findall(r"\[PAUSE\s+([0-9]+(?:\.[0-9]+)?)\]", value, re.I)


NUMERIC_SHORT_KEYS = {
    "paradox.payroll.value",
    "paradox.rate.value",
    "arithmetic.employment.value",
    "arithmetic.laborForce.value",
    "arithmetic.unemployed.value",
    "doors.hires.then",
    "doors.hires.now",
    "doors.quits.then",
    "doors.quits.now",
    "doors.layoffs.then",
    "doors.layoffs.now",
    "engine.demand.value",
    "engine.output.value",
    "engine.hours.value",
    "engine.productivity.value",
}


def display_number(value: str) -> Decimal:
    text = unicodedata.normalize("NFKC", value).upper().replace("−", "-").strip()
    sign = Decimal(-1) if "-" in text else Decimal(1)
    ten_thousand = re.search(r"(\d+)万([\d,]*)", text)
    if ten_thousand:
        remainder = int((ten_thousand.group(2) or "0").replace(",", ""))
        return sign * Decimal(int(ten_thousand.group(1)) * 10_000 + remainder)
    match = re.search(r"\d+(?:[.,]\d+)?", text)
    if not match:
        raise ValueError(value)
    number = Decimal(match.group(0).replace(",", "."))
    if "K" in text or "MIL" in text:
        number *= 1000
    return sign * number


def validate(locale_dir: Path) -> dict[str, Any]:
    payloads = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(locale_dir.glob("*.json"))
    }
    required_locales = {"en", "es", "pt-BR", "ja"}
    errors: list[str] = []
    if set(payloads) != required_locales:
        errors.append(f"locale_set:{sorted(payloads)}")
    english_keys = set(payloads["en"]["short"]["strings"])
    english_numbers = {
        key: display_number(payloads["en"]["short"]["strings"][key])
        for key in NUMERIC_SHORT_KEYS
    }
    english_pauses = {
        chapter: pauses(text)
        for chapter, text in payloads["en"]["longform"]["narration_chapters"].items()
    }
    expected_anchor_ids: set[str] | None = None
    locale_results: dict[str, Any] = {}
    for locale, payload in payloads.items():
        local_errors: list[str] = []
        if payload.get("schema") != "contentops.v2.localized_editorial_package.v1":
            local_errors.append("schema")
        if payload.get("locale") != locale:
            local_errors.append("locale_tag")
        chapters = payload.get("longform", {}).get("narration_chapters", {})
        if set(chapters) != set(english_pauses):
            local_errors.append("chapter_set")
        for chapter, expected in english_pauses.items():
            if pauses(str(chapters.get(chapter, ""))) != expected:
                local_errors.append(f"pause_controls:{chapter}")
        strings = payload.get("short", {}).get("strings", {})
        if set(strings) != english_keys:
            local_errors.append("stable_string_keys")
        else:
            for key, expected in english_numbers.items():
                try:
                    actual = display_number(str(strings[key]))
                except ValueError:
                    local_errors.append(f"numeric_display_unparseable:{key}")
                    continue
                if actual != expected:
                    local_errors.append(f"numeric_display_changed:{key}:{actual}:{expected}")
        segments = payload.get("short", {}).get("narration_segments", [])
        if [item.get("id") for item in segments] != [f"caption.{index:02d}" for index in range(1, 11)]:
            local_errors.append("short_segment_ids")
        assertions = payload.get("anchor_assertions", [])
        if locale == "en":
            anchor_count = 0
        else:
            ids = [str(item.get("id", "")) for item in assertions]
            if len(ids) != len(set(ids)) or len(ids) < 40:
                local_errors.append("anchor_ids")
            if expected_anchor_ids is None:
                expected_anchor_ids = set(ids)
            elif set(ids) != expected_anchor_ids:
                local_errors.append("anchor_set_mismatch")
            for assertion in assertions:
                surface = str(assertion.get("localized_surface", "")).strip()
                if not surface:
                    local_errors.append(f"empty_anchor_surface:{assertion.get('id')}")
            anchor_count = len(assertions)
        locale_results[locale] = {
            "result": "PASS" if not local_errors else "FAIL",
            "chapter_count": len(chapters),
            "stable_string_key_count": len(strings),
            "short_segment_count": len(segments),
            "anchor_assertion_count": anchor_count,
            "errors": local_errors,
        }
        errors.extend(f"{locale}:{item}" for item in local_errors)
    return {
        "schema": "contentops.v2.fwb_locale_validation.v1",
        "result": "PASS_FACTUAL_ANCHORS" if not errors else "FAIL_FACTUAL_ANCHORS",
        "anchor_set_size": len(expected_anchor_ids or set()),
        "locales": locale_results,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("locale_dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.locale_dir)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["result"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
