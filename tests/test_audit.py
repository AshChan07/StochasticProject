import unittest
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
import pipeline_fixtures as fx
from data_pipeline import bhavcopy
from data_pipeline.forwards import parity_forward
from data_pipeline.iv import implied_vol
from src.pricing import black, iv
from src.robustness import simulate_futures, greek_step, attribution
from src.backtest import Market, run, positive_quotes
ROOT=Path(__file__).resolve().parents[1]

class AuditTests(unittest.TestCase):
    def test_schema_boundary_is_july(self):
        self.assertIn('historical',bhavcopy.url_for(date(2024,7,5)))
        self.assertIn('20240708',bhavcopy.url_for(date(2024,7,8)))

    def test_both_schema_normalizers(self):
        d=date(2023,12,14)
        a=bhavcopy.normalise(fx.legacy_zip(d)); b=bhavcopy.normalise(fx.udiff_zip(d))
        cols=['date','instrument','expiry','strike','opt_type','open','close']
        pd.testing.assert_frame_equal(a[cols],b[cols],check_dtype=False)
        self.assertEqual(set(a.instrument),{'FUTIDX','OPTIDX'})

    def test_parity_recovers_fixture_forward(self):
        d=date(2023,12,14); rows=bhavcopy.normalise(fx.udiff_zip(d))
        for expiry,g in rows[rows.instrument.eq('OPTIDX')].groupby('expiry'):
            tau=(expiry-pd.Timestamp(d)).days/365
            if tau <= 0: continue  # fixture uses a half-day expiry quote
            expected=fx.spot_on(d)*np.exp((fx.R-fx.Q)*tau)
            self.assertLess(abs(parity_forward(g,tau,fx.R)-expected),.1)

    def test_special_saturday(self):
        self.assertIn(date(2025,2,1),list(bhavcopy.weekdays(date(2025,1,31),date(2025,2,3))))

    def test_nan_quotes_are_not_executable(self):
        for prices in [(1,np.nan,2),(np.inf,2,3),(1,0,2),(1,-1,3)]:
            self.assertFalse(positive_quotes(*prices))
        self.assertTrue(positive_quotes(1,2,3))

    def test_black_pde_and_delta_discount(self):
        F,K,tau,r,v=103.,100.,.4,.065,.25
        eps=.01; dt=1e-5
        value,delta=black(F,K,tau,r,v)
        theta=(black(F,K,tau-dt,r,v)[0]-black(F,K,tau+dt,r,v)[0])/(2*dt)
        gamma=(black(F+eps,K,tau,r,v)[0]-2*value+black(F-eps,K,tau,r,v)[0])/eps**2
        self.assertAlmostEqual(float(theta+.5*v*v*F*F*gamma-r*value),0,places=5)
        # Put and call deltas differ by the discount factor, not by one.
        self.assertAlmostEqual(float(delta-black(F,K,tau,r,v,True)[1]),np.exp(-r*tau),places=10)

    def test_futures_replication_converges(self):
        a,target=simulate_futures(n=64,paths=5000)
        b,_=simulate_futures(n=512,paths=5000)
        self.assertLess(b[0].std(),.5*a[0].std())
        self.assertLess(abs(b[0].mean()-target),5*b[0].std()/np.sqrt(5000))

    def test_futures_equal_vol_same_hedge(self):
        a,target=simulate_futures(n=126,paths=3000,actual=.2)
        np.testing.assert_array_equal(a[0],a[1]);self.assertEqual(target,0)

    def test_greek_approximation_small_step(self):
        F,K,tau,r,v=103.,100.,.4,.065,.25
        for put in [False,True]:
            terms=greek_step(F,K,tau,r,v,put,.001,1e-7,1e-6)
            exact=black(F+.001,K,tau-1e-7,r,v+1e-6,put)[0]-black(F,K,tau,r,v,put)[0]
            self.assertLess(abs(exact-terms.sum()),1e-8)

    def test_independent_iv_solver(self):
        for put in [False,True]:
            price=black(103,100,.4,.065,.25,put)[0]
            self.assertAlmostEqual(float(implied_vol(price,103,100,.4,.065,not put)),float(iv(price,103,100,.4,.065,put)),places=9)

class HistoricalAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.m=Market(ROOT)

    def test_empty_trades_have_schema(self):
        d,t,met,e=run(self.m,'2025-07-01','2025-12-31',threshold=100)
        self.assertTrue(t.empty);self.assertIn('pnl',t);self.assertEqual(met['net_pnl'],0)
        self.assertEqual(list(e.columns), ['date','event'])

    def test_no_predecessor_rejected(self):
        with self.assertRaises(ValueError):run(self.m,'2024-07-08','2024-07-15')

    def test_invalid_configuration(self):
        for kwargs in [dict(rule='typo'),dict(execution='settle'),dict(rebalance=0)]:
            with self.assertRaises(ValueError):run(self.m,'2025-07-01','2025-12-31',**kwargs)

    def test_unhedged_control_same_trades(self):
        a,t,_,_=run(self.m,'2025-07-01','2025-12-31',threshold=0,rule='unhedged')
        _,u,_,_=run(self.m,'2025-07-01','2025-12-31',threshold=0)
        pd.testing.assert_frame_equal(t.drop(columns='pnl'),u.drop(columns='pnl'))
        self.assertEqual(a.futures_turnover.sum(),0);self.assertEqual(a.futures_pnl.sum(),0)
        schedule=pd.Series(.03,index=self.m.spot.loc['2025-07-01':'2025-12-31'].index)
        fixed,trades,_,_=run(self.m,'2025-07-01','2025-12-31',threshold=.03)
        rolling,_,_,_=run(self.m,'2025-07-01','2025-12-31',threshold_schedule=schedule)
        pd.testing.assert_frame_equal(fixed,rolling)
        greek=attribution(self.m,fixed,trades)
        self.assertTrue(greek.valid.all())
        np.testing.assert_allclose(greek[['delta','gamma','theta','vega','residual']].sum(axis=1),greek.option_pnl)
        self.assertAlmostEqual(greek.option_pnl.sum(),fixed.option_pnl.sum())

    def test_next_close_keeps_decision_time(self):
        _,t,_,_=run(self.m,'2025-07-01','2025-12-31',threshold=0,execution='close')
        for _,row in t.iterrows():
            prev=self.m.spot.index[self.m.spot.index.get_loc(row.entry_date)-1]
            self.assertEqual(row.entry_signal,self.m.panel.loc[prev,'signal'])

    def test_all_held_contracts_retained(self):
        _,t,_,_=run(self.m,'2025-07-01','2025-12-31',threshold=0)
        for _,row in t.iterrows():
            for day in self.m.spot.loc[row.entry_date:row.exit_date].index:
                c,p,f=self.m.quote(day,row.expiry,row.strike)
                self.assertTrue(positive_quotes(c.open,p.open,f.open))
