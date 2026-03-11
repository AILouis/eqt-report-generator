# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Tool

### Web UI (Streamlit)
```bash
.venv\Scripts\activate
streamlit run app.py
```
Opens a browser UI where you enter an API key, pick a model, look up a ticker, and download the PDF. No files are written to disk — PDFs are served from memory.

### CLI
```bash
# Activate the virtual environment first (Windows)
.venv\Scripts\activate

# Run with a ticker (API key auto-loaded from key.txt)
python main.py --ticker NVDA

# Override output filename
python main.py --ticker TSLA --output my_report.pdf

# Pass API key explicitly
python main.py --ticker AAPL --api-key sk-or-...
```

Output PDFs are saved to `Reports/{YYYYMMDD}/{TICKER}/{TICKER}_Report_{YYYYMMDD}_{HHMM}.pdf`.

## Architecture

Strict one-way dependency graph (no circular imports):

```
app.py (Streamlit web UI)
  ├── ticker_resolver.py ← resolve_ticker() for the UI lookup step
  ├── orchestrator.py    ← generate_report() called with progress_callback + model override
  ├── config.py          ← AVAILABLE_MODELS list for the model dropdown
  └── market_data.py     ← fetch_stock_overview, compute_technical_data, generate_chart_image,
                            fmt_pct, fmt_dollar, fmt_price, fmt_volume (dashboard metrics)
        └── yf_session.py  ← Shared curl_cffi session for Yahoo Finance (cloud IP bypass)

main.py (CLI entry point)
  ├── ticker_resolver.py ← normalise raw input + yfinance company lookup
  │     └── yf_session.py ← Shared session for yfinance calls
  └── orchestrator.py
        ├── config.py          ← all constants, agent definitions, all prompts
        ├── agents.py          ← builds prompts, calls LLM (uses config + llm_client)
        │     └── llm_client.py ← raw HTTP POST to OpenRouter, retry logic only
        ├── market_data.py     ← yfinance fetch + fmt_pct/fmt_dollar/fmt_price/fmt_volume
        │     └── yf_session.py  ← Shared curl_cffi session (cloud IP bypass)
        │                         + compute_technical_data() + format_technical_block()
        │                         + generate_chart_image() (mplfinance candlestick chart)
        │                         + generate_seasonality_chart() (monthly returns bar chart)
        ├── text_utils.py      ← pure string functions: citation extraction, text cleaning,
        │                         strip_redundant_content()
        └── pdf_builder.py     ← ReportLab assembly (uses config, market_data, text_utils)
```

**Key design principle**: each file has exactly one responsibility. `config.py` is the single source of truth for all prompts and agent definitions — never hardcode prompt strings elsewhere.

## Ticker Input Formats

`ticker_resolver.py` converts any of these into the yfinance-compatible symbol before the pipeline starts:

| User input | Resolved to | Notes |
|---|---|---|
| `NVDA` | `NVDA` | Plain US ticker (unchanged) |
| `NVDA US` | `NVDA` | Bloomberg space notation, US |
| `SHEL LN` | `SHEL.L` | Bloomberg → London suffix |
| `7203 JP` | `7203.T` | Bloomberg → Tokyo suffix |
| `0700 HK` | `0700.HK` | Bloomberg → Hong Kong suffix |
| `MC FP` | `MC.PA` | Bloomberg → Euronext Paris |
| `NVDA.O` | `NVDA` | Reuters NASDAQ code |
| `SHEL.L` | `SHEL.L` | Already correct yfinance format |
| `BRKB` | `BRK-B` | Class-share hyphen insertion (fallback) |

`ticker_resolver.py` also supports a broad set of international Bloomberg exchange codes (Germany, France, Netherlands, Japan, Hong Kong, Australia, India, Korea, Taiwan, Canada, Brazil, and more — see `_BLOOMBERG_SUFFIX` dict in the file).

After resolution, `main.py` shows the company name and asks the user to confirm before the pipeline runs.

## Data Flow

1. **main.py** normalises raw ticker via `ticker_resolver.normalize_ticker()`, confirms company name with user
2. **orchestrator.py** resolves API key (arg → env var → `key.txt`), runs steps in order
3. **Step 0**: `market_data.fetch_stock_overview()` hits yfinance for live price data; then `market_data.compute_technical_data()` computes SMA-20/50/100/200, RSI-14, MACD (12/26/9), last 30 OHLCV sessions, and 5-year monthly seasonality
4. **Step 1**: Five agents run sequentially in this order: `technical`, `macro`, `flow`, `narrative`, `fundamental` — each via `agents.run_agent()` → `llm_client.call_openrouter()` with `use_web_search=True`. The technical agent additionally receives a pre-formatted block of computed indicators and OHLCV data.
5. **Step 2**: `agents.run_cio()` calls the CIO synthesis prompt (no web search, `max_tokens=4500`). Receives all five agent reports plus the live market snapshot.
6. **Step 3**: `pdf_builder.build_pdf()` renders everything; calls `text_utils.extract_citations_and_clean()` on each section to strip URLs from body and accumulate citations for the References section

## Technical Indicators (Computed Locally)

The technical agent does **not** rely on web search for price data or indicator values. Instead, `market_data.compute_technical_data(ticker)` computes these from 1Y yfinance OHLCV history before the agents run:

- **SMA-20, SMA-50, SMA-100, SMA-200** + price distance (%) from each
- **RSI-14** computed from 14-period smoothed average gain/loss
- **MACD (12/26/9)**: EMA-12 minus EMA-26; signal line is EMA-9 of MACD; histogram = MACD minus signal
- **Last 30 OHLCV sessions** as a raw table
- **5-year average monthly returns** (seasonality) — computed on 5Y history, grouped by calendar month

`format_technical_block(tech_data, ticker)` formats all of this into a prompt-ready text block injected into the technical agent's user prompt. The technical agent is instructed to treat these values as authoritative and to restrict web search to: general TA methodology/pattern definitions, recent analyst price targets (≤90 days old), and news explaining unusual moves.

If `compute_technical_data()` returns `None` (fetch failure), the technical agent runs without the data block — report still generates.

## PDF Contents

`pdf_builder.build_pdf()` assembles the report in this order:
1. **Header**: company name, ticker, date, model used
2. **Stock Overview table**: current price, 1D/5D/YTD changes (green/red), 52W high/low, market cap, volume
3. **Candlestick chart**: 1-year OHLCV with SMA-20/50/200 overlays, volume subplot, RSI-14 panel, MACD panel (generated by `generate_chart_image()` via mplfinance)
4. **Seasonality chart**: 12-bar chart of 5-year average monthly returns (generated by `generate_seasonality_chart()`)
5. **Five agent sections** (Technical, Macro, Flow, Narrative, Fundamental): each with verdict card (BULLISH/NEUTRAL/BEARISH) and body text
6. **CIO Synthesis** (new page): 8-section structured output
7. **Glossary** (new page): ~50 curated terms filtered to those that appear in the report text
8. **References** (new page): all extracted source URLs as clickable links

## Citation Architecture (Known Complexity)

The AI is instructed (via `GROUNDING_INSTRUCTION` in `config.py`) to:
- Write a clean body with **no** inline URLs or citation markers
- Append a `SOURCES` block at the very end in `[Title (Date)](url)` format

`text_utils.extract_citations_and_clean()` then runs an 11-step pipeline:
1. Extracts well-formed `[text](url)` markdown links → accumulates in `all_sources`
2. Extracts split-line links: `[Title]\n(https://url)`
3. Strips entire SOURCES/REFERENCES/CITATIONS blocks
4. Strips `[Title - domain.com]` citation artifacts (no URL)
5. Strips any remaining `[text]` brackets (bare citation titles, inline reference markers)
6. Strips unclosed brackets (token-limit truncation artifacts)
7. Strips bare `(https://...)` URLs plus author-date inline citations like `(Source Name, YYYY-MM-DD)`
8. Strips bare `https://` URLs
9. Cleans up whitespace artifacts (double spaces, dangling punctuation, empty parens)
10. Removes lines that are only punctuation or bare bullet markers
11. Removes CJK characters from body text (citation labels rendered in References with CJK-capable font)

Returns a **3-tuple**: `(cleaned_text, citations_list, metrics_dict)`. All callers must unpack all three values.

`text_utils.strip_redundant_content()` is a separate function called by the orchestrator on every agent report before passing to the PDF builder. It removes memo headers (To:/From:/Date:/Subject:), standalone "Memorandum" titles, CIO/committee headers, "As of [date]," sentence openers, and bare References/Sources headings.

The References section at the end of the PDF is populated from `all_sources` collected across all agent sections + the CIO report.

## Modifying Agents

All agent prompts, personas, and section structures live in `config.py`:
- `AGENTS` dict: keys are `macro`, `flow`, `technical`, `narrative`, `fundamental`. Each entry has `name`, `description`, `persona` (system prompt), and `task` (user prompt template with `{ticker}`)
- `GROUNDING_INSTRUCTION`: citation rules injected into every agent's system prompt
- `CONTENT_GUIDELINES`: formatting rules (ALL CAPS numbered sections, bullet points, 400-word limit for most agents, 450 for technical agent) — injected into every agent's user message
- `CIO_TASK`: CIO synthesis prompt with `{ticker}`, `{macro}`, `{flow}`, `{technical}`, `{narrative}`, `{fundamental}`, and `{market_snapshot}` placeholders
- `GLOSSARY`: dict of ~50 curated financial terms with definitions — `pdf_builder.py` filters this to terms that appear in the report text

The technical agent's `task` prompt is structured differently from the others: it references the provided data blocks directly and restricts web search scope. Do not add back a generic "search for indicators" instruction — the data is already provided.

## LLM Configuration

- Default model: `OPENROUTER_MODEL = "anthropic/claude-3.5-haiku:online"` (the `:online` suffix enables web search)
- `AVAILABLE_MODELS` list in `config.py` drives the Streamlit dropdown; the CLI always uses `OPENROUTER_MODEL`
- Agent calls: `temperature=0.3`, `max_tokens=1200`
- CIO synthesis: `temperature=0.2`, `max_tokens=4500`
- Web search plugin: `{"id": "web", "max_results": 8}` — only for the 5 agents, not CIO
- Model can be overridden at runtime: `generate_report(..., model="...")` (used by the Streamlit UI)
- Retry logic: up to `LLM_MAX_RETRIES=3` attempts; rate-limit (429) backs off at `10 × 2^attempt` seconds; server errors (5xx) and network failures back off at `LLM_RETRY_WAIT_BASE × 2^attempt` (base = 5s)

## Dependencies

`requests`, `yfinance`, `reportlab`, `mplfinance`, `streamlit`, `curl_cffi` — see `requirements.txt`.
