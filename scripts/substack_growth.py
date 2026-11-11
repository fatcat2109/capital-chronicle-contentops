"""CC-468: one explicit prepare, Note continuation or read-only review action."""
from datetime import datetime, timezone
from contextlib import contextmanager
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.published_content_v1 import PRODUCTION_STORE


class ReadOnlyStore(ContentOpsDurableStore):
    @contextmanager
    def get_connection(self):
        connection = self.get_read_only_connection()
        try:
            yield connection
        finally:
            connection.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare-events", "note", "report"))
    parser.add_argument("--table", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--producer-commit")
    parser.add_argument("--acquisition-observation", type=Path, help="report: retained visible Substack source-table observation")
    parser.add_argument("--store", type=Path, default=PRODUCTION_STORE)
    parser.add_argument("--publish", action="store_true", help="only for note: continue the existing sole coordinator")
    args = parser.parse_args(argv)
    if args.publish and args.command != "note":
        parser.error("--publish applies to the Note continuation only")
    now = datetime.now(timezone.utc)
    if args.command == "prepare-events":
        if not args.table or not args.producer_commit:
            parser.error("prepare-events requires --table and --producer-commit")
        from live_contentops.event_reaction_source_v1 import prepare
        result = {"item": "CC-468", "event_sources": prepare(args.table, args.out,
            generated_at_utc=now.isoformat(), producer_commit=args.producer_commit)}
    elif args.command == "note":
        from live_contentops.substack_daily_note_v1 import run_due
        result = run_due(ContentOpsDurableStore(args.store, auto_migrate=False), output_root=args.out,
                         publish=args.publish, automatic_neo=args.publish)
    else:
        from live_contentops.substack_growth_review_v1 import report
        result = report(ReadOnlyStore(args.store, auto_migrate=False), now=now,
            acquisition_observation=json.loads(args.acquisition_observation.read_bytes()) if args.acquisition_observation else None)
    args.out.mkdir(parents=True, exist_ok=True)
    path = args.out / (args.command + "-result.json")
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"item": "CC-468", "state": result.get("state") or result.get("decision_state"),
                      "result_path": str(path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
