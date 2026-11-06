"""Event publication uses admitted source bytes without a second rights record."""
from copy import deepcopy
from hashlib import sha256

import pytest

from live_contentops.event_article_guard_v1 import PublicOutputError, check_source_bound_event_article
from tests.test_event_article_guard_v1 import packet


def admitted():
    article, _ = packet()
    source_text = "Official initial payroll change: +29,000 jobs."
    copy = "Payrolls changed by +29,000."
    number = "+29,000"
    start = source_text.index(number)
    ref = f"SOURCE_1:{start}:{start + len(number)}"
    offset = copy.index(number)
    article["copy"]["scenarios"] = copy
    article["numeric_bindings"] = [{"copy_path": "copy.scenarios", "start": offset,
        "end": offset + len(number), "evidence_ref": ref}]
    source = {"source_id": "SOURCE_1", "canonical_content_text": source_text,
        "canonical_content_sha256": sha256(source_text.encode()).hexdigest(),
        "url": "https://www.bls.gov/news.release/archives/empsit_10022026.htm",
        "publisher": "BLS", "published_at_utc": "2026-10-02T12:30:00Z",
        "source_authority_class": "official_public_primary_source",
        "source_reuse_constraints": {"scope": "BLS_AGENCY_AUTHORED_PUBLIC_DOMAIN_TEXT_PREVIEW_BACKGROUND",
            "authority_ref": "JIM_DECISION_41"}}
    return article, [source]


def test_publisher_consumes_official_number_from_existing_admitted_packet():
    article, sources = admitted()
    result = check_source_bound_event_article(article, sources)
    assert result["status"] == "PASS" and result["numeric_bindings"] == 1


@pytest.mark.parametrize("fault", ["hash", "clock", "rights", "private", "span"])
def test_changed_or_unadmitted_source_cannot_supply_event_numbers(fault):
    article, sources = admitted()
    source = sources[0]
    if fault == "hash":
        source["canonical_content_text"] += " Changed"
    elif fault == "clock":
        source["known_at_utc"] = "2026-11-07T00:00:00Z"
    elif fault == "rights":
        source["source_authority_class"] = "unlicensed_vendor"
    elif fault == "private":
        source["public_claim_allowed"] = False
    else:
        article["numeric_bindings"][0]["evidence_ref"] = "SOURCE_1:0:999999"
    with pytest.raises(PublicOutputError):
        check_source_bound_event_article(article, sources)


def test_model_threshold_uses_label_and_not_vendor_table_permission():
    article, sources = admitted()
    source = sources[0]
    source["source_authority_class"] = "governed_capital_chronicle_report_only"
    source["source_reuse_constraints"] = {"scope": "CAPITAL_CHRONICLE_OWN_REPORT_PUBLIC_EXCERPTS",
        "authority_ref": "JIM_DECISION_89"}
    with pytest.raises(PublicOutputError, match="MODEL_ESTIMATE_LABEL_REQUIRED"):
        check_source_bound_event_article(article, sources)
