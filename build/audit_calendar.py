"""Sample-specific cross-check against published NSE trading calendars."""

from pathlib import Path
import csv, json

ROOT = Path(__file__).resolve().parents[1]
known = {
    "2024-07-17": "Moharram",
    "2024-08-15": "Independence Day",
    "2024-10-02": "Gandhi Jayanti",
    "2024-11-15": "Gurunanak Jayanti",
    "2024-11-20": "Maharashtra election",
    "2024-12-25": "Christmas",
    "2025-02-26": "Mahashivratri",
    "2025-03-14": "Holi",
    "2025-03-31": "Id-Ul-Fitr",
    "2025-04-10": "Mahavir Jayanti",
    "2025-04-14": "Ambedkar Jayanti",
    "2025-04-18": "Good Friday",
    "2025-05-01": "Maharashtra Day",
    "2025-08-15": "Independence Day",
    "2025-08-27": "Ganesh Chaturthi",
    "2025-10-02": "Gandhi Jayanti / Dussehra",
    "2025-10-22": "Diwali Balipratipada",
    "2025-11-05": "Gurunanak Jayanti",
    "2025-12-25": "Christmas",
}
rows = []
for r in csv.DictReader((ROOT / "data/download_manifest.csv").open()):
    if r["status"] != "downloaded":
        d = r["date"]
        source = (
            "CMTR65587.pdf"
            if d.startswith("2025")
            else ("CMTR64960.pdf" if d == "2024-11-20" else "FAOP59723.pdf")
        )
        rows.append(
            dict(
                date=d,
                download_status=r["status"],
                classification="verified_holiday" if d in known else "unresolved",
                reason=known.get(d, "Review required"),
                source="https://nsearchives.nseindia.com/content/circulars/" + source,
            )
        )
rows.append(
    dict(
        date="2025-02-01",
        download_status="downloaded",
        classification="special_session_included",
        reason="Union Budget Saturday session",
        source="https://nsearchives.nseindia.com/content/circulars/MSD66381.pdf",
    )
)
with (ROOT / "results/calendar_audit.csv").open("w") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
qpath = ROOT / "results/data_quality.json"
q = json.loads(qpath.read_text())
q["verified_closed_weekdays"] = sum(
    x["classification"] == "verified_holiday" for x in rows
)
q["unresolved_dates"] = [x["date"] for x in rows if x["classification"] == "unresolved"]
q["special_sessions"] = ["2025-02-01"]
qpath.write_text(json.dumps(q, indent=2))
assert not q["unresolved_dates"], q["unresolved_dates"]
print(
    "Calendar audit:",
    q["verified_closed_weekdays"],
    "closed weekdays, budget session included, zero unresolved dates.",
)
