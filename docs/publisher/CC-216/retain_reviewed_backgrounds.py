"""Use the live preparation/writer adapters and save compact CC-216 readback."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from live_contentops.contentops_editorial_desk_v1 import (
    retain_reviewed_preview_background, preview_preparation_research,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.v1_simple_gemini_newsroom_v1 import _source_pack

EVENTS = {"nfp": "bls-emsit-20261106", "cpi": "bls-cpi-20261110", "ppi": "bls-ppi-20261113"}
OUTPUT = Path(__file__).resolve().parent / "reviewed-background-readback.json"


def main(names):
    store = ContentOpsDurableStore(
        "A:/Capital Chronicle/Runtime/ContentOps/contentops_daily_app_v1.sqlite3", auto_migrate=False)
    results = json.loads(OUTPUT.read_bytes()) if OUTPUT.exists() else {}
    for name in names:
        event, run = EVENTS[name], "cc216-" + name + "-background-20261105-v1"
        retained = retain_reviewed_preview_background(store, event_id=event, run_id=run)
        now = datetime.now(timezone.utc).isoformat()
        research = preview_preparation_research(store, event_id=event, cutoff_utc=now)
        source = research.evidence({"headline_ids": list(research.records)}, cutoff_utc=now)
        assert source["status"] == "PASS", source.get("failure_reason")
        pack = _source_pack(source.get("official_source_documents", source.get("evidence_documents", [])))
        backgrounds = [d["preview_preparation"]["reviewed_background"] for d in pack
            if d.get("preview_preparation", {}).get("reviewed_background")]
        assert len(backgrounds) == 1 and backgrounds[0]["run_id"] == run
        background = backgrounds[0]
        assert background["article_revision"] == retained["article_revision"]
        for asset in background["media_assets"]:
            assert sha256(Path(asset["path"]).read_bytes()).hexdigest() == asset["sha256"]
        results[name] = {"event_id": event, "run_id": run, "retained_message_id": retained["message_id"],
            "article_identity": background["article_identity"], "article_revision": background["article_revision"],
            "review_id": background["review_id"], "background_reviewed_at_utc": background["reviewed_at_utc"],
            "writer_source_pack_readback_at_utc": now, "writer_received_reviewed_article": True,
            "title": background["article"]["title"], "retained_media_count": len(background["media_assets"]),
            "media_hashes_verified": True, "source_documents": len(pack),
            "dossier_scenarios_added": background["dossier_scenarios_added"], "public_write_performed": False}
        OUTPUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(json.dumps(results[name]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("names", choices=EVENTS, nargs="+")
    main(parser.parse_args().names)
