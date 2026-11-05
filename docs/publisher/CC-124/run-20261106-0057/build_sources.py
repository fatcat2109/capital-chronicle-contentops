"""Bind real Neo SEC text and unchanged held Treasury/calendar captures."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

OPERATING = Path(r"A:\Capital Chronicle\ContentOps")
sys.path.insert(0, str(OPERATING))
from live_contentops.browser_rendered_source_recovery_v1 import _canonical_rendered_text
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch

HERE = Path(__file__).resolve().parent
RUN = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-bitcoin-rates-20261106-h")
ROOT = RUN / "source-editions-bitcoin"
PRIOR = RUN.parent / "cc124-nfp-us500-preview-20261105-g/source-editions-jobs-treasury"
now = datetime.now(timezone.utc).isoformat()

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

prior = json.loads((PRIOR / "index.json").read_bytes())
records = [r for r in prior["records"] if r["headline_id"] in {
    "cc124-treasury-nominal-20261104", "cc124-bls-november-calendar"}]
shutil.copytree(PRIOR / "treasury", ROOT / "treasury", dirs_exist_ok=True)
shutil.copyfile(PRIOR / "nominal.csv", ROOT / "nominal.csv")

raw = (ROOT / "sec-bulletin-visible.txt").read_text(encoding="utf-8")
markdown = raw.split("\n", 1)[1].rsplit("\n[END_UNTRUSTED_PAGE_CONTENT", 1)[0].strip()
assert markdown.startswith("Sept. 9, 2024") and "no legal force or effect" in markdown
text = _canonical_rendered_text(markdown)
url = "https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/ETPBulletinSeptember2024"
observed = datetime.fromtimestamp(1793901825956 / 1000, timezone.utc).isoformat()
capture = {"status": "PASS", "final_url": url,
    "retrieval_method": "READ_ONLY_BROWSEROS_NEO_RENDERED_PAGE", "content_truncated": False,
    "rendered_markdown": markdown, "rendered_page_sha256": hashlib.sha256(markdown.encode()).hexdigest(),
    "canonical_content_text": text, "canonical_content_sha256": hashlib.sha256(text.encode()).hexdigest(),
    "credential_or_session_material_read": False, "public_write_performed": False,
    "observed_at_utc": observed, "original_browser_output_sha256": digest(ROOT / "sec-bulletin-visible.txt")}
save(ROOT / "sec-capture.json", capture)
profile = json.loads((OPERATING / "config/native_desktop_operator_profile_v1.json").read_bytes())
for root_name in profile["research_editions_root"]:
    root = Path(root_name)
    if not (root / "index.json").exists():
        continue
    spec = next((r for r in json.loads((root / "index.json").read_bytes())["records"]
                 if r["headline_id"] == "goal28-crypto-safeguards"), None)
    if spec:
        shutil.copyfile(root / spec["policy_capture_path"], ROOT / "sec-policy.json")
        break
else:
    raise RuntimeError("Held SEC agency-text policy not located")
document = {"document_id": "cc124-sec-bitcoin-etp-bulletin-20240909",
    "title": "Exchange-Traded Products Providing Exposure to Bitcoin and Ether - Investor Bulletin",
    "source_url": url, "publisher": "SEC Office of Investor Education and Advocacy",
    "source_identity": "www.investor.gov", "raw_sha256": capture["rendered_page_sha256"],
    "canonical_content_text": text, "canonical_content_sha256": capture["canonical_content_sha256"],
    "source_adapter_family": "sec_regulatory", "source_authority_class": "official_public_primary_source",
    "published_at_utc": "2024-09-09T23:59:59Z", "published_at_source": "Sept. 9, 2024",
    "publication_clock_basis": "UPPER_BOUND_OF_VISIBLE_PUBLICATION_DATE_NOT_ACTUAL_TIME",
    "content_truncated": False}
save(ROOT / "sec-admission.json", {"status": "PASS", "official_source_documents": [document],
    "provenance": {"retrieved_at_utc": observed, "browser_page_id": 589,
        "browser_tool": "BrowserOS Neo read article; full retained output", "source_is_dated_background": True}})
paragraph = markdown.split("\n\n")[1]
proposition = _canonical_rendered_text(paragraph)
start = text.index(proposition)
hold_start = text.index("Spot bitcoin and ether ETPs are exchange-traded commodity trusts")
hold_end = text.index("How are spot bitcoin and ether ETPs regulated?", hold_start)
records.append({"headline_id": document["document_id"], "headline_text": proposition,
    "capture_path": "sec-capture.json", "capture_class": "READ_ONLY_BROWSEROS_NEO_RENDERED_PAGE",
    "source_capture_sha256": capture["rendered_page_sha256"], "loader_result_path": "sec-admission.json",
    "policy_capture_path": "sec-policy.json", "policy_capture_class": "READ_ONLY_BROWSEROS_NEO_RENDERED_PAGE",
    "policy_url": spec["policy_url"], "policy_capture_sha256": digest(ROOT / "sec-policy.json"),
    "policy_retrieved_at_utc": spec["policy_retrieved_at_utc"], "revision_at_utc": now,
    "proposition_span": [start, start + len(proposition)], "context_spans": [[hold_start, hold_end]],
    "candidate_catalyst_tags": ["bitcoin", "us_rates", "employment"],
    "policy_application_basis": "Investor.gov is SEC OIEA and its footer links the SEC privacy policy; agency-authored text only."})
save(ROOT / "index.json", {"schema_version": prior["schema_version"], "records": records})
research = RetainedSourceResearch(ROOT)
assert not research.gaps, research.gaps
assert len(research.records) == 3
pending = json.loads((RUN / "source_preparation_required.json").read_bytes())
requests = []
for issued in pending["source_requests"]:
    record = next(r for r in research.records.values() if r["document"]["source_url"] == issued["url"])
    spec = next(r for r in records if r["headline_id"] == record["headline_id"])
    path = ROOT / spec["capture_path"]
    if digest(path) != record["source_capture_sha256"]:
        rendered = json.loads(path.read_bytes())["rendered_markdown"]
        path = ROOT / (record["headline_id"] + "-rendered.txt")
        path.write_bytes(rendered.encode())
        assert digest(path) == record["source_capture_sha256"]
    requests.append({**issued, "non_chargeable": True, "observed_at_utc": record["retrieval_time_utc"],
        "capture_path": str(path), "capture_sha256": digest(path),
        "clock_basis": "Exact retained original acquisition; no recapture or clock refresh"})
response = {"within_bound_live_budget": True,
    "expected_selection_request_sha256": pending["expected_selection_request_sha256"],
    "expected_source_request_sha256": pending["request_sha256"],
    "expected_evidence_sha256": pending["expected_evidence_sha256"], "candidate_id": pending["candidate_id"],
    "research_root": str(ROOT), "supporting_headline_ids": list(research.records),
    "additional_source_requests": requests,
    "owner_instruction": "Bitcoin rate-versus-risk watch, not new custody news. Use SEC 9 September 2024 background, official nominal Treasury history through 4 November 2026, and the 6 November jobs schedule. No current Bitcoin price, ETF flow, return correlation, payroll outcome, consensus or trade call is supplied. Mechanisms are conditional. Preserve all dates; reuse Treasury/calendar original clocks. Source-context proposition must describe this reader question, not the older custody announcement."}
save(HERE / "source-recovery-input.json", response)
save(HERE / "source-admission-acceptance.json", {"records": list(research.records), "gaps": research.gaps,
    "research_revision": research.revision, "sec_capture_path": str(ROOT / "sec-bulletin-visible.txt"),
    "sec_capture_sha256": digest(ROOT / "sec-bulletin-visible.txt"), "read_at_utc": observed,
    "rights": {key: r["rights_state"] for key, r in research.records.items()}})
print(json.dumps({"verified_records": list(research.records), "gaps": research.gaps}))
