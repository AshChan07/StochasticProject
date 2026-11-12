# MAC F244: Volatility Arbitrage and Delta Hedging on NIFTY Options

Core replication of Ahmad & Wilmott (2005), with an empirical NIFTY adaptation.
Authors supplied in the proposal: Arnav, Rohan, Joel, Ashwath, Advay.
Add your institutional ID numbers before submission if your instructor requires them.

## Deliverables
- deliverables/project_report.pdf: four-page report.
- deliverables/project_presentation_final.pptx: editable presentation with speaker notes.
- docs/THEORY_AND_VIVA.md: extended derivation and viva preparation.
- results/: simulation outputs, forecast evaluation, trade logs, daily ledgers, sensitivities and figures.
- data/clean/: real NSE historical data and derived signals.
- DATA_DOWNLOAD_GUIDE.md: original sources and optional extensions.
- src/, tests/, download_data.py, run_project.py: reproducible implementation.

## Run
Python 3.11+ recommended. In a fresh virtual environment:
```
python -m pip install -r requirements.txt
python run_project.py
python -m unittest discover -s tests -v
```
The default run uses included clean files. It regenerates numerical results and PNG figures, with no network access. Report/deck generation is separate; see build/README.md. It does not automatically overwrite submission documents after changing assumptions.

To rebuild data from source:
```
python download_data.py
python run_project.py --rebuild-data
```
To run only the Monte Carlo replication:
```
python run_project.py --simulation-only
```
Data fetching uses curl with HTTPS and bounded retries. All missing requests are logged. No unavailable file is silently converted into prices. Source ZIPs are immutable cache files. Date and contract-key validation fail loudly.

## Fixed experiment design
- Market sample: 8 July 2024–31 December 2025, including the 1 February 2025 special session.
- Warm-up: 60 close log returns. EWMA lambda 0.94, annualization 252.
- Calibration: 7 October 2024–30 June 2025. Thresholds 0, 1, 2, 3 volatility percentage points. Select the largest mean net P&L across both hedge rules with at least 10 trades.
- Test: 1 July–31 December 2025. No threshold reselection on test data.
- Entry selection: closest strike to matched futures close with both legs traded and valid IV; first futures-matched expiry 14–65 calendar days away.
- Signals and deltas use prior close data. Execution uses the next session's recorded opening prices. Open quotes across contracts can be asynchronous and are an approximation to executable prices.
- One long or short straddle unit, fractional futures, no overlaps. Hold five observed sessions, exit earlier at 7 days to expiry or sample end. No new entry in the last five sessions. No new position on an exit day.
- No future volume filter at execution. A missing/nonpositive entry open cancels the trade. Missing held-position marks raise an error. Invalid prior IV carries the hedge and logs an event.
- Daily futures hedge under per-leg implied vol or EWMA forecast vol. Position identifiers never change during a trade.
- Flat rate 6.5% is an assumption. Cash earns/pays the same rate; futures variation margin is approximated at each observation.
- Base costs: 0.20% of option premium each way plus 1 bp of futures notional traded, all-in illustrative proxies. Not exact brokerage/STT/exchange-fee reconstruction. Sensitivities: 0x, 1x, 2x, 5x and hedge every 1/2/5 sessions.
- P&L is in index points per one signed straddle unit. Fixed reporting capital 100,000 provides an illustrative denominator only. Exchange lots, collateral haircuts, actual margin and position limits are not enforced. These are research results, not account-level executable returns.

## Interpretation
The simulation uses a known constant volatility and continuous-limit theory. The historical forecast is uncertain, implied volatility changes, and trades close before expiry. Historical gains therefore do not inherit the paper's guarantee. Test performance is descriptive for one short period. An IID paired-trade bootstrap is included but ignores serial dependence.

## What the proposal promised that is not implemented
GARCH, Parkinson range forecasts, VIX benchmarking, the 2019–2026 sample, Heston calibration/hedges, fixed-vega sizing and a full Greek P&L decomposition are outside this completed core scope. The report states the implemented scope. Exact attribution instead separates option marks, futures gains, financing and transaction costs without a Taylor-series residual.

## Files and units
All volatility fields are decimals (0.20 = 20%); thresholds 0.01 = one volatility point. Dates are exchange-local dates without intraday timestamps. Option and futures prices are index points. rates are annual decimals. Option IV uses Black-76 on matched futures, deterministic rates and calendar time /365.

## Reproducibility and provenance
Monte Carlo seed=244. 20,000 paths per volatility scenario; 6,000 paths at each convergence frequency. data/download_manifest.csv has raw-file hashes. results/experiment.json has all selected assumptions. Tests verify reference prices, parity, numerical delta, IV inversion, simulation convergence, causal signals, and P&L reconciliation.
