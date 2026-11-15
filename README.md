# Volatility Arbitrage and Delta Hedging on NIFTY Index Options

A reproducible stochastic-calculus project that implements the central hedging comparison in **Ahmad & Wilmott (2005)** and applies two delta-hedging rules to historical NIFTY monthly options.

**Course:** MAC F244 — Stochastic Calculus and Application to Finance  
**Institution:** BITS Pilani, K K Birla Goa Campus  
**Instructor:** Mayank Goel  
**Team:** Arnav, Rohan, Joel, Ashwath and Advay

## Overview

When an option’s implied volatility differs from the volatility expected for its underlying, which volatility should determine the hedge?

This project investigates that question through:

1. A mathematical derivation using Itô’s formula and the Black–Scholes pricing PDE.
2. Monte Carlo replication with known actual volatility.
3. A historical NIFTY straddle backtest comparing implied-volatility delta with EWMA-forecast-volatility delta.
4. Transaction-cost, threshold and rebalancing-frequency sensitivity analysis.

**Status:** The core implementation, cleaned historical data, numerical results, four-page report, presentation and viva notes are included. The calibrated strategy produces only **three test-period trades**, so the historical results are exploratory, not evidence of reliable arbitrage or hedge superiority.

## Integrated pipeline and independent audit

The November 15 revision integrates Joel’s supplied parser, parity-forward diagnostics, independent IV solver and archive fixtures into the working project. Read [AUDIT_AND_INTEGRATION.md](docs/AUDIT_AND_INTEGRATION.md) for the findings, fixes, evidence and remaining limitations.

The theory now derives **both stock and futures wealth equations**, with the correct premium-paid futures delta and no financed futures principal. The viva guide explains stochastic IV, vega/vanna/volga, basis risk, variance risk premia and the mismatch between a five-session forecast check and an option’s maturity. A separate futures Monte Carlo verifies the accounting.

**New evidence changes the interpretation:** at the selected threshold, next-close execution gives 97.44 points for implied delta and 87.56 for forecast delta, reversing the next-open ranking. The identical next-open option trades without a hedge earn 147.99 points. These checks reinforce that three trades cannot establish superiority.

Added outputs are **retrospective diagnostics on previously inspected data**, not a fresh independent test. Monthly expanding calibration carries open positions across month boundaries and retains the 3-point threshold in every fold. It does not create more independent observations.

| New output under `results/` | Purpose |
|---|---|
| `futures_simulation.csv` | Separate theoretical replication with futures variation margin |
| `parity_diagnostics.csv`, `audit_summary.json` | Option-implied forward vs traded futures; independent IV cross-check |
| `execution_controls.csv` | Next-open/next-close and identical-entry unhedged controls |
| `rate_sensitivity.csv` | Recompute IV/signals under 3%, 6.5%, 10% assumed rates; freeze threshold and strike choices |
| `walk_forward.csv`, `walk_forward_daily_*.csv` | Monthly past-only recalibration with continuous test-position tracking |
| `forecast_benchmark.csv` | EWMA vs rolling-60 volatility on matching five-session targets |
| `greek_attribution_*.csv` | Approximate delta/gamma/theta/vega attribution with residual and invalid-IV flags |

Run the same `python run_project.py` command to regenerate these outputs. No extra downloads are needed. The integrated normalizer accepts legacy schemas, but rebuilding a legacy sample requires a separately validated spot series and an expanded calendar audit; the main empirical sample remains July 2024–December 2025. The supplied folder contained code, not additional real market data.

## Main deliverables

| Deliverable | Location |
|---|---|
| Four-page project report | [project_report.pdf](deliverables/project_report.pdf) |
| Editable 16-slide presentation with speaker notes | [project_presentation_final.pptx](deliverables/project_presentation_final.pptx) |
| Extended derivation and viva questions | [THEORY_AND_VIVA.md](docs/THEORY_AND_VIVA.md) |
| Slide-by-slide speaking notes, approximately 17 minutes | [PRESENTATION_NOTES.md](docs/PRESENTATION_NOTES.md) |
| Computed results summary | [RESULTS_SUMMARY.md](results/RESULTS_SUMMARY.md) |
| Data sources and download instructions | [DATA_DOWNLOAD_GUIDE.md](DATA_DOWNLOAD_GUIDE.md) |
| Submission checklist | [DELIVERABLES.md](DELIVERABLES.md) |

## Directory chart

The chart lists the main project files. Raw data and generated build files may exist locally but are excluded from Git.

```text
StochasticProject/
├── README.md                          # Main project documentation
├── PROJECT_README.md                  # Earlier project overview
├── DELIVERABLES.md                    # Submission checklist
├── DATA_DOWNLOAD_GUIDE.md             # Sources and download instructions
├── FILES_SHA256SUMS.txt                # Checksums for packaged project files
├── requirements.txt                  # Python dependencies
├── run_project.py                    # Run simulations and historical study
├── download_data.py                  # Download and cache NSE archives
├── .gitignore                        # Excludes raw downloads and build output
│
├── src/
│   ├── __init__.py
│   ├── pricing.py                    # Black–Scholes, Black-76, delta and IV
│   ├── simulation.py                 # GBM paths and self-financing stock hedge
│   ├── data.py                       # Archive normalization and ATM selection
│   ├── backtest.py                   # EWMA, trading rules, ledger and analysis
│   └── robustness.py                 # Futures replication and retrospective checks
│
├── data_pipeline/                    # Adapted modules from Joel’s supplied pipeline
│   ├── __init__.py
│   ├── config.py
│   ├── bhavcopy.py                    # Legacy/UDiFF normalizer and archive helpers
│   ├── forwards.py                    # Liquid-strike parity diagnostics
│   └── iv.py                          # Independent IV implementation
│
├── tests/
│   ├── test_project.py               # Original 14 regression tests
│   ├── test_audit.py                  # 16 additional audit tests
│   └── pipeline_fixtures.py           # Synthetic archives from supplied pipeline
│
├── data/
│   ├── download_manifest.csv         # Source URLs, download status and hashes
│   ├── raw/                          # Original NSE ZIPs; local only, Git-ignored
│   └── clean/
│       ├── nifty_daily.csv           # NIFTY underlying closes
│       ├── nifty_futures.csv         # Futures prices and contract identifiers
│       ├── nifty_options_chain.csv.gz # Monthly options, prices and IVs
│       ├── atm_panel.csv             # Daily eligible ATM option pairs
│       └── signal.csv                # Forecast, implied volatility and signal
│
├── results/
│   ├── RESULTS_SUMMARY.md
│   ├── experiment.json               # Experiment assumptions and chosen threshold
│   ├── runtime_versions.json         # Versions used for the saved results
│   ├── data_quality.json
│   ├── calendar_audit.csv
│   ├── archive_coverage.csv
│   ├── clean_data_manifest.json
│   ├── simulation_summary.csv
│   ├── simulation_paths.csv.gz
│   ├── histogram.csv
│   ├── convergence.csv
│   ├── forecast_evaluation.csv
│   ├── forecast_metrics.csv
│   ├── threshold_calibration.csv
│   ├── test_metrics.csv
│   ├── backtest_daily_implied.csv
│   ├── backtest_daily_forecast.csv
│   ├── trades_implied.csv
│   ├── trades_forecast.csv
│   ├── events_implied.csv
│   ├── events_forecast.csv
│   ├── sensitivity.csv
│   ├── test_threshold_sensitivity.csv
│   └── figures/                      # Report figures and volatility comparison
│
├── deliverables/
│   ├── project_report.pdf
│   └── project_presentation_final.pptx
│
├── docs/
│   ├── AUDIT_AND_INTEGRATION.md
│   ├── THEORY_AND_VIVA.md
│   ├── PRESENTATION_NOTES.md
│   └── report_source.md               # Editable report text
│
└── build/
    ├── README.md                     # Document-building instructions
    ├── build_report.py               # ReportLab PDF builder
    ├── build_slides.mjs               # Editable presentation builder
    ├── slide_data.json               # Numerical inputs for the presentation
    ├── audit_calendar.py             # Sample-specific NSE calendar audit
    └── test_results.txt               # Saved test output
```

## Quick start

### Requirements

- Python **3.11 or newer** is recommended; the saved numerical results used Python 3.12.
- Dependencies listed in `requirements.txt`.
- `curl` and internet access are needed only when downloading original NSE archives.
- No API key, brokerage account or paid dataset is required for the included experiment.

### Setup on macOS or Linux

Open a terminal in this repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows, create the environment with `py -m venv .venv` and activate it in PowerShell with `.venv\Scripts\Activate.ps1`.

### Run the project

```bash
python run_project.py
```

The default command uses the included cleaned data and regenerates numerical CSVs and PNG figures under `results/`. No network access is required when the cleaned files are present. Existing numerical outputs are overwritten.

To run only the theoretical Monte Carlo replication:

```bash
python run_project.py --simulation-only
```

To run the tests:

```bash
python -m unittest discover -s tests -v
```

**The report and presentation do not regenerate automatically.** If you change the experiment, regenerate the numerical results and update the documents and their interpretation separately.

## Data and provenance

The historical sample covers **8 July 2024 through 31 December 2025**:

- **370 trading sessions**, including the special Saturday budget session on 1 February 2025.
- **222,520 monthly-option records** and **1,110 futures records**.
- NIFTY closes derived from the NSE archive’s underlying-price field.
- Nineteen unavailable weekday files matched against published holiday calendars.

The source is NSE’s **F&O-UDiFF Common Bhavcopy Final** archive. Monthly option expiries are identified by matching actual futures expiries. All strikes are retained to track held positions. File dates and contract-key uniqueness are validated, and invalid implied volatilities are not replaced with invented values.

The cleaned dataset is included. To download the original files again:

```bash
python download_data.py
python run_project.py --rebuild-data
python build/audit_calendar.py
```

The downloader caches original ZIPs in `data/raw/`, which Git ignores. It records source URLs, download outcomes and SHA-256 hashes in `data/download_manifest.csv`.

For a narrower range within the supported sample:

```bash
python download_data.py --start 2025-01-01 --end 2025-12-31 --workers 3
```

The parser processes all ZIPs already present in `data/raw/`. A narrower download request does **not** remove previously cached files or change the backtest’s fixed train/test dates. Use a separate cache and update the experiment explicitly if you intend to change the sample.

**Coverage limitation:** The integrated normalizer supports legacy and UDiFF schemas. The completed real-data experiment uses UDiFF from July 2024 onward. Earlier years still require a validated spot series and calendar review. Extending beyond the current sample also requires checking special trading sessions.

If automated downloads fail, download the original ZIPs manually from [NSE derivatives reports](https://www.nseindia.com/all-reports-derivatives), place them in `data/raw/` without renaming them, and rebuild. Full instructions and optional sources are in [DATA_DOWNLOAD_GUIDE.md](DATA_DOWNLOAD_GUIDE.md).

## Methodology

### 1. Mathematical replication

The simulated underlying follows geometric Brownian motion under the physical measure:

$$
dS_t = \mu S_t\,dt + \sigma S_t\,dB_t.
$$

Let $V_i$ denote the option value at implied volatility $\sigma_i$, and let $\Delta_h$ be the hedge delta. Holding one option, $-\Delta_h$ shares and cash $C$ gives wealth $W = V_i - \Delta_h S + C$. With self-financing rebalancing, Itô’s formula and the pricing PDE give:

$$
dW-rW\,dt = \frac{1}{2}(\sigma^2-\sigma_i^2)S^2\Gamma_i\,dt
+ (\Delta_i-\Delta_h)\big[(\mu-r)S\,dt+\sigma S\,dB\big].
$$

- **Known actual-volatility hedge:** Under continuous trading and the model assumptions, discounted terminal profit equals the difference between the actual-volatility and implied-volatility option values.
- **Constant implied-volatility hedge:** The explicit Brownian term cancels, but accumulated gamma gains remain path-dependent.

The simulation uses exact GBM transitions, a stock hedge and an explicit interest-bearing cash account. The historical study instead uses futures and uncertain volatility forecasts. It does not inherit the theoretical guarantee.

### 2. Monte Carlo setup

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

Both hedge rules use the same simulated paths.

### 3. Historical trading design

| Component | Implemented rule |
|---|---|
| Volatility estimate | EWMA, λ = 0.94, initialized with 60 squared close log returns |
| Annualization | 252 trading sessions |
| Option pricing and IV | Black-76 using matched-expiry futures |
| Entry candidate | First monthly expiry 14–65 calendar days away; nearest eligible strike to futures close |
| Signal | Forecast volatility minus mean call/put implied volatility |
| Direction | Long above +k; short below −k; otherwise no trade |
| Decision and execution | Previous-close signal and delta; next-session recorded opening prices |
| Position size | One signed straddle unit with fractional futures |
| Holding period | Five observed sessions; earlier exit at seven days to expiry or sample end |
| Position tracking | Same strike and expiry throughout each trade; no overlapping positions |
| Hedge rules | Per-leg implied-volatility delta versus EWMA-forecast-volatility delta |
| Assumed interest rate | Flat 6.5% annually |
| Base option cost | 0.20% of premium per entry/exit side |
| Base futures cost | One basis point of traded notional |
| Cost sensitivity | 0×, 1×, 2× and 5× base assumptions |
| Hedge-frequency sensitivity | Every 1, 2 or 5 sessions |

An unavailable or nonpositive entry opening price cancels the entry. Missing held-position opening marks raise an error. Invalid prior implied volatility carries the existing hedge and records an event. No new trade opens on an exit day or during the final five sessions of a sample.

### 4. Calibration and test split

- **Calibration:** 7 October 2024–30 June 2025.
- **Test:** 1 July–31 December 2025.
- **Candidate thresholds:** 0, 1, 2 and 3 volatility percentage points.
- **Selection:** Highest average calibration net P&L across both hedge rules, with at least ten calibration trades.
- **Selected threshold:** **3 volatility points** (`0.03`).

Test-period threshold alternatives are reported as diagnostics. They do not replace the threshold chosen using calibration data.

The ledger separates option-price changes, futures gains, financing and direct modeled costs. Daily net P&L reconciles to completed-trade P&L.

## Saved results

### Simulation

For 30% actual volatility and 20% implied volatility:

| Quantity | Actual-volatility hedge | Implied-volatility hedge |
|---|---:|---:|
| Mean discounted P&L | 3.7840 | 3.7404 |
| Standard deviation | 0.6218 | 1.8547 |

The theoretical actual-hedge profit is **3.7807**, compared with a simulated mean of **3.7840** and Monte Carlo standard error of approximately **0.0044**. The convergence experiment estimates a log–log error slope of **−0.496**, close to the theoretical −0.5 reference.

### Historical test

The selected threshold produces **three trades**, all short straddles, across 126 test sessions.

| Metric | Implied-volatility delta | Forecast-volatility delta |
|---|---:|---:|
| Net P&L, index points | 159.22 | 165.80 |
| Maximum drawdown, index points | 55.78 | 65.70 |
| Direct modeled costs, index points | 12.28 | 14.31 |
| Annualized daily P&L Sharpe | 1.63 | 1.54 |

The forecast hedge has slightly higher net P&L but also higher drawdown. Three trades cannot establish a dependable performance advantage. Increasing costs to five times the base assumptions reverses the small P&L ranking. At the zero-threshold diagnostic, 21 test trades yield net P&L of 46.09 and 103.50 points respectively.

See [results/RESULTS_SUMMARY.md](results/RESULTS_SUMMARY.md), [test_metrics.csv](results/test_metrics.csv), [sensitivity.csv](results/sensitivity.csv) and [test_threshold_sensitivity.csv](results/test_threshold_sensitivity.csv).

## Units and interpretation

- Volatilities are annualized decimals: `0.20` means 20%.
- Threshold `0.01` means **one volatility percentage point**.
- Option and futures prices and P&L are in **index points per one straddle unit**, not rupees per exchange lot.
- Option maturity and financing use calendar days divided by 365.
- Dates are exchange-local dates without intraday timestamps.
- A fixed reporting capital of 100,000 supplies an illustrative return denominator. It is not a reconstructed margin account.
- Sharpe uses annualized daily incremental P&L, including inactive days. Its interpretation is limited by the short sample and few trades.

## Validation and reproducibility

The included **30 tests** cover the original checks below, plus dual-schema parsing, parity recovery, special sessions, nonfinite quote rejection, the Black-76 PDE, futures replication, independent IV inversion, empty trades, predecessor availability, execution timing, unhedged controls and held-contract retention:

- A reference Black–Scholes price and put-call parity.
- Futures delta against finite differences.
- Implied-volatility inversion and invalid-price rejection.
- Expiry payoff handling.
- Equal-volatility simulations and replication-error convergence.
- Cash financing and futures P&L.
- Contract-key uniqueness and inclusion of the special budget session.
- Identical trade selection across hedge rules.
- Trade-to-daily-ledger reconciliation.
- Cost sensitivity, lagged entry signals and invariance of earlier results to later signal changes.

Reproducibility files:

- [experiment.json](results/experiment.json): selected assumptions and threshold.
- [runtime_versions.json](results/runtime_versions.json): numerical environment used.
- [download_manifest.csv](data/download_manifest.csv): raw-data provenance and checksums.
- [clean_data_manifest.json](results/clean_data_manifest.json): cleaned-data checksums.
- [test_results.txt](build/test_results.txt): saved test output.
- [FILES_SHA256SUMS.txt](FILES_SHA256SUMS.txt): packaged-file checksums, which need refreshing after modifying covered files.

Dependency ranges are specified in `requirements.txt`; exact versions for the saved numerical run are recorded separately.

## Report and presentation generation

The default numerical command does not overwrite the report or slide deck.

To rebuild the report from the current saved results:

```bash
python build/build_report.py
```

The PDF builder uses ReportLab. Its narrative describes the fixed experiment, so changing parameters requires updating numerical prose and conclusions as well as regenerating tables and figures.

The presentation builder uses the Codex bundled `@oai/artifact-tool` runtime and machine-specific paths. The exported PPTX is standalone and editable in PowerPoint or compatible software. You do not need Codex to view or edit it.

Read [build/README.md](build/README.md) for document-authoring requirements. Editable report text and speaker notes are in `docs/`.

## Limitations and unimplemented extensions

The historical study uses daily opening prices, which are not synchronized bid/ask quotes. Costs are illustrative all-in proxies, not an exact reconstruction of historical brokerage, STT and exchange fees. Exchange lot sizes, margin constraints, collateral costs and position limits are not enforced. Futures variation margin is approximated at each observation.

The forecast is uncertain, implied volatility changes, and positions close before expiry. These features differ from the paper’s constant-volatility, continuous-trading benchmark. The paired-trade bootstrap interval is suppressed below 20 trades; even above that threshold, IID resampling would not account for serial dependence.

The following proposal extensions are **not implemented**:

- GARCH and Parkinson volatility estimates.
- India VIX benchmarking.
- Heston calibration and hedging.
- Fixed-vega sizing.
- Exact continuous-time Greek attribution; the implemented discrete Taylor decomposition includes a residual.
- The originally proposed 2019–2026 sample.

The completed scope uses EWMA, July 2024–December 2025 data, fixed per-unit sizing, exact accounting attribution, approximate Greek attribution, and the audit diagnostics described above.

## Team preparation and presentation responsibilities

This is a proposed preparation split for Arnav, Rohan, Joel, Ashwath and Advay, based on the current 16-slide deck. It assigns learning and improvement ownership. Joel’s supplied pipeline is now incorporated with documented adaptations; this table is not a full code-authorship record. Everyone should understand the overall experiment and its limitations.

### Presentation allocation

The existing speaker notes total approximately 17 minutes. Times below follow those notes; shorten them together if the course presentation slot is shorter. Arnav has the longest section because it includes the derivation; Advay also leads the closing discussion and routes questions.

| Member | Slides and approximate time | What to learn and explain | Main preparation files |
|---|---|---|---|
| **Arnav** | **1–4**, 4 min 10 sec: question, paper and theory | Actual, implied and forecast volatility; GBM; Itô’s formula; the pricing PDE; delta and gamma; self-financing cash; derivation of the wealth equation; why actual-volatility replication and implied-volatility hedging have different terminal dispersion | `docs/THEORY_AND_VIVA.md`, `docs/report_source.md`, `src/pricing.py`; paper Sections 3–4 |
| **Rohan** | **5–7**, 3 min 10 sec: Monte Carlo and convergence | Exact GBM transitions; shared paths and random seed; stock/cash rebalancing; discounted terminal P&L; theoretical benchmark; standard deviation versus standard error; interpretation of the −0.496 convergence slope | `src/simulation.py`, `results/simulation_summary.csv`, `results/convergence.csv`, relevant tests in `tests/test_project.py` |
| **Joel** | **8–10**, 3 min 30 sec: data, trading rules and calibration | NSE archive provenance; cleaning and expiry matching; Black-76 IV; EWMA and warm-up; previous-close decisions and next-open execution; contract selection and exits; calibration/test separation and threshold selection | `download_data.py`, `src/data.py`, `src/backtest.py`, `DATA_DOWNLOAD_GUIDE.md`, `results/threshold_calibration.csv` |
| **Ashwath** | **11–13**, 3 min 15 sec: historical results and costs | Trace one trade through the ledger; option, futures, financing and cost contributions; points versus rupees; drawdown and Sharpe; three-trade sample limitation; why more P&L does not imply a better hedge; cost-induced ranking reversal | `src/backtest.py`, `results/RESULTS_SUMMARY.md`, `results/trades_*.csv`, `results/backtest_daily_*.csv`, `results/test_metrics.csv`, `results/sensitivity.csv` |
| **Advay** | **14–16**, 2 min 40 sec: robustness, conclusions and reproducibility | Threshold diagnostics versus test-set tuning; limits of the three-trade bootstrap; model/execution limitations; implemented versus proposed scope; how to reproduce the results; priorities for future work | `results/test_threshold_sensitivity.csv`, `results/experiment.json`, `tests/test_project.py`, `DELIVERABLES.md`, this README |

Each person should read their slide notes in [PRESENTATION_NOTES.md](docs/PRESENTATION_NOTES.md), understand the corresponding figure or table, and explain their section without reading the slide verbatim.

### New preparation priorities after the audit

- **Arnav:** Derive the futures equation as well as the stock equation; explain the discounted delta, zero-value futures and stochastic-IV terms.
- **Rohan:** Explain the additional futures simulation, its distinct theoretical target and why stock financing cannot be copied into a futures ledger.
- **Joel:** Explain the integrated parser, July 2024 routing boundary, same-date futures expiry matching, all-strike retention and why parity remains a diagnostic.
- **Ashwath:** Explain the execution-ranking reversal, unhedged control and Greek residual. Do not describe 165.80 points as proof of hedge superiority.
- **Advay:** Explain the retrospective status of the added checks, monthly position continuity, suppressed bootstrap interval and remaining margin/quote limitations.

Several original improvement suggestions below are now partially addressed by the audit. Use them for verification and further work, not as claims that the new diagnostics are still absent.

### Individual viva preparation

Prepare short answers to these questions and practice explaining any equation or number you use:

- **Arnav:** Why does the implied-delta hedge cancel the explicit Brownian term without guaranteeing deterministic terminal profit? Under what assumptions does the actual-volatility hedge replicate? Why is the historical experiment not guaranteed arbitrage?
- **Rohan:** Why use exact GBM transitions and identical paths for both hedges? Why does discrete hedging leave error? What does a slope near −1/2 mean? Why is a Monte Carlo standard error different from P&L dispersion?
- **Joel:** How is IV recovered from an option price? Why use matched futures and Black-76? How do the signal and execution timestamps prevent look-ahead? How was the threshold selected, and what data were withheld?
- **Ashwath:** How does one completed trade reconcile with daily P&L? Why are results quoted per unit in index points? Why can the forecast hedge earn more yet have worse drawdown and Sharpe? How do costs change the comparison?
- **Advay:** Why can we not claim superiority from three trades? Why not choose the best-looking test threshold? Which extensions remain unimplemented? What additional evidence would make the historical conclusion more convincing?

### Improvement ownership

These are follow-up ownership suggestions; consult the audit section for work already implemented. Finish the core understanding and rehearsal first. Prioritize the small checks below before adding models or changing the experiment close to submission.

| Owner | First improvement to attempt | Completion criterion | Optional extension if time permits |
|---|---|---|---|
| **Arnav** | Audit notation and assumptions across the report, slides and theory notes | All symbols are defined consistently; stock-delta theory is distinguished from futures-delta implementation; continuous trading, constant volatility and financing assumptions are explicit | Add a short worked derivation to the existing theory notes showing the self-financing substitution step by step |
| **Rohan** | Check Monte Carlo stability using a few additional seeds in a separate experiment | Save a compact comparison of mean, dispersion and Monte Carlo error; explain variation without replacing the published baseline merely because another seed looks better | Compare convergence in both actual-volatility scenarios and document computation time |
| **Joel** | Strengthen the data-quality summary using existing cleaned data | Document date coverage, missing/invalid quotes, duplicate contract checks and entry exclusions; distinguish a rejected candidate from a missing mark for an existing position | Extend the supported UDiFF sample and audit the exchange calendar, with a new untouched test interval specified before inspecting outcomes |
| **Ashwath** | Produce a worked ledger walkthrough for one existing test trade | Show entry/exit prices, signed position, futures hedge changes, financing and costs; totals reconcile to the saved trade and daily ledgers | Add realistic lot-size and fee scenarios only after sourcing date-specific contract sizes and charge schedules; clearly separate them from the current per-unit baseline |
| **Advay** | Audit reproducibility and consistency of the final submission | Run setup and tests, check report/deck numbers against saved outputs, verify links, and record discrepancies; ensure all five speakers use the same limitations and conclusions | Design a walk-forward evaluation with calibration restricted to past data; implement only if sufficient data and validation time are available |

The first tasks use the included data and require **no additional downloads**. Extending the historical sample requires more NSE archives; realistic trading-cost and lot-size work requires official historical specifications. Consult [DATA_DOWNLOAD_GUIDE.md](DATA_DOWNLOAD_GUIDE.md) before collecting extra data. GARCH, Heston and additional forecasting models are lower priority than credible evaluation and clear explanations.

Keep exploratory outputs separate from the saved baseline. If an improvement changes the submitted experiment, rerun the relevant checks, update the report, slides and README together, and refresh the checksum manifest. Do not tune parameters on the existing test period and describe it as an untouched test afterward.

### Shared preparation and rehearsal

1. **Everyone reads:** the four-page report, this README’s methodology/results/limitations, and the introductory portions of [THEORY_AND_VIVA.md](docs/THEORY_AND_VIVA.md).
2. **Everyone can explain:** the research question, the two hedge rules, the difference between known actual and forecast volatility, the train/test split, the main simulation result, and why three historical trades are insufficient for a general performance claim.
3. **Each owner prepares:** a one-page outline, one walkthrough of an equation/code path/trade relevant to their section, and answers to their viva questions above.
4. **Cross-check in pairs:** Arnav and Rohan check theory against simulation; Joel and Ashwath check data and timing against the trade ledger; Advay checks consistency across all sections and the final artifacts.
5. **Rehearse once end to end:** time the talk, practice handoffs, and ask questions outside each person’s assigned section. Use the current results without presenting optional work as completed.
6. **Before submission:** open the final PDF and PPTX, verify the team details and course requirements, and agree on one final version. Advay coordinates this check; every member signs off on their own section.

## GitHub Desktop notes

Open this repository in GitHub Desktop to review and commit changes. The project does not submit orders or push commits automatically.

Raw ZIP archives, Python caches, virtual environments, temporary chart workbooks and generated preview/build files are ignored. The cleaned data, code, selected build sources, results, report and final presentation can be versioned. Avoid committing the large raw archive cache or local `node_modules` dependencies.

## References

1. Ahmad, R. and Wilmott, P. (2005). *Which Free Lunch Would You Like Today, Sir?: Delta Hedging, Volatility Arbitrage and Optimal Portfolios.* Wilmott Magazine, November, pp. 64–79. Core replication: Sections 3–4. [Publisher page](https://www.wilmott.com/which-free-lunch-would-you-like-today-sir-delta-hedging-volatility-arbitrage-and-optimal-portfolios-riaz-ahmad-and-paul-wilmott/).
2. Black, F. (1976). *The Pricing of Commodity Contracts.* Journal of Financial Economics, 3, pp. 167–179.
3. Shreve, S. E. (2004). *Stochastic Calculus for Finance II: Continuous-Time Models.* Springer, Chapters 4–5.
4. J.P. Morgan/Reuters (1996). *RiskMetrics Technical Document*, 4th edition.
5. National Stock Exchange of India. *F&O-UDiFF Common Bhavcopy Final*. [Official reports](https://www.nseindia.com/all-reports-derivatives). Individual source URLs and calendar references accompany the dataset.
