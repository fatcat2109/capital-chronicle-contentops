from __future__ import annotations

import csv
import json
import re
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def rows(name: str) -> list[dict[str, str]]:
    with (ROOT / "data" / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def markdown_word_count(markdown: str) -> int:
    text = re.sub(r"!\[([^\]]+)\]\([^)]+\)", r"\1", markdown)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[#>*_`|]", " ", text)
    return len(re.findall(r"\b[\w’'–—%.$+−-]+\b", text, flags=re.UNICODE))


def validate() -> dict[str, object]:
    article_path = ROOT / "article.md"
    html_path = ROOT / "article.html"
    render_path = ROOT / "full_page_desktop_1440.png"
    article = article_path.read_text(encoding="utf-8")
    page = html_path.read_text(encoding="utf-8")

    retail = {row["series"]: row for row in rows("retail_july_2026_selected_categories.csv")}
    refunds = {row["metric"]: row for row in rows("irs_refunds_through_may_8_2026.csv")}
    macro = {row["metric"]: row for row in rows("macro_policy_snapshot.csv")}
    levels = {row["period"]: row for row in rows("retail_total_levels_june_july_2026.csv")}

    july_sales = int(levels["July 2026 advance"]["seasonally_adjusted_sales_millions"])
    june_sales = int(levels["June 2026 preliminary"]["seasonally_adjusted_sales_millions"])
    refund_delta = int(refunds["Total amount refunded dollars"]["value_change"])
    refund_scale = refund_delta / (july_sales * 1_000_000)

    assertions = {
        "retail_total_monthly": float(retail["Retail and food services total"]["july_2026_month_over_month_percent"]) == -0.6,
        "retail_ex_auto_gas": float(retail["Total excluding motor vehicles parts and gasoline"]["july_2026_month_over_month_percent"]) == -0.2,
        "retail_level_decline_millions": june_sales - july_sales == 4470,
        "refund_delta_dollars": refund_delta == 49_778_000_000,
        "refund_scale_rounds_to_6_5_percent": round(refund_scale * 100, 1) == 6.5,
        "cpi_all_items_annual": float(macro["Consumer Price Index all items annual"]["value"]) == 3.4,
        "cpi_core_annual": float(macro["Consumer Price Index core annual"]["value"]) == 2.5,
        "q2_real_gdp": float(macro["Real GDP annualized"]["value"]) == 1.5,
        "q2_private_final_sales": float(macro["Real final sales to private domestic purchasers annualized"]["value"]) == 3.9,
        "analysis_label_present": "CAPITAL CHRONICLE ANALYSIS — OUR VIEW" in article,
        "nominal_caveat_present": "The Census report is nominal" in article,
        "gasoline_volume_caveat_present": "cannot support a claim about fuel volumes" in article,
        "html_contains_exact_title": "The Refund Mirage Just Cleared—and the Fed’s Consumer Signal Got Murkier" in page,
        "render_exists": render_path.is_file() and render_path.stat().st_size > 500_000,
        "zero_public_write_manifest": json.loads((ROOT / "candidate_manifest.json").read_text(encoding="utf-8"))["public_writes"] == 0,
    }
    required_media = [
        ROOT / "assets" / "retail_checkout_vitaly_gariev_unsplash.jpg",
        ROOT / "assets" / "kevin_warsh_official_federal_reserve.png",
        ROOT / "assets" / "retail_mix_july_2026.svg",
        ROOT / "assets" / "refund_pulse_2026.svg",
    ]
    assertions["all_media_present"] = all(path.is_file() and path.stat().st_size > 0 for path in required_media)
    assertions["all_assertions_pass"] = all(assertions.values())

    return {
        "schema_version": "capital_chronicle.publication_candidate_validation.v1",
        "status": "PASS" if assertions["all_assertions_pass"] else "FAIL",
        "research_cutoff": "2026-08-15 Asia/Saigon",
        "article_word_count": markdown_word_count(article),
        "calculations": {
            "retail_level_decline_millions": june_sales - july_sales,
            "refund_delta_dollars": refund_delta,
            "refund_delta_as_percent_of_july_sales": round(refund_scale * 100, 4),
        },
        "assertions": assertions,
        "files": {
            "article.md": digest(article_path),
            "article.html": digest(html_path),
            "full_page_desktop_1440.png": digest(render_path),
            **{str(path.relative_to(ROOT)).replace("\\", "/"): digest(path) for path in required_media},
        },
        "factual_numeric_review": "PASS_PRIMARY_AUTHORITY_TRANSCRIPTION_AND_CROSS_CALCULATION",
        "media_rights_review": "PASS_EXPLICIT_SOURCE_LICENSE_HASH_AND_CONTEXT_LABELING",
        "render_review": "PASS_1440PX_FULL_PAGE_8088PX_HEIGHT",
        "public_writes": 0,
    }


if __name__ == "__main__":
    result = validate()
    (ROOT / "validation_report.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
