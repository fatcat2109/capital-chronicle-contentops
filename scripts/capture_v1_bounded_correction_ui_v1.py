"""Capture readable normal-viewport V1 bounded-correction UI evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def capture(*, url: str, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        page.goto(url, wait_until="networkidle")
        page.evaluate("document.body.style.zoom = '100%'")
        page.get_by_role("button", name="Performance", exact=True).click()
        page.get_by_text("Performance", exact=True).first.wait_for()

        targets = [
            ("performance-01-top.png", lambda: page.evaluate("window.scrollTo(0, 0)")),
            ("performance-02-middle.png", lambda: page.get_by_text("Daily observations", exact=True).scroll_into_view_if_needed()),
            ("performance-03-late.png", lambda: (
                page.get_by_text("Long-tail observations", exact=True).scroll_into_view_if_needed(),
                page.evaluate("window.scrollBy(0, -520)"),
            )),
            ("performance-04-bottom.png", lambda: page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")),
        ]
        for filename, position in targets:
            position()
            page.wait_for_timeout(250)
            path = output_dir / filename
            page.screenshot(path=str(path), full_page=False)
            records.append({
                "path": str(path.resolve()), "viewport": [1440, 1000],
                "scroll_y": int(page.evaluate("window.scrollY")), "browser_zoom": "100%",
            })

        for view, filename in (("Platforms", "platforms-01.png"), ("Learning", "learning-01.png")):
            page.get_by_role("button", name=view, exact=True).click()
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(250)
            path = output_dir / filename
            page.screenshot(path=str(path), full_page=False)
            records.append({
                "path": str(path.resolve()), "viewport": [1440, 1000],
                "scroll_y": 0, "browser_zoom": "100%",
            })
        browser.close()
    result = {
        "schema_version": "contentops.v1_bounded_correction_ui_evidence.v1",
        "url": url, "captures": records, "stitched_full_page_captures": 0,
        "public_writes": 0,
    }
    (output_dir / "ui_capture_evidence_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:5173")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(capture(url=args.url, output_dir=args.output_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
