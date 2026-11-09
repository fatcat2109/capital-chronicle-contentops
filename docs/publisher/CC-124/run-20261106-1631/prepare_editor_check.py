"""Project the exact existing assembled package for its one native editor check."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from live_contentops.native_publication_promotion_v1 import ReadOnlyStore
from live_contentops.native_desktop_editorial_v1 import native_artifact_key, native_review_revision

HERE = Path(__file__).resolve().parent
RUN = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-oil-euro-followup-20261106-v2")
store = ReadOnlyStore(r"A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3")
result = json.loads(store.get_outbox_message(native_artifact_key(store, RUN.name, "cc-editorial-final-"))["payload"])
native = json.loads((RUN / "desktop_response_revise.json").read_bytes())
assert result["simple_result"]["revision_performed"] is True
assert result["article"]["substack_body_markdown"] == native["output"]["article"]["substack_body_markdown"]
packet = {
    "operation_id": RUN.name,
    "article_identity": result["article_identity"],
    "revision": native_review_revision(result),
    "article": result["article"],
    "previews": result["previews"],
    "evidence": result["evidence"],
    "media_assets": result["media_assets"],
    "claim_lineage": result.get("claim_lineage"),
    "accepted_native_response_path": str(RUN / "desktop_response_revise.json"),
    "accepted_native_body_matches_assembly": True,
    "text_approved": False,
    "first_text_approval_utc": None,
    "expected_review_id": None,
    "policy": "JIM_DECISION_53_WRITER_ONE_EDITOR_CHECK_PUBLISH",
}
path = HERE / (sys.argv[1] if len(sys.argv) > 1 else "editor-check-input.json")
path.write_text(json.dumps(packet, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "article_identity": packet["article_identity"], "revision": packet["revision"],
    "preview_count": len(packet["previews"]), "media_count": len(packet["media_assets"]),
    "accepted_native_body_matches_assembly": True}))
