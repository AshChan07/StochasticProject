# Independent audit and pipeline integration

Audit date: 15 November 2026. Branch: `improve/pipeline-theory-audit`.
The supplied photograph makes a broad criticism but does not expose its detailed arguments. This audit therefore checks the implementations and assumptions independently. It does not claim that every possible objection has been eliminated.

## What was integrated

Joel's supplied `macf244-volarb` contributes the legacy/UDiFF normalizer, an independent Black-76 IV solver, liquid-strike put-call-parity calculation and synthetic archive fixtures. Adapted modules are in `data_pipeline/`; fixtures are in `tests/pipeline_fixtures.py`. The main `src/data.py` builder actually calls the shared normalizer and parity routine on the existing 370 cached archives. The independent IV solver checks 1,934 valid quotes against the main solver. Maximum absolute volatility difference is about 4.63e-13.

We retain the established futures-based IV and hedge definition. An option-implied forward is useful as a diagnostic, but silently replacing a traded futures price with it would introduce an unmodelled hedge basis. The imported full downloader/market/panel orchestration is not the production entry point. Its rate-download fallbacks, strike-band filter and global monthly-expiry inference were deliberately not adopted.

## Findings and disposition

| Finding | Resolution and evidence | Remaining qualification |
|---|---|---|
| Stock theorem presented alongside futures implementation without deriving the bridge | Added the futures wealth/PDE derivation and independent futures replication simulation; finite-difference PDE and discounted-delta tests | Deterministic rates/carry, continuous trading and known volatility remain ideal assumptions |
| Implied-volatility motion omitted from the simple wealth equation | Added vega, volga and vanna quadratic-variation terms; implemented approximate Greek attribution with an explicit residual | Attribution is descriptive and uses observed subsequent IV changes; it is not a forecast |
| Supplied pipeline claims a clean January 2024 format switch | Preferred routing now switches on 8 July 2024, after legacy discontinuation; schema detected from actual columns | There was earlier format overlap. Legacy parsing is tested synthetically, not a completed long historical study |
| Supplied pipeline drops strikes outside a moving 15% band | Production chain retains all monthly strikes and tests held-contract availability | Legacy dates without a validated spot series fail explicitly |
| Supplied pipeline identifies monthly expiries from a global maximum per month | Production pipeline continues to require a same-date, exact-expiry futures match | No inference from future-listed expiry calendars |
| Supplied pipeline treats 404s as holidays and misses weekend sessions | Unavailable archives remain unclassified; do not permanently cache missing responses; retain 1 February 2025 special session and existing calendar audit | Calendar audit must be extended explicitly for a new sample |
| Option-implied forward can differ from hedge futures | Added parity-vs-futures diagnostics; median absolute gap 1.84 bp, 95th percentile 6.37 bp | Small average basis is not proof of synchronized or executable prices |
| NaN prices could pass a minimum-price check | Explicit finite, positive checks for all three instruments | Missing held marks stop the run rather than fabricate a fill |
| IV solver could return its lower bound for a price outside the numerical bracket | Validate both numerical bracket endpoints, as well as economic bounds | Deep ITM/OTM IV remains poorly identified and may be missing |
| Empty trades, first-session predecessor and unknown hedge rules were brittle | Stable empty output schemas, required prior observation, explicit parameter/rule checks | Invalid input now raises an explanatory error |
| Three-trade bootstrap looked more informative than justified | Confidence interval suppressed for fewer than 20 trades | Twenty is only a suppression policy, not a guarantee of valid statistical inference |
| No unhedged control or execution-time comparison | Added identical-entry unhedged control and lagged next-close execution | These are retrospective stress checks, not an independent test |
| No rolling recalibration check | Added expanding monthly calibration; positions carry across test-month boundaries | Threshold remains 3 points in every fold; no extra independent trades are created |
| Forecast evaluation had no simple comparator | Added rolling-60 variance baseline on identical available dates | Overlapping five-day targets are dependent; no significance claim |
| Rate assumption not stressed | Recompute IV/signals at 3%, 6.5%, 10%, retain the original threshold, report trade counts | Fixed-rate scenarios are not point-in-time historical yields; strike choice remains fixed |
| Reporting capital and Sharpe could suggest implementability | Label all returns as illustrative per-unit results; explain zero-initial-wealth excess P&L and unmodelled collateral | No historical SPAN margin, lot rounding, bid/ask or statutory fee reconstruction |

## What the new evidence says

At the selected threshold, next-open net P&L is 159.22 points for implied delta and 165.80 for forecast delta. Next-close execution, still using previous-close decisions, gives 97.44 and 87.56 respectively. The ranking reverses. This changes both entry/exit prices and intraday exposure; it is an execution-convention stress test, not an estimate of actual slippage.

The same three trades without a futures hedge yield 147.99 points at opens. Thus positive straddle outcomes are not by themselves evidence that the volatility forecast or hedge was superior. The zero-threshold diagnostic has 21 trades, predominantly short volatility, and is a different trading policy; it cannot repair the selected policy's tiny sample.

The futures Monte Carlo at 1,008 rebalances has actual-hedge mean 3.76705 versus theoretical 3.76494 (standard error 0.00315). This validates the futures accounting under its own model, in addition to the existing stock replication.

EWMA test RMSE is 0.02471 versus 0.03451 for rolling-60 volatility; QLIKE is 0.16318 versus 0.21431. These descriptive comparisons assess five-session spot volatility, not maturity-matched option variance or statistically significant forecast superiority.

## Reproduce

Run `python run_project.py` and `python -m unittest discover -s tests -v`. Run with `--rebuild-data` if the original cached archives are available. New outputs include `futures_simulation.csv`, `parity_diagnostics.csv`, `execution_controls.csv`, `rate_sensitivity.csv`, `walk_forward.csv`, `walk_forward_daily_*.csv`, `forecast_benchmark.csv`, `greek_attribution_*.csv`, and `audit_summary.json` under `results/`.

## What we cannot repair with the supplied files

The new folder contains code, not an additional historical market dataset. Neither dataset supplies synchronized bid/ask quotes, order-book depth, historical margin requirements or complete point-in-time fee schedules. More models cannot manufacture this evidence. Longer independent observations, realistic execution and collateral constraints are needed before a tradability claim.

No new data download is required for the integrated study. For an extension, use official NSE derivatives archives and calendars, supply independently validated NIFTY spot history for legacy dates, and obtain historical contract specifications/fees and synchronized quotes. Do not treat Yahoo/FRED fallbacks or a different threshold selected after looking at results as a cure for missing evidence.

## Source verification

- NSE, official derivatives report page: https://www.nseindia.com/all-reports-derivatives . Legacy discontinuation/UDiFF transition: circular 62424, 12 June 2024; earlier overlapping-format notice: https://nsearchives.nseindia.com/content/circulars/INVG61787.pdf . The new module uses July 8 as a routing preference, not a claim that UDiFF did not exist earlier.
- Black (1976), *The pricing of commodity contracts*: https://doi.org/10.1016/0304-405X(76)90024-6 . Futures gains and premium-paid option pricing must be distinguished from financing a stock position.
- Ahmad & Wilmott (2005), Sections 3–4, remains the stock-model replication reference. The futures derivation and diagnostic simulations are extensions of this project.
