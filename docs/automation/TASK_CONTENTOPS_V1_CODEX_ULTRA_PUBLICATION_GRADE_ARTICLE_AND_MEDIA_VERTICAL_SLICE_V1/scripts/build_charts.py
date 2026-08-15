from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "source_data"
OUT = ROOT / "charts"

NAVY = "#102234"
INK = "#18252d"
CREAM = "#f7f2e8"
PAPER = "#fffdf8"
RUST = "#b95d3b"
TEAL = "#2e7775"
GOLD = "#d8b56a"
SLATE = "#8b9aa3"
GRID = "#d8d2c7"


def set_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 13,
            "axes.titleweight": "bold",
            "axes.titlesize": 23,
            "axes.labelcolor": INK,
            "axes.edgecolor": GRID,
            "xtick.color": INK,
            "ytick.color": INK,
            "text.color": INK,
            "figure.facecolor": CREAM,
            "axes.facecolor": CREAM,
            "savefig.facecolor": CREAM,
        }
    )


def save(fig: plt.Figure, stem: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    svg_path = OUT / f"{stem}.svg"
    fig.savefig(svg_path, bbox_inches="tight", pad_inches=0.25)
    fig.savefig(OUT / f"{stem}.png", dpi=200, bbox_inches="tight", pad_inches=0.25)
    svg_text = svg_path.read_text(encoding="utf-8")
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
        encoding="utf-8",
    )
    plt.close(fig)


def read_rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def retail_path() -> None:
    rows = read_rows("retail_sales_2026.csv")
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"]
    total = np.array([float(row["total_usd_millions"]) for row in rows])
    core = np.array([float(row["ex_auto_gas_usd_millions"]) for row in rows])
    total_index = total / total[0] * 100
    core_index = core / core[0] * 100
    x = np.arange(len(months))

    fig, ax = plt.subplots(figsize=(12, 6.75))
    ax.axvspan(2.65, 4.35, color=GOLD, alpha=0.18, lw=0)
    ax.text(3.5, 104.9, "PEAK REFUND WINDOW", ha="center", va="center", color="#765d28", fontsize=10, fontweight="bold")
    ax.plot(x, total_index, color=NAVY, lw=4, marker="o", ms=8, label="Total retail + food services")
    ax.plot(x, core_index, color=TEAL, lw=3, marker="o", ms=7, label="Ex autos + gasoline")
    ax.scatter([6], [total_index[-1]], s=160, color=RUST, zorder=5, edgecolor=CREAM, linewidth=2)
    ax.annotate(
        "July: -0.6% m/m\n$763.6bn",
        xy=(6, total_index[-1]),
        xytext=(5.05, 101.0),
        arrowprops={"arrowstyle": "-", "color": RUST, "lw": 1.8},
        color=RUST,
        fontsize=12,
        fontweight="bold",
    )
    ax.annotate(
        "Ex autos + gas: -0.2%",
        xy=(6, core_index[-1]),
        xytext=(4.45, 103.55),
        arrowprops={"arrowstyle": "-", "color": TEAL, "lw": 1.5},
        color=TEAL,
        fontsize=11,
        fontweight="bold",
    )
    ax.set_title("The refund-powered run stalled in July", loc="left", color=NAVY, pad=20)
    ax.text(0, 1.02, "Seasonally adjusted sales, January 2026 = 100", transform=ax.transAxes, fontsize=12, color="#53636c")
    ax.set_xticks(x, months)
    ax.set_ylim(99.5, 105.4)
    ax.set_yticks([100, 101, 102, 103, 104, 105])
    ax.grid(axis="y", color=GRID, linewidth=0.9)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(0, 0.94), ncol=2, fontsize=11)
    fig.text(
        0.01,
        0.01,
        "Source: U.S. Census Bureau, Advance Monthly Retail Trade Survey. Current vintage retrieved Aug. 15, 2026. Not adjusted for price changes.",
        fontsize=9.5,
        color="#66747c",
    )
    fig.tight_layout(rect=(0, 0.055, 1, 1))
    save(fig, "retail_path_2026")


def category_mix() -> None:
    rows = read_rows("july_2026_category_changes.csv")
    categories = [row["category"] for row in rows]
    values = np.array([float(row["month_over_month_percent"]) for row in rows])
    colors = [RUST if value < 0 else TEAL if value > 0 else SLATE for value in values]
    y = np.arange(len(categories))

    fig, ax = plt.subplots(figsize=(12, 7.2))
    ax.barh(y, values, color=colors, height=0.62)
    ax.axvline(0, color=NAVY, lw=1.2)
    ax.set_yticks(y, categories)
    ax.invert_yaxis()
    ax.set_xlim(-2.55, 2.25)
    ax.set_xticks([-2, -1, 0, 1, 2], ["-2%", "-1%", "0", "+1%", "+2%"])
    for index, value in enumerate(values):
        offset = 0.08 if value >= 0 else -0.08
        align = "left" if value >= 0 else "right"
        label = "0.0%" if value == 0 else f"{value:+.1f}%"
        ax.text(value + offset, index, label, va="center", ha=align, color=INK, fontweight="bold", fontsize=11)
    ax.set_title("A sharp headline, but not a household shutdown", loc="left", color=NAVY, pad=20)
    ax.text(0, 1.015, "July 2026 change from June, selected categories", transform=ax.transAxes, fontsize=12, color="#53636c")
    ax.grid(axis="x", color=GRID, linewidth=0.9)
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    ax.tick_params(axis="both", length=0)
    fig.text(
        0.01,
        0.01,
        "Source: U.S. Census Bureau, Advance Monthly Retail Trade Survey, Aug. 14, 2026. Seasonally adjusted; not adjusted for price changes.",
        fontsize=9.5,
        color="#66747c",
    )
    fig.tight_layout(rect=(0, 0.055, 1, 1))
    save(fig, "july_category_mix")


def refund_impulse() -> None:
    rows = read_rows("irs_refunds_may_2026.csv")
    years = [row["as_of_year"] for row in rows]
    amounts = [float(row["total_refund_amount_usd_billions"]) for row in rows]
    averages = [int(row["average_refund_usd"]) for row in rows]

    fig, ax = plt.subplots(figsize=(10, 6.75))
    bars = ax.bar(years, amounts, color=[SLATE, GOLD], width=0.56)
    ax.set_ylim(0, 370)
    ax.set_yticks([0, 100, 200, 300], ["$0bn", "$100bn", "$200bn", "$300bn"])
    for bar, amount in zip(bars, amounts):
        ax.text(bar.get_x() + bar.get_width() / 2, amount + 10, f"${amount:.1f}bn", ha="center", fontweight="bold", fontsize=17, color=NAVY)
    ax.text(0.5, 0.57, "+18.1%", transform=ax.transAxes, ha="center", va="center", fontsize=34, color=RUST, fontweight="bold")
    ax.text(0.5, 0.49, "year over year", transform=ax.transAxes, ha="center", va="center", fontsize=11, color="#5d6c74")
    ax.text(
        0.5,
        0.25,
        f"Average refund: \\${averages[0]:,}  →  \\${averages[1]:,}",
        transform=ax.transAxes,
        ha="center",
        fontsize=13,
        color=INK,
        fontweight="bold",
        bbox={"boxstyle": "round,pad=0.45", "facecolor": PAPER, "edgecolor": GRID},
    )
    ax.set_title("The spring cash cushion was unusually large", loc="left", color=NAVY, pad=20)
    ax.text(0, 1.015, "Cumulative individual income-tax refunds through comparable early-May dates", transform=ax.transAxes, fontsize=11.5, color="#53636c")
    ax.grid(axis="y", color=GRID, linewidth=0.9)
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    ax.tick_params(axis="both", length=0)
    fig.text(
        0.01,
        0.01,
        "Source: Internal Revenue Service, 2026 filing-season statistics through May 8; comparison date May 9, 2025.",
        fontsize=9.5,
        color="#66747c",
    )
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    save(fig, "irs_refund_impulse")


def source_excerpt() -> None:
    fig = plt.figure(figsize=(12, 6.3), facecolor=PAPER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    ax.add_patch(plt.Rectangle((0.055, 0.07), 0.89, 0.86, facecolor=CREAM, edgecolor=GRID, linewidth=1.3))
    ax.add_patch(plt.Rectangle((0.055, 0.07), 0.018, 0.86, facecolor=RUST, edgecolor="none"))
    ax.text(0.105, 0.83, "PRIMARY SOURCE / CB26-131", fontsize=11, color=RUST, fontweight="bold", transform=ax.transAxes)
    ax.text(0.105, 0.75, "ADVANCE MONTHLY SALES FOR RETAIL AND FOOD SERVICES", fontsize=19, color=NAVY, fontweight="bold", transform=ax.transAxes)
    ax.text(0.105, 0.68, "July 2026 · released August 14, 2026", fontsize=12, color="#5d6c74", transform=ax.transAxes)
    excerpt = (
        "Advance estimates of U.S. retail and food services sales for July 2026, adjusted for seasonal variation and\n"
        "holiday and trading-day differences, but not for price changes, were $763.6 billion, down 0.6 percent\n"
        "(±0.4 percent) from the previous month, but up 5.0 percent (±0.5 percent) from July 2025."
    )
    ax.text(0.105, 0.54, excerpt, fontsize=15, color=INK, linespacing=1.55, va="top", transform=ax.transAxes)
    ax.text(0.105, 0.23, "$763.6bn", fontsize=30, color=NAVY, fontweight="bold", transform=ax.transAxes)
    ax.text(0.35, 0.23, "−0.6% m/m", fontsize=30, color=RUST, fontweight="bold", transform=ax.transAxes)
    ax.text(0.64, 0.23, "+5.0% y/y", fontsize=30, color=TEAL, fontweight="bold", transform=ax.transAxes)
    ax.text(0.105, 0.12, "Typeset excerpt; wording and uncertainty intervals reproduced from the official Census release.", fontsize=10.5, color="#66747c", transform=ax.transAxes)
    save(fig, "census_release_excerpt")


def main() -> None:
    set_style()
    retail_path()
    category_mix()
    refund_impulse()
    source_excerpt()


if __name__ == "__main__":
    main()
