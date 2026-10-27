"""Synthetic acceptance for isolated contract tests; never actual MAX visual proof."""
from pathlib import Path

from PIL import Image

from live_contentops.contentops_editorial_desk_v1 import record_native_article_review
from live_contentops.native_desktop_editorial_v1 import (
    DesktopInputRequired, NativeDesktopTurn, final_visual_binding, request_final_visual_review,
    FINAL_VISUAL_DATA_CHECKS, FINAL_VISUAL_LAYOUT_CHECKS, FINAL_VISUAL_PHOTO_CHECKS,
)


def visual_request_fixture(store, binding, result, *, revision_tag="initial"):
    root = Path(binding["output_dir"])
    turn = NativeDesktopTurn(store, run_id=binding["run_id"], output_dir=root, owner_manual_validation=True)
    observation = {"surface": "CODEX_NATIVE_SUBAGENT", "invocation_id": "CONTROLLED_MAX_NOT_REAL_VISUAL_PROOF",
        "model": "gpt-6.1-sol", "reasoning_effort": "max", "speed": "standard",
        "observation_source": "CONTROLLED_CONTRACT_FIXTURE_NOT_ACTUAL_NATIVE_EXECUTION"}
    if not turn._get("write", "response"):
        turn._put("write", "response", {"request_sha256": "CONTROLLED", "output": {}, "invocation_observation": observation})
    folder = root / "controlled-final-visual" / revision_tag
    folder.mkdir(parents=True, exist_ok=True)
    html = folder / "views.html"
    html.write_text("<p>Controlled render fixture, no visual product proof: " + revision_tag + "</p>")
    from hashlib import sha256
    source = {"path": str(html), "sha256": sha256(html.read_bytes()).hexdigest()}
    targets = final_visual_binding(result, renders=None)
    renders = []
    for viewport, width in [("desktop", 1200), ("mobile", 390)]:
        pixels = folder / (viewport + ".png")
        Image.new("RGB", (width, 300), "white").save(pixels)
        for destination, identity in targets["variants"].items():
            renders.append({"render_id": destination + "-" + viewport, "destination": destination,
                "viewport": viewport, "path": str(pixels), "sha256": sha256(pixels.read_bytes()).hexdigest(),
                "render_source": source, "variant_sha256": identity})
    try:
        request_final_visual_review(turn, renders=renders)
    except DesktopInputRequired as pending:
        request = pending.request
    else:
        raise AssertionError("Expected a fresh controlled final visual request")
    governed = request["governed_input"]["binding"]
    output = {"decision": "ACCEPT", "asset_findings": [], "render_findings": []}
    for asset in governed["assets"]:
        keys = (*FINAL_VISUAL_LAYOUT_CHECKS, *(FINAL_VISUAL_DATA_CHECKS if asset["modality"] == "source_backed_chart" else FINAL_VISUAL_PHOTO_CHECKS))
        output["asset_findings"].append({"asset_id": asset["asset_id"], "asset_sha256": asset["sha256"],
            "pixels_inspected": True, "checks": dict.fromkeys(keys, "PASS"), "findings": [],
            "evidence_notes": "Synthetic contract acceptance; not actual visual judgment or model execution."})
    for render in governed["renders"]:
        output["render_findings"].append({"render_id": render["render_id"], "sha256": render["sha256"],
            "pixels_inspected": True, "checks": dict.fromkeys(FINAL_VISUAL_LAYOUT_CHECKS, "PASS"), "findings": [],
            "evidence_notes": "Synthetic viewport coverage; no rendered-product quality claim."})
    response = {"request_sha256": request["request_sha256"], "invocation_observation": observation, "output": output}
    return turn, request, response


def accept_final_visual_fixture(store, binding, result, review):
    turn, request, response = visual_request_fixture(store, binding, result)
    turn.submit(request["stage"], response)
    return record_native_article_review(store, run_id=binding["run_id"], article_identity=result["article_identity"],
        decision="KEEP", rationale="Controlled contract fixture only; this is not real MAX visual review evidence.",
        expected_review_id=review["review_id"], final_visual_review={"stage": request["stage"],
            "request_sha256": request["request_sha256"], "output_dir": str(turn.root)})
