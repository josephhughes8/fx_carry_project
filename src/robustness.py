"""
Robustness checks for the G10 carry backtest.

Re-runs the same strategy while varying one knob at a time, so you can see
whether the headline result depends on specific choices (a sign of curve-fitting)
or holds across sensible variations (a sign it's real).

Two sweeps:
  1. Currencies per leg (2/3/4...): tests portfolio-construction sensitivity.
  2. Transaction costs (0/1/5/10/20 bp): tests how much the edge depends on
     cheap execution. Carry rebalances monthly, so cost matters a lot.

Prints the tables AND saves a plot to ../output/robustness_charts.png.

Run from src/ after data is in ../data/:
    python robustness.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import backtest as bt


def leg_sweep(rates, spot, legs=(1, 2, 3, 4), cost_bps=1.0):
    print("=== Sensitivity to currencies per leg "
          f"(costs held at {cost_bps}bp) ===")
    print(f'{"n_leg":>6} {"ann_ret":>9} {"sharpe":>8} {"maxDD":>8} {"skew":>7}')
    rows = []
    for n in legs:
        ret = bt.run_backtest(rates, spot, n_leg=n, cost_bps=cost_bps)
        st = bt.stats(ret)
        print(f'{n:>6} {st["ann_return"]:>9.4f} {st["sharpe"]:>8.2f} '
              f'{st["max_drawdown"]:>8.3f} {st["skew"]:>7.2f}')
        rows.append((n, st))
    return rows


def cost_sweep(rates, spot, costs=(0, 1, 5, 10, 20), n_leg=3):
    print(f"=== Sensitivity to transaction costs (n_leg held at {n_leg}) ===")
    print(f'{"cost_bps":>9} {"ann_ret":>9} {"sharpe":>8} {"maxDD":>8}')
    rows = []
    for c in costs:
        ret = bt.run_backtest(rates, spot, n_leg=n_leg, cost_bps=c)
        st = bt.stats(ret)
        print(f'{c:>9} {st["ann_return"]:>9.4f} {st["sharpe"]:>8.2f} '
              f'{st["max_drawdown"]:>8.3f}')
        rows.append((c, st))
    return rows


def plot_sweeps(leg_rows, cost_rows, path="output/robustness_charts.png"):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    # --- Leg sweep: Sharpe bars (robustness = flat bars) ---
    legs = [n for n, _ in leg_rows]
    leg_sharpe = [st["sharpe"] for _, st in leg_rows]
    ax1.bar([str(n) for n in legs], leg_sharpe, color="#3a6ea5", width=0.6)
    ax1.axhline(0.5, ls="--", color="#888", lw=1)
    ax1.set_xlabel("Currencies per leg")
    ax1.set_ylabel("Sharpe ratio")
    ax1.set_title("Robust to construction:\nSharpe ~flat across leg size",
                  fontsize=11, fontweight="bold")
    ax1.set_ylim(0, max(leg_sharpe) * 1.25)
    for x, v in zip([str(n) for n in legs], leg_sharpe):
        ax1.text(x, v + 0.01, f"{v:.2f}", ha="center", fontsize=9)
    ax1.grid(True, axis="y", alpha=0.3)

    # --- Cost sweep: Sharpe declining line (the vulnerability) ---
    costs = [c for c, _ in cost_rows]
    cost_sharpe = [st["sharpe"] for _, st in cost_rows]
    ax2.plot(costs, cost_sharpe, "o-", color="#a02020", lw=2, markersize=7)
    ax2.axhline(0, ls="--", color="#888", lw=1)
    ax2.set_xlabel("Transaction cost (bp per rebalance)")
    ax2.set_ylabel("Sharpe ratio")
    ax2.set_title("Cost-sensitive:\nedge erodes, gone by ~20bp",
                  fontsize=11, fontweight="bold")
    for x, v in zip(costs, cost_sharpe):
        ax2.text(x, v + 0.03, f"{v:.2f}", ha="center", fontsize=9)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(path, dpi=130, bbox_inches="tight")
    print(f"\nSaved {path}")


def main():
    D = "data"
    rates, spot = bt.load_data(f"{D}/short_rates.csv", f"{D}/spot_usd.csv")
    leg_rows = leg_sweep(rates, spot)
    print()
    cost_rows = cost_sweep(rates, spot)
    plot_sweeps(leg_rows, cost_rows)
    print()
    print("How to read this:")
    print("- Leg sweep (left): flat bars = robust to portfolio construction.")
    print("- Cost sweep (right): falling line = edge depends on cheap execution.")
    print("  Viable only if you trade G10 FX below ~5-10bp round trip.")


if __name__ == "__main__":
    main()