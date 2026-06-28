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
    
    # Estimate sequence label length (e.g. (10/10) is 7 chars)
    est_seq_len = 8
    
    # Determine maximum chunk size per segment
    first_segment_reserved = est_seq_len + len(caveat_text) + 15
    other_segments_reserved = est_seq_len + 55
    
    # Pre-split the text based on available space
    chunks = []
    current_idx = 0
    while current_idx < len(text):
        reserved = first_segment_reserved if len(chunks) == 0 else other_segments_reserved
        available_len = max_length - reserved
        if available_len <= 10:
            available_len = max_length - est_seq_len - 5
            
        chunk = text[current_idx:current_idx + available_len]
        if not chunk:
            break
        chunks.append(chunk.strip())
        current_idx += len(chunk)
        
    segments = []
    total_count = len(chunks)
    
    for idx, chunk in enumerate(chunks):
        seg_num = idx + 1
        sequence_label = f"({seg_num}/{total_count})"
        
        # Build segment text safely
        seg_body = f"{sequence_label} {chunk}"
        
        # If it is the first segment, or if we want to preserve caveats
        if idx == 0 and caveat_text:
            seg_body += f"\n\n[Warning: {caveat_text}]"
        else:
            seg_body += "\n\n[Unverified Source: Verification Required]"
            
        # Enforce max length constraint verification
        if len(seg_body) > max_length:
            seg_body = seg_body[:max_length - 4] + "..."
            
        # Deterministic payload hashing for segment
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
