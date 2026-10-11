# Meeting architecture improvements

The meeting's telecom pages illustrate a business-user workflow; Lumen retains its retail domain. The model hosting/signup/billing journey is an example platform, not implemented product scope.

## Implemented

- A browser revision guard checks the state captured when a request starts. A manual navigation/filter/date change prevents that pending response from overwriting the user's view. Actions are prepared together and applied to one target state. Unknown/failed actions stop execution instead of appearing successful.
- Browser turns request deferred context updates. Context, undo history and pending confirmations are committed only after successful rendering and verification. Cancellation discards those pending changes. Pending transactions and render receipts expire after ten minutes. Direct backend benchmark calls retain their existing immediate execution path.
- The UI holds the analytical answer until its view loads. `/api/render` supplies a short-lived server payload receipt. `/api/verify` compares applied controls, checks that receipt and refuses failed widget payloads. Validated analysis is recalculated after rendering without another model call; changed figures cause cancellation. The post-render result is the answer shown in chat.
- Facts receive exact source anchors only when view, metric, SQL and raw value match a unique rendered value. Buttons highlight the grid cell or chart point. Derived percentages/contributions and figures from other pages retain query evidence; they are not falsely labelled as direct rendered cells.
- Metadata retrieval chooses a page before model slot filling. The prompt includes that page's widgets/control definitions and current UI state. Metrics, dimensions, filter fields, page IDs and sorting are restricted to the selected page. Large city/product/customer enumerations are bounded: include definitions, counts, samples and request-grounded values rather than entire option catalogs.
- Three-step explicit requests can traverse Olist Sales, Delivery and Reviews, with each calculation and source scope retained. More than four steps clarify rather than silently truncating. Unavailable metrics/entities continue to clarify.
- Execution evidence separates subrequests, workflow nodes, state-changing actions, backend time, post-render calculation time and total browser time. These counts are not interchangeable with LLM reasoning steps.

## Verification boundaries

Receipts prove that the server produced a successful payload for the submitted state; they do not independently inspect browser DOM pixels. Playwright results separately exercise actual DOM state, source highlights and recovery. The local imported databases are read-only at runtime. This is not a distributed snapshot-isolation protocol or multi-user state synchronization service.

There is one controller with five LangGraph stages, not five independent agents. The graph is in memory; retrieval uses BM25 plus TF-IDF vectors and structural reranking. Neural embeddings remain optional. No Excel AppAgent, MCP execution bridge, external browser fallback or production Blackboard bus is claimed. Baserow remains a read-only snapshot adapter without a supplied live platform.

Relative dates use active-dataset reference bounds; financial-year handling uses the existing Indian April–March convention. Configurable per-tenant calendars/timezones remain unsupported. Numerical traceability is not semantic proof or evidence of external causation.

## Evaluation

`eval/architecture_challenges.jsonl` contains eight Codex-authored regression requests, explicitly not an independent human holdout. `eval.verify_architecture_browser` calculates expected Olist figures directly from official CSVs with Decimal aggregation and separate order iteration. It records destination, controls, calculation, verification and latency separately, plus manual-change, failed-render and exact-source highlight checks. Results are in `eval/reports/architecture_browser.json`, separate from `latest.json`.

The initial full-filter page prompt produced three Groq HTTP 413 errors; each visibly fell back to rules. Bounding option catalogs fixed the observed issue, and three subsequent live requests succeeded. The live runner now fails its inference check if a fallback occurs, even when the fallback returns the correct destination. Individual live samples do not establish arbitrary-language accuracy.

## Windows rehearsal

```powershell
# Stop the old Lumen terminal with Ctrl+C, then:
.\start.bat
# Open the URL printed by the launcher; current .env uses http://localhost:8004.
# Hard refresh the browser with Ctrl+F5.
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m eval.verify_architecture_browser --url http://localhost:8004
.\.venv\Scripts\python.exe -m eval.verify_olist_browser --url http://localhost:8004
.\.venv\Scripts\python.exe -m eval.verify_retail_extensions_browser --url http://localhost:8004
.\.venv\Scripts\python.exe -m eval.run_olist_checks
.\.venv\Scripts\python.exe -m eval.run_olist_live
```

For deterministic browser evaluation use a separate terminal/server with `$env:LUMEN_AGENT_MODE='rules'`. Live model evaluation loads the configured provider and requires its service/key/network. Local Ollama remains available; no environment secrets are changed by these improvements.
