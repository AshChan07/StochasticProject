# Volatility Arbitrage and Delta Hedging on NIFTY Index Options

A stochastic-calculus project implementing the central hedging comparison in **Ahmad & Wilmott (2005)** and applying two delta-hedging rules to historical NIFTY monthly options.

**Course:** MAC F244 — Stochastic Calculus and Application to Finance  
**Institution:** BITS Pilani, K K Birla Goa Campus  
**Instructor:** Mayank Goel  
**Team:** Arnav, Rohan, Joel, Ashwath and Advay  
**GitHub Repository:** [https://github.com/AshChan07/StochasticProject](https://github.com/AshChan07/StochasticProject)  
*(Note: Ensure repository visibility is set to Public for evaluation, or add course evaluators as collaborators.)*

---

## Overview

When an option's implied volatility differs from the volatility expected for its underlying, which volatility should determine the hedge?

This project investigates that question through:

1. A mathematical derivation using Itô's formula and the Black–Scholes pricing PDE.
2. Monte Carlo replication with known actual volatility.
3. A historical NIFTY straddle backtest comparing implied-volatility delta with EWMA-forecast-volatility delta.
4. Transaction-cost, threshold and rebalancing-frequency sensitivity analysis.

> **Note on Historical Findings:** The calibrated strategy produces only **three test-period trades** (all short straddles), so the empirical results are exploratory and cannot establish statistical arbitrage or general hedge superiority.

---

## Directory Structure

```text
MAC_F244_Volatility_Arbitrage/
├── README.md                              # Project documentation
├── requirements.txt                       # Python dependencies (numpy, pandas, scipy, matplotlib, reportlab, pypdf, requests)
├── run_project.py                         # Master runner: executes simulations, backtest, and writes results/
├── download_data.py                       # Downloads official NSE UDiFF archives into data/raw/
│
├── src/
│   ├── __init__.py
│   ├── pricing.py                         # Black–Scholes, Black-76, delta, vega, and IV bisection solver
│   ├── simulation.py                      # GBM Monte Carlo, self-financing cash hedge, tail risk (VaR/CVaR)
│   ├── backtest.py                        # EWMA volatility, trading rules, ledger, and accounting reconciliation
│   ├── robustness.py                      # Exploratory diagnostics: futures SDE, Greek attribution, walk-forward
│   └── data.py                            # Archive normalisation, futures matching, ATM straddle selection
│
├── data_pipeline/
│   ├── __init__.py
│   ├── bhavcopy.py                        # Dual-schema NSE bhavcopy parser (legacy & post-July-2024 UDiFF)
│   ├── config.py                          # Schema column definitions, archive URLs, default constants
│   ├── forwards.py                        # Put-call parity forward extractor
│   └── iv.py                              # Black-76 vectorised implied volatility utilities
│
├── tests/
│   ├── pipeline_fixtures.py               # In-memory synthetic bhavcopy fixtures across schema boundaries
│   ├── test_project.py                    # 17 core unit tests (pricing, parity, convergence, ledger)
│   └── test_audit.py                      # 16 pipeline audit tests (Black-76 PDE, execution timestamps, schemas)
│
└── data/
    ├── download_manifest.csv              # Official download audit log (390 dates, URLs, statuses, SHA-256 hashes)
    └── clean/
        ├── nifty_daily.csv                # Underlying closes (370 sessions, derived from archive underlying median)
        ├── nifty_futures.csv              # Futures contracts, closes, settles, volume, OI
        ├── nifty_options_chain.csv.gz     # All monthly options with Black-76 implied volatilities (222,520 records)
        └── atm_panel.csv                  # Filtered ATM monthly straddle candidates (14–65 days to expiry)
```

Running `python run_project.py` dynamically creates `results/` containing all output CSVs (trade ledgers, performance metrics, sensitivity tables) and figures (`results/figures/*.png`).

---

## Quick Start

### Requirements
- Python **3.11 or newer** (tested on Python 3.12).
- Dependencies: `pip install -r requirements.txt`.
- No API key, brokerage account, or paid subscription is required. All necessary cleaned data is included.

### Execution

```bash
# 1. Run full reproducible study (simulation + backtest + generate all CSVs/figures)
python run_project.py

# 2. Run theoretical Monte Carlo simulation only
python run_project.py --simulation-only

# 3. Run all 33 automated tests
python -m unittest discover -s tests -v
```

---

## Methodology & Derivation

### 1. Mathematical Replication

The simulated underlying follows geometric Brownian motion under the physical measure $\mathbb{P}$:

$$
dS_t = \mu S_t\,dt + \sigma S_t\,dB_t.
$$

Let $V_i(S, t)$ denote the option value marked at implied volatility $\sigma_i$, satisfying the Black–Scholes PDE with $\sigma_i$. Holding one option, $-\Delta_h$ shares, and cash balance $C_t$, portfolio wealth is $W_t = V_i - \Delta_h S_t + C_t$ with $W_0 = 0$. Under self-financing rebalancing, Itô's lemma and the pricing PDE yield the excess wealth increment:

$$
dW_t - rW_t\,dt = \frac{1}{2}(\sigma^2 - \sigma_i^2)S_t^2\Gamma_i\,dt + (\Delta_i - \Delta_h)\big[(\mu - r)S_t\,dt + \sigma S_t\,dB_t\big].
$$

- **Known Actual-Volatility Hedge ($\Delta_h = \Delta_\sigma = \partial V_\sigma/\partial S$):**  
  Let $V_\sigma(S,t)$ be the theoretical Black–Scholes value under actual volatility $\sigma$. By continuous replication, a self-financing stock-cash holding reproducing expiry payoff $V_\sigma(S_T,T) = (S_T-K)^+ = V_i(S_T,T)$ costs $V_\sigma(S_0,0)$ at $t=0$. Because the market option was purchased at $V_i(S_0,0)$, terminal discounted wealth satisfies the exact path-independent identity:
  $$
  e^{-rT}W_T = V_\sigma(S_0,0) - V_i(S_0,0).
  $$
  Intermediate marked-to-market valuations fluctuate, but terminal replication profit is fixed.

- **Constant Implied-Volatility Hedge ($\Delta_h = \Delta_i$):**  
  The residual delta $(\Delta_i - \Delta_h)$ vanishes, eliminating the Brownian diffusion term $dB_t$:
  $$
  e^{-rT}W_T = \frac{1}{2}(\sigma^2 - \sigma_i^2)\int_0^T e^{-rt}S_t^2\Gamma_i(S_t,t)\,dt.
  $$
  Since $\Gamma_i > 0$ for a long vanilla option, the sign of instantaneous profit matches $\operatorname{sign}(\sigma^2 - \sigma_i^2)$, but its terminal magnitude depends heavily on the realized stock path.

### 2. Monte Carlo Setup

| Parameter | Value |
|---|---|
| Initial price ($S_0$) & Strike ($K$) | 100 |
| Maturity ($T$) | 1.0 year |
| Physical drift ($\mu$) | 10% |
| Risk-free rate ($r$) | 5% |
| Implied volatility ($\sigma_i$) | 20% |
| Actual-volatility scenarios ($\sigma$) | 15% and 30% |
| Simulation paths | 20,000 per scenario |
| Rebalancing steps | 252 steps/year |
| Convergence experiment | 6,000 paths evaluated across step frequencies |
| Random seed | 244 (exact shared paths across hedge rules) |

### 3. Historical Backtest Design

| Component | Rule |
|---|---|
| Underlying data | NSE NIFTY 50 monthly options & futures (8 Jul 2024 – 31 Dec 2025; 370 sessions) |
| Volatility forecast | EWMA with $\lambda = 0.94$, 60-day return warm-up, annualized with 252 sessions |
| Option pricing & IV | Black-76 evaluated against matched-expiry futures prices |
| Contract selection | Nearest ATM strike for the nearest monthly contract 14–65 days to expiry |
| Signal | Forecast volatility minus mean ATM call/put implied volatility |
| Direction | Long straddle above $+k$; short straddle below $-k$; flat otherwise |
| Execution timing | Previous-day close signal and delta; next-day opening-price execution |
| Trade holding period | 5 sessions, or exit 7 days before expiry / sample end |
| Transaction costs | 0.20% of option premium per side; 1 bp (0.01%) of traded futures notional |
| Assumed risk-free rate | Flat 6.5% per annum |

### 4. Calibration & Test Split
- **Calibration period:** 7 October 2024 – 30 June 2025 (selects threshold $k$).
- **Test period:** 1 July 2025 – 31 December 2025 (held strictly untouched during selection).
- **Selected threshold:** **$k = 0.03$ (3.0 volatility percentage points)**, chosen as the threshold with at least 10 calibration trades maximizing average net training P&L across both hedge rules.

---

## Numerical Results

### Simulation Replication
At 30% actual volatility vs. 20% implied volatility:
- **Theoretical actual-volatility hedge profit:** **3.7807**
- **Simulated actual-volatility hedge mean:** **3.7840** (Std. Dev: 0.6218, MC standard error ≈ 0.0044)
- **Simulated implied-volatility hedge mean:** **3.7404** (Std. Dev: 1.8547)
- **Convergence slope:** **−0.496** on log-log grid (matching theoretical $N^{-1/2} = -0.50$).

### Test Period Historical Performance ($k=3$, Selected Baseline)
Across 126 test sessions, only **3 trades** triggered (all short straddles in October–November 2025):

| Metric | Implied-Vol Delta | Forecast-Vol Delta |
|---|---:|---:|
| Completed trades | 3 (all short) | 3 (all short) |
| Net P&L (index points) | **159.22** | **165.80** |
| Gross P&L (index points) | 171.51 | 180.12 |
| Direct modeled costs | 12.28 | 14.31 |
| Max drawdown (index points) | 55.78 | 65.70 |
| Annualized Sharpe (excess P&L) | 1.63 | 1.54 |

The forecast hedge earns 6.58 points higher net P&L in aggregate (mean per-trade difference of 2.19 index points), but suffers larger maximum drawdown. With only 3 completed trades, an IID paired bootstrap was suppressed by design; this sample is too small to substantiate statistical significance.

### Cost Sensitivity
| Cost Multiplier | Implied Net P&L | Forecast Net P&L |
|---|---:|---:|
| 0× (frictionless) | 171.52 | 180.12 |
| 1× (base model) | 159.22 | 165.80 |
| 2× | 146.93 | 151.48 |
| 5× | 110.06 | 108.52 |

At 5× base costs, the ranking reverses, highlighting that higher turnover in forecast hedging erodes its gross advantage.

### Diagnostic Threshold Sensitivity Table
The table below displays out-of-sample test results across alternative threshold candidates $k \in \{0.00, 0.01, 0.02, 0.03\}$:

| Threshold $k$ | Rule | Trades | Net P&L | Costs | Max DD | Sharpe |
|---|---|---:|---:|---:|---:|---:|
| **0.00** | Implied | 21 | 46.09 | 91.88 | 303.99 | 0.16 |
| **0.00** | Forecast | 21 | 103.50 | 98.85 | 232.03 | 0.36 |
| **0.01** | Implied | 17 | 389.76 | 76.08 | 230.91 | 1.49 |
| **0.01** | Forecast | 17 | 413.33 | 82.54 | 201.58 | 1.59 |
| **0.02** | Implied | 7 | 46.36 | 32.07 | 195.98 | 0.29 |
| **0.02** | Forecast | 7 | 137.25 | 35.98 | 115.40 | 0.90 |
| **0.03 (Selected)** | Implied | 3 | 159.22 | 12.28 | 55.78 | 1.63 |
| **0.03 (Selected)** | Forecast | 3 | 165.80 | 14.31 | 65.70 | 1.54 |

> [!WARNING]
> **Diagnostic Guardrail:** Although $k = 0.01$ achieves substantially higher test-period net P&L (413.33 points), it was **not** selected because threshold selection was strictly locked to training data ($k=3$). Retuning thresholds based on test outcomes constitutes data snooping.

---

## Scope & Exploratory Modules

- **Primary Reported Pipeline:** Uses EWMA volatility estimation ($\lambda=0.94$), Black-76 delta hedging, and accounting ledger reconciliation.
- **GARCH(1,1) Estimation:** Implemented in `src/backtest.py` (`fit_garch11`) and fitted on training returns. It serves as an exploratory benchmark and is stored in `atm_panel.csv` but is **not** used in the primary trading signal.
- **Greek Attribution & Futures SDE:** Implemented in `src/robustness.py`. These modules explore higher-order Greek decomposition ($\Delta, \Gamma, \Theta, \text{Vega}$) and continuous futures Itô dynamics. They are standalone diagnostic tools verified by unit tests and are not part of the default baseline run.
- **Extensions Not Implemented:** India VIX trading, Heston stochastic volatility calibration, exchange margin modeling, and multi-year extensions (2019–2024).

---

## Raw Data Downloading & Rebuild Workflow

The project includes cleaned data in `data/clean/` and the provenance log `data/download_manifest.csv` containing SHA-256 hashes of all 370 trading sessions.

To re-download and verify raw archives from NSE:
1. Run `python download_data.py --start 2024-07-08 --end 2025-12-31 --workers 3`.  
   This downloads official UDiFF archives from `archives.nseindia.com` into `data/raw/` and logs HTTP responses in `data/download_manifest.csv`.
2. Run `python run_project.py --rebuild-data`.  
   This re-normalizes raw archives, verifies file dates against session timestamps, inverts Black-76 implied volatilities across all strikes, and regenerates `data/clean/`.

---

## Automated Test Suite

Run all **33 unit and audit tests**:
```bash
python -m unittest discover -s tests -v
```

Covered checks:
- **Pricing & Greeks:** Black-Scholes reference price, put-call parity, finite-difference futures delta, vectorised IV inversion, Black-76 PDE residual bounds.
- **Simulation Identities:** GBM exact transitions, cash financing, equal-volatility zero-profit identity, $N^{-1/2}$ error convergence, drift invariance across $\mu \in [-0.20, +0.30]$.
- **Pipeline & Execution:** Dual-schema normalisation (UDiFF & legacy), date validation, next-session execution timing, duplicate contract rejection, trade ledger reconciliation.
