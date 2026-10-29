import json
from hashlib import sha256

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.contentops_official_release_intake_v1 import attach_official_release_facts
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.v1_simple_gemini_newsroom_v1 import _candidate_universe


def fixture(tmp_path):
    fact={"fact_id":"controlled-fact","release_identity":"BLS|CPI|2026-09|2026-10-14","family":"cpi",
        "publisher":"U.S. Bureau of Labor Statistics","official_url":"https://www.bls.gov/news.release/cpi.htm",
        "reference_period":"2026-09","metric":{"label":"CPI all items monthly change","value":0.6,
            "unit":"percent_change_mom","basis":"MONTH_ON_MONTH_SEASONALLY_ADJUSTED"},
        "clocks":{"row_known_at_utc":"2026-10-29T07:04:24Z","publication":{"utc":"2026-10-14T12:30:00Z"}},
        "rights":{"state":"PUBLIC_SAFE_FACT","purpose":"contentops_factual_source_intake",
            "conditions":["Attribute BLS and link official source"],"free_source_notice":None,"model_input":"NO_NEW_PERMISSION"},
        "revision":{"original_first_print_known_at":None},"historical_first_print_pit":False}
    projection={"content_sha256":"projection","facts":[fact],"limits":{"consensus":None},
        "restricted":[{"reason":"UNASSESSED_RIGHTS"}],"missing":[{"reference_period":"2026-10","actual":None}],
        "missing_metrics":[],"unavailable":[]}
    value={"projection":projection,"lineage":{"provider":"provider","projection":{"content_sha256":"projection"},
        "source_manifest":{"edition":"controlled-edition"},"integration_descriptor":"descriptor"},
        "missing_request_context":{"October actual":None}}
    value["content_sha256"]=sha256_of(value)
    path=tmp_path/"reader.json"
    path.write_text(json.dumps(value))
    config={"enabled":True,"result_path":str(path),"result_file_sha256":sha256(path.read_bytes()).hexdigest(),
        "provider":"provider","projection":"projection","consumer_observed_at_utc":"2026-10-30T00:00:00Z"}
    research=RetainedSourceResearch.__new__(RetainedSourceResearch)
    research.root=tmp_path
    research.revision="existing"
    research.records={}
    research.gaps=[]
    return research,config,value


def test_governed_fact_enters_existing_candidate_and_evidence_owner_with_original_rights_clocks(tmp_path):
    research,config,value=fixture(tmp_path)
    assert attach_official_release_facts(research,config=config) is research
    heads=research.headlines(cutoff_utc="2026-10-30T01:00:00Z")
    assert len(_candidate_universe({"headlines":heads},[]))==1
    assert research.headlines(cutoff_utc="2026-10-29T07:04:23Z")==[]
    assert research.headlines(cutoff_utc="2026-10-29T23:59:59Z")==[]  # Not yet known by this consumer.
    record=next(iter(research.records.values()))
    doc=record["document"]
    assert doc["governed_official_facts"]==value["projection"]["facts"]
    assert doc["missing_release_requests"][0]["actual"] is None
    assert doc["consensus"] is None and not doc["historical_first_print_pit"]
    assert record["source_timestamp_utc"]=="2026-10-14T12:30:00Z"
    assert record["known_at_utc"]=="2026-10-30T00:00:00Z"
    assert record["source_edition_known_at_utc"]=="2026-10-29T07:04:24Z"
    assert record["source_permissions"]["original_fact_rights"][0]["model_input"]=="NO_NEW_PERMISSION"
    assert len(research.gaps)==2 and not doc.get("publication_authority")
    frozen=research.frozen_snapshot()
    assert RetainedSourceResearch.from_frozen_snapshot(frozen).records==research.records
    assert attach_official_release_facts(research,config=config).frozen_snapshot()==frozen


def test_changed_file_or_provider_cannot_be_substituted(tmp_path):
    research,config,_=fixture(tmp_path)
    with pytest.raises(ValueError,match="LINEAGE"):
        attach_official_release_facts(research,config={**config,"provider":"other"})
    from pathlib import Path
    Path(config["result_path"]).write_text("{}")
    with pytest.raises(ValueError,match="RESULT_CHANGED"):
        attach_official_release_facts(research,config=config)
