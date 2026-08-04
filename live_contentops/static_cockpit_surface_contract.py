"""Static cockpit surface contract (LOCAL HTML PREVIEW ONLY, NO DISPATCH)."""

import copy
import html
import json
import os.path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import static_cockpit_surface_policy as policy
from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174YI_YJ_YK_STATIC_COCKPIT_SURFACE_CONTRACT_V0"
MODEL = "STATIC_COCKPIT_SURFACE_CONTRACT_0174YI_YJ_YK"
MODEL_VERSION = "0174YI_YJ_YK_STATIC_COCKPIT_SURFACE_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "ebe0b3c9c792a6eb0c8a80b8b73d41a6538665a1"
DOC_REL_DIR = os.path.join("docs", "automation", "0174YI_YJ_YK")
SURFACE_PACKET = "static_cockpit_surface_packet.json"
SURFACE_HTML = "static_cockpit_surface.html"
FIXTURE_OUTPUTS = "static_cockpit_surface_fixture_outputs.json"
NEXT_PACKET = "next_cockpit_ui_shell_contract_packet.json"
SURFACE_DOC = "static_cockpit_surface.md"
NEXT_DOC = "next_cockpit_ui_shell_contract.md"
NEXT_BATCH_PROMPT = "TASK_CONTENTOPS_0174YL_YM_YN_COCKPIT_UI_SHELL_CONTRACT_V0"

PATHS = {
    "read_model": os.path.join("docs", "automation", "0174YF_YG_YH", "cockpit_read_model_packet.json"),
    "read_model_outputs": os.path.join("docs", "automation", "0174YF_YG_YH", "cockpit_read_model_fixture_outputs.json"),
    "read_model_policy": os.path.join("docs", "automation", "0174YF_YG_YH", "cockpit_read_model_policy_packet.json"),
    "next_static_surface": os.path.join("docs", "automation", "0174YF_YG_YH", "next_static_cockpit_surface_contract_packet.json"),
}

UPSTREAM_CHECKSUM_KEYS = {
    "cockpit_read_model_checksum": "read_model",
    "cockpit_read_model_fixture_outputs_checksum": "read_model",
    "cockpit_read_model_policy_checksum": "read_model_policy",
    "next_static_cockpit_surface_contract_checksum": "next_static_surface",
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
    return {name: _read_json(repo_root, rel_path) for name, rel_path in PATHS.items()}


def _small_item(item):
    return {
        "item_id": item["item_id"],
        "platform": item["platform"],
        "payload_class": item["payload_class"],
        "payload_hash": item["payload_hash"],
        "payload_hash_short": item.get("payload_hash_short", item["payload_hash"][:12]),
        "review_status": item.get("review_status"),
        "allowed_operator_action": item.get("allowed_operator_action", "hold"),
        "evidence_refs": list(item.get("evidence_refs", [])),
        "limitations": list(item.get("limitations", [])),
        "source_payload_id": item.get("source_payload_id"),
        "can_dispatch": False,
        "public_postable": False,
        "human_review_required": True,
        "no_financial_advice": True,
        "no_signal_language": True,
    }


def build_fixture_outputs(inputs):
    outputs = [_small_item(item) for item in inputs["read_model_outputs"]]
    for item in outputs:
        policy.validate_no_forbidden_readiness_claims(item)
        policy.validate_no_forbidden_material(item)
    return outputs


def _platform_cards(read_model):
    counts = read_model.get("platform_counts", {})
    return [
        {
            "platform": platform_name,
            "status": policy.PLATFORM_STATUSES[platform_name],
            "reviewable_count": counts.get(platform_name, 0),
            "can_dispatch": False,
            "allowed_operator_action": "hold" if counts.get(platform_name, 0) == 0 else "open_static_cockpit_surface_preview",
        }
        for platform_name in policy.PLATFORMS
    ]


def _upstream_checksums(inputs, policy_packet):
    checksums = {"static_cockpit_surface_policy_checksum": policy_packet["static_cockpit_surface_policy_checksum"]}
    for checksum_key, source_name in UPSTREAM_CHECKSUM_KEYS.items():
        checksums[checksum_key] = inputs[source_name][checksum_key]
    return checksums


def _evidence_index(inputs, policy_packet):
    return [
        {"stage": key, "checksum": checksum}
        for key, checksum in sorted(_upstream_checksums(inputs, policy_packet).items())
    ]


def _payload_hash_index(items):
    return [
        {
            "platform": item["platform"],
            "payload_class": item["payload_class"],
            "payload_hash": item["payload_hash"],
            "payload_hash_short": item["payload_hash_short"],
            "item_id": item["item_id"],
        }
        for item in items
    ]


def _queue(items, platform_name):
    return [item for item in items if item["platform"] == platform_name]


def build_surface_packet(inputs, policy_packet, fixture_outputs, html_checksum=None):
    read_model = inputs["read_model"]
    manual_export_queue = _queue(fixture_outputs, "substack")
    x_preview_queue = _queue(fixture_outputs, "x")
    telegram_preview_queue = _queue(fixture_outputs, "telegram")
    evidence_index = _evidence_index(inputs, policy_packet)
    packet = {
        "static_cockpit_surface_id": "static_cockpit_surface_0174YI_YJ_YK",
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **policy.safety_flags(),
        "readiness_class": policy.READINESS_CLASS,
        "local_governance_status": policy.LOCAL_GOVERNANCE_STATUS,
        "manual_export_status": policy.MANUAL_EXPORT_STATUS,
        "live_dispatch_status": policy.LIVE_DISPATCH_STATUS,
        "platform_cards": _platform_cards(read_model),
        "platform_statuses": copy.deepcopy(policy.PLATFORM_STATUSES),
        "operator_banner": "Local static cockpit preview. APIs off. Live dispatch blocked. Review-only queues visible.",
        "reviewable_now_count": len(fixture_outputs),
        "manual_export_queue_count": len(manual_export_queue),
        "x_preview_queue_count": len(x_preview_queue),
        "telegram_preview_queue_count": len(telegram_preview_queue),
        "blocked_live_dispatch_count": len(read_model.get("blocked_live_dispatch_queue", [])),
        "manual_export_queue": manual_export_queue,
        "x_preview_queue": x_preview_queue,
        "telegram_preview_queue": telegram_preview_queue,
        "blocked_live_dispatch_queue": read_model.get("blocked_live_dispatch_queue", []),
        "blocker_summary": copy.deepcopy(read_model.get("blocker_summary", {})),
        "payload_hash_index": _payload_hash_index(fixture_outputs),
        "evidence_index": evidence_index,
        "allowed_actions": list(policy.ALLOWED_ACTIONS),
        "forbidden_actions": list(policy.FORBIDDEN_ACTIONS),
        "required_future_gates": list(policy.REQUIRED_FUTURE_GATES),
        "next_operator_action": "open static cockpit surface preview, review queue, then copy Substack markdown only if Jim chooses manual export",
        "next_builder_task": NEXT_BATCH_PROMPT,
        "html_file": SURFACE_HTML,
        "html_checksum": html_checksum,
        "screenshot_safe_surface": True,
        "html_scripts_allowed": False,
        "html_forms_allowed": False,
        "external_assets_allowed": False,
        "evidence_refs": [entry["checksum"] for entry in evidence_index] + list(read_model.get("evidence_refs", [])),
        "no_live_behavior_proof": {**policy.safety_flags(), "proof": "pass_static_surface_no_live_no_api_no_network"},
        "no_forbidden_material_proof": "pass_no_scripts_forms_urls_credentials_raw_destination_env_secret_provider_output",
        "no_forbidden_readiness_claim_proof": "pass_no_forbidden_readiness_claims_in_static_surface",
        "status": "pass",
    }
    policy.validate_no_forbidden_readiness_claims(packet)
    policy.validate_no_forbidden_material(packet)
    packet["static_cockpit_surface_fixture_outputs_checksum"] = adapter.compute_checksum(fixture_outputs)
    packet["static_cockpit_surface_checksum"] = adapter.compute_checksum(packet)
    return packet


def _esc(value):
    return html.escape(str(value), quote=True)


def _item_cards(items):
    if not items:
        return '<p class="muted">No items.</p>'
    rows = []
    for item in items:
        rows.append(
            '<article class="queue-card">'
            f'<div class="hash">{_esc(item["payload_hash_short"])}</div>'
            f'<h3>{_esc(item["payload_class"])}</h3>'
            f'<p>{_esc(item.get("review_status", item.get("platform", "review_only")))}</p>'
            f'<p><strong>Action:</strong> {_esc(item.get("allowed_operator_action", "review_payload_hash"))}</p>'
            f'<p><strong>Payload hash:</strong> <code>{_esc(item["payload_hash"])}</code></p>'
            f'<p><strong>Dispatch:</strong> blocked · <strong>Public:</strong> false</p>'
            '</article>'
        )
    return "\n".join(rows)


def _list_items(values):
    return "\n".join(f"<li>{_esc(value)}</li>" for value in values) or '<li class="muted">None</li>'


def _evidence_rows(entries):
    return "\n".join(
        f'<tr><td>{_esc(entry["stage"])}</td><td><code>{_esc(entry["checksum"])}</code></td></tr>'
        for entry in entries
    )


def render_html(packet):
    blockers = packet.get("blocker_summary", {}).get("blocked_reasons", [])
    cards = "\n".join(
        f'<div class="status-card"><span>{_esc(card["platform"])}</span><strong>{_esc(card["status"])}</strong><em>{card["reviewable_count"]} reviewable</em></div>'
        for card in packet["platform_cards"]
    )
    html_text = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Local static cockpit preview for review-only ContentOps queues.">
  <title>Capital Chronicle Static Cockpit Preview</title>
  <style>
    :root {{ color-scheme: dark; --bg:#08111f; --panel:#101c30; --panel2:#16243b; --line:#29405f; --text:#eef5ff; --muted:#9fb2cc; --gold:#ffd166; --cyan:#68e1fd; --rose:#ff6b8b; --green:#7ee787; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:Inter,Segoe UI,Arial,sans-serif; background:radial-gradient(circle at top left,#223b68 0,#08111f 34%,#050914 100%); color:var(--text); }}
    main {{ width:min(1180px,calc(100% - 32px)); margin:0 auto; padding:32px 0 48px; }}
    header {{ border:1px solid var(--line); border-radius:28px; padding:28px; background:linear-gradient(135deg,rgba(104,225,253,.18),rgba(255,209,102,.10)); box-shadow:0 24px 80px rgba(0,0,0,.35); }}
    h1 {{ margin:0 0 10px; font-size:clamp(32px,5vw,64px); letter-spacing:-.05em; }}
    h2 {{ margin:0 0 18px; font-size:26px; }}
    h3 {{ margin:8px 0; }}
    section {{ margin-top:24px; padding:22px; border:1px solid var(--line); border-radius:24px; background:rgba(16,28,48,.82); }}
    .banner {{ display:inline-flex; gap:10px; flex-wrap:wrap; margin-top:16px; }}
    .pill {{ border:1px solid var(--line); border-radius:999px; padding:8px 12px; background:rgba(255,255,255,.06); color:var(--cyan); font-weight:700; }}
    .pill.blocked {{ color:var(--rose); }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:16px; }}
    .status-card,.queue-card {{ border:1px solid var(--line); border-radius:20px; padding:16px; background:linear-gradient(180deg,var(--panel2),var(--panel)); }}
    .status-card span {{ display:block; color:var(--muted); text-transform:uppercase; letter-spacing:.16em; font-size:12px; }}
    .status-card strong {{ display:block; color:var(--gold); margin:8px 0; }}
    .status-card em {{ color:var(--green); font-style:normal; }}
    .queue-card .hash {{ color:var(--cyan); font-family:ui-monospace,Consolas,monospace; }}
    code {{ color:var(--cyan); overflow-wrap:anywhere; }}
    table {{ width:100%; border-collapse:collapse; }}
    th,td {{ text-align:left; padding:10px; border-bottom:1px solid var(--line); vertical-align:top; }}
    .muted {{ color:var(--muted); }}
    .next {{ font-size:20px; color:var(--gold); }}
  </style>
</head>
<body>
<main>
  <header>
    <p class="muted">Capital Chronicle ContentOps</p>
    <h1>Static Cockpit Preview</h1>
    <p>{_esc(packet["operator_banner"])}</p>
    <div class="banner">
      <span class="pill">Local only</span>
      <span class="pill">No API</span>
      <span class="pill blocked">Live dispatch blocked</span>
      <span class="pill">Reviewable: {packet["reviewable_now_count"]}</span>
    </div>
  </header>

  <section>
    <h2>Platform status</h2>
    <div class="grid">{cards}</div>
  </section>

  <section>
    <h2>Manual export queue</h2>
    <div class="grid">{_item_cards(packet["manual_export_queue"])}</div>
  </section>

  <section>
    <h2>X preview queue</h2>
    <div class="grid">{_item_cards(packet["x_preview_queue"])}</div>
  </section>

  <section>
    <h2>Telegram preview queue</h2>
    <div class="grid">{_item_cards(packet["telegram_preview_queue"])}</div>
  </section>

  <section>
    <h2>Blocked live dispatch</h2>
    <ul>{_list_items(blockers)}</ul>
  </section>

  <section>
    <h2>Payload hashes</h2>
    <div class="grid">{_item_cards(packet["payload_hash_index"])}</div>
  </section>

  <section>
    <h2>Evidence index</h2>
    <table><thead><tr><th>Stage</th><th>Checksum</th></tr></thead><tbody>{_evidence_rows(packet["evidence_index"])}</tbody></table>
  </section>

  <section>
    <h2>Next safe operator action</h2>
    <p class="next">{_esc(packet["next_operator_action"])}</p>
  </section>
</main>
</body>
</html>
"""
    policy.validate_no_forbidden_readiness_claims(html_text)
    policy.validate_no_forbidden_material(html_text)
    return html_text


def build_next_packet(surface_packet, policy_packet):
    packet = {
        "task_label": NEXT_BATCH_PROMPT,
        "model": "NEXT_COCKPIT_UI_SHELL_CONTRACT_0174YI_YJ_YK",
        "model_version": "0174YI_YJ_YK_NEXT_COCKPIT_UI_SHELL_CONTRACT_V1",
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **policy.safety_flags(),
        "next_batch_prompt": NEXT_BATCH_PROMPT,
        "next_scope": "cockpit_ui_shell_local_only_from_static_surface",
        "allowed_inputs": ["static_cockpit_surface_packet", "static_cockpit_surface_html", "static_cockpit_surface_policy_packet"],
        "forbidden_outputs": list(policy.FORBIDDEN_ACTIONS) + ["live_state_creation"],
        "readiness_class": policy.READINESS_CLASS,
        "manual_export_status": policy.MANUAL_EXPORT_STATUS,
        "live_dispatch_status": policy.LIVE_DISPATCH_STATUS,
        "static_cockpit_surface_checksum": surface_packet["static_cockpit_surface_checksum"],
        "static_cockpit_surface_policy_checksum": policy_packet["static_cockpit_surface_policy_checksum"],
        "static_cockpit_surface_fixture_outputs_checksum": surface_packet["static_cockpit_surface_fixture_outputs_checksum"],
        "static_cockpit_surface_html_checksum": surface_packet["html_checksum"],
        "ui_shell_must_remain_local_only": True,
        "status": "pass",
    }
    policy.validate_no_forbidden_readiness_claims(packet)
    policy.validate_no_forbidden_material(packet)
    packet["next_cockpit_ui_shell_contract_checksum"] = adapter.compute_checksum(packet)
    return packet


def render_doc(title, packet):
    lines = [f"# {title}", "", "> [!IMPORTANT]", "> Static cockpit preview only. Live dispatch remains blocked; APIs remain off.", ""]
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
    fixture_outputs = build_fixture_outputs(inputs)
    pre_packet = build_surface_packet(inputs, policy_packet, fixture_outputs)
    html_text = render_html(pre_packet)
    html_checksum = adapter.compute_checksum({"html": html_text})
    surface_packet = build_surface_packet(inputs, policy_packet, fixture_outputs, html_checksum=html_checksum)
    next_packet = build_next_packet(surface_packet, policy_packet)
    (out / SURFACE_PACKET).write_text(adapter.serialize(surface_packet), encoding="utf-8", newline="\n")
    (out / SURFACE_HTML).write_text(html_text, encoding="utf-8", newline="\n")
    (out / FIXTURE_OUTPUTS).write_text(adapter.serialize(fixture_outputs), encoding="utf-8", newline="\n")
    (out / NEXT_PACKET).write_text(adapter.serialize(next_packet), encoding="utf-8", newline="\n")
    (out / SURFACE_DOC).write_text(render_doc("Static Cockpit Surface", surface_packet), encoding="utf-8", newline="\n")
    (out / NEXT_DOC).write_text(render_doc("Next Cockpit UI Shell Contract", next_packet), encoding="utf-8", newline="\n")
    return copy.deepcopy({"surface": surface_packet, "policy": policy_packet, "fixture_outputs": fixture_outputs, "html": html_text, "next_packet": next_packet})


if __name__ == "__main__":
    result = write_artifacts(".")
    print("STATIC_COCKPIT_SURFACE_CHECKSUM", result["surface"]["static_cockpit_surface_checksum"])
    print("STATIC_COCKPIT_SURFACE_POLICY_CHECKSUM", result["policy"]["static_cockpit_surface_policy_checksum"])
    print("STATIC_COCKPIT_SURFACE_FIXTURE_OUTPUTS_CHECKSUM", result["surface"]["static_cockpit_surface_fixture_outputs_checksum"])
    print("STATIC_COCKPIT_SURFACE_HTML_CHECKSUM", result["surface"]["html_checksum"])
    print("NEXT_COCKPIT_UI_SHELL_CONTRACT_CHECKSUM", result["next_packet"]["next_cockpit_ui_shell_contract_checksum"])
