# Repository review

Review performed on 11 October 2026 for the hackathon submission.

## Executed checks

| Check | Result and scope |
| --- | --- |
| Backend suite | `python -m pytest -q`: 113 passed in 65.44 seconds on Windows, using the existing project environment and imported datasets. |
| Installed dependency consistency | `python -m pip check`: no broken requirements. |
| Tracked-file scan | No credential-shaped keys or copies of local configured secret values found. No local `.env`, DuckDB databases or source archives/workbooks tracked. This is a bounded scan, not a security audit. |
| Fresh-checkout data preparation | Isolated copy of the tracked files, without `.env` or imported databases, generated the synthetic database successfully. |
| Fresh-checkout diagnostics | `doctor.py` passed in that copy: 209 pages, active LangGraph, rules mode and synthetic data available. |
| API smoke checks | Homepage, health and two synthetic chat/render workflows passed in the isolated copy using FastAPI TestClient. |
| Documentation checks | README and acknowledgements local links resolved; Markdown code fences balanced; project whitespace checks passed. Upstream font licence texts retain their original trailing spaces to preserve the downloaded notices and hashes. |
| External asset notices | Official licence texts included for Chart.js, its embedded colour library, D3, Bricolage Grotesque and IBM Plex Sans. Dataset, Python dependency, model/service and AI assistance credits recorded in `ACKNOWLEDGEMENTS.md`. |

## Fixes from the review

- Setup prepares the synthetic database before diagnostics, allowing a checkout without local databases to pass that step.
- `requests`, used by the Baserow adapter, is declared as a direct dependency.
- Local review copies, connector exports and raw dataset files are ignored by Git.
- Third-party licence notices and acknowledgements are linked from the README.

## Verification boundaries

The isolated checkout reused the existing Python environment; a complete dependency download into a brand-new virtual environment was not repeated. These API checks are not browser verification. This review did not make live model requests or connect to a live Baserow instance. Earlier browser and inference measurements retain their own source snapshots and scope in the evaluation reports.

Real datasets must be downloaded and imported separately. Model inference requires local Ollama configuration or authorized provider credentials. The team's own repository-wide licence is not selected; external component and dataset licences remain applicable, including Olist's noncommercial/share-alike conditions. The application is a local demonstration, with the current scope documented in the README.
