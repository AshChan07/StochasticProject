"""Retrospective diagnostics, never an additional untouched validation set."""
import json
import numpy as np
import pandas as pd
from .pricing import black, iv
from .backtest import Market, run


def simulate_futures(n=252, paths=10000, actual=.3, implied=.2, seed=244, r=.05, mu=.05):
    """Premium-paid option + zero-value futures, with variation margin in cash.

    dF/F = mu dt + actual dB under P. Under Q the futures drift is zero.
    The terminal payoff is max(F_T-K,0); no futures principal is financed.
    """
    rng = np.random.default_rng(seed)
    dt = 1/n
    F = np.full(paths, 100.)
    premium = float(black(100, 100, 1, r, implied)[0])
    cash = np.full((2, paths), -premium)
    vols = [actual, implied]
    hedge = np.stack([-black(F,100,1,r,v)[1] for v in vols])
    for j in range(n):
        new = F*np.exp((mu-.5*actual**2)*dt+actual*np.sqrt(dt)*rng.standard_normal(paths))
        cash = cash*np.exp(r*dt)+hedge*(new-F)
        F = new
        if j < n-1:
            hedge = np.stack([-black(F,100,1-(j+1)*dt,r,v)[1] for v in vols])
    wealth = (cash+np.maximum(F-100,0))*np.exp(-r)
    target = float(black(100,100,1,r,actual)[0])-premium
    return wealth, target


def greek_step(F, K, tau, rate, vol, put, dF, elapsed, dv):
    """First/second order Black-76 Taylor terms at the earlier mark.

    Vol change is observed AFTER the interval, used for explanation only.
    Residual includes vanna, volga, higher orders and quote/model effects.
    """
    value, delta = black(F,K,tau,rate,vol,put)
    z=(np.log(F/K)+.5*vol**2*tau)/(vol*np.sqrt(tau))
    density=np.exp(-z*z/2)/np.sqrt(2*np.pi)
    gamma=np.exp(-rate*tau)*density/(F*vol*np.sqrt(tau))
    vega=np.exp(-rate*tau)*F*density*np.sqrt(tau)
    theta=rate*value-.5*vol**2*F**2*gamma
    return np.array([delta*dF,.5*gamma*dF*dF,theta*elapsed,vega*dv],float)


def attribution(m, daily, trades, rate=.065):
    rows=[]
    for _, trade in trades.iterrows():
        dates=m.spot.loc[trade.entry_date:trade.exit_date].index
        for a,b in zip(dates[:-1], dates[1:]):
            ac,ap,af=m.quote(a,trade.expiry,trade.strike)
            bc,bp,bf=m.quote(b,trade.expiry,trade.strike)
            tau=(trade.expiry-a).days/365
            later_tau=(trade.expiry-b).days/365
            total=np.zeros(4); valid=True
            for x,y,put in [(ac,bc,False),(ap,bp,True)]:
                oldvol=float(iv(x.open,af.open,trade.strike,tau,rate,put))
                newvol=float(iv(y.open,bf.open,trade.strike,later_tau,rate,put))
                if not np.isfinite([oldvol,newvol]).all():
                    valid=False;break
                total+=trade.direction*greek_step(af.open,trade.strike,tau,rate,oldvol,put,bf.open-af.open,(b-a).days/365,newvol-oldvol)
            exact=float(trade.direction*(bc.open+bp.open-ac.open-ap.open))
            if not valid:total[:]=np.nan
            rows.append(dict(date=b,trade_id=trade.trade_id,delta=total[0],gamma=total[1],theta=total[2],vega=total[3],residual=exact-total.sum(),option_pnl=exact,valid=valid))
    return pd.DataFrame(rows)


def run_diagnostics(root):
    out=root/'results'
    m=Market(root)
    conf=json.loads((out/'experiment.json').read_text()); k=conf['selected_threshold']
    sims=[]
    for n in [52,252,1008]:
        x,target=simulate_futures(n=n)
        for j,rule in enumerate(['actual','implied']):
            sims.append(dict(rebalances=n,rule=rule,paths=x.shape[1],mean=x[j].mean(),std=x[j].std(ddof=1),se=x[j].std(ddof=1)/np.sqrt(x.shape[1]),target=target))
    pd.DataFrame(sims).to_csv(out/'futures_simulation.csv',index=False)
    cases=[]
    # No threshold is chosen from these comparisons.
    for threshold in [k,0.]:
        for execution in ['open','close']:
            for rule in ['unhedged','implied','forecast']:
                _,_,metrics,_=run(m,'2025-07-01','2025-12-31',threshold=threshold,rule=rule,execution=execution)
                cases.append(metrics)
    pd.DataFrame(cases).to_csv(out/'execution_controls.csv',index=False)
    # Re-estimate historical IV at each assumed rate, keeping the original
    # threshold frozen. A rate change may change entry decisions; report counts.
    rates=[]
    original_options=m.options.copy();original_panel=m.panel.copy()
    for rate in [.03,.065,.10]:
        o=original_options.reset_index(); tau=(o.expiry-o.date).dt.days/365
        o['iv']=iv(o.close,o.futures_close,o.strike,tau,rate,o.opt_type.eq('PE'))
        m.options=o.set_index(['date','expiry','strike','opt_type']).sort_index()
        m.panel=original_panel.copy()
        for date,sig in m.panel.iterrows():
            c,p,_=m.quote(date,sig.expiry,sig.strike)
            m.panel.loc[date,['iv_call','iv_put','implied_vol','signal']]=[c.iv,p.iv,(c.iv+p.iv)/2,sig.forecast_vol-(c.iv+p.iv)/2]
        for rule in ['implied','forecast']:
            _,_,met,_=run(m,'2025-07-01','2025-12-31',threshold=k,rule=rule,r=rate)
            rates.append(dict(rate=rate,**met))
    pd.DataFrame(rates).to_csv(out/'rate_sensitivity.csv',index=False)
    m.options=original_options;m.panel=original_panel
    # Six disjoint monthly test folds, expanding calibration strictly before each.
    folds=[]
    schedule=pd.Series(index=m.spot.loc["2025-07-01":"2025-12-31"].index,dtype=float)
    selections=[]
    for month in pd.date_range('2025-07-01','2025-12-01',freq='MS'):
        train_end=month-pd.Timedelta(days=1); test_end=month+pd.offsets.MonthEnd(0)
        scores=[]
        for candidate in [0.,.01,.02,.03]:
            metrics=[run(m,'2024-10-07',str(train_end.date()),threshold=candidate,rule=rule)[2] for rule in ['implied','forecast']]
            if min(x['trades'] for x in metrics)>=10:
                scores.append((np.mean([x['net_pnl'] for x in metrics]),candidate))
        selected=max(scores,key=lambda x:x[0])[1] if scores else .02
        schedule.loc[str(month.date()):str(test_end.date())]=selected
        selections.append(dict(train_end=str(train_end.date()),test_start=str(month.date()),test_end=str(test_end.date()),threshold=selected))
    for rule in ['implied','forecast']:
        daily,trades,_,_=run(m,'2025-07-01','2025-12-31',rule=rule,threshold_schedule=schedule)
        daily.to_csv(out/f'walk_forward_daily_{rule}.csv',index=False)
        for selection in selections:
            d=daily[daily.date.between(selection['test_start'],selection['test_end'])]
            t=trades[trades.exit_date.between(selection['test_start'],selection['test_end'])]
            folds.append(dict(**selection,rule=rule,sessions=len(d),completed_trades=len(t),net_pnl=d.net_pnl.sum(),cost=d.cost.sum()))
    pd.DataFrame(folds).to_csv(out/'walk_forward.csv',index=False)
    # Return predictions assessed against lag-only rolling-60 variance benchmark.
    returns=np.log(m.spot.close).diff()
    forecast=pd.read_csv(out/'forecast_evaluation.csv',parse_dates=['date']).set_index('date')
    forecast['rolling60_vol']=returns.pow(2).rolling(60).mean().mul(252).pow(.5)
    forecasts=[]
    for sample,g in forecast.dropna().groupby('sample'):
        for method in ['forecast_vol','rolling60_vol']:
            pred=g[method]**2; target=g.future_realized_vol_5d**2
            forecasts.append(dict(sample=sample,method=method,n=len(g),rmse_vol=np.sqrt(((g[method]-g.future_realized_vol_5d)**2).mean()),qlike=(target/pred-np.log(target/pred)-1).mean()))
    pd.DataFrame(forecasts).to_csv(out/'forecast_benchmark.csv',index=False)
    for rule in ['implied','forecast']:
        d,t,_,_=run(m,'2025-07-01','2025-12-31',threshold=k,rule=rule)
        attribution(m,d,t).to_csv(out/f'greek_attribution_{rule}.csv',index=False)
    # Independent IV inversion implementation from Joel's module, sampled deterministically.
    from data_pipeline.iv import implied_vol
    sample=m.options.reset_index().query('iv == iv').iloc[::100].copy()
    sig=implied_vol(sample.close,sample.futures_close,sample.strike,sample['T'],.065,sample.opt_type.eq('CE'))
    audit=dict(iv_crosscheck_n=len(sample),iv_max_absolute_difference=float(np.nanmax(abs(sig-sample.iv))),
        basis_median_abs_bps=None,interpretation='All added analyses are retrospective robustness checks on previously inspected data; not new independent confirmation.')
    parity=out/'parity_diagnostics.csv'
    if parity.exists():
        q=pd.read_csv(parity).basis_bps.dropna();audit.update(basis_median_abs_bps=float(q.abs().median()),basis_p95_abs_bps=float(q.abs().quantile(.95)))
    (out/'audit_summary.json').write_text(json.dumps(audit,indent=2))
    print(audit)
