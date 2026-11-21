from copy import deepcopy
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest

from live_contentops import measured_odds_series_v1 as odds
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator

SOURCE = Path(__file__).resolve().parents[1] / "docs/publisher/CC-536"


@pytest.fixture
def piece():
    return json.loads((SOURCE / "piece-1.json").read_bytes())


def test_every_method_numeral_has_exact_main_binding(piece):
    report = odds.validate_piece(piece, SOURCE / "source")
    assert [r["number"] for r in report] == ["54", "2016", "2026", "20", "60", "20", "50", "14", "0.05", "54"]
    assert all(r["table_hash"] == piece["table_hash"] for r in report)


def test_unbound_public_number_is_rejected(piece):
    piece["article"]["social_summary"] += " We found 99 winners."
    with pytest.raises(ValueError, match="ODDS_UNBOUND_PUBLIC_NUMBER"):
        odds.validate_piece(piece, SOURCE / "source")


def test_a_different_value_is_not_blessed_by_a_valid_source_path(piece):
    claim = piece["number_bindings"][0]
    piece["article"][claim["field"]] = piece["article"][claim["field"]].replace("54 market", "55 market")
    claim["span"] = claim["span"].replace("54 market", "55 market")
    with pytest.raises(ValueError, match="ODDS_NUMBER_DIFFERS_FROM_SOURCE:55"):
        odds.number_report(piece, SOURCE / "source")


def test_source_bytes_are_checked_before_use(piece, tmp_path):
    shutil.copytree(SOURCE / "source", tmp_path / "source")
    table = tmp_path / "source/desk_odds_v1.json"
    table.write_bytes(table.read_bytes() + b" ")
    with pytest.raises(ValueError, match="ODDS_SOURCE_BYTES_CHANGED"):
        odds.validate_piece(piece, tmp_path / "source")


def _extra(piece, span, file, pointer, **kw):
    piece["article"]["social_summary"] = span
    piece["number_bindings"].append({"field":"social_summary","span":span,"file":file,"pointer":pointer,**kw})


def test_pooled_row_cannot_be_quoted_for_a_side(piece):
    _extra(piece, "Bitcoin short 0.531R.", "desk_odds_v1.json", "/by_market/BTCUSD/6", side="SHORT")
    with pytest.raises(ValueError, match="ODDS_ONE_SIDE_REQUIRES_SIDE_FILE"):
        odds.number_report(piece, SOURCE / "source")
    piece["number_bindings"][-1].pop("side")
    with pytest.raises(ValueError, match="ODDS_ONE_SIDE_REQUIRES_SIDE_FILE"):
        odds.number_report(piece, SOURCE / "source")


def test_side_must_match_source_and_table_hash(piece):
    prefix = "/tables/"+piece["table_hash"]+"/markets/BTCUSD/sides/BREAKOUT_WITH_TREND_20/LONG/2"
    _extra(piece, "Bitcoin short 0.1R.", "desk_odds_sides_v1.json", prefix, side="SHORT")
    with pytest.raises(ValueError, match="ODDS_EXACT_SIDE_REQUIRED"):
        odds.number_report(piece, SOURCE / "source")
    piece["number_bindings"][-1]["pointer"] = prefix.replace(piece["table_hash"], "0"*64)
    with pytest.raises(ValueError, match="ODDS_SIDE_TABLE_HASH_REQUIRED"):
        odds.number_report(piece, SOURCE / "source")


def test_side_row_binds_count_and_mean_without_requiring_a_child_pointer(piece):
    path = "/tables/" + piece["table_hash"] + "/markets/BTCUSD/sides/LONG_WHILE_UP_20/LONG"
    _extra(piece, "Bitcoin long: 96 trades, 0.801R per trade.", "desk_odds_sides_v1.json", path, side="LONG")
    rows = odds.number_report(piece, SOURCE / "source")
    assert [(r["number"], r["side"]) for r in rows if r["field"] == "social_summary"] == [
        ("96", "LONG"), ("0.801", "LONG")]


def test_public_side_label_cannot_contradict_its_bound_side(piece):
    path = "/tables/" + piece["table_hash"] + "/markets/BTCUSD/sides/LONG_WHILE_UP_20/LONG/2"
    _extra(piece, "Bitcoin short: 0.801R.", "desk_odds_sides_v1.json", path, side="LONG")
    with pytest.raises(ValueError, match="ODDS_PUBLIC_SIDE_DIFFERS_FROM_SOURCE"):
        odds.number_report(piece, SOURCE / "source")


def test_piece_two_exact_sides_reach_the_existing_native_compiler():
    piece = json.loads((SOURCE / "piece-2/piece-2.json").read_bytes())
    report = odds.validate_piece(piece, SOURCE / "piece-2/source")
    assert {r["side"] for r in report if r["side"]} == {"LONG", "SHORT"}
    assert not any("/markets/" + market + "/" in r["pointer"] for r in report for market in odds.FX)
    from live_contentops.eight_platform_substack_first_pipeline_v1 import build_native_derivative_payloads
    payloads = build_native_derivative_payloads(article=piece["article"], selection={},
        canonical_url="https://capitalchronicle.substack.com/p/with-the-trend-test-only", media_asset_ids=[])
    assert len(payloads) == 8
    assert "Gold trend-long: 76 trades, 0.391R per trade." in payloads["telegram"]["text"]
    assert payloads["x"]["posts"][0]["text"] == piece["article"]["social_hook"]
    assert "Bitcoin trend-short: 73 trades, 0.297R; the later half lost." in payloads["x"]["full_text"]


def test_piece_three_repaired_fx_and_exact_sides_reach_native_compiler():
    root = SOURCE / "piece-3"
    piece = json.loads((root / "piece-3.json").read_bytes())
    manifest, held = odds.sources(root / "source")
    report = odds.validate_piece(piece, root / "source")
    assert manifest["fx_repair_live"] is True
    assert len(report) == 119
    assert {r["side"] for r in report if r["side"]} == {"LONG", "SHORT"}
    table = held["desk_odds_v1.json"]
    markets = held["desk_odds_sides_v1.json"]["tables"][table["content_hash"]]["markets"]
    for market in odds.FX:
        assert table["markets"][market]["close_check"]["rule"] == "CLOSE_SET_TO_NEXT_SESSION_OPEN"
        assert table["markets"][market]["close_check"]["applied"] is True
        assert markets[market]["source_id"] == table["markets"][market]["source_id"]
        assert any("/markets/" + market + "/sides/" in r["pointer"] for r in report)
    # Read actual public cells against each named column, including the baseline.
    rows = [line.split("|")[1:-1] for line in piece["article"]["substack_body_markdown"].splitlines()
            if line.startswith("| ") and not line.startswith("| Market and rule")]
    order = ["XAUUSD", "USOIL", "US500", "BTCUSD", "EURUSD", "USDJPY"]
    for index, market in enumerate(order):
        for start, behaviour in [(index * 3, "WITH_YARDSTICK_5"),
                                 (18 + index * 2, "AGAINST_YARDSTICK_5")]:
            for offset, side in enumerate(("LONG", "SHORT")):
                cells = rows[start + offset]
                source = markets[market]["sides"][behaviour][side]
                assert side.lower() in cells[0]
                assert cells[1].strip() == f"{source[0]}; {source[2]}"
        baseline = markets[market]["always"]["WITH_YARDSTICK_5"]["ALWAYS_LONG"]
        assert "always long" in rows[index * 3 + 2][0]
        assert rows[index * 3 + 2][1].strip() == f"{baseline[0]}; {baseline[2]}"
    from live_contentops.eight_platform_substack_first_pipeline_v1 import build_native_derivative_payloads
    payloads = build_native_derivative_payloads(article=piece["article"], selection={},
        canonical_url="https://capitalchronicle.substack.com/p/five-sessions-did-not-settle-the-trend-question",
        media_asset_ids=[piece["media_assets"][0]["asset_id"]])
    assert len(payloads) == 8
    assert "Trend-short: 218 trades, -0.048R." in payloads["x"]["full_text"]
    assert "always long: 704 trades, 0.086R" in payloads["telegram"]["text"]
    assert "With and against use different stop widths." in payloads["youtube"]["text"]


def test_fx_result_waits_for_repaired_main_table(piece):
    _extra(piece, "Euro -0.075R.", "desk_odds_v1.json", "/by_market/EURUSD/0/2")
    with pytest.raises(ValueError, match="ODDS_FX_CLOSE_REPAIR_NOT_LIVE:EURUSD"):
        odds.number_report(piece, SOURCE / "source")


def test_construction_result_is_explicitly_pooled(piece):
    _extra(piece, "Mean -0.217R.", "desk_odds_v1.json", "/construction/stop_width/rows/0/2")
    with pytest.raises(ValueError, match="ODDS_CONSTRUCTION_POOLED_LABEL_REQUIRED"):
        odds.number_report(piece, SOURCE / "source")


def test_private_reference_book_cannot_become_a_numeric_source(piece):
    _extra(piece, "Result 450.", "desk_odds_v1.json", "/plain_book/in_sample/summary/trades")
    with pytest.raises(ValueError, match="ODDS_PUBLIC_DERIVED_FIELD_REQUIRED"):
        odds.number_report(piece, SOURCE / "source")


@pytest.mark.parametrize("piece_number", [1, 2, 3, 5])
def test_actual_coordinator_registers_and_consumes_the_same_bound_piece(tmp_path, monkeypatch, piece_number):
    store = ContentOpsDurableStore(tmp_path / "test.sqlite3")
    file = SOURCE / "piece-1.json" if piece_number == 1 else SOURCE / f"piece-{piece_number}/piece-{piece_number}.json"
    packet = odds.register(store, file, tmp_path / "article")
    assert packet["plan"]["distribution_policy"] == "SUBSTACK_FIRST_V1"
    assert packet["plan"]["substack_first_dependency"] is True
    coordinator = DurablePublicationCoordinator(store=store,transport_runtime=SimpleNamespace(),
        published_content_path=tmp_path / "published.jsonl")
    coordinator.register_plan(packet["identity"],packet["plan"])
    rows = store.list_outbox_messages(work_item_id=packet["identity"],destination="substack")
    assert len(rows)==1
    intent=json.loads(rows[0]["payload"])
    assert intent["measured_odds_piece"]==packet["identity"]
    from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _durable_intent_inputs
    assert _durable_intent_inputs(intent)["article"]["measured_odds_series"]==odds.POLICY
    from live_contentops import article_publication_quality_v1 as quality
    calls=[]
    monkeypatch.setattr(quality,"image_register",lambda _:SimpleNamespace(reserve=lambda **kw:calls.append(kw) or {"status":"RESERVED"}))
    assert quality.before_article_write(coordinator,intent,"substack")["status"]=="RESERVED"
    assert calls[0]["enforce_cap"] is True
    assert calls[0]["assets"][0]["sha256"]==packet["piece"]["media_assets"][0]["sha256"]
    assert odds.register(store,file,tmp_path / "article")==packet
    assert len(store.list_outbox_messages(work_item_id=packet["identity"],destination="substack"))==1
    if piece_number == 5:
        from live_contentops.event_article_guard_v1 import PublicOutputError, check_publication_copy

        public_body = packet["piece"]["article"]["substack_body_markdown"]
        assert "The stop entry at 0.5 normal day farther had 1190 fills" in public_body
        with pytest.raises(PublicOutputError, match="PRIVATE_OR_EXECUTION_COPY_FORBIDDEN"):
            check_publication_copy(odds.publication_check_copy({
                "body": public_body,
                "instruction": "Use a stop entry at 0.5 normal day farther.",
            }, packet["plan"]))
    altered=deepcopy(packet["plan"]);altered["plan_hash"]="a"*64
    with pytest.raises(ValueError,match="ODDS_REGISTERED_PLAN_CHANGED"):
        coordinator.register_plan(packet["identity"],altered)


@pytest.mark.parametrize("extra", ["Use 0.05 lots.", "Our positions earned 0.391R.",
                                  "An unbound mean was 0.777R.", "Go long gold."])
def test_historical_metrics_do_not_release_account_copy_or_unbound_results(tmp_path, extra):
    from live_contentops.event_article_guard_v1 import check_publication_copy, PublicOutputError
    store = ContentOpsDurableStore(tmp_path / "test.sqlite3")
    packet = odds.register(store, SOURCE / "piece-2/piece-2.json", tmp_path / "article")
    article = packet["piece"]["article"]
    copy = {"body": article["substack_body_markdown"], "social": article["social_summary"]}
    checked = odds.publication_check_copy(copy, packet["plan"])
    assert check_publication_copy(checked)["status"] == "PASS"
    with pytest.raises(PublicOutputError, match="PRIVATE_OR_EXECUTION_COPY_FORBIDDEN"):
        check_publication_copy(odds.publication_check_copy({**copy, "extra": extra}, packet["plan"]))


def test_bound_native_snapshot_reaches_the_existing_url_media_consumer(tmp_path, monkeypatch):
    from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
    from live_contentops.cloudinary_delivery_media_v1 import _validated_local_asset, READY
    store = ContentOpsDurableStore(tmp_path / "test.sqlite3")
    packet = odds.register(store, SOURCE / "piece-2/piece-2.json", tmp_path / "article")
    context = (tmp_path / "article/run_context_v1.json").read_bytes()
    delivered=[]
    def prepare(**kwargs):
        assert not kwargs["article_assets"]
        for asset in kwargs["delivery_only_assets"]:
            verified, blockers = _validated_local_asset(asset, article=kwargs["article"])
            assert not blockers, blockers
            delivered.append(verified)
        return {"status": READY, "manifest": {"assets": []}, "provider_calls": 0}
    monkeypatch.setattr(pipeline, "prepare_cloudinary_delivery_media", prepare)
    result = pipeline._prepare_cloudinary_delivery_media_for_plan(work_item_id=packet["identity"],
        plan=packet["plan"], preconditions={"canonical_publication_status":"RECONCILED_CONFIRMED",
                                          "unknown_write_count":0})
    assert result["status"] == READY
    assert len(delivered) == 1 and delivered[0]["sha256"] == packet["media_assets"][0]["sha256"]
    assert delivered[0]["delivery_only"] is True
    assert (tmp_path / "article/run_context_v1.json").read_bytes() == context
    altered=deepcopy(packet["media_assets"])
    altered[0]["sha256"]="a"*64
    with pytest.raises(ValueError,match="ODDS_DELIVERY_CHART_BINDING_CHANGED"):
        odds.delivery_snapshot_projection(packet["plan"], altered)


def test_registered_copy_and_source_manifest_are_immutable(tmp_path):
    store=ContentOpsDurableStore(tmp_path / "test.sqlite3")
    packet=odds.register(store,SOURCE / "piece-1.json",tmp_path / "article")
    path=tmp_path / "article/source/manifest.json"
    value=json.loads(path.read_bytes());value["fx_repair_live"]=True
    path.write_text(json.dumps(value),encoding="utf-8")
    with pytest.raises(ValueError,match="ODDS_REGISTERED_ARTIFACT_CHANGED:source/manifest.json"):
        odds.validate_plan(store,packet["identity"],packet["plan"])


def test_interrupted_threads_dispatch_recovers_only_its_exact_public_root(tmp_path, monkeypatch):
    from live_contentops import threads_adapter_v6 as threads
    from live_contentops.publication_coordinator_v1 import (
        ATTEMPT_STARTED, DISPATCH_CONFIRMED, RECONCILIATION_PENDING,
        RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE, CanonicalDestinationTransportRuntimeV1,
    )

    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    packet = odds.register(store, SOURCE / "piece-5/piece-5.json", tmp_path / "article")
    runtime = CanonicalDestinationTransportRuntimeV1()
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=runtime,
        published_content_path=tmp_path / "published.jsonl")
    coordinator.register_plan(packet["identity"], packet["plan"])
    ids = coordinator._ids(packet["identity"], packet["plan"]["plan_hash"], "threads")
    message = store.get_outbox_message(ids["message_id"])
    intent = runtime.finalize_intent(destination="threads", intent=json.loads(message["payload"]),
        canonical_url="https://capitalchronicle.substack.com/p/fixture-article")
    store.finalize_outbox_payload_before_dispatch(message_id=message["message_id"],
        payload=odds.canonical_bytes(intent).decode(), status="READY")
    assert store.claim_platform_dispatch_attempt(dispatch_id=ids["dispatch_id"],
        message_id=ids["message_id"], platform="threads")
    original = store.get_platform_dispatch(ids["dispatch_id"])
    root_id = "1234567890123"
    root_url = "https://www.threads.com/@official.capitalchronicle/post/exact-root"
    root_text = packet["piece"]["article"]["social_hook"]
    visible_text = "A different post on the same account."

    def read_root(**kwargs):
        assert kwargs["post_id"] == root_id
        assert kwargs["expected_text"] == root_text
        return {"status": "SUCCESS", "post_id": root_id, "public_url": root_url,
                "visible_body_text": visible_text, "account_identity_verified": True,
                "content_binding_checks": {"account_match": True, "text_match": True, "media_match": True}}

    def forbid_send(**kwargs):
        pytest.fail("Readback must never send a Threads post")

    monkeypatch.setattr(threads, "readback_threads_post", read_root)
    monkeypatch.setattr(threads, "readback_threads_chain", lambda **kw: {"status": "FAILED_THREADS_REPLY_CHAIN_READBACK"})
    monkeypatch.setattr(threads, "execute_threads_post", forbid_send)
    receipt = coordinator.readback_existing_dispatch(ids["dispatch_id"], observed_threads_root=(root_id, root_url))
    assert receipt["reconciliation_status"] == RECONCILIATION_PENDING
    assert store.get_platform_dispatch(ids["dispatch_id"]) == original
    assert original["status"] == ATTEMPT_STARTED

    visible_text = root_text
    receipt = coordinator.readback_existing_dispatch(ids["dispatch_id"], observed_threads_root=(root_id, root_url))
    assert receipt["reconciliation_status"] == RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE
    assert receipt["publish_called"] is False
    current = store.get_platform_dispatch(ids["dispatch_id"])
    assert (current["status"], current["public_object_id"], current["public_object_url"]) == (DISPATCH_CONFIRMED, root_id, root_url)
    assert current["dispatched_at"] == original["dispatched_at"]


def test_resuming_registered_piece_uses_its_saved_output_directory(tmp_path):
    store=ContentOpsDurableStore(tmp_path/'store.sqlite3')
    packet=odds.register(store,SOURCE/'piece-1.json',tmp_path/'article')
    assert odds.register(store,SOURCE/'piece-1.json',None)==packet


def test_status_needs_no_native_invocation_or_browser_executor(tmp_path,monkeypatch):
    from live_contentops import native_desktop_publication_v1 as publication
    from live_contentops import native_neo_executor_v1 as native
    store=ContentOpsDurableStore(tmp_path/'store.sqlite3')
    packet=odds.register(store,SOURCE/'piece-1.json',tmp_path/'article')
    monkeypatch.setattr(publication,'live_publication_policy',lambda _:None)
    monkeypatch.setattr(native,'bind_native_neo_coordinator',lambda *a,**kw:pytest.fail('Status created a browser executor'))
    assert odds.continue_piece(store,packet,invocation_id=None,rollout={'store_path':str(store.db_path)},command='status')=={
        'publication':{'dispatches':[]},'pending_requests':[]}


def test_exact_public_readback_skips_the_global_draft_inventory(tmp_path,monkeypatch):
    from live_contentops import substack_draft_inventory_v1 as inventory
    from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
    store=ContentOpsDurableStore(tmp_path/'store.sqlite3')
    packet=odds.register(store,SOURCE/'piece-1.json',tmp_path/'article')
    c=DurablePublicationCoordinator(store=store,transport_runtime=None)
    c.register_plan(packet['identity'],packet['plan'])
    intent=json.loads(store.list_outbox_messages(work_item_id=packet['identity'],destination='substack')[0]['payload'])
    monkeypatch.setattr(inventory,'store_draft_ids',lambda _:pytest.fail('Exact object scanned global draft history'))
    request=NeoDestinationHandoff(store=store).request(destination='substack',action='READBACK',intent=intent,
        public_object_id='224849463',public_object_url='https://capitalchronicle.substack.com/p/method')
    assert request['draft_readback_scope']['referenced_draft_ids']==['224849463']
    assert request['draft_readback_scope']['scan_unreferenced_drafts'] is False


def test_native_readback_and_pending_queries_stay_inside_the_exact_item(tmp_path,monkeypatch):
    from live_contentops.native_neo_executor_v1 import NativeNeoExecutor
    store=ContentOpsDurableStore(tmp_path/'store.sqlite3')
    executor=NativeNeoExecutor(store,operation_id='cc536-measured-odds-1',output_dir=tmp_path,
        native_invocation_id='test-native-turn')
    calls=[]
    original=store.list_outbox_messages
    def scoped(**kw):
        assert kw['work_item_id']=='cc536-measured-odds-1'
        calls.append(kw)
        return original(**kw)
    monkeypatch.setattr(store,'list_outbox_messages',scoped)
    request={'work_item_id':'cc536-measured-odds-1','action':'READBACK','destination':'substack'}
    assert executor.fresh_readback_request(request) is None
    executor.complete_readback_request(request)
    assert executor.pending(work_item_id=request['work_item_id'])==[]
    assert len(calls)==3


def test_one_destination_continuation_uses_its_canonical_and_existing_dispatch(tmp_path,monkeypatch):
    from live_contentops import native_desktop_publication_v1 as publication
    from live_contentops import native_neo_executor_v1 as native
    store=ContentOpsDurableStore(tmp_path/'store.sqlite3')
    packet=odds.register(store,SOURCE/'piece-1.json',tmp_path/'article')
    coordinator=DurablePublicationCoordinator(store=store,transport_runtime=None)
    coordinator.register_plan(packet['identity'],packet['plan'])
    calls=[]
    monkeypatch.setattr(publication,'live_publication_policy',lambda _:None)
    monkeypatch.setattr(native,'bind_native_neo_coordinator',lambda *a,**kw:(coordinator,SimpleNamespace(pending=lambda **kw:[])))
    monkeypatch.setattr(coordinator,'_dispatch_message',lambda message,**kw:calls.append((message,kw)) or {'status':'EXISTING_DISPATCH_USED'})
    args={'invocation_id':'test-native-turn','rollout':{'store_path':str(store.db_path)},'command':'dispatch','destination':'x'}
    assert odds.continue_piece(store,packet,**args)['publication']['status']=='WAITING_CANONICAL_URL'
    assert calls==[]
    monkeypatch.setattr(coordinator,'_confirmed_canonical_url_for_work_item',lambda *a,**kw:'https://capitalchronicle.substack.com/p/method')
    assert odds.continue_piece(store,packet,**args)['publication']['status']=='EXISTING_DISPATCH_USED'
    assert calls[0][0]['destination']=='x'
    assert calls[0][0]['work_item_id']==packet['identity']
    assert calls[0][1]['canonical_url']=='https://capitalchronicle.substack.com/p/method'
    odds.continue_piece(store,packet,**args,retry_reconciled_absent=True)
    assert calls[-1][1]['explicit_reconciled_absent_retry'] is True
    observed=[]
    monkeypatch.setattr(coordinator,'readback_existing_dispatch',lambda dispatch_id:observed.append(dispatch_id) or {'status':'READ_BACK'})
    assert odds.continue_piece(store,packet,**{**args,'command':'readback'})['publication']['status']=='READ_BACK'
    assert observed==[coordinator._ids(packet['identity'],packet['plan']['plan_hash'],'x')['dispatch_id']]
    company={**args,'destination':'linkedin_company'}
    assert odds.continue_piece(store,packet,**company)['publication']['status']=='EXISTING_DISPATCH_USED'
    assert calls[-1][0]['destination']=='linkedin_company'
    assert calls[-1][0]['message_id']==coordinator._ids(packet['identity'],packet['plan']['plan_hash'],'linkedin_company')['message_id']
    with pytest.raises(ValueError,match='ODDS_REGISTERED_DERIVATIVE_REQUIRED'):
        odds.continue_piece(store,packet,**{**args,'destination':'substack_notes'})
    with pytest.raises(ValueError,match='ODDS_REGISTERED_DERIVATIVE_REQUIRED'):
        odds.continue_piece(store,packet,**{**args,'destination':'substack'})


@pytest.mark.parametrize('missing_reply',[False,True])
def test_threads_official_consumer_uses_bound_root_and_full_link_reply(tmp_path,monkeypatch,piece,missing_reply):
    from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
    from live_contentops import threads_adapter_v6 as adapter
    from live_contentops import post_visuals_v1
    canonical='https://capitalchronicle.substack.com/p/method'
    payload=odds.compile_payloads(piece['article'],canonical,['chart'])['threads']
    original=deepcopy(payload)
    data={'output_dir':tmp_path,'article':piece['article'],'payloads':{'threads':payload},
          'canonical_url':canonical,'local_media':'chart.png','public_image_url':'https://example.com/chart.png',
          'media_assets':[],'primary_media':{'sha256':'a'*64}}
    monkeypatch.setattr(pipeline,'_durable_intent_inputs',lambda _:data)
    monkeypatch.setattr(post_visuals_v1,'require_publication_image',lambda *args:None)
    published=[]
    def publish(**kwargs):
        published.append(kwargs)
        return {'status':'SUCCESS','id':str(len(published))}
    monkeypatch.setattr(adapter,'execute_threads_post',publish)
    roots=[]
    def read_root(**kwargs):
        roots.append(kwargs)
        return {'status':'SUCCESS','post_id':'1','public_url':'https://www.threads.net/@official.capitalchronicle/post/test',
                'account_identity_verified':True,'visible_body_text':kwargs['expected_text']}
    monkeypatch.setattr(adapter,'readback_threads_post',read_root)
    chains=[]
    def read_chain(**kwargs):
        chains.append(kwargs)
        assert [r['text'] for r in kwargs['reply_expectations']]==payload['reply_texts']
        assert canonical in kwargs['reply_expectations'][0]['text']
        return {'status':'FAILED_THREADS_REPLY_CHAIN_READBACK' if missing_reply else 'SUCCESS'}
    monkeypatch.setattr(adapter,'readback_threads_chain',read_chain)
    result=pipeline._publish_one_destination_from_durable_intent(destination='threads',
        intent={'attempt_identity':'attempt'},authorization_context={
            'operating_mode':'AUTONOMOUS_DEFAULT','dispatch_attempt_identity':'attempt'})
    assert published[0]['text']==payload['root_text']
    assert [r['text'] for r in published[1:]]==payload['reply_texts']
    assert result['provider_readback_verified'] is (not missing_reply)
    assert roots[0]['canonical_url'] is None
    assert roots[0]['expected_media_local_path']=='chart.png'
    assert payload==original
    pipeline._readback_one_destination_from_durable_intent(destination='threads',public_object_id='1',
        public_object_url='https://www.threads.net/@official.capitalchronicle/post/test',intent={})
    assert roots[-1]['canonical_url'] is None
    assert len(chains)==2


@pytest.mark.parametrize("complete_listing", [True, False])
def test_threads_correction_only_completes_the_bound_reply_suffix(tmp_path, monkeypatch, piece, complete_listing):
    from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
    from live_contentops import post_visuals_v1, threads_adapter_v6 as threads

    canonical = "https://capitalchronicle.substack.com/p/method"
    root_id = "1234567890123"
    root_url = "https://www.threads.com/@official.capitalchronicle/post/exact-root"
    payload = odds.compile_payloads(piece["article"], canonical, ["chart"])["threads"]
    expected_replies = payload["reply_texts"]
    data = {"output_dir": tmp_path, "article": piece["article"], "payloads": {"threads": payload},
            "canonical_url": canonical, "local_media": "chart.png", "public_image_url": "", "media_assets": []}
    monkeypatch.setattr(pipeline, "_durable_intent_inputs", lambda _: data)
    monkeypatch.setattr(post_visuals_v1, "require_publication_image", lambda *args: None)
    monkeypatch.setattr(threads, "readback_threads_post", lambda **kw: {
        "status": "SUCCESS", "post_id": root_id, "public_url": root_url, "visible_body_text": payload["root_text"],
    })

    def read_chain(**kwargs):
        assert kwargs["root_id"] == root_id
        assert [row["text"] for row in kwargs["reply_expectations"]] == expected_replies
        if published:
            return {"status": "SUCCESS"}
        return {"complete_reply_listing": complete_listing,
                "own_reply_ids_in_chronological_order": ["existing-link-reply"],
                "ordered_replies": [{"id": "existing-link-reply", "parent_child_verified": True, "text_verified": True}]}

    published = []

    def publish(**kwargs):
        assert kwargs["reply_to_id"] == root_id
        published.append(kwargs["text"])
        return {"status": "SUCCESS", "id": str(len(published))}

    monkeypatch.setattr(threads, "readback_threads_chain", read_chain)
    monkeypatch.setattr(threads, "execute_threads_post", publish)
    result = pipeline._publish_one_destination_from_durable_intent(destination="threads",
        intent={"attempt_identity": "attempt", "recovery_public_object_id": root_id,
                "recovery_public_object_url": root_url},
        authorization_context={"operating_mode": "AUTONOMOUS_DEFAULT", "dispatch_attempt_identity": "attempt"})
    assert result["id"] == root_id and result["public_url"] == root_url
    assert result["provider_readback_verified"] is complete_listing
    assert published == (expected_replies[1:] if complete_listing else [])


def confirm_method(store, tmp_path):
    packet = odds.register(store,SOURCE / "piece-1.json",tmp_path / "method")
    coordinator = DurablePublicationCoordinator(store=store,transport_runtime=None)
    coordinator.register_plan(packet["identity"],packet["plan"])
    ids = coordinator._ids(packet["identity"],packet["plan"]["plan_hash"],"substack")
    assert odds.confirmed_method_page(store) is None
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"],message_id=ids["message_id"],platform="substack",
        status="DISPATCH_CONFIRMED",public_object_id="456",public_object_url="https://capitalchronicle.substack.com/p/method")
    assert odds.confirmed_method_page(store) is None
    store.register_reconciliation(reconciliation_id=ids["reconciliation_id"],work_item_id=packet["identity"],status="RECONCILED_CONFIRMED")
    return odds.confirmed_method_page(store)


def test_method_reference_waits_for_canonical_readback_then_feeds_new_copy(tmp_path):
    store=ContentOpsDurableStore(tmp_path / "test.sqlite3")
    ref=confirm_method(store,tmp_path)
    assert ref["table_hash"]==json.loads((SOURCE/"piece-1.json").read_bytes())["table_hash"]
    payload={"text":"The plan.","full_text":"The plan.","posts":[{"text":"The plan.","order":0,"role":"root","media_asset_ids":[]}]}
    amended=odds.add_method_link(payload,ref)
    assert amended["posts"][0]==payload["posts"][0]
    assert amended["posts"][1]["text"].endswith(ref["canonical_url"])
    assert payload["full_text"]=="The plan."


def test_measured_piece_reuses_the_bound_web_only_substack_transport(monkeypatch):
    from live_contentops import plan_substack_neo_v1 as substack
    from live_contentops.neo_endpoint_executor_v1 import NeoBrowserDriver
    assert substack.supports_operation("cc536-measured-odds-1")
    assert substack.supports_operation("cc536-measured-odds-7")
    assert not substack.supports_operation("cc536-measured-odds-8")
    assert not substack.supports_operation("unbound-article")
    observed=[]
    monkeypatch.setattr(substack,"perform",lambda client,packet:observed.append(packet) or {"same_transport":True})
    driver=NeoBrowserDriver(SimpleNamespace())
    packet={"operation_id":"cc536-measured-odds-1","request":{"destination":"substack"}}
    assert driver.perform(packet)=={"same_transport":True}
    assert observed==[packet]


@pytest.mark.parametrize("cause", ["NEO_CONTROL_COVERED_ACT", "PLAN_SUBSTACK_EXACT_DRAFT_MISMATCH"])
def test_repaired_substack_control_releases_only_its_proven_preclick_no_write(tmp_path, cause):
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    from live_contentops.neo_endpoint_executor_v1 import repaired_prewrite_request
    store=ContentOpsDurableStore(tmp_path/'store.sqlite3')
    packet=odds.register(store,SOURCE/'piece-1.json',tmp_path/'article')
    c=DurablePublicationCoordinator(store=store,transport_runtime=None)
    c.register_plan(packet['identity'],packet['plan'])
    ids=c._ids(packet['identity'],packet['plan']['plan_hash'],'substack')
    request={'action':'PUBLISH','destination':'substack','dispatch_attempt_identity':ids['dispatch_id'],'request_sha256':'a'*64}
    body={'operation_id':packet['identity'],'request':request}
    store.register_outbox_message(message_id='test-request',work_item_id=packet['identity'],destination='internal:native-neo-tool',payload=json.dumps(body),status='NATIVE_NEO_INTERNAL')
    result={'status':'FAILED_BEFORE_WRITE','definite_no_write':True,'public_write_performed':False,
        'stage':'BEFORE_PUBLISH_CLICK','reason_code':cause,'native_tool_return_sha256':'b'*64,
        'neo_executor_revision':'old-source','native_tool_observation':{}}
    key='native-neo-'+sha256_of([packet['identity'],request['request_sha256'],'response'])
    store.register_outbox_message(message_id=key,work_item_id=packet['identity'],destination='internal:native-neo-tool',payload=json.dumps({'result':result}),status='NATIVE_NEO_INTERNAL')
    dispatch={'status':'DEFINITE_NO_WRITE','platform':'substack','message_id':ids['message_id'],'dispatch_id':ids['dispatch_id']}
    assert repaired_prewrite_request(store,dispatch,executor_revision='new-source')['reason_code']==cause
    assert repaired_prewrite_request(store,dispatch,executor_revision='old-source') is None
    assert repaired_prewrite_request(store,{**dispatch,'status':'UNKNOWN_WRITE'},executor_revision='new-source') is None
    store.register_platform_dispatch(dispatch_id=ids['dispatch_id'],message_id=ids['message_id'],platform='substack',status='DEFINITE_NO_WRITE')
    store.register_reconciliation(reconciliation_id=ids['reconciliation_id'],work_item_id=packet['identity'],status=cause)
    assert store.claim_platform_dispatch_attempt(dispatch_id=ids['dispatch_id'],message_id=ids['message_id'],platform='substack',
        expected_status='DEFINITE_NO_WRITE',policy_no_write_cause=cause)
    result['native_tool_observation']['dispatched_at_utc']='2026-11-14T06:00:00Z'
    store.finalize_outbox_payload_before_dispatch(message_id=key,payload=json.dumps({'result':result}),status='NATIVE_NEO_INTERNAL')
    assert repaired_prewrite_request(store,dispatch,executor_revision='new-source') is None
