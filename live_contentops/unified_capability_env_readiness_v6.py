"""V6 unified capability and scoped env readiness.
Presence-only scanner records key names and booleans only; never values or env lines.
"""
from __future__ import annotations
import argparse, json, os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping
SCHEMA_VERSION="6.0.0"
TASK_LABEL="TASK_CONTENTOPS_V6_FAST_SHIP_RUNTIME_SPINE_CONSOLIDATION_UNIFIED_CAPABILITY_ENV_READINESS_HEAVY_BATCH_V0"
PACKET_STATUS_READY="unified_capability_env_readiness_available_for_product_lane_selection"
CAPABILITY_DEFS=(
 {"capability_id":"discord_webhook","platform_family":"discord","action_class":"webhook_dry_run_outbox_then_supervised_live_candidate","required_key_names":["DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK"],"optional_key_names":[],"next_allowed_task_class":"discord_dry_run_outbox_and_operator_approval_spine","manual_fallback_available":True,"approval_required":True,"audit_required":True,"live_write_requires_separate_scope":True},
 {"capability_id":"telegram_bot","platform_family":"telegram","action_class":"bot_dry_run_outbox_then_supervised_live_candidate","required_key_names":["TELEGRAM_BOT_TOKEN","TELEGRAM_CHAT_ID"],"optional_key_names":[],"next_allowed_task_class":"telegram_dry_run_outbox_and_operator_approval_spine","manual_fallback_available":True,"approval_required":True,"audit_required":True,"live_write_requires_separate_scope":True},
 {"capability_id":"substack_manual_or_browser_compose","platform_family":"substack","action_class":"manual_or_browser_compose","required_key_names":[],"optional_key_names":["SUBSTACK_EMAIL"],"next_allowed_task_class":"substack_manual_browser_compose_dry_run","manual_fallback_available":True,"approval_required":True,"audit_required":True,"live_write_requires_separate_scope":True},
 {"capability_id":"ai_provider_research_writer","platform_family":"ai_provider","action_class":"research_writer_generation","required_key_names":[],"optional_key_names":["OPENAI_API_KEY","ANTHROPIC_API_KEY"],"next_allowed_task_class":"ai_research_canonical_article_production_engine","manual_fallback_available":True,"approval_required":True,"audit_required":True,"live_write_requires_separate_scope":False},
 {"capability_id":"browser_operator","platform_family":"browser","action_class":"operator_supervised_browser_loop","required_key_names":[],"optional_key_names":[],"next_allowed_task_class":"browser_operator_command_center_ui_evidence_loop","manual_fallback_available":True,"approval_required":True,"audit_required":True,"live_write_requires_separate_scope":True},
 {"capability_id":"manual_export_fallback","platform_family":"manual","action_class":"manual_export_fallback","required_key_names":[],"optional_key_names":[],"next_allowed_task_class":"manual_export_fallback_packet","manual_fallback_available":True,"approval_required":False,"audit_required":True,"live_write_requires_separate_scope":True},)
SAMPLE_PRESENT_KEYS={"DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK","TELEGRAM_BOT_TOKEN","OPENAI_API_KEY"}
@dataclass(frozen=True)
class EnvScanSummary:
 scan_mode:str; process_env_checked:bool; dotenv_key_names_checked:bool; dotenv_path_present:bool; dotenv_missing_is_blocker:bool; checked_key_names:list[str]; key_presence:dict[str,bool]; raw_values_serialized:bool=False; value_lengths_serialized:bool=False; value_prefixes_serialized:bool=False; value_suffixes_serialized:bool=False; value_hashes_serialized:bool=False; value_digests_serialized:bool=False; env_lines_serialized:bool=False
@dataclass(frozen=True)
class CapabilityRecord:
 capability_id:str; platform_family:str; action_class:str; required_key_names:list[str]; optional_key_names:list[str]; key_presence:dict[str,bool]; capability_status:str; next_allowed_task_class:str; manual_fallback_available:bool; approval_required:bool; audit_required:bool; live_write_requires_separate_scope:bool; blockers:list[str]=field(default_factory=list)
@dataclass(frozen=True)
class UnifiedCapabilityEnvReadinessPacket:
 schema_version:str; task_label:str; packet_status:str; env_scan:dict[str,Any]; capabilities:list[dict[str,Any]]; live_provider_write_performed:bool; raw_secret_values_serialized:bool; value_lengths_serialized:bool; value_prefixes_serialized:bool; value_suffixes_serialized:bool; value_hashes_serialized:bool; value_digests_serialized:bool; env_lines_serialized:bool; provider_live_write_requires_separate_scope:bool; recommended_next_task:str; blockers:list[str]=field(default_factory=list)
def known_key_names()->list[str]:
 names=set()
 for cap in CAPABILITY_DEFS: names.update(cap["required_key_names"]); names.update(cap["optional_key_names"])
 return sorted(names)
def parse_dotenv_key_names(path:Path)->set[str]:
 if not path.exists(): return set()
 keys=set()
 for line in path.read_text(encoding="utf-8-sig").splitlines():
  stripped=line.strip()
  if not stripped or stripped.startswith("#") or "=" not in stripped: continue
  key=stripped.split("=",1)[0].strip()
  if key and key.replace("_","").isalnum(): keys.add(key)
 return keys
def collect_key_presence(env:Mapping[str,Any]|None=None,dotenv_path:str|Path|None=None,scan_mode:str="both",checked_keys:list[str]|None=None)->EnvScanSummary:
 checked=checked_keys or known_key_names(); use_process=scan_mode in {"both","process_env_only"}; use_dotenv=scan_mode in {"both","dotenv_key_name_presence_only"}; env_map=env if env is not None else os.environ; path=Path(dotenv_path) if dotenv_path is not None else Path(".env"); dotenv_names=parse_dotenv_key_names(path) if use_dotenv else set(); presence={k:bool((use_process and k in env_map) or (use_dotenv and k in dotenv_names)) for k in checked}
 return EnvScanSummary(scan_mode,use_process,use_dotenv,path.exists() if use_dotenv else False,False,checked,presence)
def _status(required:list[str],optional:list[str],presence:dict[str,bool],capability_id:str)->tuple[str,list[str]]:
 missing=[k for k in required if not presence.get(k,False)]
 if missing: return "unavailable",[f"missing_required_key_name:{k}" for k in missing]
 if capability_id in {"browser_operator","manual_export_fallback","substack_manual_or_browser_compose"}: return "configured_for_dry_run",[]
 if capability_id=="ai_provider_research_writer":
  has_ai=any(presence.get(k,False) for k in optional); return ("configured_for_dry_run" if has_ai else "unavailable",[] if has_ai else ["missing_ai_provider_key_name"])
 return "configured_for_supervised_live_scope_candidate",[]
def build_capability_records(scan:EnvScanSummary)->list[CapabilityRecord]:
 records=[]
 for cap in CAPABILITY_DEFS:
  keys=list(cap["required_key_names"]+cap["optional_key_names"]); kp={k:scan.key_presence.get(k,False) for k in keys}; status,blockers=_status(cap["required_key_names"],cap["optional_key_names"],scan.key_presence,cap["capability_id"])
  records.append(CapabilityRecord(cap["capability_id"],cap["platform_family"],cap["action_class"],list(cap["required_key_names"]),list(cap["optional_key_names"]),kp,status,cap["next_allowed_task_class"],cap["manual_fallback_available"],cap["approval_required"],cap["audit_required"],cap["live_write_requires_separate_scope"],blockers))
 return records
def make_unified_capability_env_readiness_packet(env:Mapping[str,Any]|None=None,dotenv_path:str|Path|None=None,scan_mode:str="both")->UnifiedCapabilityEnvReadinessPacket:
 scan=collect_key_presence(env,dotenv_path,scan_mode); records=build_capability_records(scan)
 return UnifiedCapabilityEnvReadinessPacket(SCHEMA_VERSION,TASK_LABEL,PACKET_STATUS_READY,asdict(scan),[asdict(r) for r in records],False,False,False,False,False,False,False,False,True,"TASK_CONTENTOPS_V6_DISCORD_DRY_RUN_OUTBOX_AND_OPERATOR_APPROVAL_SPINE_HEAVY_BATCH_V0")
def sample_packet()->UnifiedCapabilityEnvReadinessPacket: return make_unified_capability_env_readiness_packet({k:"present" for k in SAMPLE_PRESENT_KEYS},Path("__missing_sample_dotenv__"),"process_env_only")
def main(argv:list[str]|None=None)->int:
 parser=argparse.ArgumentParser(description="Build V6 unified capability/env readiness packet without serializing values."); parser.add_argument("--scan-mode",choices=["both","process_env_only","dotenv_key_name_presence_only","none"],default="both"); parser.add_argument("--dotenv-path",default=".env"); parser.add_argument("--sample",action="store_true"); parser.add_argument("--output",default=""); args=parser.parse_args(argv); pkt=sample_packet() if args.sample else make_unified_capability_env_readiness_packet(dotenv_path=args.dotenv_path,scan_mode=args.scan_mode); text=json.dumps(asdict(pkt),indent=2,sort_keys=True)
 if args.output: Path(args.output).write_text(text+"\n",encoding="utf-8")
 else: print(text)
 return 0
if __name__=="__main__": raise SystemExit(main())
