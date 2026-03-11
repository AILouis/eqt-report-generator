"""
====================================================================
  TICKER RESOLVER — Normalises raw user input into a valid yfinance
  ticker symbol and looks up the company name for user confirmation.

  Handles:
    • Bloomberg space notation   "NVDA US"  → "NVDA"
                                 "SHEL LN"  → "SHEL.L"
                                 "7203 JP"  → "7203.T"
                                 "0700 HK"  → "0700.HK"
    • Bloomberg dot notation     "NVDA.US"  → "NVDA"
    • Reuters/Refinitiv codes    "NVDA.O"   → "NVDA"
    • Already-correct yfinance   "SHEL.L"   → "SHEL.L"  (unchanged)
    • Plain US ticker            "NVDA"     → "NVDA"    (unchanged)
====================================================================
"""

import re

import yfinance as yf

from yf_session import get_yf_session


# ── Bloomberg terminal exchange codes → yfinance suffixes ────────
# US exchange codes all map to "" (no suffix needed by yfinance).

_BLOOMBERG_SUFFIX: dict[str, str] = {
    # United States
    "US": "", "UN": "", "UW": "", "UQ": "", "UA": "",
    # United Kingdom
    "LN": ".L",
    # Germany
    "GY": ".DE", "GR": ".DE",  # XETRA / Frankfurt
    "GF": ".F",                  # Frankfurt floor
    # France
    "FP": ".PA",
    # Netherlands
    "NA": ".AS",
    # Belgium
    "BB": ".BR",
    # Italy
    "IM": ".MI",
    # Spain
    "SM": ".MC",
    # Finland
    "FH": ".HE",
    # Sweden
    "SS": ".ST", "SE": ".ST",
    # Norway
    "NO": ".OL",
    # Denmark
    "DC": ".CO",
    # Switzerland
    "SW": ".SW",
    # Poland
    "PW": ".WA",
    # Turkey
    "TI": ".IS",
    # Japan
    "JP": ".T",
    # Hong Kong
    "HK": ".HK",
    # China
    "CH": ".SS",   # Shanghai
    "CG": ".SZ",   # Shenzhen
    # Australia
    "AU": ".AX",
    # New Zealand
    "NZ": ".NZ",
    # Singapore
    "SP": ".SI",
    # Malaysia
    "MK": ".KL",
    # Thailand
    "TB": ".BK",
    # South Korea
    "KS": ".KS",   # KOSPI
    "KP": ".KQ",   # KOSDAQ
    # India
    "IN": ".NS",   # NSE (most liquid)
    "IB": ".BO",   # BSE
    # Taiwan
    "TW": ".TW",
    # Canada
    "CN": ".TO",   # Toronto
    "CV": ".V",    # TSX Venture
    # Brazil
    "BZ": ".SA", "BS": ".SA",
    # Mexico
    "MM": ".MX",
    # South Africa
    "SJ": ".JO",
}

# Reuters/Refinitiv single-letter exchange codes that mean "US" → strip them
_REUTERS_US_CODES = {"O", "N", "K", "A", "P"}


def _pad_hkex(code: str) -> str:
    """Zero-pad HKEX numeric codes to 4 digits (e.g. '700' → '0700')."""
    return code.zfill(4)


# ── Normalisation ─────────────────────────────────────────────────

def normalize_ticker(raw: str) -> str:
    """
    Convert raw user input into a yfinance-compatible ticker symbol.

    The function is intentionally conservative: when in doubt it returns
    the cleaned-up input unchanged and lets yfinance validation decide.
    """
    # Collapse whitespace, uppercase
    s = re.sub(r"\s+", " ", raw.strip()).upper()

    # ── Bloomberg space-separated exchange code: "NVDA US", "SHEL LN" ──
    m = re.match(r"^([A-Z0-9][A-Z0-9\.\-]*)[ ]+([A-Z]{2,3})$", s)
    if m:
        base, code = m.group(1), m.group(2)
        if code in _BLOOMBERG_SUFFIX:
            suffix = _BLOOMBERG_SUFFIX[code]
            # HKEX codes are zero-padded to 4 digits (e.g. 700 → 0700)
            if suffix == ".HK" and base.isdigit() and len(base) < 4:
                base = _pad_hkex(base)
            return base + suffix
        # Unknown code — drop it and hope the base is valid
        return base

    # ── Dot-separated: "NVDA.US", "NVDA.O", "0700.HK", "SHEL.L" ──
    m = re.match(r"^([A-Z0-9\-]+)\.([A-Z]{1,3})$", s)
    if m:
        base, ext = m.group(1), m.group(2)
        if ext == "US":
            return base
        if ext in _REUTERS_US_CODES:
            return base
        # HKEX codes are zero-padded to 4 digits (e.g. 700.HK → 0700.HK)
        if ext == "HK" and base.isdigit() and len(base) < 4:
            return _pad_hkex(base) + ".HK"
        # Everything else (.L, .T, .DE, …) is already a valid yfinance suffix
        return s

    # Plain ticker — return as-is
    return s


# ── yfinance lookup ───────────────────────────────────────────────

def _lookup(ticker: str) -> tuple[str, str | None]:
    """
    Single yfinance attempt for *ticker* (already normalised).

    Returns (ticker, company_name) on success, (ticker, None) on failure.
    """
    try:
        t = yf.Ticker(ticker, session=get_yf_session())
        info = t.info

        name = info.get("longName") or info.get("shortName") or None

        # yfinance returns a near-empty dict for invalid tickers.
        # Confirm we have price data as a proxy for a valid symbol.
        has_price = bool(
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("previousClose")
        )
        if not has_price:
            hist = t.history(period="5d")
            if hist.empty:
                return ticker, None

        return ticker, name

    except Exception:
        return ticker, None


def resolve_ticker(raw: str) -> tuple[str, str | None]:
    """
    Normalize *raw* and attempt to fetch the company name from yfinance.

    If the primary lookup fails and the ticker looks like a class-share
    with the hyphen omitted (e.g. BRKB, BRKA, BFB), a second attempt is
    made with a hyphen inserted before the final letter (BRK-B, BRK-A, BF-B).

    Returns:
        (normalized_ticker, company_name)
        company_name is None when the ticker can't be validated.
    """
    ticker = normalize_ticker(raw)

    # Primary attempt
    t, name = _lookup(ticker)
    if name:
        return t, name

    # Only retried when the primary lookup returned no company name.
    # Inserts a hyphen before the last letter for class-share tickers: BRKB → BRK-B, BFB → BF-B
    # Only applies to plain all-alpha tickers (no dots, no existing hyphens).
    m = re.match(r"^([A-Z]{2,})([A-Z])$", ticker)
    if m:
        candidate = f"{m.group(1)}-{m.group(2)}"
        t2, name2 = _lookup(candidate)
        if name2:
            return t2, name2

    return ticker, None
