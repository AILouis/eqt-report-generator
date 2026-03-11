# Equity Research Report Generator

A multi-agent AI system that generates professional investment research reports for any publicly traded stock. Given a ticker symbol, it runs five specialized AI agents, synthesizes their findings through a CIO (Chief Investment Officer) layer, and outputs a formatted PDF report.

---

## How It Works

The system runs five specialized research agents, each with a distinct analytical lens:

| Agent | Focus |
|---|---|
| **Technical Agent** | Interprets locally computed SMA-20/50/100/200, RSI-14, MACD (12/26/9), and 30-session OHLCV history. Identifies trend structure, support/resistance, price action patterns, and breakout/reversal setups. Web search restricted to general TA methodology and recent analyst price targets. |
| **Macro Agent** | Fed policy, M2 trends, geopolitics, tariffs, AI/semiconductor capex cycle, industry outlook, regulatory changes |
| **Flow Agent** | Regulatory filings (13F, 8-K, S-4), institutional flows, options activity (put/call ratio, open interest), insider trades, buybacks, corporate signaling |
| **Narrative Agent** | Media tone, analyst rating changes, social sentiment, search trends, investment thesis strength |
| **Fundamental Agent** | Earnings, revenue growth, margins, forward guidance, competitive moat, cash flow quality, balance sheet, valuation multiples (P/E, EV/Sales, EV/EBITDA) |

After all five agents complete their analysis, the **CIO (Chief Investment Officer)** synthesizes the reports into a structured 8-section verdict:

1. Market-implied view and consensus
2. Where the research disagrees with consensus (the "edge")
3. Signal alignment scorecard (BULLISH / NEUTRAL / BEARISH per agent)
4. Market regime and factor exposure
5. Scenario analysis (bull / base / bear cases with probability-weighted 12-month expected value)
6. Trade structure and position sizing recommendation
7. Key risks and asymmetry assessment
8. Invalidation signals — specific, measurable conditions that would force a thesis re-evaluation

All agents use real-time web search via the OpenRouter web plugin, except for technical indicators — those are computed locally from Yahoo Finance price history so the technical analysis is always internally consistent with the live price. Stock overview data (current price, 52W high/low, market cap, volume, YTD change) is also fetched live from Yahoo Finance.

**Cloud deployment note:** This project uses `curl_cffi` to bypass Yahoo Finance's cloud IP blocking. When deploying to Streamlit Cloud, AWS, GCP, or Azure, `curl_cffi` is required. It falls back gracefully to standard `requests` when running locally if `curl_cffi` is not installed.

The final output is a professionally formatted **PDF report**.

---

## Features

- Accepts tickers in plain US format (`NVDA`), Bloomberg notation (`SHEL LN`, `7203 JP`, `0700 HK`, `MC FP`), Reuters notation (`NVDA.O`), and standard yfinance format (`SHEL.L`)
- Live market data dashboard shown in the web UI before generation (price, 52W range, volume, YTD change)
- Candlestick chart embedded in the PDF: 1-year price history with SMA-20/50/200 overlays, volume subplot, RSI-14 panel, and MACD panel
- Seasonality chart: 5-year average monthly returns (Jan–Dec) as a colour-coded bar chart
- Per-agent verdict cards (BULLISH / NEUTRAL / BEARISH) with colour-coded styling
- Auto-generated glossary filtered to terms that actually appear in the report (~50 curated definitions)
- All source URLs extracted from AI responses and rendered as a clickable References section
- Supports any OpenRouter-compatible model via a dropdown or free-text override in the UI
- Web UI serves PDFs from memory (nothing written to disk); CLI saves to `Reports/` with timestamped subfolder

---

## Requirements

- Python 3.10+
- An [OpenRouter API key](https://openrouter.ai/keys) (free tier available)

---

## Setup

### 1. Clone or download the project

```bash
cd path/to/Eqt_Report_Generator
```

### 2. Create and activate a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Add your API key (CLI only)

Create a file named `key.txt` in the project root and paste your OpenRouter API key into it. The CLI picks this up automatically — no flag needed.

---

## Usage

### Web UI (recommended)

```bash
streamlit run app.py
```

Opens in your browser. Enter your OpenRouter API key in the sidebar, select a model from the dropdown (or type any OpenRouter model ID in the custom field), look up a ticker, confirm the company name, and click **Generate Report** to download the PDF. No files are written to disk.

### CLI

```bash
python main.py --ticker NVDA
```

Or let it prompt you interactively:

```bash
python main.py
# Enter stock ticker (e.g. NVDA): AAPL
```

The CLI shows the resolved company name and asks you to confirm before running. If the ticker is wrong, you can enter a replacement at the prompt.

#### Custom output path

```bash
python main.py --ticker TSLA --output my_report.pdf
```

#### API key lookup order (CLI)

| Priority | Source |
|---|---|
| 1 | `--api-key YOUR_KEY` flag on the command line |
| 2 | `OPENROUTER_API_KEY` environment variable |
| 3 | `key.txt` file in the project folder (recommended) |

---

## Output

CLI reports are saved inside the `Reports/` subfolder (created automatically):

```
Reports/{YYYYMMDD}/{TICKER}/{TICKER}_Report_{YYYYMMDD}_{HHMM}.pdf
```

Example: `Reports/20260309/NVDA/NVDA_Report_20260309_1852.pdf`

Each PDF contains:
1. Header (company name, ticker, date, model used)
2. Stock overview table (price, 1D/5D/YTD changes, 52W high/low, market cap, volume)
3. Candlestick chart with SMA-20/50/200, volume, RSI-14, and MACD panels
4. Seasonality chart (5-year average monthly returns)
5. Technical Agent Report (with BULLISH/NEUTRAL/BEARISH verdict card)
6. Macro Agent Report (with verdict card)
7. Flow Agent Report (with verdict card)
8. Narrative Agent Report (with verdict card)
9. Fundamental Agent Report (with verdict card)
10. CIO Synthesis (8 structured sections)
11. Glossary (terms that appear in the report, with definitions)
12. References & Sources (clickable links extracted from all agent responses)

Each report takes approximately 2–3 minutes to generate, depending on the model and OpenRouter load.

---

## Project Structure

```
Eqt_Report_Generator/
├── app.py             # Streamlit web UI
├── main.py            # CLI entry point
├── orchestrator.py    # Pipeline coordinator — runs steps 0-3 in order
├── config.py          # All constants: model settings, agent definitions, prompts, glossary
├── agents.py          # Agent runners — constructs prompts and calls the LLM
├── llm_client.py      # Raw HTTP caller for OpenRouter API with retry logic
├── market_data.py     # Live stock data via yfinance + chart generation
├── yf_session.py      # Shared curl_cffi session (bypasses Yahoo Finance cloud blocking)
├── text_utils.py      # Citation extraction and text cleaning utilities
├── pdf_builder.py     # ReportLab PDF assembly
├── ticker_resolver.py # Converts Bloomberg/Reuters notation to yfinance symbols
├── requirements.txt   # Python dependencies
├── key.txt            # Your OpenRouter API key (create this; not committed to git)
└── Reports/           # Generated PDFs saved here by CLI (auto-created)
```

---

## Configuration

The default model is set in `config.py`:

```python
OPENROUTER_MODEL = "anthropic/claude-3.5-haiku:online"
```

The Streamlit UI also exposes a model dropdown (`AVAILABLE_MODELS` in `config.py`) and a free-text override field — no code change needed to try a different model from the UI. Any model on [OpenRouter](https://openrouter.ai/models) with an `:online` suffix supports real-time web search.

To modify agent personas, tasks, section structures, or the CIO synthesis prompt, edit `config.py` — all prompts live there and nowhere else.

---

## Disclaimer

This tool is for informational purposes only and does not constitute financial advice. Always conduct your own due diligence before making investment decisions.
