"""V6 Platform Thread and Comment Continuation.

Implements safe, deterministic segmentation for long-form variant content.
"""
from __future__ import annotations

import hashlib
from typing import Any


def segment_text_by_limits(
    text: str,
    max_length: int,
    platform_family: str,
    required_caveats: list[str] | None = None
) -> list[dict[str, Any]]:
    """Segments body text into ordered review-only parts with sequence metadata.
    
    Adheres strictly to V6 safety invariants (no autonomous posts, no bypass language).
    """
    caveats = required_caveats or []
    caveat_text = "\n".join(caveats) if caveats else ""
    
    # First pass to estimate the number of segments
    chunks = []
    current_idx = 0
    while current_idx < len(text):
        if len(chunks) == 0 and caveat_text:
            footer = f"\n\n[Warning: {caveat_text}]"
        else:
            footer = "\n\n[Unverified Source: Verification Required]"
            
        reserved = 10 + len(footer)
        available = max_length - reserved
        if available <= 0:
            available = 1
            
        # Smart boundary split to avoid mid-word splits
        candidate = text[current_idx:current_idx + available]
        if len(candidate) < len(text) - current_idx:
            last_space = -1
            for idx_c, char in enumerate(reversed(candidate)):
                if char.isspace() or char in [".", ",", ";", "!", "?", "-"]:
                    last_space = len(candidate) - 1 - idx_c
                    break
            if last_space != -1 and last_space > available // 2:
                available = last_space + 1
                
        chunk = text[current_idx:current_idx + available]
        if not chunk:
            break
        chunks.append(chunk.strip())
        current_idx += len(chunk)
        
    total_count = len(chunks)
    if total_count == 0:
        total_count = 1
        
    # Second pass with exact sequence label length
    chunks = []
    current_idx = 0
    while current_idx < len(text):
        seg_num = len(chunks) + 1
        sequence_label = f"({seg_num}/{total_count})"
        if len(chunks) == 0 and caveat_text:
            footer = f"\n\n[Warning: {caveat_text}]"
        else:
            footer = "\n\n[Unverified Source: Verification Required]"
            
        header = f"{sequence_label} "
        reserved = len(header) + len(footer)
        available = max_length - reserved
        
        if available <= 0:
            available = 1
            
        # Smart boundary split to avoid mid-word splits
        candidate = text[current_idx:current_idx + available]
        if len(candidate) < len(text) - current_idx:
            last_space = -1
            for idx_c, char in enumerate(reversed(candidate)):
                if char.isspace() or char in [".", ",", ";", "!", "?", "-"]:
                    last_space = len(candidate) - 1 - idx_c
                    break
            if last_space != -1 and last_space > available // 2:
                available = last_space + 1
                
        chunk = text[current_idx:current_idx + available]
        if not chunk:
            break
        chunks.append(chunk.strip())
        current_idx += len(chunk)
        
    segments = []
    total_count = len(chunks)
    
    for idx, chunk in enumerate(chunks):
        seg_num = idx + 1
        sequence_label = f"({seg_num}/{total_count})"
        header = f"{sequence_label} "
        
        if idx == 0 and caveat_text:
            footer = f"\n\n[Warning: {caveat_text}]"
        else:
            footer = "\n\n[Unverified Source: Verification Required]"
            
        seg_body = f"{header}{chunk}{footer}"
        
        # Calculate SHA-256 hash deterministically
        h = hashlib.sha256(seg_body.encode("utf-8")).hexdigest()
        
        segments.append({
            "segment_index": seg_num,
            "total_segments": total_count,
            "sequence_label": sequence_label,
            "segment_text": seg_body,
            "segment_hash": h,
            "review_only": True,
            "public_postable": False,
            "dispatch_allowed_now": False
        })
        
    return segments
