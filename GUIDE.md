# Beginner's Guide to the Equity Research Report Generator

This guide is written for someone who is new to coding and completely new to this project. It explains everything in plain English — what the tool does, what you need to install, how to set it up, and how to use it. Skip to any section using the table of contents below.

---

## Table of Contents

1. [What does this project do?](#1-what-does-this-project-do)
2. [What you need before starting](#2-what-you-need-before-starting)
3. [Step-by-step setup](#3-step-by-step-setup)
4. [How to run the tool](#4-how-to-run-the-tool)
5. [What each file does](#5-what-each-file-does)
6. [How does it actually work? (the full pipeline)](#6-how-does-it-actually-work-the-full-pipeline)
7. [Common errors and how to fix them](#7-common-errors-and-how-to-fix-them)
8. [Glossary of terms](#8-glossary-of-terms)

---

## 1. What does this project do?

This tool creates a professional **investment research report** for any publicly traded stock — the kind of report that analysts at investment banks spend hours writing. You give it a stock ticker symbol (like `NVDA` for Nvidia, or `AAPL` for Apple), and it automatically:

1. Fetches live price data from Yahoo Finance
2. Sends the data to five AI specialists, each looking at the stock from a different angle
3. Combines all five analyses through an AI "Chief Investment Officer" who writes a final verdict
4. Generates a polished PDF report you can download

The whole process takes about 2–3 minutes and runs entirely automatically after you start it.

### What kinds of analysis does it produce?

The five AI specialists are:

- **Technical Analyst** — looks at price charts, moving averages, momentum indicators (RSI, MACD), and identifies patterns like support/resistance levels and breakout setups. Uses locally computed data rather than web searches for prices, so the numbers are always accurate and consistent.
- **Macro Strategist** — looks at the big economic picture: interest rates, inflation, geopolitics, tariffs, and how the overall environment affects this specific stock
- **Flow Analyst** — tracks where large institutional investors (hedge funds, pension funds) are putting their money, and what options market activity is signalling
- **Narrative Analyst** — assesses whether the stock's investment story is gaining or losing traction in the media, social platforms, and analyst community
- **Fundamental Analyst** — digs into the company's financial results: earnings, revenue growth, profit margins, debt levels, and whether the stock price is justified by the business fundamentals

After those five reports, a "CIO" (Chief Investment Officer) reads all of them and produces a final structured verdict that includes:

- An assessment of what the current stock price is already pricing in
- Where the research disagrees with the market consensus
- A signal alignment scorecard rating each of the five agents as BULLISH, NEUTRAL, or BEARISH
- Bull / base / bear scenarios with probability estimates and price targets
- A specific trade recommendation with position sizing
- Measurable conditions that would indicate the thesis is wrong

---

## 2. What you need before starting

### Python

Python is a programming language. This project is written in Python. You need Python version **3.10 or higher** installed on your computer.

To check if you already have Python:

- Open a terminal (on Windows: press Win+R, type `cmd`, press Enter)
- Type `python --version` and press Enter
- If it says `Python 3.10.x` or higher, you are good
- If it says version 3.9 or lower, or "not found", go to [python.org/downloads](https://www.python.org/downloads/) and install the latest version

When installing Python on Windows, tick the box that says **"Add Python to PATH"** — this is important and easy to miss.

### An OpenRouter API key

OpenRouter is a service that provides access to AI models (like Claude, GPT, Gemini, and others) through one unified interface. This project uses OpenRouter to run the AI analysis.

You need a free API key:

1. Go to [openrouter.ai/keys](https://openrouter.ai/keys)
2. Create a free account
3. Click "Create Key" to generate your API key
4. Copy the key — it starts with `sk-or-`

The free tier provides enough credits to generate several reports. Keep your key private — treat it like a password.

### pip

`pip` is Python's package manager — it installs Python libraries (pre-written code that does specific things). It comes bundled with Python 3.10+, so you almost certainly already have it. If you are unsure, run `pip --version` in your terminal.

### A terminal / command prompt

A terminal is the text-based window where you type commands. On Windows, use **PowerShell** or **Command Prompt** (cmd.exe). On Mac, use **Terminal** (search for it in Spotlight).

---

## 3. Step-by-step setup

Follow these steps in order. Each step builds on the previous one.

### Step 1: Download the project

If you received the project as a zip file, extract it to any folder. If you are using git:

```bash
git clone <repository-url>
```

Make a note of the full path to the folder. For this guide we use `D:\Desktop\Projects\Eqt_Report_Generator` as an example.

### Step 2: Open a terminal and navigate to the project folder

On Windows, open PowerShell and type:

```powershell
cd "D:\Desktop\Projects\Eqt_Report_Generator"
```

Replace the path with wherever you extracted the project.

### Step 3: Create a virtual environment

A **virtual environment** is an isolated copy of Python just for this project. It keeps the project's dependencies separate from other Python projects on your computer and prevents version conflicts.

On Windows:

```powershell
python -m venv .venv
```

On Mac / Linux:

```bash
python3 -m venv .venv
```

This creates a hidden folder called `.venv` inside the project folder. You only need to do this once.

### Step 4: Activate the virtual environment

You must "activate" the virtual environment each time you open a new terminal window to work on this project.

On Windows (PowerShell):

```powershell
.venv\Scripts\activate
```

On Mac / Linux:

```bash
source .venv/bin/activate
```

After activation, you will see `(.venv)` at the start of your terminal prompt. This tells you the virtual environment is active and all Python commands will use it.

If you get a security error on Windows about scripts being disabled, run this first:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try the activate command again.

### Step 5: Install the required libraries

With the virtual environment active, install all the project's dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This downloads and installs: `requests`, `yfinance`, `reportlab`, `mplfinance`, `streamlit`, and `curl_cffi`. It may take 1–2 minutes depending on your internet connection.

### Step 6: Add your API key (for the CLI)

Create a plain text file called `key.txt` in the project root folder. Open it with any text editor (Notepad works fine), paste your OpenRouter API key (the one starting with `sk-or-`) as the only line in the file, and save it.

The CLI will automatically read this file when you run a report — no flags needed.

If you plan to use only the web UI (Streamlit), skip this step. You will enter the key directly in the browser instead.

---

## 4. How to run the tool

There are two ways to use the tool: the **Web UI** (recommended for most people) and the **CLI** (command line interface).

### Option A: Web UI (recommended)

The web UI runs in your browser and is the easiest way to use the tool.

1. Make sure your virtual environment is active (you see `(.venv)` in the terminal)
2. Run:
  ```bash
   streamlit run app.py
  ```
3. Streamlit will automatically open a browser tab at `http://localhost:8501`. If it does not open automatically, look for that URL in the terminal output and open it manually.

**What you will see in the browser:**

The page is divided into a sidebar and a main area.

**Sidebar (always visible on the left):**

- Enter your OpenRouter API key in the password field (characters are hidden as you type; the key is never stored anywhere)
- Select a model from the dropdown. The default is Claude 3.5 Haiku — a good balance of speed and quality
- Optionally type any OpenRouter model ID in the "Custom model ID" field to use a different model

**Main area — Step 1: Enter a ticker**

- Type a stock ticker and click "Look Up"
- Accepted formats: `NVDA`, `AAPL`, `SHEL LN`, `7203 JP`, `0700 HK`, `NVDA.O`, `MC FP`, `SHEL.L`
- The tool resolves the ticker and looks up the company name from Yahoo Finance

**Main area — Step 2: Confirm and generate**

- After a successful lookup, a green banner confirms the company name (e.g. "Found: NVIDIA Corporation (NVDA)")
- Live market data is shown: current price (with a green or red delta), 5-day change, year-to-date change, market cap, 52-week high/low, and volume
- A 1-year candlestick chart with SMA overlays is displayed
- Click **Generate Report** (the blue button)
- A progress bar appears showing each step: market data fetch, then each of the five agents by name, then CIO synthesis, then PDF assembly
- Each step shows a short status message while it runs
- Total time is approximately 2–3 minutes

**Main area — Step 3: Download**

- When complete, a download button appears
- Click it to save the PDF to your computer's default downloads folder
- Nothing is stored on any server — the PDF exists only in your browser session for this tab

### Option B: CLI (command line)

The CLI is faster if you are comfortable with terminals and don't need the visual dashboard.

1. Make sure your virtual environment is active
2. Run with a specific ticker:
  ```bash
   python main.py --ticker NVDA
  ```
3. The tool looks up the company name and asks you to confirm:
  ```
     Looking up 'NVDA'...
     Found: NVIDIA Corporation (NVDA). Is this correct? [Y/n]:
  ```
4. Press Enter (or type `y`) to confirm. Report generation starts immediately.
5. Progress is printed to the terminal as each step completes. When finished:
  ```
   DONE!  Open your report: Reports/20260310/NVDA/NVDA_Report_20260310_1423.pdf
  ```

**Other CLI options:**

```bash
# Specify a custom output file path
python main.py --ticker TSLA --output my_report.pdf

# Pass the API key directly (instead of using key.txt)
python main.py --ticker AAPL --api-key sk-or-your-key-here

# Run without specifying a ticker — it will prompt you interactively
python main.py
```

**Where the PDF is saved (CLI):**

Reports are automatically saved inside a `Reports/` subfolder with a date/ticker structure:

```
Reports/20260310/NVDA/NVDA_Report_20260310_1423.pdf
```

The folder is created automatically if it doesn't exist.

---

## 5. What each file does

Here is every Python file in the project, explained in plain English.

### `config.py` — All settings and AI instructions

This is the most important file in the project. Everything the AI agents say, how they say it, and which model they use is controlled here. It contains:

- `**OPENROUTER_MODEL**`: The default AI model (currently Claude 3.5 Haiku)
- `**AVAILABLE_MODELS**`: The list of models shown in the web UI dropdown
- `**AGENTS**`: A dictionary defining all five research agents. Each agent entry has:
  - `name`: Display name (e.g. "Macro Agent")
  - `description`: Short description shown in the PDF
  - `persona`: The "system prompt" — instructions telling the AI what role to play
  - `task`: The "user prompt" — what to research and how to format the answer
- `**CIO_TASK**`: The full instructions for the CIO synthesis step
- `**GROUNDING_INSTRUCTION**`: Citation rules injected into every agent's system prompt
- `**CONTENT_GUIDELINES**`: Formatting rules (section headers must be ALL CAPS, use bullet points, max 400 words) injected into every agent's user message
- `**GLOSSARY**`: A dictionary of about 50 financial terms with definitions. The PDF builder filters this to only the terms that actually appear in the generated report.

If you want to change what an agent researches, how long the reports are, which model is used, or the style of the output — this is the only file you need to edit.

### `main.py` — The command line entry point

This is what runs when you type `python main.py`. It:

1. Reads command-line arguments (`--ticker`, `--output`, `--api-key`)
2. Prompts for a ticker interactively if none was provided
3. Looks up the company name and asks you to confirm (loops if you say no)
4. Calls `generate_report()` from `orchestrator.py` to do the actual work

If you want to change how the tool is invoked from the command line, or add new arguments, this is the file to edit.

### `app.py` — The web UI

This is what runs when you type `streamlit run app.py`. It creates the three-step browser interface. It also shows a live market data dashboard with price metrics and a chart before you generate the report.

Streamlit re-runs this file from top to bottom every time the user clicks anything. The `st.session_state` dictionary is used to remember information (the resolved ticker, the generated PDF) between re-runs.

### `orchestrator.py` — The pipeline coordinator

This file runs all the steps in sequence. Think of it as a project manager who delegates every task to a specialist and then assembles the results. The main function is `generate_report()` which:

1. Resolves the API key (checks command-line argument first, then environment variable, then `key.txt`)
2. Fetches live market data from Yahoo Finance
3. Computes technical indicators
4. Runs all five AI research agents in sequence
5. Runs the CIO synthesis
6. Builds the PDF

It also calls the `progress_callback` function (provided by `app.py`) at each checkpoint so the web UI can update its progress bar.

### `agents.py` — The AI agent runner

This file constructs the messages sent to the AI and calls the API. It contains two functions:

- `**run_agent()**`: Builds the prompt for one agent by combining the agent's persona and task from `config.py` with today's date, the live market snapshot, and (for the technical agent) the pre-computed indicator data. Then calls `llm_client.py` to get the response.
- `**run_cio()**`: Takes all five finished agent reports, slots them into the `CIO_TASK` template from `config.py`, and calls the AI for the CIO verdict. No web search is used for this step.

### `llm_client.py` — The HTTP caller

This file contains one function: `call_openrouter()`. It is the lowest-level file in the project — it knows nothing about agents, tickers, or reports. It just sends an HTTP POST request to the OpenRouter API and returns the AI's text response.

It handles retrying automatically if there is a problem:

- **Rate limit (HTTP 429)**: waits 10 seconds, then 20, then 40 before retrying
- **Server error (HTTP 5xx)**: waits 5 seconds, then 10, then 20
- **Network failure**: same as server errors

You do not need to touch this file unless the OpenRouter API itself changes.

### `market_data.py` — Live stock data and charts

This file connects to Yahoo Finance (via the `yfinance` library) to fetch real data and compute indicators. Its main functions:

- `**fetch_stock_overview()`**: Downloads current price, 52-week high/low, market cap, volume, and recent price changes
- `**compute_technical_data()**`: Downloads 1 year of daily price history and computes SMA-20/50/100/200, RSI-14, MACD (12/26/9), the last 30 rows of OHLCV data, and 5-year average monthly returns (seasonality). Returns `None` if the fetch fails so the pipeline degrades gracefully.
- `**format_technical_block()**`: Converts the computed data into a formatted text block that gets injected into the technical agent's prompt
- `**format_snapshot_for_prompt()**`: Converts the overview data into a formatted block injected into all agent prompts
- `**generate_chart_image()**`: Uses mplfinance to render a 1-year candlestick chart with SMA-20/50/200 overlays, volume subplot, RSI-14 panel, and MACD panel. Returns the image as bytes.
- `**generate_seasonality_chart()**`: Uses matplotlib to render a bar chart of average returns by calendar month. Returns the image as bytes.
- Display formatters used by the PDF builder: `fmt_pct()`, `fmt_dollar()`, `fmt_price()`, `fmt_volume()`

### `text_utils.py` — Text cleaning

The AI responses sometimes contain URLs and citation markers mixed into the analysis text. This file cleans that up. It contains two functions:

- `**extract_citations_and_clean()**`: Runs an 11-step pipeline to extract all source URLs from the AI's SOURCES section, then strips all URLs, markdown links, and citation markers from the body text. Returns a 3-tuple: `(cleaned_text, list_of_citations, metrics_dict)`.
- `**strip_redundant_content()**`: Removes boilerplate the AI sometimes adds even when instructed not to — things like memo headers ("To:", "From:", "Date:"), "As of March 2026," openers, and bare "References:" headings.

### `pdf_builder.py` — Assembles the final PDF

This file takes all the cleaned text and data and builds the PDF using the `reportlab` library. The main function is `build_pdf()`. It assembles the report in this order: header, stock overview table, candlestick chart, seasonality chart, five agent sections (each with a verdict card), CIO synthesis, glossary, and references.

It also registers fonts: it looks for Windows system fonts (Arial, then SimHei for CJK characters in source titles) and falls back to DejaVu Sans from the matplotlib installation if Arial is not found.

### `ticker_resolver.py` — Converts ticker formats

Different financial data providers use different naming conventions for the same stock. This file converts user input into the format that Yahoo Finance understands.

- `**normalize_ticker()**`: Pure string conversion — no network calls. Handles Bloomberg space notation (`SHEL LN` → `SHEL.L`), Bloomberg dot notation (`NVDA.US` → `NVDA`), Reuters notation (`NVDA.O` → `NVDA`), and plain tickers.
- `**resolve_ticker()**`: Calls `normalize_ticker()` then attempts a Yahoo Finance lookup to get the company name. Also tries inserting a hyphen for class-share tickers (`BRKB` → tries `BRK-B`). Returns `(ticker, company_name_or_None)`.

### `requirements.txt` — Dependency list

A plain text file listing the Python libraries this project needs. When you run `pip install -r requirements.txt`, pip reads this file and installs all the libraries listed. 

### `yf_session.py` — Shared session for Yahoo Finance calls

Yahoo Finance blocks requests from cloud datacenter IPs (AWS, GCP, Azure — including Streamlit Cloud) at multiple layers: IP range detection, TLS fingerprint detection, and header checks. This file provides a shared `curl_cffi` session that impersonates a Chrome browser at the TLS level, bypassing all three checks reliably.

- `**get_yf_session()**`: Returns a cached session object. Uses `curl_cffi` with Chrome impersonation if available; falls back to a plain `requests.Session` with browser headers for local development.

Both `market_data.py` and `ticker_resolver.py` import this session to make their yfinance calls. If you are deploying to a cloud server, make sure `curl_cffi` is installed (it is in `requirements.txt`).

---

## 6. How does it actually work? (the full pipeline)

Here is exactly what happens, step by step, from the moment you click "Generate Report" to the moment the PDF is ready.

### Step 0: Fetch market data (about 5–10 seconds)

The orchestrator calls two functions from `market_data.py`:

`**fetch_stock_overview(ticker)**` — connects to Yahoo Finance and downloads:

- The current stock price (using `currentPrice`, falling back to `regularMarketPrice`, then `previousClose`, then the most recent close from history)
- 1-day and 5-day price changes as percentages
- Year-to-date price change
- 52-week high and low
- Market capitalisation
- Trading volume

`**compute_technical_data(ticker)**` — downloads 1 year of daily price history and computes:

- **SMA-20, SMA-50, SMA-100, SMA-200**: rolling averages of closing prices over 20, 50, 100, and 200 sessions. Also calculates how far the current price is above or below each average, as a percentage.
- **RSI-14**: computed as 100 minus (100 / (1 + RS)), where RS is the ratio of the average 14-day gain to the average 14-day loss. Values above 70 suggest overbought conditions; below 30 suggests oversold.
- **MACD (12/26/9)**: the MACD line is the 12-period EMA minus the 26-period EMA. The signal line is the 9-period EMA of the MACD line. The histogram is MACD minus signal. When MACD crosses above signal, it is considered a bullish crossover.
- **Last 30 OHLCV sessions**: a table of the most recent 30 trading days with open, high, low, close, and volume for each day.
- **5-year monthly seasonality**: using 5 years of price history, computes the average return for each calendar month. This shows which months have historically been strong or weak for this particular stock.

All of this computation happens locally on your machine before any AI call is made. This ensures the technical agent always receives accurate, internally consistent data — not potentially stale figures scraped from a website.

### Step 1: Five AI agents run (the main analysis, about 60–90 seconds total)

The agents run one after another (not simultaneously) in this order: Technical, Macro, Flow, Narrative, Fundamental.

For each agent, `agents.py` builds a message with two parts:

**System prompt** (sets the AI's role):

```
You are a technical analysis expert with 20 years of experience...
[citation rules from GROUNDING_INSTRUCTION]
```

**User message** (the actual task):

```
Today's date is March 10, 2026.

=== AUTHORITATIVE MARKET DATA SNAPSHOT ===
Current Price: $875.50 USD
1D Change: +1.23%
52W High: $974.00 USD
...

=== COMPUTED TECHNICAL INDICATORS ===        <- technical agent only
SMA-20: $852.30  (+2.7% above)
SMA-50: $831.10  (+5.3% above)
RSI-14: 62.4  (Neutral 30-70)
MACD line: 8.3401  (MACD above signal — bullish)
...
[30 rows of daily OHLCV data]
...
[5-year monthly seasonality table]

Analyse the technical picture for NVDA using the data blocks provided above...
[formatting rules: 450 words max, ALL CAPS section headers, bullet points]
```

This message is sent to OpenRouter with web search enabled (`use_web_search=True`). The AI can search the internet while composing its answer. However, the technical agent is explicitly instructed not to search for NVDA's price or indicator values — those are already provided accurately in the prompt.

Each response ends with a `SOURCES` block listing the web pages the AI cited.

Between each agent call, the orchestrator waits 2 seconds to avoid hitting the API's rate limit.

### Step 2: CIO synthesis (about 30–60 seconds)

The orchestrator calls `agents.run_cio()` which builds one large message containing:

- All five agent reports
- The live market data snapshot
- Detailed instructions for the 8-section CIO format

This is sent to the AI without web search enabled — the CIO only reasons over the information already collected. It does not search the internet.

The CIO produces an 8-section structured verdict covering market-implied view, identified edge, signal alignment scorecard, market regime analysis, scenario analysis with probability-weighted price targets, trade structure recommendation, risk assessment, and invalidation signals.

### Step 3: Clean the text

Before building the PDF, the orchestrator passes each agent report through `text_utils.strip_redundant_content()`. This removes memo headers ("To: Investment Committee", "From: Macro Analyst", "Date: March 10, 2026") and boilerplate sentence openers ("As of March 2026, the Federal Reserve...") that the AI sometimes writes despite being instructed not to.

### Step 4: Build the PDF

`pdf_builder.build_pdf()` runs through every section:

**For each agent section**, it calls `text_utils.extract_citations_and_clean()` which:

1. Finds every `[Source Title (Date)](https://url)` link in the SOURCES block
2. Adds it to a shared `all_sources` list
3. Strips all URLs and citation markers from the body text
4. Returns clean prose ready for the PDF

Then it looks for a `VERDICT:` line (e.g. `VERDICT: BULLISH — Fed tailwinds support AI infrastructure demand`) and converts it into a coloured card at the top of the section: green background for BULLISH, red for BEARISH, grey for NEUTRAL.

The rest of the body text is converted into ReportLab flowables: numbered ALL-CAPS lines become subheadings in dark blue, bullet point lines become indented bullets, and plain text becomes body paragraphs.

After all sections are processed, the PDF is assembled with:

- A glossary page showing only the terms from `config.GLOSSARY` that actually appear somewhere in the report text
- A references page with all `all_sources` rendered as numbered clickable links

The completed PDF is written to disk at the timestamped path (CLI) or returned as bytes to the web UI (Streamlit).

---

## 7. Common errors and how to fix them

### "No module named 'streamlit'" or "No module named 'yfinance'"

The dependencies are not installed, or the virtual environment is not active.

Fix:

1. Activate the virtual environment: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Mac/Linux)
2. Install dependencies: `pip install -r requirements.txt`

### "No OpenRouter API key found"

The tool could not find your API key. It checks three places in order: (1) the `--api-key` flag, (2) the `OPENROUTER_API_KEY` environment variable, (3) a file called `key.txt` in the project folder.

Fix: Create `key.txt` in the project root and paste your key into it as the only content on the first line. No quotes, no extra text.

### "HTTP 401" — Unauthorized

Your API key is invalid or has been revoked.

Fix: Go to [openrouter.ai/keys](https://openrouter.ai/keys), generate a new key, and update `key.txt`.

### "HTTP 402" — Insufficient credits

Your OpenRouter account has run out of credits.

Fix: Add credits at [openrouter.ai/credits](https://openrouter.ai/credits). You can also switch to a less expensive model by changing `OPENROUTER_MODEL` in `config.py`.

### "HTTP 429" — Rate limited

You sent too many requests to the API in a short time. The tool retries automatically (waits 10s, then 20s, then 40s). If it keeps failing even after retries, wait a minute and run the report again.

### Ticker not found — "was not found in market data"

The ticker could not be validated against Yahoo Finance. Possible causes:

- A typo in the ticker symbol (verify it on [finance.yahoo.com](https://finance.yahoo.com))
- The stock was recently listed and has little history
- The exchange code is not supported

The tool will still try to run (the AI agents can still produce analysis), but market data, charts, and technical indicators will be missing from the PDF.

### "PDF build failed" / ReportLab error

This is rare. It usually means the AI produced text with unusual formatting that confused the PDF layout engine.

Fix: Run the report again — the AI output varies slightly between runs.

### The web UI does not open automatically

Streamlit should open a browser tab automatically. If it does not, look for this line in the terminal:

```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

Open that URL manually in your browser.

### "streamlit: command not found" after installing

The virtual environment is not active.

Fix: Run `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Mac/Linux), then try again.

### The chart is missing from the PDF

Chart generation requires `mplfinance` to be installed and the stock to have enough price history (at least 20 trading days). For very new stocks or in the rare case where `mplfinance` fails, the chart is silently skipped and the rest of the report generates normally.

### Windows: "running scripts is disabled on this system"

PowerShell's execution policy is blocking the activation script.

Fix:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then run `.venv\Scripts\activate` again.

---

## 8. Glossary of terms

These terms appear throughout this guide and in the generated reports.

**API (Application Programming Interface)** — A way for two software systems to communicate. When this tool sends a request to OpenRouter, it is using OpenRouter's API.

**API key** — A secret string that identifies you when calling an API. Yours starts with `sk-or-`. Keep it private — anyone with your key can use your account.

**Bearish** — A negative outlook on an investment, meaning you expect the price to fall.

**Bloomberg terminal** — A professional financial data terminal used by traders and analysts at large institutions. It uses its own ticker naming convention (e.g. `SHEL LN` for Shell on the London Stock Exchange). This tool accepts Bloomberg-format tickers.

**Bullish** — A positive outlook on an investment, meaning you expect the price to rise.

**Candlestick chart** — A type of financial chart where each "candle" represents one day's trading. The body of the candle spans from the opening price to the closing price. The thin "wicks" above and below show the day's high and low. Green candles mean the price closed higher than it opened; red means it closed lower.

**CIO (Chief Investment Officer)** — The senior executive responsible for an investment firm's overall strategy. In this tool, the CIO is an AI agent that reads all five specialist reports and produces the final investment verdict.

**CLI (Command Line Interface)** — Interacting with a program by typing text commands in a terminal window, rather than using a graphical interface with buttons and menus.

**Dependency** — A library or software package that a program relies on to run. This project's dependencies are listed in `requirements.txt`.

**EMA (Exponential Moving Average)** — A moving average that gives more weight to recent prices, making it more responsive to new price movements than a simple average. Used to compute MACD.

**EPS (Earnings Per Share)** — A company's net profit divided by its number of outstanding shares. A key metric watched by investors.

**EV/EBITDA** — Enterprise Value divided by EBITDA. A valuation ratio used to compare companies regardless of their capital structure (how much debt they carry).

**FCF (Free Cash Flow)** — The cash a company generates after paying for capital expenditures (investments in equipment, facilities, etc.). Considered a reliable measure of a company's true profitability.

**MACD (Moving Average Convergence Divergence)** — A momentum indicator that measures the relationship between two exponential moving averages (12-period and 26-period). When the MACD line crosses above its signal line, it is considered a bullish signal; crossing below is bearish.

**Market cap (Market Capitalisation)** — The total market value of all a company's outstanding shares, calculated as share price multiplied by number of shares. A proxy for the company's total size.

**mplfinance** — A Python library specifically designed for plotting financial charts (candlestick, OHLCV). This project uses it to generate the chart embedded in the PDF.

**OHLCV** — Open, High, Low, Close, Volume. The five standard data points recorded for each trading day.

**OpenRouter** — A service that provides unified access to many AI models (Claude, GPT, Gemini, etc.) through a single API. This project uses OpenRouter to run all the AI agents.

**P/E ratio (Price-to-Earnings)** — The stock price divided by earnings per share. A high P/E means investors expect fast future growth; a low P/E suggests the market has more modest expectations.

**PDF (Portable Document Format)** — A file format that preserves layout and formatting regardless of what device or software opens it. This tool produces PDF reports.

**pip** — Python's built-in package manager. Used to install libraries: `pip install something`.

**Python** — The programming language this project is written in. Version 3.10 or higher is required.

**ReportLab** — A Python library for programmatically generating PDF documents. This project uses it to assemble the final report layout.

**RSI (Relative Strength Index)** — A momentum oscillator scaled from 0 to 100. Readings above 70 are traditionally considered "overbought" (the stock may have risen too far too fast); below 30 is "oversold". RSI-14 uses the past 14 trading days.

**SMA (Simple Moving Average)** — The arithmetic mean of closing prices over a specified number of days. SMA-200 is the average of the last 200 trading days and is widely watched as a long-term trend indicator. Prices sustained above their SMA-200 are generally considered to be in an uptrend.

**Streamlit** — A Python library for creating interactive web applications. This project uses it for the browser-based interface (`app.py`).

**Ticker symbol** — A short code used to identify a publicly traded stock on an exchange. Examples: `AAPL` (Apple), `MSFT` (Microsoft), `NVDA` (Nvidia), `SHEL.L` (Shell on the London Stock Exchange).

**Virtual environment** — An isolated Python installation dedicated to one project. It keeps that project's library versions separate from the rest of your system so different projects don't conflict with each other.

**Web search plugin** — An OpenRouter feature that lets AI models search the internet in real time while generating a response. The `:online` suffix on model names (e.g. `claude-3.5-haiku:online`) enables this. The five research agents use it; the CIO synthesizer does not.

**yfinance** — A free Python library that downloads stock price data from Yahoo Finance. This project uses it to fetch live prices and historical OHLCV data.

**52-week high / low** — The highest and lowest prices at which a stock has traded over the past 52 weeks (one year). Used as a reference point for how extended or depressed the current price is relative to its recent range.