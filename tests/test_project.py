import unittest, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "build/matplotlib"))
import numpy as np, pandas as pd
from src.pricing import bs, black, iv
from src.simulation import simulate
from src.backtest import Market, run, ledger_increment


class PricingTests(unittest.TestCase):
    def test_bs_reference(self):
        self.assertAlmostEqual(
            float(bs(100, 100, 1, 0.05, 0.2)[0]), 10.450583572, places=7
        )

    def test_put_call_parity(self):
        c, _ = black(104, 100, 0.4, 0.06, 0.3)
        p, _ = black(104, 100, 0.4, 0.06, 0.3, True)
        self.assertAlmostEqual(float(c - p), np.exp(-0.06 * 0.4) * 4, places=9)

    def test_futures_delta(self):
        eps = 0.001
        c, d = black(104, 100, 0.4, 0.06, 0.3)
        fd = (
            black(104 + eps, 100, 0.4, 0.06, 0.3)[0]
            - black(104 - eps, 100, 0.4, 0.06, 0.3)[0]
        ) / (2 * eps)
        self.assertAlmostEqual(float(d), float(fd), places=7)

    def test_iv_round_trip(self):
        for put in [False, True]:
            for k in [85, 100, 115]:
                p, _ = black(103, k, 0.25, 0.065, 0.24, put)
                self.assertAlmostEqual(
                    float(iv(p, 103, k, 0.25, 0.065, put)), 0.24, places=8
                )

    def test_invalid_price_not_forced(self):
        self.assertTrue(np.isnan(iv(200, 100, 100, 1, 0.05)))

    def test_expiry(self):
        self.assertEqual(float(bs(110, 100, 0, 0.05, 0.2)[0]), 10)


class SimulationTests(unittest.TestCase):
    def test_equal_vol_fair_price(self):
        x, target = simulate(paths=5000, actual=0.2, implied=0.2, mu=0.05)
        self.assertTrue(np.array_equal(x[0], x[1]))
        self.assertEqual(target, 0)
        self.assertLess(abs(x[0].mean()), 4 * x[0].std() / np.sqrt(5000))

    def test_replication_and_convergence(self):
        x, target = simulate(n=126, paths=4000)
        y, _ = simulate(n=504, paths=4000)
        self.assertLess(y[0].std(), 0.65 * x[0].std())
        self.assertLess(abs(y[0].mean() - target), 4 * y[0].std() / np.sqrt(4000))

    def test_cash_and_futures(self):
        c, i, f = ledger_increment(-100, 0.5, 100, 110, 3, 0.05)
        self.assertAlmostEqual(f, 5)
        self.assertAlmostEqual(c, -100 * np.exp(0.05 * 3 / 365) + 5)

    def test_drift_invariance_actual_vol(self):
        pnl_pos, target = simulate(paths=3000, actual=0.3, implied=0.2, mu=0.25, seed=42)
        pnl_neg, _ = simulate(paths=3000, actual=0.3, implied=0.2, mu=-0.25, seed=42)
        self.assertAlmostEqual(float(pnl_pos[0].mean()), target, delta=0.15)
        self.assertAlmostEqual(float(pnl_neg[0].mean()), target, delta=0.15)


class HistoricalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.market = Market(ROOT)

    def test_dates_and_coverage(self):
        self.assertIn(pd.Timestamp("2025-02-01"), self.market.spot.index)
        self.assertFalse(self.market.options.index.duplicated().any())

    def test_identical_entries_and_reconciliation(self):
        d, t, _, _ = run(
            self.market, "2025-07-01", "2025-12-31", threshold=0, rule="implied"
        )
        e, u, _, _ = run(
            self.market, "2025-07-01", "2025-12-31", threshold=0, rule="forecast"
        )
        pd.testing.assert_frame_equal(t.drop(columns="pnl"), u.drop(columns="pnl"))
        self.assertAlmostEqual(d.net_pnl.sum(), t.pnl.sum(), places=7)
        self.assertTrue(
            np.allclose(d.net_pnl, d.option_pnl + d.futures_pnl + d.financing - d.cost)
        )

    def test_cost_sensitivity(self):
        _, _, a, _ = run(
            self.market, "2025-07-01", "2025-12-31", threshold=0, cost_mult=0
        )
        _, _, b, _ = run(
            self.market, "2025-07-01", "2025-12-31", threshold=0, cost_mult=2
        )
        self.assertEqual(a["trades"], b["trades"])
        self.assertGreater(a["net_pnl"], b["net_pnl"])

    def test_future_signals_do_not_change_past(self):
        m = self.market
        baseline, _, _, _ = run(m, "2025-07-01", "2025-12-31", threshold=0)
        old = m.panel.copy()
        m.panel.loc[m.panel.index > "2025-09-01", "signal"] *= -100
        changed, _, _, _ = run(m, "2025-07-01", "2025-12-31", threshold=0)
        m.panel = old
        pd.testing.assert_frame_equal(
            baseline[baseline.date <= "2025-09-01"],
            changed[changed.date <= "2025-09-01"],
        )

    def test_previous_close_drives_entry(self):
        _, t, _, _ = run(self.market, "2025-07-01", "2025-12-31", threshold=0)
        for _, row in t.iterrows():
            idx = self.market.spot.index.get_loc(row.entry_date)
            prev = self.market.spot.index[idx - 1]
            self.assertLess(prev, row.entry_date)
            self.assertAlmostEqual(
                row.entry_signal, self.market.panel.loc[prev, "signal"]
            )

    def test_garch_forecasting(self):
        params = self.market.garch_params
        self.assertGreater(params["omega"], 0)
        self.assertGreater(params["alpha"], 0)
        self.assertGreater(params["beta"], 0)
        self.assertLess(params["alpha"] + params["beta"], 1.0)
        self.assertTrue((self.market.garch_forecast > 0).all())

    def test_multi_position_capacity(self):
        d1, t1, m1, _ = run(
            self.market, "2025-07-01", "2025-12-31", threshold=0.03, max_positions=1
        )
        d2, t2, m2, _ = run(
            self.market, "2025-07-01", "2025-12-31", threshold=0.03, max_positions=2
        )
        self.assertGreaterEqual(len(t2), len(t1))
        self.assertAlmostEqual(d2.net_pnl.sum(), t2.pnl.sum(), places=7)
        self.assertTrue(
            np.allclose(d2.net_pnl, d2.option_pnl + d2.futures_pnl + d2.financing - d2.cost)
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
