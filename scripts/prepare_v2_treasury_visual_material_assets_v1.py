"""Acquire, bind, and visually audit the Treasury repair's source material.

This is a bounded, read-only acquisition step.  It downloads only explicit
government/public-domain/CC-BY sources, recomputes the frozen CFTC rows from
the exact source bytes, and produces a candidate board before motion work.
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import textwrap
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps


TASK_ID = "TASK_CONTENTOPS_V2_TREASURY_OWNER_VISUAL_INTEGRITY_AND_ASSET_DIVERSITY_REPAIR_V1"
STORY_ID = "CFTC_TREASURY_POSITIONING_20260811_SHORT_LONGFORM_V1"
OLD_RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_short_longform_low_cost_audio_20260815")
DEFAULT_RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps\v2_treasury_owner_visual_integrity_diversity_20260815")
PDFTOPPM = Path(r"C:\Users\bullw\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe")
EXPECTED_SOURCE_SHA256 = "e3e4bff2592777fbd9a125e723bdb087b5110b47b95c16e1b376dcb029b44f96"
EXPECTED_ROWS = {
    "UST 2Y NOTE": ("c70fb895f4fa8c3df8f38d3cf3aa0a41a39d52388d8f15289cc02fe7e1303da8", 1_680_389, -1_359_521, -12_900, -25_340),
    "UST 5Y NOTE": ("ec1e9bc0dd9a4c68764c19f95b02bdd4ad8c7f5176cebaa6337ef953b63b76da", 2_883_977, -2_147_744, -79_277, 63_695),
    "UST 10Y NOTE": ("4beffa46b41271563ccb4cd48bc5ef903184e793356a2fc9c3a967a1b7d6bf6e", 2_554_411, -2_163_714, -40_268, 67_956),
}


ASSETS: list[dict[str, Any]] = [
    {
        "asset_id": "CFTC_ENTRANCE_2026",
        "filename": "cftc-entrance-2026.jpg",
        "url": "https://commons.wikimedia.org/wiki/Special:Redirect/file/Commodity_Futures_Trading_Commission_entrance_Washington_DC_2026-03-15_08-47-48.jpg?width=3840",
        "source_page": "https://commons.wikimedia.org/wiki/File:Commodity_Futures_Trading_Commission_entrance_Washington_DC_2026-03-15_08-47-48.jpg",
        "rights": "CC BY 4.0; credit G. Edward Johnson; crop/color treatment allowed; no endorsement implied",
        "family": "documentary_photo",
        "source_material_family": "cftc_institutional_context",
        "orientation": "landscape",
        "crop_notes": "Use entrance/logo as factual CFTC context; preserve visible agency identity.",
        "embedded_text": "CFTC agency sign/logo",
        "selected": True,
        "story_use": ["S01", "S04", "L01", "L02", "L18"],
    },
    {
        "asset_id": "TREASURY_BUILDING_HIGHSMITH",
        "filename": "treasury-building-highsmith.jpg",
        "url": "https://cdn.loc.gov/service/pnp/highsm/16800/16870v.jpg",
        "source_page": "https://www.loc.gov/item/2011635063/",
        "rights": "Library of Congress; Carol M. Highsmith Archive; no known restrictions on publication",
        "family": "documentary_photo",
        "source_material_family": "treasury_institutional_context",
        "orientation": "landscape",
        "crop_notes": "Wide facade; use for Treasury-market institutional context, not as proof of a numeric claim.",
        "embedded_text": "None material",
        "selected": True,
        "story_use": ["L01", "L07", "L12", "L17", "L18"],
    },
    {
        "asset_id": "FED_ECCLES_1937",
        "filename": "fed-eccles-building-1937.jpg",
        "url": "https://commons.wikimedia.org/wiki/Special:Redirect/file/US%20Federal%20Reserve%20Eccles%20Building%201937.jpg?width=3840",
        "source_page": "https://commons.wikimedia.org/wiki/File:US_Federal_Reserve_Eccles_Building_1937.jpg",
        "rights": "Public domain U.S. Federal Reserve Board work",
        "family": "documentary_photo",
        "source_material_family": "fed_institutional_context",
        "orientation": "landscape",
        "crop_notes": "Historic facade; pair with dated 2026 Fed research documents, clearly labeling dates.",
        "embedded_text": "None material",
        "selected": True,
        "story_use": ["S05", "S06", "L10", "L11", "L14"],
    },
    {
        "asset_id": "FED_2026_FIGURE_1",
        "filename": "fed-2026-fig1-exposures-repo-turnover.png",
        "url": "https://www.federalreserve.gov/econres/notes/feds-notes/fig1-4082.png",
        "source_page": "https://www.federalreserve.gov/econres/notes/feds-notes/decomposing-hedge-funds-u-s-treasury-exposures-20260622.html",
        "rights": "Official Federal Reserve research figure; U.S. government source; retain source/date",
        "family": "primary_source_figure",
        "source_material_family": "fed_2026_exposure_research",
        "orientation": "landscape",
        "crop_notes": "Use full figure or an explicitly labeled panel crop; keep axes/source legible.",
        "embedded_text": "Four chart panels, titles, axes, note/source",
        "selected": True,
        "story_use": ["L09", "L10", "L12", "L17"],
    },
    {
        "asset_id": "FED_2026_FIGURE_2",
        "filename": "fed-2026-fig2-holdings-share.png",
        "url": "https://www.federalreserve.gov/econres/notes/feds-notes/fig2-4082.png",
        "source_page": "https://www.federalreserve.gov/econres/notes/feds-notes/decomposing-hedge-funds-u-s-treasury-exposures-20260622.html",
        "rights": "Official Federal Reserve research figure; U.S. government source; retain source/date",
        "family": "primary_source_figure",
        "source_material_family": "fed_2026_exposure_research",
        "orientation": "landscape",
        "crop_notes": "Static full-context figure only; use for portfolio-scale context.",
        "embedded_text": "Holdings share chart, axes, note/source",
        "selected": True,
        "story_use": ["L10", "L17"],
    },
    {
        "asset_id": "FED_2026_FIGURE_3",
        "filename": "fed-2026-fig3-uses.png",
        "url": "https://www.federalreserve.gov/econres/notes/feds-notes/fig3-4082.png",
        "source_page": "https://www.federalreserve.gov/econres/notes/feds-notes/decomposing-hedge-funds-u-s-treasury-exposures-20260622.html",
        "rights": "Official Federal Reserve research figure; U.S. government source; retain source/date",
        "family": "primary_source_figure",
        "source_material_family": "fed_2026_exposure_research",
        "orientation": "landscape",
        "crop_notes": "Use to prove that hedge-fund Treasury exposure contains multiple strategies.",
        "embedded_text": "Stacked chart, legend, axes, note/source",
        "selected": True,
        "story_use": ["S06", "L11", "L12", "L16"],
    },
    {
        "asset_id": "FED_2026_FIGURE_4",
        "filename": "fed-2026-fig4-basis-trade.png",
        "url": "https://www.federalreserve.gov/econres/notes/feds-notes/fig4-4082.png",
        "source_page": "https://www.federalreserve.gov/econres/notes/feds-notes/decomposing-hedge-funds-u-s-treasury-exposures-20260622.html",
        "rights": "Official Federal Reserve research figure; U.S. government source; retain source/date",
        "family": "primary_source_figure",
        "source_material_family": "fed_2026_exposure_research",
        "orientation": "landscape",
        "crop_notes": "Use with $830bn/September 2025 label; not as an August 2026 live estimate.",
        "embedded_text": "Dual-axis chart, legend, axes, note/source",
        "selected": True,
        "story_use": ["S05", "L08", "L10", "L16"],
    },
    {
        "asset_id": "FED_2026_FIGURE_5",
        "filename": "fed-2026-fig5-swap-spread.png",
        "url": "https://www.federalreserve.gov/econres/notes/feds-notes/fig5-4082.png",
        "source_page": "https://www.federalreserve.gov/econres/notes/feds-notes/decomposing-hedge-funds-u-s-treasury-exposures-20260622.html",
        "rights": "Official Federal Reserve research figure; U.S. government source; retain source/date",
        "family": "primary_source_figure",
        "source_material_family": "fed_2026_exposure_research",
        "orientation": "landscape",
        "crop_notes": "Candidate for alternative-strategy context; lower priority than Figure 3.",
        "embedded_text": "Line chart, axes, note/source",
        "selected": True,
        "story_use": ["L11", "L12"],
    },
    {
        "asset_id": "FED_2024_BASIS_FIGURE_2",
        "filename": "fed-2024-basis-fig2-leveraged-short-tenors.png",
        "url": "https://www.federalreserve.gov/econres/notes/feds-notes/fig2-3458.png",
        "source_page": "https://www.federalreserve.gov/econres/notes/feds-notes/quantifying-treasury-cash-futures-basis-trades-20240308.html",
        "rights": "Official Federal Reserve research figure; retain source/date and CFTC data attribution",
        "family": "primary_source_figure",
        "source_material_family": "fed_2024_basis_proxy_research",
        "orientation": "landscape",
        "crop_notes": "Static full-context figure only; historical proxy context, not an August 2026 observation.",
        "embedded_text": "Treasury-tenor short-position chart, axes, note/source",
        "selected": True,
        "story_use": ["S06", "L08", "L11"],
    },
    {
        "asset_id": "FED_2024_BASIS_FIGURE_5",
        "filename": "fed-2024-basis-fig5-net-repo.png",
        "url": "https://www.federalreserve.gov/econres/notes/feds-notes/fig5-3458.png",
        "source_page": "https://www.federalreserve.gov/econres/notes/feds-notes/quantifying-treasury-cash-futures-basis-trades-20240308.html",
        "rights": "Official Federal Reserve research figure; U.S. government source; retain source/date",
        "family": "primary_source_figure",
        "source_material_family": "fed_2024_basis_proxy_research",
        "orientation": "landscape",
        "crop_notes": "Static full-context figure only; historical net-repo proxy context.",
        "embedded_text": "Net-repo chart, axes, note/source",
        "selected": True,
        "story_use": ["S07", "L09", "L13", "L15"],
    },
    {
        "asset_id": "FED_2024_BASIS_FIGURE_6",
        "filename": "fed-2024-basis-fig6-proxy-comparison.png",
        "url": "https://www.federalreserve.gov/econres/notes/feds-notes/fig6-3458.png",
        "source_page": "https://www.federalreserve.gov/econres/notes/feds-notes/quantifying-treasury-cash-futures-basis-trades-20240308.html",
        "rights": "Official Federal Reserve research figure; U.S. government source; retain source/date",
        "family": "primary_source_figure",
        "source_material_family": "fed_2024_basis_proxy_research",
        "orientation": "landscape",
        "crop_notes": "Static full-context figure only; use to show why futures shorts are not an identity.",
        "embedded_text": "TRACE/net-repo/leveraged-short comparison, axes, note/source",
        "selected": True,
        "story_use": ["S06", "L11", "L15", "L16"],
    },
    {
        "asset_id": "FED_2023_POSITIONING_FIGURE_4",
        "filename": "fed-2023-fig4-treasury-tenor-positioning.png",
        "url": "https://www.federalreserve.gov/econres/notes/feds-notes/fig4-3355.png",
        "source_page": "https://www.federalreserve.gov/econres/notes/feds-notes/recent-developments-in-hedge-funds-treasury-futures-and-repo-positions-20230830.html",
        "rights": "Official Federal Reserve research figure; retain source/date and CFTC data attribution",
        "family": "primary_source_figure",
        "source_material_family": "fed_2023_treasury_positioning_research",
        "orientation": "landscape",
        "crop_notes": "Static full-context figure only; historical context distinct from the governed 2026 snapshot.",
        "embedded_text": "2Y/5Y/10Y positioning panels, axes, note/source",
        "selected": True,
        "story_use": ["L01", "L06", "L17"],
    },
    {
        "asset_id": "CBOT_1900_SESSION",
        "filename": "cbot-session-1900.jpg",
        "url": "https://cdn.loc.gov/service/pnp/pan/6a20000/6a20100/6a20124v.jpg",
        "source_page": "https://www.loc.gov/item/2007663560/",
        "rights": "Library of Congress; no known restrictions on publication",
        "family": "archival_photo",
        "source_material_family": "archival_exchange_context",
        "orientation": "panorama",
        "crop_notes": "Archival exchange scene only; not modern Treasury-futures evidence.",
        "embedded_text": "None material",
        "selected": False,
        "rejection_reason": "Visually rich but temporally and instrumentally remote; risks decorative finance imagery.",
        "story_use": [],
    },
    {
        "asset_id": "NYSE_FLOOR_HIGHSMITH",
        "filename": "nyse-floor-highsmith.jpg",
        "url": "https://tile.loc.gov/storage-services/service/pnp/highsm/16000/16025v.jpg",
        "source_page": "https://www.loc.gov/item/2011634218/",
        "rights": "Library of Congress; Carol M. Highsmith Archive; no known restrictions on publication",
        "family": "documentary_photo",
        "source_material_family": "equity_exchange_context",
        "orientation": "landscape",
        "crop_notes": "Equity exchange context, not Treasury-market plumbing.",
        "embedded_text": "Exchange signage/screens",
        "selected": False,
        "rejection_reason": "Wrong market; would create generic-trading-screen decoration rather than factual context.",
        "story_use": [],
    },
]


DOCUMENT_SOURCES = [
    {
        "asset_id": "CFTC_RELEASE_SCHEDULE_2026",
        "filename": "cftc-release-schedule-2026.html",
        "url": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm",
        "source_page": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm",
        "rights": "Official CFTC public source",
        "family": "primary_document",
        "source_material_family": "cftc_official_document",
        "selected": True,
        "story_use": ["L02"],
    },
    {
        "asset_id": "FED_NOTE_2026_HTML",
        "filename": "fed-note-2026.html",
        "url": "https://www.federalreserve.gov/econres/notes/feds-notes/decomposing-hedge-funds-u-s-treasury-exposures-20260622.html",
        "source_page": "https://www.federalreserve.gov/econres/notes/feds-notes/decomposing-hedge-funds-u-s-treasury-exposures-20260622.html",
        "rights": "Official Federal Reserve public research source",
        "family": "primary_document",
        "source_material_family": "fed_2026_exposure_research",
        "selected": True,
        "story_use": ["L10", "L11"],
    },
    {
        "asset_id": "TREASURY_REMARKS_2024_HTML",
        "filename": "treasury-remarks-2024.html",
        "url": "https://home.treasury.gov/news/press-releases/jy2618",
        "source_page": "https://home.treasury.gov/news/press-releases/jy2618",
        "rights": "Official U.S. Treasury public source",
        "family": "primary_document",
        "source_material_family": "treasury_official_document",
        "selected": True,
        "story_use": ["L07", "L12"],
    },
    {
        "asset_id": "FED_BASIS_NOTE_2024_HTML",
        "filename": "fed-basis-note-2024.html",
        "url": "https://www.federalreserve.gov/econres/notes/feds-notes/quantifying-treasury-cash-futures-basis-trades-20240308.html",
        "source_page": "https://www.federalreserve.gov/econres/notes/feds-notes/quantifying-treasury-cash-futures-basis-trades-20240308.html",
        "rights": "Official Federal Reserve public research source",
        "family": "primary_document",
        "source_material_family": "fed_2024_basis_proxy_research",
        "selected": True,
        "story_use": ["S05", "S06", "L08", "L11"],
    },
    {
        "asset_id": "FED_POSITIONING_NOTE_2023_HTML",
        "filename": "fed-positioning-note-2023.html",
        "url": "https://www.federalreserve.gov/econres/notes/feds-notes/recent-developments-in-hedge-funds-treasury-futures-and-repo-positions-20230830.html",
        "source_page": "https://www.federalreserve.gov/econres/notes/feds-notes/recent-developments-in-hedge-funds-treasury-futures-and-repo-positions-20230830.html",
        "rights": "Official Federal Reserve public research source",
        "family": "primary_document",
        "source_material_family": "fed_2023_treasury_positioning_research",
        "selected": True,
        "story_use": ["L01", "L06", "L17"],
    },
]


PDF_SOURCES = [
    {
        "asset_id": "CFTC_TFF_EXPLANATORY_NOTES_PDF",
        "filename": "cftc-tff-explanatory-notes.pdf",
        "url": "https://www.cftc.gov/sites/default/files/idc/groups/public/@commitmentsoftraders/documents/file/tfmexplanatorynotes.pdf",
        "source_page": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm",
        "rights": "Official CFTC public document",
        "source_material_family": "cftc_official_document",
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def download(url: str, target: Path) -> None:
    if target.is_file() and target.stat().st_size:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "CapitalChronicle-ContentOps/1.0 source-material-audit"})
    with urllib.request.urlopen(request, timeout=45) as response, target.open("wb") as output:
        shutil.copyfileobj(response, output)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "arialbd.ttf" if bold else "arial.ttf"
    return ImageFont.truetype(str(Path(r"C:\Windows\Fonts") / name), size)


def document_image(title: str, date: str, kicker: str, body: list[str], source: str, target: Path) -> None:
    image = Image.new("RGB", (1600, 1000), "#f3efe4")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1600, 112), fill="#17334a")
    draw.text((62, 34), kicker.upper(), font=font(28, True), fill="#e4b25f")
    draw.text((62, 155), title, font=font(56, True), fill="#102231")
    draw.text((64, 232), date, font=font(28, True), fill="#486475")
    y = 315
    for paragraph in body:
        for line in textwrap.wrap(paragraph, width=69):
            draw.text((66, y), line, font=font(31), fill="#172a37")
            y += 43
        y += 23
    draw.line((64, 886, 1536, 886), fill="#b5a98f", width=2)
    draw.text((64, 910), source, font=font(21), fill="#516472")
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, quality=95)


def verify_cftc(runtime: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source = OLD_RUNTIME / "authority" / "tff_txt_2026" / "FinFutYY.txt"
    if sha256(source) != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("frozen_cftc_source_hash_mismatch")
    target = runtime / "authority" / "cftc" / "FinFutYY.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    rows: list[dict[str, Any]] = []
    with target.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            name = row["Market_and_Exchange_Names"].split(" - ")[0]
            if row["Report_Date_as_YYYY-MM-DD"] != "2026-08-11" or name not in EXPECTED_ROWS:
                continue
            clean = {key: value.strip() if isinstance(value, str) else value for key, value in row.items()}
            values = {
                "market": name,
                "open_interest": int(clean["Open_Interest_All"]),
                "asset_long": int(clean["Asset_Mgr_Positions_Long_All"]),
                "asset_short": int(clean["Asset_Mgr_Positions_Short_All"]),
                "lever_long": int(clean["Lev_Money_Positions_Long_All"]),
                "lever_short": int(clean["Lev_Money_Positions_Short_All"]),
                "contract_units": clean["Contract_Units"],
            }
            values["asset_net"] = values["asset_long"] - values["asset_short"]
            values["lever_net"] = values["lever_long"] - values["lever_short"]
            values["asset_net_weekly_change"] = int(clean["Change_in_Asset_Mgr_Long_All"]) - int(clean["Change_in_Asset_Mgr_Short_All"])
            values["lever_net_weekly_change"] = int(clean["Change_in_Lev_Money_Long_All"]) - int(clean["Change_in_Lev_Money_Short_All"])
            values["row_sha256"] = hashlib.sha256(json.dumps(clean, sort_keys=True).encode()).hexdigest()
            expected = EXPECTED_ROWS[name]
            observed = (values["row_sha256"], values["asset_net"], values["lever_net"], values["asset_net_weekly_change"], values["lever_net_weekly_change"])
            if observed != expected:
                raise RuntimeError(f"cftc_row_mismatch:{name}:{observed}")
            rows.append(values)
    rows.sort(key=lambda row: ["UST 2Y NOTE", "UST 5Y NOTE", "UST 10Y NOTE"].index(row["market"]))
    if len(rows) != 3:
        raise RuntimeError(f"required_rows_missing:{len(rows)}")
    receipt = {
        "status": "PASS_ZERO_TRUST_EXACT_RAW_ROWS",
        "source_path": str(target),
        "source_url": "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip",
        "source_sha256": sha256(target),
        "report_date": "2026-08-11",
        "rows": rows,
        "checks": ["row byte cleaning + SHA-256", "asset and leveraged net recomputation", "weekly net-change recomputation"],
    }
    write_json(runtime / "receipts" / "cftc_zero_trust_verification.json", receipt)
    return receipt, rows


def cftc_rows_image(rows: list[dict[str, Any]], target: Path) -> None:
    image = Image.new("RGB", (1800, 1120), "#f4f0e6")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1800, 125), fill="#17334a")
    draw.text((62, 32), "CFTC · TRADERS IN FINANCIAL FUTURES", font=font(34, True), fill="#ffffff")
    draw.text((62, 155), "Exact report rows · positions as of 11 August 2026", font=font(48, True), fill="#122734")
    draw.text((64, 222), "Faithful derivative from governed FinFutYY.txt bytes — not a reconstructed estimate", font=font(25), fill="#526875")
    columns = [(64, "CONTRACT"), (350, "OPEN INTEREST"), (710, "ASSET MGR NET"), (1110, "LEVERAGED NET"), (1480, "WEEKLY Δ")]
    y = 325
    draw.rectangle((48, y - 20, 1752, y + 62), fill="#dbe3e1")
    for x, label in columns:
        draw.text((x, y), label, font=font(23, True), fill="#17334a")
    y += 112
    for row in rows:
        draw.line((48, y - 20, 1752, y - 20), fill="#b9b09d", width=2)
        values = [
            row["market"].replace("UST ", ""),
            f'{row["open_interest"]:,}',
            f'{row["asset_net"]:+,}',
            f'{row["lever_net"]:+,}',
            f'{row["asset_net_weekly_change"]:+,} / {row["lever_net_weekly_change"]:+,}',
        ]
        for (x, _), value in zip(columns, values):
            color = "#087d69" if value.startswith("+") else "#a45d08" if value.startswith("-") else "#172a37"
            draw.text((x, y), value, font=font(31, True if x in (710, 1110) else False), fill=color)
        y += 130
    draw.rounded_rectangle((62, 870, 1738, 1008), 18, fill="#fffaf0", outline="#c7b58c", width=3)
    draw.text((88, 898), "BOUNDARY", font=font(24, True), fill="#a45d08")
    draw.text((270, 898), "Categories do not identify firms or motives. Futures shorts ≠ basis exposure.", font=font(29, True), fill="#172a37")
    draw.text((88, 955), f"Source SHA-256 {EXPECTED_SOURCE_SHA256}", font=font(21), fill="#526875")
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, quality=95)


def board(items: list[dict[str, Any]], target: Path) -> None:
    cards: list[Image.Image] = []
    for item in items:
        path = Path(item["local_path"])
        try:
            image = Image.open(path).convert("RGB")
        except Exception:
            continue
        image = ImageOps.fit(image, (520, 292), method=Image.Resampling.LANCZOS)
        card = Image.new("RGB", (560, 390), "#102330")
        card.paste(image, (20, 18))
        d = ImageDraw.Draw(card)
        status = "SELECT" if item.get("selected") else "REJECT"
        color = "#45d3b5" if item.get("selected") else "#ef7b73"
        d.rectangle((20, 318, 142, 357), fill=color)
        d.text((32, 326), status, font=font(20, True), fill="#07131b")
        d.text((158, 322), item["asset_id"][:29], font=font(19, True), fill="#f3efe4")
        d.text((20, 364), f'{item["width"]}×{item["height"]} · {item["source_material_family"]}', font=font(15), fill="#b7c6cf")
        cards.append(card)
    cols = 3
    rows = (len(cards) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 560, rows * 390 + 130), "#07131b")
    d = ImageDraw.Draw(sheet)
    d.text((34, 28), "TREASURY VISUAL MATERIAL · PRE-MOTION ASSET BOARD", font=font(37, True), fill="#f3efe4")
    d.text((36, 78), "Rights, resolution, crop and story-use decisions are recorded in asset_board.json", font=font(21), fill="#9fb4c1")
    for index, card in enumerate(cards):
        sheet.paste(card, ((index % cols) * 560, 130 + (index // cols) * 390))
    target.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(target, quality=93)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    args = parser.parse_args()
    runtime: Path = args.runtime
    assets_dir = runtime / "assets" / "candidates"
    sources_dir = runtime / "authority" / "web_sources"
    retrieved = datetime.now(timezone.utc).isoformat()
    receipt, rows = verify_cftc(runtime)

    items: list[dict[str, Any]] = []
    for spec in ASSETS:
        target = assets_dir / spec["filename"]
        download(spec["url"], target)
        with Image.open(target) as image:
            width, height = image.size
            media_type = Image.MIME.get(image.format, image.format)
        row = dict(spec, local_path=str(target), sha256=sha256(target), bytes=target.stat().st_size,
                   width=width, height=height, media_type=media_type, retrieved_at=retrieved)
        items.append(row)

    for spec in DOCUMENT_SOURCES:
        target = sources_dir / spec["filename"]
        download(spec["url"], target)
        spec["source_sha256"] = sha256(target)

    for spec in PDF_SOURCES:
        target = sources_dir / spec["filename"]
        download(spec["url"], target)
        spec["source_sha256"] = sha256(target)

    fsr_pdf = sources_dir / "financial-stability-report-20260508.pdf"
    download("https://www.federalreserve.gov/publications/files/financial-stability-report-20260508.pdf", fsr_pdf)
    for page in (37, 38, 39):
        fsr_prefix = assets_dir / f"fed-fsr-2026-page-{page}"
        fsr_image = assets_dir / f"fed-fsr-2026-page-{page}.png"
        if not fsr_image.is_file():
            subprocess.run([str(PDFTOPPM), "-f", str(page), "-l", str(page), "-r", "150", "-png", "-singlefile", str(fsr_pdf), str(fsr_prefix)], check=True)

    cftc_notes_pdf = sources_dir / PDF_SOURCES[0]["filename"]
    for page in (1, 4):
        prefix = assets_dir / f"cftc-tff-explanatory-notes-page-{page}"
        image = assets_dir / f"cftc-tff-explanatory-notes-page-{page}.png"
        if not image.is_file():
            subprocess.run([str(PDFTOPPM), "-f", str(page), "-l", str(page), "-r", "180", "-png", "-singlefile", str(cftc_notes_pdf), str(prefix)], check=True)

    derivative_specs = [
        {
            "asset_id": "CFTC_EXACT_ROWS_DERIVATIVE", "filename": "cftc-exact-rows-2026-08-11.png", "family": "primary_data_derivative",
            "source_material_family": "cftc_governed_snapshot",
            "source_page": "https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip", "rights": "Official CFTC data; faithful derivative from exact governed source bytes",
            "story_use": ["S02", "S03", "S04", "L03", "L04", "L05", "L06", "L18"], "selected": True,
            "crop_notes": "Prefer full table; in portrait use one contract row at a time with derivative label visible.", "embedded_text": "Exact values, date, evidence boundary, source SHA-256",
        },
        {
            "asset_id": "CFTC_RELEASE_SCHEDULE_DERIVATIVE", "filename": "cftc-release-schedule-derivative.png", "family": "primary_document_derivative",
            "source_material_family": "cftc_official_document",
            "source_page": DOCUMENT_SOURCES[0]["source_page"], "rights": "Official CFTC page; faithful editorial excerpt tied to cached HTML SHA-256",
            "story_use": ["L02"], "selected": True, "crop_notes": "Full document view then August 14 highlight; never imply live data.", "embedded_text": "Release convention and August 2026 dates",
        },
        {
            "asset_id": "FED_NOTE_COVER_DERIVATIVE", "filename": "fed-note-cover-derivative.png", "family": "primary_document_derivative",
            "source_material_family": "fed_2026_exposure_research",
            "source_page": DOCUMENT_SOURCES[1]["source_page"], "rights": "Official Federal Reserve page; faithful editorial excerpt tied to cached HTML SHA-256",
            "story_use": ["L10", "L11"], "selected": True, "crop_notes": "Pair with actual figure; keep June 22, 2026 date and source hash.", "embedded_text": "Title, date, documented $4tn/$3tn/$830bn scale",
        },
        {
            "asset_id": "TREASURY_REMARKS_DERIVATIVE", "filename": "treasury-remarks-derivative.png", "family": "primary_document_derivative",
            "source_material_family": "treasury_official_document",
            "source_page": DOCUMENT_SOURCES[2]["source_page"], "rights": "Official U.S. Treasury page; faithful editorial excerpt tied to cached HTML SHA-256",
            "story_use": ["L07", "L12"], "selected": True, "crop_notes": "Use as institutional source page, not a portrait proxy.", "embedded_text": "Title, date, Treasury-market function excerpt",
        },
        {
            "asset_id": "FED_FSR_2026_PAGE_38", "filename": "fed-fsr-2026-page-38.png", "family": "primary_document_page",
            "source_material_family": "fed_2026_financial_stability_report",
            "source_page": "https://www.federalreserve.gov/publications/files/financial-stability-report-20260508.pdf", "rights": "Official Federal Reserve report page",
            "story_use": ["L13"], "selected": True, "crop_notes": "Static full-context page only; use as narrative bridge into hedge-fund leverage.", "embedded_text": "Dealer funding narrative, insurer leverage figure, hedge-fund leverage introduction",
        },
        {
            "asset_id": "FED_FSR_2026_PAGE_37", "filename": "fed-fsr-2026-page-37.png", "family": "primary_document_page",
            "source_material_family": "fed_2026_financial_stability_report",
            "source_page": "https://www.federalreserve.gov/publications/files/financial-stability-report-20260508.pdf", "rights": "Official Federal Reserve report page",
            "story_use": ["L14"], "selected": True, "crop_notes": "Static full-context page only; dealer leverage/intermediation source.", "embedded_text": "Broker-dealer leverage, profits, intermediation-capacity narrative, sources, page number",
        },
        {
            "asset_id": "FED_FSR_2026_PAGE_39", "filename": "fed-fsr-2026-page-39.png", "family": "primary_document_page",
            "source_material_family": "fed_2026_financial_stability_report",
            "source_page": "https://www.federalreserve.gov/publications/files/financial-stability-report-20260508.pdf", "rights": "Official Federal Reserve report page",
            "story_use": ["S07", "L13", "L14", "L16"], "selected": True, "crop_notes": "Static full-context page only; actual figures 3.11–3.13.", "embedded_text": "Hedge-fund leverage and dealer survey figures 3.11–3.13, sources, page number",
        },
        {
            "asset_id": "CFTC_TFF_EXPLANATORY_PAGE_1", "filename": "cftc-tff-explanatory-notes-page-1.png", "family": "primary_document_page",
            "source_material_family": "cftc_official_document",
            "source_page": PDF_SOURCES[0]["source_page"], "rights": "Official CFTC explanatory-notes page",
            "story_use": ["S04", "L02", "L03"], "selected": True, "crop_notes": "Static full-context page only; classification/source-clock context.", "embedded_text": "TFF category design and Tuesday-position explanation",
        },
        {
            "asset_id": "CFTC_TFF_EXPLANATORY_PAGE_4", "filename": "cftc-tff-explanatory-notes-page-4.png", "family": "primary_document_page",
            "source_material_family": "cftc_official_document",
            "source_page": PDF_SOURCES[0]["source_page"], "rights": "Official CFTC explanatory-notes page",
            "story_use": ["S04", "L02", "L05", "L18"], "selected": True, "crop_notes": "Static full-context page only; classification-limitation context.", "embedded_text": "Potential limitations: CFTC classifies traders, not each trading activity",
        },
        {
            "asset_id": "FED_BASIS_NOTE_2024_DERIVATIVE", "filename": "fed-basis-note-2024-derivative.png", "family": "primary_document_derivative",
            "source_material_family": "fed_2024_basis_proxy_research",
            "source_page": DOCUMENT_SOURCES[3]["source_page"], "rights": "Official Federal Reserve page; faithful editorial excerpt tied to cached HTML SHA-256",
            "story_use": ["S05", "S06", "L08", "L11"], "selected": True, "crop_notes": "Static full-context excerpt only; retain March 8, 2024 date/source.", "embedded_text": "Basis mechanism and proxy limitation",
        },
        {
            "asset_id": "FED_POSITIONING_NOTE_2023_DERIVATIVE", "filename": "fed-positioning-note-2023-derivative.png", "family": "primary_document_derivative",
            "source_material_family": "fed_2023_treasury_positioning_research",
            "source_page": DOCUMENT_SOURCES[4]["source_page"], "rights": "Official Federal Reserve page; faithful editorial excerpt tied to cached HTML SHA-256",
            "story_use": ["L01", "L06", "L17"], "selected": True, "crop_notes": "Static full-context excerpt only; retain August 30, 2023 date/source.", "embedded_text": "Asset-manager long / leveraged-fund short historical mechanism context",
        },
    ]

    cftc_rows_image(rows, assets_dir / derivative_specs[0]["filename"])
    document_image(
        "Commitments of Traders · Release Schedule", "2026 schedule · August releases: 7 · 14 · 21 · 28",
        "CFTC SOURCE CLOCK", ["Reports are usually released Friday at 3:30 p.m. Eastern.", "The release usually includes data from the previous Tuesday.", "The August 14 release corresponds to the August 11 snapshot used here."],
        f"Official CFTC HTML snapshot · SHA-256 {DOCUMENT_SOURCES[0]['source_sha256']}", assets_dir / derivative_specs[1]["filename"])
    document_image(
        "Decomposing Hedge Funds’ U.S. Treasury Exposures", "FEDS Notes · 22 June 2026 · Phillip J. Monin",
        "FEDERAL RESERVE RESEARCH", ["Large hedge funds: $4.0tn gross Treasury exposure as of September 2025.", "$2.4tn long · $1.6tn short · about $3.0tn repo cash borrowing.", "Estimated cash–futures basis trade: about $830bn — substantial, not the entire book."],
        f"Official Federal Reserve HTML snapshot · SHA-256 {DOCUMENT_SOURCES[1]['source_sha256']}", assets_dir / derivative_specs[2]["filename"])
    document_image(
        "Remarks at the 2024 U.S. Treasury Market Conference", "26 September 2024 · U.S. Department of the Treasury",
        "TREASURY MARKET RESILIENCE", ["Treasuries finance the government, support monetary policy, serve as collateral and benchmark global asset prices.", "Resilience work spans transparency, repo reporting, buybacks and central clearing."],
        f"Official Treasury HTML snapshot · SHA-256 {DOCUMENT_SOURCES[2]['source_sha256']}", assets_dir / derivative_specs[3]["filename"])
    document_image(
        "Quantifying Treasury Cash-Futures Basis Trades", "FEDS Notes · 8 March 2024",
        "FEDERAL RESERVE RESEARCH", ["The basis package pairs a repo-financed cash Treasury with a short Treasury future.", "Leveraged-fund short futures are timely but may overestimate basis activity because the category includes other strategies.", "Use futures, repo, TRACE and portfolio measures together."],
        f"Official Federal Reserve HTML snapshot · SHA-256 {DOCUMENT_SOURCES[3]['source_sha256']}", assets_dir / "fed-basis-note-2024-derivative.png")
    document_image(
        "Treasury Futures and Repo Positions", "FEDS Notes · 30 August 2023",
        "FEDERAL RESERVE RESEARCH", ["Asset-manager long futures and leveraged-fund shorts rose together across Treasury tenors.", "The pairing is consistent with basis activity but does not identify every leveraged-fund short as a basis position."],
        f"Official Federal Reserve HTML snapshot · SHA-256 {DOCUMENT_SOURCES[4]['source_sha256']}", assets_dir / "fed-positioning-note-2023-derivative.png")

    for spec in derivative_specs:
        target = assets_dir / spec["filename"]
        with Image.open(target) as image:
            width, height = image.size
            media_type = Image.MIME.get(image.format, image.format)
        source_sha = receipt["source_sha256"] if spec["asset_id"] == "CFTC_EXACT_ROWS_DERIVATIVE" else (
            sha256(fsr_pdf) if spec["asset_id"].startswith("FED_FSR_2026_PAGE_") else
            PDF_SOURCES[0]["source_sha256"] if spec["asset_id"].startswith("CFTC_TFF_EXPLANATORY_PAGE_") else
            next(row["source_sha256"] for row in DOCUMENT_SOURCES if row["source_page"] == spec["source_page"])
        )
        items.append(dict(spec, local_path=str(target), sha256=sha256(target), source_sha256=source_sha,
                          bytes=target.stat().st_size, width=width, height=height, media_type=media_type,
                          orientation="landscape" if width >= height else "portrait", retrieved_at=retrieved))

    selected = [item for item in items if item.get("selected")]
    rejected = [item for item in items if not item.get("selected")]
    board_payload = {
        "schema": "contentops.v2.treasury_asset_board.v2", "task_id": TASK_ID, "story_id": STORY_ID,
        "status": "PASS_PRE_MOTION_ASSET_BOARD_READY", "created_at": retrieved,
        "visual_policy": "CONCRETE_FIRST_ABSTRACT_SECOND; documentary/source/data material before explanatory abstraction",
        "selected": selected, "rejected": rejected,
        "counts": {"candidates": len(items), "selected": len(selected), "rejected": len(rejected),
                   "selected_external_or_source_assets": len(selected),
                   "selected_source_material_families": len({item["source_material_family"] for item in selected}),
                   "presentation_grammars": 0},
        "taxonomy_note": "Source-material families describe actual source provenance/semantics. Presentation grammars are reported from serialized render props and never counted as source-material diversity.",
    }
    write_json(runtime / "contracts" / "asset_board.json", board_payload)
    board(items, runtime / "review" / "pre-motion-asset-board.jpg")

    public = runtime / "render" / "public" / "assets"
    public.mkdir(parents=True, exist_ok=True)
    for item in selected:
        shutil.copy2(item["local_path"], public / Path(item["local_path"]).name)
    write_json(runtime / "receipts" / "asset_acquisition.json", {
        "status": "PASS", "retrieved_at": retrieved, "downloads": len(ASSETS) + len(DOCUMENT_SOURCES) + len(PDF_SOURCES) + 1,
        "selected_assets_copied_to_render_public": len(selected), "network_scope": "explicit read-only sources only",
        "public_writes": 0, "uploads": 0, "browser_profile_uses": 0,
    })
    print(json.dumps({"status": "PASS_PRE_MOTION_ASSET_BOARD_READY", "board": str(runtime / "review" / "pre-motion-asset-board.jpg"), "selected": len(selected), "cftc": receipt["status"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
