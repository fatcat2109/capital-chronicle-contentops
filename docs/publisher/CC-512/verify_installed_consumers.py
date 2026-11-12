"""One installed image/variants preparation, retaining source checks and artifacts.

This does not dispatch or change an issued outbox payload. Each role's actual
model return is saved before any downstream acceptance result is evaluated.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import sys

OPERATING = Path(r"A:\Capital Chronicle\ContentOps")
EVIDENCE = Path(__file__).resolve().parent
RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc512-light-caller-integration")
sys.path.insert(0, str(OPERATING))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("role", choices=["image", "variants"])
    parser.add_argument("--post-key")
    args = parser.parse_args()
    record = {"item": "CC-512", "role": args.role, "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "public_write_performed": False, "issued_payload_changed": False}
    try:
        if args.role == "image":
            from live_contentops import image_quality_v1 as quality
            source = OPERATING / "docs/publisher/CC-465/media/gallery/cc465-retained-cpi-layout-event-2-T.json"
            asset = json.loads(source.read_bytes())
            meta = asset["image_template"]
            folder = RUNTIME / "media"
            record.update(consumer_module=quality.__file__, source_metadata=str(source), source_image_sha256=asset["sha256"])
            try:
                prepared = quality.prepare_asset(meta["input"], meta["master"], folder, meta.get("snapshot"),
                    image_number=meta["image_number"], page=meta.get("page", 0))
            except ValueError as exc:
                # A valid low score must continue to refuse the actual image.
                record["consumer_refusal"] = str(exc)
                prepared = json.loads((folder / Path(asset["path"]).with_suffix(".json").name).read_bytes())
            record.update(asset=prepared, same_rendered_image=prepared["sha256"] == asset["sha256"],
                          status=prepared["image_quality"]["vision"]["status"])
        else:
            from live_contentops import plan_reader_editorial_v1 as editorial
            from live_contentops import plan_analysis_pages_v1 as pages
            from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
            from live_contentops.published_content_v1 import PRODUCTION_STORE
            store = ContentOpsDurableStore(PRODUCTION_STORE, auto_migrate=False)
            stored_row = store.get_outbox_message(args.post_key)
            row = json.loads(stored_row["payload"])
            # The already-issued pre-CC466 row keeps its original payload.
            # Bind the preparation to its confirmed original page locally.
            packet_row = store.get_outbox_message("plan-analysis-" + row["plan_id"])
            packet = json.loads(packet_row["payload"]) if packet_row else None
            if not packet or not pages.page_status(store, packet)["confirmed"]:
                raise ValueError("SUBSTACK_PLAN_PAGE_NOT_CONFIRMED")
            row.setdefault("source_plan", packet["source_plan"])
            record.update(consumer_module=editorial.__file__, post_key=args.post_key,
                          plan_id=row["source_plan"]["plan_id"], canonical_confirmed=True)
            result = editorial.prepare_variants(packet, row, output_dir=RUNTIME / args.post_key)
            assert store.get_outbox_message(args.post_key)["payload"] == stored_row["payload"]
            record.update(result=result, status=result["status"])
    except Exception as exc:
        record.update(status="FAILED", cause=type(exc).__name__ + ":" + str(exc))
    finally:
        record["ended_at_utc"] = datetime.now(timezone.utc).isoformat()
        path = EVIDENCE / ("installed-" + args.role + "-call.json")
        save(path, record)
        print(json.dumps({"evidence": str(path), "status": record["status"], "cause": record.get("cause")}))


if __name__ == "__main__":
    main()
