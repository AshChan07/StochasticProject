# Theory and viva guide

## Scope of the replication
We reproduce the constant-volatility single-option hedging comparison in Sections 3–4 of Ahmad and Wilmott (2005). We do not reproduce the later portfolio-optimization or utility-maximization sections. The NIFTY experiment is an original empirical adaptation, not a replication of the paper's market sample.

## Three different volatilities
- Actual sigma: the diffusion coefficient in the data-generating GBM. Known only in the simulation.
- Implied sigma_i: the volatility that makes a pricing formula equal an observed option premium.
- Hedge sigma_h: the volatility inserted into the delta formula. In historical work, the forecast is an estimate and cannot stand in for known actual volatility in a guarantee.

## Derivation, with financing explicitly defined
For a non-dividend-paying stock under the physical measure, dS = mu S dt + sigma S dW.
An option marked at constant implied volatility has value V_i(S,t). Its PDE is
V_t + r S V_S + (sigma_i^2 / 2) S^2 V_SS - r V = 0.
Write delta_i = V_S and gamma_i = V_SS. Hold one long option, h = -delta_h shares, and cash C. Wealth is W = V_i - delta_h S + C. Initially C_0 = -V_i(0) + delta_h(0) S_0 so W_0 = 0. Self-financing means stock adjustments are paid from cash.

Ito gives dV_i = V_t dt + delta_i dS + (sigma^2 / 2) S^2 gamma_i dt.
Thus dW = dV_i - delta_h dS + r C dt. Substitute C = W - V_i + delta_h S, and then the pricing PDE:

dW - rW dt = 0.5 (sigma^2 - sigma_i^2) S^2 gamma_i dt
             + (delta_i - delta_h) [(mu-r) S dt + sigma S dW_B].

Here W_B denotes Brownian motion; W denotes portfolio wealth. Discounted wealth obeys d(exp(-rt) W) = exp(-rt) times the right-hand side. Calling the right-hand side simply 'dP&L' without identifying financing or discounting can hide the rW term.

### Known actual-volatility hedge
If delta_h is calculated with sigma, the hedge replicates the option priced at actual volatility. At expiry both pricing formulas have the same payoff. Under continuous trading, constant parameters and no costs:
exp(-rT) W_T = V(S_0,0;sigma) - V(S_0,0;sigma_i).
This is path-independent at expiry. Intermediate market marks can fluctuate. With discrete hedging the identity becomes an approximation with random replication error.

### Constant implied-volatility hedge
If delta_h = delta_i, the explicit Brownian term in discounted wealth cancels:
exp(-rT) W_T = 0.5 (sigma^2 - sigma_i^2) integral_0^T exp(-rt) S_t^2 gamma_i(S_t,t) dt.
For a long vanilla option gamma is nonnegative. Under those assumptions the instantaneous discounted gain has the sign of sigma^2 - sigma_i^2. Its magnitude remains random because S and gamma depend on the path. 'No explicit dW term' does not mean a deterministic terminal outcome.

### What breaks in historical markets?
Actual volatility is unknown and can vary. Market implied volatility moves and has a smile. Mark-to-market changes then contain vega and other terms. Daily trading leaves residual risk; costs and quote timing also matter. A 5-session straddle trade is not the hold-to-expiry call experiment. Historical conclusions are therefore empirical comparisons, not proofs of arbitrage.

## Black-76 and futures
Using matched-expiry futures F as a forward proxy avoids estimating a dividend yield. For deterministic rates, price a European call as exp(-r tau)[F N(d1)-K N(d2)], with d1=[log(F/K)+0.5 v^2 tau]/(v sqrt(tau)) and d2=d1-v sqrt(tau). The put follows parity.
The derivative with respect to the futures price is exp(-r tau)N(d1) for a call and exp(-r tau)[N(d1)-1] for a put. The hedge for a signed straddle q is minus q times the sum of those two derivatives. The two implied volatilities can differ in the historical implementation.
Unlike stock, a futures position does not require paying F upfront. Its marked gain is h times the price change. We approximate variation margin by crediting the opening-to-opening gain to cash at each observation. Exact intraday settlement and margin funding are outside the experiment.

## Exact discrete ledger
Simulation (stock): start with C=-option_price-h*S. Accrue C at r over dt. Generate S_new using the exact GBM transition. A hedge adjustment from h_old to h_new changes cash by -(h_new-h_old)*S_new. At expiry, wealth=payoff+h*S+C. Discount by exp(-rT).

Historical (futures): start with C=-q*(call_open+put_open)-entry_cost. A new observation adds C*(exp(r*dt)-1) and h_old*(F_new-F_old) to cash. Changing futures quantity costs fees/slippage but no futures principal. Marked wealth is C+q*(call_open+put_open). At exit sell the option position, close the futures quantity, and deduct costs. The sum of daily net gains equals the sum of completed trade P&Ls.

## Forecast and causality
Use NIFTY close log returns. Seed variance with the first 60 squared returns. Thereafter v_t=0.94*v_(t-1)+0.06*return_t^2. Forecast annual volatility=sqrt(252*v_t). This is a flat conditional variance forecast across the holding horizon, not a guarantee.
At yesterday's close choose an eligible monthly expiry, nearest liquid strike, direction, and hedge quantity. Execute at today's recorded opening prices. Subsequent hedge quantities also use yesterday's close. No current-day closing data or volume is used to decide an opening trade. Opening quotes across instruments are not synchronous, so fills remain an idealized EOD-data proxy.

## Likely viva questions
1. Why does gamma appear? Ito's quadratic-variation term contributes 0.5*sigma^2*S^2*gamma*dt, and the pricing PDE subtracts the corresponding implied-variance term.
2. Why are P and Q different? Paths and empirical returns describe the physical measure P. Pricing uses risk-neutral expectations Q. Changing measure changes the drift, not the diffusion coefficient in this model.
3. Why a straddle? It concentrates exposure to volatility through a call and put at the same strike and expiry. Its delta is not generally exactly zero.
4. Is implied volatility a physical forecast? Not necessarily. Prices also reflect risk premia, supply/demand, and model assumptions.
5. Why two implied volatilities? Real call and put quotes may be asynchronous or have carry/model discrepancies. Each leg's own implied volatility reproduces its observed premium under the chosen futures proxy.
6. Why could the forecast hedge have higher P&L? It changes directional exposure and costs. A gain difference is not proof of a better volatility forecast.
7. How do you prevent look-ahead? Chronological threshold calibration, lagged signals and deltas, fixed contract identifiers, and no use of future realized volatility for entries.
8. Are returns per lot? No. They are per one index unit of a straddle with fractional futures. Multiply by a valid common lot size only after accounting for actual contract rules. This study does not enforce exchange lot or margin constraints.
9. What does Sharpe measure here? Annualized mean daily incremental P&L divided by its standard deviation. Normalizing both by a fixed reporting capital leaves the ratio unchanged. The short sample and serial dependence limit its interpretation.
10. Why use an assumed rate and costs? To keep the experiment reproducible without inventing a statutory schedule. Their levels are disclosed and cost sensitivity is reported.
11. Why does equal actual/implied volatility not give exactly zero P&L on every simulated path? Discrete rebalancing produces error even when the option is correctly priced.
12. Does an all-positive simulated sample prove arbitrage in practice? No. It is conditional on model assumptions, selected parameters, and a finite simulation sample.
13. What changed from the proposal? The implemented scope uses July 2024–December 2025, EWMA, a five-session holding period, fixed per-unit sizing, and simple all-in cost proxies. GARCH, VIX, Heston, fixed-vega sizing, and Greek attribution are unimplemented extensions.
14. Why fixed contract tracking? Replacing a held strike by each day's ATM strike would introduce hidden trades and invalidate P&L.
15. What is the strongest conclusion? The simulation validates the theoretical difference between terminal replication risk and path-dependent gains. The historical study tests how a practical forecast hedge behaves under explicitly simplified assumptions.

## Sources
Ahmad & Wilmott (2005), Wilmott Magazine, November, pp.64–79. Paper URL: https://citeseerx.ist.psu.edu/document?doi=22554822cff90a56962f8ce4327587e86a42f1dc&repid=rep1&type=pdf
Black (1976), The Pricing of Commodity Contracts, Journal of Financial Economics 3, 167–179.
Shreve (2004), Stochastic Calculus for Finance II, Chapters 4–5.
J.P. Morgan/Reuters (1996), RiskMetrics Technical Document, 4th edition (EWMA convention).
