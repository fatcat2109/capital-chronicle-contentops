"""Local-only incident reproduction and rendered evidence; no public calls or store writes."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from PIL import Image
from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
from live_contentops.media_manifest_authority_v1 import build_delivery_only_editorial_card
from live_contentops.rolling_x_grounded_article_media_builder_v1 import build_post_image_card

BASE = "5150b4b01da742094dabd1ce3c65fbb597003071"
OUT = Path(__file__).resolve().parent


def run():
    source = subprocess.check_output(["git", "show", BASE + ":live_contentops/_eight_platform_substack_first_pipeline_impl_v1.py"], cwd=ROOT).decode("utf-8")
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "_durable_intent_inputs")
    namespace = dict(pipeline.__dict__)
    exec(compile(ast.Module(body=[node], type_ignores=[]), BASE, "exec"), namespace)
    baseline = namespace["_durable_intent_inputs"]
    checks = []
    with TemporaryDirectory(prefix="cc186-visual-repro-") as temp:
        root = Path(temp)
        assets, hosted = [], []
        for name, color in [("old-card", "navy"), ("reviewed-chart", "white")]:
            path = root / (name + ".png")
            Image.new("RGB", (160, 90), color).save(path)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assets.append({"asset_id": name, "path": str(path), "sha256": digest})
            hosted.append({"media_asset_id": name, "sha256": digest, "public_delivery_sha256": digest,
                "local_public_hash_continuity": True, "verified_public_delivery_url": "https://example.invalid/" + name + ".png"})
        article = {"title": "An admitted release", "subtitle": "A retained official release.", "native_brief_layout": True,
            "substack_body_markdown": "Retained source-bound public article. Analysis, not financial advice."}
        (root / "run_context_v1.json").write_text(json.dumps({"article": article, "selection": {}, "media": {"assets": assets}}))
        (root / "delivery_media_manifest_v1.json").write_text(json.dumps({"assets": hosted}))
        intent = {"output_dir": str(root), "destination_plan": {"destination": "instagram_business"},
            "canonical_url": "https://capitalchronicle.substack.com/p/local-fixture",
            "native_payload": {"text": "Accepted public copy", "media_asset_ids": ["reviewed-chart", "old-card"]}}
        before, after = baseline(intent), pipeline._durable_intent_inputs(intent)
        checks.append({"case": "reviewed_order", "expected": "reviewed-chart", "before": before["primary_media"].get("media_asset_id"),
            "after": after["primary_media"].get("media_asset_id"), "before_pass": False, "after_pass": True})
        assert checks[-1]["before"] == "old-card" and checks[-1]["after"] == "reviewed-chart"
        intent["native_payload"]["media_asset_ids"] = ["unresolved-reviewed-chart"]
        before = baseline(intent)
        try:
            pipeline._durable_intent_inputs(intent)
        except ValueError as exc:
            after_cause = str(exc)
        else:
            raise AssertionError("missing reviewed image must not select retained hosted card")
        checks.append({"case": "unresolved_selected_id", "expected": "no transport with unrelated old card",
            "before": before["primary_media"].get("media_asset_id"), "after": after_cause, "before_pass": False, "after_pass": True})
        assert checks[-1]["before"] == "old-card" and after_cause.startswith("reviewed_delivery_media_asset_unavailable:")
    packet = ROOT / "tests/evidence/cc-142/reader-chart-revision.json"
    article = json.loads(packet.read_text(encoding="utf-8"))["article"]
    # The supplied article is already admitted; this local render makes no new source claim.
    card = build_post_image_card(article, output_dir=OUT / "render", accepted_evidence_sha256="a" * 64)
    delivery = build_delivery_only_editorial_card(output_path=OUT / "render/delivery-facts-card.png",
        title=article["title"], source_label="CONFIRMED", source_page_url="https://www.bls.gov/", article=article)
    evidence = {"base_commit": BASE, "baseline_function_sha256": hashlib.sha256(ast.get_source_segment(source, node).encode()).hexdigest(),
        "reproduction": checks, "public_requests": 0, "production_store_writes": 0,
        "retained_article_path": str(packet.relative_to(ROOT)), "retained_article_file_sha256": hashlib.sha256(packet.read_bytes()).hexdigest(),
        "local_render_scope": "Local formatting check from retained admitted article. Repeated a-hash is a fixture admission token, not a production approval.",
        "post_card": card, "delivery_card": delivery,
        "existing_public_object": {"url": "https://www.instagram.com/p/DfUAKIzgfPH/", "id": "18140916916727008", "changed": False}}
    (OUT / "reproduction-and-renders.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"reproduction": checks, "post_card": card["path"], "delivery_card": delivery["path"], "public_requests": 0}, indent=2))


if __name__ == "__main__":
    run()
