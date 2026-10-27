"""Controlled regression evidence; these tests never stand in for editorial judgment."""

from copy import deepcopy
from hashlib import sha256
import json
import pytest

from live_contentops.native_desktop_editorial_v1 import (
    NativeDesktopTurn,
    DesktopInputRequired,
    validate_visual_decision,
    validate_release_media,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.v1_simple_gemini_newsroom_v1 import (
    _reader_safe_native_article,
    _worker_prompt,
    SimpleGeminiNewsroomError,
    _selected_news_peg_blockers,
    reader_photo_caption,
)
from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    _editorial_data_values,
    build_editorial_data_chart,
)
from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import (
    build_native_derivative_payloads,
)


def decision(kind="ANALYSIS", count=2):
    return {
        "reader_first_version": "DATA_JOURNALISM_V1",
        "story_kind": kind,
        "editorial_thesis": "Controlled argument, never actual story acceptance.",
        "channel_media": {d: ["controlled-distinct-0"] if count else [] for d in (
            "telegram", "discord", "x", "linkedin", "facebook_page", "instagram_business", "threads", "youtube")},
        "charts": [
            {
                "asset_id": f"controlled-distinct-{i}",
                "question": f"Distinct question {i}",
                "why_useful": "Controlled contract",
                "placement_after": f"Section {i}",
                "data_spec": {"controlled": True},
            }
            for i in range(count)
        ],
    }


def test_public_source_date_label_does_not_expose_internal_clock_basis():
    from live_contentops.v1_simple_gemini_newsroom_v1 import native_source_reader_label
    assert native_source_reader_label({"publisher": "Wire", "published_at_source": "EXACT_GOVERNED_SIDECAR_SOURCE_TIMESTAMP",
        "published_at_utc": "2026-10-27T01:32:04Z"}) == "Wire · 2026-10-27"
    assert native_source_reader_label({"publisher": "Source", "published_at_source": "2026-10-21",
        "published_at_utc": "2026-10-21T00:00:00Z"}) == "Source · 2026-10-21"
    assert native_source_reader_label({"publisher": "Retained", "published_at_source": "UNESTABLISHED"}) == "Retained"


def chart_packet():
    text = "Comparable 2025 revenue 100 USD million; 2026 revenue 120 USD million."
    doc = {
        "document_id": "controlled",
        "url": "https://example.org/source",
        "publisher": "Controlled fixture",
        "canonical_content_text": text,
        "source_reuse_constraints": {
            "attribution_required": True,
            "policy_capture_sha256": "a" * 64,
            "source_capture_sha256": "b" * 64,
        },
    }
    points = []
    for i, (period, value) in enumerate((("2025", 100), ("2026", 120))):
        points.append(
            {
                "period": period,
                "value": value,
                "observation_kind": "REPORTED_ACTUAL",
                "inputs": [
                    {
                        "document_id": "controlled",
                        "support_excerpt": text,
                        "value_text": str(value),
                        "source_period_text": period,
                        "source_content_sha256": sha256(text.encode()).hexdigest(),
                        "metric": "Revenue",
                        "unit": "USD million",
                        "prepared_period": period,
                        "binding_basis": "ACTUAL_LIGHT_EXACT_SERIES_AND_PERIOD_INDEX",
                        "period_basis": {
                            "series_periods": ["2025", "2026"],
                            "period_index": i,
                            "prepared_value": value,
                            "series_sha256": "c" * 64,
                        },
                    }
                ],
            }
        )
    return {
        "asset_id": "controlled-dj-chart-r1",
        "chart_type": "grouped_bar",
        "question": "Controlled persistence question",
        "title": "Controlled fixture, no editorial acceptance",
        "unit": "USD million",
        "series": [{"name": "Revenue", "points": points}],
        "source_caption": "Source: controlled fixture, not real data.",
        "missingness": [],
    }, [doc]


def test_analytical_one_chart_holds_and_explicit_news_zero_is_valid():
    with pytest.raises(ValueError, match="TWO_TO_FIVE"):
        validate_visual_decision(decision(count=1))
    news = decision("NEWS", 0)
    with pytest.raises(ValueError, match="EXCEPTION_REASON"):
        validate_visual_decision(news)
    news["exception_reason"] = (
        "A narrow attributed announcement has no defensible useful quantitative comparison."
    )
    with pytest.raises(ValueError, match="INSTAGRAM_REQUIRES_EDITOR_SELECTED_IMAGE"):
        validate_visual_decision(news)
    news["contextual_photo_ids"] = ["controlled-photo"]
    news["channel_media"]["instagram_business"] = ["controlled-photo"]
    assert validate_visual_decision(news) == news
    duplicate = decision()
    duplicate["charts"][1]["asset_id"] = duplicate["charts"][0]["asset_id"]
    with pytest.raises(ValueError, match="DISTINCT"):
        validate_visual_decision(duplicate)
    with pytest.raises(ValueError, match="MAX_VISUAL"):
        validate_release_media(
            {"article": {"reader_first_version": "DATA_JOURNALISM_V1"}}
        )


def test_original_chart_values_units_periods_and_source_hash_fail_closed(tmp_path):
    packet, docs = chart_packet()
    assert _editorial_data_values(packet, docs) == [[100, 120]]
    for field, value, error in (
        ("unit", "GBP million", "DIMENSION"),
        ("value_text", "20", "EXACT_VALUE"),
        ("prepared_period", "2024", "PREPARED_PERIOD"),
        ("source_content_sha256", "d" * 64, "HASH"),
    ):
        bad = deepcopy(packet)
        bad["series"][0]["points"][1]["inputs"][0][field] = value
        with pytest.raises(ValueError, match=error):
            _editorial_data_values(bad, docs)
    asset = build_editorial_data_chart(packet, docs, output_dir=tmp_path)
    changed = deepcopy(packet)
    changed["title"] = "Changed packet must use distinct identity"
    with pytest.raises(ValueError, match="ID_ALREADY_BOUND"):
        build_editorial_data_chart(changed, docs, output_dir=tmp_path)
    other = deepcopy(packet)
    other["asset_id"] = "controlled-second-chart-r1"
    second = build_editorial_data_chart(other, docs, output_dir=tmp_path)
    assert asset["path"] != second["path"]


@pytest.mark.parametrize("values", [(83.1,82.5),(31.2,33.0),(82.5,82.5),(82.50,82.51)])
def test_paired_label_years_stay_bound_for_falling_rising_equal_and_close(values):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import _label_paired_endpoints
    fig,ax=plt.subplots()
    _label_paired_endpoints(ax,values,0,["2025","2026"],["#718e8a","#12666a"],suffix="%")
    for index,annotation in enumerate(ax.texts):
        assert annotation.xy==(values[index],0)
        assert annotation.get_text()==f"{2025+index}: {values[index]:g}%"
        if values[0]!=values[1]:
            assert (annotation.get_position()[0]<0)==(values[index]<values[1-index])
        assert annotation.arrow_patch is not None
    assert ax.texts[0].get_position()[1]<0<ax.texts[1].get_position()[1]
    plt.close(fig)


@pytest.mark.parametrize("kind", ["horizontal_diverging_bar", "SMALL_MULTIPLE_HORIZONTAL_DIVERGING_BARS"])
@pytest.mark.parametrize("numbers", [(-10, -8, -5), (0, 0, 0), (2, 5, 10), (-10, 0, 2), (-10000, 100, 2000)])
def test_signed_horizontal_marks_zero_and_labels_remain_inside_actual_axes(kind, numbers):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import _draw_editorial_chart

    rows = [list(numbers)]
    if kind == "SMALL_MULTIPLE_HORIZONTAL_DIVERGING_BARS":
        rows.append([n / 2 for n in numbers])
    packet = {"chart_type": kind, "title": "Controlled signed-geometry regression",
        "unit": "Controlled units", "source_caption": "Synthetic test data; not an article.",
        "series": [{"label": f"Series {i + 1}", "points": [{"period": f"Q{q + 1} 2026"} for q in range(3)]}
            for i in range(len(rows))]}
    fig = _draw_editorial_chart(packet, rows, plt, np)
    try:
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        domains = []
        for ax, expected in zip(fig.axes, rows):
            low, high = ax.get_xlim()
            domains.append((low, high))
            assert low < 0 < high  # Includes the baseline for all-negative and all-zero data.
            assert [mark.get_x() for mark in ax.patches] == [0] * len(expected)
            assert [mark.get_width() for mark in ax.patches] == expected
            for mark, value in zip(ax.patches, expected):
                endpoint = ax.transData.transform((mark.get_x() + mark.get_width(), 0))[0]
                baseline = ax.transData.transform((0, 0))[0]
                assert ax.bbox.x0 <= endpoint <= ax.bbox.x1
                assert (endpoint - baseline) * value >= 0
            for label in ax.texts:
                box = label.get_window_extent(renderer)
                assert ax.bbox.x0 <= box.x0 <= box.x1 <= ax.bbox.x1
                assert "%" not in label.get_text()  # Never relabel a non-percent unit as percent.
        assert len(set(domains)) == 1  # Every small multiple uses the same actual scale.
    finally:
        plt.close(fig)


def test_signed_horizontal_percent_labels_keep_the_declared_unit():
    import matplotlib.pyplot as plt
    import numpy as np
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import _draw_editorial_chart

    packet = {"chart_type": "horizontal_diverging_bar", "title": "Controlled percentage comparison",
        "unit": "% versus prior year", "source_caption": "Synthetic percent regression data.",
        "series": [{"label": "Controlled", "points": [{"period": "2025"}, {"period": "2026"}]}]}
    fig = _draw_editorial_chart(packet, [[-3.2, 21.2]], plt, np)
    try:
        assert [label.get_text() for label in fig.axes[0].texts] == ["-3.2%", "+21.2%"]
    finally:
        plt.close(fig)


def test_point_bound_chart_links_exclude_wrong_quarter_and_retain_multiple_sources(tmp_path):
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import editorial_chart_source_links,validate_editorial_data_chart
    packet,docs=chart_packet()
    unrelated={**docs[0],"document_id":"unused","url":"https://example.org/wrong-quarter"}
    asset=build_editorial_data_chart(packet,[unrelated,*docs],output_dir=tmp_path)
    assert asset["source_page_url"]==docs[0]["url"]
    assert [s["document_id"] for s in asset["source_links"]]==["controlled"]
    second={**docs[0],"document_id":"second","url":"https://example.org/second-quarter"}
    multi=deepcopy(packet)
    multi["series"][0]["points"][1]["inputs"][0]["document_id"]="second"
    assert [s["url"] for s in editorial_chart_source_links(multi,[unrelated,second,*docs])]==[docs[0]["url"],second["url"]]
    asset["source_links"][0]["url"]=unrelated["url"]
    with pytest.raises(ValueError,match="SOURCE_LINKS_CHANGED"):
        validate_editorial_data_chart(asset,[unrelated,*docs])


def test_reviewed_media_correction_invalidates_keep_and_checks_exact_revision(tmp_path,monkeypatch):
    from live_contentops.native_desktop_editorial_v1 import bind_editorial_media,native_review_revision,validated_native_review
    from live_contentops.contentops_editorial_desk_v1 import record_native_article_review
    import live_contentops.v1_simple_gemini_newsroom_v1 as compiler
    store=ContentOpsDurableStore(tmp_path/"controlled.sqlite3")
    run="controlled-media-correction"
    work="cc-opportunity-"+sha256_of(run)
    store.create_work_item(story_id=work,work_item_id=work,title="Controlled",target_surface="CONTENTOPS_EDITORIAL_ONLY")
    path=tmp_path/"controlled.png"
    path.write_bytes(b"controlled")
    asset={"asset_id":"chart","path":str(path),"sha256":sha256(path.read_bytes()).hexdigest(),"caption":"Prior caption","alt_text":"Controlled chart","source_page_url":"https://example.org/source","underlying_source_rights_status":"public_domain"}
    result={"model_execution_state":"NATIVE_DESKTOP_REQUEST_RETURN","qualified_article_count":1,"article_identity":"a"*64,
        "article":{"title":"Controlled","substack_body_markdown":"Fact [[SOURCE:SOURCE_1]].","resolved_article_mode":"DATA_OR_DOCUMENT_LENS"},
        "media_assets":[asset],"evidence":[{"source_id":"SOURCE_1","url":asset["source_page_url"],"published_at_utc":"2026-10-21T00:00:00Z"}],
        "simple_result":{"publication_lifecycle_plan":{"plan_hash":"b"*64}}}
    key="cc-editorial-final-"+sha256_of(run)
    store.register_outbox_message(message_id=key,work_item_id=work,destination="internal:cc-report-simple-result",payload=json.dumps(result),status="EDITORIAL_INTERNAL")
    record_native_article_review(store,run_id=run,article_identity=result["article_identity"],decision="KEEP",rationale="Controlled revision review, not owner acceptance.")
    changed={**asset,"caption":"Corrected caption"}
    with pytest.raises(ValueError,match="EXACT_REVIEWED_REVISION"):
        bind_editorial_media(store,run_id=run,article_identity=result["article_identity"],assets=[changed])
    monkeypatch.setattr(compiler,"_native_preview_bundle",lambda **_:({"packages":{"telegram":{"text":"Controlled"}}},[]))
    bind_editorial_media(store,run_id=run,article_identity=result["article_identity"],assets=[changed],expected_package_revision=native_review_revision(result))
    with pytest.raises(ValueError,match="NATIVE_REVIEW_REVISION_CHANGED"):
        validated_native_review(store,run_id=run)


def test_compact_cash_reference_table_cannot_change_reported_levels(tmp_path):
    packet,docs=chart_packet()
    old,new=packet["series"][0]["points"]
    def point(source,period,negative=False):
        p=deepcopy(source)
        p.update(period=period,scale=-1 if negative else 1,value=-source["value"] if negative else source["value"])
        if negative:
            p["sign_presentation_reason"]="Controlled reconciliation removes this reported quantity."
        return p
    labels=["Opening","Financing","Capital expenditure","Reported total"]
    reference=[{"name":year,"points":[point(source,label,j in {1,2}) for j,label in enumerate(labels)]} for year,source in [("2025",old),("2026",new)]]
    packet.update(chart_type="HORIZONTAL_CHANGE_BRIDGE_WITH_REPORTED_LEVELS",reported_reference_series=reference,subtitle="Controlled periods and units",
        render_spec={"height_inches":8.8,"value_domain":[0,150],"row_order":labels,"small_note":"Controlled rounding note.",
            "reference_table":{"columns":["Reported levels","2025","2026"],"rows":[{"label":name,"values":[100 if j!=2 else -100,120 if j!=2 else -120]} for j,name in enumerate(labels)]}})
    packet["series"]=[{"name":"Controlled change","points":[point(new,label) for label in labels]}]
    asset=build_editorial_data_chart(packet,docs,output_dir=tmp_path)
    assert asset["width"]==1120 and asset["height"]==1760
    packet["reader_table"]={"caption":"Reported levels | USD million", "unit":"USD million",
        "columns":["2025","2026"],"rows":deepcopy(packet["render_spec"]["reference_table"]["rows"]),
        "definition_note":"Controlled definitions.","reconciliation_note":"Controlled reconciliation.","scope_note":"Controlled scope."}
    packet["support_caption"]="Controlled source-bound supporting context."
    packet["derivative_context"]={"fallback_when_html_table_absent":"Controlled reported levels and scope."}
    packet["asset_id"]="controlled-dj-chart-with-table-r2"
    asset=build_editorial_data_chart(packet,docs,output_dir=tmp_path)
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import validate_editorial_data_chart
    assert asset["reader_table"]["columns"]==["2025","2026"]
    assert asset["support_caption"]==packet["support_caption"]
    assert asset["distribution_context"]==packet["derivative_context"]["fallback_when_html_table_absent"]
    for mutation in ("year", "level"):
        altered=deepcopy(packet)
        if mutation=="year":
            altered["reader_table"]["columns"].reverse()
        else:
            altered["reader_table"]["rows"][0]["values"][0]+=1
        with pytest.raises(ValueError,match="READER_TABLE_YEAR_OR_VALUES_CHANGED"):
            _editorial_data_values(altered,docs)
    asset["reader_table"]["rows"][0]["values"][0]+=1
    with pytest.raises(ValueError,match="READER_CONTEXT_CHANGED"):
        validate_editorial_data_chart(asset,docs)
    packet["render_spec"]["reference_table"]["rows"][3]["values"][1]=119
    with pytest.raises(ValueError,match="REFERENCE_LEVELS_CHANGED"):
        _editorial_data_values(packet,docs)


def _signed_cash_render_packet(sign=1):
    values = [sign * v for v in (2638, -1900, -133, 606)]
    return {
        "title": "A smaller gain after IBM's cash adjustments",
        "subtitle": "Nine months ended September 30 | 2026 minus 2025 | USD million",
        "value_roles": {"rounded_component_sum": {"value": sum(values[:3])},
            "reported_gain_minus_rounded_component_sum": {"value": values[3] - sum(values[:3])}},
        "render_spec": {"width_inches": 5.6, "height_inches": 13.2,
            "plotted_point_indices": [0, 1, 2], "value_domain": [-3000, 3000],
            "palette": {"background": "#FAF8F4", "company_total": "#183D40", "negative": "#B46632",
                        "neutral": "#778C8A", "positive": "#136C70"},
            "contribution_panel_title": "Three changes in the cash reconciliation",
            "component_rows": [{"point_ref": {"series_index": 0, "point_index": index},
                "display_label": label, "display_value": f"{value:+,.0f}", "start": 0, "end": value,
                "direction": "LEFT_FROM_ZERO" if value < 0 else "RIGHT_FROM_ZERO",
                "color_role": "negative" if value < 0 else "positive"}
                for index, (label, value) in enumerate(zip([
                    "GAAP operating-cash gain", "Larger removal of\nFinancing receivables", "Higher net capital spending"], values[:3]))],
            "axis": {"domain": [-3000, 3000], "visible": True, "ticks": [-3000, -1500, 0, 1500, 3000],
                "tick_labels": ["-3,000", "-1,500", "0", "+1,500", "+3,000"], "axis_label": "Change | USD million",
                "direction_key": {"negative_half": "← Reduces free-cash gain", "positive_half": "Adds to free-cash gain →"},
                "grid": {"values": [-3000, -1500, 1500, 3000], "color": "#D8DEDA"}},
            "reported_result_panel": {"point_ref": {"series_index": 0, "point_index": 3}, "display_value": f"{values[3]:+,.0f}",
                "heading": "Reported IBM-defined free-cash gain", "background": "#EEF1EB",
                "definition": "Company-defined non-GAAP measure", "reported_levels": "7,181 in 2025 → 7,787 in 2026"},
            "reference_table": {"heading": "Reported nine-month levels | USD million", "year_order": [2025, 2026],
                "rows": [{"label": label, "values": pair} for label, pair in [
                    ("GAAP operating cash flow", [9153, 11791]), ("Less: Financing-receivables change", [905, 2805]),
                    ("Net capital expenditures (signed)", [-1067, -1200]), ("IBM-defined free cash flow", [7181, 7787])]],
                "definition_note": "GAAP operating cash flow; IBM-defined free cash flow is non-GAAP."},
            "scope_note": "Consolidated IBM cash; not Software cash conversion or a full cash-balance bridge."}}, [values]


@pytest.mark.parametrize("sign", [1, -1])
def test_signed_cash_actual_marks_use_common_zero_and_keep_reported_result_out_of_sum(sign):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import to_rgba
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import _draw_signed_cash_contributions

    packet, values = _signed_cash_render_packet(sign)
    fig = _draw_signed_cash_contributions(packet, values, plt)
    canvas, plot = fig.axes
    assert len(plot.patches) == 3
    assert plot.get_xscale() == "linear" and plot.get_xlim() == (-3000, 3000)
    assert list(plot.get_xticks()) == [-3000, -1500, 0, 1500, 3000]
    assert plot.spines["bottom"].get_visible()
    for index, (bar, value) in enumerate(zip(plot.patches, values[0][:3])):
        assert bar.get_gid() == f"cash-contribution-{index}"
        assert bar.get_x() == 0 and bar.get_width() == value
        start, end = plot.transData.transform([(0, 0), (value, 0)])[:, 0]
        assert (end < start) == (value < 0)
        role = "negative" if value < 0 else "positive"
        assert bar.get_facecolor() == to_rgba(packet["render_spec"]["palette"][role])
    visible = "\n".join(text.get_text() for axis in fig.axes for text in axis.texts)
    expression = ("+2,638 - 1,900 - 133 = +605" if sign == 1 else "-2,638 + 1,900 + 133 = -605")
    assert expression in visible and f"Reported gain: {sign * 606:+,}" in visible
    assert "$1 million rounding difference." in visible
    assert not any(abs(bar.get_width()) == 606 for bar in plot.patches)
    assert plot.get_xlabel() == "Change | USD million"
    plt.close(fig)


def test_signed_cash_all_essential_text_stays_inside_actual_rendered_image():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import _draw_signed_cash_contributions

    packet, values = _signed_cash_render_packet()
    fig = _draw_signed_cash_contributions(packet, values, plt)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    texts = [text for axis in fig.axes for text in [*axis.texts,
        *([*axis.get_xticklabels(), axis.xaxis.label] if axis.axison else [])] if text.get_text()]
    for text in texts:
        box = text.get_window_extent(renderer)
        assert 0 <= box.x0 <= box.x1 <= fig.bbox.width, text.get_text()
        assert 0 <= box.y0 <= box.y1 <= fig.bbox.height, text.get_text()
    plt.close(fig)


@pytest.mark.parametrize("mutation", ["result_as_component", "wrong_direction", "missing_zero", "invented_rounding"])
def test_signed_cash_rejects_misleading_geometry_or_result_semantics(mutation):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import _draw_signed_cash_contributions

    packet, values = _signed_cash_render_packet()
    if mutation == "result_as_component":
        packet["render_spec"]["plotted_point_indices"].append(3)
    elif mutation == "wrong_direction":
        packet["render_spec"]["component_rows"][1]["end"] = 1900
    elif mutation == "missing_zero":
        packet["render_spec"]["axis"]["ticks"].remove(0)
    else:
        packet["value_roles"]["rounded_component_sum"]["value"] += 606
    with pytest.raises(ValueError, match="SIGNED_CASH_"):
        _draw_signed_cash_contributions(packet, values, plt)


def _compact_cash_render_packet(sign=1):
    packet, values = _signed_cash_render_packet(sign)
    spec = packet["render_spec"]
    spec.update(title_wrapping={"lines":["A smaller gain after IBM's", "cash adjustments"]},
        subtitle_lines=["Nine months ended September 30", "2026 minus 2025 | USD million"],
        contribution_panel_title="Contribution changes",
        result_marker_point_ref={"series_index":0,"point_index":3},
        source_footer="Source: IBM Q3 2026 results | 21 Oct 2026",
        scope_note="Consolidated IBM cash; not Software cash\nconversion or a full cash-balance bridge.",
        geometry_export_px={"canvas":[1120,1760],"plot_x_limits":[64,1056],"title_top":36,
            "subtitle_top":200,"contribution_heading_top":326,"bar_height":32,
            "contribution_rows":[{"label_top":398,"mark_center_y":478},
                {"label_top":534,"mark_center_y":652},{"label_top":708,"mark_center_y":789}],
            "result_top_rule_y":841,"result_heading_top":866,"result_label_top":936,
            "result_marker_center_y":1019,"shared_axis_y":1080,"reported_fcf_levels_top":1200,
            "rounding_note_top":1280,"scope_note_top":1430,"source_footer_top":1585})
    spec["axis"].update(ticks=[-3000,0,3000],tick_labels=["-3,000","0","+3,000"],
        shared_with_reported_result_marker=True)
    spec["axis"].pop("direction_key")
    spec["reported_result_panel"].update(x_value=values[0][3],marker={"stem_from_zero":False},
        heading="Reported result (non-GAAP)",row_label="IBM-defined free-cash gain",
        reported_levels="2025: 7,181 | 2026: 7,787")
    return packet,values


@pytest.mark.parametrize("sign", [1,-1])
def test_compact_cash_bars_and_separate_result_use_identical_actual_scale(sign):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import _draw_compact_cash_comparison
    packet,values=_compact_cash_render_packet(sign)
    fig=_draw_compact_cash_comparison(packet,values,plt)
    ax,=fig.axes
    assert tuple(fig.canvas.get_width_height())==(1120,1760)
    bars=[p for p in ax.patches if str(p.get_gid()).startswith("cash-contribution-")]
    assert len(bars)==3 and ax.get_xlim()==(-3000,3000) and ax.get_xscale()=="linear"
    for bar,value in zip(bars,values[0][:3]):
        assert bar.get_x()==0 and bar.get_width()==value
        start,end=ax.transData.transform([(0,0),(value,0)])[:,0]
        assert (end<start)==(value<0)
    marker,=[p for p in ax.lines if p.get_gid()=="cash-reported-result"]
    assert list(marker.get_xdata())==[values[0][3]] and marker.get_marker()=="D"
    assert marker.get_linestyle()=="None" and marker.get_transform()==ax.transData
    origin=ax.transData.transform((0,0))[0]
    marker_x=ax.transData.transform((values[0][3],0))[0]
    original_x=ax.transData.transform((values[0][0],0))[0]
    assert (marker_x-origin)/(original_x-origin)==pytest.approx(606/2638)
    assert not any(abs(p.get_width())==606 for p in bars)
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    texts=[*ax.texts,*ax.get_xticklabels()]
    for text in texts:
        box=text.get_window_extent(renderer)
        assert 0<=box.x0<=box.x1<=fig.bbox.width,text.get_text()
        assert 0<=box.y0<=box.y1<=fig.bbox.height,text.get_text()
    visible="\n".join(t.get_text() for t in texts)
    assert "←" not in visible and "→" not in visible
    assert f"Reported {values[0][3]:+,.0f}; $1 million" in visible
    plt.close(fig)


@pytest.mark.parametrize("mutation",["separate_scale","stem","result_as_component","wrong_marker_value"])
def test_compact_cash_rejects_misleading_result_semantics(mutation):
    import matplotlib.pyplot as plt
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import _draw_compact_cash_comparison
    packet,values=_compact_cash_render_packet()
    spec=packet["render_spec"]
    if mutation=="separate_scale":
        spec["axis"]["shared_with_reported_result_marker"]=False
    elif mutation=="stem":
        spec["reported_result_panel"]["marker"]["stem_from_zero"]=True
    elif mutation=="result_as_component":
        spec["plotted_point_indices"].append(3)
    else:
        spec["reported_result_panel"]["x_value"]=605
    with pytest.raises(ValueError,match="SIGNED_CASH_"):
        _draw_compact_cash_comparison(packet,values,plt)


def test_selected_chart_caption_context_reaches_only_affected_native_channel_packages():
    from live_contentops.v1_simple_gemini_newsroom_v1 import _publication_media_metadata,_native_preview_bundle
    choice=decision()
    choice["channel_media"]={d:["cash"] if d in {"discord","instagram_business"} else ["other"] for d in choice["channel_media"]}
    article={"title":"Controlled cash context", "dek":"Reported cash needs its definition.",
        "social_hook":"Reported cash needs its definition.","social_mechanism_summary":"The adjustment changes the comparison.",
        "social_policy_summary":"Use the same period.","social_cross_asset_summary":"Compare reported measures.",
        "substack_body_markdown":"A controlled fixture. [[SOURCE:SOURCE_1]]",
        "reader_first_version":"DATA_JOURNALISM_V1","visual_editorial_decision":choice,
        "public_source_bindings":[{"source_id":"SOURCE_1","publisher":"Controlled","url":"https://example.org/source"}]}
    link={"label":"Controlled Q3","url":"https://example.org/source"}
    assets=[{"asset_id":name,"modality":"source_backed_chart","caption":"Short caption","source_links":[link]} for name in ("cash","other")]
    fallback="Reported levels: 2025 / 2026. Non-GAAP; consolidated scope."
    assets[0]["distribution_context"]=fallback
    published,_=_publication_media_metadata(assets,compact=True)
    assert fallback in published[0]["caption"] and fallback not in published[1]["caption"]
    after,_=_native_preview_bundle(article=article,article_mode="DATA_OR_DOCUMENT_LENS",article_identity="controlled",
        media_asset_ids=["cash","other"],media_assets=assets)
    before,_=_native_preview_bundle(article=article,article_mode="DATA_OR_DOCUMENT_LENS",article_identity="controlled",
        media_asset_ids=["cash","other"],media_assets=[{k:v for k,v in a.items() if k!="distribution_context"} for a in assets])
    for d,payload in after["packages"].items():
        if d in {"discord","instagram_business"}:
            assert fallback in json.dumps(payload) and payload!=before["packages"][d]
            assert payload["media_asset_ids"]==["cash"]
        else:
            assert payload==before["packages"][d]


def test_compact_authored_links_retain_distinct_sources_and_internal_markers():
    article = {
        "reader_first_version": "DATA_JOURNALISM_V1",
        "title": "Controlled title",
        "dek": "Controlled dek",
        "source_date_notice": "Source date internal. Interpretation remains analysis.",
        "substack_body_markdown": "First [[CITE:SOURCE_1|company release]] says a fact. [[SOURCE:SOURCE_1]]\n\n### Cash\n\nSecond source-bound paragraph. [[SOURCE:SOURCE_1]]\n\nPrior comparison. [[SOURCE:SOURCE_2]]",
        "public_source_bindings": [
            {
                "source_id": f"SOURCE_{i}",
                "url": f"https://example.org/{i}",
                "publisher": "Company",
                "reader_label": f"Company Q{i}",
            }
            for i in (1, 2)
        ],
    }
    before = deepcopy(article)
    public = _reader_safe_native_article(article, article_mode="DATA_OR_DOCUMENT_LENS")
    assert article == before
    body = public["substack_body_markdown"]
    assert body.count("https://example.org/1") == 2
    assert "[company release]" in body and "### Cash" in body and "### Sources" in body
    assert (
        "[[SOURCE:" not in body
        and "[[CITE:" not in body
        and "Interpretation remains" not in body
    )
    assert "Source date" not in public["editorial_scope_notice"]
    bad = deepcopy(article)
    bad["substack_body_markdown"] = "[[CITE:SOURCE_8|unbound phrase]]"
    with pytest.raises(SimpleGeminiNewsroomError):
        _reader_safe_native_article(bad, article_mode="DATA_OR_DOCUMENT_LENS")
    with_notes = {**article, "substack_body_markdown": article["substack_body_markdown"]
        + "\n\n## Sources and notes\n\nCompany-defined cash measure. [[SOURCE:SOURCE_1]]"}
    notes_body = _reader_safe_native_article(with_notes, article_mode="DATA_OR_DOCUMENT_LENS")["substack_body_markdown"]
    assert notes_body.count("Sources") == 1
    assert "Company-defined cash measure." in notes_body
    assert "Company Q1" in notes_body and "Company Q2" in notes_body
    linked_notes = {**article, "substack_body_markdown": article["substack_body_markdown"]
        + "\n\n## Sources and notes\n\n[[CITE:SOURCE_1|Current results]] and [[CITE:SOURCE_2|Prior results]]. [[SOURCE:SOURCE_1]] [[SOURCE:SOURCE_2]]"}
    linked_body = _reader_safe_native_article(linked_notes, article_mode="DATA_OR_DOCUMENT_LENS")["substack_body_markdown"]
    assert linked_body.count("Sources") == 1
    assert "Company Q1" not in linked_body and "Company Q2" not in linked_body
    assert "[Current results](https://example.org/1)" in linked_body
    data_notes = {**linked_notes, "substack_body_markdown": linked_notes["substack_body_markdown"].replace(
        "## Sources and notes", "## Sources and data notes")}
    data_body = _reader_safe_native_article(data_notes, article_mode="DATA_OR_DOCUMENT_LENS")["substack_body_markdown"]
    assert data_body.count("Sources") == 1
    assert "Company Q1" not in data_body and "Company Q2" not in data_body


def test_reader_photo_caption_retains_archive_date_and_original_evidence():
    asset = {"caption": "Company headquarters. Archive context image; Commons DateTimeOriginal records 2022-03-27 17:48:57."}
    before = deepcopy(asset)
    assert reader_photo_caption(asset) == "Company headquarters. Archival photograph dated 2022-03-27."
    assert asset == before
    caption = "Archive context, not a photograph of current trading."
    assert reader_photo_caption({"caption": caption}) == caption


def test_channel_photo_preview_shows_compiler_credit_once_without_dropping_unknown_rights():
    """Render the owning React view; compact transport credits use the creator's short name."""
    from pathlib import Path
    import re
    import subprocess
    from live_contentops.v1_simple_gemini_newsroom_v1 import _publication_media_metadata

    ui = Path(__file__).resolve().parents[1] / "ui/contentops_v5"
    asset = {
        "asset_id": "controlled-photo", "modality": "documentary_photo",
        "creator_publisher": "Controlled Photographer\u00a0",
        "attribution": "Controlled Photographer / Controlled Archive, CC BY-SA 2.0. Unchanged original.",
        "caption": "Controlled refinery, United Kingdom, 16 June 2017. Archive photograph; context only.",
        "source_page_url": "https://example.org/controlled-original",
        "license_url": "https://creativecommons.org/licenses/by-sa/2.0",
        "changes_description": "Unchanged original; display resizing only.",
        "path": "controlled-test-only.jpg", "sha256": "a" * 64,
        "preview_data_url": "data:image/png;base64,controlled-test-not-real-media",
        "alt_text": "Controlled archive photograph", "width": 640,
    }
    asset["reader_caption"] = asset["caption"]
    _, credit = _publication_media_metadata([asset], compact=True)
    cases = []
    for name, text, selected_asset, posted in (
        ("compact", credit, asset, False),
        ("posted", credit, asset, True),
        ("extra_notice", credit + " Separate required notice.", asset, False),
        ("wrong_creator", credit.replace("[Controlled Photographer]", "[Different creator]"), asset, False),
        ("wrong_source", credit.replace("https://example.org/controlled-original", "https://example.org/other"), asset, False),
        ("missing_pixels", credit, {**asset, "preview_data_url": None}, False),
    ):
        payload = {"text": "Controlled news copy.\n\n" + text, "media_asset_ids": [asset["asset_id"]]}
        if posted:
            payload["posts"] = [{"text": payload["text"], "media_asset_ids": [asset["asset_id"]]}]
        cases.append({"name": name, "native_edition": [{
            "run_id": "controlled", "article_identity": "controlled", "media_assets": [selected_asset],
            "article": {"title": "Controlled", "dek": "Controlled brief", "substack_body_markdown": "Controlled body."},
            "previews": [{"destination": "instagram_business", "preview_id": "controlled", "payload": payload}],
        }]})
    entry = """
        import React from 'react';
        import { renderToStaticMarkup } from 'react-dom/server';
        import { readFileSync } from 'node:fs';
        import { ReportEditorialWorkspace } from './src/views/ReportEditorialWorkspace.tsx';
        const cases = JSON.parse(readFileSync(0, 'utf8'));
        process.stdout.write(JSON.stringify(cases.map(data => ({name: data.name,
            html: renderToStaticMarkup(React.createElement(ReportEditorialWorkspace, {data}))}))));
    """
    runner = """
        const {buildSync} = require('esbuild');
        const bundle = buildSync({stdin: {contents: process.argv[1], resolveDir: process.cwd(), loader: 'tsx'},
            bundle: true, platform: 'node', format: 'cjs', jsx: 'automatic', write: false,
            define: {'import.meta.env': '{}'}});
        new Function('require', 'module', 'exports', bundle.outputFiles[0].text)(require, {exports: {}}, {});
    """
    completed = subprocess.run(["node", "-e", runner, entry], cwd=ui,
        input=json.dumps(cases), text=True, encoding="utf-8", capture_output=True)
    assert completed.returncode == 0, completed.stderr
    rendered = json.loads(completed.stdout)
    for case in rendered:
        preview = re.search(r'<details[^>]*data-edition-destination="instagram_business"[^>]*>(.*?)</details>',
            case["html"], re.S).group(1)
        assert "Controlled news copy." in preview
        assert 'alt="Controlled archive photograph"' in preview or case["name"] == "missing_pixels"
        if case["name"] in {"compact", "posted"}:
            assert preview.count(asset["caption"]) == 1
            assert "Photo:" not in preview
            assert preview.count('href="' + asset["source_page_url"] + '"') == 1
            assert preview.count('href="' + asset["license_url"] + '"') == 1
        else:
            assert "Photo:" in preview
            if case["name"] == "extra_notice":
                assert "Separate required notice." in preview


@pytest.mark.parametrize("publisher,source_url,short_name", [
    ("Federal Reserve Bank of New York", "https://www.newyorkfed.org/markets/reference-rates/effr", "New York Fed"),
    ("U.S. Energy Information Administration", "https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx", "EIA"),
    ("Yonhap News Agency", "https://en.yna.co.kr/view/AEN20261026001800320", "Yonhap"),
])
def test_native_packages_keep_bound_short_publisher_attribution_without_machine_labels(publisher, source_url, short_name):
    from live_contentops.v1_simple_gemini_newsroom_v1 import _native_preview_bundle

    article = {"title": "Controlled overnight comparison", "dek": "The New York Fed reports a steady median.",
        "social_hook": "The New York Fed reports a steady median.",
        "social_mechanism_summary": "A median does not describe every transaction.",
        "social_policy_summary": "A funding observation does not forecast policy.",
        "social_cross_asset_summary": "The next observation tests persistence.",
        "substack_body_markdown": "The New York Fed reports a steady median. [[SOURCE:SOURCE_1]]",
        "reader_first_version": "DATA_JOURNALISM_V1", "visual_editorial_decision": decision(),
        "public_source_bindings": [{"source_id": "SOURCE_1", "publisher": "Federal Reserve Bank of New York",
            "url": "https://www.newyorkfed.org/markets/reference-rates/effr"}]}
    state = {"primary_reporting_publisher": "Federal Reserve Bank of New York",
        "reader_visible_epistemic_label": "CONFIRMED", "event_confirmation_state": "CONFIRMED"}
    article["public_source_bindings"][0].update(publisher=publisher, url=source_url)
    for key in ("dek", "social_hook", "substack_body_markdown"):
        article[key] = article[key].replace("New York Fed", short_name)
    state["primary_reporting_publisher"] = publisher
    before = deepcopy(article)
    bundle, intents = _native_preview_bundle(article=article, article_mode="DATA_OR_DOCUMENT_LENS",
        article_identity="controlled-not-dispatched", epistemic_state=state,
        media_asset_ids=["controlled-distinct-0", "controlled-distinct-1"])
    assert article == before
    assert len(intents) == bundle["package_count"] == 8
    for destination, payload in bundle["packages"].items():
        text = "\n".join(str(v) for k, v in payload.items() if k in {"text", "full_text", "root_text"})
        assert short_name in text and "CONFIRMED" not in text
        assert payload["media_asset_ids"] == ["controlled-distinct-0"]
        if destination in {"linkedin", "threads"}:
            assert f"Source: {short_name}." in text
    canonical_input = _reader_safe_native_article(article, article_mode="DATA_OR_DOCUMENT_LENS", epistemic_state=state)
    for canonical_url in ("https://example.org/p/pending", "https://example.org/p/read-back"):
        rematerialized = build_native_derivative_payloads(article=canonical_input, selection={},
            canonical_url=canonical_url, media_asset_ids=["controlled-distinct-0", "controlled-distinct-1"])
        for destination in ("linkedin", "threads"):
            visible = rematerialized[destination].get("full_text") or rematerialized[destination]["text"]
            assert f"Source: {short_name}." in visible
            assert rematerialized[destination]["media_asset_ids"] == ["controlled-distinct-0"]
    unbound = {**article, "public_source_bindings": []}
    with pytest.raises(SimpleGeminiNewsroomError, match="epistemic_state_missing"):
        _native_preview_bundle(article=unbound, article_mode="DATA_OR_DOCUMENT_LENS",
            article_identity="controlled-not-dispatched", epistemic_state=state,
            media_asset_ids=["controlled-distinct-0", "controlled-distinct-1"])
    wrong_host = {**article, "public_source_bindings": [{**article["public_source_bindings"][0],
        "url": "https://example.org/unrelated-report"}]}
    with pytest.raises(SimpleGeminiNewsroomError, match="epistemic_state_missing"):
        _native_preview_bundle(article=wrong_host, article_mode="DATA_OR_DOCUMENT_LENS",
            article_identity="controlled-not-dispatched", epistemic_state=state,
            media_asset_ids=["controlled-distinct-0", "controlled-distinct-1"])
    inflated = {**article, "social_policy_summary": "Confirmed funding stress has arrived."}
    with pytest.raises(SimpleGeminiNewsroomError, match="epistemic_certainty_inflation"):
        _native_preview_bundle(article=inflated, article_mode="DATA_OR_DOCUMENT_LENS",
            article_identity="controlled-not-dispatched", epistemic_state={**state, "event_confirmation_state": "UNCONFIRMED"},
            media_asset_ids=["controlled-distinct-0", "controlled-distinct-1"])


def test_review_binds_actual_public_conversion_and_all_reader_first_previews(monkeypatch):
    from live_contentops.native_desktop_editorial_v1 import native_review_revision
    import live_contentops.v1_simple_gemini_newsroom_v1 as newsroom
    result = {"article_identity": "controlled-article", "article": {
        "title": "Controlled", "reader_first_version": "DATA_JOURNALISM_V1",
        "substack_body_markdown": "Controlled original text.", "visual_editorial_decision": decision()},
        "previews": [{"destination": "x", "payload": {"text": "Controlled preview"}}],
        "simple_result": {"publication_lifecycle_plan": {"plan_hash": "controlled-plan"}}}
    initial = native_review_revision(result)
    changed = deepcopy(result)
    changed["previews"][0]["payload"]["text"] = "Changed after review"
    assert native_review_revision(changed) != initial
    converter = newsroom._reader_safe_native_article
    monkeypatch.setattr(newsroom, "_reader_safe_native_article", lambda *a, **kw: {
        **converter(*a, **kw), "substack_body_markdown": "Different public conversion"})
    assert native_review_revision(result) != initial


def test_native_max_visual_return_restart_and_same_writer_binding(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "controlled.sqlite3")
    run = "controlled-reader-first"
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(
        story_id=work,
        work_item_id=work,
        title="Controlled",
        target_surface="CONTENTOPS_EDITORIAL_ONLY",
    )
    turn = NativeDesktopTurn(
        store, run_id=run, output_dir=tmp_path, owner_manual_validation=True
    )
    with pytest.raises(DesktopInputRequired) as pending:
        turn(
            logical_invocation_id=run + ":visual-edit",
            governed_input={},
            prompt="Controlled visual input",
            validator=lambda raw: (True, None, json.loads(raw), None),
        )
    observation = {
        "surface": "CODEX_NATIVE_SUBAGENT",
        "model": "gpt-6.1-sol",
        "reasoning_effort": "max",
        "invocation_id": "controlled-context",
        "observation_source": "CONTROLLED_TEST_NOT_MODEL_PROOF",
    }
    envelope = {
        "request_sha256": pending.value.request["request_sha256"],
        "output": decision(),
        "invocation_observation": observation,
    }
    turn.submit("visual-edit", envelope)
    restarted = NativeDesktopTurn(
        store, run_id=run, output_dir=tmp_path, owner_manual_validation=True
    )
    assert restarted._get("visual-edit", "response")["output"] == decision()
    turn._put(
        "write",
        "request",
        {
            "request_sha256": "controlled-write",
            "governed_input": {},
            "prompt": "controlled",
        },
    )
    with pytest.raises(ValueError, match="SAME_VISUAL_EDITOR_WRITER"):
        turn.submit(
            "write",
            {
                "request_sha256": "controlled-write",
                "output": {},
                "invocation_observation": {
                    **observation,
                    "invocation_id": "different-context",
                },
            },
        )
    assert "READER_FIRST_DATA_JOURNALISM" in _worker_prompt(
        {"reader_first_version": "DATA_JOURNALISM_V1"}
    )
    assert "READER_FIRST_DATA_JOURNALISM" not in _worker_prompt({})


def test_actual_native_compiler_retains_distinct_subsets_after_canonical_readback():
    destinations = [
        "telegram",
        "discord",
        "x",
        "linkedin",
        "facebook_page",
        "instagram_business",
        "threads",
        "youtube",
    ]
    choices = {
        d: ["chart-a"] if i % 2 == 0 else ["chart-b", "chart-c"]
        for i, d in enumerate(destinations)
    }
    article = {
        "title": "Controlled cash comparison",
        "subtitle": "Cash conversion differs from profitability.",
        "social_hook": "Investment absorbed the cash inflow.",
        "social_mechanism_summary": "Investment absorbed the cash inflow.",
        "social_policy_summary": "The next comparable quarter tests persistence.",
        "social_cross_asset_summary": "Compare spending with operating cash.",
        "substack_body_markdown": "A source-bound controlled comparison, never a real article.",
        "native_brief_layout": True,
        "reader_first_version": "DATA_JOURNALISM_V1",
        "native_destination_media": choices,
        "native_destination_credits": {},
        "native_media_sources": {"chart-a":[{"document_id":"q3","url":"https://example.org/q3","label":"Q3 source"}],
            "chart-b":[{"document_id":"q1","url":"https://example.org/q1","label":"Q1 source"},
                {"document_id":"q2","url":"https://example.org/q2","label":"Q2 source"}]},
    }
    pending = build_native_derivative_payloads(
        article=article,
        selection={},
        canonical_url="https://capitalchronicle.substack.com/p/pending-publication-control",
        media_asset_ids=["chart-a", "chart-b", "chart-c"],
    )
    observed = build_native_derivative_payloads(
        article=article,
        selection={},
        canonical_url="https://capitalchronicle.substack.com/p/actual-controlled-readback",
        media_asset_ids=["chart-a", "chart-b", "chart-c"],
    )
    assert len(pending) == len(observed) == 8
    for destination in destinations:
        assert (
            pending[destination]["media_asset_ids"]
            == observed[destination]["media_asset_ids"]
            == choices[destination]
        )
        assert pending[destination]["media_source_links"]==observed[destination]["media_source_links"]
        assert set(observed[destination]["media_source_links"])<=set(choices[destination])
        posts = observed[destination].get("posts", [])
        if posts:
            assert posts[0]["media_asset_ids"] == choices[destination]
            assert all(not p["media_asset_ids"] for p in posts[1:])
    bad = deepcopy(article)
    bad["native_destination_media"]["x"] = ["unbound-chart"]
    with pytest.raises(ValueError, match="SUBSET_UNBOUND"):
        build_native_derivative_payloads(
            article=bad,
            selection={},
            canonical_url="https://example.org/actual",
            media_asset_ids=["chart-a"],
        )
    empty_instagram = deepcopy(article)
    empty_instagram["native_destination_media"]["instagram_business"] = []
    with pytest.raises(ValueError, match="INSTAGRAM_IMAGE_REQUIRED"):
        build_native_derivative_payloads(article=empty_instagram, selection={},
            canonical_url="https://example.org/actual", media_asset_ids=["chart-a", "chart-b", "chart-c"])


def test_one_prewrite_visual_amendment_preserves_original_and_same_editor(tmp_path, monkeypatch):
    import live_contentops.visual_asset_discovery_v1 as photos
    monkeypatch.setattr(photos, "validate_contextual_photo", lambda asset: None)
    store = ContentOpsDurableStore(tmp_path / "controlled.sqlite3")
    run = "controlled-visual-amendment"
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(story_id=work, work_item_id=work, title="Controlled", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    turn = NativeDesktopTurn(store, run_id=run, output_dir=tmp_path, owner_manual_validation=True)
    with pytest.raises(DesktopInputRequired) as pending:
        turn(logical_invocation_id=run + ":visual-edit", governed_input={}, prompt="Controlled",
            validator=lambda raw: (True, None, json.loads(raw), None))
    observation = {"surface": "CODEX_NATIVE_SUBAGENT", "model": "gpt-6.1-sol", "reasoning_effort": "max",
        "invocation_id": "controlled-same-editor", "observation_source": "CONTROLLED_TEST_NOT_MODEL_PROOF"}
    turn.submit("visual-edit", {"request_sha256": pending.value.request["request_sha256"],
        "output": decision(), "invocation_observation": observation})
    original = turn._get("visual-edit", "response")
    with pytest.raises(DesktopInputRequired) as amended_request:
        turn.request_visual_amendment(reason="Instagram requires a suitable exact selected image.",
            contextual_assets=[{"asset_id": "controlled-photo"}])
    with pytest.raises(DesktopInputRequired):
        turn(logical_invocation_id=run + ":write", governed_input={}, prompt="Controlled",
            validator=lambda raw: (True, None, json.loads(raw), None))
    amended = decision("NEWS", 0)
    amended["exception_reason"] = "Controlled genuine news needs no quantitative comparison."
    amended["contextual_photo_ids"] = ["controlled-photo"]
    amended["channel_media"]["instagram_business"] = ["controlled-photo"]
    envelope = {"request_sha256": amended_request.value.request["request_sha256"], "output": amended,
        "invocation_observation": {**observation, "invocation_id": "different-editor"}}
    with pytest.raises(ValueError, match="SAME_PREWRITER_VISUAL_EDITOR"):
        turn.submit("visual-edit-amend", envelope)
    turn.submit("visual-edit-amend", {**envelope, "invocation_observation": observation})
    restarted = NativeDesktopTurn(store, run_id=run, output_dir=tmp_path, owner_manual_validation=True)
    assert restarted.visual_response()["output"] == amended
    assert restarted._get("visual-edit", "response") == original
    turn._put("write", "request", {"request_sha256": "controlled-write", "governed_input": {}, "prompt": "Controlled"})
    with pytest.raises(ValueError, match="UNBOUND_PREWRITER_VISUAL_AMENDMENT"):
        turn.request_visual_amendment(reason="A later amendment cannot replace frozen writer evidence.",
            contextual_assets=[{"asset_id": "controlled-photo"}])


def test_light_proposal_requires_actual_bound_return_before_max_visual_request(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "controlled.sqlite3")
    run = "controlled-light-then-max"
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(story_id=work, work_item_id=work, title="Controlled", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    turn = NativeDesktopTurn(store, run_id=run, output_dir=tmp_path, owner_manual_validation=True)
    with pytest.raises(DesktopInputRequired) as pending:
        turn(logical_invocation_id=run + ":media-plan", governed_input={}, prompt="Controlled Light",
            validator=lambda raw: (True, None, json.loads(raw), None))
    preparation = {"native_plan_run_id": run, "native_plan_stage": "media-plan",
        "native_plan_request_sha256": pending.value.request["request_sha256"],
        "story_plan": {"thesis": "Controlled proposal", "exact_series": []}}
    with pytest.raises(ValueError, match="COMPLETED_LIGHT_PREPARATION"):
        turn.request_visual_decision(source_packet={"controlled": True}, preparation=preparation)
    turn.submit("media-plan", {"request_sha256": preparation["native_plan_request_sha256"],
        "output": {"story_plan": preparation["story_plan"]}, "invocation_observation": {
            "surface": "CODEX_NATIVE_SUBAGENT", "model": "gpt-6.1-sol", "reasoning_effort": "low",
            "invocation_id": "controlled-light", "observation_source": "CONTROLLED_TEST_NOT_MODEL_PROOF"}})
    with pytest.raises(DesktopInputRequired) as visual:
        turn.request_visual_decision(source_packet={"controlled": True}, preparation=preparation)
    assert visual.value.request["stage"] == "visual-edit"
    assert visual.value.request["requested_reasoning_effort"] == "max"
    assert visual.value.request["governed_input"]["actual_light_preparation"] == preparation
    altered = deepcopy(preparation)
    altered["story_plan"]["thesis"] = "Unreturned replacement"
    with pytest.raises(ValueError, match="COMPLETED_LIGHT_PREPARATION"):
        turn.request_visual_decision(source_packet={}, preparation=altered)


def test_normal_media_entry_resumes_completed_light_and_same_max_without_refreezing(tmp_path):
    from scripts.run_native_desktop_editorial import operation, BINDING_SCHEMA

    root = tmp_path / "reader"
    root.mkdir()
    binding = {"schema_version": BINDING_SCHEMA, "run_id": "controlled-normal-media-entry",
        "store_path": str(tmp_path / "controlled.sqlite3"), "output_dir": str(root),
        "feed_pointer_path": str(tmp_path / "unused-feed.json"),
        "published_memory_store": str(tmp_path / "unused-memory.sqlite3"),
        "published_memory_output_root": str(tmp_path / "unused-memory"), "owner_manual_validation": True}
    (root / "editorial_media_plan_required.json").write_text(json.dumps({"source_pack": []}))
    light_pending = operation(binding, command="media-plan")
    assert light_pending["stage"] == "media-plan"
    store = ContentOpsDurableStore(binding["store_path"], auto_migrate=False)
    turn = NativeDesktopTurn(store, run_id=binding["run_id"], output_dir=root, owner_manual_validation=True)
    frozen_light = turn.frozen_request("media-plan")
    turn.submit("media-plan", {"request_sha256": light_pending["request_sha256"],
        "output": {"story_plan": {"thesis": "Controlled proposal", "exact_series": []}},
        "invocation_observation": {"surface": "CODEX_NATIVE_SUBAGENT", "model": "gpt-6.1-sol",
            "reasoning_effort": "low", "invocation_id": "controlled-light",
            "observation_source": "CONTROLLED_TEST_NOT_MODEL_PROOF"}})
    visual_pending = operation(binding, command="media-plan")
    assert visual_pending["stage"] == "visual-edit"
    assert turn.frozen_request("visual-edit")["requested_reasoning_effort"] == "max"
    turn.submit("visual-edit", {"request_sha256": visual_pending["request_sha256"], "output": decision(),
        "invocation_observation": {"surface": "CODEX_NATIVE_SUBAGENT", "model": "gpt-6.1-sol",
            "reasoning_effort": "max", "invocation_id": "controlled-same-max",
            "observation_source": "CONTROLLED_TEST_NOT_MODEL_PROOF"}})
    # The existing writer may now emit a richer pending media request. That is not new Light input.
    (root / "editorial_media_plan_required.json").write_text(json.dumps({
        "source_pack": [], "visual_editorial_decision": decision(), "visual_request_sha256": visual_pending["request_sha256"]}))
    resumed = operation(binding, command="media-plan")
    assert resumed["classification"] == "NATIVE_VISUAL_PLAN_RETURNED_ASSETS_REQUIRED"
    assert turn.frozen_request("media-plan") == frozen_light
    assert turn._get("visual-edit", "response")["output"] == decision()


def _save_json(path, value):
    raw = json.dumps(value, ensure_ascii=False).encode()
    path.write_bytes(raw)
    return sha256(raw).hexdigest()


def _controlled_primaries(root):
    """Portable synthetic captures, never admitted evidence for the real edition."""
    root.mkdir(parents=True, exist_ok=True)
    policy_text = ("Copyright does not protect facts, but may protect the way these things are expressed.")
    policy = {"status": "PASS", "final_url": "https://www.copyright.gov/help/faq/faq-protect.html",
        "retrieval_method": "READ_ONLY_BROWSEROS_NEO_RENDERED_PAGE", "content_truncated": False,
        "rendered_markdown": policy_text, "rendered_page_sha256": sha256(policy_text.encode()).hexdigest(),
        "canonical_content_text": policy_text, "canonical_content_sha256": sha256(policy_text.encode()).hexdigest(),
        "credential_or_session_material_read": False, "public_write_performed": False,
        "fixture_only": "CONTROLLED_TEST_NOT_REAL_SOURCE"}
    policy_hash = _save_json(root / "policy.json", policy)
    sources = [
        ("controlled-effr", "https://www.newyorkfed.org/markets/reference-rates/controlled-fixture",
         "Controlled overnight rate observations", "Federal Reserve Bank of New York", "ORIGINAL_DATA_PRODUCER"),
        ("controlled-eia", "https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?controlled-fixture",
         "Controlled commercial crude-stock observations", "U.S. Energy Information Administration", "ORIGINAL_DATA_PRODUCER"),
        ("controlled-binary", "https://ir.tesla.com/_flysystem/s3/sec/controlled-fixture.pdf",
         "Controlled quarterly filing facts", "Tesla", "ISSUER"),
        ("controlled-issuer", "https://investors.southwest.com/news-events/press-releases/detail/controlled-fixture",
         "SOUTHWEST CONTROLLED RESULTS: STRATEGY DRIVES MARGIN EXPANSION", "Southwest Airlines", "ISSUER"),
    ]
    records = []
    for identity, url, title, publisher, role in sources:
        text = title + "\nControlled fixture only: reported revenue 100 in 2025 and 120 in 2026, USD million."
        original = {"url": url, "text": text, "observed": "2026-10-24T12:00:00Z"}
        if identity == "controlled-binary":
            binary = b"CONTROLLED_BINARY_FIXTURE_NOT_A_REAL_FILING"
            (root / "controlled.bin").write_bytes(binary)
            original["binary_capture"] = {"path": "controlled.bin", "sha256": sha256(binary).hexdigest(),
                "extracted_text_sha256": sha256(text.encode()).hexdigest()}
        original_path = identity + "-original.json"
        original_hash = _save_json(root / original_path, original)
        capture_path = identity + "-capture.json"
        capture = {"status": "PASS", "url": url, "canonical_content_text": text,
            "source_capture_sha256": original_hash, "public_write_performed": False,
            "credential_or_session_material_read": False, "observed_at_utc": original["observed"],
            "excerpts": [{"start": 0, "end": len(text), "text": text}]}
        capture_hash = _save_json(root / capture_path, capture)
        document = {"document_id": identity, "title": title, "publisher": publisher, "source_url": url,
            "source_interest_role": role, "source_adapter_family": "original_public_facts",
            "source_authority_class": "first_party_public_source" if role == "ISSUER" else "official_public_primary_source",
            "canonical_content_text": text, "canonical_content_sha256": sha256(text.encode()).hexdigest(),
            "raw_sha256": capture_hash, "content_truncated": False, "published_at_utc": "2026-10-23T12:00:00Z"}
        loader_path = identity + "-loader.json"
        _save_json(root / loader_path, {"status": "PASS", "official_source_documents": [document],
            "provenance": {"retrieved_at_utc": original["observed"]}})
        spec = {"headline_id": identity, "headline_text": title, "capture_path": capture_path,
            "loader_result_path": loader_path, "original_capture_path": original_path,
            "original_capture_sha256": original_hash, "source_capture_sha256": capture_hash,
            "authorship_class": "ORIGINAL_PUBLIC_FACTS_ONLY", "public_expression_reuse_allowed": False,
            "policy_url": policy["final_url"], "policy_capture_path": "policy.json",
            "policy_capture_sha256": policy_hash, "policy_retrieved_at_utc": "2026-10-24T12:00:00Z",
            "revision_at_utc": "2026-10-24T13:00:00Z", "proposition_span": [0, len(title)]}
        if identity in {"controlled-effr", "controlled-eia"}:
            terms_path = identity + "-terms.json"
            if identity == "controlled-effr":
                terms_url = "https://www.newyorkfed.org/privacy/termsofuse"
                terms_hash = _save_json(root / terms_path, {"url": terms_url, "text":
                    "Controlled terms: personal or business purposes; modify and create derivative works; "
                    "must include any copyright notice."})
            else:
                terms_url = "https://www.eia.gov/about/copyrights_reuse.php"
                raw = b"Controlled terms: public domain; you may use and/or distribute; protected materials excluded."
                (root / terms_path).write_bytes(raw)
                terms_hash = sha256(raw).hexdigest()
            spec["data_terms"] = {"capture_path": terms_path, "sha256": terms_hash, "url": terms_url}
        records.append(spec)
    index = {"schema_version": "contentops.retained_source_research.v1", "records": records}
    _save_json(root / "index.json", index)
    return index


def test_original_primary_admission_preserves_exact_sources_and_facts_only_scope(tmp_path):
    _controlled_primaries(tmp_path)
    result = RetainedSourceResearch(tmp_path)
    assert len(result.records) == 4 and not result.gaps
    for record in result.records.values():
        permissions = record["source_permissions"]
        assert permissions["public_expression_reuse_allowed"] is False
        assert permissions["images_logos_exhibits_reuse_allowed"] is False
        assert permissions["attribution_required"] is True
    assert result.records["controlled-effr"]["source_permissions"]["data_terms"]["endorsement_granted"] is False


def _isolated_primary(root, headline_id):
    index = _controlled_primaries(root)
    spec = next(r for r in index["records"] if r["headline_id"] == headline_id)
    index["records"] = [spec]
    return index, spec


@pytest.mark.parametrize("mutation,expected", [
    ("expression", "ORIGINAL_FACTS_CAPTURE_INVALID"),
    ("canonical_hash", "ORIGINAL_FACTS_CAPTURE_INVALID"),
    ("source_identity", "ORIGINAL_FACTS_SOURCE_IDENTITY_CHANGED"),
    ("original_bytes", "ORIGINAL_FACTS_SOURCE_BYTES_CHANGED"),
    ("future_clock", "RESEARCH_CLOCK_ORDER_INVALID"),
    ("restricted_terms", "ORIGINAL_DATA_TERMS_NOT_VERIFIED"),
    ("binary_bytes", "ORIGINAL_FACTS_BINARY_OR_EXTRACTION_CHANGED"),
    ("third_party_series", "ORIGINAL_DATA_PRODUCER_IS_THIRD_PARTY_RIGHTS_NOT_ADMITTED"),
])
def test_original_primary_admission_rejects_material_boundary_tampering(tmp_path, mutation, expected):
    headline = "controlled-binary" if mutation == "binary_bytes" else "controlled-eia" if mutation == "third_party_series" else "controlled-effr"
    index, spec = _isolated_primary(tmp_path, headline)
    capture_path = tmp_path / spec["capture_path"]
    loader_path = tmp_path / spec["loader_result_path"]
    original_path = tmp_path / spec["original_capture_path"]
    capture = json.loads(capture_path.read_bytes())
    loader = json.loads(loader_path.read_bytes())
    original = json.loads(original_path.read_bytes())
    if mutation == "expression":
        spec["public_expression_reuse_allowed"] = True
    elif mutation == "canonical_hash":
        loader["official_source_documents"][0]["canonical_content_sha256"] = "0" * 64
        _save_json(loader_path, loader)
    elif mutation == "original_bytes":
        original_path.write_bytes(original_path.read_bytes() + b" ")
    elif mutation == "future_clock":
        loader["provenance"]["retrieved_at_utc"] = "2026-10-26T00:00:00Z"
        _save_json(loader_path, loader)
    elif mutation == "restricted_terms":
        terms_path = tmp_path / spec["data_terms"]["capture_path"]
        terms = json.loads(terms_path.read_bytes())
        terms["text"] = "No commercial use or derivatives allowed."
        spec["data_terms"]["sha256"] = _save_json(terms_path, terms)
    elif mutation == "binary_bytes":
        binary = tmp_path / original["binary_capture"]["path"]
        binary.write_bytes(binary.read_bytes() + b"tampered")
    elif mutation in {"source_identity", "third_party_series"}:
        if mutation == "source_identity":
            original["url"] = "https://www.newyorkfed.org/markets/different-source"
        else:
            original["text"] += " Data Source: Thomson Reuters"
        spec["original_capture_sha256"] = _save_json(original_path, original)
        capture["source_capture_sha256"] = spec["original_capture_sha256"]
        spec["source_capture_sha256"] = _save_json(capture_path, capture)
        loader["official_source_documents"][0]["raw_sha256"] = spec["source_capture_sha256"]
        _save_json(loader_path, loader)
    _save_json(tmp_path / "index.json", index)
    result = RetainedSourceResearch(tmp_path)
    assert not result.records
    assert [g["state"] for g in result.gaps] == [expected]


def test_reference_rate_chart_cannot_drop_required_credit_or_notices():
    packet, sources = chart_packet()
    url = "https://www.newyorkfed.org/markets/reference-rates/effr"
    sources[0]["url"] = url
    sources[0]["source_reuse_constraints"]["data_terms"] = {
        "required_attribution": "Controlled required credit", "url": "https://www.newyorkfed.org/privacy/termsofuse"}
    packet["required_attribution"] = {"attribution": "Controlled required credit",
        "source_url": url, "terms_url": "https://www.newyorkfed.org/privacy/termsofuse",
        "reference_rates_notice": "Controlled reference-rate notice", "non_affiliation_notice": "Controlled no affiliation"}
    assert _editorial_data_values(packet, sources)
    for key in ("attribution", "terms_url", "reference_rates_notice", "non_affiliation_notice"):
        altered = deepcopy(packet)
        altered["required_attribution"].pop(key)
        with pytest.raises(ValueError, match="EDITORIAL_CHART_(DATA_CREDIT|REFERENCE_RATE_NOTICES)_REQUIRED"):
            _editorial_data_values(altered, sources)


def test_short_document_peg_keeps_exact_period_and_issuer_without_title_padding():
    selected = {"headline_text": "Q3 2026 Update", "source_account": "Tesla"}
    article = {"title": "Tesla's cash recovery faces a durability test",
        "dek": "Investment and operating cash moved in different directions.",
        "substack_body_markdown": "Tesla's Q3 2026 Update reports the comparison."}
    assert not _selected_news_peg_blockers(article, selected)
    for changed in (
        {"title": "Another issuer's cash recovery faces a durability test"},
        {"substack_body_markdown": "Tesla's Q2 2026 Update reports the comparison."},
        {"substack_body_markdown": "An unrelated dated article."},
    ):
        assert _selected_news_peg_blockers({**article, **changed}, selected)


def test_issuer_promotional_title_proves_publication_without_proving_its_cause(tmp_path):
    from live_contentops.v1_simple_epistemic_state_v1 import build_epistemic_state

    _controlled_primaries(tmp_path)
    research = RetainedSourceResearch(tmp_path)
    record = research.records["controlled-issuer"]
    title = record["headline_text"]
    request = {"story_context": {"report_provenance": {"event_proposition": title}}}
    result = research.evidence({**request, "headline_ids": [record["headline_id"]]},
        cutoff_utc=record["revision_at_utc"])
    assert result["status"] == "PASS"
    state = result["epistemic_state"]
    assert state["event_proposition_scope"] == "PUBLICATION_OF_EXACT_ISSUER_DOCUMENT_ONLY"
    assert state["issuer_causal_explanation_independently_verified"] is False
    assert 'published a release titled "' in state["event_proposition"]
    doc = result["official_source_documents"][0]
    changed_title, _ = build_epistemic_state(request=request,
        documents=[{**doc, "title": "Different title"}], selected_route="OFFICIAL_PRIMARY")
    assert not (changed_title or {}).get("event_proposition_scope")
    for mutation in (
        {"source_interest_role": "ADVOCATE"},
        {"source_reuse_constraints": {}},
    ):
        altered, blockers = build_epistemic_state(request=request,
            documents=[{**doc, **mutation}], selected_route="OFFICIAL_PRIMARY")
        assert altered is None and "epistemic_selected_event_not_supported_by_route" in blockers
    other_request = {"story_context": {"report_provenance": {
        "event_proposition": "Southwest revenue drives gains across the whole economy in 2026"}}}
    altered, blockers = build_epistemic_state(request=other_request,
        documents=[doc], selected_route="OFFICIAL_PRIMARY")
    assert altered is None and blockers
