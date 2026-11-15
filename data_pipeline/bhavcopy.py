"""Download NSE F&O bhavcopies and normalise both schemas onto one table.

Legacy (preferred before 8 July 2024): /content/historical/DERIVATIVES/2023/AUG/fo14AUG2023bhav.csv.zip
UDiFF  (preferred from 8 July 2024)    : /content/fo/BhavCopy_NSE_FO_0_0_0_20250814_F_0000.csv.zip

Every weekday is requested. A 404 is an unavailable archive, not proof of a holiday. Calendar validation
is separate. Missing responses are retried on subsequent runs.
"""
from __future__ import annotations

import io
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from . import config as C

COLUMNS = ["date", "instrument", "expiry", "strike", "opt_type", "open", "high", "low",
           "close", "settle", "contracts", "oi", "chg_oi", "lot_size", "underlying"]

_UDIFF_INSTR = {"IDF": "FUTIDX", "IDO": "OPTIDX", "STF": "FUTSTK", "STO": "OPTSTK"}


def url_for(d: date) -> str:
    if d >= C.UDIFF_START:
        return f"{C.BASE}/content/fo/BhavCopy_NSE_FO_0_0_0_{d:%Y%m%d}_F_0000.csv.zip"
    mon = d.strftime("%b").upper()
    return f"{C.BASE}/content/historical/DERIVATIVES/{d:%Y}/{mon}/fo{d:%d}{mon}{d:%Y}bhav.csv.zip"


def zip_path(d: date, raw_dir: Path | None = None) -> Path:
    return (raw_dir or C.RAW_FO) / f"{d:%Y}" / f"fo_{d:%Y%m%d}.zip"


def weekdays(start: date, end: date):
    d = start
    while d <= end:
        if d.weekday() < 5 or d in {date(2025, 2, 1)}:
            yield d
        d += timedelta(days=1)


def fetch(d: date, session=None, raw_dir: Path | None = None, retries: int = 3) -> Path | None:
    """Return a cached zip, or None for an unclassified unavailable archive."""
    path = zip_path(d, raw_dir)
    if path.exists():
        return path
    if session is None:
        import requests
        session = requests.Session()
    path.parent.mkdir(parents=True, exist_ok=True)
    last = None
    for attempt in range(retries):
        try:
            r = session.get(url_for(d), headers=C.HTTP_HEADERS, timeout=45)
        except Exception as exc:          # network error: back off and retry
            last = exc
            time.sleep(2 * (attempt + 1))
            continue
        if r.status_code == 404:
            return None
        if r.status_code == 200 and r.content[:2] == b"PK":
            tmp = path.with_suffix(".part")
            if not zipfile.is_zipfile(io.BytesIO(r.content)):
                raise ValueError("Invalid ZIP response")
            tmp.write_bytes(r.content)
            tmp.replace(path)             # never leave a half-written zip under the real name
            return path
        last = RuntimeError(f"HTTP {r.status_code}")
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"bhavcopy download failed for {d}: {last}")


def download_range(start: date, end: date, workers: int = 4, raw_dir: Path | None = None):
    """Download every weekday in [start, end]. Returns (ok_dates, unavailable_dates, failures)."""
    import requests
    session = requests.Session()
    days = list(weekdays(start, end))
    ok, unavailable, failures = [], [], []

    def one(d):
        try:
            return d, fetch(d, session, raw_dir), None
        except Exception as exc:
            return d, None, exc

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for i, (d, path, err) in enumerate(pool.map(one, days), 1):
            if err is not None:
                failures.append((d, str(err)))
            elif path is None:
                unavailable.append(d)
            else:
                ok.append(d)
            if i % 100 == 0 or i == len(days):
                print(f"  bhavcopy {i}/{len(days)}  files={len(ok)} unavailable={len(unavailable)} "
                      f"failed={len(failures)}", flush=True)
    return ok, unavailable, failures


def _read_csv(path_or_bytes) -> pd.DataFrame:
    src = io.BytesIO(path_or_bytes) if isinstance(path_or_bytes, bytes) else path_or_bytes
    with zipfile.ZipFile(src) as zf:
        name = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
        with zf.open(name) as fh:
            raw = pd.read_csv(fh, low_memory=False)
    raw.columns = [str(c).strip() for c in raw.columns]
    return raw


def _num(s):
    return pd.to_numeric(s, errors="coerce")


def _txt(s):
    # blanks arrive as NaN; fill before casting so pandas 2 and 3 behave the same
    return s.fillna("").astype(str).str.strip()


def _normalise_udiff(raw: pd.DataFrame, symbol: str) -> pd.DataFrame:
    raw = raw[_txt(raw["TckrSymb"]) == symbol]
    opt = _txt(raw["OptnTp"]).replace({"": "FUT"})
    return pd.DataFrame({
        "date": pd.to_datetime(raw["TradDt"]),
        "instrument": _txt(raw["FinInstrmTp"]).map(_UDIFF_INSTR),
        "expiry": pd.to_datetime(raw["XpryDt"]),
        "strike": _num(raw["StrkPric"]),
        "opt_type": opt,
        "open": _num(raw["OpnPric"]), "high": _num(raw["HghPric"]),
        "low": _num(raw["LwPric"]), "close": _num(raw["ClsPric"]),
        "settle": _num(raw["SttlmPric"]),
        "contracts": _num(raw["TtlTradgVol"]),
        "oi": _num(raw["OpnIntrst"]), "chg_oi": _num(raw["ChngInOpnIntrst"]),
        "lot_size": _num(raw["NewBrdLotQty"]),
        "underlying": _num(raw["UndrlygPric"]),
    })


def _normalise_legacy(raw: pd.DataFrame, symbol: str) -> pd.DataFrame:
    raw = raw.rename(columns=str.upper)
    raw = raw[_txt(raw["SYMBOL"]) == symbol]
    opt = _txt(raw["OPTION_TYP"]).replace({"XX": "FUT"})
    return pd.DataFrame({
        "date": pd.to_datetime(_txt(raw["TIMESTAMP"]).str.title(), format="%d-%b-%Y"),
        "instrument": _txt(raw["INSTRUMENT"]),
        "expiry": pd.to_datetime(_txt(raw["EXPIRY_DT"]).str.title(), format="%d-%b-%Y"),
        "strike": _num(raw["STRIKE_PR"]),
        "opt_type": opt,
        "open": _num(raw["OPEN"]), "high": _num(raw["HIGH"]),
        "low": _num(raw["LOW"]), "close": _num(raw["CLOSE"]),
        "settle": _num(raw["SETTLE_PR"]),
        "contracts": _num(raw["CONTRACTS"]),
        "oi": _num(raw["OPEN_INT"]), "chg_oi": _num(raw["CHG_IN_OI"]),
        "lot_size": float("nan"),        # legacy files carry neither lot size
        "underlying": float("nan"),      # nor the underlying print
    })


def normalise(path_or_bytes, symbol: str = C.SYMBOL) -> pd.DataFrame:
    """One bhavcopy zip -> NIFTY index futures and options on the common schema."""
    raw = _read_csv(path_or_bytes)
    df = _normalise_udiff(raw, symbol) if "FinInstrmTp" in raw.columns \
        else _normalise_legacy(raw, symbol)
    df = df[df["instrument"].isin(["FUTIDX", "OPTIDX"])].copy()
    df.loc[df["instrument"] == "FUTIDX", "strike"] = float("nan")
    for col in ["date", "expiry"]:
        df[col] = df[col].dt.normalize()
    if df.duplicated(["date", "instrument", "expiry", "strike", "opt_type"]).any():
        raise ValueError("Duplicate contract keys")
    return df[COLUMNS].reset_index(drop=True)


def load_range(start: date, end: date, raw_dir: Path | None = None) -> pd.DataFrame:
    """Normalise every cached zip in [start, end] into one table."""
    frames = []
    for d in weekdays(start, end):
        p = zip_path(d, raw_dir)
        if p.exists():
            frame = normalise(p)
            if not frame.date.eq(pd.Timestamp(d)).all():
                raise ValueError(f"Archive date mismatch: {p}")
            frames.append(frame)
    if not frames:
        raise FileNotFoundError("no cached bhavcopy files in range; run the download step")
    return pd.concat(frames, ignore_index=True)
