"""Build exact media-plan inputs for the existing newsroom CLI, without dispatch."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

BASE = Path("A:/Capital Chronicle/Runtime/ContentOps/daily_app_outputs/owner-manual")
HERE = Path(__file__).resolve().parent


def main(name):
    root = BASE / ("cc216-" + name + "-background-20261105-v1")
    request = json.loads((root / "desktop_request_media-plan.json").read_bytes())
    response = json.loads((root / "desktop_response_media-plan.json").read_bytes())
    assert request["request_sha256"] == response["request_sha256"]
    assets = json.loads((root / "rendered-assets.json").read_bytes())
    for asset in assets:
        assert sha256(Path(asset["path"]).read_bytes()).hexdigest() == asset["sha256"]
        assert asset["visual_review"]["asset_sha256"] == asset["sha256"]
        assert asset["visual_review"]["pixels_inspected"] is True
    context_path = HERE / "main-daily-analysis-context.json"
    context = json.loads(context_path.read_bytes())
    context = {"context_record_path": str(context_path),
        "context_record_sha256": sha256(context_path.read_bytes()).hexdigest(),
        "analysis_cutoff_utc": context["analysis_cutoff_utc"],
        "qualitative_question": context["exact_qualitative_span"],
        "use": context["use"], "not_factual_event_evidence": True}
    value = {"plan": {"native_plan_run_id": root.name, "native_plan_stage": "media-plan",
        "native_plan_request_sha256": request["request_sha256"],
        "story_plan": response["output"]["story_plan"], "desk_analysis_context": context}, "assets": assets}
    target = root / "media-plan-binding.json"
    target.write_text(json.dumps(value, indent=2), encoding="utf-8")
    print(json.dumps({"response_path": str(target), "assets": len(assets), "public_write_performed": False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name", choices=["nfp", "cpi", "ppi"])
    main(parser.parse_args().name)
