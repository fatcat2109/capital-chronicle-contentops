"""CC-238: the short newsroom window prompts follow the current rules and name real CLI commands."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "docs" / "publisher" / "CC-238"
RETIRED = (
    "01a1657e", "send_message_to_thread", "argon_event", "personal instructions", "Claude L1",
    "2-5 distinct", "2-5 useful", "ANALYSIS retains", "retains its lawful photo", "never caps",
    "arbitrary one-repair", "L2 ContentOps", "L3 send",
)


def prompts():
    full = (DIR / "window-prompt-full.txt").read_text(encoding="utf-8")
    brief = (DIR / "window-prompt-brief.txt").read_text(encoding="utf-8") + "\n" + full
    return {"full": full.replace("{AUTOMATION_ID}", "v1-newsroom-test"),
            "brief": brief.replace("{AUTOMATION_ID}", "v1-newsroom-test")}


@pytest.mark.parametrize("kind", ["full", "brief"])
def test_window_prompt_has_no_retired_rule_and_is_short(kind):
    text = prompts()[kind]
    for needle in RETIRED:
        assert needle not in text, needle
    assert "{AUTOMATION_ID}" not in text
    assert len(text.split()) < 1100  # the 2,300-word prompts they replace


@pytest.mark.parametrize("kind", ["full", "brief"])
def test_window_prompt_keeps_bindings_budgets_roles_and_current_media_rules(kind):
    text = prompts()[kind]
    for needle in ("gpt-6.1-sol/max", "gpt-6-luna/max", "gpt-6.1-sol/low", "ten non-chargeable",
                   "LLM_OPERATOR_PAUSED", "config/native_desktop_rollout_v1.json",
                   "analysis_scope OTHER_ANALYSIS", "A missing photo never holds a piece",
                   "at most one round", "send no message to any chat or thread",
                   "window-result", "window-blocked --binding", "UNKNOWN", "BrowserOS Neo"):
        if needle == "UNKNOWN":
            needle = "uncertain write"
        assert needle in text, needle


def test_window_prompt_names_only_real_commands():
    source = (ROOT / "scripts" / "run_native_desktop_editorial.py").read_text(encoding="utf-8")
    choices = source[source.index('parser.add_argument("command"'):]
    choices = choices[:choices.index("))") + 2]
    known = set(re.findall(r'"([a-z][a-z-]+)"', choices))
    text = prompts()["full"]
    used = set(re.findall(r"run_native_desktop_editorial\.py ([a-z-]+)", text))
    used |= set(re.findall(r"(?:^|[ ,(])(advance|submit|media-plan|final-visual-review|review|handoff|publication-prepare|"
        r"publication-resume|publication-tool-begin|publication-tool-submit|window-result|window-blocked)(?= --| |,|\.|;|\))", text))
    assert {"scheduled", "advance", "submit", "media-plan", "review", "handoff", "window-result",
            "window-blocked", "publication-resume", "final-visual-review"} <= used
    assert used <= known, used - known
    # The retired notice chain is not run (window-blocked-begin and window-notice-begin only appear after "do not run").
    for command in ("window-notice-begin", "window-blocked-begin", "window-notice-record", "window-blocked-record"):
        for m in re.finditer(re.escape(command), text):
            assert "do not run" in text[max(0, m.start() - 60):m.start()]

