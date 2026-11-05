"""One CC-216 preparation, using held records and the existing story outbox."""
from datetime import datetime, timezone
from hashlib import sha256
import gzip
import json
from pathlib import Path

from bs4 import BeautifulSoup

from live_contentops.contentops_editorial_desk_v1 import record_pre_event_preparation
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.official_release_history_v1 import load_cc010_history, FAMILIES

ROOT = Path(__file__).resolve().parent
STORE = Path("A:/Capital Chronicle/Runtime/ContentOps/contentops_daily_app_v1.sqlite3")
CONSENSUS = Path("A:/Capital Chronicle/ResearchRuns/cc-068-release-consensus/root")


def main():
    result_path = ROOT / "prepared-inputs.json"
    if result_path.is_file():
        print(json.dumps({"result_path": str(result_path), "state": "USE_EXISTING_PREPARATION"}))
        return
    now = datetime.now(timezone.utc).isoformat()
    store = ContentOpsDurableStore(STORE, auto_migrate=False)
    latest = {}
    with store.get_read_only_connection() as conn:
        rows = conn.execute("SELECT message_id,payload FROM outbox_messages WHERE destination=? ORDER BY rowid",
            ("internal:native-story-preparation",)).fetchall()
    for row in rows:
        packet = json.loads(row["payload"])
        if packet["event_id"].startswith("bls-"):
            latest[packet["event_id"]] = (row["message_id"], packet)
    config = json.loads(Path("config/official_release_history_v1.json").read_bytes())
    archive = Path(config["cc010_archive_root"])
    (ROOT / "sources").mkdir(exist_ok=True)
    (ROOT / "held-inputs").mkdir(exist_ok=True)
    results = []
    for event, family, release, source, measure in [
        ("bls-emsit-20261106", "empsit", "US_NFP_20261106", "investing", "payrolls"),
        ("bls-cpi-20261110", "cpi", "US_CPI_20261110", "myfxbook", "cpi_yoy"),
        ("bls-ppi-20261113", "ppi", "US_PPI_20261113", "myfxbook", "ppi_mom"),
    ]:
        history = load_cc010_history(archive, series=FAMILIES[family], end_period="2026-09", cutoff_utc=now)
        history_path = ROOT / "held-inputs" / (family + "-history.json")
        history_path.write_text(json.dumps(history, indent=2), encoding="utf-8")
        projection_path = CONSENSUS / "daily/2026-11-05" / (release + ".json")
        projection_raw = projection_path.read_bytes()
        projection = json.loads(projection_raw)
        if event in latest:
            previous, packet = latest[event]
            packet = {**packet, "supersedes_preparation_message_id": previous}
        else:
            record = history["series"][0]["observations"][-1]["source_record"]
            raw = gzip.decompress((archive / record["source_relative_artifact"]).read_bytes())
            assert sha256(raw).hexdigest() == record["source_sha256"]
            capture = ROOT / "sources" / (family + "-prior-official.html")
            capture.write_bytes(raw)
            pre = BeautifulSoup(raw, "html.parser").find("pre").get_text()
            first = pre.index("The Producer Price Index for final demand")
            end = pre.index("Final Demand\n", first)
            spans = [p.strip() for p in pre[first:end].split("\n\n") if p.strip()]
            schedule = CONSENSUS / "input/bls-ppi-schedule.json"
            packet = {"event_id": event, "title": "October producer-price preview, 13 November",
                "planned_release_utc": projection["released_at_utc"],
                "reader_question": "Does the next producer-price report broaden the prior inflation shock or show it fading?",
                "background": "Use the dated September final-demand release as the baseline. Separate goods, services and the measure excluding foods, energy and trade services; none is the October result.",
                "official_sources": [{"url": record["source_url"], "capture_path": str(capture),
                    "capture_sha256": record["source_sha256"], "published_at_utc": record["release_datetime_utc"],
                    "observed_at_utc": record["retrieved_at_utc"], "reference_period": "2026-09"},
                    {"url": "https://www.bls.gov/schedule/news_release/ppi.htm", "capture_path": str(schedule),
                     "capture_sha256": sha256(schedule.read_bytes()).hexdigest()}],
                "prior_fact_spans": [{"capture_sha256": record["source_sha256"],
                    "exact_source_span": p, "metric": "BLS September PPI official summary"} for p in spans],
                "watchpoints": ["Final demand goods and services separately.",
                    "Trade services measure margins, not goods prices.",
                    "Producer inflation is not a mechanical forecast of consumer inflation."],
                "release_work": "CC-107 adds only the exact frozen dossier's scenarios and probabilities, reviews the affected copy and dispatches through the existing coordinator before T0.",
                "missing_inputs": ["Frozen October PPI dossier, due before T0; actual October release is not available"],
                "released_facts_admitted": False, "publication_authority": False}
        packet.update(known_at_utc=now, preparation_revision="CC216_EARLY_PREVIEW_BACKGROUND",
            single_consensus_fact={"projection_path": str(projection_path),
                "projection_sha256": sha256(projection_raw).hexdigest(), "capture_root": str(CONSENSUS),
                "release_id": release, "source": source, "measure_key": measure})
        receipt = record_pre_event_preparation(store, packet)
        packet_path = ROOT / "held-inputs" / (event + "-admitted-preparation.json")
        packet_path.write_text(json.dumps({"receipt": receipt, "packet": packet}, indent=2), encoding="utf-8")
        results.append({"event_id": event, "receipt": receipt, "packet_path": str(packet_path),
            "history_path": str(history_path), "cutoff_utc": now})
    result_path.write_text(json.dumps({"prepared_at_utc": now, "store_path": str(STORE),
        "records": results, "public_write_performed": False}, indent=2), encoding="utf-8")
    print(json.dumps({"result_path": str(result_path), "events": [r["event_id"] for r in results]}))


if __name__ == "__main__":
    main()
