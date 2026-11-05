"""Read CC-124 output with the accepted CC-122 consumer; send nothing."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import types

ROOT = Path(__file__).resolve().parent
REPOSITORY = Path(r"A:\Capital Chronicle\Worktrees\codex-main-exec")
COMMIT = "e8f565d8f8"

def source(path):
    return subprocess.run(["git", "show", COMMIT + ":" + path], cwd=REPOSITORY,
        capture_output=True, text=True, encoding="utf-8", check=True).stdout

consumer_source = source("tools/product/contentops_digest_v1.py")
consumer = types.ModuleType("accepted_cc122_contentops_reader")
exec(compile(consumer_source, "<accepted-cc122-contentops-reader>", "exec"), consumer.__dict__)
main_source = source("tools/product/main_daily_digest_v1.py")
reader_node = next(n for n in ast.parse(main_source).body if isinstance(n, ast.ClassDef) and n.name == "Reader")
namespace = {"Path":Path, "hashlib":hashlib, "json":json}
exec(compile(ast.Module(body=[reader_node], type_ignores=[]), "<accepted-cc122-reader>", "exec"), namespace)
reader = namespace["Reader"]()
next_digest_reference = datetime(2026,11,6,0,0,tzinfo=timezone.utc)
record = consumer.default_production_record(next_digest_reference)
expected = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\newsroom-production-day-2026-11-05-bangkok\newsroom_production_day_v1.json")
assert record == expected
result = consumer.collect_contentops(reader, record=record, store=consumer.STORE, now=datetime.now(timezone.utc))
assert result["state"] == "SAVED_RECORD"
assert result["distinct_articles_published"] == 1
assert result["confirmed_copies_by_channel"]["x"] == 1
assert result["confirmed_copies_by_channel"]["youtube"] == 1
assert result["confirmed_copies_by_channel"]["linkedin_company"] == 1
output = {"consumer_accepted_commit":subprocess.run(["git","rev-parse",COMMIT],cwd=REPOSITORY,
    capture_output=True,text=True,check=True).stdout.strip(),
    "consumer_source_sha256":hashlib.sha256(consumer_source.encode()).hexdigest(),
    "checked_at_utc":datetime.now(timezone.utc).isoformat(),
    "next_digest_reference_for_path_selection_only":next_digest_reference.isoformat(),
    "record_sha256":hashlib.sha256(record.read_bytes()).hexdigest(),
    "observed_reader_result":result,"schedule_changed":False,"digest_dispatched":False}
(ROOT / "digest-consumer-acceptance.json").write_text(json.dumps(output,indent=2),encoding="utf-8")
print(json.dumps({"reader_state":result["state"],"distinct_articles_published":result["distinct_articles_published"],
    "confirmed_copies_by_channel":result["confirmed_copies_by_channel"],"next_0700_record":str(record),"digest_dispatched":False}))
