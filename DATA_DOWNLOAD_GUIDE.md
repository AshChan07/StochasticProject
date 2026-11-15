# Data sources and download instructions

## Data already downloaded
The package contains cleaned NSE NIFTY options, futures and underlying closes for 8 July 2024–31 December 2025. No additional market download is needed to reproduce the included experiment. Raw exchange ZIPs remain in data/raw on the original workspace, but are excluded from the compact submission archive. data/download_manifest.csv records source URLs, availability and SHA-256 checksums.

## Download the source files again
Official NSE page: https://www.nseindia.com/all-reports-derivatives
Choose Historical Reports, select the date, and download **F&O-UDiFF Common Bhavcopy Final (zip)**. This one file contains both NIFTY options and futures. Do not choose the cash-equity bhavcopy.

Direct example: https://archives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_20250102_F_0000.csv.zip
General URL: https://archives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_YYYYMMDD_F_0000.csv.zip

Run `python download_data.py` from the project folder. ZIPs go into data/raw. If direct download is blocked, download in a normal browser and place the original ZIPs there. Then run `python run_project.py --rebuild-data`. Do not rename ZIPs: the parser verifies the date in the filename against the records.

The code deliberately supports the post-July-2024 UDiFF sample. The context's assertion that the legacy format ended on 1 January 2024 was incorrect. Earlier data needs a legacy parser and a separate calendar audit. Do not merely extend the start date into 2019.

## Calendar checks
Unavailable weekdays are listed separately from genuine zero-volume instruments. Standard holidays are checked against NSE's calendar circulars; November 20, 2024 was an additional election holiday. The special Saturday session on February 1, 2025 is included. Weekday Muhurat sessions are retained when an archive exists. This is a sample-specific calendar; extending the sample requires checking additional special sessions.
- 2024 F&O calendar: https://nsearchives.nseindia.com/content/circulars/FAOP59723.pdf
- 2025 calendar: https://nsearchives.nseindia.com/content/circulars/CMTR65587.pdf
- Election holiday: https://nsearchives.nseindia.com/content/circulars/CMTR64960.pdf
- Budget session: https://nsearchives.nseindia.com/content/circulars/MSD66381.pdf

## Optional data for a more realistic extension
These are not necessary to reproduce the current results:
1. **Time-stamped option and futures bid/ask quotes** from NSE Data & Analytics or a licensed market-data vendor. Required for synchronized execution, realistic spreads and intraday hedging. Daily OHLC does not establish simultaneous executable prices.
   https://www.nseindia.com/static/market-data/real-time-data-subscription
2. **Historical Treasury-bill yields**, from RBI Database on Indian Economy: https://data.rbi.org.in/ . Select the relevant 91-day Treasury-bill series and record frequency, units and publication dates. The current study uses an explicitly assumed flat 6.5% annual rate.
3. **India VIX historical values**, from NSE: https://www.nseindia.com/reports-indices-historical-vix . VIX is optional context, not a substitute for the option contracts actually traded.
4. **Historical lot sizes, margin rules and taxes/fees**, from NSE contract files, circulars and the relevant broker's historical charges. The current study uses one straddle unit and fractional futures, with illustrative all-in cost proxies. It does not claim exact historical STT/brokerage modeling.

## Core paper
Ahmad & Wilmott, “Which Free Lunch Would You Like Today, Sir?: Delta Hedging, Volatility Arbitrage and Optimal Portfolios”, Wilmott Magazine, November 2005, pp.64–79.
Publisher: https://www.wilmott.com/which-free-lunch-would-you-like-today-sir-delta-hedging-volatility-arbitrage-and-optimal-portfolios-riaz-ahmad-and-paul-wilmott/
Academic paper mirror: https://citeseerx.ist.psu.edu/document?doi=22554822cff90a56962f8ce4327587e86a42f1dc&repid=rep1&type=pdf


## Integrated parser revision

Joel’s legacy/UDiFF parser is now integrated into `src/data.py`; existing raw ZIPs rebuild the same empirical sample. Legacy parsing alone does not supply missing spot history, calendars, synchronized quotes or margins. The optional `data_pipeline.bhavcopy` helpers prefer legacy URLs before 8 July 2024 and UDiFF thereafter; formats overlapped earlier. Missing archives are not automatically holidays. Only the special weekend session in the completed sample is explicitly included; review official calendars before extending dates. The project does not use Yahoo or FRED fallback data in the submitted results.
