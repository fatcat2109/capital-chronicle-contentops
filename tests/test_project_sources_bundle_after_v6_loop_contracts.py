"""Unit tests for the AFTER_V6_LOOP_CONTRACTS project sources upload bundle."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from live_contentops import generate_project_sources_bundle_after_v6_loop_contracts as generator

FORBIDDEN_KEYWORDS = [
    "discord.com/api/webhooks",
    "token_value",
    "cookie_value",
    "secret_key"
]

FINANCIAL_ADVICE_KEYWORDS = [
    "buy", "sell", "hold", "target price", "stop loss", "position size", "trade setup", "alpha call", "guaranteed return"
]


def test_bundle_generation_and_integrity(tmp_path, monkeypatch):
    # Run the generator inside a temp directory or target output
    monkeypatch.chdir(tmp_path)
    generator.main()

    out_dir = tmp_path / "docs/automation/V6_PROJECT_SOURCES_UPLOAD_BUNDLE_AFTER_V6_LOOP_CONTRACTS"
    assert out_dir.exists()

    required_files = [
        "CURRENT_STATE_SUMMARY_AFTER_V6_LOOP_CONTRACTS.md",
        "NEW_CHAT_CONTINUATION_AFTER_V6_LOOP_CONTRACTS.md",
        "PROJECT_SOURCE_EXPORT_AFTER_V6_LOOP_CONTRACTS.md",
        "PROJECT_SOURCES_REPLACEMENT_INDEX_AFTER_V6_LOOP_CONTRACTS.md",
        "PROJECT_SOURCES_DELETE_REPLACE_GUIDE_AFTER_V6_LOOP_CONTRACTS.md",
        "UPLOAD_BUNDLE_MANIFEST_AFTER_V6_LOOP_CONTRACTS.json",
        "BUNDLE_FILE_LIST_AFTER_V6_LOOP_CONTRACTS.txt",
        "OPERATOR_NEXT_ACTIONS_AFTER_V6_LOOP_CONTRACTS.md",
        "IMPLEMENTATION_REPORT_AFTER_V6_LOOP_CONTRACTS.md"
    ]

    for rf in required_files:
        assert (out_dir / rf).exists()

    # Verify manifest and BUNDLE_FILE_LIST contents match
    manifest_data = json.loads((out_dir / "UPLOAD_BUNDLE_MANIFEST_AFTER_V6_LOOP_CONTRACTS.json").read_text(encoding="utf-8"))
    assert manifest_data["schema_version"] == "6.0.0"
    assert manifest_data["accepted_baseline"] == "e2d1abc98eb7bbd04ae72ed9722798e84a6c8bd7"

    list_lines = (out_dir / "BUNDLE_FILE_LIST_AFTER_V6_LOOP_CONTRACTS.txt").read_text(encoding="utf-8").strip().splitlines()

    manifest_files = list(manifest_data["files"].keys())
    assert sorted(list_lines) == sorted(manifest_files)

    for item in list_lines:
        assert item.startswith("docs/automation/V6_PROJECT_SOURCES_UPLOAD_BUNDLE_AFTER_V6_LOOP_CONTRACTS/")

    # Scan generated files for leaks or forbidden content
    for rf in required_files:
        content = (out_dir / rf).read_text(encoding="utf-8")
        content_lower = content.lower()

        # Check for raw secrets / webhook URLs
        for key in FORBIDDEN_KEYWORDS:
            assert key not in content_lower

        # Check for financial advice
        for k in FINANCIAL_ADVICE_KEYWORDS:
            assert not re.search(rf"\b{re.escape(k)}\b", content_lower)

        # Check that no file claims live execution
        assert "live write" not in content_lower or "no live write" in content_lower or "no live writes" in content_lower
        assert "env read" not in content_lower or "no env read" in content_lower or "no env reads" in content_lower or "no environment" in content_lower
        assert "provider call" not in content_lower or "no provider call" in content_lower or "no provider calls" in content_lower or "no llm" in content_lower
        assert "network call" not in content_lower or "no network call" in content_lower or "no network calls" in content_lower
        assert "browser session" not in content_lower or "no browser session" in content_lower or "no browser sessions" in content_lower
        assert "scraping" not in content_lower or "no scraping" in content_lower or "no community scraping" in content_lower


def test_no_forbidden_behavior_in_bundle_generator():
    import subprocess
    attrs = dir(generator)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs

    forbidden_modules = [
        "requests", "httpx", "urllib", "openai", "anthropic", "google.genai",
        "vertex", "discord", "telegram", "tweepy", "selenium", "playwright",
        "bs4", "scrapy"
    ]
    code = f"""
import sys
import importlib
try:
    importlib.import_module("live_contentops.generate_project_sources_bundle_after_v6_loop_contracts")
except Exception as e:
    print(f"ImportError: {{e}}")
    sys.exit(1)
forbidden = {forbidden_modules}
found = [m for m in forbidden if m in sys.modules and sys.modules[m] is not None and m != "urllib"]
if found:
    print("FOUND_FORBIDDEN:" + ",".join(found))
    sys.exit(2)
sys.exit(0)
"""
    res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert res.returncode == 0, f"Forbidden imports found or import failed. Output: {res.stdout.strip()}. Stderr: {res.stderr.strip()}"
