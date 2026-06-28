"""V6 AI Provider Gate.

Manages LLM provider execution modes and credential safety checks under the V6 Operating Profile.
"""
from __future__ import annotations

import os
from typing import Any

PROVIDER_MODES = [
    "disabled",
    "dry_run_stub",
    "manual_external_llm",
    "nine_router_live_deferred",
    "vertex_fallback_deferred"
]

DEFAULT_MODE = "dry_run_stub"


def get_provider_mode() -> str:
    """Returns the current provider execution mode."""
    return os.environ.get("V6_AI_PROVIDER_MODE", DEFAULT_MODE)


def inspect_provider_credentials() -> dict[str, bool]:
    """Inspects credentials by presence only.
    
    Never prints secret values, lengths, prefixes, suffixes, or digests.
    """
    keys = [
        "OPENAI_API_KEY",
        "VERTEX_CREDENTIALS",
        "NINE_ROUTER_API_KEY",
        "ANTHROPIC_API_KEY"
    ]
    return {k: (k in os.environ) for k in keys}


def call_llm_deferred(prompt_family: str, prompt_text: str, schema: dict[str, Any] | None = None) -> dict[str, Any]:
    """Defers LLM call or handles it via dry-run stubs."""
    mode = get_provider_mode()
    
    if mode == "disabled":
        raise ValueError("AI provider is globally disabled.")
        
    if mode == "dry_run_stub":
        # Returns simple schema-wrapped dry run stubs for validation
        stub_res = {
            "result_status": "review_only_stub",
            "prompt_family": prompt_family,
            "prompt_text_length": len(prompt_text),
            "stub_response": f"Dry run stub response for prompt family: {prompt_family}"
        }
        if schema:
            # Simple dummy instantiation matching requested keys in schema if possible
            for key, val_type in schema.get("properties", {}).items():
                if val_type.get("type") == "string":
                    stub_res[key] = f"Stub string for {key}"
                elif val_type.get("type") == "boolean":
                    stub_res[key] = False
                elif val_type.get("type") == "array":
                    stub_res[key] = []
                elif val_type.get("type") == "number" or val_type.get("type") == "integer":
                    stub_res[key] = 0
                else:
                    stub_res[key] = None
        return stub_res
        
    # Deferred modes return a placeholder showing they are deferred
    return {
        "result_status": f"deferred_via_{mode}",
        "prompt_family": prompt_family,
        "deferred": True
    }
