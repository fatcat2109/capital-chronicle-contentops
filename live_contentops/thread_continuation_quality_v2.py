"""V6 Thread Continuation Quality.

Analyzes platform thread segments for truncation, splits, and compliance boundaries.
"""
from __future__ import annotations

import re
from typing import Any


def check_mid_word_splits(segments: list[dict[str, Any]], original_text: str) -> bool:
    """Detects word boundaries split mid-word (e.g. 'macroeconomic a' and 'djustments')."""
    if not original_text:
        return False
    chunks = []
    for s in segments:
        text = s.get("segment_text", "")
        # Remove sequence label prefix
        label = s.get("sequence_label", "")
        if label and text.startswith(label):
            text = text[len(label):].lstrip()
        # Remove footer suffix
        for footer_marker in ["\n\n[Warning:", "\n\n[Unverified Source:"]:
            idx = text.find(footer_marker)
            if idx != -1:
                text = text[:idx]
        chunks.append(text.strip())
        
    for i in range(len(chunks) - 1):
        c1 = chunks[i]
        c2 = chunks[i + 1]
        if c1 and c2:
            words_c1 = re.findall(r"\b\w+\b", c1)
            words_c2 = re.findall(r"\b\w+\b", c2)
            if words_c1 and words_c2:
                last_word = words_c1[-1]
                first_word = words_c2[0]
                joined = last_word + first_word
                if re.search(rf"\b{joined}\b", original_text, re.IGNORECASE):
                    return True
    return False


def inspect_thread_continuation(
    platform_variants: dict[str, Any],
    max_limits: dict[str, int],
    original_text: str = ""
) -> dict[str, Any]:
    """Inspects thread continuation segments across variants."""
    blockers = []
    details = {}
    
    for fam, var in platform_variants.items():
        max_len = max_limits.get(fam, 100000)
        var_blockers = []
        
        segments = var.get("segments", [])
        segment_texts = [s.get("segment_text", "") for s in segments]
        joined_segments = "\n\n---\n\n".join(segment_texts)
        
        # Check if variant_text drops later segments (when segments exist)
        if len(segments) > 1 and var.get("variant_text") != joined_segments:
            # Allow full text without segment wrappers, but it must contain the content
            # If it's shorter than joined chunks, it drops content
            if len(var.get("variant_text", "")) < sum(len(s.get("segment_text", "")) for s in segments) * 0.8:
                var_blockers.append("variant_text_drops_later_segments")
                
        # Check bypass or spam framing
        for word in ["bypass", "spam", "autonomous", "reply", "dm", "direct message", "engagement bait"]:
            if word in var.get("variant_text", "").lower():
                var_blockers.append("continuation_bypass_or_spam_framing_detected")
                
        for s in segments:
            # Check segment hash
            h = s.get("segment_hash")
            if not h or h == "stub_hash_value":
                var_blockers.append("stub_segment_hash_detected")
            elif not isinstance(h, str) or not re.match(r"^[0-9a-f]{64}$", h):
                var_blockers.append("invalid_segment_hash_format")
                
            # Check length limits
            if len(s.get("segment_text", "")) > max_len:
                var_blockers.append("segment_length_limit_exceeded")
                
            # Check truncation markers
            if s.get("segment_text", "").endswith("..."):
                var_blockers.append("segment_truncation_detected")
                
            # Check caveats/disclosure present in threaded flow
            has_discl = any("disclosure" in text.lower() or "recommendation" in text.lower() for text in segment_texts)
            has_limit = any("limit" in text.lower() or "uncertain" in text.lower() for text in segment_texts)
            if not has_discl or not has_limit:
                var_blockers.append("caveats_missing_from_thread_flow")
                
        # Check mid-word segment split
        if check_mid_word_splits(segments, original_text):
            var_blockers.append("mid_word_segment_split_detected")
            
        if var_blockers:
            blockers.extend(var_blockers)
            details[fam] = sorted(list(set(var_blockers)))
            
    return {
        "is_valid": len(blockers) == 0,
        "blockers": sorted(list(set(blockers))),
        "details": details
    }
