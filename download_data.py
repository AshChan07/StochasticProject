"""Download public NSE UDiFF files. Cache ZIPs and log every failed request."""

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse, subprocess, zipfile, hashlib, csv, datetime

ROOT = Path(__file__).resolve().parent


def fetch(day):
    name = f"BhavCopy_NSE_FO_0_0_0_{day:%Y%m%d}_F_0000.csv.zip"
    url = "https://archives.nseindia.com/content/fo/" + name
    dest = ROOT / "data/raw" / name
    if not (dest.exists() and zipfile.is_zipfile(dest)):
        tmp = dest.with_suffix(".part")
        p = subprocess.run(
            [
                "curl",
                "--http1.1",
                "-L",
                "-sS",
                "--max-time",
                "25",
                "--retry",
                "1",
                "-A",
                "Mozilla/5.0",
                "-o",
                str(tmp),
                "-w",
                "%{http_code}",
                url,
            ],
            capture_output=True,
            text=True,
        )
        if p.returncode or p.stdout != "200" or not zipfile.is_zipfile(tmp):
            tmp.unlink(missing_ok=True)
            return [str(day), url, "unavailable_" + p.stdout, "", p.stderr[:120]]
        tmp.replace(dest)
    return [
        str(day),
        url,
        "downloaded",
        hashlib.sha256(dest.read_bytes()).hexdigest(),
        "",
    ]


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--start", default="2024-07-08")
    p.add_argument("--end", default="2025-12-31")
    p.add_argument("--workers", type=int, default=3)
    a = p.parse_args()
    start = datetime.date.fromisoformat(a.start)
    end = datetime.date.fromisoformat(a.end)
    days = [
        start + datetime.timedelta(days=i)
        for i in range((end - start).days + 1)
        if (start + datetime.timedelta(days=i)).weekday() < 5
    ]
    special = datetime.date(2025, 2, 1)  # NSE budget-day session, circular MSD66381.
    if start <= special <= end:
        days = sorted(set(days + [special]))
    (ROOT / "data/raw").mkdir(parents=True, exist_ok=True)
    rows = []
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        for i, row in enumerate(pool.map(fetch, days)):
            rows.append(row)
            if i % 25 == 0:
                print(i + 1, "/", len(days), row[0], row[2], flush=True)
    with (ROOT / "data/download_manifest.csv").open("w") as f:
        w = csv.writer(f)
        w.writerow(["date", "source_url", "status", "sha256", "error"])
        w.writerows(rows)
    print(
        "Downloaded",
        sum(r[2] == "downloaded" for r in rows),
        "of",
        len(rows),
        "weekday requests; unavailable days require calendar review.",
        flush=True,
    )
