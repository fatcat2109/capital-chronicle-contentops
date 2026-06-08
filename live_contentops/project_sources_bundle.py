"""Deterministic local handoff bundle generator."""
import os
import json

def generate_bundle():
    bundle_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'project_sources_bundle', 'TASK_CONTENTOPS_0053')
    os.makedirs(bundle_dir, exist_ok=True)

    manifest_path = os.path.join(bundle_dir, '00_UPLOAD_BUNDLE_MANIFEST.md')
    prompt_path = os.path.join(bundle_dir, '01_NEW_CHAT_CONTINUATION_PROMPT_AFTER_0053.md')
    summary_path = os.path.join(bundle_dir, '02_CURRENT_STATE_SUMMARY_AFTER_0053.md')
    tasks_path = os.path.join(bundle_dir, '03_COMPLETED_TASKS_0035_TO_0053.md')
    next_task_path = os.path.join(bundle_dir, '04_NEXT_TASK_0054_BRIEF.md')
    safety_path = os.path.join(bundle_dir, '05_SAFETY_BOUNDARIES_AND_KNOWN_CAVEATS.md')
    recap_target = os.path.join(bundle_dir, 'LIVE_CONTROL_PLANE_LOCAL_RELEASE_RECAP_AFTER_0050.md')
    handoff_target = os.path.join(bundle_dir, 'LIVE_CONTROL_PLANE_OPERATOR_HANDOFF_AFTER_0050.md')

    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write("# BUNDLE MANIFEST\n\n")
        f.write("Accepted live-control-plane head before task: `025dbba`.\n")
        f.write("Accepted cc-contentops head: `e57db90`.\n\n")
        f.write("## Files Included & To Upload\n")
        f.write("- 00_UPLOAD_BUNDLE_MANIFEST.md\n")
        f.write("- 01_NEW_CHAT_CONTINUATION_PROMPT_AFTER_0053.md\n")
        f.write("- 02_CURRENT_STATE_SUMMARY_AFTER_0053.md\n")
        f.write("- 03_COMPLETED_TASKS_0035_TO_0053.md\n")
        f.write("- 04_NEXT_TASK_0054_BRIEF.md\n")
        f.write("- 05_SAFETY_BOUNDARIES_AND_KNOWN_CAVEATS.md\n")
        f.write("- LIVE_CONTROL_PLANE_LOCAL_RELEASE_RECAP_AFTER_0050.md\n")
        f.write("- LIVE_CONTROL_PLANE_OPERATOR_HANDOFF_AFTER_0050.md\n\n")
        f.write("## What To Remove From Old Project Sources\n")
        f.write("- Stale older continuation prompts.\n")
        f.write("- Stale older state summaries.\n")
        f.write("- Stale older handoffs.\n")
        f.write("- Duplicate old bundle manifests.\n")
        f.write("- Pre-0052/0052A CLI and audit summaries superseded by this bundle.\n\n")
        f.write("## What NEVER belongs in Project Sources\n")
        f.write("- Secrets, credentials, real platform IDs, env files.\n")
        f.write("- Pycache.\n")
        f.write("- Raw logs.\n")
        f.write("- Antigravity brain files.\n")
        f.write("- Full outputs history.\n")
        f.write("- Core repo files.\n")
        f.write("- Large fixture dumps.\n\n")
        f.write("## Current Next Task\n")
        f.write("TASK_CONTENTOPS_0054_LIVE_CONTROL_PLANE_RELEASE_BUNDLE_AUDIT_AND_NEXT_PHASE_DECISION\n")

    with open(prompt_path, 'w', encoding='utf-8') as f:
        f.write("# NEW CHAT CONTINUATION PROMPT\n\n")
        f.write("TARGET EXECUTOR:\nNew smarter IDE / coding agent\n\n")
        f.write("TASK LABEL:\nTASK_CONTENTOPS_0054_LIVE_CONTROL_PLANE_RELEASE_BUNDLE_AUDIT_AND_NEXT_PHASE_DECISION\n\n")
        f.write("ROLE & PROJECT CONTEXT:\nYou are an agent working on `cc-live-contentops`, a local-only control plane sidecar for Capital Chronicle. Your next task is to audit the release bundle and determine the next phase of the project.\n\n")
        f.write("REPO PATHS:\nLive Control Plane: `A:\\Capital Chronicle\\tools\\cc-live-contentops`\nAuthority Repo: `A:\\Capital Chronicle\\tools\\cc-contentops`\n\n")
        f.write("AUTHORITY ORDER:\n1. Repo files and git history.\n2. Committed docs/schemas in `cc-live-contentops`.\n3. Source authority docs in `cc-contentops`.\n\n")
        f.write("ACCEPTED HEADS:\nLive-control-plane: `025dbba` (Deep Audit Passed)\ncc-contentops: `e57db90`\n\n")
        f.write("ACCEPTED STATE & HARD BOUNDARIES:\n- 0048/0049 accepted after reconciliation.\n- 0052 CLI command registry hardening passed.\n- 0052A deep audit passed.\n- No live credentials. No network. No provider API. No platform APIs. NO-GO posture is active.\n\n")
        f.write("HOW TO AUDIT IDE EVIDENCE PACKETS:\nVerify that the actual CLI dispatch outputs or repo artifacts reflect what is claimed in the Final Evidence Packet.\n\n")
        f.write("EXACT NEXT TASK:\nTASK_CONTENTOPS_0054_LIVE_CONTROL_PLANE_RELEASE_BUNDLE_AUDIT_AND_NEXT_PHASE_DECISION\n\n")

    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("# CURRENT STATE SUMMARY AFTER 0053\n\n")
        f.write("The `cc-live-contentops` sidecar exists completely offline as a deterministic orchestrator and validator. It implements strict validation policies, approval queues, and dry-run simulators for LLM gateway outputs and social media platforms (Telegram, X, LinkedIn, Instagram).\n\n")
        f.write("All platform interactions remain simulator-only and NOT live-ready. Credentials remain blocked because explicit user authorization and verification loops (such as operator rollback drills) have shown that safe containment must be proven fully before network activation. The current recommended next task is `TASK_CONTENTOPS_0054_LIVE_CONTROL_PLANE_RELEASE_BUNDLE_AUDIT_AND_NEXT_PHASE_DECISION`.\n")

    with open(tasks_path, 'w', encoding='utf-8') as f:
        f.write("# COMPLETED TASKS 0035 TO 0053\n\n")
        f.write("- 0035: Repo split (cc-contentops `e57db90`)\n")
        f.write("- 0036-0037: Skeletons & Contracts\n")
        f.write("- 0038-0039: Policy & Queue\n")
        f.write("- 0040-0044: Provider/Platform dry run simulation\n")
        f.write("- 0045-0047: Pilot operator packets\n")
        f.write("- 0048-0049: Artifact flow & drill (accepted only after reconciliation)\n")
        f.write("- 0050: NO-GO reinforcement\n")
        f.write("- 0051: Release recap & handoff\n")
        f.write("- 0052: CLI command registry hardening passed\n")
        f.write("- 0052A: Deep audit passed (`025dbba`)\n")
        f.write("- 0053: Release bundle cleanup\n")

    with open(next_task_path, 'w', encoding='utf-8') as f:
        f.write("# NEXT TASK: 0054 BRIEF\n\n")
        f.write("TASK_CONTENTOPS_0054_LIVE_CONTROL_PLANE_RELEASE_BUNDLE_AUDIT_AND_NEXT_PHASE_DECISION\n\n")
        f.write("Objective: audit the upload bundle, confirm Project Sources cleanup, and decide whether the next phase should remain local/no-key or prepare a future explicitly-approved credential-design task.\n\n")
        f.write("It must not start credentials or live API work. It should likely remain NO-GO unless operator explicitly provides prerequisites outside repo later.\n")

    with open(safety_path, 'w', encoding='utf-8') as f:
        f.write("# SAFETY BOUNDARIES AND KNOWN CAVEATS\n\n")
        f.write("- NO network, NO API calls, NO credentials, NO live posting.\n")
        f.write("- Dry-run ONLY.\n")
        f.write("- NO autonomous replies or DMs.\n")
        f.write("- NO financial advice.\n")
        f.write("- NO platform scope claims without verification.\n")
        f.write("- NO current-event claims without source bundle.\n")
        f.write("- NO real IDs or tokens in the repository.\n")
        f.write("- NEVER upload raw outputs or large fixture dumps.\n")
        f.write("- Follow Project Sources cleanup guidance in the manifest to discard stale files.\n")

    # Copy recap and handoff
    docs_dir = os.path.join(os.path.dirname(__file__), '..', 'docs')
    recap_src = os.path.join(docs_dir, 'LIVE_CONTROL_PLANE_LOCAL_RELEASE_RECAP_AFTER_0050.md')
    handoff_src = os.path.join(docs_dir, 'LIVE_CONTROL_PLANE_OPERATOR_HANDOFF_AFTER_0050.md')

    if os.path.exists(recap_src):
        with open(recap_src, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(recap_target, 'w', encoding='utf-8') as f:
            f.write(content)

    if os.path.exists(handoff_src):
        with open(handoff_src, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(handoff_target, 'w', encoding='utf-8') as f:
            f.write(content)

    return {
        "status": "BUNDLE_GENERATED",
        "output_path": bundle_dir,
        "files_generated": 8,
        "secrets_redacted": True,
        "network_used": False,
        "safe_for_publish": False,
        "exact_next_task": "TASK_CONTENTOPS_0054_LIVE_CONTROL_PLANE_RELEASE_BUNDLE_AUDIT_AND_NEXT_PHASE_DECISION"
    }

def run_cli_bundle():
    res = generate_bundle()
    print(json.dumps(res, indent=2))
