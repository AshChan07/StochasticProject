Volatility Arbitrage and Delta Hedging on NIFTY Index Options

MAC F244 · Stochastic Calculus and Application to Finance · November 2026

Arnav, Rohan, Joel, Ashwath and Advay<br/>BITS Pilani, K K Birla Goa Campus · Instructor: Mayank Goel

1. Research question and scope

Which volatility should determine the delta hedge when market implied volatility differs from a volatility estimate? We reproduce the constant-volatility single-option results in Sections 3–4 of Ahmad and Wilmott [1], then compare implied-volatility and EWMA-forecast hedges on real NIFTY monthly straddles. The simulation tests a mathematical identity; the historical study evaluates an uncertain forecast under discrete execution.

2. Stochastic-calculus formulation

Under the physical measure P, dS = μS dt + σS dB, with constant actual volatility σ. The option is marked at V<sub>i</sub>(S,t), using constant implied volatility σ<sub>i</sub>. It satisfies the Black–Scholes PDE at σ<sub>i</sub> [2]. We hold one option, −Δ<sub>h</sub> shares and cash C. Wealth is W = V<sub>i</sub> − Δ<sub>h</sub>S + C, initially zero. Rebalancing is self-financing.

V<sub>t</sub> + rSV<sub>S</sub> + ½σ<sub>i</sub><super>2</super>S<super>2</super>V<sub>SS</sub> − rV = 0

Applying Itô’s formula and substituting C = W − V<sub>i</sub> + Δ<sub>h</sub>S gives the excess wealth increment:

dW − rW dt = ½(σ<super>2</super> − σ<sub>i</sub><super>2</super>)S<super>2</super>Γ<sub>i</sub> dt<br/>+ (Δ<sub>i</sub> − Δ<sub>h</sub>)[(μ − r)S dt + σS dB].

The known-actual-volatility hedge replicates the payoff: discounted terminal gain equals V(σ) - V(σ<sub>i</sub>). With implied delta, the explicit Brownian term cancels, but the gamma integral remains path-dependent. These are continuous-trading, constant-volatility, cost-free limits; pricing is under Q while realized gains are under P.

Futures hedge: a different financing equation

For matched futures, dF = aF dt + σ<sub>F</sub>F dB under P. Black-76 [4] satisfies V<sub>t</sub> + ½σ<sub>i</sub><super>2</super>F<super>2</super>V<sub>FF</sub> - rV = 0. Futures require no principal payment: W = V + C and dC = rC dt - Δ<sub>h</sub>dF. Therefore:

dW - rW dt = ½(σ<sub>F</sub><super>2</super> - σ<sub>i</sub><super>2</super>)F<super>2</super>Γ<sub>i</sub>dt + (Δ<sub>i</sub> - Δ<sub>h</sub>)dF.

Call futures delta is e<super>-rτ</super>N(d<sub>1</sub>), not stock delta. Deterministic carry gives F = Se<super>(r-q)(T-t)</super> and equal spot/futures diffusion volatility; actual basis changes make spot EWMA only a proxy. Stochastic implied volatility I adds Vega dI + ½Volga d[I] + Vanna d[F,I]. Delta hedging alone does not remove these risks.

A five-session exit also differs from hold-to-expiry replication. The forecast-minus-IV signal is a heuristic: P&amp;L depends on gamma-weighted variance, changing IV and risk premia, not an unweighted volatility gap. The full derivation and assumptions are in the viva guide.


--- PAGE BREAK ---


3. Numerical replication

We generate exact GBM transitions with S<sub>0</sub> = K = 100, T = 1 year, μ = 10%, r = 5% and implied volatility 20%. Each scenario uses 20,000 paths, 252 hedge intervals and seed 244. The two hedge rules share each path. Cash accrues interest, each stock rebalance debits cash, and expiry wealth includes the payoff and hedge liquidation. Results below are discounted index points per call.

Actual volatility | Hedge volatility | Mean P&L | P&L std. dev.

15% | actual | -1.858 | 0.294

15% | implied | -1.764 | 0.716

30% | actual | 3.784 | 0.622

30% | implied | 3.740 | 1.855

At 30% actual volatility, theoretical profit is 3.7807 and simulated actual-hedge mean is 3.7840 (Monte Carlo standard error 0.0044). At 15%, the theoretical value is −1.8589 and simulated mean is −1.8579. Implied-volatility hedging retains substantially more terminal dispersion.

Figure 1. Simulated discounted P&amp;L. Teal: actual-volatility hedge. Orange: implied-volatility hedge. All gains/losses are conditional on the simulated model.

Figure 2. Replication-error standard deviation, 6,000 paths per frequency. The fitted log–log slope is −0.496, close to the −0.5 reference.

A separate futures replication uses premium financing plus variation margin. At 1,008 rebalances its mean discounted actual-hedge gain is 3.76705 versus theory 3.76494 (standard error 0.00315). This checks the futures extension; finite simulated gains are not practical arbitrage guarantees.


--- PAGE BREAK ---


4. Historical experiment

NSE UDiFF bhavcopies [3] supply 370 sessions from 8 July 2024 to 31 December 2025, including the special 1 February 2025 budget session. The clean panel contains 222,520 monthly-option records and 1,110 futures records. The index close comes from the archive’s underlying-price field. Contract keys and file dates are validated; unavailable dates are audited separately.

Monthly options must match an observed futures expiry. Black-76 [4] on the matched futures close yields each leg’s implied volatility and futures delta. All strikes remain available for tracking held contracts. Invalid IV observations are excluded from entry selection; no artificial volatility fills are used. The flat 6.5% rate is an assumption, not a downloaded RBI yield.

EWMA variance uses 60 initial returns and λ = 0.94 [5], then updates using only available closes. Volatility is annualized with 252 sessions. At a decision close, choose the first monthly expiry 14–65 days away and the nearest strike with both legs traded and valid IV. Signal = forecast minus mean call/put IV.

Buy above +k, sell below −k. Execute at the next session’s recorded opens. Hold one straddle unit for five sessions, with earlier exit at seven calendar days to expiry. No overlapping positions or new entry on an exit day. Keep strike and expiry fixed. Futures quantities, including rebalances, use the preceding close and may be fractional. Opening quotes can be asynchronous, so execution is approximate.

Calibration runs 7 October 2024–30 June 2025. Among k = 0, 1, 2, 3 volatility points with at least ten training trades, the largest average net P&amp;L across both hedge rules selects <b>k = 3 points</b>. The original held-out test period is July–December 2025; added audit diagnostics reuse this already-inspected sample. Selection is on training P&amp;L rather than test performance.

Base costs are illustrative all-in proxies: 0.20% of option premium each way and 1 bp of traded futures notional. Cash financing and daily futures gains are explicit. These proxies do not reconstruct historical taxes, brokerage or margin. P&amp;L is per index unit; exchange lot and collateral constraints are not enforced.

Test result (126 sessions) | Implied hedge | Forecast hedge

Completed trades | 3 (all short) | 3 (all short)

Net P&L, index points | 159.22 | 165.80

Direct modeled costs | 12.28 | 14.31

Max. drawdown, index points | 55.78 | 65.70

Annualized daily P&L Sharpe | 1.63 | 1.54

Only three test trades trigger, all in October–November. Each is profitable, but this tiny sample cannot establish reliable profitability or hedge superiority. The forecast hedge earns 6.58 more points overall while showing a larger maximum drawdown. Sharpe annualizes daily incremental P&amp;L, including inactive days, and is unstable with so few trades.


--- PAGE BREAK ---


5. Results, sensitivity and limitations

Figure 3. Test-period cumulative net P&amp;L at the training-selected threshold. Long flat sections reflect no position, not missing marks.

Cost multiplier | Implied net P&L | Forecast net P&L

0x | 171.52 | 180.12

1x | 159.22 | 165.80

2x | 146.93 | 151.48

5x | 110.06 | 108.52

Higher costs reduce both outcomes and reverse the small hedge ranking at 5x costs. In the threshold diagnostic, k = 0 generates 21 test trades and net P&amp;L of 46.09 (implied) and 103.50 (forecast). We do not replace the selected threshold with a better-looking test alternative. Full threshold and hedge-frequency sensitivities accompany the code.

The simulation strongly supports the constant-volatility replication identity and the N<super>−1/2</super> error rate. The market comparison is exploratory: few trades, one test period, uncertain forecasts, changing IV, asynchronous opening prints, fractional sizing and omitted margin effects constrain inference. The three-trade bootstrap interval is suppressed. Next-close execution reverses the ranking: 97.44 points for implied delta versus 87.56 for forecast delta; the same next-open trades without futures earn 147.99 points. These retrospective controls show sensitivity, not independent confirmation.

<b>Conclusion.</b> Choosing the hedge volatility changes the risk profile. Known-volatility replication controls terminal risk in the ideal model. Forecast-volatility hedging in this NIFTY sample produces a slightly larger net gain, but the evidence does not support a general superiority or an implementable arbitrage claim. A stronger study requires longer independent samples, synchronized bid/ask quotes and historical contract-level costs.

<b>Implemented scope.</b> Joel’s dual-schema normalizer, parity diagnostics and independent IV solver are integrated. Added checks cover rolling calibration, rate assumptions, a rolling-60 forecast baseline and approximate Greek attribution with a residual. GARCH, VIX, Heston, fixed-vega sizing, long historical coverage and realistic margins remain extensions.

References and reproducibility

[1] Ahmad, R. &amp; Wilmott, P. (2005). Which Free Lunch Would You Like Today, Sir? Wilmott Magazine, November, 64–79. Sections 3–4.<br/>[2] Shreve, S. E. (2004). Stochastic Calculus for Finance II. Springer, Chapters 4–5.<br/>[3] NSE. F&amp;O-UDiFF Common Bhavcopy Final. <link href="https://www.nseindia.com/all-reports-derivatives" color="#126c75">nseindia.com/all-reports-derivatives</link>. Source URLs and SHA-256 hashes in data/download_manifest.csv.<br/>[4] Black, F. (1976). The Pricing of Commodity Contracts. Journal of Financial Economics 3, 167–179.<br/>[5] J.P. Morgan/Reuters (1996). RiskMetrics Technical Document, 4th ed.

Run: python run_project.py. Tests: python -m unittest discover -s tests -v. The regression suite covers both schemas, futures PDE/replication, invalid quotes, causality, convergence and ledger identities. Numerical CSVs, individual trades, full assumptions and download instructions are included.