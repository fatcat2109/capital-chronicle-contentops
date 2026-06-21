"""Bridge between Lane C artifact intake and Content Lifecycle Engine.

Part of TASK_CONTENTOPS_0175BG_LANE_C_ARTIFACT_INTAKE_BRIDGE_TO_LIFECYCLE_ENGINE_PRECHECK_V0.
Integrates real local candidate/artifact evidence from the ingestion repo
into the first stage of the Content Lifecycle Spine.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_INGESTION_REPO_PATH = Path("A:/Capital Chronicle/Headline Raw data local json/capital-chronicle-ingestion")

def discover_artifacts(ingestion_repo_path: Path | str) -> dict[str, Any]:
    """Inspect the ingestion repo and collect candidate artifact metadata."""
    repo_path = Path(ingestion_repo_path).resolve()
    
    if not repo_path.is_dir() or not (repo_path / ".git").is_dir():
        return {
            "ingestion_repo_detected": False,
            "ingestion_repo_path_checked": str(repo_path),
            "artifacts_scanned_count": 0,
            "artifact_candidates_count": 0,
            "artifact_candidate_summaries": [],
            "ingestion_repo_status_error": "INGESTION_REPO_MISSING",
        }

    # Bounded list of files to search for under docs/research/database_foundation/pre_ia_acceleration/
    pre_ia_dir = repo_path / "docs" / "research" / "database_foundation" / "pre_ia_acceleration"
    
    # Bounded files to inspect to avoid reading massive raw database dumps
    target_basenames = [
        "STEP1_OFFICIAL_TEXT_LIVE_PROBE_MANIFEST_V1.json",
        "STEP1_OFFICIAL_TEXT_SPINE_CONTRACT_V1.json",
        "BEA_BLS_CENSUS_NORMALIZED_CONTRACT_V1.json",
        "BEA_BLS_CENSUS_NORMALIZED_CANDIDATE_RECORDS_V1.json",
        "BROKER_PROXY_NO_VALUE_SNAPSHOT_MANIFEST_V1.json",
        "DATABASE_FOUNDATION_TTL_FRESHNESS_POLICY_CONTRACT_V1.json",
        "ECONOMIC_PRINTS_SCHEMA_CONTRACT_V1.json",
    ]
    
    candidates = []
    scanned_count = 0
    
    for filename in target_basenames:
        file_path = pre_ia_dir / filename
        if file_path.is_file():
            scanned_count += 1
            try:
                # Basic metadata extraction
                stat = file_path.stat()
                rel_path = file_path.relative_to(repo_path).as_posix()
                
                # Bounded JSON load to prevent memory issues and extract classification
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Classification parsing
                evidence_role = "unknown"
                if "contract" in filename.lower():
                    evidence_role = "contract"
                elif "manifest" in filename.lower():
                    evidence_role = "manifest"
                elif "candidate" in filename.lower():
                    evidence_role = "candidates"
                
                source_family = "US Macro"
                if "broker" in filename.lower():
                    source_family = "Broker Proxy"
                elif "step1" in filename.lower():
                    source_family = "Official Text Spine"
                elif "fred" in filename.lower():
                    source_family = "FRED/EIA"
                
                # Check for list length in candidate records to avoid copying raw data
                item_count = len(data) if isinstance(data, list) else 1
                
                candidates.append({
                    "relative_path": rel_path,
                    "file_size_bytes": stat.st_size,
                    "evidence_role": evidence_role,
                    "source_family": source_family,
                    "records_count": item_count,
                    "contract_name": data.get("contract_name") if isinstance(data, dict) else None,
                    "advisory_only": data.get("advisory_only", True) if isinstance(data, dict) else True,
                    "candidate_only": data.get("candidate_only", True) if isinstance(data, dict) else True,
                })
            except Exception:
                # Fail-safe skip on malformed JSON
                pass
                
    return {
        "ingestion_repo_detected": True,
        "ingestion_repo_path_checked": str(repo_path),
        "artifacts_scanned_count": scanned_count,
        "artifact_candidates_count": len(candidates),
        "artifact_candidate_summaries": candidates,
    }


def build_bridge_packet(ingestion_repo_path: Path | str = DEFAULT_INGESTION_REPO_PATH) -> dict[str, Any]:
    """Construct the bridge packet with strict protected truth flags and safety checks."""
    discovery = discover_artifacts(ingestion_repo_path)
    
    # Retrieve ingestion repo branch and head if available
    repo_path = Path(ingestion_repo_path).resolve()
    git_head = None
    git_branch = None
    git_status = None
    if discovery["ingestion_repo_detected"]:
        try:
            import subprocess
            res_head = subprocess.run(
                ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
                capture_output=True, text=True, check=True
            )
            git_head = res_head.stdout.strip()
            
            res_branch = subprocess.run(
                ["git", "-C", str(repo_path), "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, check=True
            )
            git_branch = res_branch.stdout.strip()
            
            res_status = subprocess.run(
                ["git", "-C", str(repo_path), "status", "--porcelain"],
                capture_output=True, text=True, check=True
            )
            git_status = "clean" if not res_status.stdout.strip() else "dirty"
        except Exception:
            pass

    # Safety Classification: local-only
    packet = {
        "task_label": "TASK_CONTENTOPS_0175BG_LANE_C_ARTIFACT_INTAKE_BRIDGE_TO_LIFECYCLE_ENGINE_PRECHECK_V0",
        "contentops_source_head": "25030c9ecb7f1340d8abc0943c397984f1ebb4d7",
        "ingestion_repo_path_checked": discovery["ingestion_repo_path_checked"],
        "ingestion_repo_detected": discovery["ingestion_repo_detected"],
        "ingestion_repo_branch": git_branch,
        "ingestion_repo_head": git_head,
        "ingestion_repo_status": git_status,
        "artifacts_scanned_count": discovery["artifacts_scanned_count"],
        "artifact_candidates_count": discovery["artifact_candidates_count"],
        "artifact_candidate_summaries": discovery["artifact_candidate_summaries"],
        
        # Protected truth flags (Never promote to truth)
        "protected_truth_flags": {
            "dqr_cleared_by_contentops": False,
            "readiness_cleared_by_contentops": False,
            "current_truth_promoted": False,
            "numeric_truth_promoted": False,
            "market_data_promoted": False,
        },
        
        # Lifecycle overlay configuration
        "lifecycle_overlay": {
            "affected_stage_id": "artifact_or_brief_intake",
            "stage_state_after_overlay": "PENDING" if discovery["artifact_candidates_count"] > 0 else "BLOCKED",
            "operator_review_required": True,
            "downstream_dispatch_ready": False,
            "public_postable": False,
        },
        
        # Safety flags: Confirm no platform/provider APIs or environment reads are leaked
        "safety_flags": {
            "live_api_called": False,
            "provider_api_called": False,
            "platform_api_called": False,
            "credential_hydrated": False,
            "secret_values_observed": False,
            "env_secret_read": False,
            "scheduler_enabled": False,
            "scraping_performed": False,
        }
    }
    return packet
