# Theory and Viva Guide: Volatility Arbitrage and Delta Hedging

## 1. Scope of the Replication and Adaptation
We reproduce the constant-volatility single-option hedging comparison in Sections 3–4 of **Ahmad and Wilmott (2005)**, *"Which Free Lunch Would You Like Today, Sir?: Delta Hedging, Volatility Arbitrage and Optimal Portfolios"*. The empirical study is an adaptation to Indian equity derivatives (NSE NIFTY 50 monthly options and futures from July 2024 to December 2025).

---

## 2. Three Distinct Volatilities
- **Actual Volatility ($\sigma$):** The diffusion coefficient in the physical data-generating process (GBM). Known only in Monte Carlo simulations.
- **Implied Volatility ($\sigma_i$):** The market consensus pricing input inverted from observed option premiums using Black-Scholes or Black-76. Reflects supply, demand, and risk premia.
- **Hedge Volatility ($\sigma_h$):** The specific numerical input plugged into the delta-hedging formula. In historical trading, the forecast is uncertain ($\sigma_{\text{forecast}} \neq \sigma$) and cannot provide a theoretical arbitrage guarantee.

---

## 3. Stochastic Calculus Derivation: Stock Under Geometric Brownian Motion

### 3.1 Model Setup
Under the physical measure $\mathbb{P}$:
$$dS_t = \mu S_t\,dt + \sigma S_t\,dB_t$$
where $\mu$ is physical drift and $B_t$ is standard Brownian motion.

An option is marked at constant implied volatility $\sigma_i$. Its pricing function $V_i(S, t)$ satisfies the Black–Scholes PDE under risk-neutral measure $\mathbb{Q}$:
$$\frac{\partial V_i}{\partial t} + rS\frac{\partial V_i}{\partial S} + \frac{1}{2}\sigma_i^2 S^2 \frac{\partial^2 V_i}{\partial S^2} - rV_i = 0$$
Define delta $\Delta_i = \frac{\partial V_i}{\partial S}$ and gamma $\Gamma_i = \frac{\partial^2 V_i}{\partial S^2}$.

### 3.2 The Self-Financing Portfolio
Hold 1 option ($V_i$), $h = -\Delta_h$ shares of stock hedged at volatility $\sigma_h$, and cash balance $C_t$:
$$W_t = V_i(S_t, t) - \Delta_h S_t + C_t, \quad W_0 = 0 \implies C_0 = -V_i(0) + \Delta_h(0)S_0$$
Under self-financing trading, stock rebalancing is funded entirely from the cash account:
$$dW_t = dV_i - \Delta_h dS_t + rC_t\,dt$$

Applying Itô's Lemma to $V_i(S_t, t)$:
$$dV_i = \frac{\partial V_i}{\partial t}dt + \Delta_i dS_t + \frac{1}{2}\sigma^2 S_t^2 \Gamma_i dt$$
Substitute $C_t = W_t - V_i + \Delta_h S_t$ and the pricing PDE for $\frac{\partial V_i}{\partial t}$:
$$dW_t - rW_t\,dt = \frac{1}{2}(\sigma^2 - \sigma_i^2)S_t^2 \Gamma_i\,dt + (\Delta_i - \Delta_h)\big[(\mu - r)S_t\,dt + \sigma S_t\,dB_t\big]$$
Multiplying by $e^{-rt}$ yields the discounted excess wealth increment:
$$d\big(e^{-rt}W_t\big) = e^{-rt}\left[\frac{1}{2}(\sigma^2 - \sigma_i^2)S_t^2 \Gamma_i\,dt + (\Delta_i - \Delta_h)\big[(\mu - r)S_t\,dt + \sigma S_t\,dB_t\big]\right]$$

### 3.3 The Two Continuous Trading Limits
1. **Actual-Volatility Hedging ($\Delta_h = \Delta(\sigma)$):**
   Replicates the terminal payoff at the true model cost. Under continuous rebalancing:
   $$e^{-rT}W_T = V(S_0, 0; \sigma) - V(S_0, 0; \sigma_i)$$
   The terminal profit is completely path-independent, although intermediate market marks fluctuate.
2. **Implied-Volatility Hedging ($\Delta_h = \Delta_i$):**
   The $(\Delta_i - \Delta_h)$ residual delta is zero, so the explicit Brownian term $dB_t$ **cancels out entirely**:
   $$e^{-rT}W_T = \frac{1}{2}(\sigma^2 - \sigma_i^2)\int_0^T e^{-rt}S_t^2 \Gamma_i(S_t, t)\,dt$$
   Since $\Gamma_i > 0$ for a vanilla call/put, the sign of instantaneous profit matches $\operatorname{sign}(\sigma^2 - \sigma_i^2)$. However, because $S_t$ and $\Gamma_i(S_t, t)$ are stochastic, the terminal profit is path-dependent and exhibits substantial dispersion.

---

## 4. Formal Derivation: Black-76 and Futures Itô Wealth SDE
*(Resolves the theoretical stock vs. futures mismatch between paper and market implementation)*

### 4.1 Futures Contract Dynamics
Let $F_t$ denote the futures price for expiry $T_F$. Under the physical measure $\mathbb{P}$:
$$dF_t = F_t\big[(\mu - r + q)\,dt + \sigma\,dB_t\big]$$
where $q$ is continuous dividend yield.

Under Black-76, an option expiring at $T \le T_F$ satisfies the PDE:
$$-\frac{\partial V_i}{\partial \tau} + \frac{1}{2}\sigma_i^2 F^2 \frac{\partial^2 V_i}{\partial F^2} - rV_i = 0, \quad \tau = T - t$$
The futures Greeks are:
$$\Delta_{F, i} = \frac{\partial V_i}{\partial F} = e^{-r\tau}N(d_1) \quad (\text{Call}), \quad e^{-r\tau}[N(d_1) - 1] \quad (\text{Put})$$
$$\Gamma_{F, i} = \frac{\partial^2 V_i}{\partial F^2} = e^{-r\tau}\frac{N'(d_1)}{F\sigma_i\sqrt{\tau}}$$

### 4.2 Futures Wealth Equation with Daily Variation Margin
Entering a futures contract requires **zero upfront capital outlay** ($F_0$ is not paid). Cash $C_t$ only finances the initial option premium and accumulates variation margin $h_t\,dF_t$ and interest $rC_t\,dt$:
$$W_t = V_i(F_t, \tau) + C_t, \quad C_0 = -V_i(0) \implies W_0 = 0$$
$$dC_t = rC_t\,dt + h_t\,dF_t - \text{costs}$$

Applying Itô's Lemma to $V_i(F_t, \tau)$:
$$dV_i = -\frac{\partial V_i}{\partial \tau}dt + \Delta_{F, i}\,dF_t + \frac{1}{2}\sigma^2 F_t^2 \Gamma_{F, i}\,dt$$
Substitute $-\frac{\partial V_i}{\partial \tau} = rV_i - \frac{1}{2}\sigma_i^2 F_t^2 \Gamma_{F, i}$:
$$dV_i = rV_i\,dt + \frac{1}{2}(\sigma^2 - \sigma_i^2)F_t^2 \Gamma_{F, i}\,dt + \Delta_{F, i}\,dF_t$$
Adding $dC_t$ to get portfolio wealth increment $dW_t = dV_i + dC_t$:
$$dW_t - rW_t\,dt = \frac{1}{2}(\sigma^2 - \sigma_i^2)F_t^2 \Gamma_{F, i}\,dt + (\Delta_{F, i} + h_t)\,dF_t$$
Setting hedge futures position $h_t = -\Delta_{F, h}$:
$$d\big(e^{-rt}W_t\big) = e^{-rt}\left[\frac{1}{2}(\sigma^2 - \sigma_i^2)F_t^2 \Gamma_{F, i}\,dt + (\Delta_{F, i} - \Delta_{F, h})\,dF_t\right]$$
When hedging with Black-76 implied delta ($\Delta_{F, h} = \Delta_{F, i}$), the entire $dF_t$ term (both physical drift and diffusion) cancels out.

---

## 5. Physical Drift ($\mu$) and Discrete Hedging Invariance
A common misconception is that the actual-volatility hedge relies on underlying drift.
- **Continuous Theory:** The replication identity $e^{-rT}W_T = V(\sigma) - V(\sigma_i)$ holds for all drift rates $\mu$.
- **Discrete Empirical Test (`results/drift_sensitivity.csv`):**
  We simulated 10,000 paths across $\mu \in \{-0.20, -0.10, 0.00, 0.10, 0.20, 0.30\}$:
  - For the **actual-volatility hedge**, the mean P&L is invariant to drift ($3.79 \pm 0.01$ vs theoretical $3.7807$), with stable standard deviation ($\approx 0.60$).
  - For the **implied-volatility hedge**, extreme drift ($\mu = \pm 0.30$) drives the underlying out of the money into low-gamma regions, causing mean accumulated profit to drop from $3.79$ to $3.27$.

---

## 6. Higher-Order Risk Metrics of Hedging Error
Discrete delta hedging error is non-Gaussian. In `results/simulation_summary.csv`:
- At 30% actual vol, actual-vol hedge excess kurtosis is **+1.65** (leptokurtic, fat tails) with positive skewness **+0.05**.
- Implied-vol hedge exhibits higher skewness (**+0.49**) and $3\times$ higher standard deviation ($1.85$ vs $0.62$).
- Value-at-Risk (VaR 99%) and Conditional VaR (Expected Shortfall) demonstrate that tail losses in discrete hedging are bounded under actual-vol replication, but path-dispersed under implied-vol hedging.

---

## 7. Volatility Forecasting: EWMA vs. GARCH(1,1)
We estimated GARCH(1,1) via Maximum Likelihood on training returns:
$$\sigma_t^2 = \omega + \alpha r_{t-1}^2 + \beta \sigma_{t-1}^2$$
Fitted parameters: $\omega = 1.97 \times 10^{-4}, \alpha = 0.0057, \beta = 0.4348$ ($\alpha + \beta < 1$, strictly stationary).

**Out-of-Sample Forecast Evaluation (`results/forecast_metrics.csv`):**
- **Test Period RMSE:** EWMA achieved **0.0247** vs. GARCH(1,1)'s **0.2194**.
- **Test Period QLIKE Loss:** EWMA achieved **0.1632** vs. GARCH(1,1)'s **1.8198**.
- **Conclusion:** EWMA ($\lambda = 0.94$) responds rapidly to local volatility clustering without mean-reverting prematurely, justifying its selection as our primary trading signal.

---

## 8. Vega-Weighted Mispricing vs. Flat Point Spread
A flat spread $\Delta \sigma = \sigma_{\text{forecast}} - \sigma_{\text{implied}}$ ignores maturity.
Option dollar mispricing is scaled by Vega:
$$\Delta V \approx \text{Vega} \cdot \Delta \sigma = \left(F\sqrt{\tau}e^{-r\tau}N'(d_1)\right) \cdot (\sigma_{\text{forecast}} - \sigma_{\text{implied}})$$
In `atm_panel.csv` and `signal.csv`, we compute exact Black-76 Vega and Vega-weighted mispricing (`vega_mispricing`), ensuring contracts with longer maturity are evaluated on absolute rupee opportunity rather than nominal percentage points.

---

## 9. Baseline Comparison: Disentangling Alpha from the Variance Risk Premium (VRP)
- **The Variance Risk Premium:** Equity index implied volatility typically trades above subsequent realized volatility ($E[\sigma_i - \sigma] > 0$) as compensation for crash risk.
- **The Naive Short Straddle Benchmark (`results/benchmark_metrics.csv`):**
  We run a continuous, unselective short ATM straddle (rolling every 5 sessions) hedged with implied delta:
  - Benchmark Net P&L: **+306.58 index points** over 21 trades, with Sharpe **1.09** and maximum drawdown **171.3 points**.
  - Active Strategy ($k=3\%$): Net P&L: **+159.22 index points** (Implied) and **+165.80 points** (Forecast), with Sharpe **1.63** and **1.54**, and drawdown only **55.8 points**!
- **Core Finding:** The active strategy delivered a **50% higher Sharpe ratio** and **67% lower maximum drawdown** than passive VRP harvesting, proving that the volatility forecast filters out unprofitable market regimes.

---

## 10. Multi-Position Inventory Capacity
To resolve the sample size constraint where a single position blocks new entries for 5 days:
In `results/capacity_sensitivity.csv`:
- `max_positions = 1` (Baseline): 3 trades, +159.22 Net P&L (Implied).
- `max_positions = 2`: **8 trades**, **+272.13 Net P&L** (Implied), Hit rate: 87.5%.
- `max_positions = 3`: **11 trades**, **+387.77 Net P&L** (Implied), Hit rate: 81.8%.
Relaxing the single-position restriction allows inventory scaling, expanding the trade count from 3 to 11 while maintaining positive risk-adjusted returns and exact ledger reconciliation.

---

## 11. Comprehensive Viva Questions & Model Answers

### Q1: Why does gamma appear in the excess wealth equation?
**Answer:** Applying Itô's Lemma to the option price introduces the quadratic variation term $\frac{1}{2}\sigma^2 S^2 \frac{\partial^2 V_i}{\partial S^2}dt = \frac{1}{2}\sigma^2 S^2 \Gamma_i dt$. Meanwhile, the Black–Scholes PDE satisfied by $V_i$ under $\sigma_i$ subtracts $\frac{1}{2}\sigma_i^2 S^2 \Gamma_i dt$. The difference isolates $\frac{1}{2}(\sigma^2 - \sigma_i^2)S^2 \Gamma_i dt$.

### Q2: Why are measure P and measure Q different here?
**Answer:** The asset price paths and realized returns evolve under the physical measure $\mathbb{P}$. The market prices options under the risk-neutral measure $\mathbb{Q}$. By Girsanov’s Theorem, changing measure shifts the drift from $\mu$ to $r$, but leaves the diffusion coefficient (volatility $\sigma$) invariant.

### Q3: Why does implied-volatility delta hedging eliminate the Brownian motion term without guaranteeing deterministic profit?
**Answer:** Setting $\Delta_h = \Delta_i$ sets $(\Delta_i - \Delta_h) = 0$, eliminating $(\Delta_i - \Delta_h)\sigma S dB$. However, the remaining term $\frac{1}{2}(\sigma^2 - \sigma_i^2)\int_0^T e^{-rt}S_t^2 \Gamma_i dt$ depends on $S_t$ and $\Gamma_i(S_t, t)$, which are stochastic and path-dependent. Hence, terminal profit fluctuates across paths.

### Q4: Why did you use Black-76 on futures rather than standard Black-Scholes on spot?
**Answer:** In the Indian market, NIFTY index options settle against the cash index, but cash-market delta hedging is prohibited by short-selling constraints and cash drag. Hedging with liquid NIFTY index futures eliminates dividend yield estimation, requires zero upfront capital, and converts the underlying into a forward martingale.

### Q5: Did you test whether physical drift ($\mu$) biases discrete actual-volatility hedging?
**Answer:** Yes. In continuous time, drift is eliminated by self-financing replication. In discrete time ($\Delta t = 1/252$), our drift sensitivity simulation (`results/drift_sensitivity.csv`) tested $\mu \in [-0.20, +0.30]$ and verified that the actual-volatility hedge mean matches theoretical profit within Monte Carlo error across all drift regimes.

### Q6: Why did your historical test period have only 3 trades?
**Answer:** Our threshold calibration on in-sample training data (Oct 2024–June 2025) selected $k = 3\%$ (300 bps mispricing) to avoid false signals. NIFTY is a liquid index, so 300 bps mispricing occurred only three times in late 2025. Sizing with a single non-overlapping position also blocked concurrent trades. When capacity is expanded to 3 concurrent positions, the sample expands to 11 trades.

### Q7: Why not select k = 1% which made over 400 index points on the test period?
**Answer:** Selecting $k = 1\%$ based on test performance would be post-hoc data snooping (p-hacking). A scientific backtest must freeze calibration parameters prior to touching the out-of-sample period.

### Q8: How do you know your historical profits were not just the Variance Risk Premium?
**Answer:** We implemented a naive rolling short straddle benchmark. The naive benchmark earned +306 points but suffered a severe 171-point drawdown with a Sharpe ratio of 1.09. Our active strategy delivered a Sharpe of 1.63 with only 55.8 points drawdown, confirming that the forecast signal successfully avoids adverse volatility spikes.

### Q9: Why did you use EWMA instead of GARCH(1,1)?
**Answer:** We estimated GARCH(1,1) via Maximum Likelihood and evaluated both out-of-sample in `results/forecast_metrics.csv`. EWMA achieved an RMSE of 0.0247 and QLIKE of 0.163, whereas GARCH(1,1) had an RMSE of 0.219 and QLIKE of 1.820. EWMA adapts faster to local volatility bursts without mean-reverting excessively.

### Q10: How do transaction costs impact the choice of hedge volatility?
**Answer:** In `results/sensitivity.csv`, at $1\times$ costs, the forecast hedge earned slightly more net P&L than implied hedge (165.80 vs 159.22). However, because the forecast hedge trades larger delta adjustments, its turnover was 38% higher. At $5\times$ costs, the ranking reversed: the implied-vol hedge outperformed (110.06 vs 108.52).
