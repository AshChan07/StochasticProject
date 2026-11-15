# Document build sources

The numerical project needs only the dependencies in ../requirements.txt. It is independent of Codex and of these document builders.

## Report
Run `python build/build_report.py` from the project directory after installing requirements. It reads results and figures. On macOS it uses Arial; otherwise it uses Helvetica. The source is a four-page ReportLab layout. Its narrative is written for the fixed experiment in README.md: if assumptions or datasets change, update all interpretation and numerical prose as well as tables. docs/report_source.md provides editable report text.

## Slides
build_slides.mjs uses the Codex bundled @oai/artifact-tool package and presentation finalizer. The bundled runtime paths are specific to the authoring machine. The exported PPTX is standalone and editable in PowerPoint or compatible software; no Codex dependency is needed to view or edit it. All graphs and tables are native objects. Speaker notes are also in docs/PRESENTATION_NOTES.md.

To rebuild with Codex, load its workspace dependencies, update the runtime and SKILL paths, link node_modules to the bundled packages, refresh slide_data.json from results CSVs, and run the module. Use a new output filename because the finalizer will not overwrite an existing presentation. Do not change the historical narrative without rerunning results.

Calendar audit code is sample-specific and uses the official circulars listed in DATA_DOWNLOAD_GUIDE.md. The audit must be updated if the date range changes.


The revised slide builder writes `deliverables/project_presentation_audited.pptx` for validation. After inspection, promote that file to `project_presentation_final.pptx`; the latter is the submission artifact. Its numerical slide inputs remain the unchanged baseline; audit findings are added in the narrative.
