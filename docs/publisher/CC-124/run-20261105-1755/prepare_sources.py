"""Admit exact Neo Treasury CSVs and BLS calendar; no network or publication."""
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import csv
import json
import re
import sys

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from live_contentops.browser_rendered_source_recovery_v1 import _extract_rendered_page, _canonical_rendered_text
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch

OP = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-gold-yields-20261105-e")
RUN = Path(__file__).resolve().parent
CAPTURES = OP / "source-captures"
ROOT = OP / "source-editions-treasury"
ROOT.mkdir(exist_ok=True)


def write(name, value):
    path = ROOT / name
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return sha256(path.read_bytes()).hexdigest()


def rendered(text, url):
    return {"status": "PASS", "final_url": url, "retrieval_method": "READ_ONLY_BROWSEROS_NEO_RENDERED_PAGE",
        "content_truncated": False, "rendered_markdown": text, "rendered_page_sha256": sha256(text.encode()).hexdigest(),
        "canonical_content_text": _canonical_rendered_text(text),
        "canonical_content_sha256": sha256(_canonical_rendered_text(text).encode()).hexdigest(),
        "credential_or_session_material_read": False, "public_write_performed": False}


records = []
reads = {r["page"]: r for r in json.loads((CAPTURES / "corrected-reads.json").read_bytes())}
facts_policy = REPO / "docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal35/source_editions/facts-policy.json"
(ROOT / "facts-policy.json").write_bytes(facts_policy.read_bytes())
now = datetime.now(timezone.utc).isoformat()
summary = {"calculation_owner": "Python Decimal from exact downloaded Treasury CSVs", "series": {}}
for kind, column, page in [("nominal", "10 Yr", 538), ("real", "10 YR", 539)]:
    binary = (CAPTURES / ("treasury-" + kind + "-2026.csv")).read_bytes()
    file_name = kind + ".csv"
    (ROOT / file_name).write_bytes(binary)
    rows = list(csv.DictReader(binary.decode("utf-8-sig").splitlines()))
    ordered = sorted(rows, key=lambda r: datetime.strptime(r["Date"], "%m/%d/%Y"))
    assert len(rows) == len({r["Date"] for r in rows}) == 212
    assert ordered[-1]["Date"] == "11/04/2026"
    assert all(r[column] not in ("", "N/A") for r in ordered)
    series_name = "Daily Treasury Par " + ("Real " if kind == "real" else "") + "Yield Curve Rates"
    title = "U.S. Treasury " + kind + " 10-year par yields, 2 January through 4 November 2026; percent."
    text = title + "\n" + "\n".join(datetime.strptime(r["Date"], "%m/%d/%Y").date().isoformat() + " " + r[column] for r in ordered)
    url = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_" + ("real_" if kind == "real" else "") + "yield_curve&field_tdr_date_value=2026"
    known = now  # download clock unavailable; verified exact local file after acquisition
    original_hash = write(kind + "-original.json", {"url": url, "text": text, "observed": known,
        "binary_download_source": "Treasury page's observed Download CSV link through Neo",
        "observation_clock_basis": "LOCAL_VERIFICATION_AFTER_NEO_DOWNLOAD_EXACT_DOWNLOAD_CLOCK_UNAVAILABLE",
        "binary_capture": {"path": file_name, "sha256": sha256(binary).hexdigest(),
                           "extracted_text_sha256": sha256(text.encode()).hexdigest()}})
    capture_hash = write(kind + "-facts.json", {"status": "PASS", "url": url, "canonical_content_text": text,
        "observed_at_utc": known, "source_capture_sha256": original_hash,
        "public_write_performed": False, "credential_or_session_material_read": False,
        "excerpts": [{"start": 0, "end": len(text), "text": text}]})
    item_id = "cc124-treasury-" + kind + "-20261104"
    doc = {"document_id": item_id, "title": series_name, "source_url": url,
        "publisher": "U.S. Department of the Treasury", "source_identity": "home.treasury.gov",
        "source_interest_role": "ORIGINAL_DATA_PRODUCER", "raw_sha256": capture_hash,
        "canonical_content_text": text, "canonical_content_sha256": sha256(text.encode()).hexdigest(),
        "source_adapter_family": "official_macro", "source_authority_class": "official_public_primary_source",
        "published_at_utc": "2026-11-04T23:59:59Z", "published_at_source": "November 4, 2026",
        "publication_clock_basis": "UPPER_BOUND_OF_LAST_OBSERVATION_DATE_NOT_ACTUAL_PUBLICATION_TIME",
        "reference_period": "2026-01-02/2026-11-04", "content_truncated": False}
    write(kind + "-admission.json", {"status": "PASS", "official_source_documents": [doc], "provenance": {"retrieved_at_utc": known}})
    records.append({"authorship_class": "ORIGINAL_PUBLIC_FACTS_ONLY", "headline_id": item_id,
        "headline_text": title, "capture_path": kind + "-facts.json", "source_capture_sha256": capture_hash,
        "original_capture_path": kind + "-original.json", "original_capture_sha256": original_hash,
        "loader_result_path": kind + "-admission.json", "policy_url": "https://www.copyright.gov/help/faq/faq-protect.html",
        "policy_capture_path": "facts-policy.json", "policy_capture_sha256": sha256(facts_policy.read_bytes()).hexdigest(),
        "policy_retrieved_at_utc": "2026-10-21T21:02:03.468Z", "revision_at_utc": now,
        "proposition_span": [0, len(title)], "public_expression_reuse_allowed": False,
        "research_metadata": {"observation_date": "2026-11-04", "unit": "percent", "frequency": "daily",
            "actual_estimate_forecast": "OFFICIAL_PAR_YIELD_ESTIMATE", "first_print_claim": False,
            "source_binary_sha256": sha256(binary).hexdigest(), "missing_values": 0}})
    summary["series"][kind] = {"last_date": ordered[-1]["Date"], "last": ordered[-1][column],
        "previous_date": ordered[-2]["Date"], "previous": ordered[-2][column],
        "daily_change_basis_points": str((Decimal(ordered[-1][column]) - Decimal(ordered[-2][column])) * 100),
        "observations": len(ordered), "source_sha256": sha256(binary).hexdigest(), "source_url": url}

# Exact BLS authored calendar text, with its retained agency copyright policy.
read = reads[540]
url, text, truncated = _extract_rendered_page(read["read"])
assert not truncated and "Employment Situation" in text and "October 2026" in text
canonical = _canonical_rendered_text(text)
key = "cc124-bls-november-calendar"
page = rendered(text, url)
write("bls-calendar.json", page)
base = REPO / "docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal20/retained_research"
policy = next(s for s in json.loads((base / "index.json").read_bytes())["records"] if s["policy_url"] == "https://www.bls.gov/bls/linksite.htm")
(ROOT / "bls-policy.json").write_bytes((base / policy["policy_capture_path"]).read_bytes())
begin = canonical.index("6 Employment Situation October 2026")
end = canonical.index("08:30 AM", begin) + len("08:30 AM")
clock = canonical.index("NOTE: All times on calendar are Eastern Time.")
doc = {"document_id": key, "title": "BLS November 2026 release calendar", "source_url": url,
    "publisher": "U.S. Bureau of Labor Statistics", "raw_sha256": page["rendered_page_sha256"],
    "canonical_content_text": canonical, "canonical_content_sha256": page["canonical_content_sha256"],
    "source_adapter_family": "official_macro", "source_authority_class": "official_public_primary_source",
    "published_at_utc": "2026-11-03T23:59:59Z", "published_at_source": "Last Modified Date: November 03, 2026",
    "publication_clock_basis": "UPPER_BOUND_OF_STATED_LAST_MODIFIED_DATE_NOT_EXACT_TIME", "content_truncated": False}
write("bls-admission.json", {"status": "PASS", "official_source_documents": [doc], "provenance": {"retrieved_at_utc": read["observed_at_utc"]}})
records.append({"headline_id": key, "headline_text": canonical[begin:end], "capture_path": "bls-calendar.json",
    "capture_class": "READ_ONLY_BROWSEROS_NEO_RENDERED_PAGE", "source_capture_sha256": page["rendered_page_sha256"],
    "loader_result_path": "bls-admission.json", "policy_url": policy["policy_url"], "policy_capture_path": "bls-policy.json",
    "policy_capture_sha256": policy["policy_capture_sha256"], "policy_retrieved_at_utc": policy["policy_retrieved_at_utc"],
    "revision_at_utc": now, "proposition_span": [begin, end],
    "context_spans": [[clock, clock + len("NOTE: All times on calendar are Eastern Time.")],
                      [canonical.index("November 2026"), canonical.index("November 2026") + len("November 2026")]],
    "candidate_catalyst_tags": ["employment", "gold", "rates"]})
write("index.json", {"schema_version": "contentops.retained_source_research.v1", "records": records})
research = RetainedSourceResearch(ROOT)
assert not research.gaps, research.gaps
assert len(research.records) == 3
summary["ten_year_par_yield_difference"] = {"label": "Nominal minus real par yield; not a pure inflation forecast",
    "latest_percentage_points": str(Decimal(summary["series"]["nominal"]["last"]) - Decimal(summary["series"]["real"]["last"])),
    "previous_percentage_points": str(Decimal(summary["series"]["nominal"]["previous"]) - Decimal(summary["series"]["real"]["previous"]))}
(RUN / "official-data-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

pending = json.loads((OP / "source_preparation_required.json").read_bytes())
requests = []
# Preserve the three original issued URLs, including the two actual 404s.
initial = {r["page"]: r for r in json.loads((CAPTURES / "initial-reads.json").read_bytes())}
for n, issued in enumerate(pending["source_requests"]):
    if n < 2:
        path = CAPTURES / ("issued-treasury-" + str(n) + "-404.txt")
        path.write_text(initial[538 + n]["read"], encoding="utf-8")
    else:
        path = ROOT / "bls-calendar-visible.txt"
        path.write_text(text, encoding="utf-8")
    requests.append({**issued, "non_chargeable": True, "observed_at_utc": now,
        "capture_path": str(path), "capture_sha256": sha256(path.read_bytes()).hexdigest(),
        **({"status": "SOURCE_MISSING", "error": "Page Not Found at issued Treasury path; corrected link observed on same Treasury site."} if n < 2 else {})})
for kind in ["nominal", "real"]:
    spec = next(r for r in records if r["headline_id"] == "cc124-treasury-" + kind + "-20261104")
    doc = json.loads((ROOT / (kind + "-admission.json")).read_bytes())["official_source_documents"][0]
    for url, path, reason in [(doc["source_url"], ROOT / spec["capture_path"], "Corrected official path; exact 10-year series from its downloaded CSV."),
        ("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/2026/all?type=daily_treasury_" + ("real_" if kind == "real" else "") + "yield_curve&field_tdr_date_value=2026&page&_format=csv", ROOT / (kind + ".csv"), "Exact CSV link downloaded by Neo; retain original bytes.")]:
        requests.append({"url": url, "reason": reason, "non_chargeable": True, "observed_at_utc": now,
            "capture_path": str(path), "capture_sha256": sha256(path.read_bytes()).hexdigest()})
# The BLS record uses the exact visible rendered bytes, rather than JSON container bytes.
requests[2]["capture_sha256"] = page["rendered_page_sha256"]
for name, url in [("site-policies", "https://home.treasury.gov/subfooter/site-policies-and-notices"),
                  ("privacy-policy", "https://home.treasury.gov/subfooter/privacy-policy")]:
    path = CAPTURES / (name + "-observation.json")
    path.write_text(json.dumps({"url": url, "observed_by": "BrowserOS Neo", "observation": "Page read for source policy context; no factual series admitted from it.", "verified_at_utc": now}), encoding="utf-8")
    requests.append({"url": url, "reason": "Actual source policy context read; no additional factual claim.", "non_chargeable": True,
        "observed_at_utc": now, "capture_path": str(path), "capture_sha256": sha256(path.read_bytes()).hexdigest()})
response = {"within_bound_live_budget": True, "expected_selection_request_sha256": pending["expected_selection_request_sha256"],
    "expected_source_request_sha256": pending["request_sha256"], "expected_evidence_sha256": pending["expected_evidence_sha256"],
    "candidate_id": pending["candidate_id"], "research_root": str(ROOT), "supporting_headline_ids": list(research.records),
    "additional_source_requests": requests,
    "owner_instruction": "Use exact official Treasury nominal and real par yields, preserving observation dates and retrieval clocks. No gold price, current plan or observed gold response is established. BLS confirms October jobs on November 6 at 08:30 Eastern; no release result is known. Keep the existing cutoff, budget and accepted Light returns."}
(RUN / "source-recovery-input.json").write_text(json.dumps(response, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"admitted_records": len(research.records), "source_requests": len(requests), "summary": summary}))
