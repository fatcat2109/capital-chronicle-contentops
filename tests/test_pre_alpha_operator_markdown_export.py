import pytest
from live_contentops import pre_alpha_operator_markdown_export

def test_markdown_export_safety_and_structure():
    md, is_safe = pre_alpha_operator_markdown_export.generate_markdown_export()

    # Markdown export generates text
    assert isinstance(md, str)
    assert len(md) > 100

    # Safety headers and markers
    assert "## Safety Header" in md
    assert "Operator final check required" in md
    assert "Not public-postable by default" in md
    assert "No platform API payload" in md

    # Check for required sections
    assert "## Run Summary" in md
    assert "## Ready for Operator Review" in md
    assert "## Blocked or Not Ready" in md
    assert "## Platform Manual Templates" in md
    assert "## Manual Publish Record Reminder" in md
    assert "## Manual Performance Record Reminder" in md
    assert "## Content Performance Review" in md
    assert "## Next Operator Actions" in md

    # Check forbidden claims
    assert "no inferred publication" in md.lower()
    assert "missing metrics remain missing/null" in md.lower()
    assert "no statistical significance" in md.lower()
    assert "never auto-post" in md.lower()

    # The default fixtures are expected to have some blocked items or ready items, 
    # but regardless the formatting strings should appear.
    assert "**Stage:**" in md or "None." in md
    assert "Copy/Paste Text Block" in md or "No ready items." in md

def test_markdown_deterministic():
    md1, s1 = pre_alpha_operator_markdown_export.generate_markdown_export()
    md2, s2 = pre_alpha_operator_markdown_export.generate_markdown_export()
    assert md1 == md2
    assert s1 == s2
