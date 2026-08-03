"""Fast One-Cycle Automation Wrapper V0 for ContentOps.

Orchestrates:
1. Intake validation & rendering
2. Operator decision & public override evaluation
3. Duplicate checks & preflight
4. Public dispatch if safe (Discord webhook)
5. Evidence persistence
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from live_contentops.cc_artifact_packet_intake_v0 import intake_packet, load_packet
from live_contentops.cc_artifact_packet_operator_decision_v1 import (
    load_existing_intake_artifacts,
    write_operator_decision_outputs,
)
from live_contentops.live_entrypoint_registry_v1 import (
    LEGACY_AUTOMATION_QUARANTINED,
    quarantine,
)
from live_contentops.public_permissive_supervised_mode_v0 import (
    PUBLIC_MODE_CANDIDATE_COMMENTARY,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKET = ROOT / "tests" / "fixtures" / "cc_artifact_packet_v0" / "sample_internal_draft_packet_v0.json"
DEFAULT_INTAKE_DIR = ROOT / "docs" / "automation" / "CC_ARTIFACT_PACKET_INTAKE_ADAPTER_V0"
DEFAULT_DECISION_DIR = ROOT / "docs" / "automation" / "CC_ARTIFACT_PACKET_OPERATOR_DECISION_V1"
DEFAULT_PUBLIC_PREVIEW_DIR = ROOT / "docs" / "automation" / "PUBLIC_PERMISSIVE_SUPERVISED_MODE_V0"
OUTPUT_DIR = ROOT / "docs" / "automation" / "FAST_ONE_CYCLE_AUTOMATION_V0"


def run_fast_one_cycle(
    packet_path: str | Path = DEFAULT_PACKET,
    intake_dir: str | Path = DEFAULT_INTAKE_DIR,
    decision_dir: str | Path = DEFAULT_DECISION_DIR,
    public_preview_dir: str | Path = DEFAULT_PUBLIC_PREVIEW_DIR,
    output_dir: str | Path = OUTPUT_DIR,
    dispatch_live: bool = False,
) -> dict[str, Any]:
    quarantine(
        "contentops.legacy_fast_one_cycle.v0",
        LEGACY_AUTOMATION_QUARANTINED,
        "Fast one-cycle automation is legacy; use ContentOpsProductionOrchestrator.",
    )
    packet_path = Path(packet_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Intake
    intake_summary = intake_packet(
        packet_path=packet_path,
        output_dir=intake_dir,
        dry_run=True,
    )
    
    # 2. Operator Decision (with supervised public override)
    packet = load_packet(packet_path)
    artifacts = load_existing_intake_artifacts(intake_dir)
    
    decision_outputs = write_operator_decision_outputs(
        packet=packet,
        artifacts=artifacts,
        output_dir=decision_dir,
        operator_go=True,
        operator_public_override=True,
        public_mode=PUBLIC_MODE_CANDIDATE_COMMENTARY,
        public_preview_output_dir=public_preview_dir,
        packet_path=packet_path,
        intake_dir=intake_dir,
    )
    
    # 3. Load generated preview and payloads
    article_path = Path(public_preview_dir) / "candidate_public_preview_v0.md"
    payloads_path = Path(public_preview_dir) / "candidate_platform_payloads_v0.json"
    evidence_path = Path(public_preview_dir) / "public_permissive_evidence_v0.json"
    
    article_content = article_path.read_text(encoding="utf-8") if article_path.exists() else ""
    payloads = json.loads(payloads_path.read_text(encoding="utf-8")) if payloads_path.exists() else {}
    public_evidence = json.loads(evidence_path.read_text(encoding="utf-8")) if evidence_path.exists() else {}
    
    # Write fast run files
    (output_dir / "article.md").write_text(article_content, encoding="utf-8")
    with open(output_dir / "platform_payloads.json", "w", encoding="utf-8") as f:
        json.dump(payloads, f, indent=2, sort_keys=True)
        
    # 4. Dispatch (if safe/allowed)
    dispatch_result = {"status": "NOT_ATTEMPTED", "platform": "discord"}
    is_safe = public_evidence.get("public_ready", False)
    
    # Prefer Discord if configured safely.
    discord_webhook = (
        os.environ.get("DISCORD_ANNOUNCEMENTS_WEBHOOK_URL")
        or os.environ.get("DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK")
        or ""
    )
    
    if dispatch_live and is_safe:
        discord_bundle = payloads.get("payloads", {}).get("discord", {})
        discord_payload = discord_bundle.get("text") or article_content
        # Perform the actual dispatch
        dispatch_result = execute_discord_post(
            message=discord_payload,
            webhook_url=discord_webhook if discord_webhook else None,
            dry_run=not bool(discord_webhook),
        )
        
    # Write dispatch results
    with open(output_dir / "dispatch_results.json", "w", encoding="utf-8") as f:
        json.dump(dispatch_result, f, indent=2, sort_keys=True)
        
    # 5. Create E2E run evidence
    run_evidence = {
        "task_label": "TASK_CONTENTOPS_FAST_ONE_CYCLE_AUTOMATION_V0",
        "timestamp": public_evidence.get("created_at") or "",
        "packet_id": packet.get("packet_id"),
        "topic": packet.get("topic"),
        "article_path": str(output_dir / "article.md"),
        "platform_payloads_path": str(output_dir / "platform_payloads.json"),
        "dispatch_results_path": str(output_dir / "dispatch_results.json"),
        "intake_status": intake_summary.get("classification"),
        "decision_status": decision_outputs.get("decision_packet", {}).get("classification"),
        "public_ready": is_safe,
        "dispatch_status": dispatch_result.get("status"),
        "dispatch_platform": dispatch_result.get("platform"),
        "dispatch_id": dispatch_result.get("id", None),
        "webhook_configured": bool(discord_webhook),
    }
    with open(output_dir / "run_evidence.json", "w", encoding="utf-8") as f:
        json.dump(run_evidence, f, indent=2, sort_keys=True)
        
    return {
        "run_evidence": run_evidence,
        "article_content": article_content,
        "payloads": payloads,
        "dispatch_result": dispatch_result,
    }
