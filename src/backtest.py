"""
Cross-sectional G10 carry backtest.

Each rebalance (monthly):
  1. Rank currencies by short rate.
  2. Long the top `n_leg`, short the bottom `n_leg`, equal-weight, dollar-neutral.
  3. Realised return over the next period per currency =
        carry (rate differential earned over the period)
      + spot return of that FX vs USD.
     Since the book is dollar-neutral (equal long/short USD notional),
     the USD leg nets out and we're left with the cross-sectional
     high-yielder-minus-low-yielder return, carry + relative spot.

Usage:
    python backtest.py
Reads ../data/short_rates.csv and ../data/spot_usd.csv (monthly, %-p.a. rates,
spot as USD per 1 unit of FX). Writes ../output/results.csv and prints stats.
"""

import numpy as np
import pandas as pd


def load_data(rates_path, spot_path):
    rates = pd.read_csv(rates_path, index_col="date", parse_dates=True)
    spot = pd.read_csv(spot_path, index_col="date", parse_dates=True)
    # align to month-end, forward-fill within month, keep common columns/dates
    rates = rates.resample("ME").last()
    spot = spot.resample("ME").last()
    cols = sorted(set(rates.columns) & set(spot.columns))
    idx = rates.index.intersection(spot.index)
    return rates.loc[idx, cols], spot.loc[idx, cols]


def run_backtest(rates, spot, n_leg=1, cost_bps=0.0):
    # monthly spot return per currency (USD per FX, so + = FX appreciated vs USD)
    spot_ret = spot.pct_change().shift(-1)          # return realised NEXT period
    # carry earned over the coming month = annualised rate / 12, in decimal
    carry = (rates / 100.0) / 12.0

    dates = rates.index[:-1]                          # last row has no fwd return
    port_ret = []
    for dt in dates:
        r = rates.loc[dt].dropna()
        if len(r) < 2 * n_leg:
            port_ret.append(np.nan)
            continue
        ranked = r.sort_values(ascending=False)
        longs = ranked.index[:n_leg]
        shorts = ranked.index[-n_leg:]

        # total return per currency this month = carry + spot move
        tot = carry.loc[dt] + spot_ret.loc[dt]
        long_ret = tot[longs].mean()
        short_ret = tot[shorts].mean()
        gross = long_ret - short_ret

        # rebalance cost: assume full turnover of both legs each month
        cost = 2 * n_leg * (cost_bps / 1e4) * 2 / (2 * n_leg)  # per-unit avg
        port_ret.append(gross - cost)

    out = pd.Series(port_ret, index=dates, name="carry_ret").dropna()
    return out


def stats(ret):
    ann = 12
    mu = ret.mean() * ann
    vol = ret.std() * np.sqrt(ann)
    sharpe = mu / vol if vol else np.nan
    cum = (1 + ret).cumprod()
    dd = (cum / cum.cummax() - 1).min()
    return {
        "ann_return": round(mu, 4),
        "ann_vol": round(vol, 4),
        "sharpe": round(sharpe, 2),
        "max_drawdown": round(dd, 4),
        "skew": round(ret.skew(), 2),
        "n_months": len(ret),
    }


if __name__ == "__main__":
    rates, spot = load_data("data/short_rates.csv", "data/spot_usd.csv")
    ret = run_backtest(rates, spot, n_leg=3, cost_bps=1.0)
    ret.to_csv("output/results.csv")
    print(stats(ret))

    # regime split to show policy-divergence dependence
    for label, lo, hi in [
        ("pre-2008", "1990-01-01", "2007-12-31"),
        ("ZIRP 08-21", "2008-01-01", "2021-12-31"),
        ("post-2022", "2022-01-01", "2100-01-01"),
    ]:
        seg = ret.loc[lo:hi]
        if len(seg) > 6:
            print(label, stats(seg))
