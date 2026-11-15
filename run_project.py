"""Run the full reproducible numerical study, without downloading by default."""

from pathlib import Path
import argparse, json
import os

ROOT = Path(__file__).resolve().parent

# Use a local matplotlib config dir so the script works from any extracted location
os.environ.setdefault(
    "MPLCONFIGDIR", str(ROOT / ".mplconfig")
)
(ROOT / ".mplconfig").mkdir(parents=True, exist_ok=True)

from src import data, simulation, backtest

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--rebuild-data", action="store_true")
    p.add_argument("--simulation-only", action="store_true")
    a = p.parse_args()
    # Ensure output directories exist
    (ROOT / "results/figures").mkdir(parents=True, exist_ok=True)
    slope = simulation.run(ROOT)
    print("Simulation convergence slope:", slope, flush=True)
    if not a.simulation_only:
        if (
            a.rebuild_data
            or not (ROOT / "data/clean/atm_panel.csv").exists()
            or not (ROOT / "data/clean/nifty_options_chain.csv.gz").exists()
        ):
            print(data.build(ROOT), flush=True)
        print(backtest.experiment(ROOT), flush=True)
