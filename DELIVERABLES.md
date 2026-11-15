# Submission contents

## Submit
1. `deliverables/project_report.pdf` — four-page final report.
2. `deliverables/project_presentation_final.pptx` — 16 editable slides with speaker notes, planned for about 17 minutes plus questions.
3. Source-code folder — `src`, `data_pipeline`, `tests`, `run_project.py`, `download_data.py`, `requirements.txt` and `README.md`.

Include `data/clean` and `results` with the code when submission size permits. They allow the instructor to reproduce and inspect the study without downloading market data.

## Study and rehearse
- `docs/THEORY_AND_VIVA.md`: derivation, financial accounting and 23 viva questions.
- `docs/PRESENTATION_NOTES.md`: slide-by-slide speaking notes.
- `docs/AUDIT_AND_INTEGRATION.md`: integrated pipeline, independently found issues, fixes and remaining limitations.
- `docs/report_source.md`: editable report text.
- `DATA_DOWNLOAD_GUIDE.md`: official sources and optional additional data.

## Before submission
Check the spelling of all group members' names and add institutional IDs if required. Read the report and rehearse the explanation of both hedge rules. Review the documented differences from the proposal: this package implements the EWMA core with a shorter real-data sample, not the optional GARCH/Heston extensions.

The simulation and historical results are computed, not placeholders. Historical inference is limited by three trades at the selected threshold, simplified costs and opening-price execution proxies. These limitations are stated in both report and slides.
