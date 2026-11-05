"""Admit already captured official FX/Treasury/calendar bytes; no network/store writes."""
from datetime import datetime
from decimal import Decimal, localcontext
from hashlib import sha256
from pathlib import Path
import csv
import json
import sys

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from live_contentops.browser_rendered_source_recovery_v1 import _extract_rendered_page, _canonical_rendered_text
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch

OP = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-jobs-fx-watch-20261105-f")
PRIOR = OP.parent / "cc124-gold-yields-20261105-e" / "source-editions-treasury"
ROOT = OP / "source-editions-fx"
RUN = Path(__file__).resolve().parent
KNOWN = "2026-11-05T13:44:00Z"


def digest(raw):
    return sha256(raw).hexdigest()


def write(name, value):
    raw = (json.dumps(value, indent=2, ensure_ascii=True) + "\n").encode()
    (ROOT / name).write_bytes(raw)
    return digest(raw)


def prepare():
    ROOT.mkdir(exist_ok=True)
    prior = json.loads((PRIOR / "index.json").read_bytes())
    records = [s for s in prior["records"] if s["headline_id"] in {
        "cc124-treasury-nominal-20261104", "cc124-bls-november-calendar"}]
    assert len(records) == 2
    # Exact copies preserve original identities, rights hashes, retrieval and admission clocks.
    names = {"nominal.csv", "bls-calendar-visible.txt"}
    for spec in records:
        names.update(spec[k] for k in ("capture_path", "original_capture_path", "loader_result_path", "policy_capture_path") if k in spec)
    for name in sorted(names):
        raw = (PRIOR / name).read_bytes()
        (ROOT / name).write_bytes(raw)
        assert (ROOT / name).read_bytes() == raw

    capture_path = OP / "source-captures" / "fed-h10-20261102-read.md"
    raw = capture_path.read_bytes()
    (ROOT / "fed-h10-original-read.md").write_bytes(raw)
    url, text, truncated = _extract_rendered_page(raw.decode("utf-8-sig"))
    assert url == "https://www.federalreserve.gov/releases/h10/current/" and not truncated
    assert "Release Date: November 2, 2026" in text
    canonical = _canonical_rendered_text(text)
    page = {"status": "PASS", "final_url": url,
        "retrieval_method": "READ_ONLY_BROWSEROS_NEO_RENDERED_PAGE", "content_truncated": False,
        "rendered_markdown": text, "rendered_page_sha256": digest(text.encode()),
        "canonical_content_text": canonical, "canonical_content_sha256": digest(canonical.encode()),
        "credential_or_session_material_read": False, "public_write_performed": False,
        "original_tool_read_path": "fed-h10-original-read.md", "original_tool_read_sha256": digest(raw),
        "observed_at_utc": KNOWN, "observation_clock_basis": "PARENT_OBSERVED_NEO_READ_MINUTE_PRECISION"}
    write("fed-h10-rendered.json", page)
    policy_root = REPO / "docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal21/retained_research"
    policy = next(s for s in json.loads((policy_root / "index.json").read_bytes())["records"]
        if s["policy_url"] == "https://www.federalreserve.gov/disclaimer.htm")
    policy_raw = (policy_root / policy["policy_capture_path"]).read_bytes()
    assert digest(policy_raw) == policy["policy_capture_sha256"]
    (ROOT / "fed-policy.json").write_bytes(policy_raw)
    key = "cc124-fed-h10-20261102-fx"
    start = canonical.index("Release Date: November 2, 2026")
    finish = start + len("Release Date: November 2, 2026")
    doc = {"document_id": key, "title": "Federal Reserve H.10 Weekly, November 2, 2026",
        "source_url": url, "publisher": "Board of Governors of the Federal Reserve System",
        "raw_sha256": page["rendered_page_sha256"], "canonical_content_text": canonical,
        "canonical_content_sha256": page["canonical_content_sha256"],
        "source_adapter_family": "official_policy", "source_authority_class": "official_public_primary_source",
        "published_at_utc": "2026-11-02T23:59:59Z", "published_at_source": "November 2, 2026",
        "publication_clock_basis": "UPPER_BOUND_OF_STATED_RELEASE_DATE_NOT_EXACT_TIME",
        "reference_period": "2026-10-26/2026-10-30", "content_truncated": False}
    write("fed-h10-admission.json", {"status": "PASS", "official_source_documents": [doc],
        "provenance": {"retrieved_at_utc": KNOWN, "retrieval_precision": "MINUTE"}})
    contexts = []
    for marker in ["(Rates in currency units per U.S. dollar except as noted by an asterisk)",
                   "* U.S. dollars per currency unit."]:
        at = canonical.index(marker)
        contexts.append([at, at + len(marker)])
    records.append({"headline_id": key, "headline_text": canonical[start:finish],
        "capture_path": "fed-h10-rendered.json", "capture_class": "READ_ONLY_BROWSEROS_NEO_RENDERED_PAGE",
        "source_capture_sha256": page["rendered_page_sha256"], "loader_result_path": "fed-h10-admission.json",
        "policy_url": policy["policy_url"], "policy_capture_path": "fed-policy.json",
        "policy_capture_class": "READ_ONLY_BROWSEROS_NEO_RENDERED_PAGE",
        "policy_capture_sha256": policy["policy_capture_sha256"],
        "policy_retrieved_at_utc": policy["policy_retrieved_at_utc"], "revision_at_utc": KNOWN,
        "proposition_span": [start, finish], "context_spans": contexts,
        "candidate_catalyst_tags": ["fx_rates", "EURUSD", "USDJPY", "employment"],
        "research_metadata": {"observation_date": "2026-10-30", "period_start": "2026-10-26",
            "unit": "EURUSD: USD per EUR; USDJPY: JPY per USD", "frequency": "daily",
            "actual_estimate_forecast": "OFFICIAL_REFERENCE_RATE", "first_print_claim": False,
            "retrieval_after_frozen_cutoff": True, "release_before_frozen_cutoff": True,
            "not_current_executable_spot": True, "missing_values": 0}})
    write("index.json", {"schema_version": "contentops.retained_source_research.v1", "records": records})
    research = RetainedSourceResearch(ROOT)
    assert not research.gaps, research.gaps
    assert len(research.records) == 3

    def row(label):
        lines = [line for line in text.splitlines() if line.startswith("| " + label + " |")]
        assert len(lines) == 1
        values = [v.strip() for v in lines[0].split("|")[3:-1]]
        assert len(values) == 5
        return [Decimal(v) for v in values]

    eur, yen = row("*EMU MEMBERS"), row("JAPAN")
    dates = ["2026-10-" + str(d) for d in range(26, 31)]
    nominal = {}
    for r in csv.DictReader((ROOT / "nominal.csv").read_text(encoding="utf-8-sig").splitlines()):
        dt = datetime.strptime(r["Date"], "%m/%d/%Y").date().isoformat()
        assert dt not in nominal
        nominal[dt] = Decimal(r["10 Yr"])
    assert all(d in nominal for d in dates)
    with localcontext() as ctx:
        ctx.prec = 40
        aligned = [{"date": d, "eurusd_usd_per_eur": str(eur[i]), "usdjpy_jpy_per_usd": str(yen[i]),
            "usdeur_eur_per_usd": str(Decimal(1) / eur[i]), "jpyusd_usd_per_jpy": str(Decimal(1) / yen[i]),
            "us10y_par_yield_percent": str(nominal[d])} for i, d in enumerate(dates)]
        def change(values):
            return {"first": str(values[0]), "last": str(values[-1]), "absolute_change": str(values[-1] - values[0]),
                "percent_change": str((values[-1] / values[0] - 1) * 100)}
        changes = {"eurusd": change(eur), "usdjpy": change(yen),
            "usdeur": change([1 / x for x in eur]), "jpyusd": change([1 / x for x in yen])}
    latest = sorted(nominal)[-1]
    assert latest == "2026-11-04"
    summary = {"calculation_owner": "Python Decimal; precision 40 for ratios; no floating-point arithmetic",
        "fed_release_date": "2026-11-02", "fx_observation_window": [dates[0], dates[-1]],
        "aligned_observations": aligned, "window_changes": changes,
        "matched_us10y_change_basis_points": str((nominal[dates[-1]] - nominal[dates[0]]) * 100),
        "later_treasury_observation": {"date": latest, "yield_percent": str(nominal[latest]),
            "matched_fx_observation": None},
        "jobs_calendar": {"release_date": "2026-11-06", "reference_month": "October 2026",
            "source_time": "08:30 AM Eastern Time", "date_correct_utc": "2026-11-06T13:30:00Z",
            "reader_gmt_plus_7": "2026-11-06T20:30:00+07:00", "result": None},
        "caveats": ["FX reference rates end October 30, not November 5 live spot.",
            "Daily series are date-aligned, not synchronized intraday observations; no causal or correlation estimate.",
            "Treasury latest November 4 is displayed separately; no FX observation is imputed for that date.",
            "No payroll forecast, consensus or jobs result is supplied.",
            "H.10 captured after frozen cutoff; release and all admitted observations precede it; retrieval is not backdated.",
            "Inverse rates are calculated reciprocals, not separately observed quotes."],
        "source_hashes": {n: digest((ROOT / n).read_bytes()) for n in sorted(names | {
            "fed-h10-original-read.md", "fed-h10-rendered.json", "fed-h10-admission.json", "fed-policy.json", "index.json"})},
        "verified_record_ids": list(research.records), "verification_gaps": research.gaps}
    (RUN / "fx-official-data-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source_root": str(ROOT), "verified_records": len(research.records),
        "gaps": research.gaps, "window_changes": changes,
        "matched_us10y_change_basis_points": summary["matched_us10y_change_basis_points"],
        "later_treasury_observation": summary["later_treasury_observation"],
        "summary_sha256": digest((RUN / "fx-official-data-summary.json").read_bytes())}))


if __name__ == "__main__":
    prepare()
