# Computed results

Data: 370 sessions, 222,520 monthly option rows, 1,110 futures rows.
Calendar: 19 unavailable weekday files match published holidays; the budget Saturday is included. No unresolved date gaps in the audited sample.

## Simulation
Known actual volatility 30%, implied 20%: theoretical discounted gain 3.780671; sample mean 3.783992, standard deviation 0.621769. Implied-volatility hedge mean 3.740430, standard deviation 1.854661. 20,000 paths. Convergence slope -0.495799.

## Historical test
Threshold 3 volatility points, chosen on October 2024–June 2025 calibration. Test July–December 2025. Three trades, all short straddles.

- implied delta: net 159.22 points; maximum drawdown 55.78; modeled costs 12.28; daily P&L Sharpe 1.63.
- forecast delta: net 165.80 points; maximum drawdown 65.70; modeled costs 14.31; daily P&L Sharpe 1.54.

These are per-unit research P&Ls, not executable account returns. Only three trades prevent strong inference. Full threshold diagnostics include 21 trades at threshold zero.

## Forecast evaluation
Forward targets use the following five close-to-close returns. Calibration targets crossing the split are excluded. Overlapping targets imply dependent forecast errors.
- test: 121 targets; volatility RMSE 0.024711 in annual decimal units; normalized QLIKE 0.163181.
- train: 179 targets; volatility RMSE 0.064152 in annual decimal units; normalized QLIKE 0.420581.

## Verification
14 automated tests passed. Pricing references, put-call parity, IV inversion, finite-difference delta, simulation convergence, lagged decisions, cost sensitivity and ledger identities are covered. See build/test_results.txt.

## Audit revision

The baseline next-open results above are unchanged. Next-close fills using lagged decisions reverse the selected-threshold ranking: 97.44 points implied vs 87.56 forecast. The same next-open entries unhedged yield 147.99 points. The three-trade bootstrap interval is now suppressed. See `execution_controls.csv`.

Futures replication at 1,008 rebalances: actual-hedge mean 3.76705, theory 3.76494, standard error 0.00315. EWMA test RMSE 0.02471 vs rolling-60 0.03451; QLIKE 0.16318 vs 0.21431. Parity basis median absolute 1.84 bp, 95th percentile 6.37 bp. All added empirical checks are retrospective; no new independent validation claim is made. Full findings: `docs/AUDIT_AND_INTEGRATION.md`.
