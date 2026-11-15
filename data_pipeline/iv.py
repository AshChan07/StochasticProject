"""Black-76 pricing and a vectorised implied-volatility solver.

Index options are priced off the forward F of the same expiry, so dividends
never need modelling:
    call = DF * (F N(d1) - K N(d2)),   put = DF * (K N(-d2) - F N(-d1)),
    d1 = (ln(F/K) + sigma^2 T / 2) / (sigma sqrt T),  d2 = d1 - sigma sqrt T,  DF = e^{-rT}.

The price is strictly increasing in sigma, so bisection always converges when
a solution exists. Prices outside the no-arbitrage bounds return NaN rather
than a made-up volatility.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import norm

SIG_LO, SIG_HI = 1e-4, 5.0


def black76(F, K, T, r, sigma, is_call):
    F, K, T, r, sigma = (np.asarray(x, float) for x in (F, K, T, r, sigma))
    is_call = np.asarray(is_call, bool)
    sq = sigma * np.sqrt(T)
    d1 = (np.log(F / K) + 0.5 * sq**2) / sq
    d2 = d1 - sq
    df = np.exp(-r * T)
    call = df * (F * norm.cdf(d1) - K * norm.cdf(d2))
    put = df * (K * norm.cdf(-d2) - F * norm.cdf(-d1))
    return np.where(is_call, call, put)


def implied_vol(price, F, K, T, r, is_call, iters: int = 100):
    """Vectorised IV. NaN where the price breaks the no-arbitrage bounds."""
    price, F, K, T, r = np.broadcast_arrays(*(np.asarray(x, float) for x in (price, F, K, T, r)))
    is_call = np.broadcast_to(np.asarray(is_call, bool), price.shape)
    df = np.exp(-r * T)
    lower = np.where(is_call, np.maximum(df * (F - K), 0), np.maximum(df * (K - F), 0))
    upper = np.where(is_call, df * F, df * K)
    ok = np.isfinite(price) & (T > 0) & (F > 0) & (K > 0) & (price > lower) & (price < upper)

    lo = np.full(price.shape, SIG_LO)
    hi = np.full(price.shape, SIG_HI)
    # bracket check: a price above the 500%-vol price cannot be inverted
    ok &= black76(F, K, np.where(ok, T, 1), r, hi, is_call) >= price
    ok &= black76(F, K, np.where(ok, T, 1), r, lo, is_call) <= price
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        above = black76(F, K, np.where(ok, T, 1), r, mid, is_call) > price
        hi = np.where(above, mid, hi)
        lo = np.where(above, lo, mid)
    out = 0.5 * (lo + hi)
    return np.where(ok, out, np.nan)
