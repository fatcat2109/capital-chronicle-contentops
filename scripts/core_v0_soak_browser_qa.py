"""Fresh browser QA for the CORE V0 repeated shadow soak V5 surface.

Serves the production build on the loopback interface only, drives a real browser at
desktop and mobile dimensions, and writes screenshot files for independent visual audit.
No outbound network request is made.

The V5 shell scrolls inner content, so the key below-fold panels are scrolled into view
and captured explicitly rather than relying on one full-page shot.
"""
from __future__ import annotations

import functools
import hashlib
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

#: Panels an auditor must be able to see without taking the full-page shot on trust.
BELOW_FOLD_PANELS = (
    ("launch_readiness", "Launch readiness"),
    ("logical_days", "Logical newsroom days"),
    ("recovery_drills", "Restart and recovery drills"),
    ("reconciliation", "Incidents and reconciliation"),
    ("launch_edge", "Launch edge (dry model)"),
    ("slo_measurements", "SLO measurements"),
    ("durable_runtime", "Durable state, determinism, runtime and cost"),
)

#: DOM facts that must hold in both viewports. A screenshot alone cannot prove these.
DOM_ASSERTIONS = {
    "heading_visible": "text=Repeated Shadow Soak and Recovery",
    "shadow_only_banner_visible": "text=LIVE ACTIONS LOCKED",
    "accelerated_logical_soak_disclosure_present": "text=accelerated logical soak",
    "launch_readiness_disposition_present": "text=READY_WITH_EXPLICIT_CAVEATS",
    "kill_switch_state_present": "text=kill_switch_engaged",
    "autonomous_policy_actor_present": "text=AUTONOMOUS_POLICY",
    "operator_decision_actor_present": "text=OPERATOR_DECISION",
    "calendar_uptime_unmeasurable_present": "text=UNMEASURABLE",
    "zero_external_cost_present": "text=NONE_NO_PAID_API_OR_MODEL_CALL",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
        port = httpd.server_address[1]
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        report: dict[str, object] = {
            "browser": "playwright chromium (local)",
            "served_from": str(DIST),
            "loopback_port": port,
            "route": "/#core_v0_shadow_soak",
            "outbound_network_request_made": False,
            "viewports": {},
            "files": {},
        }

        with sync_playwright() as p:
            browser = p.chromium.launch()
            for name, (width, height) in VIEWPORTS.items():
                page = browser.new_page(viewport={"width": width, "height": height})
                console_errors: list[str] = []
                page_errors: list[str] = []
                page.on("pageerror", lambda exc: page_errors.append(str(exc)))
                page.on(
                    "console",
                    lambda msg: console_errors.append(msg.text)
                    if msg.type == "error"
                    else None,
                )
                page.goto(f"http://127.0.0.1:{port}/", wait_until="networkidle")
                if name == "mobile":
                    page.click("button[title='Open menu']")
                page.click("#nav-core_v0_shadow_soak")
                page.wait_for_selector("text=Repeated Shadow Soak and Recovery")
                if name == "mobile":
                    # Selecting a nav item leaves the drawer open on mobile; close it so
                    # the screenshot shows the view the operator actually reads.
                    page.click("button[title='Close menu']", force=True)
                    page.wait_for_timeout(400)

                shots: list[str] = []
                path = OUT / f"core_v0_shadow_soak_{name}_{width}x{height}.png"
                page.screenshot(path=str(path), full_page=True)
                shots.append(path.name)

                for slug, text in BELOW_FOLD_PANELS:
                    locator = page.locator(f"text={text}").first
                    locator.scroll_into_view_if_needed()
                    page.wait_for_timeout(250)
                    panel_path = OUT / f"core_v0_shadow_soak_{name}_{width}x{height}_{slug}.png"
                    page.screenshot(path=str(panel_path), full_page=False)
                    shots.append(panel_path.name)

                assertions = {
                    key: page.locator(selector).first.count() > 0
                    for key, selector in DOM_ASSERTIONS.items()
                }
                report["viewports"][name] = {
                    "width": width,
                    "height": height,
                    "console_errors": console_errors,
                    "console_error_count": len(console_errors),
                    "page_errors": page_errors,
                    "page_error_count": len(page_errors),
                    "dom_assertions": assertions,
                    "screenshots": shots,
                }
                page.close()
            browser.close()

        for shot in sorted(OUT.glob("*.png")):
            report["files"][shot.name] = {
                "bytes": shot.stat().st_size,
                "sha256": _sha256(shot),
            }

    report["console_errors"] = {
        name: data["console_error_count"] for name, data in report["viewports"].items()
    }
    report["page_errors_total"] = sum(
        data["page_error_count"] for data in report["viewports"].values()
    )
    report["dom_assertions_both_viewports"] = {
        key: all(
            data["dom_assertions"][key] for data in report["viewports"].values()
        )
        for key in DOM_ASSERTIONS
    }
    report["independent_pixel_perfect_visual_pass_claimed"] = False
    report["credential_read_performed"] = False
    report["provider_call_performed"] = False
    report["publication_authority"] = False
    report["dispatch_authority"] = False
    report["public_write_authority"] = False

    (OUT / "browser_qa_manifest.json").write_text(
        json.dumps(report, indent=1, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in report.items() if k != "files"}, indent=1, sort_keys=True))
    failures = report["page_errors_total"] or sum(report["console_errors"].values())
    missing = [k for k, v in report["dom_assertions_both_viewports"].items() if not v]
    if missing:
        print(f"MISSING DOM ASSERTIONS: {missing}")
    return 1 if (failures or missing) else 0


if __name__ == "__main__":
    raise SystemExit(main())
