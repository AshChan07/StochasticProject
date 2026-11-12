"""Black-Scholes and Black-76 prices/Greeks; volatility is an annual decimal."""

import numpy as np
from scipy.special import ndtr


def bs(S, K, T, r, v, put=False):
    S, T, v = np.broadcast_arrays(
        np.asarray(S, float), np.asarray(T, float), np.asarray(v, float)
    )
    tau = np.maximum(T, 1e-12)
    vv = np.maximum(v, 1e-12)
    root = np.sqrt(tau)
    d1 = (np.log(S / K) + (r + vv * vv / 2) * tau) / (vv * root)
    d2 = d1 - vv * root
    price = S * ndtr(d1) - K * np.exp(-r * tau) * ndtr(d2)
    delta = ndtr(d1)
    if put:
        price = price - S + K * np.exp(-r * tau)
        delta = delta - 1
    payoff = np.maximum(K - S, 0) if put else np.maximum(S - K, 0)
    return np.where(T <= 0, payoff, price), np.where(
        T <= 0, (S < K) * -1.0 if put else (S > K) * 1.0, delta
    )


def black(F, K, T, r, v, put=False):
    price, delta = bs(np.asarray(F) * np.exp(-r * np.asarray(T)), K, T, r, v, put)
    return price, delta * np.exp(-r * np.asarray(T))


def vega(F, K, T, r, v):
    d1 = (np.log(np.asarray(F) / K) + 0.5 * v * v * T) / (v * np.sqrt(T))
    return np.exp(-r * T) * F * np.exp(-d1 * d1 / 2) / np.sqrt(2 * np.pi) * np.sqrt(T)


def iv(price, F, K, T, r, put=False):
    price, F, K, T, put = np.broadcast_arrays(
        np.asarray(price, float),
        np.asarray(F, float),
        np.asarray(K, float),
        np.asarray(T, float),
        np.asarray(put, bool),
    )
    disc = np.exp(-r * T)
    lower = disc * np.maximum(np.where(put, K - F, F - K), 0)
    upper = disc * np.where(put, K, F)
    valid = (
        (T > 0) & (F > 0) & (K > 0) & (price > lower + 1e-8) & (price < upper - 1e-8)
    )
    lo = np.full(price.shape, 1e-5)
    hi = np.full(price.shape, 5.0)
    for _ in range(55):
        mid = (lo + hi) / 2
        c, _ = black(F, K, T, r, mid)
        p = c - disc * (F - K)
        value = np.where(put, p, c)
        lo = np.where(value < price, mid, lo)
        hi = np.where(value >= price, mid, hi)
    out = (lo + hi) / 2
    return np.where(valid & (out < 4.999), out, np.nan)
