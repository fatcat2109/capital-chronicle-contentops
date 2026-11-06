"""Bind actual Neo BLS captures to the existing retained-source adapter."""
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
import json
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO))
from live_contentops.browser_rendered_source_recovery_v1 import _extract_rendered_page, _canonical_rendered_text
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch

ROOT = HERE / "source"
now = datetime.now(timezone.utc).isoformat()
original_index = ROOT / "main-index-before-supports.json"
raw_index = original_index.read_bytes() if original_index.exists() else (ROOT / "index.json").read_bytes()
index = json.loads(raw_index)
assert len(index["records"]) == 1
if not original_index.exists():
    original_index.write_bytes(raw_index)
index["records"][0] = {**json.loads((HERE / "source-claim-trace.json").read_bytes())["source_spec"],
    "authorship_class": "CAPITAL_CHRONICLE_MAIN_REPORT_PROJECTION"}

def capture(envelope_path, name, url):
    envelope = Path(envelope_path).read_text(encoding="utf-8")
    origin, markdown, truncated = _extract_rendered_page(envelope)
    assert origin == url and not truncated
    text = _canonical_rendered_text(markdown)
    result = {"status": "PASS", "final_url": url, "requested_url": url,
        "retrieval_method": "READ_ONLY_BROWSEROS_NEO_RENDERED_PAGE", "content_truncated": False,
        "rendered_markdown": markdown, "rendered_page_sha256": sha256(markdown.encode()).hexdigest(),
        "canonical_content_text": text, "canonical_content_sha256": sha256(text.encode()).hexdigest(),
        "observed_at_utc": now, "credential_or_session_material_read": False,
        "public_write_performed": False, "capture_source": "Actual saved BrowserOS Neo page.read result"}
    path = ROOT / (name + "-capture.json")
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result, path

policy, policy_path = capture(ROOT / "bls-policy-read.txt", "bls-policy", "https://www.bls.gov/bls/linksite.htm")
captures = [
    (r"\\?\C:\Users\bullw\AppData\Local\BrowserClaw\Application\155.0.8317.26\.browseros\tool-output\read-1793973257482-28e0ae41-39f4-4438-b78c-a08dfba42090.md", "bls-october-release", "https://www.bls.gov/news.release/empsit.nr0.htm", "Employment Situation Summary", "Total nonfarm payroll employment rose by 165,000 in October"),
    (r"\\?\C:\Users\bullw\AppData\Local\BrowserClaw\Application\155.0.8317.26\.browseros\tool-output\read-1793973140352-2201778c-01d9-406a-884f-a28c969ba1e8.md", "bls-october-sectors", "https://www.bls.gov/news.release/empsit.t17.htm", "October 2026 establishment employment by industry", "| Total nonfarm |"),
]
for envelope_path, name, url, title, marker in captures:
    cap, path = capture(envelope_path, name, url)
    text = cap["canonical_content_text"]
    start = text.index(marker)
    if name.endswith("release"):
        end = text.index("today.", start) + len("today.")
    else:
        end = text.index("| Total private", start)
    proposition = text[start:end].strip()
    constraints = {"attribution_required": True, "scope": "AGENCY_AUTHORED_TEXT_ONLY_EXCLUDES_LOGOS_PHOTOS_THIRD_PARTY",
        "policy_capture_sha256": sha256(policy_path.read_bytes()).hexdigest(),
        "source_capture_sha256": cap["rendered_page_sha256"]}
    doc = {"document_id": name, "title": title, "publisher": "U.S. Bureau of Labor Statistics",
        "source_url": url, "url": url, "published_at_utc": "2026-11-06T13:30:00Z", "known_at_utc": now,
        "raw_sha256": cap["rendered_page_sha256"], "canonical_content_text": text,
        "canonical_content_sha256": cap["canonical_content_sha256"], "content_truncated": False,
        "source_adapter_family": "official_macro", "source_authority_class": "official_public_primary_source",
        "source_reuse_constraints": constraints, "public_claim_allowed": True}
    loader = {"status": "PASS", "official_source_documents": [doc],
        "provenance": {"retrieved_at_utc": now, "retrieval_method": cap["retrieval_method"]}}
    loader_path = ROOT / (name + "-loader.json")
    loader_path.write_text(json.dumps(loader, indent=2) + "\n", encoding="utf-8", newline="\n")
    spec = {"headline_id": name, "headline_text": proposition, "capture_path": path.name,
        "capture_class": cap["retrieval_method"], "policy_capture_class": policy["retrieval_method"],
        "policy_capture_path": policy_path.name, "policy_url": policy["final_url"],
        "policy_capture_sha256": sha256(policy_path.read_bytes()).hexdigest(),
        "policy_retrieved_at_utc": now, "source_capture_sha256": cap["rendered_page_sha256"],
        "loader_result_path": loader_path.name, "proposition_span": [start, start + len(proposition)],
        "revision_at_utc": now, "candidate_catalyst_tags": ["payrolls", "employment", "official-support"],
        "supporting_headline_ids": ["cc124-nfp-arrival-review-20261106"],
        "research_metadata": {"role": "OFFICIAL_SUPPORT_FOR_HELD_MAIN_REPORT", "observation_date": "2026-10",
            "vintage": "OCTOBER_RELEASE_AS_READ_20261106", "independent_market_reaction": False}}
    index["records"].append(spec)
(ROOT / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8", newline="\n")
research = RetainedSourceResearch(ROOT)
assert not research.gaps, research.gaps
assert len(research.records) == 3
(HERE / "source-validation.json").write_text(json.dumps({"observed_at_utc": now,
    "verifier": "RetainedSourceResearch", "records": list(research.records), "gaps": research.gaps,
    "source_index_sha256": research.revision, "public_write_performed": False}, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"source_records": list(research.records), "gaps": research.gaps, "index_sha256": research.revision}))
