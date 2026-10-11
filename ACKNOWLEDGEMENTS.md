# Acknowledgements and third-party notices

Lumen combines its application metadata, dataset adapters, planning and validation logic, analytical queries, evidence handling and dashboard interface with the external projects listed below. Their authors retain ownership of their work. Inclusion does not imply endorsement.

## Datasets

| Source | Attribution and terms | Use in Lumen |
| --- | --- | --- |
| [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii) | Chen, D. (2012). Online Retail II. UCI Machine Learning Repository. DOI: [10.24432/C5CG6D](https://doi.org/10.24432/C5CG6D). CC BY 4.0. | Imported invoice lines for retail sales analysis. Cleaning changes are documented in [REAL_DATA.md](docs/REAL_DATA.md) and the import manifest. |
| [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) | Olist and the dataset contributors. Dataset card identifies CC BY-NC-SA 4.0. | Imported order, customer, item, payment and review records for sales, delivery and reviews. Aggregation and cleaning changes are documented in [OLIST_DATA.md](docs/OLIST_DATA.md). |

Official source downloads and imported DuckDB databases are excluded from this repository. Derived evaluation results and screenshots identify their dataset and metric scope. Olist's dataset terms include noncommercial and share-alike conditions; do not assume the hackathon demonstration grants permission for commercial deployment or unrestricted redistribution of derived data. Consult the source terms before another use.

Sahyadri Retail is generated demonstration data, rather than an external real dataset. Its scenario and numerical ground truth are implemented in `backend/data/generate_data.py` and `data/ground_truth.json`.

## Bundled frontend assets

| Asset | Credits | Licence notice |
| --- | --- | --- |
| [Chart.js 4.5.1](https://github.com/chartjs/Chart.js/tree/v4.5.1) | Chart.js Contributors; charts | [MIT](frontend/vendor/licenses/Chart.js-LICENSE.txt) |
| [@kurkle/color 0.3.2](https://github.com/kurkle/color/tree/v0.3.2) | Jukka Kurkela; colour utilities embedded in Chart.js | [MIT](frontend/vendor/licenses/KurkleColor-LICENSE.txt) |
| [D3 7.9.0](https://github.com/d3/d3/tree/v7.9.0) | Mike Bostock and contributors; metadata graph visualization | [ISC](frontend/vendor/licenses/D3-LICENSE.txt) |
| [Bricolage Grotesque](https://github.com/ateliertriay/bricolage) | The Bricolage Grotesque Project Authors; dashboard headings | [SIL Open Font License 1.1](frontend/vendor/licenses/BricolageGrotesque-OFL.txt) |
| [IBM Plex Sans](https://github.com/IBM/plex) | IBM Corp. and contributors; dashboard text | [SIL Open Font License 1.1](frontend/vendor/licenses/IBMPlexSans-OFL.txt) |

JavaScript copyright headers are retained. The bundled fonts are local WOFF2 Latin subsets in the weights referenced by the stylesheet. The included font licences apply to these distributed font assets. [Licence provenance](frontend/vendor/licenses/sources.json) records upstream URLs and downloaded licence-text hashes.

## Python dependencies

Direct runtime dependencies are declared in [requirements.txt](requirements.txt); development dependencies are in [requirements-dev.txt](requirements-dev.txt). They are installed separately, rather than vendored in this repository.

| Project | Role | Licence of installed project |
| --- | --- | --- |
| [FastAPI](https://github.com/fastapi/fastapi) | HTTP API | MIT |
| [Uvicorn](https://github.com/encode/uvicorn) | ASGI server | BSD 3-Clause |
| [Pydantic](https://github.com/pydantic/pydantic) | Typed request and action validation | MIT |
| [DuckDB](https://github.com/duckdb/duckdb) | Analytical storage and SQL | MIT |
| [NumPy](https://github.com/numpy/numpy) | Numerical processing | BSD 3-Clause; distributions also contain bundled-component notices |
| [pandas](https://github.com/pandas-dev/pandas) | Import and tabular transformations | BSD 3-Clause |
| [scikit-learn](https://github.com/scikit-learn/scikit-learn) | TF-IDF retrieval | BSD 3-Clause |
| [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz) | Fuzzy matching | MIT |
| [HTTPX](https://github.com/encode/httpx) | Model HTTP requests | BSD 3-Clause |
| [Requests](https://github.com/psf/requests) | Baserow HTTP requests | Apache 2.0 |
| [LangGraph](https://github.com/langchain-ai/langgraph) | Stateful agent workflow | MIT |
| [openpyxl](https://foss.heptapod.net/openpyxl/openpyxl) | Excel workbook import | MIT |
| [xlrd](https://github.com/python-excel/xlrd) | Legacy Excel import | BSD |
| [pytest](https://github.com/pytest-dev/pytest) | Backend tests | MIT |
| [Playwright](https://github.com/microsoft/playwright-python) | Browser verification | Apache 2.0 |

Licence names were checked against installed distribution metadata where available. Refer to each dependency's own licence files, including transitive dependencies and browser binaries, for the complete terms. Optional Sentence Transformers support is documented in the development requirements and retrieval implementation; it is not required for the default TF-IDF workflow.

## Models and external services

- [Ollama](https://github.com/ollama/ollama) provides the optional local model runtime. The supplied `Modelfile` references [Qwen2.5 3B](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct). Model weights are downloaded separately and retain their own terms.
- [Groq](https://groq.com/) is an optional inference service. The selected provider and model depend on local configuration. Service and model terms apply separately; credentials and model weights are not included here.
- [Baserow](https://baserow.io/user-docs/database-api) supplies the API used by the optional read-only connector. Lumen includes its own adapter, not the Baserow platform. A live instance and authorized credentials are required.

## Development assistance and project licensing

Parts of the implementation, documentation and regression checks were developed or refined with AI coding assistance through OpenAI Codex. AI-authored regression questions are identified as such in the evaluation protocol; they are not claimed as an independent human-written holdout. Recorded checks and known limitations accompany the implementation.

This file provides attribution; it does not assign a new licence to the team's application code. Third-party licences continue to apply to their respective components and datasets. The team has not yet selected a repository-wide licence for its own code.
