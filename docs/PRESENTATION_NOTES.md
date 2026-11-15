## Slide 1

Timing: 38 seconds. Introduce the project and paper. Our empirical application uses real NIFTY data but differs from the idealized replication. The report states the reduced scope transparently. Ahmad & Wilmott (2005), Wilmott Magazine, November, pp.64–79, Sections 3–4. https://citeseerx.ist.psu.edu/document?doi=22554822cff90a56962f8ce4327587e86a42f1dc&repid=rep1&type=pdf

## Slide 2

Timing: 51 seconds. Distinguish three quantities. Implied volatility is a pricing input inferred from premiums. Actual volatility is known only in our synthetic data. Forecast volatility is uncertain. We ask how changing the delta input changes gains and dispersion. Ahmad & Wilmott (2005), Wilmott Magazine, November, pp.64–79, Sections 3–4. https://citeseerx.ist.psu.edu/document?doi=22554822cff90a56962f8ce4327587e86a42f1dc&repid=rep1&type=pdf

## Slide 3

Timing: 85 seconds. The original stock replication is retained in the report. Here F is the traded matched-expiry futures price. Futures have no financed principal: W=V+C and dC=rC dt−delta_h dF. Use the Black-76 PDE V_t+0.5 sigma_i² F² V_FF−rV=0. The residual drift is aF, not (a−r)F. Call delta is exp(−r tau)N(d1). Deterministic carry links spot and futures volatility; real basis variation is a limitation. Source: Shreve, Stochastic Calculus for Finance II, Chapters 4–5; Ahmad & Wilmott (2005), Wilmott Magazine, November, pp.64–79, Sections 3–4. https://citeseerx.ist.psu.edu/document?doi=22554822cff90a56962f8ce4327587e86a42f1dc&repid=rep1&type=pdf

## Slide 4

Timing: 77 seconds. Actual-volatility hedging replicates the terminal payoff at its correct model cost. Implied-volatility hedging removes the explicit Brownian term in market-marked gains, but gamma varies with the price path. Both statements assume constant volatilities and no costs. Our historical straddles close before expiry and use forecasts. If IV I changes, Ito adds Vega dI + half Volga d[I] + Vanna d[F,I]. The signal is a heuristic; gains depend on gamma-weighted variance and risk premia. Ahmad & Wilmott (2005), Wilmott Magazine, November, pp.64–79, Sections 3–4. https://citeseerx.ist.psu.edu/document?doi=22554822cff90a56962f8ce4327587e86a42f1dc&repid=rep1&type=pdf

## Slide 5

Timing: 55 seconds. Describe exact GBM transitions rather than Euler discretization. Both hedge rules use the same paths, reducing comparison noise. We finance stock trades explicitly and discount terminal wealth. There are two actual-volatility scenarios, one below and one above implied. Results are from src/simulation.py and results/simulation_summary.csv.

## Slide 6

Timing: 77 seconds. At actual volatility 30%, the actual hedge mean is 3.784 with standard error .0044, close to the theoretical 3.7807. The implied hedge mean is 3.740 with a much larger standard deviation. The density chart is computed from 20,000 simulated discounted P&Ls, not market returns. An all-positive sample does not prove a practical guarantee. Ahmad & Wilmott (2005), Wilmott Magazine, November, pp.64–79, Sections 3–4. https://citeseerx.ist.psu.edu/document?doi=22554822cff90a56962f8ce4327587e86a42f1dc&repid=rep1&type=pdf Data: results/histogram.csv and simulation_summary.csv.

## Slide 7

Timing: 60 seconds. Explain the log-log plot: a slope of minus one half means quadrupling the number of trades roughly halves the standard deviation. We use 6,000 paths at each frequency. This stock convergence applies to the known actual-volatility hedge; implied-volatility terminal dispersion does not vanish in the same way. The additional futures experiment uses F0=K=100, maturity one year, physical futures drift 5%, rate 5%, actual vol 30%, implied 20%, 10,000 paths and seed 244; at 1,008 rebalances mean is 3.76705 versus target 3.76494 with standard error 0.00315. The stock and futures theoretical targets differ because their starting prices/carry conventions differ. Data: results/convergence.csv.

## Slide 8

Timing: 60 seconds. Show provenance and changes from the proposal. The code uses the official archive underlying field, so separate Yahoo or VIX data is unnecessary. Monthly expiries match actual futures contracts. All option strikes are retained so held contracts do not disappear from the tracking panel. Dates and duplicates are checked. Joel’s parser and independent IV solver are integrated. Legacy schema support does not mean a longer empirical sample was downloaded. All strikes remain; monthly expiries match futures on the same day. Option parity is a diagnostic, not a replacement hedge instrument. NSE F&O UDiFF archives: https://www.nseindia.com/all-reports-derivatives . Raw URLs and hashes: data/download_manifest.csv. Calculations: results/*.csv.

## Slide 9

Timing: 81 seconds. At the preceding close use EWMA lambda .94 and 60-return warm-up, find the nearest strike of the first monthly expiry 14–65 days away, and select direction. Trade at next-session opens. Subsequent deltas are also lagged. The same strike and expiry persist through the trade. One signed straddle unit, at most one open position, five-session holding period, early exit at seven days to expiry. Source: src/backtest.py. NSE F&O UDiFF archives: https://www.nseindia.com/all-reports-derivatives . Raw URLs and hashes: data/download_manifest.csv. Calculations: results/*.csv.

## Slide 10

Timing: 68 seconds. The threshold candidates are 0, 1, 2 and 3 volatility points. Choose the highest average training P&L across the two hedge rules subject to ten trades. Three points wins with ten training trades. It was not selected on the test period. This selection itself can overfit, so the later results remain exploratory. Data: results/threshold_calibration.csv.

## Slide 11

Timing: 77 seconds. July–December contains 126 sessions, but only three trades trigger at the chosen threshold. They are short straddles in October–November. The forecast hedge gains 6.58 points more in aggregate. This is far too little evidence for superiority. Flat periods are zero positions, not missing data. Data: results/backtest_daily_*.csv. NSE F&O UDiFF archives: https://www.nseindia.com/all-reports-derivatives . Raw URLs and hashes: data/download_manifest.csv. Calculations: results/*.csv.

## Slide 12

Timing: 60 seconds. Discuss both gain and drawdown. The forecast hedge has higher next-open net gain but also larger drawdown and lower annualized daily P&L Sharpe. Next-close fills using the same lagged decisions reverse the ranking: implied 97.44 versus forecast 87.56 points. This changes exposure as well as prices; it is a sensitivity test, not measured slippage. Unhedged next-open trades earn 147.99 points. Every trade wins in this tiny sample, which should not be advertised as a reliable hit rate. A 100,000 reporting-capital denominator is illustrative and actual exchange margins are unmodeled. Data: results/test_metrics.csv.

## Slide 13

Timing: 60 seconds. Costs are all-in proxies: .20% of option premium each side and one basis point of futures notional. They are not a statutory tax model. At five times costs, the implied hedge slightly outperforms the forecast hedge. Delta turnover differs between methods. Data: results/sensitivity.csv.

## Slide 14

Timing: 60 seconds. Zero-threshold diagnostic generates 21 trades, with modest net gains. A one-point threshold looks better on test data, but selecting it now would be test-set tuning. We retain three points as the calibrated choice and show all candidates. Results describe one sample. Data: results/test_threshold_sensitivity.csv.

## Slide 15

Timing: 68 seconds. Strongest result is the mathematical replication. The market adaptation demonstrates reproducible empirical methodology, not a trading recommendation. Three trades, a short test interval, forecast uncertainty and execution approximations prevent broad performance claims. Future work should prioritize synchronized quotes, historical fees, lots/margin, and longer independent test periods before adding model complexity. Ahmad & Wilmott (2005), Wilmott Magazine, November, pp.64–79, Sections 3–4. https://citeseerx.ist.psu.edu/document?doi=22554822cff90a56962f8ce4327587e86a42f1dc&repid=rep1&type=pdf NSE F&O UDiFF archives: https://www.nseindia.com/all-reports-derivatives . Raw URLs and hashes: data/download_manifest.csv. Calculations: results/*.csv.

## Slide 16

Timing: 34 seconds. Point to the reproducible project folder and theory guide for viva preparation. All results arise from the accompanying code and public NSE files. Approximate Greek attribution now includes an explicit residual. Added rolling calibration, rate and execution stress checks, and a rolling-60 forecast comparator are retrospective diagnostics, not new held-out evidence. GARCH, Heston, VIX, fixed-vega sizing and historical margin modelling remain incomplete. Ahmad & Wilmott (2005), Wilmott Magazine, November, pp.64–79, Sections 3–4. https://citeseerx.ist.psu.edu/document?doi=22554822cff90a56962f8ce4327587e86a42f1dc&repid=rep1&type=pdf NSE F&O UDiFF archives: https://www.nseindia.com/all-reports-derivatives . Raw URLs and hashes: data/download_manifest.csv. Calculations: results/*.csv.