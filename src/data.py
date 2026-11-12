"""Normalize downloaded NSE UDiFF ZIPs; keep all strikes to track held contracts."""

import zipfile, json
from pathlib import Path
import pandas as pd, numpy as np
from .pricing import iv


def build(root, r=0.065):
    out = root / "data/clean"
    out.mkdir(parents=True, exist_ok=True)
    parts = []
    audit = []
    use = [
        "TradDt",
        "FinInstrmTp",
        "TckrSymb",
        "XpryDt",
        "StrkPric",
        "OptnTp",
        "OpnPric",
        "ClsPric",
        "SttlmPric",
        "UndrlygPric",
        "TtlTradgVol",
        "OpnIntrst",
        "NewBrdLotQty",
    ]
    for zpath in sorted((root / "data/raw").glob("*.zip")):
        with zipfile.ZipFile(zpath) as z:
            d = pd.read_csv(
                z.open(z.namelist()[0]), usecols=lambda x: x in use, low_memory=False
            )
        d = d[d.TckrSymb.eq("NIFTY") & d.FinInstrmTp.isin(["IDO", "IDF"])].copy()
        expected = pd.to_datetime(zpath.name.split("_")[6], format="%Y%m%d")
        dates = pd.to_datetime(d.TradDt).dt.normalize()
        if not dates.eq(expected).all():
            raise ValueError("Date mismatch " + str(zpath))
        audit.append(dict(date=expected, rows=len(d)))
        parts.append(d)
    if not parts:
        raise RuntimeError(
            "No NSE ZIPs. Run download_data.py or follow DATA_DOWNLOAD_GUIDE.md."
        )
    d = pd.concat(parts, ignore_index=True).rename(
        columns={
            "TradDt": "date",
            "XpryDt": "expiry",
            "StrkPric": "strike",
            "OptnTp": "opt_type",
            "OpnPric": "open",
            "ClsPric": "close",
            "SttlmPric": "settle",
            "UndrlygPric": "underlying",
            "TtlTradgVol": "volume",
            "OpnIntrst": "oi",
            "NewBrdLotQty": "lot_size",
        }
    )
    for col in ["date", "expiry"]:
        d[col] = pd.to_datetime(d[col]).dt.normalize()
    for col in [
        "strike",
        "open",
        "close",
        "settle",
        "underlying",
        "volume",
        "oi",
        "lot_size",
    ]:
        d[col] = pd.to_numeric(d[col], errors="coerce")
    f = d[d.FinInstrmTp.eq("IDF")].copy()
    o = d[d.FinInstrmTp.eq("IDO") & d.opt_type.isin(["CE", "PE"])].copy()
    keys = ["date", "expiry"]
    if f.duplicated(keys).any() or o.duplicated(keys + ["strike", "opt_type"]).any():
        raise ValueError("Duplicate contracts")
    # Actual matching futures expiries identify monthly options; no weekday inference.
    o = o.merge(
        f[keys + ["close"]].rename(columns={"close": "futures_close"}),
        on=keys,
        how="inner",
    )
    o["T"] = (o.expiry - o.date).dt.days / 365
    o = o[o["T"] > 0].copy()
    o["iv"] = iv(o.close, o.futures_close, o.strike, o["T"], r, o.opt_type.eq("PE"))
    spot = (
        d[d.underlying > 0]
        .groupby("date")
        .underlying.median()
        .rename("close")
        .reset_index()
    )
    spread = d[d.underlying > 0].groupby("date").underlying.agg(["min", "max"])
    spread["relative_range"] = (spread["max"] - spread["min"]) / spot.set_index(
        "date"
    ).close
    if (spread.relative_range > 0.001).any():
        raise ValueError("Inconsistent spot in archive")
    o.to_csv(out / "nifty_options_chain.csv.gz", index=False)
    f[keys + ["open", "close", "settle", "volume", "oi", "lot_size"]].to_csv(
        out / "nifty_futures.csv", index=False
    )
    spot.to_csv(out / "nifty_daily.csv", index=False)
    panels = []
    for day, g in o.groupby("date"):
        eligible = g[(g.expiry - g.date).dt.days.between(14, 65)]
        if eligible.empty:
            continue
        expiry = eligible.expiry.min()
        g = eligible[eligible.expiry.eq(expiry)]
        c = g[g.opt_type.eq("CE")]
        p = g[g.opt_type.eq("PE")]
        both = c.merge(p, on=["date", "expiry", "strike"], suffixes=("_c", "_p"))
        both = both[
            (both.volume_c > 0)
            & (both.volume_p > 0)
            & both.iv_c.notna()
            & both.iv_p.notna()
        ]
        if both.empty:
            continue
        x = both.loc[(both.strike - both.futures_close_c).abs().idxmin()]
        panels.append(
            dict(
                date=day,
                expiry=expiry,
                strike=x.strike,
                forward=x.futures_close_c,
                iv_call=x.iv_c,
                iv_put=x.iv_p,
                implied_vol=(x.iv_c + x.iv_p) / 2,
                T=x.T_c,
                call_close=x.close_c,
                put_close=x.close_p,
            )
        )
    panel = pd.DataFrame(panels)
    panel.to_csv(out / "atm_panel.csv", index=False)
    manifest = pd.read_csv(root / "data/download_manifest.csv")
    missing = manifest[manifest.status.ne("downloaded")]["date"].tolist()
    report = dict(
        first_date=str(spot.date.min().date()),
        last_date=str(spot.date.max().date()),
        sessions=len(spot),
        option_rows=len(o),
        futures_rows=len(f),
        iv_valid_fraction=float(o.iv.notna().mean()),
        atm_sessions=len(panel),
        unavailable_weekdays=missing,
        rate_assumption=r,
        spot_source="NSE UDiFF UndrlygPric median per day",
        monthly_selection="Exact expiry match with NIFTY index futures",
        notes="Unavailable weekdays are not automatically classified as holidays. IV validity across all strikes includes deep ITM/OTM illiquid contracts.",
    )
    (root / "results/data_quality.json").write_text(json.dumps(report, indent=2))
    pd.DataFrame(audit).to_csv(root / "results/archive_coverage.csv", index=False)
    return report
