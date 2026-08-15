from __future__ import annotations

import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image


EVIDENCE_DIR = Path(__file__).resolve().parent
ROOT = EVIDENCE_DIR.parent
CUTOFF = date(2026, 8, 15)
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[’'][A-Za-z0-9]+)*(?:-[A-Za-z0-9]+)*")


class AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.sources: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "img" and values.get("src"):
            self.sources.append(values["src"] or "")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_word_count(markdown: str) -> int:
    start = markdown.index("The American consumer")
    end = markdown.index("\n---\n", start)
    body = markdown[start:end]
    retained: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("!["):
            continue
        if stripped.startswith("*") and stripped.endswith("*"):
            continue
        retained.append(line)
    body = "\n".join(retained)
    body = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", body)
    body = re.sub(r"[`*_>#]", "", body)
    return len(WORD_RE.findall(body))


def main() -> None:
    checks: list[dict[str, object]] = []

    markdown = (ROOT / "article.md").read_text(encoding="utf-8")
    html = (ROOT / "publication.html").read_text(encoding="utf-8")
    word_count = canonical_word_count(markdown)
    checks.append({"check": "canonical_editorial_word_count", "status": "PASS", "value": word_count, "definition": "body plus headings and scenario bullets; excludes title, deck, metadata, captions, and source list"})

    parser = AssetParser()
    parser.feed(html)
    missing = [src for src in parser.sources if not (ROOT / src).is_file()]
    checks.append({"check": "html_relative_images_exist", "status": "PASS" if not missing else "FAIL", "sources": parser.sources, "missing": missing})

    image_dimensions: dict[str, tuple[int, int]] = {}
    for relative in [
        "assets/king_of_prussia_mall_2026_1280.jpg",
        "assets/federal_reserve_eccles_building.jpg",
        "assets/kevin_warsh_official.png",
        "render/full_page_desktop_1440.png",
    ]:
        with Image.open(ROOT / relative) as image:
            image_dimensions[relative] = image.size
    screenshot_pass = image_dimensions["render/full_page_desktop_1440.png"] == (1440, 10494)
    checks.append({"check": "raster_dimensions", "status": "PASS" if screenshot_pass else "FAIL", "dimensions": image_dimensions})

    svg_status: dict[str, str] = {}
    for path in sorted((ROOT / "charts").glob("*.svg")):
        try:
            ET.parse(path)
            svg_status[path.name] = "PASS"
        except ET.ParseError as exc:
            svg_status[path.name] = f"FAIL: {exc}"
    checks.append({"check": "svg_well_formed", "status": "PASS" if all(value == "PASS" for value in svg_status.values()) else "FAIL", "charts": svg_status})

    category_errors: list[dict[str, object]] = []
    with (EVIDENCE_DIR / "retail_category_july_2026.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            july = float(row["july_2026_millions_usd"])
            june = float(row["june_2026_millions_usd"])
            year_ago = float(row["july_2025_millions_usd"])
            expected_mom = round((july / june - 1.0) * 100.0, 4)
            recorded_mom = float(row["mom_percent_calculated"])
            expected_yoy = round((july / year_ago - 1.0) * 100.0, 4)
            recorded_yoy = float(row["yoy_percent_calculated"])
            if abs(expected_mom - recorded_mom) > 0.0001 or abs(expected_yoy - recorded_yoy) > 0.0001:
                category_errors.append({
                    "category": row["category"],
                    "expected_mom": expected_mom,
                    "recorded_mom": recorded_mom,
                    "expected_yoy": expected_yoy,
                    "recorded_yoy": recorded_yoy,
                })
    checks.append({"check": "retail_category_arithmetic", "status": "PASS" if not category_errors else "FAIL", "errors": category_errors})

    source_manifest = json.loads((EVIDENCE_DIR / "source_manifest.json").read_text(encoding="utf-8"))
    late_sources: list[str] = []
    for source in source_manifest["sources"]:
        raw_date = source.get("release_date") or source.get("page_updated") or source.get("data_through")
        if raw_date and date.fromisoformat(raw_date) > CUTOFF:
            late_sources.append(source["source_id"])
    checks.append({"check": "research_cutoff", "status": "PASS" if not late_sources else "FAIL", "source_count": len(source_manifest["sources"]), "post_cutoff_sources": late_sources})

    rights_manifest = json.loads((EVIDENCE_DIR / "media_rights_manifest.json").read_text(encoding="utf-8"))
    hash_errors: list[dict[str, str]] = []
    for asset in rights_manifest["assets"]:
        path = ROOT / asset["local_path"]
        actual = sha256(path)
        if actual != asset["sha256"]:
            hash_errors.append({"path": asset["local_path"], "expected": asset["sha256"], "actual": actual})
    checks.append({"check": "media_hash_binding", "status": "PASS" if not hash_errors else "FAIL", "errors": hash_errors})

    required_claim_strings = [
        "$763.6 billion",
        "0.6% from June",
        "5.0% above July 2025",
        "$324.757 billion",
        "$49.778 billion more",
        "18.1%",
        "3.4% over 12 months",
        "2.5% over the year",
        "14.7% above a year earlier",
        "1.5% annualized rate",
        "3.50%–3.75%",
        "9–3 vote",
    ]
    missing_claims = [claim for claim in required_claim_strings if claim not in markdown]
    checks.append({"check": "required_numeric_claims_present", "status": "PASS" if not missing_claims else "FAIL", "missing": missing_claims})

    forbidden_volume_claims = re.findall(r"gasoline volume (?:fell|declined|dropped|rose|increased)", markdown, flags=re.IGNORECASE)
    attribution_pass = "CAPITAL CHRONICLE ANALYSIS" in markdown or "OUR VIEW" in markdown
    checks.append({"check": "gasoline_receipts_volume_guardrail", "status": "PASS" if not forbidden_volume_claims else "FAIL", "matches": forbidden_volume_claims})
    checks.append({"check": "analysis_attribution_label", "status": "PASS" if attribution_pass else "FAIL"})

    public_write = json.loads((EVIDENCE_DIR / "public_write_audit.json").read_text(encoding="utf-8"))
    checks.append({"check": "zero_public_writes", "status": "PASS" if public_write["public_writes"] == 0 else "FAIL", "value": public_write["public_writes"]})

    pdf_size = (ROOT / "render" / "full_page_desktop.pdf").stat().st_size
    png_size = (ROOT / "render" / "full_page_desktop_1440.png").stat().st_size
    checks.append({"check": "render_artifacts_nonempty", "status": "PASS" if min(pdf_size, png_size) > 100000 else "FAIL", "png_bytes": png_size, "pdf_bytes": pdf_size})

    failures = [check for check in checks if check["status"] != "PASS"]
    output = {
        "schema": "capital_chronicle.blind_publication_candidate.validation_run.v1",
        "overall_status": "PASS" if not failures else "FAIL",
        "canonical_article_word_count": word_count,
        "checks": checks,
        "failure_count": len(failures),
    }
    print(json.dumps(output, indent=2))
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
