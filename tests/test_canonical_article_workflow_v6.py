from live_contentops import canonical_article_workflow_v6 as article_workflow

def test_article_creation_is_review_only_by_default():
    grounding = {
        "research_packet_id": "res_123",
        "source_refs": ["valid_ref"]
    }
    art = article_workflow.create_canonical_article(
        research_packet=grounding,
        title="Valid Title",
        subtitle="Valid Subtitle",
        body_markdown="This is valid historical treasury yield research text.",
        citations=["valid_ref"],
        limitations="This has yield analysis parameters that are limited and uncertain.",
        disclosure="No financial recommendations."
    )
    assert art["draft_status"] == "draft_completed"
    assert art["human_review_required"] is True

def test_missing_limitations_section_blocks():
    grounding = {
        "research_packet_id": "res_123",
        "source_refs": ["valid_ref"]
    }
    art = article_workflow.create_canonical_article(
        research_packet=grounding,
        title="Valid Title",
        subtitle="Valid Subtitle",
        body_markdown="This is valid historical treasury yield research text.",
        citations=["valid_ref"],
        limitations="", # empty limitations
        disclosure="No financial recommendations."
    )
    assert art["draft_status"] == "review_only"
    assert "limitations_section_required" in art["blockers"]

def test_fake_citations_are_rejected():
    grounding = {
        "research_packet_id": "res_123",
        "source_refs": ["valid_ref"]
    }
    art = article_workflow.create_canonical_article(
        research_packet=grounding,
        title="Valid Title",
        subtitle="Valid Subtitle",
        body_markdown="This is valid historical treasury yield research text.",
        citations=["fake_ref_id"], # not in grounding
        limitations="This has yield analysis parameters that are limited and uncertain.",
        disclosure="No financial recommendations."
    )
    assert art["draft_status"] == "review_only"
    assert "invalid_citation_reference:fake_ref_id" in art["blockers"]

def test_financial_advice_phrasing_is_blocked():
    grounding = {
        "research_packet_id": "res_123",
        "source_refs": ["valid_ref"]
    }
    art = article_workflow.create_canonical_article(
        research_packet=grounding,
        title="Valid Title",
        subtitle="Valid Subtitle",
        body_markdown="You should buy yield-curve options for guaranteed profit",
        citations=["valid_ref"],
        limitations="This has yield analysis parameters that are limited and uncertain.",
        disclosure="No financial recommendations."
    )
    assert art["draft_status"] == "review_only"
    assert "financial_advice_detected" in art["blockers"]
