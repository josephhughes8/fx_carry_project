"""
Pull G10 short rates and USD spot from FRED.

Run locally (this needs internet access to api.stlouisfed.org):
    pip install fredapi pandas
    export FRED_API_KEY=your_key_here   # free from https://fred.stlouisfed.org/docs/api/api_key.html
    python fetch_data.py

Outputs two CSVs into ../data/: short_rates.csv and spot_usd.csv
"""

import os
import pandas as pd
from fredapi import Fred

fred = Fred(api_key=os.environ["FRED_API_KEY"])

# --- Short rates (3M interbank where available, else policy rate) ---
# NOTE: coverage varies. Verify each series' start date and units on FRED;
# some are discontinued post-EONING/LIBOR transition and may need swapping
# for the newer risk-free-rate equivalents (e.g. SOFR, ESTR, SONIA, TONA).
RATE_SERIES = {
    "USD": "IR3TIB01USM156N",   # 3M interbank, US
    "EUR": "IR3TIB01EZM156N",   # 3M interbank, euro area
    "JPY": "IR3TIB01JPM156N",   # 3M interbank, Japan
    "GBP": "IR3TIB01GBM156N",   # 3M interbank, UK
    "CHF": "IR3TIB01CHM156N",   # 3M interbank, Switzerland
    "AUD": "IR3TIB01AUM156N",   # 3M interbank, Australia
    "NZD": "IR3TIB01NZM156N",   # 3M interbank, New Zealand
    "CAD": "IR3TIB01CAM156N",   # 3M interbank, Canada
    "SEK": "IR3TIB01SEM156N",   # 3M interbank, Sweden
    "NOR": "IR3TIB01NOM156N",   # 3M interbank, Norway
}

# --- USD spot exchange rates ---
# FRED quotes some as USD-per-FX and some as FX-per-USD. Flag the convention
# so we can normalise everything to "USD value of 1 unit of FX" downstream.
SPOT_SERIES = {
    # series_id, convention: "USD_per_FX" or "FX_per_USD"
    "EUR": ("DEXUSEU", "USD_per_FX"),
    "GBP": ("DEXUSUK", "USD_per_FX"),
    "AUD": ("DEXUSAL", "USD_per_FX"),
    "NZD": ("DEXUSNZ", "USD_per_FX"),
    "JPY": ("DEXJPUS", "FX_per_USD"),
    "CHF": ("DEXSZUS", "FX_per_USD"),
    "CAD": ("DEXCAUS", "FX_per_USD"),
    "SEK": ("DEXSDUS", "FX_per_USD"),
    "NOR": ("DEXNOUS", "FX_per_USD"),
    # USD spot vs itself is trivially 1.0, handled downstream
}


def fetch_rates():
    out = {}
    for ccy, sid in RATE_SERIES.items():
        try:
            out[ccy] = fred.get_series(sid)
        except Exception as e:
            print(f"WARN {ccy} ({sid}) failed: {e}")
    df = pd.DataFrame(out)
    df.index.name = "date"
    return df


def fetch_spot():
    out = {}
    for ccy, (sid, conv) in SPOT_SERIES.items():
        s = fred.get_series(sid)
        if conv == "FX_per_USD":
            s = 1.0 / s          # normalise to USD per 1 unit of FX
        out[ccy] = s
    out["USD"] = None            # placeholder; USD/USD = 1.0 set downstream
    df = pd.DataFrame(out)
    df["USD"] = 1.0
    df.index.name = "date"
    return df


if __name__ == "__main__":
    r = fetch_rates()
    s = fetch_spot()
    r.to_csv("../data/short_rates.csv")
    s.to_csv("../data/spot_usd.csv")
    print("Saved short_rates.csv", r.shape, "and spot_usd.csv", s.shape)
