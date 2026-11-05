"""Retain the actual post-click platform refusal without inventing a no-click result."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
begin = json.loads((HERE / "youtube-publish-begin-expanded.json").read_bytes())
click = json.loads((HERE / "youtube-click-observed.json").read_bytes())
raw = Path(click["verified"]["path"]).read_text(encoding="utf-8")
preclick = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
observed = json.loads((HERE / "youtube-absence-observed.json").read_bytes())
assert observed["authenticated"] and observed["target_post_absent"]
assert "24" in observed["visible_dialogs"][0]
response = {"tool_request_sha256": begin["tool_request_sha256"],
    "tool_observation": {"surface": "CODEX_EXEC", "tool_name": "mcp__browseros_neo__run",
        "native_invocation_id": "/root", "observed_at_utc": observed["observed_at_utc"],
        "dispatched_at_utc": preclick["observed_at_utc"],
        "observation_source": "Actual own-channel composer, one publish click, visible YouTube advanced-features refusal and own-channel posts readback. No repeated click."},
    "result": {"request_sha256": begin["request"]["request_sha256"], "status": "UNKNOWN_WRITE",
        "stage": "PUBLISH_CLICK_ATTEMPTED", "observed_identity": "@CapitalChronicleYouTube",
        "reason_code": "YOUTUBE_ADVANCED_FEATURE_VERIFICATION_OR_24H_WAIT",
        "platform_message": observed["visible_dialogs"][0], "public_write_performed": False,
        "retry_permitted": False},
    "composed": {"identity": {"authenticated": True, "observed_identity": "@CapitalChronicleYouTube",
        "observed_at_utc": preclick["observed_at_utc"],
        "basis": "Own channel link and Manage videos were observed in this composer flow before the one click."},
        "pre_click_posts": [preclick["text"]],
        "readback": {"status": "BLOCKED", **observed, "public_write_performed": False}}}
(HERE / "youtube-publish-response.json").write_text(json.dumps(response, indent=2), encoding="utf-8")
print(json.dumps({"reason": response["result"]["reason_code"], "dispatched_at_utc": preclick["observed_at_utc"],
    "absence_observed_at_utc": observed["observed_at_utc"], "no_retry": True}))
