# Volatility Arbitrage and Delta Hedging on NIFTY Index Options

A stochastic-calculus project implementing the central hedging comparison in **Ahmad & Wilmott (2005)** and applying two delta-hedging rules to historical NIFTY monthly options.

**Course:** MAC F244 — Stochastic Calculus and Application to Finance  
**Institution:** BITS Pilani, K K Birla Goa Campus  
**Instructor:** Mayank Goel  
**Team:** Arnav, Rohan, Joel, Ashwath and Advay  
**GitHub:** https://github.com/AshChan07/StochasticProject

---

## Overview

When an option's implied volatility differs from the volatility expected for its underlying, which volatility should determine the hedge?

This project investigates that question through:

1. A mathematical derivation using Itô's formula and the Black–Scholes pricing PDE.
2. Monte Carlo replication with known actual volatility.
3. A historical NIFTY straddle backtest comparing implied-volatility delta with EWMA-forecast-volatility delta.
4. Transaction-cost, threshold and rebalancing-frequency sensitivity analysis.

> **Note:** The calibrated strategy produces only three test-period trades, so the historical results are exploratory, not evidence of reliable arbitrage or hedge superiority.

---

## Directory Structure

```text
MAC_F244_Volatility_Arbitrage/
├── README.md                              # This file
├── requirements.txt                       # Python dependencies
├── run_project.py                         # Entry point: runs simulations and backtest
│
├── src/
│   ├── __init__.py
│   ├── pricing.py                         # Black–Scholes, Black-76, delta, vega and IV solver
│   ├── simulation.py                      # GBM paths, self-financing hedge, tail risk
│   ├── backtest.py                        # EWMA forecast, trading rules, ledger and analysis
│   ├── robustness.py                      # Walk-forward, rate sensitivity, Greek attribution
│   └── data.py                            # Archive normalisation and ATM option selection
│
├── data_pipeline/
│   ├── __init__.py
│   ├── bhavcopy.py                        # Dual-schema NSE UDiFF bhavcopy parser
│   ├── config.py                          # Schema and column configuration
│   ├── forwards.py                        # Parity-based forward/futures price builder
│   └── iv.py                              # Black-76 implied volatility utilities
│
├── tests/
│   ├── pipeline_fixtures.py               # Synthetic bhavcopy fixtures for audit tests
│   ├── test_project.py                    # 17 core unit tests
│   └── test_audit.py                      # 16 pipeline and audit tests
│
└── data/
    └── clean/
        ├── nifty_daily.csv                # NIFTY underlying closes (370 sessions)
        ├── nifty_futures.csv              # Futures prices and contract identifiers
        └── nifty_options_chain.csv.gz     # Monthly options, prices and IVs (222,520 records)
```

---

## Quick Start

**Requirements:** Python 3.11 or newer (results generated with Python 3.12). No API key or paid dataset required.

### Setup

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Windows (PowerShell)
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run

```bash
# Full pipeline: Monte Carlo simulation + historical backtest
python run_project.py

# Simulation only
python run_project.py --simulation-only

# Run all 33 tests
python -m unittest discover -s tests -v
```

---

## Data and Provenance

Historical sample: **8 July 2024 through 31 December 2025**

- 370 trading sessions (including the special Saturday budget session, 1 February 2025)
- 222,520 monthly-option records; 1,110 futures records
- Source: NSE **F&O-UDiFF Common Bhavcopy Final** archives
- Monthly expiries identified by matching actual futures expiries
- Invalid implied volatilities are not replaced with invented values

The cleaned dataset is included in `data/clean/`. To re-download and rebuild from the original NSE archives, see the full instructions at the [GitHub repository](https://github.com/AshChan07/StochasticProject).

> **Format note:** This implementation supports the post-July-2024 UDiFF schema. Extending into earlier years requires a legacy parser and calendar review.

---

## Methodology

### 1. Mathematical Replication

The simulated underlying follows geometric Brownian motion under the physical measure:

$$
dS_t = \mu S_t\,dt + \sigma S_t\,dB_t.
$$

Let $V_i$ denote the option value at implied volatility $\sigma_i$, and let $\Delta_h$ be the hedge delta. Holding one option, $-\Delta_h$ shares and cash $C$ gives wealth $W = V_i - \Delta_h S + C$. With self-financing rebalancing, Itô's formula and the pricing PDE give:

$$
dW - rW\,dt = \frac{1}{2}(\sigma^2 - \sigma_i^2)S^2\Gamma_i\,dt
+ (\Delta_i - \Delta_h)\big[(\mu - r)S\,dt + \sigma S\,dB\big].
$$

- **Known actual-volatility hedge:** Discounted terminal profit equals the difference between actual- and implied-volatility option values (path-independent under continuous trading).
- **Implied-volatility hedge:** The Brownian term cancels, but accumulated gamma gains remain path-dependent.

The simulation uses exact GBM transitions, a stock hedge and an explicit interest-bearing cash account. The historical study uses futures and uncertain forecasts — it does not inherit the theoretical guarantee.

### 2. Monte Carlo Setup

| Parameter | Value |
|---|---|
| Initial price and strike | 100 |
| Maturity | One year |
| Physical drift | 10% |
| Risk-free rate | 5% |
| Implied volatility | 20% |
| Actual-volatility scenarios | 15% and 30% |
| Paths per scenario | 20,000 |
| Rebalances per year | 252 |
| Random seed | 244 |
| Convergence experiment | 6,000 paths at each frequency |

### 3. Historical Trading Design

| Component | Rule |
|---|---|
| Volatility estimate | EWMA, λ = 0.94, initialised with 60 squared log-returns |
| Annualisation | 252 trading sessions |
| Option pricing and IV | Black-76 using matched-expiry futures |
| Entry candidate | First monthly expiry 14–65 calendar days away; nearest eligible strike to futures close |
| Signal | Forecast volatility minus mean call/put implied volatility |
| Direction | Long above +k; short below −k; otherwise no trade |
| Decision and execution | Previous-close signal and delta; next-session recorded opening prices |
| Holding period | Five observed sessions; earlier exit at seven days to expiry or sample end |
| Assumed interest rate | Flat 6.5% annually |
| Base option cost | 0.20% of premium per entry/exit side |
| Base futures cost | One basis point of traded notional |
| Cost sensitivity | 0×, 1×, 2× and 5× base assumptions |

### 4. Calibration and Test Split

- **Calibration:** 7 October 2024 – 30 June 2025
- **Test:** 1 July – 31 December 2025
- **Selected threshold:** 3 volatility percentage points (`0.03`) — chosen as the threshold maximising average calibration net P&L across both hedge rules, with at least ten calibration trades.

---

## Results

### Simulation

For 30% actual volatility and 20% implied volatility:

| Quantity | Actual-volatility hedge | Implied-volatility hedge |
|---|---:|---:|
| Mean discounted P&L | 3.7840 | 3.7404 |
| Standard deviation | 0.6218 | 1.8547 |

Theoretical actual-hedge profit: **3.7807**. Simulated mean: **3.7840** (MC standard error ≈ 0.0044). Convergence log–log slope: **−0.496** (theoretical reference: −0.5).

### Historical Test

Three trades, all short straddles, across 126 test sessions:

| Metric | Implied-vol delta | Forecast-vol delta |
|---|---:|---:|
| Net P&L, index points | 159.22 | 165.80 |
| Maximum drawdown, index points | 55.78 | 65.70 |
| Direct modelled costs, index points | 12.28 | 14.31 |
| Annualised daily P&L Sharpe | 1.63 | 1.54 |

The forecast hedge has slightly higher net P&L but also higher drawdown. Three trades cannot establish a dependable performance advantage. Increasing costs to five times the base assumptions reverses the small P&L ranking.

---

## Units and Interpretation

- Volatilities are annualised decimals: `0.20` = 20%.
- Threshold `0.01` means **one volatility percentage point**.
- Option, futures and P&L figures are in **index points per one straddle unit**, not rupees per exchange lot.
- Option maturity and financing use calendar days divided by 365.
- A fixed reporting capital of 100,000 is used as an illustrative return denominator only.
- Sharpe uses annualised daily incremental P&L including inactive days; interpretation is limited by the short sample and few trades.

---

## Tests

33 automated tests covering:

- Black–Scholes price, put-call parity, Black-76 PDE residuals
- Futures delta (finite differences), IV inversion, invalid-price rejection
- GBM replication error and convergence
- GARCH(1,1) estimation, EWMA drift invariance
- Multi-position capacity, trade ledger reconciliation
- Cost sensitivity, lagged entry signals
- Pipeline schema boundaries, parity recovery, Greek attribution

---

## Limitations

- Daily opening prices are not synchronised bid/ask quotes.
- Costs are illustrative proxies, not exact historical brokerage/STT/exchange fees.
- Exchange lot sizes, margin constraints and position limits are not enforced.
- The forecast is uncertain; positions close before expiry. These differ from the paper's constant-volatility, continuous-trading benchmark.

---

## References

1. Ahmad, R. and Wilmott, P. (2005). *Which Free Lunch Would You Like Today, Sir?: Delta Hedging, Volatility Arbitrage and Optimal Portfolios.* Wilmott Magazine, November, pp. 64–79.
2. Black, F. (1976). *The Pricing of Commodity Contracts.* Journal of Financial Economics, 3, pp. 167–179.
3. Shreve, S. E. (2004). *Stochastic Calculus for Finance II: Continuous-Time Models.* Springer, Chapters 4–5.
4. J.P. Morgan/Reuters (1996). *RiskMetrics Technical Document*, 4th edition.
5. National Stock Exchange of India. *F&O-UDiFF Common Bhavcopy Final*. [nseindia.com/all-reports-derivatives](https://www.nseindia.com/all-reports-derivatives).
