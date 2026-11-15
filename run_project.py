"""Run the full reproducible numerical study, without downloading by default."""

from pathlib import Path
import argparse, json, hashlib, platform
from importlib.metadata import version
import os

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(__file__).resolve().parent / "build/matplotlib")
)
from src import data, simulation, backtest, robustness

ROOT = Path(__file__).resolve().parent
if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--rebuild-data", action="store_true")
    p.add_argument("--simulation-only", action="store_true")
    a = p.parse_args()
    (ROOT / "results/figures").mkdir(parents=True, exist_ok=True)
    slope = simulation.run(ROOT)
    print("Simulation convergence slope:", slope, flush=True)
    if not a.simulation_only:
        if (
            a.rebuild_data
            or not (ROOT / "data/clean/nifty_options_chain.csv.gz").exists()
        ):
            print(data.build(ROOT), flush=True)
        print(backtest.experiment(ROOT), flush=True)
        robustness.run_diagnostics(ROOT)
        manifest = [dict(file=str(f.relative_to(ROOT)), bytes=f.stat().st_size,
                         sha256=hashlib.sha256(f.read_bytes()).hexdigest())
                    for f in sorted((ROOT / "data/clean").glob("*")) if f.is_file()]
        (ROOT / "results/clean_data_manifest.json").write_text(json.dumps(manifest, indent=2))
    versions = {name: version(name) for name in ["numpy", "pandas", "scipy", "matplotlib"]}
    versions.update(python=platform.python_version(), platform=platform.platform())
    (ROOT / "results/runtime_versions.json").write_text(json.dumps(versions, indent=2))
