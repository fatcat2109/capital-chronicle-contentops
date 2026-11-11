"""CC-465's five native image templates, compiled from structured source fields.

The TradingView download remains an immutable input. Text is measured before
drawing; no clipping, ellipsis, font substitution or type shrinking is used.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from functools import lru_cache
from hashlib import sha256
import io
import math
from pathlib import Path
import re

from PIL import Image, ImageCms, ImageDraw, ImageFont

from .image_template_inputs_v1 import MARKETS, ORDER, digest, validate_binding

POLICY = "CC465_IMAGE_TEMPLATES_V1"
TEMPLATES = ("call", "event", "result", "weekly", "map")
SIZE = {"W": (1600, 900), "T": (1080, 1350)}
CHART = {"W": (0, 104, 1600, 804), "T": (0, 170, 1080, 1020)}
COLOURS = {"paper": "#F5F5F0", "ink": "#111111", "muted": "#4A4A45", "rule": "#D4D4CC",
           "zebra": "#ECECE6", "yellow": "#FDCF09", "green": "#08755A", "red": "#B3261E", "blue": "#1F5FBF"}
FONTS = Path(__file__).parent / "assets" / "cc465"


class LayoutError(ValueError):
    def __init__(self, cause, field="", **details):
        super().__init__(cause)
        self.field, self.details = field, details


@lru_cache(maxsize=80)
def font(size, weight=400, mono=False):
    path = FONTS / ("IBMPlexMono-Medium.ttf" if mono else "PublicSans.ttf")
    result = ImageFont.truetype(str(path), size)
    if not mono:
        result.set_variation_by_axes([weight])
    return result


def price(value, market):
    if value is None:
        return ""
    value = Decimal(str(value))
    if not value.is_finite():
        raise LayoutError("IMAGE_LEVEL_NOT_FINITE")
    places = 4 if market == "EURUSD" else 2 if market in {"USDJPY", "USOIL"} else 0
    return f"{value:,.{places}f}"


def r_text(value):
    if value is None:
        return "No entry"
    num = Decimal(str(value))
    if not num.is_finite():
        raise LayoutError("IMAGE_R_NOT_FINITE")
    return ("+" if num > 0 else "−" if num < 0 else "") + f"{abs(num):.1f}R"


def field(data, key, cap, *, required=True):
    value = data.get(key)
    value = "" if value is None else str(value)
    if len(value) > cap:
        value = str(data.get(key + "_short") or "")
    if not value and required:
        raise LayoutError("IMAGE_WRITER_REVISION_REQUIRED", key, maximum_characters=cap,
                          too_long_by=max(0, len(str(data.get(key) or "")) - cap))
    if len(value) > cap:
        if not required:
            return ""
        raise LayoutError("IMAGE_WRITER_REVISION_REQUIRED", key, maximum_characters=cap,
                          too_long_by=len(value) - cap)
    if "…" in value or "..." in value or "\n" in value:
        raise LayoutError("IMAGE_TEXT_CUT_OR_MULTILINE", key)
    return value


class Canvas:
    def __init__(self, master):
        self.master = master
        self.image = Image.new("RGB", SIZE[master], COLOURS["paper"])
        self.draw = ImageDraw.Draw(self.image)
        self.texts, self.drawings, self.notes = [], [], []
        self.margin = 48 if master == "W" else 40

    def text(self, value, box, *, size=None, weight=400, mono=False, colour="ink", key="", wrap=1, optional=False):
        if not value:
            return
        value = str(value)
        size = size or (36 if self.master == "W" else 34)
        face = font(size, weight, mono)
        x, y, right, bottom = box
        words, lines, current = value.split(), [], ""
        for word in words:
            test = (current + " " + word).strip()
            if self.draw.textlength(test, font=face) > right - x:
                if not current or wrap == 1:
                    if optional:
                        return
                    raise LayoutError("IMAGE_TEXT_DOES_NOT_FIT", key, value=value, size=size)
                lines.append(current); current = word
            else:
                current = test
        lines.append(current)
        if len(lines) > wrap:
            if optional:
                return
            raise LayoutError("IMAGE_TEXT_DOES_NOT_FIT", key, value=value, maximum_lines=wrap)
        for line in lines:
            bounds = self.draw.textbbox((0, 0), line, font=face)
            height = bounds[3] - bounds[1]
            actual = [x, y, x + bounds[2] - bounds[0], y + height]
            if actual[2] > right or actual[3] > bottom:
                raise LayoutError("IMAGE_TEXT_CLIPPED", key, value=value)
            self.draw.text((x-bounds[0], y-bounds[1]), line, font=face, fill=COLOURS.get(colour, colour))
            self.texts.append({"text": line, "box": actual, "zone": list(box), "size": size,
                               "weight": weight, "mono": mono, "colour": colour, "field": key})
            y += size + 8

    def heading(self, title, right="", *, direction=None, horizon="", status=""):
        wide = self.master == "W"
        w = self.image.width; m = self.margin
        self.draw.rectangle((m, 24, m+11, 79 if wide else 95), fill=COLOURS["yellow"])
        title_size = 56 if wide else 64
        title_end = m + 28 + self.draw.textlength(title, font=font(title_size, 700))
        self.text(title, (m+28, 20 if wide else 28, w-m, 92 if wide else 104), size=title_size, weight=700, key="title")
        if direction:
            if direction not in {"LONG", "SHORT"}:
                raise LayoutError("IMAGE_DIRECTION_INVALID")
            x = math.ceil(title_end + 24)
            sw = math.ceil(self.draw.textlength(direction, font=font(36 if wide else 38, 700)))+24
            if x+sw > w-m:
                raise LayoutError("IMAGE_HEADER_COLLISION")
            self.draw.rounded_rectangle((x, 25 if wide else 34, x+sw, 78 if wide else 91), radius=6,
                                        fill=COLOURS["green" if direction == "LONG" else "red"])
            self.text(direction, (x+12, 34 if wide else 44, x+sw-8, 78 if wide else 91),
                      size=36 if wide else 38, weight=700, colour="#FFFFFF", key="direction")
            hx = x+sw+22 if wide else m
            hy = 36 if wide else 113
            self.text(horizon, (hx, hy, w-m, 90 if wide else 162), key="horizon", weight=600)
            if wide:
                title_end = hx + self.draw.textlength(horizon, font=font(36, 600))
        value = right or status
        if value:
            f = font(36 if wide else 38, 600)
            x = w-m-self.draw.textlength(value, font=f)
            if wide and x < title_end+24:
                raise LayoutError("IMAGE_HEADER_COLLISION", "status")
            self.text(value, (x, 36 if wide else 113, w-m, 94 if wide else 166),
                      size=36 if wide else 38, weight=600, key="status")

    def footer(self, lines=(), cells=()):
        m, w = self.margin, self.image.width
        if self.master == "W":
            for i, line in enumerate(lines):
                self.text(line, (m, 808+i*44, w-m, 851+i*44), key="footer")
            y = 852
        else:
            for i, (label, value, mono) in enumerate(cells):
                x, y = m+(i%2)*540, 1030+(i//2)*108
                self.text(label, (x, y, x+460, y+38), size=32, colour="muted", key="cell_label")
                self.text(value, (x, y+40, x+460, y+103), size=48 if mono else 34, mono=mono, key=label)
            if lines:
                self.text(lines[-1], (m, 1248, w-m, 1292), key="footer", optional=False)
            y = 1302
        # Omit the wordmark when it would touch existing copy (spec section 3).
        mark = "CAPITAL CHRONICLE"
        width = self.draw.textlength(mark, font=font(36 if self.master == "W" else 38, 700))
        x = w-m-width
        overlaps = any(t["box"][0] < w-m and t["box"][2]+24 > x and t["box"][1] < y+38
                       and t["box"][3] > y for t in self.texts)
        if not overlaps:
            self.text(mark, (x, y, w-m, self.image.height-7), size=36 if self.master == "W" else 38, weight=700, key="wordmark")


def _paste_chart(canvas, snapshot):
    box = CHART[canvas.master]
    width, height = box[2]-box[0], box[3]-box[1]
    raw = Path(snapshot["path"]).read_bytes()
    if sha256(raw).hexdigest() != snapshot["sha256"]:
        raise LayoutError("IMAGE_CHART_BYTES_CHANGED")
    with Image.open(io.BytesIO(raw)) as source:
        source = source.convert("RGB")
        error = abs(source.width/source.height/(width/height)-1)
        if error > .03:
            raise LayoutError("IMAGE_CHART_CAPTURE_SHAPE", difference=error, maximum=.03)
        scale = min(width/source.width, height/source.height, 1.)
        target = (round(source.width*scale), round(source.height*scale))
        # Never upscale a snapshot. A smaller capture must be retaken.
        if min(target[0]/width, target[1]/height) < .97:
            raise LayoutError("IMAGE_CHART_CAPTURE_TOO_SMALL")
        original_size = source.size
        if source.size != target:
            source = source.resize(target, Image.Resampling.LANCZOS)
        origin = (box[0]+(width-target[0])//2, box[1]+(height-target[1])//2)
        canvas.image.paste(source, origin)
    return {"box": list(box), "original_size": list(original_size), "paste_box": [*origin, origin[0]+target[0], origin[1]+target[1]],
            "scale": scale, "shape_error": error, "paper_margin_fraction": max(1-target[0]/width, 1-target[1]/height)}


def _levels(canvas, data, snapshot, framing):
    from .tradingview_plan_overlay_v1 import _price_y
    plan, market = data.get("plan") or {}, data["market"]
    if not plan:
        return {"required": False, "levels_visible": True}
    scale = snapshot.get("chart_geometry")
    if not scale or scale.get("source_sha256") != snapshot["sha256"]:
        raise LayoutError("IMAGE_PRICE_GEOMETRY_REQUIRED")
    factor = framing["scale"]; ox, oy = framing["paste_box"][:2]
    left, top, right, bottom = scale["pane_box"]
    # The captured pane includes TradingView's legend. Leave it whole.
    left, top, right, bottom = left*factor+ox+12, top*factor+oy+62, right*factor+ox-12, bottom*factor+oy-12
    height = bottom-top
    def py(value):
        return _price_y(scale, value)*factor+oy
    low, high, invalid = (plan.get(k) for k in ("entry_low", "entry_high", "invalidation"))
    if any(v is None for v in (low, high, invalid)):
        raise LayoutError("IMAGE_PLAN_LEVELS_REQUIRED")
    ya, yb = sorted((py(low), py(high)))
    draw = ImageDraw.Draw(canvas.image, "RGBA")
    required_ys = [ya, yb, py(invalid)]
    visible = all(top+.06*height <= y <= bottom-.06*height for y in required_ys)
    if visible:
        draw.rectangle((left, ya, right, yb), fill=(31, 95, 191, 36))
        for y in (ya, yb): draw.line((left,y,right,y), fill=COLOURS["blue"], width=2)
    entries = [("Entry " + price(low, market)+"–"+price(high, market), (ya+yb)/2, "blue")]
    entries.append(("Invalidation "+price(invalid, market), py(invalid), "red"))
    target_visible = False
    if plan.get("target") is not None:
        ty = py(plan["target"])
        target_visible = top <= ty <= bottom and snapshot.get("last_30_days_fill_fraction", 0) >= .35
        if target_visible: entries.append(("Target "+price(plan["target"], market),ty,"green"))
    last_label_end = top
    for label, y, colour in sorted(entries, key=lambda e:e[1]):
        if not top <= y <= bottom:
            continue
        if not label.startswith("Entry"):
            draw.line((left,y,right,y), fill=COLOURS[colour], width=3)
        face = font(28,600); tw = draw.textlength(label, font=face)
        ly = max(top+8, min(y-18,bottom-42), last_label_end)
        if ly+40 > bottom:
            raise LayoutError("IMAGE_LEVEL_LABEL_COLLISION")
        draw.rectangle((left+4,ly-8,left+tw+28,ly+34),fill=(255,255,255,224))
        canvas.text(label,(left+12,ly,left+tw+24,ly+34),size=28,weight=600,colour=colour,key="chart_level")
        last_label_end = ly+46
    return {"required": True, "levels_visible": visible, "pane_box": [left,top,right,bottom],
            "entry_colour": COLOURS["blue"], "target_visible": target_visible}


def _chart(canvas, data, snapshot):
    plan, kind, market = data.get("plan") or {}, data["template"], data["market"]
    framing = _paste_chart(canvas, snapshot)
    levels = _levels(canvas, data, snapshot, framing)
    p = lambda v: price(v, market)
    entry = p(plan.get("entry_low"))+"–"+p(plan.get("entry_high"))
    target = p(plan.get("target"))
    target_line = ("Target "+target+(" (beyond this chart)" if not levels.get("target_visible") else "")) if target else ""
    odds = ""
    main, alt = plan.get("main_probability_pct"), plan.get("alt_probability_pct")
    if main is not None and alt is not None:
        if any(isinstance(v,bool) or not 0 <= v <= 100 or int(v) != v for v in (main,alt)):
            raise LayoutError("IMAGE_PROBABILITY_INVALID")
        odds = f"Main {main:g}% · Alternative {alt:g}%"
    elif plan:
        canvas.notes.append("PROBABILITY_PAIR_ABSENT")
    if kind in {"call", "result"}:
        if plan.get("market_name") != MARKETS.get(market): raise LayoutError("IMAGE_MARKET_NAME_INVALID")
        horizon = field(plan,"horizon_label",10)
        if horizon not in {"Short-term","Mid-term","Long-term"}: raise LayoutError("IMAGE_HORIZON_INVALID")
        if kind == "call":
            status = field(plan,"status_label",18)
            canvas.heading(MARKETS[market],direction=plan.get("direction"),horizon=horizon,status=status)
            line1 = " · ".join(s for s in ("Entry "+entry,"Invalidation "+p(plan.get("invalidation")),target_line) if s)
            line2 = " · ".join(s for s in (odds,"Time exit "+plan["time_exit_et"] if plan.get("time_exit_et") else "") if s)
            cells = [("Entry",entry,True),("Invalidation",p(plan.get("invalidation")),True),
                     ("Target" if target else "Entry window ends",target or plan.get("entry_window_ends_et",""),bool(target)),
                     ("Time exit",plan.get("time_exit_et",""),False)]
            canvas.footer([line1,line2] if canvas.master == "W" else [odds],cells)
        else:
            result = data["result"]
            canvas.heading(MARKETS[market],right=r_text(result.get("r")),direction=plan.get("direction"),horizon=horizon)
            outcome = field(result,"outcome_label",24)
            if outcome not in {"Target reached","Stopped at invalidation","Time exit","Closed early","Expired, no entry"}:
                raise LayoutError("IMAGE_OUTCOME_INVALID")
            line1 = " · ".join(s for s in (outcome,"Held "+str(result.get("held_text") or "") if result.get("held_text") else "",
                     "Best "+r_text(result["best_r"]) if result.get("best_r") is not None else "",
                     "Worst "+r_text(result["worst_r"]) if result.get("worst_r") is not None else "") if s)
            times = " to ".join(s for s in (result.get("entry_time_et"),result.get("exit_time_et")) if s)
            cells=[("Outcome",outcome,False),("Held",result.get("held_text",""),False),
                   ("Best and worst",r_text(result.get("best_r"))+" / "+r_text(result.get("worst_r")),False),
                   ("Entry to exit",result.get("time_range_short") or times,False)]
            canvas.footer([line1,times] if canvas.master == "W" else [],cells)
            path = result.get("path")
            if result.get("r") is not None and not path:
                canvas.notes.append("RESULT_CAPTURE_TIME_COORDINATES_REQUIRED")
            elif path:
                _result_path(canvas,result,snapshot,framing,levels)
    elif kind == "event":
        event = data["event"]
        canvas.heading(field(event,"name",28),field(event,"time_et",30))
        values=[label+" "+field(event,key,16,required=False) for label,key in
                (("Consensus","consensus"),("Previous","previous"),("Implied move","implied_move")) if event.get(key)]
        line=" · ".join(values)
        canvas.footer([line,"Chart: "+MARKETS[market]] if canvas.master == "W" else ["Chart: "+MARKETS[market]],
                      [(label,field(event,key,16,required=False),False) for label,key in (("Consensus","consensus"),("Previous","previous"),("Implied move","implied_move"))])
    else:
        morning=data["map"]
        canvas.heading("Morning map",field(morning,"date_et",16))
        canvas.footer([field(morning,"lead_line",72)] if canvas.master == "W" else [field(morning,"lead_line",72)])
    return framing, levels


def _result_path(canvas,result,snapshot,framing,levels):
    from .tradingview_plan_overlay_v1 import _price_y
    path=result["path"]; box=levels["pane_box"];factor=framing["scale"];ox,oy=framing["paste_box"][:2]
    if path.get("snapshot_sha256") != snapshot["sha256"]:
        raise LayoutError("IMAGE_RESULT_PATH_CAPTURE_CHANGED")
    coordinates=[]
    for name in ("entry","exit"):
        point=path[name];x=point["x"]*factor+ox;y=_price_y(snapshot["chart_geometry"],point["price"])*factor+oy
        if point.get("time_et") != result[name+"_time_et"] or not box[0] <= x <= box[2] or not box[1] <= y <= box[3]:
            raise LayoutError("IMAGE_RESULT_PATH_NOT_IN_VIEW")
        coordinates.append((x,y))
    fraction=(coordinates[1][0]-coordinates[0][0])/(box[2]-box[0])
    if not .4 <= fraction <= .7: raise LayoutError("IMAGE_RESULT_PATH_TIMEFRAME_REQUIRED")
    draw=ImageDraw.Draw(canvas.image,"RGBA")
    draw.rectangle((coordinates[0][0],box[1],coordinates[1][0],box[3]),fill=(17,17,17,15))
    for name,(x,y),colour in zip(("Entry","Exit"),coordinates,("blue","ink")):
        draw.ellipse((x-9,y-9,x+9,y+9),fill=COLOURS[colour])
        label=name+" "+price(path[name.lower()]["price"],result.get("market") or snapshot.get("market") or "USDJPY")
        canvas.text(label,(x-80,y-50,min(x+280,box[2]),y-10),size=28,weight=600,colour=colour,key="chart_level")


def _table(canvas,data,page):
    wide=canvas.master=="W";kind=data["template"];m=canvas.margin;w,h=canvas.image.size
    top=120 if wide else 186;bottom=796 if wide else 1220
    if kind=="event":
        event=data["event"];scenarios=event["scenarios"]
        if not 2 <= len(scenarios) <= 3:raise LayoutError("IMAGE_SCENARIO_COUNT")
        canvas.heading(field(event,"name",28))
        for i,row in enumerate(scenarios):
            y=top+i*(200 if wide else 320);height=200 if wide else 320
            if i%2:canvas.draw.rectangle((m,y,w-m,y+height),fill=COLOURS["zebra"])
            if i==0:canvas.draw.rectangle((m,y,m+11,y+height),fill=COLOURS["yellow"])
            canvas.text(field(row,"name",14),(m+28,y+12,m+330,y+58),weight=600,key="scenario.name")
            canvas.text(str(row["probability_pct"])+"%",(m+350,y+12,m+510,y+58),mono=True,key="scenario.probability")
            canvas.text(field(row,"trigger",30),(m+550 if wide else m+28,y+12 if wide else y+66,w-m-20,y+58 if wide else y+112),key="scenario.trigger")
            canvas.text(field(row,"reading",72),(m+28,y+70 if wide else y+130,w-m-20,y+122 if wide else y+222),wrap=1 if wide else 2,key="scenario.reading")
            x=m+28
            for reaction in row.get("reactions",[]):
                if reaction["market"] not in MARKETS or reaction["direction"] not in {"up","down","flat"}:raise LayoutError("IMAGE_REACTION_INVALID")
                label=MARKETS[reaction["market"]];tw=canvas.draw.textlength(label,font=font(36 if wide else 34))
                ry=y+142 if wide else y+264
                canvas.text(label,(x,ry,x+tw+2,ry+46),key="reaction")
                x+=tw+12;_arrow(canvas,x,ry+10,reaction["direction"]);x+=54
                if x>w-m:raise LayoutError("IMAGE_TEXT_DOES_NOT_FIT","reactions")
            canvas.draw.line((m,y+height,w-m,y+height),fill=COLOURS["rule"],width=2)
    elif kind=="map":
        morning=data["map"];rows=morning["rows"]
        if [r["market"] for r in rows] != list(ORDER):raise LayoutError("IMAGE_MAP_MARKET_ORDER")
        canvas.heading("Morning map",field(morning,"date_et",16))
        for i,row in enumerate(rows):
            y=top+i*(100 if wide else 160)
            if i%2:canvas.draw.rectangle((m,y,w-m,y+(100 if wide else 160)),fill=COLOURS["zebra"])
            canvas.text(MARKETS[row["market"]],(m+12,y+8,m+310,y+54),weight=600,key="map.market")
            canvas.text(price(row["last"],row["market"]),(m+350,y+8,m+600,y+54),mono=True,key="map.last")
            change=row["change_1d_pct"];move=("+" if change>0 else "−" if change<0 else "")+f"{abs(change):.1f}%"
            canvas.text(move,(m+620,y+8,m+795,y+54),mono=True,colour="green" if change>0 else "red" if change<0 else "muted",key="map.change")
            if wide:canvas.text(field(row,"state_word",13),(m+880,y+8,w-m-12,y+54),key="map.state")
            view=field(row,"view_line",34);driver=field(row,"driver_line",34)
            canvas.text("View: "+view,(m+12,y+56,w-m-12,y+100),key="map.view")
            canvas.text("Today: "+driver,(m+820 if wide else m+12,y+56 if wide else y+106,w-m-12,y+100 if wide else y+152),key="map.driver")
    else:
        week=data["week"];limit=6 if wide else 8;rows=week["rows"][page*limit:(page+1)*limit]
        canvas.heading("Weekly scorecard",str(week["start"])+"–"+str(week["end"]))
        stats=f"{week['calls_closed']} calls closed · {week['hit_rate_pct']}% right · {r_text(week['total_r'])} total · {r_text(week['avg_r'])} average"
        canvas.text(stats,(m+12,top+8,w-m-12,top+100),wrap=1 if wide else 2,key="week.stats")
        top+=100 if not wide else 92
        for i,row in enumerate(rows):
            y=top+i*(88 if wide else 108);height=88 if wide else 108
            if i%2:canvas.draw.rectangle((m,y,w-m,y+height),fill=COLOURS["zebra"])
            if wide:
                # Outcome shares a two-line cell; the font stays at 36 px.
                columns=[(12,300,MARKETS[row['market']],False),(320,470,row['direction'],False),
                         (480,695,row['horizon_label'],False),(710,880,"Said "+str(row['main_probability_pct'])+"%",False),
                         (900,1270,row['outcome_label'],False),(1290,1500,r_text(row['r']),True)]
                for a,b,value,mono in columns:canvas.text(value,(m+a,y+8,m+b,y+height-4),mono=mono,wrap=2,key="week.row")
            else:
                canvas.text(MARKETS[row['market']]+" · "+row['direction'],(m+12,y+8,w-m-210,y+54),key="week.market")
                canvas.text(r_text(row['r']),(w-m-200,y+8,w-m-12,y+54),mono=True,key="week.r")
                value=row['horizon_label']+" · Said "+str(row['main_probability_pct'])+"% · "+row['outcome_label']
                canvas.text(value,(m+12,y+58,w-m-12,y+height-4),key="week.row")
        if week.get("wrong_note"):
            note=field(week,"wrong_note",60,required=False)
            canvas.text("Where we were wrong: "+note,(m,810 if wide else 1240,w-m,h-12),key="week.wrong",optional=True)
    canvas.footer([])
    return None,None


def _arrow(canvas,x,y,direction):
    if direction=="flat":canvas.draw.rectangle((x,y+8,x+21,y+13),fill=COLOURS["muted"])
    else:
        points=[(x,y+21),(x+11,y),(x+22,y+21)] if direction=="up" else [(x,y),(x+11,y+21),(x+22,y)]
        canvas.draw.polygon(points,fill=COLOURS["green" if direction=="up" else "red"])


def compile_image(data,master,snapshot=None,*,image_number=1,page=0):
    validate_binding(data)
    if data.get("schema") != "image_input_v1" or data.get("template") not in TEMPLATES or master not in SIZE:
        raise LayoutError("IMAGE_INPUT_SCHEMA_INVALID")
    chart = data["template"] != "weekly" and image_number==1
    canvas=Canvas(master)
    if chart:
        if not snapshot:raise LayoutError("IMAGE_TRADINGVIEW_CAPTURE_REQUIRED")
        from .tradingview_snapshot_v1 import SYMBOLS
        if snapshot.get("tv_symbol") != SYMBOLS.get(data.get("market")):raise LayoutError("IMAGE_CHART_SYMBOL_MISMATCH")
        framing,levels=_chart(canvas,data,snapshot)
    else:framing,levels=_table(canvas,data,page)
    alt=data.get("alt_text") or (("TradingView "+str(snapshot.get("interval_label"))+" chart of "+MARKETS[data["market"]]+".") if chart
                                else {"event":"Event scenarios and their market implications.","weekly":"Weekly calls and their results in R.","map":"Six markets, their daily moves and today's drivers."}[data["template"]])
    if len(alt)>300:raise LayoutError("IMAGE_ALT_TEXT_TOO_LONG")
    metadata={"policy":POLICY,"template":data["template"],"master":master,"image_number":image_number,"page":page,
              "input":deepcopy(data),"snapshot":deepcopy(snapshot) if chart else None,"framing":framing,"levels":levels,
              "texts":canvas.texts,"notes":canvas.notes,"alt_text":alt,"chart":chart,
              "template_revision":template_revision()}
    return canvas.image,metadata


def template_revision():
    return digest({"source":sha256(Path(__file__).read_bytes()).hexdigest(),
                   "fonts":{p.name:sha256(p.read_bytes()).hexdigest() for p in FONTS.glob('*.ttf')}})


def render(data,master,out_dir,snapshot=None,*,image_number=1,page=0):
    image,meta=compile_image(data,master,snapshot,image_number=image_number,page=page)
    folder=Path(out_dir);folder.mkdir(parents=True,exist_ok=True)
    post=str(data["post_id"])
    if not re.fullmatch(r"[A-Za-z0-9_-]+",post):raise LayoutError("IMAGE_POST_FILENAME_INVALID")
    path=folder/f"{post}-{data['template']}-{image_number+page}-{master}.png"
    profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    image.save(path,format="PNG",icc_profile=profile)
    raw=path.read_bytes()
    return {"asset_id":"cc465-"+sha256(raw).hexdigest()[:24],"path":str(path.resolve()),"sha256":sha256(raw).hexdigest(),
            "width":image.width,"height":image.height,"mime_type":"image/png","alt_text":meta["alt_text"],
            "modality":"tradingview_chart_snapshot" if meta["chart"] else "source_bound_data_card",
            "credit":"Chart: TradingView" if meta["chart"] else "Capital Chronicle",
            "rights_basis":__import__('live_contentops.tradingview_snapshot_v1',fromlist=['RIGHTS_BASIS']).RIGHTS_BASIS if meta["chart"] else "Capital Chronicle's own source-bound analysis.",
            "image_template":meta,**({"tradingview_snapshot":deepcopy(snapshot)} if meta["chart"] else {}),
            "delivery_only":True,"article_inclusion":True,"canonical_article_media":True}
