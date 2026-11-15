"""Paths and constants for the NIFTY options data pipeline (Joel's module)."""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path

DATA = Path(os.environ.get("MACF244_DATA", Path.cwd() / "data"))
RAW_FO = DATA / "raw" / "fo"        # bhavcopy zips exactly as NSE serves them
CLEAN = DATA / "clean"              # outputs handed to the rest of the team
REPORT = DATA / "report"            # validation report and figures

BASE = "https://nsearchives.nseindia.com"

# Legacy files ceased after 5 July 2024; formats overlapped before that.
# This is our preferred URL routing boundary, not the first-ever UDiFF date.
# NSE circular MSD62424, 12 June 2024.
UDIFF_START = date(2024, 7, 8)

# The archive host rejects an empty User-Agent; no cookies are needed.
HTTP_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept": "*/*",
    "Referer": "https://www.nseindia.com/",
}

SYMBOL = "NIFTY"
DAYS_PER_YEAR = 365.0     # calendar-day time to expiry, as for India VIX
DEFAULT_RATE = 0.065      # fallback continuous risk-free rate if no curve is found
MIN_DTE = 7               # trade the first monthly expiry with >= 7 days left
MONEYNESS_BAND = 0.15     # keep strikes within +/-15% of the forward in the chain file
MIN_CONTRACTS = 1         # a leg with fewer contracts traded is flagged illiquid


def ensure_dirs() -> None:
    for p in (RAW_FO, CLEAN, REPORT):
        p.mkdir(parents=True, exist_ok=True)
