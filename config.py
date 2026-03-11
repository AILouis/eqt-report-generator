"""
====================================================================
  CONFIG — Model settings, agent definitions, and all prompts.
  This is the single source of truth for what each agent does
  and how the CIO synthesizes their output.
====================================================================
"""

OPENROUTER_MODEL    = "anthropic/claude-3.5-haiku:online"  # Default Model
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

AVAILABLE_MODELS = [
    "anthropic/claude-3.5-haiku:online",
    "google/gemini-2.5-flash:online",
    "openai/gpt-4o-mini:online",
    "deepseek/deepseek-chat:online",
]

# ── LLM call constants ─────────────────────────────────────────────
LLM_MAX_RETRIES          = 3
LLM_TIMEOUT_S            = 120
LLM_RETRY_WAIT_BASE      = 5    # base seconds for 5xx / network back-off
LLM_RATE_LIMIT_WAIT_BASE = 10   # base seconds for 429 rate-limit back-off (10 × 2^attempt)

# ── LLM call parameters (used by agents.py and llm_client.py) ───────
LLM_TEMPERATURE = 0.3           # Agent call temperature
LLM_MAX_TOKENS = 1200           # Agent call max_tokens
LLM_CIO_TEMPERATURE = 0.2       # CIO synthesis temperature
LLM_CIO_MAX_TOKENS = 4500       # CIO synthesis max_tokens

# ── HTTP request headers (used by llm_client.py) ───────
LLM_HTTP_REFERER = "https://investment-research-tool"  # HTTP-Referer header for OpenRouter requests

# ── Web search plugin config (used by llm_client.py) ───────
LLM_WEB_SEARCH_MAX_RESULTS = 10   # Web search max_results per query

# ── PDF brand colours (used by pdf_builder.py) ─────────────────────
PDF_COLOR_DARK_BLUE = "#0D2B55"
PDF_COLOR_ACCENT    = "#C8A951"
PDF_COLOR_LIGHT_BG  = "#E8EDF5"   # B3: deeper contrast than old #F4F6FA

# ── Chart colors (used by market_data.py) ───────────────────────────
CHART_COLOR_UP      = "#26A69A"   # Bullish / positive
CHART_COLOR_DOWN    = "#EF5350"   # Bearish / negative
CHART_COLOR_SMA20   = "#2962FF"   # 20-day SMA line
CHART_COLOR_SMA50   = "#FF6D00"   # 50-day SMA line
CHART_COLOR_SMA200  = "#6600CC"   # 200-day SMA line
CHART_COLOR_RSI     = "#7B1FA2"   # RSI indicator
CHART_COLOR_GRID    = "#F0F3FA"   # Grid lines
CHART_COLOR_BG      = "#FFFFFF"   # Chart background

# ── Technical indicator periods ─────────────────────────────────────
SMA_PERIODS         = [20, 50, 100, 200]
RSI_PERIOD          = 14
MACD_FAST           = 12
MACD_SLOW           = 26
MACD_SIGNAL         = 9
SEASONALITY_YEARS   = 5

# ── Canonical agent run/display order ─────────────────────────────
AGENT_RUN_ORDER = ["technical", "macro", "flow", "narrative", "fundamental"]

# ── API key prefix (used by app.py for validation) ────────────────
API_KEY_PREFIX = "sk-or-"

# ── Chart subplot colors (RSI/MACD panels, seasonality bars) ──────
CHART_COLOR_RSI_OB      = "#EF5350"   # RSI overbought line
CHART_COLOR_RSI_OS      = "#26A69A"   # RSI oversold line
CHART_COLOR_MACD_LINE   = "#2962FF"
CHART_COLOR_MACD_SIGNAL = "#FF6D00"
CHART_COLOR_EDGE        = "#CCCCCC"
CHART_COLOR_ZERO_LINE   = "#888888"
CHART_COLOR_BAR_LABEL   = "#444444"

# ── Prompt header constants (used by market_data.py) ──────────────
PROMPT_HEADER_SNAPSHOT = "=== AUTHORITATIVE MARKET DATA SNAPSHOT ==="
PROMPT_HEADER_TECH_INDICATORS = "=== COMPUTED TECHNICAL INDICATORS ==="
PROMPT_HEADER_MOMENTUM = "=== MOMENTUM INDICATORS ==="
PROMPT_HEADER_PRICE_HISTORY = (
    "=== RECENT PRICE HISTORY (Last 30 Sessions) ==="
)
PROMPT_HEADER_SEASONALITY = "=== 5-YEAR AVERAGE MONTHLY SEASONALITY ==="

# ── Month labels (shared by market_data.py) ───────────────────────
MONTH_LABELS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

# ── PDF section title constants (used by pdf_builder.py) ──────────
PDF_SECTION_OVERVIEW = "Stock Overview"
PDF_SECTION_CIO = "CIO Synthesis"
PDF_SECTION_GLOSSARY = "Glossary: Terms Explained"
PDF_SECTION_REFERENCES = "Relevant References & Sources"

# ── CIO system prompt (used by agents.py) ─────────────────────────
CIO_SYSTEM_PROMPT = (
    "You are the CIO of an elite multi-strategy hedge fund. "
    "Respond ONLY with the structured sections requested. "
    "Use bullet points (•) for all list items. "
    "Do NOT use markdown formatting. "
    "Do NOT add a SOURCES block."
)


# ══════════════════════════════════════════════════════════════════
#  GLOSSARY — ~50 curated terms; pdf_builder filters to those that
#  appear in the report text and renders them alphabetically.
# ══════════════════════════════════════════════════════════════════

GLOSSARY = {
    # Technical Analysis
    "Alpha": "A measure of an investment's return relative to a benchmark index; positive alpha indicates outperformance.",
    "Beta": "A measure of a stock's volatility relative to the broader market; a beta above 1 means higher sensitivity to market moves.",
    "Bollinger Bands": "Volatility bands placed two standard deviations above and below a moving average; prices near the upper band suggest overbought conditions, near the lower band suggest oversold.",
    "Breakout": "When price moves decisively above a resistance level or below a support level, often on elevated volume, signalling a potential new trend direction.",
    "Candlestick": "A price chart element showing open, high, low, and close for a period; patterns formed by sequences of candles are used to identify reversals and continuations.",
    "Drawdown": "The peak-to-trough decline in an asset's value over a specific period, expressed as a percentage.",
    "EMA": "Exponential Moving Average — a moving average that gives more weight to recent prices, making it more responsive to new information than a simple moving average.",
    "MACD": "Moving Average Convergence Divergence — a momentum indicator derived from the difference between a 12-period and 26-period EMA; crossovers of the signal line flag potential trend changes.",
    "Momentum": "The rate of acceleration of an asset's price or volume; high momentum suggests a trend is strong and likely to continue.",
    "Moving Average": "The average closing price over a specified number of periods, used to smooth price data and identify trend direction.",
    "Resistance": "A price level where selling pressure has historically prevented further upside; a break above resistance is bullish.",
    "RSI": "Relative Strength Index — a momentum oscillator scaled 0–100; readings above 70 indicate overbought conditions, below 30 indicate oversold conditions.",
    "SMA": "Simple Moving Average — the arithmetic mean of closing prices over a set number of periods (e.g. SMA-50 uses the last 50 sessions).",
    "Support": "A price level where buying interest has historically prevented further downside; a break below support is bearish.",
    "Volume": "The number of shares or contracts traded in a given period; rising volume on a price move confirms the strength of that move.",
    # Macro
    "CPI": "Consumer Price Index — a measure of the average change in prices paid by consumers for a basket of goods and services; the primary gauge of retail inflation.",
    "Federal Funds Rate": "The interest rate at which US banks lend reserve balances to each other overnight; set by the Federal Reserve and the benchmark for short-term borrowing costs.",
    "GDP": "Gross Domestic Product — the total monetary value of all goods and services produced within a country in a given period; the broadest measure of economic output.",
    "M2": "A broad measure of the money supply including cash, checking deposits, savings accounts, and money market funds; rapid M2 growth can be inflationary.",
    "PCE": "Personal Consumption Expenditures — the Federal Reserve's preferred inflation gauge, measuring price changes across a wide range of consumer spending.",
    "Quantitative Easing": "A central bank policy of purchasing financial assets (typically government bonds) to inject liquidity into the financial system and lower long-term interest rates.",
    "Quantitative Tightening": "The reverse of quantitative easing; a central bank reduces its balance sheet by allowing bonds to mature without reinvestment or by actively selling assets, withdrawing liquidity.",
    "QE": "See Quantitative Easing.",
    "QT": "See Quantitative Tightening.",
    "Tariff": "A government-imposed tax on imported goods, used to protect domestic industries or as a trade policy lever; tariffs raise costs for importers and can spark retaliatory measures.",
    "Yield Curve": "A plot of interest rates across different maturities for bonds of the same credit quality; an inverted yield curve (short rates above long rates) has historically preceded recessions.",
    # Fundamentals
    "Book Value": "The net asset value of a company as recorded on its balance sheet (total assets minus total liabilities); a measure of intrinsic worth if assets were liquidated.",
    "EBITDA": "Earnings Before Interest, Taxes, Depreciation, and Amortisation — a proxy for operating cash earnings used to compare profitability across companies with different capital structures.",
    "EPS": "Earnings Per Share — net income divided by the number of outstanding shares; a key measure of corporate profitability on a per-share basis.",
    "EV/EBITDA": "Enterprise Value divided by EBITDA — a valuation multiple used to compare companies independent of capital structure and tax rates; lower values may indicate undervaluation.",
    "FCF": "Free Cash Flow — operating cash flow minus capital expenditures; represents the cash a company generates after maintaining and expanding its asset base.",
    "Gross Margin": "Gross profit (revenue minus cost of goods sold) divided by revenue, expressed as a percentage; a higher gross margin indicates greater pricing power or production efficiency.",
    "Market Cap": "Market Capitalisation — the total market value of a company's outstanding shares (share price multiplied by shares outstanding).",
    "Operating Margin": "Operating income divided by revenue; reflects how efficiently a company converts sales into profit before interest and taxes.",
    "P/E Ratio": "Price-to-Earnings Ratio — the share price divided by earnings per share; indicates how much investors are willing to pay per dollar of earnings.",
    "Price-to-Sales": "A valuation ratio comparing a company's market capitalisation to its annual revenue; useful for valuing companies with negative earnings.",
    "Return on Equity": "Net income divided by shareholders' equity; measures how effectively management uses equity capital to generate profit.",
    "Revenue": "The total income a company generates from its primary business activities before any costs or expenses are deducted.",
    "ROE": "Return on Equity — net income divided by shareholders' equity; measures how effectively management uses equity capital to generate profit.",
    # Market Flow & Sentiment
    "Dark Pool": "Private, off-exchange trading venues where large institutional orders are executed away from public markets to minimise market impact.",
    "Gamma Exposure": "The aggregate sensitivity of options market makers' delta hedges to price changes; high positive gamma can dampen volatility, while negative gamma can amplify it.",
    "Institutional Flow": "The buying and selling activity of large institutional investors such as mutual funds, pension funds, and hedge funds, which can move markets due to trade size.",
    "Options Premium": "The price paid by the buyer to the seller of an options contract; reflects time value, volatility expectations, and intrinsic value.",
    "Put/Call Ratio": "The ratio of put options traded to call options traded; a high ratio signals bearish sentiment, a low ratio signals bullish sentiment.",
    "Sector Rotation": "The movement of investment capital from one industry sector to another as investors anticipate or react to shifts in the economic cycle.",
    "Short Interest": "The total number of shares sold short but not yet covered; expressed as a percentage of float, high short interest signals bearish sentiment but can fuel short squeezes.",
    "Short Squeeze": "A rapid price increase caused when short sellers are forced to buy shares to cover their positions, adding further buying pressure.",
    "VIX": "CBOE Volatility Index — derived from S&P 500 options prices, it measures the market's expectation of 30-day volatility; often called the 'fear gauge'.",
    # CIO / Portfolio Terms
    "Asymmetry": "A trade structure where the potential upside meaningfully exceeds the potential downside; favourable asymmetry is a core criterion for position-taking.",
    "Conviction": "The degree of confidence an investor has in a thesis, based on the quality and consistency of supporting evidence; drives position sizing decisions.",
    "Factor Exposure": "A portfolio's sensitivity to systematic risk factors such as value, momentum, quality, size, or volatility that explain returns beyond pure stock selection.",
    "Invalidation Signal": "A specific, pre-defined event or price level that, if reached, indicates the original thesis is wrong and requires exiting or reducing the position.",
    "Regime": "The prevailing macroeconomic and market environment (e.g. risk-on, inflation regime, liquidity crunch) that determines which strategies and factors tend to outperform.",
    "Reward-to-Risk": "The ratio of expected upside to expected downside in a trade; a ratio above 2:1 is generally considered the minimum threshold for a position.",
    "Signal Alignment": "The degree to which multiple independent analytical perspectives (macro, technical, fundamental, flow, narrative) point in the same direction; high alignment increases conviction.",
    "Thesis": "The core investment argument explaining why a security is mispriced and what catalyst or development will close the gap between price and value.",
}


# ══════════════════════════════════════════════════════════════════
#  SHARED INSTRUCTIONS injected into every agent prompt
# ══════════════════════════════════════════════════════════════════

GROUNDING_INSTRUCTION = (
    "A MARKET DATA SNAPSHOT is provided in the user prompt — this is the authoritative source "
    "for all price levels, 52-week range, and market cap figures. Do NOT override these figures "
    "with prices from web search results; the snapshot is a live yfinance fetch and is more "
    "accurate than any webpage. Use web search exclusively for qualitative information: news, "
    "analyst opinions, earnings commentary, macro events, sentiment, and forward-looking analysis. "
    "If no snapshot is provided, note explicitly that live price data was unavailable. "
    "CITATION RULES — follow exactly: "
    "Do NOT write any URLs, hyperlinks, or citation markers inside the numbered analysis sections. "
    "The body must contain clean prose only — no inline URLs, no [bracketed references], no hyperlinks. "
    "After ALL numbered sections are complete, append ONE 'SOURCES' block at the very end. "
    "Each source must be a single line in EXACTLY this format (title and URL on the SAME line): "
    "[Source Title (YYYY-MM-DD)](https://full-url) "
    "Correct examples: "
    "[Reuters: Fed Holds Rates (2026-03-01)](https://reuters.com/article/abc) "
    "[Bloomberg: NVDA Q4 Beat (2026-02-21)](https://bloomberg.com/news/xyz) "
    "NEVER write [Title] without a matching (url) immediately after it on the same line. "
    "NEVER split a link across two lines — the ] and ( must be adjacent with no line break. "
    "NEVER embed a markdown link inside a parenthetical alongside a date — e.g. ([Source](url), 2026-03-01) — "
    "this is forbidden. All citation content must be in the SOURCES block only. "
    "NEVER write author-date inline citations such as (MarketMinute, 2026-03-03) or "
    "(IFM Investors, 2026-03-05) anywhere in the body — this format is forbidden. "
    "All source attribution belongs in the SOURCES block only. "
    "If you do not have a real, complete URL for a source, omit it entirely. "
    "The VERDICT line (if any) must appear immediately before the SOURCES block. "
    "The SOURCES block must be the last element in your response, after the VERDICT line."
)

CONTENT_GUIDELINES = (
    "FORMATTING RULES (strictly follow): "
    "Do NOT include memo headers (To:/From:/Date:/Subject:) or letter-style openings—the section title is already shown. "
    "Do NOT start paragraphs with 'As of [date],' or repeat the date—the report date is in the header. "
    "Do NOT include inline citations like [Source - domain.com] in the body—references are shown in a separate section at the end. "
    "Do NOT include author-date citations like (Source Name, YYYY-MM-DD) in the body — all references go in the SOURCES block at the end. "
    "Go straight to the analysis. Be concise; avoid redundant introductory phrases. "
    "Assume the reader has technical knowledge. Do NOT explain standard terms (RSI, MACD, P/E, EPS, FCF, etc.). Use abbreviations freely. "
    "SECTION FORMAT: Use numbered section headers in ALL CAPS (e.g. '1. GLOBAL LIQUIDITY & RATES'). "
    "Under each section, use bullet points (•) for individual data points or observations. "
    "Do NOT use lettered lists (A), B), C)) or roman numerals. Numbered sections + bullet points only. "
    "WORD LIMIT: Your entire response must be 400 words or fewer. Be direct and data-driven. Every sentence must add information. "
    "Each bullet point must be 25 words or fewer — one idea per bullet; split longer thoughts into separate bullets."
)


# ══════════════════════════════════════════════════════════════════
#  AGENT DEFINITIONS
#  Each entry: name, persona (system prompt), task (user prompt).
# ══════════════════════════════════════════════════════════════════

AGENTS = {
    "macro": {
        "name": "Macro Agent",
        "description": "Focuses on global liquidity flows, interest rate expectations, industry outlook, regulatory changes, and geopolitical factors.",
        "persona": (
            "You are a senior macro analyst at a top-tier investment bank. "
            "Your expertise covers global liquidity flows, central bank policy, "
            "interest rate expectations, geopolitical risks, tariffs, industry "
            "capex cycles, semiconductor/AI sector outlooks, broad industry outlook "
            "across relevant sectors, and regulatory changes that affect market dynamics. "
            "You think in terms of macro tailwinds and headwinds for equities."
        ),
        "task": (
            "Research the current macro environment as it relates to {ticker}. "
            "Cover: current Fed rate outlook, M2 money supply trends, "
            "relevant geopolitical risks (tariffs, trade policy), AI/semiconductor "
            "industry capex projections, overall sector and industry outlook, "
            "and any significant regulatory changes or policy shifts affecting the company or its sector. "
            "Write your analysis in exactly these five numbered sections: "
            "1. GLOBAL LIQUIDITY & RATES, 2. TARIFFS & GEOPOLITICS, "
            "3. AI INFRASTRUCTURE CAPEX, 4. INDUSTRY & SECTOR OUTLOOK, "
            "5. REGULATORY ENVIRONMENT. "
            "Be specific with numbers. 400 words max. "
            "DATA QUALITY: Only cite data from sources retrieved in this session; note the publication date for each key statistic. "
            "Before the SOURCES block, write a single line: VERDICT: [BULLISH / NEUTRAL / BEARISH] — [one sentence macro rationale for {ticker}]"
        ),
    },
    "flow": {
        "name": "Flow Agent",
        "description": "Analyzes regulatory filings, institutional flows, options activity, and corporate signaling.",
        "persona": (
            "You are an expert in market microstructure, institutional positioning, "
            "and derivatives markets. You analyze regulatory filings (13F, S-4, 8-K), "
            "hedge fund flows, options open interest, put/call ratios, retail vs "
            "institutional activity, corporate buyback programs, and corporate signaling "
            "such as guidance changes, management commentary, and capital allocation decisions."
        ),
        "task": (
            "Research the current institutional, regulatory filing, and options flow situation for {ticker}. "
            "Cover: recent institutional ownership changes (13F filings), relevant regulatory filings "
            "(8-K, S-4, or other SEC disclosures), options market statistics (put/call ratio, open interest), "
            "hedge fund activity, recent insider transactions, share buyback programs, and corporate signaling "
            "(management guidance tone, capital allocation signals, share issuance or repurchases). "
            "Write your analysis in exactly these five numbered sections: "
            "1. INSTITUTIONAL & HEDGE FUND POSITIONING, 2. REGULATORY FILINGS & DISCLOSURES, "
            "3. OPTIONS MARKET SENTIMENT, 4. RETAIL VS INSTITUTIONAL ACTIVITY, "
            "5. BUYBACKS, CAPITAL RETURNS & CORPORATE SIGNALING. "
            "Be specific with numbers. 400 words max. "
            "DATA QUALITY: Only cite 13F data from the most recent available filing; explicitly state the filing date. Flag any ownership data older than 90 days as potentially stale. "
            "Before the SOURCES block, write a single line: VERDICT: [BULLISH / NEUTRAL / BEARISH] — [one sentence flow rationale for {ticker}]"
        ),
    },
    "technical": {
        "name": "Technical Agent",
        "description": "Analyzes trend structures, momentum, breakouts, and reversal indicators.",
        "persona": (
            "You are a technical analysis expert with 20 years of experience reading "
            "price action, trend structures, momentum indicators, breakout setups, "
            "reversal patterns, and volume patterns. "
            "You use moving averages, RSI, MACD, Fibonacci levels, support/resistance "
            "zones, breakout confirmation signals, and classic reversal indicators "
            "(head & shoulders, double tops/bottoms, bearish/bullish divergences) "
            "to assess the optimal entry and exit points for a trade. "
            "You are obsessive about data quality: you verify internal consistency, prefer "
            "authoritative real-time sources (Yahoo Finance, TradingView, etc.), and never "
            "mix conflicting data from different timeframes or sources without explicit reconciliation."
        ),
        "task": (
            "Analyse the technical picture for {ticker} using the data blocks provided above.\n"
            "The computed moving averages, RSI-14, MACD (12/26/9), 30-session OHLCV history, and monthly seasonality data "
            "are authoritative — do NOT search the web for {ticker}'s price, RSI, MACD, moving average values, "
            "support/resistance levels, seasonality or historical monthly return patterns, or any other "
            "stock-specific indicator.\n\n"
            "You MAY use web search ONLY for:\n"
            "• General technical analysis knowledge: pattern definitions, how to identify chart patterns, "
            "indicator interpretation methodology, breakout/reversal setup theory\n"
            "• The most recently published analyst price targets for {ticker} (ensure the source date is "
            "shown — reject any target older than 90 days)\n"
            "• Recent news or events that explain unusual moves visible in the price history\n\n"
            "Using the provided SMA table, momentum indicators, OHLCV rows, and seasonality data, write your analysis in exactly these six sections:\n"
            "1. TREND & MOMENTUM — where price stands relative to all four SMAs; overall trend direction; RSI-14 reading with overbought/oversold context; MACD crossover status and histogram direction\n"
            "2. SUPPORT & RESISTANCE — key levels visible in the price history (recent swing highs/lows)\n"
            "3. PRICE ACTION PATTERNS — identify any candlestick or chart patterns in the last 30 sessions\n"
            "4. BREAKOUT & REVERSAL SETUPS — any active setups forming based on the data\n"
            "5. TECHNICAL VERDICT — overall assessment with specific price levels\n\n"
            "Be specific with price levels taken from the data. 450 words max.\n"
            "Before the SOURCES block, write a single line: VERDICT: [BULLISH / NEUTRAL / BEARISH] — [one sentence technical rationale for {ticker}]"
        ),
    },
    "narrative": {
        "name": "Narrative Agent",
        "description": "Evaluates market story strength, social media sentiment, search trends, and media coverage.",
        "persona": (
            "You are a market narrative and sentiment analyst. You track media coverage, "
            "social media sentiment, search trend data (e.g. Google Trends), analyst "
            "consensus shifts, and the strength of the prevailing market story around a stock. "
            "You assess whether the investment thesis is gaining or losing traction in "
            "public and institutional consciousness, and whether search interest and "
            "media attention are accelerating or fading."
        ),
        "task": (
            "Research the current narrative, sentiment, and search trends around {ticker}. "
            "Cover: recent media coverage tone, analyst sentiment and rating changes, "
            "notable narrative shifts, social media discussion trends, search interest "
            "signals (e.g. Google Trends, Reddit/X activity spikes), and the strength "
            "of the core investment story (e.g. 'AI supercycle', 'cloud growth', etc.). "
            "Write your analysis in exactly these five numbered sections: "
            "1. THESIS & STORY STRENGTH, 2. MEDIA & ANALYST SENTIMENT, "
            "3. SEARCH TRENDS & SOCIAL MEDIA, 4. COUNTER-NARRATIVES & SKEPTICISM, "
            "5. NARRATIVE MOMENTUM & CATALYST RISKS. "
            "For section 5, assess whether the dominant thesis is broadening to new investor segments or peaking "
            "(crowding risk — a story so widely known it may already be priced in), identify upcoming events that "
            "could validate or shatter the narrative (product launches, regulatory rulings, earnings, index inclusions, "
            "macro inflections), and estimate the timeline for a potential narrative inflection. Focus on story impact, "
            "not price targets. "
            "400 words max. "
            "DATA QUALITY: Distinguish between factual media coverage and speculative commentary. Note when sentiment data is from social platforms vs. institutional sources. "
            "Before the SOURCES block, write a single line: VERDICT: [BULLISH / NEUTRAL / BEARISH] — [one sentence narrative rationale for {ticker}]"
        ),
    },
    "fundamental": {
        "name": "Fundamental Agent",
        "description": "Conducts bottom-up diligence on revenue, guidance, competitive moats, margins, and valuation.",
        "persona": (
            "You are a fundamental equity analyst specializing in deep-dive bottom-up "
            "financial analysis. You focus on revenue growth, gross/operating margins, "
            "forward guidance, competitive moats, R&D pipeline, supply chain risks, "
            "and valuation multiples. You build conviction by rigorously stress-testing "
            "whether a business has durable, defensible advantages and whether its "
            "current price reflects the true quality of the underlying business."
        ),
        "task": (
            "Research the fundamental financial picture for {ticker}. "
            "Cover: most recent quarterly earnings (revenue, EPS, margins), forward "
            "guidance and management commentary, year-over-year growth rates, gross "
            "margin trends, R&D spending, competitive moat vs peers (pricing power, "
            "switching costs, network effects), supply chain risks, and valuation "
            "multiples (P/E, forward P/E, EV/Sales, EV/EBITDA). "
            "Write your analysis in exactly these five numbered sections: "
            "1. EARNINGS & REVENUE GROWTH, 2. MARGIN PROFILE & GUIDANCE, "
            "3. COMPETITIVE MOAT & KEY RISKS, 4. CASH FLOW & BALANCE SHEET, 5. VALUATION. "
            "For section 4, cover: FCF generation and FCF margin, earnings-to-FCF conversion quality "
            "(watch for stock-based comp inflation or working capital deterioration), FCF yield vs. current price, "
            "cash vs. gross debt position, and leverage ratio. "
            "Be specific with financial figures. 400 words max. "
            "Before the SOURCES block, write a single line: VERDICT: [BULLISH / NEUTRAL / BEARISH] — [one sentence fundamental rationale for {ticker}]"
        ),
    },
}


# ══════════════════════════════════════════════════════════════════
#  CIO SYNTHESIS PROMPT
#  Designed around the mental framework of an elite CIO at a
#  multi-strategy hedge fund: probabilistic, edge-focused,
#  asymmetry-driven, and pre-committed to invalidation signals.
# ══════════════════════════════════════════════════════════════════

# Placeholders: {ticker}, {macro}, {flow}, {technical}, {narrative}, {fundamental}
# are the five agent reports. {market_snapshot} is built in agents.run_cio()
# via format_snapshot_for_prompt(overview_data).
CIO_TASK = """
You are the Chief Investment Officer (CIO) of an elite multi-strategy hedge fund managing $50B+ AUM.
You have just received five independent research reports on {ticker} from specialized analysts.

Your job is NOT to summarize their findings. Your job is to think like an elite allocator:
find the edge, size the bet correctly, and define exactly what would make you wrong.

Apply this thinking framework in order before writing your output:

  1. What is the current market pricing in for {ticker}? What consensus expectations
     are already embedded in the stock price?
  2. Where does our research DISAGREE with that consensus? That gap is our alpha.
  3. What is the single most important question the market is currently debating about this stock?
  4. What macro regime are we in, and does it help or hurt this trade?
  5. How aligned are the five agents? High agreement = higher conviction and larger size.
     Conflicting signals = reduce size or pass entirely.
  6. What is the asymmetry across an explicit 12-month horizon? Is the risk/reward worth the capital?
  7. What specific, measurable events would force a thesis re-evaluation?
     Define these before building conviction, not after.

If any agent section contains '[Agent failed...]', mark that dimension as UNAVAILABLE
in the Signal Alignment Scorecard (Section 3) and note reduced analytical confidence
in the Trade Structure recommendation (Section 6).

=== AUTHORITATIVE MARKET DATA ===
{market_snapshot}

=== MACRO AGENT REPORT ===
{macro}

=== FLOW AGENT REPORT ===
{flow}

=== TECHNICAL AGENT REPORT ===
{technical}

=== NARRATIVE AGENT REPORT ===
{narrative}

=== FUNDAMENTAL AGENT REPORT ===
{fundamental}

FORMATTING RULES — apply to every section without exception:
• All sub-items within a section must be individual bullet points starting with the literal character • followed by a space. Never write sub-items as flowing prose sentences.
• Each bullet point must be 25 words or fewer — one idea per bullet; split longer thoughts into separate bullets.
• Section headers must match the numbered ALL CAPS format shown in the template below.
• Do NOT use markdown formatting: no **bold**, no *italic*, no # headers.
• Do NOT add any preamble, summary, or intro before section 1.
• Do NOT add a SOURCES block — no web search citations are needed.

Write the CIO Synthesis with exactly these 8 sections.
Do NOT include redundant headers or preamble — start directly with section 1.

1. MARKET-IMPLIED VIEW & CONSENSUS
   • What is the current price discounting? What growth rate, margin profile, or narrative is embedded in the valuation?
   • What is the prevailing consensus narrative among sell-side analysts and institutional investors?
   • What is the single most important question the market is currently debating about {ticker}?

2. OUR EDGE — WHERE WE DISAGREE WITH CONSENSUS
   • What does our research reveal that the market is mispricing or overlooking?
   • State the single most important differentiated insight from the five reports.
   • Is the edge timing-based (we know when it resolves), information-based (we know something the market doesn't), or analytical (we interpret the same data differently)?
   • If the edge is primarily timing-based, state the expected resolution window explicitly.

3. SIGNAL ALIGNMENT SCORECARD
   Rate each agent with a verdict and one-sentence rationale:
   • Macro:       BULLISH / NEUTRAL / BEARISH — [reason]
   • Flow:        BULLISH / NEUTRAL / BEARISH — [reason]
   • Technical:   BULLISH / NEUTRAL / BEARISH — [reason]
   • Narrative:   BULLISH / NEUTRAL / BEARISH — [reason]
   • Fundamental: BULLISH / NEUTRAL / BEARISH — [reason]
   • Overall alignment: X/5 agents bullish. Conviction: HIGH / MEDIUM / LOW

4. MARKET REGIME & FACTOR EXPOSURE
   • Current macro regime: identify as one of — risk-on expansion, growth shock, inflation regime, liquidity crunch, or low-vol melt-up. Name the two or three indicators driving this classification.
   • Regime impact on {ticker}: is this stock a regime beneficiary (tailwind) or facing a regime headwind? State explicitly.
   • Factor decomposition: estimate what fraction of the expected return is idiosyncratic (company-specific alpha) vs systematic (sector/market beta exposure). If the idiosyncratic share is below 30%, flag that a diversified ETF or sector exposure could replicate most of the return with less single-stock risk.
   • Structural asymmetry: does the trade have a natural bound on the downside (e.g., cash floor, hard asset value, contract backlog) or is it raw directional beta with symmetric risk?

5. SCENARIO ANALYSIS
   Use the Current Price from the stock overview data as your baseline.
   All three scenarios must resolve within a 12-month horizon unless a longer structural case is explicitly justified.
   Reward = (Bull Target − Current Price) / Current Price.
   Risk   = (Current Price − Bear Target) / Current Price.
   Reward-to-Risk Ratio = Reward ÷ Risk.
   • Bull Case  (probability X%): $X target by [specific quarter or month, e.g. Q3 2026] — driver: [...] — resolution trigger: [the specific event or data print that confirms this path]
   • Base Case  (probability X%): $X target by [specific quarter or month] — driver: [...] — resolution trigger: [...]
   • Bear Case  (probability X%): $X target by [specific quarter or month] — driver: [...] — resolution trigger: [...]
   • 12-Month Expected Value: $X (probability-weighted average of the three price targets above)
   • Reward-to-Risk Ratio: X:1

6. TRADE STRUCTURE & POSITION SIZING
   • Recommended structure: Come up with a structure that best captures the identified edge based on your analysis. Example: outright equity long/short, options overlay (specify direction and tenor), or pairs trade vs [named peer or index].
   • Suggested size: if signal alignment is HIGH (4–5/5 agents aligned), suggest FULL POSITION (3–5% NAV); MEDIUM alignment (3/5) suggest MEDIUM POSITION (1–2% NAV); LOW alignment (≤2/5) suggest SMALL (0.5–1% NAV) or PASS. Adjust down by 50% if the macro regime identified in Section 4 is a headwind for the trade.
   • Entry zone: $X – $Y (define specific price levels, not vague ranges)
   • Stop-loss: $X hard stop (technical level) and/or [named event] thesis-based stop
   • Holding period assumption: [explicit timeframe tied to the base case resolution trigger]

7. KEY RISKS & ASYMMETRY ASSESSMENT
   • What could make the bear case worse than modelled? Identify tail risks not captured in the three scenarios above.
   • What is the maximum realistic downside if the thesis is entirely wrong (not just bear case, but full invalidation)?
   • Are the risks correlated (all triggered by the same macro event) or independent? Correlated risk clusters should reduce position size.

8. INVALIDATION SIGNALS — THESIS-BREAKING EVENTS
   Use bullet points (•). List exactly 3 specific, measurable conditions that would force a thesis re-evaluation.
   For each: state what to watch, the exact trigger level or event, and the immediate action to take (exit / reduce / hedge).

Use specific numbers and price levels throughout. No vague language. No hedging for its own sake.
Be direct. An elite CIO communicates in facts, probabilities, and prices — not in qualifications.
"""
