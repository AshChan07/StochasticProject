"""Synthetic bhavcopy files in NSE's exact legacy and UDiFF layouts.

Prices come from Black-76 at a known volatility and forward, rounded to the
0.05 tick, so tests can check the pipeline recovers the inputs.
"""
from __future__ import annotations
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import io
import zipfile
from datetime import date, timedelta

import numpy as np
import pandas as pd

from data_pipeline.iv import black76

R, Q = 0.065, 0.012          # rate and dividend yield used to build forwards
LEGACY_COLS = ["INSTRUMENT", "SYMBOL", "EXPIRY_DT", "STRIKE_PR", "OPTION_TYP", "OPEN", "HIGH",
               "LOW", "CLOSE", "SETTLE_PR", "CONTRACTS", "VAL_INLAKH", "OPEN_INT", "CHG_IN_OI",
               "TIMESTAMP"]
UDIFF_COLS = ["TradDt", "BizDt", "Sgmt", "Src", "FinInstrmTp", "FinInstrmId", "ISIN", "TckrSymb",
              "SctySrs", "XpryDt", "FininstrmActlXpryDt", "StrkPric", "OptnTp", "FinInstrmNm",
              "OpnPric", "HghPric", "LwPric", "ClsPric", "LastPric", "PrvsClsgPric", "UndrlygPric",
              "SttlmPric", "OpnIntrst", "ChngInOpnIntrst", "TtlTradgVol", "TtlTrfVal",
              "TtlNbOfTxsExctd", "SsnId", "NewBrdLotQty", "Rmks", "Rsvd1", "Rsvd2", "Rsvd3", "Rsvd4"]


def last_weekday(year, month, weekday):
    d = date(year + month // 12, month % 12 + 1, 1) - timedelta(days=1)
    while d.weekday() != weekday:
        d -= timedelta(days=1)
    return d


def expiries_for(d: date) -> list[date]:
    """Three monthly (last Thursday) expiries plus the next two weekly Thursdays."""
    months = []
    y, m = d.year, d.month
    while len(months) < 3:
        e = last_weekday(y, m, 3)
        if e >= d:
            months.append(e)
        m += 1
        if m > 12:
            y, m = y + 1, 1
    weeks, w = [], d
    while len(weeks) < 2:
        if w.weekday() == 3:
            weeks.append(w)
        w += timedelta(days=1)
    return sorted(set(months + weeks))


def sigma_on(d: date) -> float:
    """Known 'true' volatility that drifts over the sample."""
    return 0.12 + 0.002 * (d.toordinal() % 20)


def spot_on(d: date) -> float:
    return 21000.0 + 15.0 * (d.toordinal() % 37)


def market_rows(d: date) -> list[dict]:
    S, sig = spot_on(d), sigma_on(d)
    rows = []
    for e in expiries_for(d):
        T = max((e - d).days, 0.5) / 365.0
        F = S * np.exp((R - Q) * T)
        monthly = e == last_weekday(e.year, e.month, 3)
        if monthly:
            rows.append(dict(kind="FUT", expiry=e, strike=np.nan, opt=None,
                             close=round(F * 20) / 20, contracts=50000, oi=1e7, und=S))
        for K in np.arange(round(S / 50) * 50 - 2500, round(S / 50) * 50 + 2550, 50.0):
            for opt in ("CE", "PE"):
                p = float(black76(F, K, T, R, sig, opt == "CE"))
                p = max(round(p * 20) / 20, 0.05)
                far = abs(K / S - 1) > 0.08
                rows.append(dict(kind="OPT", expiry=e, strike=K, opt=opt, close=p,
                                 contracts=0 if far else 1000, oi=5e5, und=S))
    return rows


def legacy_zip(d: date) -> bytes:
    out = []
    for r in market_rows(d):
        fut = r["kind"] == "FUT"
        out.append({"INSTRUMENT": "FUTIDX" if fut else "OPTIDX", "SYMBOL": "NIFTY",
                    "EXPIRY_DT": r["expiry"].strftime("%d-%b-%Y"),
                    "STRIKE_PR": 0 if fut else r["strike"], "OPTION_TYP": "XX" if fut else r["opt"],
                    "OPEN": r["close"], "HIGH": r["close"], "LOW": r["close"], "CLOSE": r["close"],
                    "SETTLE_PR": r["close"], "CONTRACTS": r["contracts"], "VAL_INLAKH": 1.0,
                    "OPEN_INT": r["oi"], "CHG_IN_OI": 0, "TIMESTAMP": d.strftime("%d-%b-%Y").upper()})
    # noise the pipeline must drop: another index and a stock option
    out.append({**out[-1], "SYMBOL": "BANKNIFTY"})
    out.append({**out[-1], "INSTRUMENT": "OPTSTK", "SYMBOL": "RELIANCE"})
    df = pd.DataFrame(out, columns=LEGACY_COLS)
    df[""] = ""                                # real legacy files end with an empty column
    return _zip(df, f"fo{d:%d}{d.strftime('%b').upper()}{d:%Y}bhav.csv")


def udiff_zip(d: date) -> bytes:
    out = []
    for r in market_rows(d):
        fut = r["kind"] == "FUT"
        row = {c: "" for c in UDIFF_COLS}
        row.update({"TradDt": d.isoformat(), "BizDt": d.isoformat(), "Sgmt": "FO", "Src": "NSE",
                    "FinInstrmTp": "IDF" if fut else "IDO", "TckrSymb": "NIFTY",
                    "XpryDt": r["expiry"].isoformat(), "StrkPric": "" if fut else r["strike"],
                    "OptnTp": "" if fut else r["opt"], "OpnPric": r["close"], "HghPric": r["close"],
                    "LwPric": r["close"], "ClsPric": r["close"], "LastPric": r["close"],
                    "UndrlygPric": r["und"], "SttlmPric": r["close"], "OpnIntrst": r["oi"],
                    "ChngInOpnIntrst": 0, "TtlTradgVol": r["contracts"], "NewBrdLotQty": 50})
        out.append(row)
    out.append({**out[-1], "TckrSymb": "BANKNIFTY"})
    out.append({**out[-1], "FinInstrmTp": "STO", "TckrSymb": "RELIANCE"})
    return _zip(pd.DataFrame(out, columns=UDIFF_COLS),
                f"BhavCopy_NSE_FO_0_0_0_{d:%Y%m%d}_F_0000.csv")


def _zip(df: pd.DataFrame, name: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(name, df.to_csv(index=False))
    return buf.getvalue()


HOLIDAYS = {date(2023, 12, 25)}


def trading_days(start=date(2023, 12, 11), end=date(2024, 1, 31)):
    d = start
    while d <= end:
        if d.weekday() < 5 and d not in HOLIDAYS:
            yield d
        d += timedelta(days=1)


def write_raw_dir(raw_dir):
    """Populate a raw cache exactly as the downloader would."""
    from data_pipeline import bhavcopy
    from data_pipeline.config import UDIFF_START
    for d in trading_days():
        p = bhavcopy.zip_path(d, raw_dir)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(udiff_zip(d) if d >= UDIFF_START else legacy_zip(d))
    for d in HOLIDAYS:
        p = bhavcopy.zip_path(d, raw_dir)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.with_suffix(".missing").touch()
