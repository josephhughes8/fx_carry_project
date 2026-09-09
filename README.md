# G10 FX Carry Backtest

Cross-sectional carry strategy on G10 currencies: each month rank currencies by
short rate, go long the top yielders, short the bottom, dollar-neutral. Total
return decomposes as **carry (rate differential) + spot move**, which is the
whole point of the strategy: carry is the steady reward, spot is the risk.

## Setup

```bash
pip install -r requirements.txt
```

## 1. Get the data (run locally, needs internet)

Get a free FRED API key: https://fred.stlouisfed.org/docs/api/api_key.html

```bash
export FRED_API_KEY=your_key_here
cd src
python fetch_data.py
```

This writes `data/short_rates.csv` and `data/spot_usd.csv`.

### Data caveats to check
- **Discontinued series:** several 3M interbank series ended with the
  LIBOR/EONIA transition (~2021-22). The tail may need swapping for the newer
  risk-free rates (SOFR, ESTR, SONIA, TONA). Flagged in `fetch_data.py`.
- **Spot convention:** FRED mixes USD-per-FX and FX-per-USD quotes. The script
  normalises everything to "USD value of 1 unit of FX", but eyeball a couple of
  series to confirm.

## 2. Run the backtest

```bash
cd src
python backtest.py
```

Prints overall stats (annualised return, vol, Sharpe, max drawdown, skew) plus a
regime split (pre-2008 / ZIRP 2008-21 / post-2022) to show the strategy's
dependence on policy divergence.

## Structure

```
fx_carry/
  src/
    fetch_data.py   # FRED pull, G10 series IDs (run locally)
    backtest.py     # rank-based long-short engine (source-agnostic)
  data/             # CSVs land here
  output/           # results.csv lands here
  notebooks/        # add analysis/plots here
```

## Extensions
- Vol-scale positions instead of equal-weight
- Momentum overlay to cut exposure in stressed regimes
- Transaction cost sensitivity (cost_bps arg in run_backtest)
- Bolt on EM currencies for the wide end of the carry spread
