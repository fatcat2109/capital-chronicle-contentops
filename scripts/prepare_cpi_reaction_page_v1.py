"""Prepare CC-425 in the existing newsroom; never sends or schedules anything."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops.capital_chronicle_desk_record_source_v1 import desk_evidence, read_export
from live_contentops.cpi_reaction_page_v1 import EVENT_PAGES, bind_tables, writer_guidance
from live_contentops.v1_simple_gemini_newsroom_v1 import _source_pack


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def prepare(binding_path, profile_path, out, *, cutoff_utc, event="CPI"):
    spec = EVENT_PAGES[event]
    record_id, title = spec["record_id"], spec["title"]
    pointer = json.loads(Path(binding_path).read_bytes())
    specs = pointer.get("desk_record_exports", [])
    records = [r for s in specs for r in read_export(s, cutoff_utc=cutoff_utc)
               if r["binding"]["record_id"] == record_id]
    if len(records) != 1 or records[0]["binding"]["fixture"]:
        raise ValueError("ONE_REAL_" + event + "_REACTION_EXPORT_REQUIRED")
    record = records[0]
    evidence = desk_evidence(records, {"headline_ids": [record["headline_id"]]})
    pack = _source_pack(evidence["evidence_documents"])
    if len(pack) != 1 or not pack[0].get("cpi_reaction_page"):
        raise ValueError("CPI_REACTION_WRITER_CONSUMER_NOT_WIRED")
    # Each source edition has its own files. A refresh cannot rewrite a path
    # already frozen into an editorial operation or reviewed article.
    out = Path(out).resolve() / ("source-" + record["binding"]["export_bytes_sha256"][:16])
    out.mkdir(parents=True, exist_ok=True)
    matching = [s for s in specs if s["sha256"] == record["binding"]["export_bytes_sha256"]]
    if len(matching) != 1:
        raise ValueError("CPI_REACTION_EXPORT_BINDING_AMBIGUOUS")
    original = Path(matching[0]["path"]).read_bytes()
    if hashlib.sha256(original).hexdigest() != matching[0]["sha256"]:
        raise ValueError("DESK_EXPORT_BYTES_MISMATCH")
    snapshot = out / "desk-export.json"
    snapshot.write_bytes(original)
    own_pointer = {**pointer, "desk_record_exports": [{"path": str(snapshot),
                    "sha256": matching[0]["sha256"]}]}
    save(out / "feed-binding.json", own_pointer)
    profile = json.loads(Path(profile_path).read_bytes())
    profile["feed_pointer_path"] = str(out / "feed-binding.json")
    save(out / "profile.json", profile)
    save(out / "source-pack.json", pack)
    rendered = bind_tables({"substack_body_markdown": "[[CPI_REACTION_TABLES]]"}, pack)
    (out / "reader-tables.md").write_text(rendered["substack_body_markdown"] + "\n", encoding="utf-8")
    (out / "writer-guidance.txt").write_text(writer_guidance(pack), encoding="utf-8")
    summary = {"item": "CC-425" if event == "CPI" else "CC-468", "event_family": event,
        "observed_at_utc": cutoff_utc,
        "preparation_dir": str(out),
        "source_known_at_utc": record["known_at_utc"],
        "source_data_cutoff_utc": pack[0].get("data_cutoff_utc"),
        "source_export_path": matching[0]["path"], "source_export_sha256": matching[0]["sha256"],
        "source_record_id": record_id, "title": title,
        "consumer": "read_export -> desk_evidence -> _source_pack -> bind_tables",
        "writer_source_chars": len(pack[0]["canonical_content_text"]),
        "full_source_preserved": pack[0]["canonical_content_text"] == evidence["evidence_documents"][0]["canonical_content_text"],
        "tables": len(pack[0]["cpi_reaction_page"]["tables"]),
        "table_sha256": rendered["cpi_reaction_page"]["table_sha256"],
        "source_table_sha256": [t["source_table_sha256"] for t in pack[0]["cpi_reaction_page"]["tables"]],
        "publication_state": "NOT_DISPATCHED",
        "remaining": (["CC-417: Ops Product reads the table before the first post",
                      "CC-417 producer refresh: the November map/result and actual data cutoff",
                      "Native final article, media/review, canonical readback and CPI review link"]
                      if event == "CPI" else ["Native final article and source-bound media/review",
                        "Existing coordinator publication and exact public readback",
                        "Reference the confirmed canonical page in the relevant event review"])}
    save(out / "consumer-readback.json", summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binding", required=True)
    parser.add_argument("--event", choices=EVENT_PAGES, default="CPI")
    parser.add_argument("--profile", default="config/native_desktop_operator_profile_v1.json")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = prepare(args.binding, args.profile, args.out,
                     cutoff_utc=datetime.now(timezone.utc).isoformat(), event=args.event)
    print(json.dumps({k: result[k] for k in ("item", "source_export_sha256", "consumer", "tables",
                                           "full_source_preserved", "publication_state")}))
