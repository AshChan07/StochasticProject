"""Historical straddle experiment. Prior-close signals/deltas execute at next open.
One signed straddle unit, fractional futures, no overlapping positions.
Costs are illustrative all-in proxies, NOT an exact historical statutory schedule.
"""

import json
import numpy as np, pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from .pricing import black, vega


def fit_garch11(returns_train):
    """Maximum likelihood estimation of GARCH(1,1) on training returns."""
    ret = returns_train.dropna().to_numpy()
    s2 = float(np.var(ret))
    if s2 <= 0:
        s2 = 1e-4

    def neg_loglik(params):
        omega, alpha, beta = params
        n = len(ret)
        v = np.zeros(n)
        v[0] = s2
        for t in range(1, n):
            v[t] = omega + alpha * (ret[t - 1] ** 2) + beta * v[t - 1]
        v = np.maximum(v, 1e-9)
        return 0.5 * np.sum(np.log(2 * np.pi) + np.log(v) + (ret ** 2) / v)

    init = [s2 * 0.05, 0.08, 0.88]
    bounds = [(1e-8, 1.0), (0.005, 0.35), (0.4, 0.98)]
    cons = {"type": "ineq", "fun": lambda p: 0.999 - (p[1] + p[2])}
    res = minimize(neg_loglik, init, bounds=bounds, constraints=cons, method="SLSQP")
    if res.success:
        return res.x
    return init


class Market:
    def __init__(self, root, ewma_lambda=0.94):
        if not 0 < ewma_lambda < 1:
            raise ValueError("EWMA lambda must lie in (0,1)")
        clean = root / "data/clean"
        o = pd.read_csv(
            clean / "nifty_options_chain.csv.gz", parse_dates=["date", "expiry"]
        )
        f = pd.read_csv(clean / "nifty_futures.csv", parse_dates=["date", "expiry"])
        self.options = o.set_index(
            ["date", "expiry", "strike", "opt_type"]
        ).sort_index()
        self.futures = f.set_index(["date", "expiry"]).sort_index()
        spot = (
            pd.read_csv(clean / "nifty_daily.csv", parse_dates=["date"])
            .set_index("date")
            .sort_index()
        )
        returns = np.log(spot.close).diff()
        if spot.index.duplicated().any() or not np.isfinite(spot.close).all() or (spot.close <= 0).any():
            raise ValueError("Invalid spot dates or closes")
        if self.options.index.duplicated().any() or self.futures.index.duplicated().any():
            raise ValueError("Duplicate contract keys")
        self.spot = spot
        # Initial 60 returns only, then a one-step EWMA update including today's close.
        v = np.full(len(spot), np.nan)
        ret = returns.to_numpy()
        if len(v) > 60:
            v[60] = np.mean(ret[1:61] ** 2)
            for j in range(61, len(v)):
                v[j] = ewma_lambda * v[j - 1] + (1 - ewma_lambda) * ret[j] ** 2
        self.forecast = pd.Series(np.sqrt(v * 252), index=spot.index)
        # GARCH(1,1) Volatility forecast
        train_rets = returns.loc[:"2025-06-30"]
        omega, alpha, beta = fit_garch11(train_rets)
        self.garch_params = dict(omega=float(omega), alpha=float(alpha), beta=float(beta))
        gv = np.full(len(spot), np.nan)
        if len(gv) > 1:
            gv[0] = np.var(ret[1:61]) if len(ret) > 60 else np.var(ret[1:])
            for j in range(1, len(gv)):
                r_prev = ret[j - 1] if np.isfinite(ret[j - 1]) else 0.0
                gv[j] = omega + alpha * (r_prev ** 2) + beta * gv[j - 1]
        self.garch_forecast = pd.Series(
            np.sqrt(np.maximum(gv, 1e-8) * 252), index=spot.index
        )

        panel = pd.read_csv(
            clean / "atm_panel.csv", parse_dates=["date", "expiry"]
        ).set_index("date")
        panel["forecast_vol"] = self.forecast
        panel["garch_forecast"] = self.garch_forecast
        panel["signal"] = panel.forecast_vol - panel.implied_vol

        # Vega & Vega-weighted mispricing
        tau = np.maximum(panel["T"].to_numpy(dtype=float), 1e-6)
        panel["vega"] = vega(
            panel.forward.to_numpy(dtype=float),
            panel.strike.to_numpy(dtype=float),
            tau,
            0.065,
            panel.implied_vol.to_numpy(dtype=float),
        )
        panel["vega_mispricing"] = panel.vega * panel.signal

        panel.to_csv(clean / "signal.csv")
        self.panel = panel
        future = sum(returns.shift(-j) ** 2 for j in range(1, 6)) / 5 * 252
        evals = pd.DataFrame(
            {"forecast_vol": self.forecast, "future_realized_vol_5d": np.sqrt(future)}
        )
        evals["target_end"] = pd.Series(spot.index, index=spot.index).shift(-5)
        evals["sample"] = np.where(evals.index > "2025-06-30", "test", "train")
        evals.loc[
            (evals.index <= "2025-06-30") & (evals.target_end > "2025-06-30"),
            "future_realized_vol_5d",
        ] = np.nan
        (root / "results").mkdir(parents=True, exist_ok=True)
        evals.to_csv(root / "results/forecast_evaluation.csv")
        metrics = []
        for period, g in evals.dropna().groupby("sample"):
            fv = g.forecast_vol**2
            rv = g.future_realized_vol_5d**2
            metrics.append(
                dict(
                    sample=period,
                    n=len(g),
                    rmse_vol=float(
                        np.sqrt(
                            ((g.forecast_vol - g.future_realized_vol_5d) ** 2).mean()
                        )
                    ),
                    qlike=float((rv / fv - np.log(rv / fv) - 1).mean()),
                )
            )
        pd.DataFrame(metrics).to_csv(root / "results/forecast_metrics.csv", index=False)

    def quote(self, day, expiry, strike):
        c = self.options.loc[(day, expiry, strike, "CE")]
        p = self.options.loc[(day, expiry, strike, "PE")]
        f = self.futures.loc[(day, expiry)]
        return c, p, f


def positive_quotes(*values):
    return bool(np.all(np.isfinite(values)) and np.all(np.asarray(values) > 0))


def ledger_increment(cash, hedge, Fprev, Fnew, days, r):
    interest = cash * np.expm1(r * days / 365)
    futures = hedge * (Fnew - Fprev)
    return cash + interest + futures, interest, futures


def run(
    m,
    start,
    end,
    threshold=0.02,
    rule="implied",
    cost_mult=1.0,
    rebalance=1,
    r=0.065,
    holding=5,
    capital=100000.0,
    execution="open",
    threshold_schedule=None,
    force_direction=None,
    max_positions=1,
):
    if rule not in {"implied", "forecast", "unhedged"}:
        raise ValueError("Unknown hedge rule")
    if execution not in {"open", "close"}:
        raise ValueError("Execution must be open or close")
    if holding < 1 or rebalance < 1 or (threshold < 0 and force_direction is None) or cost_mult < 0 or capital <= 0:
        raise ValueError("Invalid experiment parameters")
    dates = m.spot.loc[start:end].index
    if dates.empty or m.spot.index.get_loc(dates[0]) == 0:
        raise ValueError("Sample needs observations and a preceding decision session")
    all_dates = m.spot.index
    daily = []
    trades = []
    events = []
    pos = None
    count = 0
    if max_positions <= 1:
        for i, day in enumerate(dates):
            active_threshold = threshold if threshold_schedule is None else float(threshold_schedule.loc[day])
            if not np.isfinite(active_threshold) or (active_threshold < 0 and force_direction is None):
                raise ValueError("Invalid scheduled threshold")
            prev = all_dates[all_dates.get_loc(day) - 1]
            option_pnl = hedge_pnl = finance = cost = turnover = 0.0
            trade_id = 0
            if pos is not None:
                c, p, f = m.quote(day, pos["expiry"], pos["strike"])
                if not positive_quotes(c[execution], p[execution], f[execution]):
                    raise ValueError(
                        f"Missing executable held-position opening quote {day}"
                    )
                mark = c[execution] + p[execution]
                before = pos["cash"] + pos["q"] * pos["mark"]
                pos["cash"], finance, hedge_pnl = ledger_increment(
                    pos["cash"], pos["h"], pos["F"], f[execution], (day - pos["last"]).days, r
                )
                option_pnl = pos["q"] * (mark - pos["mark"])
                trade_id = pos["id"]
                exit_now = (
                    (i - pos["entry_i"] >= holding)
                    or ((pos["expiry"] - day).days <= 7)
                    or i == len(dates) - 1
                )
                if exit_now:
                    cost = cost_mult * (
                        0.002 * abs(pos["q"]) * mark + 0.0001 * abs(pos["h"]) * f[execution]
                    )
                    turnover = abs(pos["h"]) * f[execution]
                    pos["cash"] += pos["q"] * mark - cost
                    pnl = pos["cash"]
                    trades.append(
                        dict(
                            trade_id=trade_id,
                            entry_date=pos["entry_date"],
                            exit_date=day,
                            expiry=pos["expiry"],
                            strike=pos["strike"],
                            direction=pos["q"],
                            entry_signal=pos["signal"],
                            pnl=pnl,
                            holding_sessions=i - pos["entry_i"],
                        )
                    )
                    daily_pnl = pos["cash"] - before
                    pos = None
                else:
                    newh = pos["h"]
                    if (i - pos["entry_i"]) % rebalance == 0:
                        pc, pp, pf = m.quote(prev, pos["expiry"], pos["strike"])
                        vols = (
                            [pc.iv, pp.iv]
                            if rule == "implied"
                            else [m.forecast.loc[prev]] * 2
                        )
                        if rule == "unhedged":
                            newh = 0.0
                        elif np.all(np.isfinite(vols)) and min(vols) > 0 and positive_quotes(pf.close):
                            tau = (pos["expiry"] - prev).days / 365
                            newh = -pos["q"] * (
                                float(black(pf.close, pos["strike"], tau, r, vols[0])[1])
                                + float(
                                    black(pf.close, pos["strike"], tau, r, vols[1], True)[1]
                                )
                            )
                        else:
                            events.append(
                                dict(date=day, event="hedge_carried_invalid_prior_iv")
                            )
                    turnover = abs(newh - pos["h"]) * f[execution]
                    cost = cost_mult * 0.0001 * turnover
                    pos["cash"] -= cost
                    pos.update(h=newh, F=f[execution], mark=mark, last=day)
                    daily_pnl = pos["cash"] + pos["q"] * mark - before
            else:
                daily_pnl = 0.0
                if i + holding < len(dates) and prev in m.panel.index:
                    sig = m.panel.loc[prev]
                    if np.isfinite(sig.signal) and abs(sig.signal) > active_threshold:
                        try:
                            c, p, f = m.quote(day, sig.expiry, sig.strike)
                        except KeyError:
                            events.append(
                                dict(date=day, event="entry_cancelled_missing_contract")
                            )
                            c = None
                        if (
                            c is not None
                            and positive_quotes(c[execution], p[execution], f[execution])
                            and (sig.expiry - day).days > 7
                        ):
                            q = force_direction if force_direction is not None else (1 if sig.signal > 0 else -1)
                            tau = (sig.expiry - prev).days / 365
                            vols = (
                                [sig.iv_call, sig.iv_put]
                                if rule == "implied"
                                else [sig.forecast_vol] * 2
                            )
                            h = -q * (
                                float(black(sig.forward, sig.strike, tau, r, vols[0])[1])
                                + float(
                                    black(sig.forward, sig.strike, tau, r, vols[1], True)[1]
                                )
                            )
                            if rule == "unhedged":
                                h = 0.0
                            if not np.isfinite(h):
                                raise ValueError("Invalid entry hedge")
                            mark = c[execution] + p[execution]
                            turnover = abs(h) * f[execution]
                            cost = cost_mult * (0.002 * mark + 0.0001 * turnover)
                            count += 1
                            pos = dict(
                                id=count,
                                q=q,
                                h=h,
                                expiry=sig.expiry,
                                strike=sig.strike,
                                cash=-q * mark - cost,
                                mark=mark,
                                F=f[execution],
                                last=day,
                                entry_i=i,
                                entry_date=day,
                                signal=sig.signal,
                            )
                            daily_pnl = -cost
                            trade_id = count
                        elif c is not None:
                            events.append(
                                dict(
                                    date=day,
                                    event="entry_cancelled_unavailable_open_or_expiry",
                                )
                            )
            daily.append(
                dict(
                    date=day,
                    trade_id=trade_id,
                    option_pnl=option_pnl,
                    futures_pnl=hedge_pnl,
                    financing=finance,
                    cost=cost,
                    net_pnl=daily_pnl,
                    futures_turnover=turnover,
                    position=0 if pos is None else pos["q"],
                )
            )

    else:
        # Multi-position inventory loop
        positions = []
        count = 0
        for i, day in enumerate(dates):
            active_threshold = (
                threshold
                if threshold_schedule is None
                else float(threshold_schedule.loc[day])
            )
            if not np.isfinite(active_threshold) or (
                active_threshold < 0 and force_direction is None
            ):
                raise ValueError("Invalid scheduled threshold")
            prev = all_dates[all_dates.get_loc(day) - 1]
            day_opt = day_fut = day_fin = day_cst = day_trn = 0.0
            day_tids = []
            active = []
            for pos in positions:
                c, p, f = m.quote(day, pos["expiry"], pos["strike"])
                if not positive_quotes(c[execution], p[execution], f[execution]):
                    raise ValueError(f"Missing executable quote {day}")
                mark = c[execution] + p[execution]
                before = pos["cash"] + pos["q"] * pos["mark"]
                pos["cash"], fin, hpnl = ledger_increment(
                    pos["cash"], pos["h"], pos["F"], f[execution], (day - pos["last"]).days, r
                )
                opnl = pos["q"] * (mark - pos["mark"])
                day_fin += fin
                day_fut += hpnl
                day_opt += opnl
                day_tids.append(pos["id"])

                exit_now = (
                    (i - pos["entry_i"] >= holding)
                    or ((pos["expiry"] - day).days <= 7)
                    or i == len(dates) - 1
                )
                if exit_now:
                    cost = cost_mult * (
                        0.002 * abs(pos["q"]) * mark + 0.0001 * abs(pos["h"]) * f[execution]
                    )
                    trn = abs(pos["h"]) * f[execution]
                    pos["cash"] += pos["q"] * mark - cost
                    day_cst += cost
                    day_trn += trn
                    trades.append(
                        dict(
                            trade_id=pos["id"],
                            entry_date=pos["entry_date"],
                            exit_date=day,
                            expiry=pos["expiry"],
                            strike=pos["strike"],
                            direction=pos["q"],
                            entry_signal=pos["signal"],
                            pnl=pos["cash"],
                            holding_sessions=i - pos["entry_i"],
                        )
                    )
                else:
                    newh = pos["h"]
                    if (i - pos["entry_i"]) % rebalance == 0:
                        pc, pp, pf = m.quote(prev, pos["expiry"], pos["strike"])
                        vols = (
                            [pc.iv, pp.iv]
                            if rule == "implied"
                            else [m.forecast.loc[prev]] * 2
                        )
                        if rule == "unhedged":
                            newh = 0.0
                        elif np.all(np.isfinite(vols)) and min(vols) > 0 and positive_quotes(pf.close):
                            tau = (pos["expiry"] - prev).days / 365
                            newh = -pos["q"] * (
                                float(black(pf.close, pos["strike"], tau, r, vols[0])[1])
                                + float(
                                    black(pf.close, pos["strike"], tau, r, vols[1], True)[1]
                                )
                            )
                        else:
                            events.append(
                                dict(date=day, event="hedge_carried_invalid_prior_iv")
                            )
                    trn = abs(newh - pos["h"]) * f[execution]
                    cost = cost_mult * 0.0001 * trn
                    pos["cash"] -= cost
                    pos.update(h=newh, F=f[execution], mark=mark, last=day)
                    day_cst += cost
                    day_trn += trn
                    active.append(pos)
            positions = active

            # Check new entry if below capacity limit
            if (
                len(positions) < max_positions
                and i + holding < len(dates)
                and prev in m.panel.index
            ):
                sig = m.panel.loc[prev]
                if np.isfinite(sig.signal) and abs(sig.signal) > active_threshold:
                    try:
                        c, p, f = m.quote(day, sig.expiry, sig.strike)
                    except KeyError:
                        c = None
                    if (
                        c is not None
                        and positive_quotes(c[execution], p[execution], f[execution])
                        and (sig.expiry - day).days > 7
                    ):
                        q = (
                            force_direction
                            if force_direction is not None
                            else (1 if sig.signal > 0 else -1)
                        )
                        tau = (sig.expiry - prev).days / 365
                        vols = (
                            [sig.iv_call, sig.iv_put]
                            if rule == "implied"
                            else [sig.forecast_vol] * 2
                        )
                        h = -q * (
                            float(black(sig.forward, sig.strike, tau, r, vols[0])[1])
                            + float(
                                black(sig.forward, sig.strike, tau, r, vols[1], True)[1]
                            )
                        )
                        if rule == "unhedged":
                            h = 0.0
                        if not np.isfinite(h):
                            raise ValueError("Invalid entry hedge")
                        mark = c[execution] + p[execution]
                        trn = abs(h) * f[execution]
                        cost = cost_mult * (0.002 * mark + 0.0001 * trn)
                        count += 1
                        positions.append(
                            dict(
                                id=count,
                                q=q,
                                h=h,
                                expiry=sig.expiry,
                                strike=sig.strike,
                                cash=-q * mark - cost,
                                mark=mark,
                                F=f[execution],
                                last=day,
                                entry_i=i,
                                entry_date=day,
                                signal=sig.signal,
                            )
                        )
                        day_cst += cost
                        day_trn += trn
                        day_tids.append(count)
            daily.append(
                dict(
                    date=day,
                    trade_id=";".join(map(str, day_tids)) if day_tids else "0",
                    option_pnl=day_opt,
                    futures_pnl=day_fut,
                    financing=day_fin,
                    cost=day_cst,
                    net_pnl=day_opt + day_fut + day_fin - day_cst,
                    futures_turnover=day_trn,
                    position=sum(p["q"] for p in positions),
                )
            )
        if len(positions) > 0:
            raise AssertionError("Unclosed multi-positions")
    d = pd.DataFrame(daily)
    t = pd.DataFrame(trades, columns=["trade_id", "entry_date", "exit_date", "expiry", "strike", "direction", "entry_signal", "pnl", "holding_sessions"])
    if max_positions <= 1 and pos is not None:
        raise AssertionError("Unclosed position")
    if not np.allclose(
        d.net_pnl, d.option_pnl + d.futures_pnl + d.financing - d.cost, atol=1e-7
    ):
        raise AssertionError("Ledger does not reconcile")
    if not np.isclose(d.net_pnl.sum(), 0 if t.empty else t.pnl.sum(), atol=1e-7):
        raise AssertionError("Trades do not reconcile")
    d["cumulative_pnl"] = d.net_pnl.cumsum()
    d["return_on_fixed_capital"] = d.net_pnl / capital
    curve = np.r_[0, d.cumulative_pnl]
    dd = curve - np.maximum.accumulate(curve)
    std = d.net_pnl.std(ddof=1)
    metric = dict(
        rule=rule,
        execution=execution,
        threshold=threshold,
        cost_multiplier=cost_mult,
        rebalance_sessions=rebalance,
        sessions=len(d),
        trades=len(t),
        net_pnl=d.net_pnl.sum(),
        gross_pnl=d.net_pnl.sum() + d.cost.sum(),
        cost=d.cost.sum(),
        max_drawdown_points=-dd.min(),
        sharpe_excess=np.sqrt(252) * d.net_pnl.mean() / std if std > 0 else np.nan,
        hit_rate=(t.pnl > 0).mean() if len(t) else np.nan,
        mean_trade_pnl=t.pnl.mean() if len(t) else np.nan,
        return_fixed_capital=d.net_pnl.sum() / capital,
        futures_turnover=d.futures_turnover.sum(),
        long_trades=int((t.direction == 1).sum()) if len(t) else 0,
        short_trades=int((t.direction == -1).sum()) if len(t) else 0,
    )
    return d, t, metric, pd.DataFrame(events, columns=["date", "event"])


def run_benchmark(m, start, end, holding=5, cost_mult=1.0, r=0.065, capital=100000.0):
    """Naive rolling short ATM straddle benchmark (Variance Risk Premium baseline).
    Sells ATM straddles whenever no position is open, delta-hedging daily with implied vol.
    """
    return run(
        m,
        start,
        end,
        threshold=-999.0,
        rule="implied",
        cost_mult=cost_mult,
        rebalance=1,
        r=r,
        holding=holding,
        capital=capital,
        force_direction=-1,
    )


def experiment(root):
    m = Market(root)
    out = root / "results"
    out.mkdir(parents=True, exist_ok=True)
    train = []
    for k in [0.0, 0.01, 0.02, 0.03]:
        for rule in ["implied", "forecast"]:
            _, _, metric, _ = run(m, "2024-10-07", "2025-06-30", threshold=k, rule=rule)
            train.append(metric)
    tr = pd.DataFrame(train)
    tr.to_csv(out / "threshold_calibration.csv", index=False)
    g = tr.groupby("threshold").agg(pnl=("net_pnl", "mean"), trades=("trades", "min"))
    g = g[g.trades >= 10]
    k = float(g.pnl.idxmax()) if len(g) else 0.02
    rows = []
    curve = {}
    for rule in ["implied", "forecast"]:
        d, t, met, e = run(m, "2025-07-01", "2025-12-31", threshold=k, rule=rule)
        rows.append(met)
        d.to_csv(out / f"backtest_daily_{rule}.csv", index=False)
        t.to_csv(out / f"trades_{rule}.csv", index=False)
        e.to_csv(out / f"events_{rule}.csv", index=False)
        curve[rule] = d
    pd.DataFrame(rows).to_csv(out / "test_metrics.csv", index=False)
    sensitivity = []
    for cm in [0, 1, 2, 5]:
        for rule in ["implied", "forecast"]:
            _, _, met, _ = run(
                m, "2025-07-01", "2025-12-31", threshold=k, rule=rule, cost_mult=cm
            )
            sensitivity.append(met)
    for freq in [2, 5]:
        for rule in ["implied", "forecast"]:
            _, _, met, _ = run(
                m, "2025-07-01", "2025-12-31", threshold=k, rule=rule, rebalance=freq
            )
            sensitivity.append(met)
    pd.DataFrame(sensitivity).to_csv(out / "sensitivity.csv", index=False)
    # Threshold alternatives are diagnostics only, never used to reselect after test.
    checks = []
    for kk in [0.0, 0.01, 0.02, 0.03]:
        for rule in ["implied", "forecast"]:
            _, _, met, _ = run(m, "2025-07-01", "2025-12-31", threshold=kk, rule=rule)
            checks.append(met)
    pd.DataFrame(checks).to_csv(out / "test_threshold_sensitivity.csv", index=False)
    paired = pd.DataFrame(
        {
            "implied": pd.read_csv(out / "trades_implied.csv").pnl,
            "forecast": pd.read_csv(out / "trades_forecast.csv").pnl,
        }
    )
    diff = (paired.forecast - paired.implied).to_numpy()
    rng = np.random.default_rng(244)
    boot = (
        rng.choice(diff, (5000, len(diff)), replace=True).mean(axis=1)
        if len(diff)
        else np.array([np.nan])
    )
    config = dict(
        train_start="2024-10-07",
        train_end="2025-06-30",
        test_start="2025-07-01",
        test_end="2025-12-31",
        selected_threshold=k,
        ewma_lambda=0.94,
        warmup_returns=60,
        holding_sessions=5,
        rate=0.065,
        option_cost_fraction=0.002,
        futures_cost_notional_fraction=0.0001,
        fixed_reporting_capital=100000,
        paired_trade_mean_difference=float(diff.mean()),
        paired_trade_bootstrap_95=(list(np.quantile(boot, [0.025, 0.975])) if len(diff) >= 20 else None),
        bootstrap_caveat="Suppressed below 20 trades; above that, IID bootstrap remains descriptive and ignores serial dependence.",
        execution="Prior-close signal and delta, next-session opening-price execution",
        sizing="One signed straddle unit with fractional futures; no exchange lot or margin enforcement",
        scope="Core replication plus historical adaptation. Primary signal and hedging use EWMA only; GARCH(1,1) is fitted on training returns as an exploratory diagnostic in data/clean/signal.csv. No Heston or exact statutory cost schedule.",
    )
    (out / "experiment.json").write_text(json.dumps(config, indent=2))
    fig, ax = plt.subplots(figsize=(8, 3.4))
    for rule, color in [("implied", "#137c83"), ("forecast", "#e39332")]:
        d = curve[rule]
        ax.plot(d.date, d.cumulative_pnl, label=rule + " vol delta", color=color)
    ax.axhline(0, color="#667", lw=0.6)
    ax.set(ylabel="Cumulative net P&L (index points)", xlabel="Test period, 2025")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "figures/historical_pnl.png", dpi=190)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 3.3))
    p = m.panel.dropna()
    ax.plot(p.index, p.implied_vol * 100, label="ATM implied", color="#137c83", lw=1)
    ax.plot(p.index, p.forecast_vol * 100, label="EWMA forecast", color="#e39332", lw=1)
    ax.axvline(pd.Timestamp("2025-07-01"), ls="--", color="#667")
    ax.set(ylabel="Annualized volatility (%)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "figures/volatility.png", dpi=190)
    plt.close(fig)
    return config
