from __future__ import annotations

import csv
import json
import re
from pathlib import Path


TASK_ROOT = Path(__file__).resolve().parent.parent


def require(relative_path: str, minimum_bytes: int = 1) -> Path:
    path = TASK_ROOT / relative_path
    assert path.is_file(), f"missing required file: {relative_path}"
    assert path.stat().st_size >= minimum_bytes, f"file too small: {relative_path}"
    return path


required_files = [
    "README.md",
    "article/article.md",
    "article/article.html",
    "article/publication.css",
    "charts/census_release_excerpt.png",
    "charts/census_release_excerpt.svg",
    "charts/irs_refund_impulse.png",
    "charts/irs_refund_impulse.svg",
    "charts/july_category_mix.png",
    "charts/july_category_mix.svg",
    "charts/retail_path_2026.png",
    "charts/retail_path_2026.svg",
    "media/us-commissary-shoppers-fort-belvoir.jpg",
    "media/kevin-warsh-fomc-press-conference.jpg",
    "render/article-desktop-full.png",
    "render/article-desktop-hero.png",
    "render/article-desktop-policy-panel.png",
    "render/article-desktop-source-treatment.png",
    "factual_source_manifest.json",
    "media_provenance_rights_manifest.json",
    "evidence/execution_record.json",
    "evidence/public_write_zero.json",
    "evidence/validation_report.md",
]
for item in required_files:
    require(item, 20)

for manifest in [
    "factual_source_manifest.json",
    "media_provenance_rights_manifest.json",
    "evidence/execution_record.json",
    "evidence/public_write_zero.json",
]:
    with require(manifest).open(encoding="utf-8") as handle:
        json.load(handle)

html = require("article/article.html").read_text(encoding="utf-8")
markdown = require("article/article.md").read_text(encoding="utf-8")

expected_headline = "The consumer didn’t fall off a cliff. The refund bridge just ended."
assert expected_headline in html and expected_headline in markdown
assert "has not been published" in html and "has not been published" in markdown

for source in re.findall(r'<img[^>]+src="([^"]+)"', html):
    assert not source.startswith(("http://", "https://")), f"remote image in article: {source}"
    assert (TASK_ROOT / "article" / source).resolve().is_file(), f"broken local image: {source}"

with require("source_data/retail_sales_2026.csv").open(newline="", encoding="utf-8") as handle:
    retail_rows = list(csv.DictReader(handle))
assert retail_rows[-1] == {
    "month": "2026-07",
    "total_usd_millions": "763602",
    "ex_auto_gas_usd_millions": "562297",
}

with require("source_data/irs_refunds_may_2026.csv").open(newline="", encoding="utf-8") as handle:
    refund_rows = {row["as_of_year"]: row for row in csv.DictReader(handle)}
assert refund_rows["2025"]["total_refund_amount_usd_billions"] == "274.979"
assert refund_rows["2026"]["total_refund_amount_usd_billions"] == "324.757"
assert round(324.757 - 274.979, 3) == 49.778

assert not (TASK_ROOT / "media/us-consumer-produce-aisle.jpg").exists()
assert not (TASK_ROOT / "source_data/census-advance-retail-sales-july-2026.pdf").exists()
assert not (TASK_ROOT / "tmp").exists()

for forbidden in ["substack.com/publish", "publication_provider_call", "CDP 9222", "CDP 9223"]:
    assert forbidden not in html

print("PASS: package structure, manifests, local media links, source extracts, and exclusion gates validated")
