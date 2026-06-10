
import pytest
import os
import json
from live_contentops.platform_dry_run_renderer import render_dry_run_from_file

FIX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "platform_dry_runs")

def _fixt(name):
    return os.path.join(FIX_DIR, name)

def test_valid_x():
    res = render_dry_run_from_file(_fixt("valid_canonical_social_post.json"), "x")
    assert res["render_status"] == "rendered"

def test_invalid_public_postable_true():
    res = render_dry_run_from_file(_fixt("invalid_public_postable_true.json"), "x")
    assert res["render_status"] == "blocked"
    assert any("blocked_flag:public_postable" in r for r in res["blocking_errors"])

def test_invalid_live_posting_enabled_true():
    res = render_dry_run_from_file(_fixt("invalid_live_posting_enabled_true.json"), "x")
    assert res["render_status"] == "blocked"
    assert any("blocked_flag:live_posting_enabled" in r for r in res["blocking_errors"])

def test_invalid_forbidden_signal_language():
    res = render_dry_run_from_file(_fixt("invalid_forbidden_signal_language.json"), "x")
    assert res["render_status"] == "blocked"
    assert any("forbidden_signal:short" in r for r in res["blocking_errors"])

def test_invalid_instagram_requires_media():
    res = render_dry_run_from_file(_fixt("invalid_instagram_text_only_without_media.json"), "instagram")
    assert res["render_status"] == "blocked"
    assert any("media_required_for_platform" in r for r in res["blocking_errors"])

def test_invalid_unknown_platform():
    res = render_dry_run_from_file(_fixt("invalid_unknown_platform.json"), "myspace")
    assert res["render_status"] == "blocked"
    assert any("unsupported_platform:myspace" in r for r in res["blocking_errors"])
