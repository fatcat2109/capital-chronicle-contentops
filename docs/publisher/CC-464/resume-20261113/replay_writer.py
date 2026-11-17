"""One dated writer replay. Never build a live pack or call a delivery route."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from live_contentops import x_reply_bot_v1 as bot
from live_contentops import x_reply_pack_v1 as packs

base = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\x_reply_pack\bot\20261112T133726-6f8f37ce")
original = packs.read_json(base / "editorial/response.json")
request = next(packs.read_json(p) for p in base.glob("reply-pack-request-*.json")
               if packs.read_json(p)["request_sha256"] == original["request_sha256"])
ranking = packs.read_json(base / "editorial/rank/response.json")
root = base.parent / ("replay-cc464-budget150-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S"))
root.mkdir()
request["draft_limit"] = 2
request["request_sha256"] = packs.digest({k: v for k, v in request.items() if k != "request_sha256"})
packs.save_json(root / "request.json", request)
summary = {"source_tick": str(base), "replay_artifact": str(root),
           "historical_cutoff_utc": request["prepared_at_utc"],
           "telegram_send_actions": 0, "x_submit_actions": 0, "live_delivery_proof": False}
try:
    path = bot.rank_and_draft(root / "request.json", output_dir=root / "editorial",
        ranker=lambda *a, **k: (ranking, {"reused_saved_artifact": str(base / "editorial/rank/response.json")}),
        now=packs.clock(request["prepared_at_utc"]))
    response = packs.read_json(path)
    posts = {p["post_id"]: p for p in request["candidates"]}
    sources = {s["source_id"]: s for s in request["sources"]}
    validation = []
    for draft in response.get("items", []):
        try:
            text = packs.validate_mobile_draft(draft, posts[draft["post_id"]], sources[draft["source_id"]],
                                              now=packs.clock(request["prepared_at_utc"]))
            validation.append({"post_id": draft["post_id"], "status": "PASS", "draft_text": text})
        except (ValueError, KeyError) as exc:
            validation.append({"post_id": draft["post_id"], "status": "REFUSED", "cause": str(exc)})
    summary.update(status="RETURNED", authored_ids=[i["post_id"] for i in response["items"]],
                   remaining_quality_post_ids=response["remaining_quality_post_ids"],
                   stage_seconds=response["stage_seconds"], validation=validation)
except ValueError as exc:
    summary.update(status="FAILED", cause=str(exc))
summary["writer_call"] = packs.read_json(root / "editorial/writer/call.json")
summary["writer_prompt_bytes"] = (root / "editorial/writer/prompt.txt").stat().st_size
summary["replay_observed_at_utc"] = datetime.now(timezone.utc).isoformat()
packs.save_json(Path(__file__).with_name("native-budget150-replay.json"), summary)
print(json.dumps(summary, indent=2))
