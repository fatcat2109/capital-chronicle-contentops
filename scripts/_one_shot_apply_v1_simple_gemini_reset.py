from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

RESET_BRANCH = "agent/web-v1-simple-gemini-runtime-reset"

EXPECTED_BLOBS = {
    "AGENTS.md": "92a2559c2ca8419dd14faa951a3f9da2cfb8b0b2",
    ".github/workflows/ci-fast.yml": "4e86e52fa5ce48bc3b5e31bdb863181b8d1ca4fd",
    "docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md": "25731ebad42880617e772e29404c9de7ba44fe65",
    "docs/automation/CONTENTOPS_FINAL_DAILY_APP_V1_CURRENT_EXECUTION_POINTER_V3.md": "a33797a17b3230d6581e26b2bf036a5ee985f897",
    "docs/automation/CODEX_DESKTOP_V1_NEWSROOM_OPERATOR.md": "6e4f46c6aeea8dc63c11f0b30534a3ba7d14c3ae",
    "docs/codegraph/V1_CONTEXT.md": "be7683964a5a011430540022ae865272978aba12",
    "live_contentops/codex_desktop_newsroom_operator_v1.py": "bf4a03a1115da2a983a295e780a112a958b59d0b",
    "live_contentops/newsroom_production_day_v1.py": "5db98f5f90a156ac5e6b7fa61dd95b8d5ca18784",
    "live_contentops/nine_router_llm_seam_v2.py": "1c56cd1ed4daa5e00ac010bb1beba4ee37cd5666",
    "live_contentops/nine_router_ordered_model_router_v2.py": "cd64e7090ff5f0b?",
    "live_contentops/production_orchestrator_v1.py": "f0e8f4b809a95dd9ce4e036a9366e435bb9d81f8",
    "tests/test_nine_router_ordered_model_router_v2.py": "f9af3cfd033b71e16f278d92ac446a86f0da31c9",
}

# Correct the only intentionally human-visible placeholder above before any mutation. This is
# kept as a code assertion rather than silently accepting a typo in the expected identity.
EXPECTED_BLOBS["live_contentops/nine_router_ordered_model_router_v2.py"] = (
    "cd64e7090ff7cfe00bb0a14691cb13f9404e7f21"
)


def run(*args: str) -> str:
    return subprocess.check_output(args, text=True).strip()


def assert_exact_checkout() -> None:
    branch = run("git", "branch", "--show-current")
    if branch != RESET_BRANCH:
        raise SystemExit(f"wrong_branch:{branch}")
    for path, expected in EXPECTED_BLOBS.items():
        actual = run("git", "hash-object", path)
        if actual != expected:
            raise SystemExit(f"blob_drift:{path}:{actual}:{expected}")


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"replace_count_invalid:{path}:{count}:{old[:80]}")
    write(path, text.replace(old, new, 1))


def replace_between(path: str, start: str, end: str, replacement: str) -> None:
    text = read(path)
    start_index = text.find(start)
    end_index = text.find(end, start_index + len(start))
    if start_index < 0 or end_index < 0:
        raise SystemExit(f"replace_between_marker_missing:{path}:{start}:{end}")
    write(path, text[:start_index] + replacement + text[end_index:])


def append_before(path: str, marker: str, addition: str) -> None:
    text = read(path)
    index = text.find(marker)
    if index < 0:
        raise SystemExit(f"append_marker_missing:{path}:{marker}")
    write(path, text[:index] + addition + text[index:])


def patch_simple_runtime() -> None:
    path = "live_contentops/v1_simple_gemini_newsroom_v1.py"
    old = '''def _source_pack(documents: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:\n    pack: list[dict[str, Any]] = []\n    for index, document in enumerate(documents[:MAX_SOURCE_DOCUMENTS], start=1):\n        url = str(document.get("reader_source_url") or document.get("source_url") or "")\n        text = str(document.get("canonical_content_text") or "")\n        if not url.startswith("https://") or len(text.strip()) < 40:\n            continue\n        pack.append(\n            {\n                "source_id": f"SOURCE_{index}",\n'''
    new = '''def _source_pack(documents: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:\n    pack: list[dict[str, Any]] = []\n    for document in documents[:MAX_SOURCE_DOCUMENTS]:\n        url = str(document.get("reader_source_url") or document.get("source_url") or "")\n        text = str(document.get("canonical_content_text") or "")\n        if not url.startswith("https://") or len(text.strip()) < 40:\n            continue\n        source_id = f"SOURCE_{len(pack) + 1}"\n        pack.append(\n            {\n                "source_id": source_id,\n'''
    replace_once(path, old, new)


def patch_qualified_record_helper() -> None:
    path = "live_contentops/newsroom_production_day_v1.py"
    helper = '''def build_current_zero_write_qualified_article_record(\n    *,\n    production_day_id: str,\n    parent_window_id: str,\n    attempt_run_id: str,\n    article: Mapping[str, Any],\n    story_identity: str,\n    update_chain_identity: str,\n    resolved_article_mode: str,\n    accepted_evidence_documents: Sequence[Mapping[str, Any]],\n    editorial_provider: str,\n    editorial_model: str,\n    editorial_reasoning_effort: str,\n    logical_model_invocation_count: int,\n    derivative_package_intents: Sequence[Mapping[str, Any]],\n) -> dict[str, Any]:\n    """Build the current provider-neutral zero-write qualification record.\n\n    The historical qualifier above remains exact evidence for the native Desktop era. New V1\n    production uses this provider-neutral builder so runtime truth records the real 9Router/Gemini\n    author instead of fabricating a Codex receipt. Public-write authority remains zero.\n    """\n    body = str(article.get("substack_body_markdown") or "").strip()\n    title = str(article.get("title") or "").strip()\n    provider = str(editorial_provider or "").strip()\n    model = str(editorial_model or "").strip()\n    effort = str(editorial_reasoning_effort or "").upper()\n    intents = [dict(row) for row in derivative_package_intents if isinstance(row, Mapping)]\n    required = tuple(str(value) for value in V1_REQUIRED_DERIVATIVE_DESTINATIONS)\n    blockers: list[str] = []\n    if not body or not title:\n        blockers.append("article_body_or_title_missing")\n    if provider != "9router":\n        blockers.append("current_v1_editorial_provider_not_9router")\n    if not model.startswith("vx/gemini-"):\n        blockers.append("current_v1_editorial_model_not_authorized_gemini")\n    if effort != "HIGH":\n        blockers.append("current_v1_editorial_reasoning_effort_not_high")\n    if int(logical_model_invocation_count) not in {2, 3}:\n        blockers.append("current_v1_logical_model_invocation_count_invalid")\n    if len(intents) != 8 or {str(row.get("destination") or "") for row in intents} != set(required):\n        blockers.append("exactly_eight_derivative_intents_required")\n    if any(str(row.get("dispatch_state") or "") != "UNDISPATCHED" for row in intents):\n        blockers.append("derivative_intent_dispatch_state_invalid")\n    evidence_rows = [dict(row) for row in accepted_evidence_documents if isinstance(row, Mapping)]\n    evidence_ids = sorted({\n        str(row.get("document_id") or row.get("source_url") or "")\n        for row in evidence_rows\n        if str(row.get("document_id") or row.get("source_url") or "")\n    })\n    if not evidence_ids:\n        blockers.append("accepted_evidence_identity_missing")\n    article_identity = hashlib.sha256(body.encode("utf-8")).hexdigest() if body else ""\n    evidence_material = [\n        {\n            "document_id": str(row.get("document_id") or ""),\n            "source_url": str(row.get("source_url") or ""),\n            "canonical_content_sha256": str(row.get("canonical_content_sha256") or ""),\n            "published_at_utc": str(row.get("published_at_utc") or ""),\n            "published_at_source": str(row.get("published_at_source") or ""),\n        }\n        for row in evidence_rows\n    ]\n    record_core = {\n        "schema_version": "contentops.newsroom_qualified_article.v1",\n        "newsroom_production_day_id": str(production_day_id),\n        "parent_window_id": str(parent_window_id),\n        "attempt_run_id": str(attempt_run_id),\n        "article_identity": article_identity,\n        "story_identity": str(story_identity),\n        "update_chain_identity": str(update_chain_identity),\n        "title": title,\n        "resolved_article_mode": str(resolved_article_mode),\n        "article_path": None,\n        "article_body_sha256": article_identity,\n        "accepted_evidence_ids": evidence_ids,\n        "accepted_evidence_sha256": _logical_hash(evidence_material),\n        "editorial_worker": {\n            "provider": provider,\n            "model": model,\n            "reasoning_effort": effort,\n            "logical_model_invocation_count": int(logical_model_invocation_count),\n            "codex_runtime_model_call_count": 0,\n            "public_write_attempted": False,\n        },\n        "derivative_package_intents": intents,\n        "derivative_package_intent_count": 8,\n        "public_write_performed": False,\n        "unknown_write_count": 0,\n        "qualification_blockers": sorted(set(blockers)),\n        "qualified": not blockers,\n    }\n    return {**record_core, "record_sha256": _logical_hash(record_core)}\n\n\n'''
    append_before(path, "def persist_qualified_article_record", helper)


def patch_orchestrator() -> None:
    path = "live_contentops/production_orchestrator_v1.py"
    replace_once(
        path,
        '        "run_rolling_x_newsroom_cycle",\n',
        '        "run_rolling_x_newsroom_cycle",\n        "run_v1_simple_gemini_newsroom",\n',
    )
    replace_once(
        path,
        '        "run_rolling_x_newsroom_cycle": _operation_contract(restart_mode=RECONCILIATION_REQUIRED, capability="LIVE_CAPABLE"),\n',
        '        "run_rolling_x_newsroom_cycle": _operation_contract(restart_mode=RECONCILIATION_REQUIRED, capability="LIVE_CAPABLE"),\n        "run_v1_simple_gemini_newsroom": _operation_contract(restart_mode=RESTART_SAFE, capability="MODEL_ASSISTED_ZERO_WRITE"),\n',
    )
    method = '''    def _dispatch_operation(self, operation: str, **kwargs: Any) -> Any:\n        if operation == "run_v1_simple_gemini_newsroom":\n            module = import_module("live_contentops.v1_simple_gemini_newsroom_v1")\n            runner = getattr(module, "run_v1_simple_gemini_newsroom")\n            if not callable(runner):\n                raise TypeError("v1_simple_gemini_newsroom_runner_not_callable")\n            return runner(**kwargs)\n        return self._resolve_dispatcher()(operation, **kwargs)\n\n'''
    append_before(path, "    def execute(self, operation: str, **kwargs: Any) -> Any:\n", method)
    replace_once(
        path,
        '        if active_store is None:\n            return self._resolve_dispatcher()(operation, **kwargs)\n',
        '        if active_store is None:\n            return self._dispatch_operation(operation, **kwargs)\n',
    )
    replace_once(
        path,
        '            result = self._resolve_dispatcher()(operation, **kwargs)\n',
        '            result = self._dispatch_operation(operation, **kwargs)\n',
    )


def patch_router_authority() -> None:
    seam = "live_contentops/nine_router_llm_seam_v2.py"
    replace_once(
        seam,
        '            ROLE_ARTICLE_WRITING: (\n                "legacy zero-write article compatibility; publication-qualified articles "\n                "use a native Codex Desktop HIGH worker"\n            ),\n',
        '            ROLE_ARTICLE_WRITING: (\n                "current V1 simple Gemini canonical article writing after bounded selected-story retrieval"\n            ),\n',
    )
    replace_once(
        seam,
        '        "v1_gemini_only_model_authority": True,\n',
        '        "v1_gemini_only_model_authority": True,\n        "v1_simple_gemini_runtime_primary": True,\n        "codex_runtime_model_calls_required": False,\n',
    )

    router = "live_contentops/nine_router_ordered_model_router_v2.py"
    replace_once(
        router,
        '#: Current V1 can reach only these two exact 9Router models.  The router never parses,\n#: normalises, or "corrects" an authority entry.  Final editorial prose remains a native\n#: Codex Desktop XHIGH responsibility; this pool is semantic/review assistance only.\n',
        '#: Current V1 routine editorial production reaches only these two exact 9Router Gemini\n#: models. The router never parses, normalises, or silently substitutes an authority entry.\n#: Codex Desktop is builder/debugger/host-proof capacity, not a routine article model.\n',
    )
    replace_once(
        router,
        '    # Legacy zero-write writer compatibility only.  A publication-qualified article is\n    # authored by a fresh native Codex Desktop XHIGH worker, never by 9Router.\n    ARTICLE_WRITING_ROLE: ARTICLE_WRITING_MODEL_POOL,\n',
        '    # Current simple V1 article writing uses this bounded Gemini pool.\n    ARTICLE_WRITING_ROLE: ARTICLE_WRITING_MODEL_POOL,\n',
    )
    replace_once(
        router,
        '        "article_writing_via_9router_is_legacy_zero_write_compatibility_only": True,\n        "publication_qualified_article_uses_native_codex_desktop_xhigh": True,\n',
        '        "article_writing_via_9router_is_legacy_zero_write_compatibility_only": False,\n        "publication_qualified_article_uses_native_codex_desktop_xhigh": False,\n        "publication_qualified_article_uses_9router_gemini": True,\n        "codex_runtime_model_calls_required": False,\n',
    )

    test = "tests/test_nine_router_ordered_model_router_v2.py"
    replace_once(
        test,
        'def test_authority_packet_is_permanent_gemini_only_and_preserves_native_xhigh_boundary() -> None:\n',
        'def test_authority_packet_is_permanent_gemini_only_and_owns_current_article_path() -> None:\n',
    )
    replace_once(
        test,
        '    assert packet["publication_qualified_article_uses_native_codex_desktop_xhigh"] is True\n',
        '    assert packet["publication_qualified_article_uses_native_codex_desktop_xhigh"] is False\n    assert packet["publication_qualified_article_uses_9router_gemini"] is True\n    assert packet["codex_runtime_model_calls_required"] is False\n',
    )


def patch_codex_noop() -> None:
    path = "live_contentops/codex_desktop_newsroom_operator_v1.py"
    replacement = '''DESKTOP_TASK_PROMPT = (\n    "SUPERSEDED_CODEX_NEWSROOM_AUTOMATION_NOOP. Read fresh repository authority. Routine V1 "\n    "article production is owned by ContentOps local state + 9Router/Gemini through the canonical "\n    "run_v1_simple_gemini_newsroom operation. If this legacy Codex Automation fires, do not run "\n    "newsroom production, do not spawn an editorial worker, do not edit repository files, do not "\n    "run tests or CodeGraph, do not create or update a PR, and do not perform any public/provider "\n    "write. Record a sanitized SUPERSEDED_CODEX_NEWSROOM_AUTOMATION_NOOP result and exit. "\n    "UNKNOWN_WRITE remains STOP RETRY -> READ BACK -> RECONCILE."\n)\nMANUAL_GO_PROMPT = (\n    "SUPERSEDED_CODEX_NEWSROOM_AUTOMATION_NOOP. Manual GO no longer invokes routine V1 production "\n    "through Codex Desktop. Use the current simple Gemini runtime or a separately scoped builder/"\n    "host-proof task. Zero public write."\n)\n\n\n'''
    replace_between(path, "DESKTOP_TASK_PROMPT = (", "def four_task_setup_packet", replacement)


def patch_authority_docs() -> None:
    reset_doc = '''# ContentOps V1 Simple Gemini Runtime Reset V1\n\nAuthority date: 2026-08-27\nStatus: `CURRENT_V1_EXECUTION_AUTHORITY`\n\nThis owner-approved reset supersedes routine Codex Desktop newsroom production and the legacy\nevidence-ready/split-phase worker critical path. Historical artifacts remain valid evidence; they\ndo not route current execution.\n\n## Current V1 routine path\n\n```text\ncurrent headline sidecars + published memory + optional read-only CC context\n-> one bounded 9Router/Gemini story-selection invocation\n-> deterministic selected-story public retrieval only (maximum 6 requests)\n-> one bounded 9Router/Gemini article-writing invocation\n-> deterministic material-claim/source-byte validation\n-> at most one bounded 9Router/Gemini revision\n-> one qualified zero-write canonical article record\n-> exactly eight UNDISPATCHED derivative intents\n-> separate existing DurablePublicationCoordinator only after explicit public-write authority\n```\n\nNormal success uses two logical model invocations. Three is the absolute ceiling when the one\nrevision is needed. Each logical invocation is bounded to the two authorized Gemini routes and no\nsame-model retry. Codex runtime model calls required: `0`.\n\nThe reset intentionally removes from the routine critical path: broad evidence-ready pools,\nsemantic leaf/global checkpoint replay, native PREPARE/COMPLETE worker handoffs, deficit-driven\nmulti-candidate catch-up inside one scheduled task, and any scheduled Codex repo building/debugging.\n\n`BoundedPublicSecondaryEvidenceLoader` remains the deterministic source-byte authority for the\nselected story. 9Router has no native web-search/citation authority. Model-provided source\ntimestamps are not authority. Every material fact, number, quote, or causal claim must bind to\nretrieved source bytes. Proprietary Capital Chronicle forecast/probability/scenario/regime/numeric\nclaims remain unavailable in this initial reset lane unless exact publication-authorized CC\nauthority is added later.\n\nSubstack remains canonical and the eight derivative destinations remain Telegram, Discord, X,\nLinkedIn, Facebook Page, Instagram Business, Threads, and YouTube Community. The reset produces\nintent only; it grants no public write. The existing publication coordinator remains the sole\npublic-write owner and `UNKNOWN_WRITE = STOP RETRY -> READ BACK -> RECONCILE`.\n\n## Reuse / supersession\n\n- PR #19 locator/retrieval primitives: `CURRENTLY_PROVEN_AND_REUSE` as selected-story donor only.\n- PR #20 article/package proof: `CURRENTLY_PROVEN_AND_REUSE`.\n- PR #29 material-claim/validate-after concepts: `CURRENTLY_PROVEN_AND_REUSE` as verifier donor.\n- PR #30 native split-phase redesign: `SUPERSEDED_DO_NOT_REUSE` for routing; host evidence remains valid.\n- PR #31 legacy resume/revision repair: `SUPERSEDED_DO_NOT_REUSE` for routing; runtime evidence remains valid.\n- Codex Desktop: builder/debugger/host-proof capacity only, second-last execution lane.\n\n## Acceptance sequence\n\n1. Static implementation and exact-head CI.\n2. One isolated zero-write host canary using current real sidecars and 9Router.\n3. Inspect the real article, source/claim bindings, model/request economics, and eight intents.\n4. Only after that proof, bind the same CLI/runtime operation to a lightweight local scheduler.\n5. Public-write enablement/readback remains a separate owner-gated step.\n\nFinal target remains 5–8 useful published articles per newsroom production day without filler.\n'''
    write("docs/automation/CONTENTOPS_V1_SIMPLE_GEMINI_RUNTIME_RESET_V1.md", reset_doc)

    operator_doc = '''# Codex Desktop V1 Newsroom Operator\n\nAuthority date: 2026-08-27\nStatus: `SUPERSEDED_FOR_ROUTINE_V1_PRODUCTION`\n\nCodex Desktop no longer owns routine V1 story selection, article writing, revision, scheduling, or\npublication. Current routine authority is `CONTENTOPS_V1_SIMPLE_GEMINI_RUNTIME_RESET_V1.md` and\n`run_v1_simple_gemini_newsroom`.\n\nThe four historical native newsroom Automation objects and their PREPARE/COMPLETE evidence remain\nvalid provenance. They must remain paused/disabled and must not be used as routine production\ninvocation. If a stale object fires, the canonical prompt is a zero-write NOOP. A scheduled\nnewsroom task must never edit code, run tests, regenerate CodeGraph, create/update PRs, or debug the\nrepository.\n\nCodex Desktop remains available only for bounded builder/debugger/Windows-host proof work after\nGitHub Connector/CI cannot produce the required evidence. Current ContentOps Codex reasoning\nceiling remains HIGH. No Codex path grants factual, numeric, CC, permission, or public-write\nauthority.\n\nHistorical native split-phase APIs may remain for compatibility and evidence archaeology; they are\nnot current routine routing. Do not create a fifth newsroom Automation.\n\n`UNKNOWN_WRITE = STOP RETRY -> READ BACK -> RECONCILE`.\n'''
    write("docs/automation/CODEX_DESKTOP_V1_NEWSROOM_OPERATOR.md", operator_doc)

    pointer = '''# Capital Chronicle ContentOps — V1 Current Execution Pointer V3\n\nAuthority date: 2026-08-27\nStatus: `CURRENT_V1_LANE_POINTER / SIMPLE_GEMINI_RUNTIME_RESET`\n\n## Current route\n\nRead `AGENTS.md`, the current authority map, North Star/Master Plan, then\n`docs/automation/CONTENTOPS_V1_SIMPLE_GEMINI_RUNTIME_RESET_V1.md`.\n\nCurrent routine execution is:\n\n`current sidecars/published memory -> one Gemini selection -> <=6 deterministic selected-story\nsource requests -> one Gemini writer -> deterministic claim/source validation -> optional one\nGemini revision -> one zero-write qualified article -> exactly eight undispatched intents`.\n\nCodex runtime model calls are zero. Public writes are zero. The existing publication coordinator\nremains the sole later public-write owner.\n\n## Reuse truth\n\nPR #19 selected-story locator/retrieval primitives, PR #20 article/package proof, and PR #29\nvalidate-after/material-claim concepts remain reusable. PR #30 and PR #31 are superseded as current\nrouting; their historical host/runtime evidence remains valid. Do not merge them into the reset.\nThe historical native Desktop Automation route is superseded and its objects must remain off.\n\n`PRODUCTION_QUOTA_ECONOMICS_NOT_ACCEPTED` still applies to the old broad discovery default. A\nselected story with no reachable trustworthy source may truthfully abstain as\n`SOURCE_DISCOVERY_REQUIRED`/source retrieval blocked; the runtime must not manufacture filler.\n\n## Exact next gate\n\n`CURRENT_HOST_RUNTIME_PROOF_REQUIRED`: run one isolated zero-write current-source canary of the\nsimple Gemini operation and inspect the real article, source bytes, claim bindings, request/model\neconomics, and eight derivative intents. If that passes, bind the same operation to a lightweight\nlocal scheduler. Do not reintroduce Codex Automation as the newsroom. Public-write/readback remains\na separate owner gate.\n\nFinal V1 target remains `5–8/day` useful published articles without filler.\n'''
    write("docs/automation/CONTENTOPS_FINAL_DAILY_APP_V1_CURRENT_EXECUTION_POINTER_V3.md", pointer)

    agents = "AGENTS.md"
    replace_once(
        agents,
        '7. `docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md`\n8. `docs/codegraph/V1_CONTEXT.md` or `docs/codegraph/V2_CONTEXT.md`\n9. current lane pointer\n10. nearest scoped `AGENTS.md`\n11. exact current implementation/tests/evidence.\n',
        '7. `docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md`\n8. `docs/automation/CONTENTOPS_V1_SIMPLE_GEMINI_RUNTIME_RESET_V1.md` for V1 work\n9. `docs/codegraph/V1_CONTEXT.md` or `docs/codegraph/V2_CONTEXT.md`\n10. current lane pointer\n11. nearest scoped `AGENTS.md`\n12. exact current implementation/tests/evidence.\n',
    )
    section6 = '''## 6. Current V1 execution architecture\n\nCurrent owner-approved routine V1 is `SIMPLE_GEMINI_RUNTIME`: ContentOps local state and current\nheadline sidecars feed one bounded 9Router/Gemini selection; deterministic selected-story public\nretrieval performs at most six requests; one bounded Gemini writer returns the canonical article\nand exact material-claim bindings; deterministic validation checks retrieved bytes; at most one\nGemini revision may run; then one qualified zero-write article record and exactly eight\nUNDISPATCHED derivative intents are persisted. Normal model count is two logical invocations and\nthree is the hard ceiling with revision. Codex runtime model calls required: zero.\n\nThis supersedes routine Desktop Automations, SDK/App-Server editorial fallback, broad evidence-ready\npools, split-phase PREPARE/COMPLETE worker handoffs, and deficit-driven multi-candidate catch-up as\nthe production critical path. Those capabilities/evidence remain historical and may be inspected,\nbut they do not route current V1. The four old native newsroom Automation objects must remain off;\nif one fires it is a zero-write NOOP. A scheduled newsroom task may never edit repository code, run\ntests, regenerate CodeGraph, open/update PRs, or become a builder/debugger. Codex Desktop remains\nsecond-last builder/debugger/host-proof capacity only.\n\nThe existing deterministic source loader, qualified-record schema, destination registry, durable\npublication coordinator, strict readback/reconciliation, UI, and Capital Chronicle authority\nboundaries remain reusable. 9Router model output has zero factual, numeric, CC, permission, rights,\nor public-write authority. The current simple lane does not authorize proprietary CC numeric/\nforecast/probability/scenario/regime claims. Public publication remains a separate owner gate.\n\nThe exact current detail is `docs/automation/CONTENTOPS_V1_SIMPLE_GEMINI_RUNTIME_RESET_V1.md`.\n\n'''
    replace_between(agents, "## 6. Current V1 execution architecture", "## 7. ContentOps/Core Analyzer boundary", section6)
    section11 = '''## 11. Locked current sequence\n\nAccepted donor capabilities are not rebuilt: current headline ingestion, published-memory/dedupe,\nPR #19 selected-story locator/retrieval primitives, PR #20 article/package proof, PR #29\nvalidate-after/material-claim concepts, production-day accounting, destination registry, durable\npublication/readback/reconciliation, and V5 read model/UI. PR #30 and PR #31 are historical evidence\nonly and `SUPERSEDED_DO_NOT_REUSE` for current routing.\n\nCurrent progression order:\n\n1. land the simple Gemini zero-write runtime through exact-head CI;\n2. prove one current real-sidecar article in an isolated zero-write host canary;\n3. inspect actual article quality, source/claim bindings, <=6 source requests, <=3 logical Gemini\n   invocations, exactly eight undispatched intents, and zero Codex runtime calls;\n4. only after that PASS, schedule the same local operation with a lightweight non-Codex scheduler;\n5. obtain separate public-write/readback authority;\n6. then measure and optimize toward 5–8 useful published articles/day without filler.\n\n`V1_FINAL_PRODUCT_ACCEPTED` remains forbidden until the explicit owner gate is granted.\n\n'''
    replace_between(agents, "## 11. Locked current sequence", "## 12. Change discipline", section11)

    authority = "docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md"
    replace_once(
        authority,
        '7. `docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md`\n8. `docs/codegraph/V1_CONTEXT.md` or `docs/codegraph/V2_CONTEXT.md`\n9. current lane pointer\n10. nearest scoped `AGENTS.md`\n11. exact current code/tests/evidence/host truth.\n',
        '7. `docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md`\n8. `docs/automation/CONTENTOPS_V1_SIMPLE_GEMINI_RUNTIME_RESET_V1.md` for V1\n9. `docs/codegraph/V1_CONTEXT.md` or `docs/codegraph/V2_CONTEXT.md`\n10. current lane pointer\n11. nearest scoped `AGENTS.md`\n12. exact current code/tests/evidence/host truth.\n',
    )
    current_override = '''## 2026-08-27 V1 simple-Gemini architecture reset\n\nJim explicitly approved a routine V1 architecture reset. `CONTENTOPS_V1_SIMPLE_GEMINI_RUNTIME_RESET_V1.md`\nis current V1 execution authority and supersedes any later Desktop-primary, SDK-editorial-fallback,\nevidence-ready-pool, or native PREPARE/COMPLETE routing language in this file. Routine V1 now uses\n9Router/Gemini for one selected story and one article, deterministic selected-story retrieval with\na six-request ceiling, deterministic material-claim validation, and at most one Gemini revision.\nCodex runtime model calls required: zero. Exactly eight zero-write derivative intents are persisted\nfor a qualified article; `DurablePublicationCoordinator` remains the sole later public-write owner.\n\nPR #30 and PR #31 are `SUPERSEDED_DO_NOT_REUSE` for routing. Their runtime evidence remains valid\nhistorical proof. The four historical native newsroom Automations must remain off and any stale\ntrigger is a NOOP. A scheduled newsroom task must never modify code/tests/CodeGraph/PRs.\n\n'''
    insert_point = "## 2026-08-24 fast-ship owner override\n"
    text = read(authority)
    idx = text.find(insert_point)
    if idx < 0:
        raise SystemExit("authority_reset_insert_marker_missing")
    write(authority, text[:idx] + current_override + text[idx:])
    replace_between(
        authority,
        "## Hybrid Codex and current Automation truth override",
        "## Locked V2-after-V1 sequence",
        '''## Current V1 simple-Gemini execution truth\n\nRoutine heavy editorial ownership is now 9Router/Gemini through the canonical simple V1 operation.\nThe old Desktop-primary/SDK-fallback/native split-phase route is superseded for production. Codex\nDesktop is builder/debugger/host-proof capacity only. The four historical native newsroom\nAutomations must remain off; no fifth object is authorized.\n\nThe current V1 progression order is static CI -> one isolated zero-write simple-Gemini host canary\n-> lightweight local scheduler proof -> separate public-write authority. 4/32 remains throughput\ntelemetry, not a prerequisite. Final target remains 5–8 useful published articles/day.\n\n''',
    )

    context = "docs/codegraph/V1_CONTEXT.md"
    context_current = '''## Current product state\n\n`SIMPLE_GEMINI_RUNTIME_RESET / ZERO_WRITE_HOST_CANARY_PENDING`\n\nCurrent routine V1 no longer routes through Desktop Automations or the legacy rolling-X\nevidence-ready/split-phase worker critical path. Current authority is the simple Gemini runtime:\ncurrent sidecars + published memory -> one Gemini selection -> <=6 deterministic selected-story\nsource requests -> one Gemini writer -> deterministic material-claim validation -> optional one\nGemini revision -> one qualified zero-write article -> exactly eight undispatched intents. Codex\nruntime model calls are zero.\n\nPR #19 locator/retrieval primitives, PR #20 article/package proof, and PR #29 validate-after concepts\nare reusable donors. PR #30/#31 and native Desktop split-phase routing are historical evidence only.\n\n## Canonical product flow\n\n```text\nlocal headline sidecars + published memory\n-> ContentOpsProductionOrchestrator.run_v1_simple_gemini_newsroom\n-> bounded 9Router/Gemini selection\n-> BoundedPublicSecondaryEvidenceLoader on selected story only\n-> bounded 9Router/Gemini article writer\n-> deterministic source/claim validation\n-> optional one Gemini revision\n-> contentops.newsroom_qualified_article.v1\n-> exactly eight UNDISPATCHED derivative intents\n-> separately authorized DurablePublicationCoordinator\n-> strict readback/reconciliation\n```\n\nFinal target remains 5–8 useful published articles/day without filler.\n\n'''
    replace_between(context, "## Current product state", "## Editorial modes", context_current)
    implementation = '''## Canonical implementation path\n\nCurrent routine implementation areas:\n\n- `live_contentops/v1_simple_gemini_newsroom_v1.py` — selected-story simple runtime;\n- `live_contentops/nine_router_llm_seam_v2.py` / `nine_router_ordered_model_router_v2.py` — bounded Gemini model authority;\n- `live_contentops/public_secondary_evidence_loader_v1.py` — deterministic selected-story retrieval;\n- `live_contentops/newsroom_production_day_v1.py` — provider-neutral qualified zero-write record;\n- `live_contentops/production_orchestrator_v1.py` — canonical public operation boundary;\n- `live_contentops/publication_coordinator_v1.py` and destination registry — sole later public-write path.\n\nThe legacy rolling-X monolith, Desktop PREPARE/COMPLETE handoff, broad ready-pool discovery, and\ndeficit catch-up loops remain available for historical evidence/compatibility only and do not route\ncurrent routine V1. Use CodeGraph for donor call paths, not to revive superseded ownership.\n\nNext exact gate: one isolated zero-write current-sidecar host canary of the simple Gemini operation,\nthen a lightweight local scheduler using the same entrypoint. No live/public write is authorized.\n\n'''
    replace_between(context, "## Canonical implementation path", "## Focused test families", implementation)


def patch_final_ci() -> None:
    path = ".github/workflows/ci-fast.yml"
    replace_once(
        path,
        "  group: ci-fast-${{ github.ref }}-${{ github.sha }}\n  cancel-in-progress: false\n",
        "  group: ci-fast-${{ github.ref }}\n  cancel-in-progress: true\n",
    )
    replace_once(
        path,
        "      - name: Validate current hybrid execution and V1 owner authority\n",
        "      - name: Run V1 simple Gemini reset regressions\n        run: |\n          python -m pytest -q tests/test_v1_simple_gemini_newsroom_v1.py\n          python -m pytest -q tests/test_newsroom_production_day_v1.py tests/test_nine_router_ordered_model_router_v2.py\n\n      - name: Validate current hybrid execution and V1 owner authority\n",
    )
    authority_step = '''      - name: Validate current hybrid execution and V1 owner authority\n        shell: bash\n        run: |\n          python - <<'PY'\n          from pathlib import Path\n          from live_contentops.production_orchestrator_v1 import CANONICAL_OPERATIONS\n          from live_contentops.nine_router_llm_seam_v2 import integration_manifest\n          from live_contentops.nine_router_ordered_model_router_v2 import authority_packet\n\n          agents = Path('AGENTS.md').read_text(encoding='utf-8')\n          authority_map = Path('docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md').read_text(encoding='utf-8')\n          policy = Path('docs/automation/CONTENTOPS_CAPABILITY_ROUTED_HYBRID_EXECUTION_POLICY_V1.md').read_text(encoding='utf-8')\n          north_star = Path('docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md').read_text(encoding='utf-8')\n          master_plan = Path('docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md').read_text(encoding='utf-8')\n          reset = Path('docs/automation/CONTENTOPS_V1_SIMPLE_GEMINI_RUNTIME_RESET_V1.md').read_text(encoding='utf-8')\n          pointer = Path('docs/automation/CONTENTOPS_FINAL_DAILY_APP_V1_CURRENT_EXECUTION_POINTER_V3.md').read_text(encoding='utf-8')\n          desktop_doc = Path('docs/automation/CODEX_DESKTOP_V1_NEWSROOM_OPERATOR.md').read_text(encoding='utf-8')\n          desktop_code = Path('live_contentops/codex_desktop_newsroom_operator_v1.py').read_text(encoding='utf-8')\n          simple = Path('live_contentops/v1_simple_gemini_newsroom_v1.py').read_text(encoding='utf-8').lower()\n\n          assert 'CAPABILITY_ROUTED_HYBRID' in agents\n          assert 'GitHub Connector / `WEB_STATIC` first' in policy\n          assert 'Codex Desktop / `CODEX_EXECUTION` is the second-last choice' in policy\n          for text in (agents, north_star, master_plan):\n              upper = text.upper()\n              assert '4 QUALIFIED ZERO-PUBLIC-WRITE ARTICLES' in upper\n              assert '5–8 PUBLISHED ARTICLES' in upper\n              assert 'DEGRADED_DAILY_OUTPUT_DEFICIT' in upper\n          assert 'Status: `CURRENT_V1_EXECUTION_AUTHORITY`' in reset\n          assert 'run_v1_simple_gemini_newsroom' in CANONICAL_OPERATIONS\n          assert 'maximum 6 requests' in reset\n          assert 'Codex runtime model calls required: `0`' in reset\n          assert 'SUPERSEDED_DO_NOT_REUSE' in reset and 'PR #30' in reset and 'PR #31' in reset\n          assert 'SIMPLE_GEMINI_RUNTIME' in agents\n          assert 'simple Gemini' in pointer\n          assert 'SUPERSEDED_FOR_ROUTINE_V1_PRODUCTION' in desktop_doc\n          assert 'SUPERSEDED_CODEX_NEWSROOM_AUTOMATION_NOOP' in desktop_code\n          assert 'official_codex' not in simple and 'codex_desktop' not in simple\n          manifest = integration_manifest()\n          packet = authority_packet()\n          assert manifest['v1_simple_gemini_runtime_primary'] is True\n          assert manifest['codex_runtime_model_calls_required'] is False\n          assert packet['publication_qualified_article_uses_9router_gemini'] is True\n          assert packet['publication_qualified_article_uses_native_codex_desktop_xhigh'] is False\n          assert packet['codex_runtime_model_calls_required'] is False\n          assert 'UNKNOWN_WRITE' in agents\n          assert 'DurablePublicationCoordinator' in reset\n          PY\n\n'''
    replace_between(
        path,
        "      - name: Validate current hybrid execution and V1 owner authority\n",
        "      - name: Check CodeGraph freshness and prepare repair artifact\n",
        authority_step,
    )
    replace_once(
        path,
        "        if: always() && steps.codegraph.outputs.rc != '0' && github.ref != 'refs/heads/agent/web-v1-simple-gemini-runtime-reset' && (github.event_name != 'push' || github.ref != 'refs/heads/master')\n",
        "        if: always() && steps.codegraph.outputs.rc != '0' && (github.event_name != 'push' || github.ref != 'refs/heads/master')\n",
    )
    replace_once(
        path,
        "    if: (github.event_name == 'push' && startsWith(github.ref, 'refs/heads/agent/web-') && github.ref != 'refs/heads/agent/web-v1-simple-gemini-runtime-reset') || (github.event_name == 'pull_request' && github.event.pull_request.head.repo.full_name == github.repository && github.event.pull_request.head.ref != 'agent/web-v1-simple-gemini-runtime-reset')\n",
        "    if: (github.event_name == 'push' && startsWith(github.ref, 'refs/heads/agent/web-')) || (github.event_name == 'pull_request' && github.event.pull_request.head.repo.full_name == github.repository)\n",
    )


def main() -> None:
    assert_exact_checkout()
    patch_simple_runtime()
    patch_qualified_record_helper()
    patch_orchestrator()
    patch_router_authority()
    patch_codex_noop()
    patch_authority_docs()
    patch_final_ci()


if __name__ == "__main__":
    main()
