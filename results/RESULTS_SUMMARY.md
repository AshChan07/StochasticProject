# Computed Results Summary

Data: 370 sessions, 222,520 monthly option rows, 1,110 futures rows (July 8, 2024 to December 31, 2025).
Calendar: 19 unavailable weekday files match published holidays; the budget Saturday (1 Feb 2025) is included.

---

## 1. Monte Carlo Simulation & Convergence
- **Scenario ($\sigma = 30\%, \sigma_i = 20\%$):**
  - Theoretical discounted profit: **3.7807 index points**.
  - Actual-volatility hedge: Sample mean **3.7840**, standard error **0.0044**, standard deviation **0.6218**, Skewness **+0.048**, Excess Kurtosis **+1.65**.
  - Implied-volatility hedge: Sample mean **3.7404**, standard error **0.0131**, standard deviation **1.8547**, Skewness **+0.495**, Excess Kurtosis **-0.300**.
  - Implied-volatility hedging terminal standard deviation is **3.0x larger** than actual-volatility hedging.
- **Convergence:** Regressing $\log_{10}(\sigma_{\text{error}})$ against $\log_{10}(N)$ across $N \in [12, 1008]$ yields a slope of **-0.4958**, confirming the continuous-limit $O(N^{-1/2})$ theoretical convergence.
- **Drift Sensitivity:** Tested across $\mu \in [-0.20, +0.30]$. Actual-volatility replication is invariant to drift ($3.79 \pm 0.01$), whereas implied-volatility accumulated profit drops from 3.79 to 3.27 under high drift due to lower gamma exposure.

---

## 2. Volatility Forecast Evaluation (EWMA vs. GARCH)
- **EWMA ($\lambda = 0.94$):**
  - Test set (121 targets): Volatility RMSE **0.0247** (annual decimal), QLIKE loss **0.1632**.
  - Train set (179 targets): Volatility RMSE **0.0642**, QLIKE loss **0.4206**.
- **GARCH(1,1) Maximum Likelihood:**
  - Parameters: $\omega = 1.97 \times 10^{-4}, \alpha = 0.0057, \beta = 0.4348$ ($\alpha + \beta = 0.4405 < 1$).
  - Test set (121 targets): Volatility RMSE **0.2194**, QLIKE loss **1.8198**.
- **Conclusion:** EWMA outperforms GARCH(1,1) by a factor of 8x in test-period RMSE and 11x in QLIKE loss, confirming its selection for signal generation.

---

## 3. Historical Backtest & Baseline Comparison
Calibrated threshold $k = 3\%$ on training set (Oct 2024–June 2025). Test period: July–December 2025 (126 sessions).

### 3.1 Active Strategy ($k=3\%$, Single Position)
- **Implied Delta:** Net P&L **+159.22 points**, Drawdown **55.78 points**, Costs **12.28 points**, Daily Sharpe **1.63** (3 trades).
- **Forecast Delta:** Net P&L **+165.80 points**, Drawdown **65.70 points**, Costs **14.31 points**, Daily Sharpe **1.54** (3 trades).
- **Cost Sensitivity:** At 5x costs, implied-vol delta (+110.06) surpasses forecast-vol delta (+108.52) due to lower futures turnover (53,579 vs 73,853).

### 3.2 Naive Short Straddle Benchmark (Variance Risk Premium Baseline)
- Net P&L: **+306.58 points** across 21 trades.
- Maximum Drawdown: **171.30 points** (3x larger than active strategy).
- Sharpe Ratio: **1.09** (Active strategy achieves **1.63**, a 50% improvement in risk-adjusted performance).

### 3.3 Inventory Capacity Sensitivity (Concurrent Positions)
- **Cap = 1:** 3 trades, Net P&L +159.22 (Implied) / +165.80 (Forecast).
- **Cap = 2:** 8 trades, Net P&L **+272.13** (Implied) / **+197.46** (Forecast), Hit Rate **87.5%**.
- **Cap = 3:** 11 trades, Net P&L **+387.77** (Implied) / **+298.74** (Forecast), Hit Rate **81.8%**.

---

## 4. Verification Suite
**17 automated unit tests** passed cleanly in 2.8s:
- Reference pricing, Black-76 put-call parity, finite-difference delta, IV round-trip, expiry boundary values.
- Zero-profit equal-volatility condition, replication error $N^{-1/2}$ convergence, discrete cash/variation margin compounding.
- Physical drift invariance of actual-volatility replication.
- Calendar coverage (including budget session), contract key uniqueness.
- GARCH(1,1) parameter stationarity and forecast positivity.
- Multi-position inventory scaling and exact daily-to-trade ledger reconciliation.
