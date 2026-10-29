"""Map an admitted, journal-free Provider result into existing retained research.

No acquisition, Provider mutation, model, scheduler or publication runs here. Original
fact rights and clocks remain attached; numeric facts do not license raw expression.
"""
from __future__ import annotations

import json
import os
from collections import defaultdict
from hashlib import sha256
from pathlib import Path

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of, _time

CONFIG = Path(__file__).resolve().parents[1] / "config/contentops_official_release_intake_v1.json"


def attach_official_release_facts(research, *, config=None):
    settings = config if config is not None else json.loads(CONFIG.read_bytes())
    if not settings.get("enabled"):
        return research
    path = (Path(settings["result_path"]) if settings.get("result_path") else
        Path(os.environ.get("LOCALAPPDATA",Path.home()/"AppData/Local"))/"CapitalChronicle/ProviderReadOnly/w1082-contentops/results/release-components.json")
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != settings["result_file_sha256"]:
        raise ValueError("OFFICIAL_RELEASE_CONSUMER_RESULT_CHANGED")
    value = json.loads(raw)
    projection, lineage = value["projection"], value["lineage"]
    if (sha256_of({k:v for k,v in value.items() if k != "content_sha256"}) != value["content_sha256"]
            or lineage["provider"] != settings["provider"]
            or projection["content_sha256"] != settings["projection"]
            or lineage["projection"]["content_sha256"] != settings["projection"]):
        raise ValueError("EXACT_OFFICIAL_RELEASE_LINEAGE_REQUIRED")
    groups = defaultdict(list)
    for fact in projection["facts"]:
        if fact["rights"]["state"] not in {"PUBLIC_SAFE_FACT","PUBLIC_SAFE_FACT_CONDITIONAL"}:
            raise ValueError("NONPUBLIC_OFFICIAL_FACT_CANNOT_ENTER_CANDIDATES")
        if fact["rights"]["purpose"] != "contentops_factual_source_intake":
            raise ValueError("OFFICIAL_FACT_INTAKE_PURPOSE_REQUIRED")
        groups[fact["release_identity"]].append(fact)
    existing = {r.get("document",{}).get("provider_projection_sha256") for r in research.records.values()}
    if projection["content_sha256"] in existing:
        return research
    for release, facts in groups.items():
        first = facts[0]
        source_known = max((f["clocks"]["row_known_at_utc"] for f in facts),key=_time)
        known = max((source_known,settings["consumer_observed_at_utc"]),key=_time)
        publication = first["clocks"]["publication"]["utc"]
        identity = "official-release-" + sha256_of([lineage["provider"],projection["content_sha256"],release])
        source_hash = sha256_of(facts)
        text = (first["publisher"] + "; retained official release " + release + ". "
            + " ".join(f["metric"]["label"]+": "+str(f["metric"]["value"])+" "+f["metric"]["unit"]
                +"; basis "+str(f["metric"].get("basis","native published basis"))+"." for f in facts))
        text += " Reference period: "+first["reference_period"]+". Retained vintage; not a new release at intake."
        rights = {"scope":"GOVERNED_PUBLIC_NUMERIC_FACTS_ONLY_EXCLUDES_RAW_TEXT_IMAGES",
            "authority":"L1_BATCH11_CONTENTOPS_FACTUAL_INTAKE_EXISTING_PUBLIC_FACT_PURPOSE",
            "MODEL_INPUT_ALLOWED":True,"LLM_INPUT_ALLOWED":True,"INTERNAL_ANALYSIS_ALLOWED":True,
            "source_capture_sha256":source_hash,"content_sha256":sha256(text.encode()).hexdigest(),
            "original_fact_rights":[f["rights"] for f in facts],
            "conditions":[c for f in facts for c in f["rights"]["conditions"]],
            "free_source_notices":[f["rights"]["free_source_notice"] for f in facts if f["rights"].get("free_source_notice")],
            "raw_text_images":"NOT_EXPORTED_OR_LICENSED_BY_THIS_PROJECTION",
            "external_licence_granted":False,"publication":"SEPARATE_CONTENTOPS_OWNER_DECISION"}
        doc = {"source_url":first["official_url"],"publisher":first["publisher"],
            "published_at_utc":publication,"source_adapter_family":"official_macro",
            "source_authority_class":"official_public_primary_source","canonical_content_text":text,
            "canonical_content_sha256":sha256(text.encode()).hexdigest(),"raw_sha256":source_hash,
            "source_reuse_constraints":rights,"public_claim_allowed":True,"content_truncated":False,
            "governed_official_facts":facts,"provider_lineage":{k:lineage[k] for k in ("provider","source_manifest","integration_descriptor")},
            "provider_projection_sha256":projection["content_sha256"],
            "missing_release_requests":projection["missing"],"missing_request_context":value.get("missing_request_context"),
            "projection_limits":projection["limits"],"consensus":None,"historical_first_print_pit":False}
        research.records[identity] = {"headline_id":identity,"headline_text":text,"text_sha256":sha256(text.encode()).hexdigest(),
            "source_identity":first["publisher"],"source_platform":"GOVERNED_OFFICIAL_RELEASE_FACTS",
            "source_account":first["publisher"],"source_url":first["official_url"],"official_source_urls":[first["official_url"]],
            "source_timestamp_utc":publication,"headline_timestamp":publication,"known_at_utc":known,
            "retrieval_time_utc":settings["consumer_observed_at_utc"],"revision_at_utc":known,
            "revision_clock_basis":"MAX_PROVIDER_EDITION_AND_ACTUAL_CONSUMER_INTAKE_NOT_OFFICIAL_REVISION",
            "source_edition_known_at_utc":source_known,
            "source_capture_sha256":source_hash,"rights_evidence_sha256":sha256_of([f["rights"] for f in facts]),
            "source_permissions":rights,"source_permission_record_sha256":sha256_of(rights),
            "rights_state":"GOVERNED_PUBLIC_NUMERIC_FACTS_WITH_ORIGINAL_CONDITIONS",
            "candidate_catalyst_tags":[first["family"],"official_release","retained_prior_context"],
            "originality":"GOVERNED_OFFICIAL_FACT_INTAKE","correction_of":None,"document":doc,"source_chart":None,
            "permitted_source_text":text,"supporting_headline_ids":[],
            "research_metadata":{"family":"FX_RATES","context_kind":"DATED_OFFICIAL_RELEASE_CONTEXT",
                "reference_period":first["reference_period"],"fact_ids":[f["fact_id"] for f in facts],
                "current_market_state_verified":False,"new_release_at_intake":False}}
    research.gaps.extend({"state":"GOVERNED_OFFICIAL_RELEASE_"+kind.upper(),"record":row}
        for kind in ("restricted","missing","missing_metrics","unavailable") for row in projection[kind])
    research.revision = sha256_of([research.revision,projection["content_sha256"]])
    return research
