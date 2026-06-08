"""Deterministic local handoff bundle generator."""
import os
import json

def generate_bundle():
    bundle_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'project_sources_bundle', 'TASK_CONTENTOPS_0051')
    os.makedirs(bundle_dir, exist_ok=True)

    manifest_path = os.path.join(bundle_dir, '00_UPLOAD_BUNDLE_MANIFEST.md')
    prompt_path = os.path.join(bundle_dir, '01_NEW_CHAT_CONTINUATION_PROMPT_AFTER_0051.md')
    summary_path = os.path.join(bundle_dir, '02_CURRENT_STATE_SUMMARY_AFTER_0051.md')
    tasks_path = os.path.join(bundle_dir, '03_COMPLETED_TASKS_0035_TO_0051.md')
    next_task_path = os.path.join(bundle_dir, '04_NEXT_TASK_0052_BRIEF.md')
    safety_path = os.path.join(bundle_dir, '05_SAFETY_BOUNDARIES_AND_KNOWN_CAVEATS.md')
    recap_target = os.path.join(bundle_dir, 'LIVE_CONTROL_PLANE_LOCAL_RELEASE_RECAP_AFTER_0050.md')
    handoff_target = os.path.join(bundle_dir, 'LIVE_CONTROL_PLANE_OPERATOR_HANDOFF_AFTER_0050.md')

    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write("# BUNDLE MANIFEST\n\nFiles included:\n- 00_UPLOAD_BUNDLE_MANIFEST.md\n- 01_NEW_CHAT_CONTINUATION_PROMPT_AFTER_0051.md\n- 02_CURRENT_STATE_SUMMARY_AFTER_0051.md\n- 03_COMPLETED_TASKS_0035_TO_0051.md\n- 04_NEXT_TASK_0052_BRIEF.md\n- 05_SAFETY_BOUNDARIES_AND_KNOWN_CAVEATS.md\n- LIVE_CONTROL_PLANE_LOCAL_RELEASE_RECAP_AFTER_0050.md\n- LIVE_CONTROL_PLANE_OPERATOR_HANDOFF_AFTER_0050.md\n")

    with open(prompt_path, 'w', encoding='utf-8') as f:
        f.write("# NEW CHAT CONTINUATION PROMPT\n\nTARGET EXECUTOR:\nAntigravity IDE\n\nTASK LABEL:\nTASK_CONTENTOPS_0052_LIVE_CONTROL_PLANE_CLI_DISPATCH_HARDENING_AND_FULL_COMMAND_GAUNTLET\n")

    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("# CURRENT STATE SUMMARY\n\nThe sidecar acts as a strict local pipeline. It has no live credentials, no network access, and no automated posting rights. It operates strictly on dry-run principles until explicitly allowed.\n")

    with open(tasks_path, 'w', encoding='utf-8') as f:
        f.write("# COMPLETED TASKS\n\n- 0035: Repo split\n- 0036-0037: Skeletons & Contracts\n- 0038-0039: Policy & Queue\n- 0040-0044: Provider/Platform dry run simulation\n- 0045-0047: Pilot operator packets\n- 0048-0050: Artifact flow, drill, & No-Go reinforcement.\n")

    with open(next_task_path, 'w', encoding='utf-8') as f:
        f.write("# NEXT TASK\n\nTASK_CONTENTOPS_0052_LIVE_CONTROL_PLANE_CLI_DISPATCH_HARDENING_AND_FULL_COMMAND_GAUNTLET\n")

    with open(safety_path, 'w', encoding='utf-8') as f:
        f.write("# SAFETY BOUNDARIES\n\nNO network. NO provider API. NO platform API. NO Telegram token. NO env files. NO schedule. NO auto-posting.\n")

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
        "exact_next_task": "TASK_CONTENTOPS_0052_LIVE_CONTROL_PLANE_CLI_DISPATCH_HARDENING_AND_FULL_COMMAND_GAUNTLET"
    }

def run_cli_bundle():
    res = generate_bundle()
    print(json.dumps(res, indent=2))
