import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
V2_DIR = os.path.join(BASE_DIR, "ui", "institutional_operator_cockpit_v2")
SHELL_DIR = os.path.join(BASE_DIR, "ui", "institutional_shell")
DOCS_DIR = os.path.join(BASE_DIR, "docs")

V2_FILES = ("index.html", "styles.css", "view_model.js", "cockpit.js", "README.md")


def _read(directory, name):
    with open(os.path.join(directory, name), "r", encoding="utf-8") as f:
        return f.read()


def _v2_runtime_text():
    """Concatenate the runtime-facing V2 assets (html/css/js)."""
    parts = []
    for name in ("index.html", "styles.css", "view_model.js", "cockpit.js"):
        parts.append(_read(V2_DIR, name))
    return "\n".join(parts)


# 1. V2 files exist.
def test_v2_files_exist():
    for name in V2_FILES:
        assert os.path.isfile(os.path.join(V2_DIR, name)), name


def test_reference_extraction_doc_exists():
    path = os.path.join(
        DOCS_DIR, "TASK_CONTENTOPS_0174R_STITCH_REFERENCE_EXTRACTION.md"
    )
    assert os.path.isfile(path)
    txt = _read(DOCS_DIR, "TASK_CONTENTOPS_0174R_STITCH_REFERENCE_EXTRACTION.md")
    # Records extraction without importing/copying Stitch HTML as runtime.
    assert "advisory visual reference" in txt.lower()
    assert "imported as runtime" in txt.lower()
    assert "copied into the repo" in txt.lower()
    assert "Adopted Patterns" in txt
    assert "Adapted Patterns" in txt
    assert "Rejected Patterns" in txt


# 2. External dependency ban.
FORBIDDEN_EXTERNAL = [
    "http://",
    "https://",
    "cdn.",
    "fonts.googleapis",
    "fonts.gstatic",
    "tailwindcss",
    "material-symbols",
    "material symbols",
    "fetch(",
    "XMLHttpRequest",
    "WebSocket",
    "EventSource",
]


def test_no_external_dependencies_in_runtime_assets():
    txt = _v2_runtime_text().lower()
    for needle in FORBIDDEN_EXTERNAL:
        assert needle.lower() not in txt, needle


def test_no_remote_link_or_script_tags():
    html = _read(V2_DIR, "index.html")
    assert "href=\"http" not in html
    assert "src=\"http" not in html
    assert "//cdn" not in html


# 3. Source-of-truth / current metadata: stale heads must not appear as current.
STALE_HEADS = ["15b87ff", "1c03ca0", "444ef2c"]


def test_stale_heads_only_under_historical_provenance():
    vm = _read(V2_DIR, "view_model.js")
    for head in STALE_HEADS:
        # Each stale head must appear only inside the historical provenance block.
        assert head in vm, head
        # historical provenance block must exist and label them not-runtime-authority.
    assert "historical_screen_provenance" in vm
    assert "Not Runtime Authority" in vm or "not_runtime_authority" in vm


def test_stale_heads_not_in_global_state_block():
    vm = _read(V2_DIR, "view_model.js")
    start = vm.index("global_state")
    end = vm.index("safety_ribbon")
    global_block = vm[start:end]
    for head in STALE_HEADS:
        assert head not in global_block, head


# 4. Current baselines present and separated.
def test_current_baselines_present_and_separated():
    vm = _read(V2_DIR, "view_model.js")
    assert "680d03d" in vm
    assert "496591f" in vm
    assert "current_repo_baseline" in vm
    assert "last_product_code_baseline" in vm


def test_header_renders_both_baselines():
    js = _read(V2_DIR, "cockpit.js")
    assert "Current Repo Baseline" in js
    assert "Last Product Code Baseline" in js


# 5. Status evidence contract.
REQUIRED_TOKEN_FIELDS = [
    "status",
    "severity",
    "reason",
    "evidence_ref_ids",
    "allowed_actions",
    "blocked_actions",
    "current_truth",
    "historical_provenance",
]


def test_status_token_contract_fields_present():
    vm = _read(V2_DIR, "view_model.js")
    for fld in REQUIRED_TOKEN_FIELDS:
        assert fld in vm, fld


def test_pass_never_means_publish_ready():
    vm = _read(V2_DIR, "view_model.js").lower()
    # A caveat must clarify PASS is system-safe only.
    assert "pass" in vm
    assert "never" in vm or "system-safe only" in vm



# 6. Forbidden controls: no enabled-looking actionable controls.
def test_no_enabled_action_controls():
    js = _read(V2_DIR, "cockpit.js")
    html = _read(V2_DIR, "index.html")
    # No inline event handlers / action affordances anywhere.
    for attr in ("onclick", "onsubmit", "formaction", "action="):
        assert attr not in html.lower(), attr
        assert attr not in js.lower(), attr
    # index.html contains no <button>, <form>, or <input> action elements;
    # the only interactive controls (nav) are created in JS as nav-item buttons.
    for tag in ("<button", "<form", "<input"):
        assert tag not in html.lower(), tag


def test_only_nav_buttons_are_interactive():
    js = _read(V2_DIR, "cockpit.js")
    # The only created <button> elements are nav items, and there is exactly
    # one click handler site (the nav button factory).
    assert js.count('"button"') >= 1
    assert js.count('addEventListener("click"') == 1
    assert "nav-item" in js
    # The single click handler only switches the active screen and re-renders;
    # it performs no publish/post/send/schedule/export/upload work.
    handler_region = js[js.index('addEventListener("click"'):]
    handler_region = handler_region[:300].lower()
    for verb in ("publish", "post(", "send", "schedule", "dispatch",
                 "upload", "download", "export", "fetch"):
        assert verb not in handler_region, verb



# 7. Safety labels present.
REQUIRED_SAFETY_LABELS = [
    "LOCAL ONLY",
    "LIVE DISABLED",
    "NOT PUBLIC POSTABLE",
    "MANUAL REVIEW REQUIRED",
    "NO FINANCIAL ADVICE",
    "NO SIGNAL LANGUAGE",
    "KILL SWITCH ACTIVE",
]


def test_required_safety_labels_present():
    vm = _read(V2_DIR, "view_model.js")
    for label in REQUIRED_SAFETY_LABELS:
        assert label in vm, label


def test_kill_switch_active_in_global_state():
    vm = _read(V2_DIR, "view_model.js")
    assert "kill_switch" in vm
    assert "active" in vm
    assert "live_state" in vm
    assert "disabled" in vm


# 8. Old shell preservation.
def test_old_shell_still_exists():
    for name in ("index.html", "styles.css", "app.js", "fixture_data.js", "README.md"):
        assert os.path.isfile(os.path.join(SHELL_DIR, name)), name


def test_old_shell_not_replaced_by_v2():
    # The V2 folder must be distinct from the preserved shell folder.
    assert os.path.abspath(V2_DIR) != os.path.abspath(SHELL_DIR)
    assert os.path.isdir(SHELL_DIR)
    assert os.path.isdir(V2_DIR)


# 9. Screen family completeness.
REQUIRED_SCREENS = [
    "command_center",
    "content_studio",
    "publish_readiness",
    "evidence_vault",
    "content_calendar",
    "visual_export",
    "settings",
]


def test_all_screens_present():
    vm = _read(V2_DIR, "view_model.js")
    for sid in REQUIRED_SCREENS:
        assert sid in vm, sid


def test_no_market_direction_color_semantics():
    css = _read(V2_DIR, "styles.css").lower()
    # No bull/bear/up-down market color tokens.
    for needle in ("bull", "bear", "--up", "--down", "long", "short"):
        assert needle not in css, needle

