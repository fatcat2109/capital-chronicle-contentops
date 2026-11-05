"""One native editorial repair with source validation and all-eight preview checks."""

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import re

from live_contentops.native_desktop_editorial_v1 import validate_native_configuration
from live_contentops.v1_simple_gemini_newsroom_v1 import (
    _hash,
    _native_preview_bundle,
    _validate_article_against_source_pack,
    _validate_worker_text,
)


BASE = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-jobs-fx-watch-20261105-f")
REQUEST_PATH = BASE / "desktop_request_revise.json"
REQUEST = json.loads(REQUEST_PATH.read_bytes())
assert REQUEST["request_sha256"] == "e1005bb0595aeb6d6a80f395a5d86f591cf30706d3126133219b07712e75ff31"
GOVERNED = REQUEST["governed_input"]
WRITER_PATH = BASE / "desktop_response_write.json"
WRITER = json.loads(WRITER_PATH.read_bytes())
PRIOR = WRITER["output"]
assert _hash(PRIOR) == GOVERNED["prior_output_hash"]
OUTPUT = deepcopy(PRIOR)
ARTICLE = OUTPUT["article"]
ORIGINAL_BODY = ARTICLE["substack_body_markdown"]

# LinkedIn uses the mechanism summary. Reuse the existing complete chart
# explanation verbatim: it has the Fed attribution, both dates, units and method.
MECHANISM = next(p.split(" [[SOURCE:")[0] for p in ORIGINAL_BODY.split("\n\n")
    if p.startswith("The first chart puts both relationships"))
ARTICLE["social_mechanism_summary"] = MECHANISM

# Threads uses the competing-explanation summary. Keep its complete argument
# and qualify the same dated comparison with its source in both copies.
OLD_SENTENCE = "The October 26-30 comparison cannot identify which driver dominated."
NEW_SENTENCE = "The October 26-30 Fed reference-rate comparison cannot identify which driver dominated."
assert ORIGINAL_BODY.count(OLD_SENTENCE) == 1
assert ARTICLE["social_policy_summary"].count(OLD_SENTENCE) == 1
ARTICLE["social_policy_summary"] = ARTICLE["social_policy_summary"].replace(OLD_SENTENCE, NEW_SENTENCE)
ARTICLE["substack_body_markdown"] = ORIGINAL_BODY.replace(OLD_SENTENCE, NEW_SENTENCE)
assert ARTICLE["substack_body_markdown"].replace(NEW_SENTENCE, OLD_SENTENCE) == ORIGINAL_BODY

# Update only the binding whose claim text is that exact revised summary.
changed_claims = []
for claim in OUTPUT["material_claim_bindings"]:
    if OLD_SENTENCE in claim["claim_text"]:
        prior_text = claim["claim_text"]
        claim["claim_text"] = prior_text.replace(OLD_SENTENCE, NEW_SENTENCE)
        changed_claims.append({"claim_id": claim["claim_id"], "prior_text": prior_text, "revised_text": claim["claim_text"]})
assert [c["claim_id"] for c in changed_claims] == ["conditional-countercase"]
assert ARTICLE["visual_editorial_decision"] == GOVERNED["visual_editorial_decision"]
assert OUTPUT["cited_sources"] == PRIOR["cited_sources"]
assert set(ARTICLE) == set(PRIOR["article"])
article_changes = [k for k in ARTICLE if ARTICLE[k] != PRIOR["article"][k]]
assert set(article_changes) == {"social_mechanism_summary", "social_policy_summary", "substack_body_markdown"}
for key in ("social_mechanism_summary", "social_policy_summary", "social_cross_asset_summary"):
    assert ARTICLE[key] in ARTICLE["substack_body_markdown"]

ok, failure_class, _, reason = _validate_worker_text(json.dumps(OUTPUT))
assert ok, (failure_class, reason)
validated, validation = _validate_article_against_source_pack(OUTPUT, GOVERNED["source_pack"],
    selected_candidate=GOVERNED["selected_candidate"], article_mode=GOVERNED["article_mode"],
    epistemic_state=GOVERNED["epistemic_state"])
preview_article = dict(validated)
preview_article.update(public_source_bindings=OUTPUT["cited_sources"],
    reader_attribution_policy=GOVERNED["reader_attribution_policy"])
media = GOVERNED["editorial_media_plan"]["assets"]
bundle, rows = _native_preview_bundle(article=preview_article, article_mode=GOVERNED["article_mode"],
    article_identity=REQUEST["run_id"], epistemic_state=GOVERNED["epistemic_state"],
    media_asset_ids=[a["asset_id"] for a in media], media_assets=media)
assert bundle["package_count"] == 8
assert bundle["every_preview_preserves_epistemic_state"]


def weighted_length(text):
    count, cursor = 0, 0
    for match in re.finditer(r"https?://[^\s)]+", text):
        count += sum(1 if ord(c) <= 0x10FF or 0x2000 <= ord(c) <= 0x200D
            or 0x2010 <= ord(c) <= 0x201F or 0x2032 <= ord(c) <= 0x2037 else 2
            for c in text[cursor:match.start()]) + 23
        cursor = match.end()
    return count + sum(1 if ord(c) <= 0x10FF or 0x2000 <= ord(c) <= 0x200D
        or 0x2010 <= ord(c) <= 0x201F or 0x2032 <= ord(c) <= 0x2037 else 2
        for c in text[cursor:])


audit = {}
assert set(bundle["packages"]) == {"telegram", "discord", "x", "linkedin", "facebook_page", "instagram_business", "threads", "youtube"}
for destination, payload in bundle["packages"].items():
    posts = payload.get("posts") or []
    texts = [p["text"] for p in posts] if posts else [str(payload.get(k) or "") for k in ("text", "full_text", "root_text", "caption")]
    visible = "\n\n".join(texts)
    assert "Analysis, not financial advice." in visible, destination
    assert "Capital Chronicle may hold positions in the markets it covers." in visible, destination
    assert "October 26-30" in visible or ("October 26" in visible and "October 30" in visible), destination
    assert re.search(r"(?<!\w)Fed(?!\w)", visible), destination
    assert payload.get("media_asset_ids"), destination
    assert not re.search(r"(?:fatcat2109|capital-chronicle-preview|github\.io|pages\.dev|workers\.dev|netlify\.app|vercel\.app|localhost|127\.0\.0\.1)", visible, re.I), destination
    audit[destination] = {"epistemic_owner_gate": "PASS", "fed_attribution_present": True,
        "dated_comparison_window_present": True, "both_reader_notices_present": True,
        "media_asset_ids": payload["media_asset_ids"], "post_count": len(posts), "preview_host_link_absent": True}
    if destination in {"x", "threads"}:
        limit = 280 if destination == "x" else 500
        metrics = payload["quality_metrics"]
        assert metrics["sentence_boundary_pass"] is True
        assert metrics["orphan_fragment_count"] == 0
        assert metrics["hard_character_slicing_used"] is False
        assert all(weighted_length(t) <= limit for t in texts), destination
        audit[destination].update(max_weighted_characters=max(map(weighted_length, texts)), platform_limit=limit)

OBS = deepcopy(WRITER["invocation_observation"])
OBS["configuration_source"] = "Supported parent continuation in the same native task /root/native_max_fx_42ae7362164c and exact frozen revision request e1005bb0595aeb6d6a80f395a5d86f591cf30706d3126133219b07712e75ff31 assign gpt-6.1-sol/max; actual runtime model and effort telemetry remains unavailable."
OBS["observation_source"] = "Supported same native subagent identity from visual planning, asset inspection and writing through this one bounded prose revision; actual model/effort values are unobserved."
OBS["revision_input"] = {"path": str(REQUEST_PATH), "sha256": sha256(REQUEST_PATH.read_bytes()).hexdigest(),
    "request_sha256": REQUEST["request_sha256"], "prior_writer_response_path": str(WRITER_PATH),
    "prior_writer_response_sha256": sha256(WRITER_PATH.read_bytes()).hexdigest(), "same_native_context": True}
assert OBS["invocation_id"] == "/root/native_max_fx_42ae7362164c"
assert OBS["model"] is None and OBS["reasoning_effort"] is None
validate_native_configuration(OBS, {"model": "gpt-6.1-sol", "reasoning_effort": "max"})
RESPONSE = {"request_sha256": REQUEST["request_sha256"], "output": OUTPUT, "invocation_observation": OBS}


def main():
    path = BASE / "desktop_response_revise.json"
    assert not path.exists(), "Preserve any already saved native revision return"
    path.write_text(json.dumps(RESPONSE, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    evidence_path = Path(__file__).with_name("revision-local-validation.json")
    evidence = {"request_sha256": REQUEST["request_sha256"], "response_path": str(path),
        "response_sha256": sha256(path.read_bytes()).hexdigest(), "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_validation": validation, "native_preview_owner_gate": {"status": "PASS", "package_count": 8},
        "local_preview_bundle": bundle, "local_preview_rows": rows, "payload_audit": audit,
        "article_fields_changed": article_changes, "canonical_prose_change": {"prior": OLD_SENTENCE, "revised": NEW_SENTENCE,
            "reason": "The exact source-bound counterpart of Threads' authored summary gains natural Fed attribution; all other canonical prose is byte-identical."},
        "changed_claim_bindings": changed_claims, "title_and_supported_values_unchanged": True,
        "source_pack_unchanged": True, "charts_and_photo_unchanged": True,
        "public_write_attempted": False, "final_assembled_pixel_review": "PENDING"}
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"response_path": str(path), "response_sha256": evidence["response_sha256"],
        "validation_path": str(evidence_path), "schema": "PASS", "source_validation": validation["status"],
        "supported_material_claim_count": validation["supported_material_claim_count"],
        "native_preview_owner_gate": evidence["native_preview_owner_gate"], "article_fields_changed": article_changes,
        "payload_audit": audit}, ensure_ascii=True))


if __name__ == "__main__":
    main()
