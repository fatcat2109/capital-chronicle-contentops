import json

from live_contentops.public_candidate_preflight_v6 import (
    FED_FUNDS_FAMILY,
    OIL_FAMILY,
    build_current_candidate_gate,
    build_pre_public_evidence,
    detect_content_families,
    triage_schedule_slots,
)


def _oil_article() -> dict:
    body = " ".join(
        [
            "WTI crude oil volatility and recession risk remain the source-backed focus for this educational article.",
            "FRED DCOILWTICO and EIA petroleum data support the chart discussion without giving investment advice.",
        ]
        * 80
    )
    return {
        "packet_id": "article_oil_new_slug",
        "source_context_packet": {
            "operator_idea": "Oil and yields policy transmission",
            "editorial_angle": "Separate current energy-price evidence from policy pass-through.",
        },
        "canonical_article_draft": {
            "title": "Oil Volatility Is Rising; Recession Risk Needs a Cleaner Evidence Map",
            "subtitle": "A source-led WTI briefing",
            "slug_candidate": "oil-volatility-recession-risk-evidence-map",
            "dek": "WTI context for a bounded recession-risk dashboard.",
            "meta_description": "Capital Chronicle maps current WTI oil volatility, source limits, and recession-risk channels.",
            "intro": body,
            "sections": [{"title": f"Section {idx}", "body": body} for idx in range(1, 6)],
            "conclusion": body,
            "source_trail": [
                {"label": "FRED DCOILWTICO", "claim_supported": "WTI price context."},
                {"label": "EIA", "claim_supported": "Petroleum source context."},
                {"label": "Federal Reserve", "claim_supported": "Policy context."},
            ],
            "citations": ["https://fred.stlouisfed.org/series/DCOILWTICO"],
            "chart_callouts": ["[CHART: WTI crude oil price and volatility]"],
            "media_callouts": ["[IMAGE: EIA Strait of Hormuz oil context]"],
            "visual_slots": [
                {
                    "asset_id": "primary",
                    "editorial_purpose": "WTI setup",
                    "data_requirement": "FRED WTI data",
                    "caption_guidance": "Name WTI and FRED",
                    "source_requirement": "FRED/EIA",
                },
                {
                    "asset_id": "recent_price",
                    "editorial_purpose": "Recent WTI path",
                    "data_requirement": "FRED WTI data",
                    "caption_guidance": "Name recent WTI path",
                    "source_requirement": "FRED/EIA",
                },
            ],
        },
    }


def _variant() -> dict:
    paragraph = " ".join(["Capital Chronicle reviews WTI oil volatility with source-led context."] * 40)
    return {
        "platform_variant_packet_id": "variant_oil",
        "image_path": "docs/automation/V6_MEDIA_SYSTEM/downloads/wti_current_volatility_context_abc.png",
        "public_image_url": None,
        "variants": {
            "substack": paragraph,
            "linkedin": paragraph,
            "facebook": paragraph,
            "discord": paragraph,
            "telegram": paragraph,
            "instagram_caption": paragraph,
        },
        "variant_threads": {"x": [paragraph[:200]], "threads": [paragraph[:400]]},
        "media_manifest": {
            "news_image_path": "docs/automation/V6_MEDIA_SYSTEM/downloads/wti_current_volatility_context_abc.png",
            "selected_media_by_platform": {
                "telegram": "docs/automation/V6_MEDIA_SYSTEM/downloads/wti_current_volatility_context_abc.png"
            },
            "media_assets": [
                {
                    "asset_id": "primary",
                    "local_path": "docs/automation/V6_MEDIA_SYSTEM/downloads/wti_current_volatility_context_abc.png",
                    "canonical_source_label": "FRED series DCOILWTICO; underlying source U.S. Energy Information Administration",
                    "visual_metric": "oil_volatility wti crude oil current price realized volatility",
                }
            ],
        },
    }


def test_detect_content_families_recognizes_incident_family():
    assert OIL_FAMILY in detect_content_families("Crude awakening WTI oil volatility")
    assert FED_FUNDS_FAMILY in detect_content_families("Effective fed funds rate: 3.63%")


def test_current_candidate_gate_blocks_oil_family_even_with_new_slug():
    ledger = [
        {
            "record_type": "incident_duplicate_freeze",
            "platform": "telegram",
            "canonical_url": "https://capitalchronicle.substack.com/p/crude-awakening-how-spiking-oil-volatility-05f",
            "topic_hint": "Crude awakening how spiking oil volatility",
            "media_hint": "WTI crude oil chart",
        }
    ]

    gate = build_current_candidate_gate(
        article_packet=_oil_article(),
        variant_packet=_variant(),
        ledger_rows=ledger,
        incident_evidence={},
    )

    assert gate["status"] == "BLOCKED"
    assert f"duplicate_article_family:{OIL_FAMILY}" in gate["blockers"]
    assert f"duplicate_media_family:{OIL_FAMILY}" in gate["blockers"]
    assert gate["telegram_payload_hash"]
    assert set(gate["per_platform_payload_hash"]) >= {"substack", "telegram", "discord"}


def test_schedule_triage_selects_fed_funds_and_skips_oil():
    schedule = {
        "schedule_date": "2026-07-08",
        "slots": [
            {
                "slot_index": 1,
                "readiness": "READY_FOR_PIPELINE",
                "topic": "Oil and yields stop moving together",
                "angle": "Energy-price policy pass-through",
            },
            {
                "slot_index": 6,
                "readiness": "READY_FOR_PIPELINE",
                "topic": "Effective fed funds rate: 3.63% July 7th vs 3.63% July 6th",
                "angle": "Frame the policy signal against rates.",
            },
        ],
    }

    triage = triage_schedule_slots(schedule, [])

    assert triage["selection_status"] == "SELECTED_REQUIRES_DRY_RUN_GATES"
    assert triage["selected_fresh_slot"]["slot_index"] == 6
    assert triage["evaluated_slots"][0]["status"] == "BLOCKED"


def test_build_pre_public_evidence_stays_blocked_until_fresh_rehearsal_ready(tmp_path, monkeypatch):
    article = tmp_path / "article.json"
    variant = tmp_path / "variant.json"
    schedule = tmp_path / "schedule.json"
    ledger = tmp_path / "ledger.jsonl"
    dry_run = tmp_path / "dry_run.json"
    incident = tmp_path / "incident.json"
    fresh = tmp_path / "fresh.json"
    article.write_text(json.dumps(_oil_article()), encoding="utf-8")
    variant.write_text(json.dumps(_variant()), encoding="utf-8")
    schedule.write_text(
        json.dumps(
            {
                "schedule_date": "2026-07-08",
                "slots": [
                    {
                        "slot_index": 6,
                        "readiness": "READY_FOR_PIPELINE",
                        "topic": "Effective fed funds rate: 3.63% July 7th vs 3.63% July 6th",
                        "angle": "Frame the policy signal against rates.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    ledger.write_text(
        json.dumps(
            {
                "record_type": "incident_duplicate_freeze",
                "platform": "telegram",
                "topic_hint": "Crude awakening how spiking oil volatility",
                "media_hint": "WTI crude oil chart",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    dry_run.write_text(json.dumps({"pipeline_result": {"pipeline_status": "LIVE_READY_REQUIRES_OPERATOR_GO"}}), encoding="utf-8")
    incident.write_text(json.dumps({}), encoding="utf-8")
    fresh.write_text(json.dumps({"pipeline_result": {"pipeline_status": "REHEARSAL_BLOCKED"}}), encoding="utf-8")
    monkeypatch.setattr("live_contentops.public_candidate_preflight_v6.inspect_python_runner_processes", lambda: {"matching_python_runner_count": 0, "process_ids": []})
    monkeypatch.setattr("live_contentops.public_candidate_preflight_v6.repo_state", lambda: {"head": "abc", "origin_master": "abc", "status_short": ""})

    packet = build_pre_public_evidence(
        article_packet_path=article,
        variant_packet_path=variant,
        schedule_path=schedule,
        ledger_path=ledger,
        dry_run_evidence_path=dry_run,
        incident_evidence_path=incident,
        fresh_rehearsal_evidence_path=fresh,
    )

    assert packet["pre_public_gate_status"] == "BLOCKED_PRE_PUBLIC_GATE"
    assert "current_rehearsal_candidate_not_public_safe" in packet["blockers"]
    assert "fresh_non_duplicate_slot_dry_run_not_live_ready:REHEARSAL_BLOCKED" in packet["blockers"]
