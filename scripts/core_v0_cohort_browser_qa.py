"""Fresh browser QA for the CORE V0 cohort closure V5 surface.

Serves the production build locally on the loopback interface only, drives a real
browser at desktop and mobile dimensions, and writes screenshot files for
independent visual audit. No outbound network request is made.
"""
from __future__ import annotations

import functools
import http.server
import json
import socketserver
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

DIST = Path(__file__).resolve().parents[1] / "ui" / "contentops_v5" / "dist"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("browser_qa")
VIEWPORTS = {"desktop": (1440, 900), "mobile": (390, 844)}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
        port = httpd.server_address[1]
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        report: dict[str, object] = {"port": port, "viewports": {}}

        with sync_playwright() as p:
            browser = p.chromium.launch()
            for name, (width, height) in VIEWPORTS.items():
                page = browser.new_page(viewport={"width": width, "height": height})
                errors: list[str] = []
                page.on("pageerror", lambda exc: errors.append(str(exc)))
                page.on(
                    "console",
                    lambda msg: errors.append(msg.text) if msg.type == "error" else None,
                )
                page.goto(f"http://127.0.0.1:{port}/", wait_until="networkidle")
                if name == "mobile":
                    page.click("button[title='Open menu']")
                page.click("#nav-core_v0_cohort_closure")
                page.wait_for_selector("text=Diversified Cohort Shadow Run")
                if name == "mobile":
                    # Selecting a nav item leaves the drawer open on mobile; close it so
                    # the screenshot shows the view the operator actually reads.
                    page.click("button[title='Close menu']", force=True)
                    page.wait_for_timeout(400)
                path = OUT / f"core_v0_cohort_closure_{name}_{width}x{height}.png"
                page.screenshot(path=str(path), full_page=True)
                report["viewports"][name] = {
                    "width": width,
                    "height": height,
                    "screenshot": str(path),
                    "console_errors": errors,
                    "heading_visible": page.is_visible("text=Diversified Cohort Shadow Run"),
                    "shadow_only_visible": page.is_visible("text=LIVE ACTIONS LOCKED"),
                }
                page.close()
            browser.close()
        httpd.shutdown()

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
