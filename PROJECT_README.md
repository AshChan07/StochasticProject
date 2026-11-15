# MAC F244: Volatility Arbitrage and Delta Hedging on NIFTY Options

Core replication of Ahmad & Wilmott (2005), with an empirical NIFTY adaptation.
Authors supplied in the proposal: Arnav, Rohan, Joel, Ashwath, Advay.
BITS Pilani, K K Birla Goa Campus.

## Deliverables
- deliverables/project_report.pdf: four-page final report.
- deliverables/project_presentation_final.pptx: editable presentation with speaker notes.
- docs/THEORY_AND_VIVA.md: extended derivation, Black-76 Futures Itô wealth SDE, and 20 comprehensive viva questions.
- results/: simulation outputs, tail risk metrics, drift sensitivity, forecast evaluation (EWMA & GARCH), trade logs, daily ledgers, naive benchmark, capacity sensitivities and figures.
- data/clean/: real NSE historical data and derived signals (with Vega-weighted mispricing).
- DATA_DOWNLOAD_GUIDE.md: original sources and optional extensions.
- src/, tests/, download_data.py, run_project.py: reproducible implementation.

## Run
Python 3.11+ recommended. In a fresh virtual environment:
```
python -m pip install -r requirements.txt
python run_project.py
python -m unittest discover -s tests -v
```
The default run uses included clean files. It regenerates numerical results and PNG figures, with no network access. Report generation: `python build/build_report.py`.

## Fixed experiment design
- Market sample: 8 July 2024–31 December 2025, including the 1 February 2025 special budget session.
- Warm-up: 60 close log returns. EWMA lambda 0.94 and Maximum-Likelihood GARCH(1,1).
- Calibration: 7 October 2024–30 June 2025. Thresholds 0, 1, 2, 3 volatility percentage points. Select the largest mean net P&L across both hedge rules with at least 10 trades (selected k = 3%).
- Test: 1 July–31 December 2025. No threshold reselection on test data.
- Entry selection: closest strike to matched futures close with both legs traded and valid IV; first futures-matched expiry 14–65 calendar days away.
- Signals and deltas use prior close data. Execution uses the next session's recorded opening prices.
- Holding: five observed sessions, exit earlier at 7 days to expiry or sample end.
- Hedging: Daily futures hedge under per-leg implied vol or EWMA forecast vol.
- Flat rate 6.5% assumption. Cash earns/pays the same rate; futures variation margin is approximated at each observation.
- Base costs: 0.20% of option premium each way plus 1 bp of futures notional traded.
- Benchmark: Naive rolling short ATM straddle (Variance Risk Premium baseline) to isolate active alpha from passive short-volatility beta.
- Capacity scaling: Evaluation of inventory limits with concurrent positions (1, 2, 3 active straddles).

## Implemented Scope & Extensions
- Completed: Ahmad & Wilmott core replication, Black-76 Futures Itô wealth SDE, exact GBM transitions, N^(-1/2) convergence, tail risk analysis (VaR/CVaR/skewness/kurtosis), physical drift invariance testing, real NSE UDiFF data parsing, EWMA vs GARCH(1,1) ML comparison, Vega-weighted mispricing, causal trade ledger, cost sensitivity, naive VRP benchmark comparison, and multi-position inventory capacity.
- Non-implemented advanced extensions: Heston stochastic volatility calibration, intraday high-frequency tick data, and statutory tax reconstruction.

## Verification
17 automated unit tests verify pricing, Black-76 Greeks, put-call parity, IV inversion, GBM simulation convergence, drift invariance, GARCH stationarity, capacity scaling, and trade-to-daily ledger reconciliation.
