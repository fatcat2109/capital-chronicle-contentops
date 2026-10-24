"""Read-only audit of the existing owner's offline review export and retained proof."""
import hashlib
import json
import subprocess
import tomllib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
RELEASE = ROOT.parent
ACCEPTED = RELEASE / "editorial-media/final-prelive"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


class PacketParser(HTMLParser):
    capture = False
    payload = ""

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.capture = dict(attrs).get("id") == "owner-review-data"

    def handle_endtag(self, tag):
        if tag == "script":
            self.capture = False

    def handle_data(self, text):
        if self.capture:
            self.payload += text


def main():
    html = RELEASE / "START_HERE.html"
    parser = PacketParser()
    parser.feed(html.read_text(encoding="utf-8"))
    packet = json.loads(parser.payload)
    data = packet["data"]
    assert set(data) == {"owner_edition", "native_edition"}
    assert len(data["native_edition"]) == 7
    assert data["owner_edition"]["held"] == 1 and data["owner_edition"]["missing"] == 0
    expected = read(ACCEPTED / "renders/inspected-content-sha256.json")
    original_links = packet["context"]["original_media_links"]
    for item in data["native_edition"]:
        content = {k: item[k] for k in ("article", "previews", "media_assets")}
        digest = hashlib.sha256(json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        assert digest == expected[item["run_id"]], item["run_id"]
        assert len(item["previews"]) == 8 and len(item["media_assets"]) == 2
        assert item["review"]["decision"] == "KEEP" and item["publication"]["state"] == "PREPARED"
        assert item["publication"]["publication_authority"] is False
        assert all(d["status"] == "NOT_DISPATCHED" for d in item["publication"]["destinations"])
    assert len(original_links) == 14
    for digest, url in original_links.items():
        assert sha(RELEASE / unquote(url)) == digest
    observations = {}
    for name, width in (("navigation-desktop.json", 1440), ("navigation-phone.json", 390)):
        rows = read(ROOT / name)
        assert len(rows) == 63 and len({r["run"] for r in rows}) == 7
        assert all(r["width"] == width and r["pageWidth"] <= width for r in rows)
        assert all(not r["unresolvedMarker"] and not r["pendingCanonicalURL"] for r in rows)
        assert all(all(i["loaded"] for i in r["images"]) for r in rows)
        observations[name] = {"view_count": len(rows), "width": width, "sha256": sha(ROOT / name)}
    checks = {}
    for name, count in (("ui-checks.xml", 17), ("desk-checks.xml", 3)):
        tree = ET.parse(ROOT / name)
        assert len(tree.findall(".//testcase")) == count
        assert not tree.findall(".//failure") and not tree.findall(".//error")
        checks[name] = {"passed_cases": count, "sha256": sha(ROOT / name)}
    assert "built in" in (ROOT / "ui-build.log").read_text(encoding="utf-8")
    assert (ROOT / "python-lint.log").read_text(encoding="utf-8").strip() == "All checks passed!"
    accepted_checks = read(ACCEPTED / "verification-source-hashes.json")
    unchanged_backend = {f: h for f, h in accepted_checks["files"].items() if f.endswith(".py")}
    for file, digest in unchanged_backend.items():
        assert sha(REPO / file) == digest
    # The prior81 cases cover these unchanged backend bytes; reader13 now rerun within17.
    host = read(ACCEPTED / "host-boundary-final-readback.json")
    for item in host["four_automations"]:
        path = Path("C:/Users/bullw/.codex/automations") / item["id"] / "automation.toml"
        assert sha(path) == item["file_sha256"]
        assert tomllib.loads(path.read_text(encoding="utf-8"))["status"] == "PAUSED"
    assert sha(Path(host["pause_path"])) == host["pause_sha256"]
    old_scopes = ["docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal35"] + [
        str(RELEASE.relative_to(REPO) / "editorial-media" / story) for story in ("oil", "ibm", "tesla", "meta", "southwest")]
    old_scopes += [str(ACCEPTED.relative_to(REPO))]
    assert not subprocess.check_output(["git", "diff", "92c78afb869a65ea813076183bce3bc50b4ab97b", "--", *old_scopes], cwd=REPO)
    files = ["scripts/run_native_desktop_editorial.py", "tests/test_native_desktop_workspace_v1.py",
             "ui/contentops_v5/scripts/render-report-workspace.mjs", "ui/contentops_v5/src/views/ReportEditorialWorkspace.tsx",
             "ui/contentops_v5/src/dailyAppTypes.ts", "ui/contentops_v5/src/test/report_editorial_workspace.test.tsx"]
    receipt = {"goal": "CONTENTOPS_V1_OWNER_REVIEW_READY_V1", "created_at": 1792826320,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(), "entry": "START_HERE.html",
        "html_sha256": sha(html), "html_bytes": html.stat().st_size,
        "approved_content_sha256": expected, "approved_content_unchanged": True,
        "originals_hash_verified": original_links, "navigation": observations, "checks": checks,
        "tested_source_sha256": {f: sha(REPO / f) for f in files}, "accepted_backend_cases_reused": 81,
        "accepted_backend_source_unchanged": unchanged_backend, "ui_build": "PASS", "changed_python_ruff": "PASS",
        "prior_artifacts_unchanged": True, "four_host_files_and_pause_unchanged": True,
        "read_only_offline": True, "requires_server": False, "public_write_performed": False,
        "merged": False, "deployed": False, "v2_v3": "OWNER_PAUSED", "release_authority": "NOT_GRANTED",
        "scope": "Changed presentation/export only; no repeated editorial/rights/source/model acceptance"}
    (ROOT / "verification.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"articles": 7, "packages": 56, "originals": 14, "unchanged_content": True,
                      "ui_cases": 17, "workspace_cases": 3, "backend_reused": 81, "host_unchanged": True}))


if __name__ == "__main__":
    main()
