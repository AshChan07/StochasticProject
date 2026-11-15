"""Self-financing stock hedge under GBM with exact transitions and a cash account."""

from pathlib import Path
import numpy as np, pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .pricing import bs


def simulate(
    n=252, paths=20000, actual=0.3, implied=0.2, seed=244, mu=0.1, r=0.05, T=1
):
    rng = np.random.default_rng(seed)
    dt = T / n
    S = np.full(paths, 100.0)
    price = float(bs(100, 100, T, r, implied)[0])
    vols = [actual, implied]
    h = np.stack([-bs(S, 100, T, r, v)[1] for v in vols])
    cash = -price - h * S
    for j in range(n):
        Sn = S * np.exp(
            (mu - 0.5 * actual**2) * dt
            + actual * np.sqrt(dt) * rng.standard_normal(paths)
        )
        cash *= np.exp(r * dt)
        if j < n - 1:
            hn = np.stack([-bs(Sn, 100, T - (j + 1) * dt, r, v)[1] for v in vols])
            cash -= (hn - h) * Sn
            h = hn
        S = Sn
    pnl = (np.maximum(S - 100, 0) + h * S + cash) * np.exp(-r * T)
    return pnl, float(bs(100, 100, T, r, actual)[0]) - price


def run(root):
    out = root / "results"
    fig = out / "figures"
    fig.mkdir(parents=True, exist_ok=True)
    rows = []
    distributions = {}
    for actual in [0.15, 0.3]:
        a, pred = simulate(actual=actual)
        for i, rule in enumerate(["actual", "implied"]):
            x = a[i]
            s = pd.Series(x)
            q01 = float(np.percentile(x, 1))
            q05 = float(np.percentile(x, 5))
            rows.append(
                dict(
                    actual=actual,
                    implied=0.2,
                    rule=rule,
                    paths=len(x),
                    rebalances=252,
                    theory_actual=pred,
                    mean=float(x.mean()),
                    std=float(x.std(ddof=1)),
                    se=float(x.std(ddof=1) / np.sqrt(len(x))),
                    skewness=float(s.skew()),
                    excess_kurtosis=float(s.kurtosis()),
                    var_95=float(-q05 if q05 < 0 else 0.0),
                    var_99=float(-q01 if q01 < 0 else 0.0),
                    cvar_95=float(-x[x <= q05].mean()) if (x <= q05).any() else 0.0,
                    cvar_99=float(-x[x <= q01].mean()) if (x <= q01).any() else 0.0,
                    positive_fraction=float((x > 0).mean()),
                )
            )
            distributions[f"{actual}_{rule}"] = x
    pd.DataFrame(rows).to_csv(out / "simulation_summary.csv", index=False)
    pd.DataFrame(distributions).to_csv(out / "simulation_paths.csv.gz", index=False)
    fig1, axs = plt.subplots(1, 2, figsize=(10, 3.7))
    hist = []
    for ax, actual in zip(axs, [0.15, 0.3]):
        for rule, color in [("actual", "#137c83"), ("implied", "#e39332")]:
            x = distributions[f"{actual}_{rule}"]
            counts, bins = np.histogram(x, bins=65)
            ax.hist(
                x,
                bins=65,
                density=True,
                alpha=0.55,
                label=rule + " vol hedge",
                color=color,
            )
            hist.extend(
                [
                    dict(
                        actual=actual,
                        rule=rule,
                        center=(bins[k] + bins[k + 1]) / 2,
                        density=c / (len(x) * (bins[k + 1] - bins[k])),
                    )
                    for k, c in enumerate(counts)
                ]
            )
        ax.set(
            title=f"Actual {actual:.0%}, implied 20%",
            xlabel="Discounted P&L per call",
            ylabel="Density",
        )
        ax.legend(fontsize=8)
    fig1.tight_layout()
    fig1.savefig(fig / "simulation_distribution.png", dpi=190)
    plt.close(fig1)
    pd.DataFrame(hist).to_csv(out / "histogram.csv", index=False)

    # Drift sensitivity analysis across mu in [-0.2, 0.3]
    drift_rows = []
    for mu in [-0.20, -0.10, 0.00, 0.10, 0.20, 0.30]:
        a, pred = simulate(n=252, paths=10000, actual=0.3, implied=0.2, mu=mu, seed=244)
        for i, rule in enumerate(["actual", "implied"]):
            x = a[i]
            drift_rows.append(
                dict(
                    mu=mu,
                    actual=0.3,
                    implied=0.2,
                    rule=rule,
                    paths=len(x),
                    theory_actual=pred,
                    mean=float(x.mean()),
                    std=float(x.std(ddof=1)),
                    error_vs_theory=float(x.mean() - pred),
                )
            )
    pd.DataFrame(drift_rows).to_csv(out / "drift_sensitivity.csv", index=False)

    conv = []
    for n in [12, 26, 52, 126, 252, 504, 1008]:
        a, pred = simulate(n=n, paths=6000)
        conv.append(
            dict(
                rebalances=n,
                actual_error_std=a[0].std(ddof=1),
                implied_pnl_std=a[1].std(ddof=1),
                actual_mean=a[0].mean(),
                prediction=pred,
            )
        )
    c = pd.DataFrame(conv)
    c.to_csv(out / "convergence.csv", index=False)
    slope = np.polyfit(np.log(c.rebalances), np.log(c.actual_error_std), 1)[0]
    fig1, ax = plt.subplots(figsize=(7, 3.6))
    ax.loglog(
        c.rebalances,
        c.actual_error_std,
        "o-",
        color="#137c83",
        label=f"Measured slope {slope:.3f}",
    )
    ax.loglog(
        c.rebalances,
        c.actual_error_std.iloc[0] * np.sqrt(c.rebalances.iloc[0] / c.rebalances),
        "--",
        color="#e39332",
        label="N^(-1/2) reference",
    )
    ax.set(xlabel="Rebalances per year", ylabel="Std. dev. of discounted P&L")
    ax.legend()
    fig1.tight_layout()
    fig1.savefig(fig / "convergence.png", dpi=190)
    plt.close(fig1)
    return slope
