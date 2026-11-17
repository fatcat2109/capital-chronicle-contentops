"""Refresh the existing gallery; retain source/capture clocks and exported R.

This makes review artifacts only. It neither accepts templates nor publishes.
"""
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from live_contentops.image_template_inputs_v1 import bind, HORIZONS
from live_contentops.image_templates_v1 import WEEKLY_CAPACITY
from live_contentops.plan_reader_copy_v1 import result_r
from scripts.image_templates_cc465 import build, write

ROOT = Path(__file__).parent
BASE = ROOT.parent
EXPORT = Path(r"A:\Capital Chronicle\ResearchRuns\plan-status-v1\plan-status.public.json")


def main():
    raw = EXPORT.read_bytes()
    export = json.loads(raw)
    by_id = {p["plan_id"]: p for p in export["plans"]}
    scored = sorted(export["scored_calls"], key=lambda r: r["resolved_at_utc"], reverse=True)
    end = datetime.fromisoformat(scored[0]["resolved_at_utc"].replace("Z", "+00:00")).astimezone(ZoneInfo("America/New_York")).date()
    start = end - timedelta(days=6)
    rows, sources = [], []
    for score in scored:
        resolved = datetime.fromisoformat(score["resolved_at_utc"].replace("Z", "+00:00")).astimezone(ZoneInfo("America/New_York")).date()
        if not start <= resolved <= end:
            continue
        plan = by_id[score["plan_id"]]
        value = result_r(plan)
        if value is None:
            raise ValueError("EXPLICIT_MAIN_R_ABSENT:" + score["plan_id"])
        label = {"STOPPED": "Stopped at invalidation", "TIME_EXIT": "Time exit", "TARGET": "Target reached", "CLOSED_EARLY": "Closed early"}.get(score["result"])
        if score["result"] == "EXPIRED" and score.get("triggered_at_utc"):
            label = "Time exit"
        if not label:
            raise ValueError("ENTERED_RESULT_OUTCOME_NOT_MAPPED:" + score["result"])
        rows.append({"market": score["asset_id"], "direction": "LONG" if score["direction"] == "BULLISH" else "SHORT",
                     "horizon_label": HORIZONS[plan["horizon_lane"]],
                     "main_probability_pct": ((plan.get("scenario_analysis") or {}).get("base_case") or {}).get("probability_pct"),
                     "outcome_label": label, "r": float(value)})
        sources.append(plan)
    values = [row["r"] for row in rows]
    computed = {"calls_closed": len(values), "hit_rate_pct": round(100 * sum(v > 0 for v in values) / len(values), 1),
                "total_r": sum(values), "avg_r": sum(values) / len(values)}
    data = {"schema": "image_input_v1", "post_id": "cc465-exported-weekly-20261112", "template": "weekly",
            "week": {"start": f"{start.day} {start:%b}", "end": f"{end.day} {end:%b}", **computed,
                     "rows": rows, "wrong_note": ""}}
    source = {"plans": sources, "computed": computed, "generated_at_utc": export["generated_at_utc"],
              "export_path": str(EXPORT), "export_sha256": sha256(raw).hexdigest(),
              "formula": "R is Main outcome.result_r; total is sum(R); average is total/count; right is 100*count(R>0)/count, rounded to one decimal; no entry is not a zero result."}
    weekly = ROOT / "inputs" / "weekly.json"
    write(weekly, bind(data, source))
    old = json.loads((BASE / "gallery-manifest.json").read_bytes())
    jobs = []
    for job in old["images"]:
        job = deepcopy(job)
        input_name = Path(job["input_path"]).name
        job["input_path"] = str(weekly.resolve() if input_name == "weekly.json" else (BASE / "inputs" / input_name).resolve())
        if job.get("snapshot_path"):
            parts = Path(job["snapshot_path"]).parts
            job["snapshot_path"] = str(BASE.joinpath(*parts[parts.index("media"):]).resolve())
        jobs.append(job)
        if input_name == "weekly.json":
            for page in range(1, (len(rows)+WEEKLY_CAPACITY[job["master"]]-1)//WEEKLY_CAPACITY[job["master"]]):
                jobs.append({**job, "page": page})
    manifest = ROOT / "gallery-manifest.json"
    write(manifest, {"images": jobs})
    assets, failures = build(manifest, ROOT / "media" / "gallery")
    page = ROOT / "media" / "gallery" / "gallery.html"
    html = page.read_text(encoding="utf-8")
    notice = ("<aside><strong>16 November continuation.</strong> The gallery retains the original "
              "11 November chart captures and source clocks for layout review. These are not fresh "
              "market posts. Main's exported signed R now fills the weekly pages. The four morning-map "
              "images remain held because this input has no daily moves or market states. Initial "
              "template acceptance has not been observed; the published weekly sample is 0/20.</aside>")
    html = html.replace("<nav>", notice + "<nav>", 1)
    for asset in assets:
        name = Path(asset["path"]).name
        quality = asset["image_quality"]
        review = quality.get("vision") or {}
        caption = (f"Combined {quality['score']}/10; "
                   + (f"{review.get('answered_by')}, {review.get('model')}/{review.get('effort')}" if review.get("status") == "REVIEWED" else "vision not reviewed"))
        # Each exact image's review score is visible on the page, without
        # converting that score into an initial template acceptance.
        needle = f'src="{escape(name)}"'
        at = html.find(needle)
        if at >= 0:
            caption_end = html.find("</figcaption>", at)
            html = html[:caption_end] + "<br>" + escape(caption) + html[caption_end:]
    page.write_text(html, encoding="utf-8")
    write(ROOT / "gallery-evidence.json", {"recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "public_export": {"path": str(EXPORT), "sha256": sha256(raw).hexdigest(), "generated_at_utc": export["generated_at_utc"]},
        "weekly": {**computed, "start": start.isoformat(), "end": end.isoformat(), "rows": len(rows),
                   "original_probability_absent": sum(r["main_probability_pct"] is None for r in rows)},
        "images": [{"path": a["path"], "sha256": a["sha256"], "bytes": Path(a["path"]).stat().st_size,
                    "template": a["image_template"]["template"], "master": a["image_template"]["master"],
                    "image_number": a["image_template"]["image_number"], "code": a["image_quality"]["code"]} for a in assets],
        "render_failures": failures,
        "limit": "Held original snapshots and original plan/event inputs retain their clocks. They show layout; this is neither a fresh market report nor a historical entry/exit chart. Missing morning-map inputs remain held. No template acceptance or publication is recorded."})
    print(json.dumps({"images": len(assets), "code_passed": sum(a["image_quality"]["code"]["passed"] for a in assets),
                      "render_failures": len(failures), "gallery": str(ROOT / "media/gallery/gallery.html")}))


if __name__ == "__main__":
    main()
