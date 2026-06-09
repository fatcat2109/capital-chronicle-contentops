import json
import os

import pytest

from live_contentops import platform_adapter_contracts as pac

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
FIXT_DIR = os.path.join(REPO_ROOT, "fixtures", "platform_dry_runs")

EXPECTED_PLATFORMS = ["x", "linkedin", "telegram", "facebook_page", "instagram", "tiktok"]


def _fixt(name):
    return os.path.join(FIXT_DIR, name)


def _load(name):
    with open(_fixt(name), "r", encoding="utf-8") as f:
        return json.load(f)


def test_registry_has_all_six_platforms():
    assert set(pac.SUPPORTED_PLATFORMS) == set(EXPECTED_PLATFORMS)


def test_registry_entries_are_live_disabled():
    for pid, reg in pac.PLATFORM_REGISTRY.items():
        assert reg["live_api_status"] == "disabled"
        assert reg["credential_read_allowed_now"] is False
        assert reg["scheduling_allowed_now"] is False
        assert reg["replies_or_dms_allowed_now"] is False
        assert reg["scraping_allowed_now"] is False
        assert reg["official_docs_verified"] is False


def test_canonical_schema_parses():
    schema = pac.load_canonical_schema()
    assert schema["title"] == "CanonicalSocialPost"


def test_payload_schema_parses():
    schema = pac.load_payload_schema()
    assert schema["title"] == "PlatformDryRunPayload"


def test_valid_canonical_post_passes_validation():
    post = _load("valid_canonical_social_post.json")
    res = pac.validate_canonical_post(post)
    assert res["valid"] is True, res["errors"]


def test_valid_post_renders_all_six_platforms_text_capable():
    post = _load("valid_canonical_social_post.json")
    results = pac.render_all_platforms(post)
    assert set(results.keys()) == set(EXPECTED_PLATFORMS)
    for pid in ("x", "linkedin", "telegram", "facebook_page"):
        r = results[pid]
        assert r["render_status"] == "rendered", (pid, r["blocking_errors"])
        assert r["dry_run"] is True
        assert r["not_public_postable"] is True
        assert r["live_posting_enabled"] is False
        assert r["credential_accessed"] is False
        assert r["network_accessed"] is False
        assert r["requires_operator_approval"] is True
        assert r["constraint_source"] == pac.CONSTRAINT_SOURCE


def test_media_required_platforms_block_text_only_post():
    post = _load("valid_canonical_social_post.json")
    results = pac.render_all_platforms(post)
    for pid in ("instagram", "tiktok"):
        r = results[pid]
        assert r["render_status"] == "blocked"
        assert "media_required_but_none_provided" in r["blocking_errors"]


def test_render_is_deterministic():
    post = _load("valid_canonical_social_post.json")
    a = pac.render_all_platforms(post)
    b = pac.render_all_platforms(post)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_all_outputs_never_public_postable_or_live():
    post = _load("valid_canonical_social_post.json")
    results = pac.render_all_platforms(post)
    for r in results.values():
        assert r["not_public_postable"] is True
        assert r["live_posting_enabled"] is False
        assert "publish_ready" not in r
        assert r.get("public_postable") is not True


def test_publish_ready_post_fails_closed_everywhere():
    post = _load("invalid_publish_ready_true.json")
    res = pac.validate_canonical_post(post)
    assert res["valid"] is False
    assert "public_postable_must_be_false" in res["errors"]
    assert "safety_flag_must_be_false:public_postable" in res["errors"]
    results = pac.render_all_platforms(post)
    for pid, r in results.items():
        assert r["render_status"] == "blocked", pid
        assert any(e.startswith("post_safety:") for e in r["blocking_errors"])


def test_signal_language_post_blocks_everywhere():
    post = _load("invalid_signal_language.json")
    res = pac.validate_canonical_post(post)
    assert res["valid"] is False
    assert "forbidden_language_in_post" in res["errors"]
    results = pac.render_all_platforms(post)
    for pid, r in results.items():
        assert r["render_status"] == "blocked", pid


def test_unsupported_media_blocks_relevant_platforms():
    post = _load("invalid_unsupported_media_for_platform.json")
    results = pac.render_all_platforms(post)
    assert results["linkedin"]["render_status"] == "rendered"
    assert results["telegram"]["render_status"] == "rendered"
    for pid in ("x", "facebook_page", "instagram", "tiktok"):
        r = results[pid]
        assert r["render_status"] == "blocked", pid
        assert any(
            e.startswith("unsupported_media_for_platform") for e in r["blocking_errors"]
        )


def test_unknown_platform_fails_closed():
    post = _load("valid_canonical_social_post.json")
    r = pac.render_platform_payload(post, "myspace")
    assert r["render_status"] == "blocked"
    assert any(e.startswith("unknown_platform") for e in r["blocking_errors"])


def test_long_text_warns_not_blocks_on_x():
    post = _load("valid_canonical_social_post.json")
    post["body"] = "x" * 5000
    r = pac.render_platform_payload(post, "x")
    assert r["render_status"] == "rendered"
    assert any(w.startswith("text_exceeds_local_placeholder_limit") for w in r["warnings"])


def test_summary_is_safe():
    s = pac.summary()
    assert s["status"] == "ok"
    assert s["live_posting_enabled"] is False
    assert s["credential_read_allowed_now"] is False
    assert s["scheduling_allowed_now"] is False
    assert s["replies_or_dms_allowed_now"] is False
    assert s["scraping_allowed_now"] is False
    assert s["official_docs_verified"] is False
    assert s["all_outputs_not_public_postable"] is True
    assert set(s["supported_platforms"]) == set(EXPECTED_PLATFORMS)


def test_payload_matches_jsonschema_when_available():
    jsonschema = pytest.importorskip("jsonschema")
    schema = pac.load_payload_schema()
    post = _load("valid_canonical_social_post.json")
    r = pac.render_platform_payload(post, "telegram")
    jsonschema.validate(instance=r, schema=schema)
