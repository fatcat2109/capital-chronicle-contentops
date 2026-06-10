
import pytest
import os
import json
from live_contentops.platform_dry_run_renderer import render_dry_run_from_file

FIX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "platform_dry_runs")

def _fixt(name):
    return os.path.join(FIX_DIR, name)

def test_platform_dry_run_schema():
    # render_dry_run already validates against schema
    res = render_dry_run_from_file(_fixt("valid_canonical_social_post.json"), "x")
    assert res["render_status"] == "rendered"
