"""Parity diagnostics adapted from Joel's supplied pipeline. Never substitutes the traded futures hedge."""
import numpy as np
import pandas as pd
from . import config as C

def _pairs(g: pd.DataFrame, liquid_only: bool) -> pd.DataFrame:
    """Strike-indexed table with call and put close/contracts/oi side by side."""
    g = g[g["close"] > 0]
    if liquid_only:
        g = g[g["contracts"] >= C.MIN_CONTRACTS]
    wide = g.pivot_table(index="strike", columns="opt_type",
                         values=["close", "contracts", "oi"], aggfunc="first")
    if ("close", "CE") not in wide or ("close", "PE") not in wide:
        return pd.DataFrame()
    wide.columns = [f"{a}_{b}" for a, b in wide.columns]
    return wide.dropna(subset=["close_CE", "close_PE"]).sort_index()


def parity_forward(g: pd.DataFrame, T: float, r: float, n: int = 5) -> float:
    p = _pairs(g, liquid_only=True)
    if p.empty:
        return np.nan
    diff = p["close_CE"] - p["close_PE"]
    anchor = diff.abs().idxmin()
    near = p.index.to_series().sub(anchor).abs().nsmallest(n).index
    f_k = near.to_numpy() + np.exp(r * T) * diff.loc[near].to_numpy()
    return float(np.median(f_k))

