import os
from live_contentops import project_sources_bundle

def test_project_sources_bundle_generation():
    res = project_sources_bundle.generate_bundle()
    
    assert res["status"] == "BUNDLE_GENERATED"
    assert res["files_generated"] == 8
    assert res["secrets_redacted"] is True
    assert res["network_used"] is False
    assert res["safe_for_publish"] is False
    assert res["exact_next_task"] == "TASK_CONTENTOPS_0052_LIVE_CONTROL_PLANE_CLI_DISPATCH_HARDENING_AND_FULL_COMMAND_GAUNTLET"
    
    bundle_dir = res["output_path"]
    assert os.path.exists(bundle_dir)
    
    files = [
        "00_UPLOAD_BUNDLE_MANIFEST.md",
        "01_NEW_CHAT_CONTINUATION_PROMPT_AFTER_0051.md",
        "02_CURRENT_STATE_SUMMARY_AFTER_0051.md",
        "03_COMPLETED_TASKS_0035_TO_0051.md",
        "04_NEXT_TASK_0052_BRIEF.md",
        "05_SAFETY_BOUNDARIES_AND_KNOWN_CAVEATS.md",
        "LIVE_CONTROL_PLANE_LOCAL_RELEASE_RECAP_AFTER_0050.md",
        "LIVE_CONTROL_PLANE_OPERATOR_HANDOFF_AFTER_0050.md"
    ]
    
    for f in files:
        assert os.path.exists(os.path.join(bundle_dir, f))

    # Read the prompt and ensure the next task is verbatim.
    with open(os.path.join(bundle_dir, "01_NEW_CHAT_CONTINUATION_PROMPT_AFTER_0051.md"), "r", encoding="utf-8") as f:
        content = f.read()
        assert "TASK_CONTENTOPS_0052_LIVE_CONTROL_PLANE_CLI_DISPATCH_HARDENING_AND_FULL_COMMAND_GAUNTLET" in content
