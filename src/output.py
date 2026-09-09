"""
Analysis / visualisation for the G10 carry backtest.

Run from src/ after backtest data is in ../data/:
    python analysis.py
Writes ../output/carry_charts.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import backtest as bt


def main():
    D = "data"
    rates, spot = bt.load_data(f"{D}/short_rates.csv", f"{D}/spot_usd.csv")
    ret = bt.run_backtest(rates, spot, n_leg=3, cost_bps=1)

    cum = (1 + ret).cumprod()
    dd = cum / cum.cummax() - 1

    regimes = [
        ("pre-2008", "1979-01-01", "2007-12-31", "#e8f0e8"),
        ("ZIRP 08-21", "2008-01-01", "2021-12-31", "#fdeaea"),
        ("post-2022", "2022-01-01", "2026-12-31", "#e8eef7"),
    ]

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(12, 8), sharex=True,
        gridspec_kw={"height_ratios": [2, 1]},
    )

    for _, lo, hi, col in regimes:
        ax1.axvspan(pd.Timestamp(lo), pd.Timestamp(hi), color=col, zorder=0)
        ax2.axvspan(pd.Timestamp(lo), pd.Timestamp(hi), color=col, zorder=0)

    ax1.plot(cum.index, cum.values, color="#1a3d1a", lw=1.4)
    ax1.set_ylabel("Growth of $1")
    ax1.set_title(
        "G10 FX Carry: cumulative return, dollar-neutral rank long-short",
        fontweight="bold",
    )
    ax1.grid(True, alpha=0.3)
    for name, lo, hi, _ in regimes:
        mid = pd.Timestamp(lo) + (pd.Timestamp(hi) - pd.Timestamp(lo)) / 2
        ax1.text(mid, cum.max() * 0.7, name, ha="center",
                 fontsize=9, color="#555", style="italic")

    ax2.fill_between(dd.index, dd.values, 0, color="#a02020", alpha=0.6)
    ax2.set_ylabel("Drawdown")
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
    ax2.grid(True, alpha=0.3)
    ax2.text(0.01, 0.08, f"Max drawdown: {dd.min():.0%}",
             transform=ax2.transAxes, fontsize=9,
             color="#a02020", fontweight="bold")

    plt.tight_layout()
    plt.savefig("output/carry_charts.png", dpi=130, bbox_inches="tight")
    print("Saved output/carry_charts.png")


if __name__ == "__main__":
    main()