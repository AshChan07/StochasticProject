"""Generate a four-page report from the saved experiment results."""

from pathlib import Path
import csv, json, re
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Image,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables"
OUT.mkdir(exist_ok=True)


def rows(name):
    with (ROOT / "results" / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


met = rows("test_metrics.csv")
sim = rows("simulation_summary.csv")
conf = json.loads((ROOT / "results/experiment.json").read_text(encoding="utf-8"))
dq = json.loads((ROOT / "results/data_quality.json").read_text(encoding="utf-8"))
sens = rows("test_threshold_sensitivity.csv")
costs = rows("sensitivity.csv")
fm = rows("forecast_metrics.csv")


def f(x, n=2):
    return f"{float(x):,.{n}f}"


fontroot = Path("/System/Library/Fonts/Supplemental")
if (fontroot / "Arial.ttf").exists():
    pdfmetrics.registerFont(TTFont("Body", str(fontroot / "Arial.ttf")))
    pdfmetrics.registerFont(TTFont("BodyBold", str(fontroot / "Arial Bold.ttf")))
    pdfmetrics.registerFontFamily(
        "Body", normal="Body", bold="BodyBold", italic="Body", boldItalic="BodyBold"
    )
else:
    from reportlab.pdfbase.pdfmetrics import Font

    pdfmetrics.registerFont(Font("Body", "Helvetica", "WinAnsiEncoding"))
    pdfmetrics.registerFont(Font("BodyBold", "Helvetica-Bold", "WinAnsiEncoding"))
    pdfmetrics.registerFontFamily(
        "Body", normal="Body", bold="BodyBold", italic="Body", boldItalic="BodyBold"
    )
styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="BodyA",
        fontName="Body",
        fontSize=9.7,
        leading=13.4,
        spaceAfter=6,
        textColor=colors.HexColor("#20303f"),
    )
)
styles.add(
    ParagraphStyle(
        name="HeadA",
        fontName="BodyBold",
        fontSize=14,
        leading=18,
        spaceBefore=8,
        spaceAfter=7,
        textColor=colors.HexColor("#126c75"),
    )
)
styles.add(
    ParagraphStyle(
        name="TitleA",
        fontName="BodyBold",
        fontSize=23,
        leading=27,
        spaceAfter=10,
        textColor=colors.HexColor("#15304a"),
    )
)
styles.add(
    ParagraphStyle(
        name="SmallA", fontName="Body", fontSize=8, leading=10.5, spaceAfter=5
    )
)
styles.add(
    ParagraphStyle(
        name="EqA",
        fontName="Body",
        fontSize=10,
        leading=14,
        spaceBefore=4,
        spaceAfter=8,
        leftIndent=8,
    )
)
styles.add(
    ParagraphStyle(
        name="CodeA",
        fontName="Courier",
        fontSize=8,
        leading=10.5,
        backColor=colors.HexColor("#f3f6f8"),
        leftIndent=6,
        rightIndent=6,
        spaceBefore=3,
        spaceAfter=4,
    )
)
story = []
source = []


def para(s, sty="BodyA"):
    s = re.sub(r"&(?!amp;|lt;|gt;|quot;|#)", "&amp;", s)
    story.append(Paragraph(s, styles[sty]))
    source.append(s)


def codeblock(s):
    story.append(Preformatted(s, styles["CodeA"]))
    source.append(f"```bash\n{s}\n```")


def head(s):
    para(s, "HeadA")


def table(data, widths):
    t = Table(
        [
            [
                Paragraph(
                    re.sub(r"&(?!amp;|lt;|gt;|quot;|#)", "&amp;", str(x)),
                    styles["SmallA"],
                )
                for x in row
            ]
            for row in data
        ],
        colWidths=widths,
        hAlign="LEFT",
    )
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5f0f1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#126c75")),
                ("LINEBELOW", (0, -1), (-1, -1), 0.4, colors.HexColor("#b0bdc5")),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 6))
    source.extend([" | ".join(map(str, row)) for row in data])


def img(name, w, h, caption):
    story.append(Image(str(ROOT / "results/figures" / name), width=w, height=h))
    para(caption, "SmallA")


def page():
    story.append(PageBreak())
    source.append("\n--- PAGE BREAK ---\n")


para("Volatility Arbitrage and Delta Hedging on NIFTY Index Options", "TitleA")
para(
    "MAC F244 · Stochastic Calculus and Application to Finance · November 2026",
    "SmallA",
)
para(
    "Arnav Kulshreshtha (2024ADPS0821G), Rohan Agrawal (2024ADPS0004G), Ashwath Chandramouli (2024ADPS0853G), Joel Thomas Thomas (2024ADPS0848G), and Advay Satish (2024ADPS0826G)<br/>BITS Pilani, K K Birla Goa Campus · Instructor: Mayank Goel",
    "SmallA",
)
head("1. Research question and scope")
para(
    "Which volatility should determine the delta hedge when market implied volatility differs from a volatility estimate? We reproduce the constant-volatility single-option results in Sections 3–4 of Ahmad and Wilmott [1], then compare implied-volatility and EWMA-forecast hedges on real NIFTY monthly straddles. The simulation tests a mathematical identity; the historical study evaluates an uncertain forecast under discrete execution."
)
head("2. Stochastic-calculus formulation")
para(
    "Under the physical measure P, dS = μS dt + σS dB, with constant actual volatility σ. The option is marked at V<sub>i</sub>(S,t), using constant implied volatility σ<sub>i</sub>. It satisfies the Black–Scholes PDE at σ<sub>i</sub> [2]. We hold one option, −Δ<sub>h</sub> shares and cash C. Wealth is W = V<sub>i</sub> − Δ<sub>h</sub>S + C, initially zero. Rebalancing is self-financing."
)
para(
    "V<sub>t</sub> + rSV<sub>S</sub> + ½σ<sub>i</sub><super>2</super>S<super>2</super>V<sub>SS</sub> − rV = 0",
    "EqA",
)
para(
    "Applying Itô’s formula and substituting C = W − V<sub>i</sub> + Δ<sub>h</sub>S gives the excess wealth increment:"
)
para(
    "dW − rW dt = ½(σ<super>2</super> − σ<sub>i</sub><super>2</super>)S<super>2</super>Γ<sub>i</sub> dt<br/>+ (Δ<sub>i</sub> − Δ<sub>h</sub>)[(μ − r)S dt + σS dB].",
    "EqA",
)
para(
    "The rW term distinguishes wealth from an instantaneous excess P&amp;L. Multiplying the right-hand side by e<super>−rt</super> gives discounted wealth changes. Quadratic variation creates the gamma term; residual delta creates the Brownian term."
)
para(
    "<b>Known actual-volatility hedge:</b> let V<sub>σ</sub>(S,t) be the theoretical Black–Scholes value process under actual volatility σ. Continuous replication with Δ<sub>h</sub> = Δ<sub>σ</sub> reproduces the expiry payoff V<sub>σ</sub>(S<sub>T</sub>,T) = (S<sub>T</sub>−K)<sup>+</sup> = V<sub>i</sub>(S<sub>T</sub>,T) starting from cost V<sub>σ</sub>(S<sub>0</sub>,0). Because the option was bought at market mark V<sub>i</sub>(S<sub>0</sub>,0), terminal discounted wealth satisfies the exact path-independent identity: e<super>−rT</super>W<sub>T</sub> = V<sub>σ</sub>(S<sub>0</sub>,0) − V<sub>i</sub>(S<sub>0</sub>,0). Intermediate market marks fluctuate, but terminal replication profit is fixed."
)
para(
    "<b>Constant implied-volatility hedge:</b> with Δ<sub>h</sub> = Δ<sub>i</sub>, the residual delta (Δ<sub>i</sub> − Δ<sub>h</sub>) vanishes, eliminating the Brownian term dB. Discounted terminal P&amp;L equals the integral of ½e<super>−rt</super>(σ<super>2</super>−σ<sub>i</sub><super>2</super>)S<super>2</super>Γ<sub>i</sub> over time. Because Γ<sub>i</sub> &gt; 0 for a long vanilla option, its profit sign matches sign(σ<super>2</super>−σ<sub>i</sub><super>2</super>), but its terminal magnitude remains stochastic and path-dependent."
)
para(
    "These statements require constant volatility, continuous trading and no costs. Changing implied volatility introduces additional risks. A forecast is not known actual volatility, and a short historical holding period does not inherit the terminal guarantee. Pricing uses Q; simulation and historical P&amp;L are evaluated under P [2]."
)
page()
head("3. Numerical replication")
para(
    "We generate exact GBM transitions with S<sub>0</sub> = K = 100, T = 1 year, μ = 10%, r = 5% and implied volatility 20%. Each scenario uses 20,000 paths, 252 hedge intervals and seed 244. The two hedge rules share each path. Cash accrues interest, each stock rebalance debits cash, and expiry wealth includes the payoff and hedge liquidation. Results below are discounted index points per call."
)
data = [["Actual volatility", "Hedge volatility", "Mean P&L", "P&L std. dev."]]
for row in sim:
    data.append(
        [
            f(float(row["actual"]) * 100, 0) + "%",
            row["rule"],
            f(row["mean"], 3),
            f(row["std"], 3),
        ]
    )
table(data, [110, 130, 105, 150])
para(
    "At 30% actual volatility, theoretical profit is 3.7807 and simulated actual-hedge mean is 3.7840 (Monte Carlo standard error 0.0044). At 15%, the theoretical value is −1.8589 and simulated mean is −1.8579. Implied-volatility hedging retains substantially more terminal dispersion."
)
img(
    "simulation_distribution.png",
    495,
    183,
    "Figure 1. Simulated discounted P&L. Teal: actual-volatility hedge. Orange: implied-volatility hedge. All gains/losses are conditional on the simulated model.",
)
img(
    "convergence.png",
    420,
    210,
    "Figure 2. Replication-error standard deviation, 6,000 paths per frequency. The fitted log–log slope is −0.496, close to the −0.5 reference.",
)
para(
    "The 30%-actual / 20%-implied simulation produced positive terminal P&amp;L on all 20,000 paths for both rules. This finite-sample observation is not a guarantee for discrete hedging or market trading. Equal-volatility pricing, parity, numerical delta and ledger reconciliation are checked by the accompanying tests.",
    "SmallA",
)
page()
head("4. Historical experiment")
para(
    f'NSE UDiFF bhavcopies [3] supply {dq["sessions"]} sessions from 8 July 2024 to 31 December 2025 (389 manifest requests: 370 downloads with SHA-256 hashes and 19 HTTP 404 weekdays), including the special 1 February 2025 budget session. The cleaned options chain contains {dq["option_rows"]:,} monthly-option records ({int(round(dq["option_rows"] * dq["iv_valid_fraction"])):,} with valid IVs), alongside {dq["futures_rows"]:,} futures records and a separate {dq["atm_sessions"]}-row ATM panel. The index close comes from the archive’s underlying-price field.'
)
para(
    "Monthly options must match an observed futures expiry. Black-76 [4] on the matched futures close yields each leg’s implied volatility and futures delta. All strikes remain available for tracking held contracts. Invalid IV observations are excluded from entry selection; no artificial volatility fills are used. The flat 6.5% rate is an assumption, not a downloaded RBI yield."
)
para(
    "EWMA variance uses 60 initial returns and λ = 0.94 [5], then updates using only available closes. Volatility is annualized with 252 sessions and evaluated against 5-session realized volatility in diagnostics. At a decision close, choose the first monthly expiry 14–65 calendar days away and the nearest strike with both legs traded and valid IV. The trading signal (forecast minus mean call/put IV) has a horizon mismatch between daily EWMA and 14–65 day IV."
)
para(
    "Buy above +k, sell below −k. Execute at the next session’s recorded opens. Hold one straddle unit for five sessions, exiting at the first available session with seven or fewer calendar days to expiry or at sample end; entries are blocked when fewer than five sessions remain in the sample. No overlapping positions or new entry on an exit day. Keep strike and expiry fixed. Futures quantities, including rebalances, use the preceding close and may be fractional."
)
para(
    "Calibration runs 7 October 2024–30 June 2025. Among k = 0, 1, 2, 3 volatility percentage points (0.00–0.03) with at least ten training trades under each rule, maximizing the average of total calibration-period net P&amp;L across the two hedge rules selects <b>k = 0.03 (3 volatility percentage points)</b>, where both rules execute 10 trades and average 230.25 points. The untouched test period is July–December 2025."
)
para(
    "Base costs are illustrative all-in proxies: 0.20% of option premium each way and 1 bp of traded futures notional. Cash financing and daily futures gains are explicit. These proxies do not reconstruct historical taxes, brokerage or margin. P&amp;L is per index unit; exchange lot and collateral constraints are not enforced."
)
table(
    [
        ["Test result (126 sessions)", "Implied hedge", "Forecast hedge"],
        ["Completed trades", "3 (all short)", "3 (all short)"],
        ["Net P&L, index points", f(met[0]["net_pnl"]), f(met[1]["net_pnl"])],
        ["Direct modeled costs", f(met[0]["cost"]), f(met[1]["cost"])],
        [
            "Max. drawdown, index points",
            f(met[0]["max_drawdown_points"]),
            f(met[1]["max_drawdown_points"]),
        ],
        [
            "Annualized daily P&L Sharpe",
            f(met[0]["sharpe_excess"]),
            f(met[1]["sharpe_excess"]),
        ],
    ],
    [235, 130, 130],
)
para(
    "Only three test trades trigger, all in October–November. Each is profitable, but this tiny sample cannot establish reliable profitability or hedge superiority. The forecast hedge earns 6.58 more points overall while showing a larger maximum drawdown. Sharpe annualizes daily incremental P&amp;L, including inactive days, and is unstable with so few trades."
)
page()
head("5. Results, sensitivity and limitations")
img(
    "historical_pnl.png",
    495,
    190,
    "Figure 3. Test-period cumulative net P&L at the training-selected threshold. Long flat sections reflect no position, not missing marks.",
)
table(
    [["Cost multiplier", "Implied net P&L", "Forecast net P&L"]]
    + [
        [f(mult, 0) + "x"]
        + [
            f(
                next(
                    x
                    for x in costs
                    if float(x["cost_multiplier"]) == mult
                    and int(x["rebalance_sessions"]) == 1
                    and x["rule"] == rule
                )["net_pnl"]
            )
            for rule in ["implied", "forecast"]
        ]
        for mult in [0, 1, 2, 5]
    ],
    [165, 165, 165],
)
para(
    "Higher costs reduce both outcomes and reverse the small hedge ranking at 5x costs. As a prespecified threshold diagnostic, k = 0 generates 21 test trades and net P&amp;L of 46.09 (implied) and 103.50 (forecast). We do not replace the selected threshold with a better-looking test alternative. Full threshold and hedge-frequency sensitivities accompany the code."
)
para(
    "The simulation strongly supports the constant-volatility replication identity and the N<super>−1/2</super> error rate. The market comparison is exploratory: few trades, one test period, uncertain forecasts, changing IV, asynchronous opening prints, fractional sizing and omitted margin effects constrain inference. The mean paired-trade difference between forecast and implied hedging is 2.19 index points (6.58 points total). An IID paired-trade bootstrap was suppressed by design because the test sample contains only three trades, which cannot establish hedge superiority."
)
para(
    "<b>Conclusion.</b> Choosing the hedge volatility changes the risk profile. Known-volatility replication controls terminal risk in the ideal model. Forecast-volatility hedging in this NIFTY sample produces a slightly larger net gain, but the evidence does not support a general superiority or an implementable arbitrage claim. A stronger study requires longer independent samples, synchronized bid/ask quotes and historical contract-level costs."
)
para(
    "<b>Implemented scope.</b> The primary backtest uses an EWMA volatility signal, real daily NSE options/futures data, the two hedge rules, and cost/frequency sensitivity. GARCH(1,1) estimation and Greek attribution are implemented in the codebase as exploratory diagnostics but are excluded from the primary decision signal. India VIX benchmarking, Heston calibration, fixed-vega sizing, and 2019–2026 coverage remain extensions. Exact accounting attribution separates option, futures, financing and costs.",
    "SmallA",
)
head("References and reproducibility")
para(
    '[1] Ahmad, R. &amp; Wilmott, P. (2005). Which Free Lunch Would You Like Today, Sir? Wilmott Magazine, November, 64–79. Sections 3–4.<br/>[2] Shreve, S. E. (2004). Stochastic Calculus for Finance II. Springer, Chapters 4–5.<br/>[3] NSE. F&amp;O-UDiFF Common Bhavcopy Final. <link href="https://www.nseindia.com/all-reports-derivatives" color="#126c75">nseindia.com/all-reports-derivatives</link>. Source URLs and SHA-256 hashes in data/download_manifest.csv.<br/>[4] Black, F. (1976). The Pricing of Commodity Contracts. Journal of Financial Economics 3, 167–179.<br/>[5] J.P. Morgan/Reuters (1996). RiskMetrics Technical Document, 4th ed.',
    "SmallA",
)
para(
    "Thirty-five unit and audit tests cover pricing, IV inversion, causality, convergence, Black-76 PDE residuals, schema/hash validation, multi-position controls, and ledger identities. Cleaned options data, downloader, and full experimental parameters are included:",
    "SmallA",
)
codeblock(
    "python run_project.py\npython -m unittest discover -s tests -v"
)


def footer(c, doc):
    c.setStrokeColor(colors.HexColor("#b0bdc5"))
    c.line(50, 36, 545, 36)
    c.setFont("Body", 8)
    c.setFillColor(colors.HexColor("#536375"))
    c.drawString(50, 23, "MAC F244 · Volatility arbitrage and delta hedging")
    c.drawRightString(545, 23, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT / "project_report.pdf"),
    pagesize=(595.28, 841.89),
    leftMargin=50,
    rightMargin=50,
    topMargin=37,
    bottomMargin=47,
)
doc.title = "Volatility Arbitrage and Delta Hedging on NIFTY Index Options"
doc.author = "Arnav Kulshreshtha, Rohan Agrawal, Ashwath Chandramouli, Joel Thomas Thomas, Advay Satish"
doc.build(story, onFirstPage=footer, onLaterPages=footer)
(ROOT / "docs/report_source.md").write_text("\n\n".join(source), encoding="utf-8")
print(OUT / "project_report.pdf")
