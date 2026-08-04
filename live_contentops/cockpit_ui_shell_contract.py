"""Cockpit UI shell contract (LOCAL STATIC HTML SHELL ONLY, NO LIVE ACTIONS)."""

import copy
import html
import json
import os.path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import cockpit_ui_shell_policy as policy
from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174YL_YM_YN_COCKPIT_UI_SHELL_CONTRACT_V0"
MODEL = "COCKPIT_UI_SHELL_CONTRACT_0174YL_YM_YN"
MODEL_VERSION = "0174YL_YM_YN_COCKPIT_UI_SHELL_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "ab6e9840f2dc1d73008bea3e6aabbbcf4db5abdd"
DOC_REL_DIR = os.path.join("docs", "automation", "0174YL_YM_YN")
SHELL_PACKET = "cockpit_ui_shell_packet.json"
SHELL_DOC = "cockpit_ui_shell.md"
SHELL_HTML = "cockpit_ui_shell.html"
SHELL_FIXTURE = "cockpit_ui_shell_fixture.json"
NEXT_QA_PACKET = "next_cockpit_browser_qa_packet.json"
NEXT_QA_DOC = "next_cockpit_browser_qa.md"
NEXT_BATCH_PROMPT = "TASK_CONTENTOPS_0174YO_YP_YQ_COCKPIT_BROWSER_QA_CONTRACT_V0"

PATHS = {
    "static_surface": os.path.join("docs", "automation", "0174YI_YJ_YK", "static_cockpit_surface_packet.json"),
    "static_policy": os.path.join("docs", "automation", "0174YI_YJ_YK", "static_cockpit_surface_policy_packet.json"),
    "static_fixture": os.path.join("docs", "automation", "0174YI_YJ_YK", "static_cockpit_surface_fixture_outputs.json"),
    "static_html": os.path.join("docs", "automation", "0174YI_YJ_YK", "static_cockpit_surface.html"),
    "next_ui_shell": os.path.join("docs", "automation", "0174YI_YJ_YK", "next_cockpit_ui_shell_contract_packet.json"),
    "read_model": os.path.join("docs", "automation", "0174YF_YG_YH", "cockpit_read_model_packet.json"),
    "manual_review": os.path.join("docs", "automation", "0174YC_YD_YE", "manual_export_review_surface_packet.json"),
    "readiness": os.path.join("docs", "automation", "0174XZ_YA_YB", "supervised_dispatch_readiness_summary_packet.json"),
    "platform_registry": os.path.join("docs", "automation", "0174WY_WZ_XA", "platform_universe_registry_v2_packet.json"),
}


def _read_json(repo_root, rel_path):
    p = pathlib.Path(repo_root) / rel_path
    if not p.exists():
        for archive_root in [
            "docs/archive/_repo_cleanup_2026-07-03-pass3",
            "docs/archive/_repo_cleanup_2026-07-03",
            "docs/archive/_repo_cleanup_2026-07-03-pass2",
        ]:
            cand = pathlib.Path(repo_root) / archive_root / rel_path
            if cand.exists():
                p = cand
                break
    return json.loads(p.read_text(encoding="utf-8"))


def load_inputs(repo_root="."):
    inputs = {name: _read_json(repo_root, rel_path) for name, rel_path in PATHS.items() if name != "static_html"}
    inputs["static_html_checksum"] = adapter.compute_checksum({"html": (pathlib.Path(repo_root) / PATHS["static_html"]).read_text(encoding="utf-8")})
    return inputs


def _source_notes(item):
    notes = []
    if item.get("review_status"):
        notes.append(item["review_status"])
    if item.get("limitations"):
        notes.extend(item["limitations"][:3])
    return notes or ["review_only_local_shell_item"]


def _evidence_card(item):
    card = {
        "component": "EvidenceCard",
        "item_id": item["item_id"],
        "payload_hash_short": item["payload_hash_short"],
        "payload_hash": item["payload_hash"],
        "payload_class": item["payload_class"],
        "platform": item["platform"],
        "source_payload_id": item.get("source_payload_id"),
        "source_notes": _source_notes(item),
        "evidence_refs": list(item.get("evidence_refs", [])),
        "can_dispatch": False,
        "public_postable": False,
        "human_review_required": True,
        "shell_action_label": _review_only_label(item.get("allowed_operator_action", "hold")),
    }
    policy.validate_no_forbidden_readiness_claims(card)
    policy.validate_no_forbidden_material(card)
    return card


def _review_only_label(action):
    labels = {
        "copy_markdown_for_substack": "Review-only manual export copy; non-executing shell affordance",
        "inspect_x_short_preview": "Inspect X short preview; non-executing shell affordance",
        "inspect_x_thread_preview": "Inspect X thread preview; non-executing shell affordance",
        "inspect_telegram_channel_update_preview": "Inspect Telegram frozen preview; non-executing shell affordance",
        "hold": "Hold; non-executing shell affordance",
    }
    return labels.get(action, "Review-only non-executing shell affordance")


def _queue(items, platform_name):
    return [item for item in items if item["platform"] == platform_name]


def build_fixture(inputs, policy_packet):
    source_items = inputs["static_fixture"]
    evidence_cards = [_evidence_card(item) for item in source_items]
    fixture = {
        "task_label": TASK_LABEL,
        "source_static_cockpit_surface_checksum": inputs["static_surface"]["static_cockpit_surface_checksum"],
        "source_static_cockpit_surface_policy_checksum": inputs["static_policy"]["static_cockpit_surface_policy_checksum"],
        "source_static_cockpit_surface_fixture_checksum": inputs["static_surface"]["static_cockpit_surface_fixture_outputs_checksum"],
        "shell_regions": list(policy_packet["shell_regions"]),
        "evidence_cards": evidence_cards,
        "manual_export_queue": _queue(evidence_cards, "substack"),
        "x_preview_queue": _queue(evidence_cards, "x"),
        "telegram_preview_queue": _queue(evidence_cards, "telegram"),
        "blocked_live_dispatch_queue": copy.deepcopy(inputs["static_surface"].get("blocked_live_dispatch_queue", [])),
        "audit_table": [
            {"source_stage": entry["stage"], "checksum": entry["checksum"], "status": "PASS_BOUND"}
            for entry in inputs["static_surface"].get("evidence_index", [])
        ],
        "status": "pass",
    }
    policy.validate_no_forbidden_readiness_claims(fixture)
    policy.validate_no_forbidden_material(fixture)
    fixture["cockpit_ui_shell_fixture_checksum"] = adapter.compute_checksum(fixture)
    return fixture


def _shell_regions(policy_packet):
    return [
        {
            "region_id": region,
            "component_class": region,
            "semantic_fields": list(policy_packet["semantic_components"][region]),
            "density": policy_packet["design_tokens"]["density"],
            "screenshot_safe": True,
        }
        for region in policy_packet["shell_regions"]
    ]


def build_shell_packet(inputs, policy_packet, fixture, html_checksum=None):
    static_surface = inputs["static_surface"]
    no_live_proof = copy.deepcopy(static_surface["no_live_behavior_proof"])
    no_live_proof.update(policy.safety_flags())
    no_live_proof["proof"] = "pass_cockpit_ui_shell_no_live_no_env_no_network_no_platform_provider"
    packet = {
        "cockpit_ui_shell_id": "cockpit_ui_shell_0174YL_YM_YN",
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **policy.safety_flags(),
        "readiness_class": policy.READINESS_CLASS,
        "live_dispatch_status": policy.LIVE_DISPATCH_STATUS,
        "local_governance_status": policy.LOCAL_GOVERNANCE_STATUS,
        "manual_export_status": policy.MANUAL_EXPORT_STATUS,
        "shell_regions": _shell_regions(policy_packet),
        "rendered_shell_regions": list(policy.SHELL_REGIONS),
        "semantic_components": copy.deepcopy(policy.SEMANTIC_COMPONENTS),
        "design_tokens": copy.deepcopy(policy.DESIGN_TOKENS),
        "platform_statuses": copy.deepcopy(policy.PLATFORM_STATUSES),
        "reviewable_now_count": static_surface["reviewable_now_count"],
        "manual_export_queue_count": static_surface["manual_export_queue_count"],
        "x_preview_queue_count": static_surface["x_preview_queue_count"],
        "telegram_preview_queue_count": static_surface["telegram_preview_queue_count"],
        "blocked_live_dispatch_count": static_surface["blocked_live_dispatch_count"],
        "evidence_index_count": len(static_surface["evidence_index"]),
        "manual_export_queue": fixture["manual_export_queue"],
        "x_preview_queue": fixture["x_preview_queue"],
        "telegram_preview_queue": fixture["telegram_preview_queue"],
        "blocked_live_dispatch_queue": fixture["blocked_live_dispatch_queue"],
        "evidence_cards": fixture["evidence_cards"],
        "audit_table": fixture["audit_table"],
        "required_future_gates": list(policy.REQUIRED_FUTURE_GATES),
        "current_truth": [
            "manual export first",
            "reviewable local queues visible",
            "platform APIs off",
            "live dispatch blocked",
            "Telegram previews are frozen and no-send",
        ],
        "future_requirements": copy.deepcopy(static_surface.get("blocker_summary", {}).get("blocked_reasons", [])),
        "next_safe_operator_action": "open cockpit UI shell preview locally; review queues; use only non-executing review-only controls",
        "allowed_review_only_actions": list(policy.ALLOWED_REVIEW_ONLY_ACTIONS),
        "forbidden_actions": list(policy.FORBIDDEN_ACTIONS),
        "html_file": SHELL_HTML,
        "html_checksum": html_checksum,
        "cockpit_ui_shell_fixture_checksum": fixture["cockpit_ui_shell_fixture_checksum"],
        "source_static_cockpit_surface_checksum": static_surface["static_cockpit_surface_checksum"],
        "source_static_cockpit_surface_policy_checksum": inputs["static_policy"]["static_cockpit_surface_policy_checksum"],
        "source_static_cockpit_surface_fixture_checksum": static_surface["static_cockpit_surface_fixture_outputs_checksum"],
        "source_static_cockpit_surface_html_checksum": inputs["static_html_checksum"],
        "source_next_cockpit_ui_shell_contract_checksum": inputs["next_ui_shell"]["next_cockpit_ui_shell_contract_checksum"],
        "no_external_dependency_proof": {
            "html_scripts_allowed": False,
            "html_forms_allowed": False,
            "external_assets_allowed": False,
            "iframe_allowed": False,
            "tracking_allowed": False,
            "runtime_network_allowed": False,
            "react_used": False,
            "tailwind_used": False,
            "cdn_used": False,
            "external_fonts_used": False,
        },
        "no_forbidden_readiness_claim_proof": "pass_no_forbidden_readiness_claims_in_cockpit_ui_shell",
        "no_live_action_affordance_proof": {
            "can_dispatch": False,
            "public_postable": False,
            "live_dispatch_status": policy.LIVE_DISPATCH_STATUS,
            "action_elements_review_only_or_non_executing": True,
            "hidden_live_affordances_allowed": False,
        },
        "no_live_behavior_proof": no_live_proof,
        "screenshot_safe_surface": True,
        "status": "pass",
    }
    policy.validate_no_forbidden_readiness_claims(packet)
    policy.validate_no_forbidden_material(packet)
    packet["cockpit_ui_shell_checksum"] = adapter.compute_checksum(packet)
    return packet


def _esc(value):
    return html.escape(str(value), quote=True)


def _badge(label, danger=False, good=False):
    cls = "badge danger" if danger else "badge good" if good else "badge"
    return f'<span class="{cls}">{_esc(label)}</span>'


def _card(card):
    refs = ", ".join(card.get("evidence_refs", [])[:2]) or "checksum-bound upstream evidence"
    return f"""
      <article class="EvidenceCard evidence-card">
        <div class="hash">{_esc(card['payload_hash_short'])}</div>
        <h3>{_esc(card['payload_class'])}</h3>
        <dl>
          <dt>Platform</dt><dd>{_esc(card['platform'])}</dd>
          <dt>Source payload</dt><dd>{_esc(card.get('source_payload_id'))}</dd>
          <dt>Source notes</dt><dd>{_esc('; '.join(card.get('source_notes', [])))}</dd>
          <dt>Evidence refs</dt><dd><code>{_esc(refs)}</code></dd>
          <dt>can_dispatch</dt><dd>false</dd>
          <dt>public_postable</dt><dd>false</dd>
        </dl>
        <p class="review-action">{_esc(card['shell_action_label'])}</p>
      </article>
    """


def _cards(cards):
    return "\n".join(_card(card) for card in cards) or '<p class="muted">No review-only items.</p>'


def _blocker_rows(blockers):
    return "\n".join(
        f"<li><strong>{_esc(item.get('required_future_gate', item.get('blocker_id', 'future_gate')))}</strong><span>{_esc(item.get('reason', item.get('status', 'blocked')))}</span></li>"
        for item in blockers
    )


def _audit_rows(rows):
    return "\n".join(
        f"<tr><td>{_esc(row['source_stage'])}</td><td><code>{_esc(row['checksum'])}</code></td><td>{_esc(row['status'])}</td></tr>"
        for row in rows
    )


def render_html(packet):
    platform_cards = "\n".join(
        f"<article class='truth-card'><span>{_esc(platform)}</span><strong>{_esc(status)}</strong></article>"
        for platform, status in sorted(packet["platform_statuses"].items())
    )
    locks = [
        "no live dispatch",
        "no platform API",
        "no credential hydration",
        "no scheduler",
        "no autonomous replies/DMs",
        "no scraping",
        "no financial advice/signal language",
    ]
    html_text = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Local review-only cockpit UI shell for Capital Chronicle ContentOps governance.">
  <title>Capital Chronicle Cockpit UI Shell</title>
  <style>
    :root {{ color-scheme: dark; --bg:#11110f; --panel:#1a1a17; --panel-2:#23231f; --panel-3:#2c2b26; --line:#3b3a32; --text:#eee9dd; --muted:#aaa397; --amber:#d7a447; --red:#c85f5f; --green:#86a86d; --neutral:#c9c0ad; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:linear-gradient(135deg,#0f0f0d,#1b1b18 45%,#0d0d0c); color:var(--text); font-family:Georgia,'Times New Roman',serif; }}
    main {{ width:min(1320px,calc(100% - 32px)); margin:0 auto; padding:28px 0 44px; }}
    .CommandHero {{ border:1px solid var(--line); background:linear-gradient(135deg,rgba(215,164,71,.16),rgba(35,35,31,.95)); border-radius:18px; padding:28px; }}
    h1 {{ margin:0 0 12px; font-size:clamp(36px,5vw,72px); letter-spacing:-.05em; }}
    h2 {{ margin:0 0 16px; font-size:26px; }}
    h3 {{ margin:8px 0 10px; }}
    section {{ margin-top:18px; border:1px solid var(--line); border-radius:16px; padding:20px; background:rgba(26,26,23,.92); }}
    .rail {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:12px; }}
    .badge,.truth-card,.metric,.evidence-card {{ border:1px solid var(--line); background:var(--panel-2); border-radius:12px; padding:12px; }}
    .badge {{ display:inline-flex; margin:4px; color:var(--amber); font-family:Arial,sans-serif; font-weight:700; text-transform:uppercase; letter-spacing:.08em; font-size:12px; }}
    .badge.danger {{ color:var(--red); }} .badge.good {{ color:var(--green); }}
    .truth-card span,.metric span {{ display:block; color:var(--muted); font:700 11px Arial,sans-serif; text-transform:uppercase; letter-spacing:.14em; }}
    .truth-card strong,.metric strong {{ display:block; margin-top:8px; color:var(--amber); overflow-wrap:anywhere; }}
    .ContentLane {{ display:grid; grid-template-columns:1fr; gap:18px; }}
    .lane-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:14px; }}
    .hash, code {{ color:var(--neutral); font-family:Consolas,'Courier New',monospace; overflow-wrap:anywhere; }}
    dl {{ display:grid; grid-template-columns:118px 1fr; gap:7px 10px; }}
    dt {{ color:var(--muted); }} dd {{ margin:0; }}
    .review-action {{ border-top:1px solid var(--line); padding-top:10px; color:var(--amber); font-family:Arial,sans-serif; font-weight:700; }}
    .BlockerStack li {{ margin:10px 0; }} .BlockerStack span {{ display:block; color:var(--muted); }}
    table {{ width:100%; border-collapse:collapse; }} th,td {{ text-align:left; padding:10px; border-bottom:1px solid var(--line); vertical-align:top; }}
    .NextActionPanel strong {{ color:var(--amber); }} .muted {{ color:var(--muted); }}
  </style>
</head>
<body>
<main>
  <header class="CommandHero">
    <p class="muted">Capital Chronicle · Institutional local governance cockpit shell</p>
    <h1>Cockpit UI Shell</h1>
    <div>{_badge(packet['readiness_class'], danger=True)}{_badge(packet['local_governance_status'], good=True)}{_badge(packet['live_dispatch_status'], danger=True)}</div>
    <p><strong>Next safe operator action:</strong> {_esc(packet['next_safe_operator_action'])}</p>
  </header>

  <section class="SignalLockStrip">
    <h2>SignalLockStrip</h2>
    <div>{''.join(_badge(lock, danger=True) for lock in locks)}</div>
  </section>

  <section class="OperationalTruthRail">
    <h2>OperationalTruthRail</h2>
    <div class="rail">{platform_cards}<article class="metric"><span>Review queue count</span><strong>{packet['reviewable_now_count']}</strong></article><article class="metric"><span>Blocker count</span><strong>{packet['blocked_live_dispatch_count']}</strong></article></div>
  </section>

  <section class="BlockerStack">
    <h2>BlockerStack</h2>
    <p><strong>Current truth:</strong> live dispatch blocked; local review shell only.</p>
    <p><strong>Future requirements:</strong> gates below remain unsatisfied and do not imply readiness.</p>
    <ul>{_blocker_rows(packet['blocked_live_dispatch_queue'])}</ul>
  </section>

  <section class="ContentLane">
    <h2>ContentLane</h2>
    <h3>Manual export queue</h3><div class="lane-grid">{_cards(packet['manual_export_queue'])}</div>
    <h3>X preview queue</h3><div class="lane-grid">{_cards(packet['x_preview_queue'])}</div>
    <h3>Telegram preview queue</h3><div class="lane-grid">{_cards(packet['telegram_preview_queue'])}</div>
    <h3>Blocked live dispatch queue</h3><ul>{_blocker_rows(packet['blocked_live_dispatch_queue'])}</ul>
  </section>

  <section class="AuditTable">
    <h2>AuditTable</h2>
    <table><thead><tr><th>Source stage</th><th>Checksum</th><th>Status</th></tr></thead><tbody>{_audit_rows(packet['audit_table'])}</tbody></table>
  </section>

  <section class="NextActionPanel">
    <h2>NextActionPanel</h2>
    <p><strong>Allowed local review actions:</strong> {_esc(', '.join(packet['allowed_review_only_actions']))}</p>
    <p><strong>Forbidden live/platform actions:</strong> {_esc(', '.join(packet['forbidden_actions']))}</p>
  </section>
</main>
</body>
</html>
"""
    policy.validate_no_forbidden_readiness_claims(html_text)
    policy.validate_no_forbidden_material(html_text)
    return html_text


def build_next_browser_qa_packet(shell_packet, policy_packet):
    packet = {
        "task_label": NEXT_BATCH_PROMPT,
        "model": "NEXT_COCKPIT_BROWSER_QA_0174YL_YM_YN",
        "model_version": "0174YL_YM_YN_NEXT_COCKPIT_BROWSER_QA_V1",
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **policy.safety_flags(),
        "next_batch_prompt": NEXT_BATCH_PROMPT,
        "next_scope": "browser_qa_for_local_cockpit_ui_shell_only",
        "allowed_inputs": ["cockpit_ui_shell_packet", "cockpit_ui_shell_html", "cockpit_ui_shell_fixture", "cockpit_ui_shell_policy_packet"],
        "forbidden_outputs": list(policy.FORBIDDEN_ACTIONS),
        "readiness_class": policy.READINESS_CLASS,
        "live_dispatch_status": policy.LIVE_DISPATCH_STATUS,
        "manual_export_status": policy.MANUAL_EXPORT_STATUS,
        "cockpit_ui_shell_checksum": shell_packet["cockpit_ui_shell_checksum"],
        "cockpit_ui_shell_policy_checksum": policy_packet["cockpit_ui_shell_policy_checksum"],
        "cockpit_ui_shell_fixture_checksum": shell_packet["cockpit_ui_shell_fixture_checksum"],
        "cockpit_ui_shell_html_checksum": shell_packet["html_checksum"],
        "rendered_shell_regions": list(shell_packet["rendered_shell_regions"]),
        "browser_qa_must_remain_local_only": True,
        "must_capture_screenshot_safe_static_html": True,
        "must_not_click_or_invent_live_actions": True,
        "status": "pass",
    }
    policy.validate_no_forbidden_readiness_claims(packet)
    policy.validate_no_forbidden_material(packet)
    packet["next_cockpit_browser_qa_packet_checksum"] = adapter.compute_checksum(packet)
    return packet


def render_doc(title, packet):
    lines = [f"# {title}", "", "> [!IMPORTANT]", "> Local cockpit UI shell only. Live dispatch remains blocked; APIs remain off.", ""]
    for key in sorted(packet):
        value = packet[key]
        if isinstance(value, list):
            value = f"{len(value)} items"
        elif isinstance(value, dict):
            value = json.dumps(value, sort_keys=True)
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def _assert_safe_output(repo_root, output_dir):
    root = pathlib.Path(repo_root).resolve()
    out = pathlib.Path(output_dir).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    if out != allowed:
        raise ValueError("unsafe_output_path_refused")
    return out


def write_artifacts(repo_root=".", output_dir=None):
    output_dir = output_dir or (pathlib.Path(repo_root) / DOC_REL_DIR)
    out = _assert_safe_output(repo_root, output_dir)
    out.mkdir(parents=True, exist_ok=True)
    policy_packet = policy.write_artifacts(repo_root)
    inputs = load_inputs(repo_root)
    fixture = build_fixture(inputs, policy_packet)
    pre_packet = build_shell_packet(inputs, policy_packet, fixture)
    html_text = render_html(pre_packet)
    html_checksum = adapter.compute_checksum({"html": html_text})
    shell_packet = build_shell_packet(inputs, policy_packet, fixture, html_checksum=html_checksum)
    next_packet = build_next_browser_qa_packet(shell_packet, policy_packet)
    (out / SHELL_PACKET).write_text(adapter.serialize(shell_packet), encoding="utf-8", newline="\n")
    (out / SHELL_DOC).write_text(render_doc("Cockpit UI Shell", shell_packet), encoding="utf-8", newline="\n")
    (out / SHELL_HTML).write_text(html_text, encoding="utf-8", newline="\n")
    (out / SHELL_FIXTURE).write_text(adapter.serialize(fixture), encoding="utf-8", newline="\n")
    (out / NEXT_QA_PACKET).write_text(adapter.serialize(next_packet), encoding="utf-8", newline="\n")
    (out / NEXT_QA_DOC).write_text(render_doc("Next Cockpit Browser QA", next_packet), encoding="utf-8", newline="\n")
    return copy.deepcopy({"shell": shell_packet, "policy": policy_packet, "fixture": fixture, "html": html_text, "next_packet": next_packet})


if __name__ == "__main__":
    result = write_artifacts(".")
    print("COCKPIT_UI_SHELL_CHECKSUM", result["shell"]["cockpit_ui_shell_checksum"])
    print("COCKPIT_UI_SHELL_POLICY_CHECKSUM", result["policy"]["cockpit_ui_shell_policy_checksum"])
    print("COCKPIT_UI_SHELL_FIXTURE_CHECKSUM", result["shell"]["cockpit_ui_shell_fixture_checksum"])
    print("COCKPIT_UI_SHELL_HTML_CHECKSUM", result["shell"]["html_checksum"])
    print("NEXT_COCKPIT_BROWSER_QA_PACKET_CHECKSUM", result["next_packet"]["next_cockpit_browser_qa_packet_checksum"])
