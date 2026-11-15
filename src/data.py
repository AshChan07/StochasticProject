"""Normalize downloaded NSE UDiFF ZIPs; keep all strikes to track held contracts."""

import hashlib, zipfile, json
from pathlib import Path
import pandas as pd, numpy as np
from .pricing import iv
from data_pipeline.bhavcopy import normalise
from data_pipeline.forwards import parity_forward


def build(root, r=0.065):
    out = root / "data/clean"
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "data/download_manifest.csv"
    manifest = pd.read_csv(manifest_path) if manifest_path.exists() else None
    expected_hashes = {}
    expected_dates = set()
    if manifest is not None:
        dl = manifest[manifest.status.eq("downloaded")].copy()
        expected_dates = set(pd.to_datetime(dl["date"]).dt.normalize())
        for _, row in dl.iterrows():
            if pd.notna(row.get("source_url")) and pd.notna(row.get("sha256")):
                expected_hashes[Path(str(row["source_url"])).name] = str(row["sha256"]).strip().lower()

    parts = []
    audit = []
    found_dates = set()
    for zpath in sorted((root / "data/raw").rglob("*.zip")):
        if zpath.name in expected_hashes:
            digest = hashlib.sha256(zpath.read_bytes()).hexdigest().lower()
            if digest != expected_hashes[zpath.name]:
                raise ValueError(f"SHA-256 mismatch for {zpath}: expected {expected_hashes[zpath.name]}, got {digest}")
        d = normalise(zpath)
        if d.date.nunique() != 1:
            raise ValueError("Archive must contain one session: " + str(zpath))
        if zpath.name.startswith("BhavCopy_"):
            expected = pd.to_datetime(zpath.name.split("_")[6], format="%Y%m%d")
            if not d.date.eq(expected).all():
                raise ValueError("Date mismatch " + str(zpath))
        elif zpath.stem.startswith("fo_"):
            date_str = zpath.stem.split("_")[1][:8]
            expected = pd.to_datetime(date_str, format="%Y%m%d")
            if not d.date.eq(expected).all():
                raise ValueError("Date mismatch " + str(zpath))
        session_date = pd.Timestamp(d.date.iloc[0]).normalize()
        found_dates.add(session_date)
        audit.append(dict(date=d.date.iloc[0], rows=len(d)))
        parts.append(d)
    if not parts:
        raise RuntimeError(
            "No raw NSE ZIPs found in data/raw. Run download_data.py first to fetch archives, "
            "or omit --rebuild-data to use the included cleaned dataset in data/clean/."
        )
    if expected_dates and not expected_dates.issubset(found_dates):
        missing_dates = sorted(str(dt.date()) for dt in (expected_dates - found_dates))
        raise ValueError(
            f"Missing {len(missing_dates)} expected archive(s) from download_manifest.csv: {missing_dates[:5]}"
        )
    d = pd.concat(parts, ignore_index=True).rename(columns={"contracts": "volume"})
    d["FinInstrmTp"] = d.instrument.map({"FUTIDX": "IDF", "OPTIDX": "IDO"})
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
    if len(spot) != d.date.nunique():
        raise ValueError("Some dates lack archive spot data (e.g. legacy schema). Supply and validate a separate spot series before extending the experiment.")
    spread = d[d.underlying > 0].groupby("date").underlying.agg(["min", "max"])
    spread["relative_range"] = (spread["max"] - spread["min"]) / spot.set_index(
        "date"
    ).close
    if (spread.relative_range > 0.001).any():
        raise ValueError("Inconsistent spot in archive")
    parity = []
    for (day, expiry), group in o.groupby(["date", "expiry"]):
        forward = parity_forward(group.rename(columns={"volume": "contracts"}), float(group["T"].iloc[0]), r)
        traded = float(group.futures_close.iloc[0])
        parity.append(dict(date=day, expiry=expiry, parity_forward=forward,
                           futures_close=traded, basis_bps=1e4*(forward/traded-1)))
    pd.DataFrame(parity).to_csv(root / "results/parity_diagnostics.csv", index=False)
    o.to_csv(out / "nifty_options_chain.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
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
