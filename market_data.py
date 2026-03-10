"""
====================================================================
  MARKET DATA — Live stock data via yfinance and display formatters.
====================================================================
"""

import io
from datetime import datetime

import yfinance as yf

from yf_session import get_yf_session


# ── Currency display helpers (shared by format_snapshot_for_prompt and format_technical_block) ──

_CURRENCY_SYMBOLS: dict[str, str] = {
    "USD": "$", "GBP": "£", "GBp": "£", "EUR": "€", "HKD": "HK$",
    "JPY": "¥", "KRW": "₩", "AUD": "A$", "CAD": "C$",
    "CHF": "CHF ", "CNY": "¥", "SGD": "S$",
}
_ZERO_DECIMAL_CURRENCIES: set[str] = {"JPY", "KRW", "IDR", "VND"}


def fetch_stock_overview(ticker: str) -> dict | None:
    """
    Fetch key stock metrics for the report's overview section.

    Returns a dict with:
        company_name, current_price, change_1d_pct, change_5d_pct,
        change_ytd_pct, high_52w, low_52w, market_cap, volume
    Returns None if the fetch fails for any reason.
    """
    try:
        t = yf.Ticker(ticker, session=get_yf_session())
        info = t.info
        hist = t.history(period="1y")

        if hist.empty:
            return None

        current = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("previousClose")
            or float(hist["Close"].iloc[-1])
        )

        prev_close = (
            info.get("previousClose")
            or (float(hist["Close"].iloc[-2]) if len(hist) > 1 else current)
        )

        def _pct(now, old):
            return round((now - old) / old * 100, 2) if old else None

        change_1d = _pct(current, prev_close) if len(hist) >= 2 else None
        change_5d = _pct(current, hist["Close"].iloc[-5]) if len(hist) >= 5 else None

        current_year = datetime.now().year
        ytd_hist = hist[hist.index >= f"{current_year}-01-01"]
        change_ytd = _pct(current, float(ytd_hist["Close"].iloc[0])) if len(ytd_hist) > 0 else None

        high_52w = info.get("fiftyTwoWeekHigh") or float(hist["High"].max())
        low_52w  = info.get("fiftyTwoWeekLow")  or float(hist["Low"].min())

        market_cap = info.get("marketCap")
        volume = info.get("volume") or info.get("averageVolume")
        if volume is None and not hist.empty:
            volume = int(hist["Volume"].iloc[-1])

        company_name = info.get("longName") or info.get("shortName") or None
        currency = info.get("currency") or "USD"

        def _f(x):
            return round(float(x), 2) if x is not None else None

        return {
            "company_name":   company_name,
            "current_price":  round(float(current), 2),
            "change_1d_pct":  _f(change_1d),
            "change_5d_pct":  _f(change_5d),
            "change_ytd_pct": _f(change_ytd),
            "high_52w":       round(float(high_52w), 2),
            "low_52w":        round(float(low_52w), 2),
            "market_cap":     int(market_cap) if market_cap is not None else None,
            "volume":         int(volume)     if volume     is not None else None,
            "currency":       currency,
        }
    except Exception as e:
        print(f"  (Warning: overview fetch failed — {e})")
        return None


# ── Display formatters ────────────────────────────────────────────

def fmt_pct(v) -> str:
    """Format a percentage change, e.g. '+3.21%'."""
    return f"{v:+.2f}%" if v is not None else "—"


def fmt_price(v, currency="USD") -> str:
    """Format a price value with the correct currency symbol."""
    if v is None:
        return "—"
    zero_dec = currency in _ZERO_DECIMAL_CURRENCIES
    sym = _CURRENCY_SYMBOLS.get(currency, f"{currency} ")
    return f"{sym}{v:,.0f}" if zero_dec else f"{sym}{v:,.2f}"


def fmt_dollar(v, currency="USD") -> str:
    """Format a large monetary value (market cap) with correct currency symbol."""
    if v is None:
        return "—"
    sym = _CURRENCY_SYMBOLS.get(currency, f"{currency} ")
    if v >= 1e12:
        return f"{sym}{v / 1e12:.2f}T"
    if v >= 1e9:
        return f"{sym}{v / 1e9:.2f}B"
    if v >= 1e6:
        return f"{sym}{v / 1e6:.2f}M"
    return f"{sym}{v:,.0f}"


def format_snapshot_for_prompt(overview_data: dict | None) -> str:
    """Format live yfinance data as an authoritative snapshot block for agent prompts."""
    if overview_data is None:
        return ""

    currency = overview_data.get("currency", "USD") or "USD"
    sym = _CURRENCY_SYMBOLS.get(currency, f"{currency} ")
    zero_dec = currency in _ZERO_DECIMAL_CURRENCIES

    def _price(v):
        if v is None:
            return "N/A"
        return f"{sym}{v:,.0f} {currency}" if zero_dec else f"{sym}{v:,.2f} {currency}"

    def _pct(v):
        if v is None:
            return "N/A"
        return f"{v:+.2f}%"

    def _mcap(v):
        if v is None:
            return "N/A"
        return fmt_dollar(v, currency)

    def _vol(v):
        if v is None:
            return "N/A"
        if v >= 1e9:
            return f"{v / 1e9:.2f}B"
        if v >= 1e6:
            return f"{v / 1e6:.1f}M"
        if v >= 1e3:
            return f"{v / 1e3:.0f}K"
        return f"{v:,.0f}"

    now_str = datetime.now().strftime("%B %d, %Y %H:%M")
    ticker_raw = overview_data.get("ticker", "")
    company = overview_data.get("company_name") or "N/A"

    lines = [
        "=== AUTHORITATIVE MARKET DATA SNAPSHOT ===",
        "Source: yfinance (live fetch)",
        f"As of: {now_str} (system time)",
        "",
        f"Ticker:        {ticker_raw}",
        f"Company:       {company}",
        f"Current Price: {_price(overview_data.get('current_price'))}",
        f"1D Change:     {_pct(overview_data.get('change_1d_pct'))}",
        f"5D Change:     {_pct(overview_data.get('change_5d_pct'))}",
        f"YTD Change:    {_pct(overview_data.get('change_ytd_pct'))}",
        f"52W High:      {_price(overview_data.get('high_52w'))}",
        f"52W Low:       {_price(overview_data.get('low_52w'))}",
        f"Market Cap:    {_mcap(overview_data.get('market_cap'))}",
        f"Volume (last): {_vol(overview_data.get('volume'))}",
        "",
        "IMPORTANT: These figures are the authoritative ground truth for this report.",
        "=========================================",
    ]
    return "\n".join(lines)


def compute_technical_data(ticker: str) -> dict | None:
    """
    Compute SMA-20/50/100/200 and extract last 30 OHLCV sessions from 1Y history.

    Returns a dict with keys:
        sma20, sma50, sma100, sma200,
        dist20, dist50, dist100, dist200,   (% distance from current price)
        ohlcv_rows (list of dicts),
        currency, current_price
    Returns None on any exception.
    """
    try:
        t = yf.Ticker(ticker, session=get_yf_session())
        info = t.info
        hist = t.history(period="1y")

        if hist.empty or len(hist) < 20:
            return None

        close = hist["Close"]
        current = float(close.iloc[-1])
        currency = info.get("currency") or "USD"

        def _sma(n):
            if len(close) < n:
                return None
            return float(close.rolling(n).mean().iloc[-1])

        def _dist(sma):
            if sma is None:
                return None
            return (current - sma) / sma * 100

        sma20  = _sma(20)
        sma50  = _sma(50)
        sma100 = _sma(100)
        sma200 = _sma(200)

        # RSI-14
        rsi_val = None
        try:
            delta = hist["Close"].diff()
            gain  = delta.clip(lower=0).rolling(14).mean()
            loss  = (-delta.clip(upper=0)).rolling(14).mean()
            rs    = gain / loss
            rsi_series = 100 - (100 / (1 + rs))
            rsi_val = round(float(rsi_series.dropna().iloc[-1]), 2)
        except Exception:
            pass

        # MACD (12/26/9)
        macd_line = macd_signal = macd_hist_val = None
        try:
            ema12 = hist["Close"].ewm(span=12, adjust=False).mean()
            ema26 = hist["Close"].ewm(span=26, adjust=False).mean()
            macd_raw    = ema12 - ema26
            signal_raw  = macd_raw.ewm(span=9, adjust=False).mean()
            macd_line   = round(float(macd_raw.iloc[-1]), 4)
            macd_signal = round(float(signal_raw.iloc[-1]), 4)
            macd_hist_val = round(float((macd_raw - signal_raw).iloc[-1]), 4)
        except Exception:
            pass

        last30 = hist.tail(30).reset_index()
        ohlcv_rows = []
        for _, row in last30.iterrows():
            date_val = row["Date"]
            date_str = date_val.strftime("%Y-%m-%d") if hasattr(date_val, "strftime") else str(date_val)[:10]
            ohlcv_rows.append({
                "date":   date_str,
                "open":   float(row["Open"]),
                "high":   float(row["High"]),
                "low":    float(row["Low"]),
                "close":  float(row["Close"]),
                "volume": int(row["Volume"]),
            })

        # Seasonality: 5-year average monthly returns
        seasonality_by_month: dict[int, float] = {}
        try:
            hist5 = yf.Ticker(ticker, session=get_yf_session()).history(period="5y")
            if not hist5.empty and len(hist5) >= 50:
                monthly = hist5["Close"].resample("ME").last().pct_change().dropna()
                by_month = monthly.groupby(monthly.index.month).mean() * 100
                seasonality_by_month = {int(m): round(float(v), 2) for m, v in by_month.items()}
        except Exception:
            pass  # non-fatal — leave empty dict

        return {
            "sma20":       sma20,
            "sma50":       sma50,
            "sma100":      sma100,
            "sma200":      sma200,
            "dist20":      _dist(sma20),
            "dist50":      _dist(sma50),
            "dist100":     _dist(sma100),
            "dist200":     _dist(sma200),
            "rsi14":       rsi_val,
            "macd_line":   macd_line,
            "macd_signal": macd_signal,
            "macd_hist":   macd_hist_val,
            "ohlcv_rows":  ohlcv_rows,
            "ohlcv_df":    hist,
            "currency":    currency,
            "current_price": current,
            "seasonality_by_month": seasonality_by_month,
        }
    except Exception as e:
        print(f"  (Warning: technical data computation failed — {e})")
        return None


def format_technical_block(tech_data: dict | None, ticker: str = "") -> str:
    """
    Format computed technical indicators as an authoritative text block
    to inject into the technical agent's prompt.
    """
    if tech_data is None:
        return ""

    currency = tech_data.get("currency", "USD") or "USD"
    sym = _CURRENCY_SYMBOLS.get(currency, f"{currency} ")
    zero_dec = currency in _ZERO_DECIMAL_CURRENCIES

    def _p(v):
        if v is None:
            return "N/A"
        return f"{sym}{v:,.0f}" if zero_dec else f"{sym}{v:,.2f}"

    def _vol(v):
        if v is None:
            return "N/A"
        if v >= 1e9:
            return f"{v / 1e9:.1f}B"
        if v >= 1e6:
            return f"{v / 1e6:.1f}M"
        if v >= 1e3:
            return f"{v / 1e3:.0f}K"
        return f"{v:,.0f}"

    def _dist_str(d):
        if d is None:
            return "N/A"
        sign = "+" if d >= 0 else ""
        direction = "above" if d >= 0 else "below"
        return f"({sign}{d:.1f}% {direction})"

    now_str = datetime.now().strftime("%B %d, %Y %H:%M")
    current = tech_data.get("current_price")

    lines = [
        "=== COMPUTED TECHNICAL INDICATORS ===",
        f"Source: yfinance 1Y OHLCV (computed locally, as of {now_str})",
        "",
        "Price vs Moving Averages:",
        f"  Current:  {_p(current)}",
        f"  SMA-20:   {_p(tech_data.get('sma20'))}  {_dist_str(tech_data.get('dist20'))}",
        f"  SMA-50:   {_p(tech_data.get('sma50'))}  {_dist_str(tech_data.get('dist50'))}",
        f"  SMA-100:  {_p(tech_data.get('sma100'))}  {_dist_str(tech_data.get('dist100'))}",
        f"  SMA-200:  {_p(tech_data.get('sma200'))}  {_dist_str(tech_data.get('dist200'))}",
        "",
    ]

    # Momentum indicators section
    rsi_val     = tech_data.get("rsi14")
    macd_line   = tech_data.get("macd_line")
    macd_signal = tech_data.get("macd_signal")
    macd_hist_v = tech_data.get("macd_hist")

    if rsi_val is not None:
        if rsi_val > 70:
            rsi_interp = "Overbought (>70)"
        elif rsi_val < 30:
            rsi_interp = "Oversold (<30)"
        else:
            rsi_interp = "Neutral (30–70)"
    else:
        rsi_interp = None

    if macd_line is not None and macd_signal is not None:
        cross_status = "MACD above signal (bullish)" if macd_line >= macd_signal else "MACD below signal (bearish)"
    else:
        cross_status = None

    lines += [
        "=== MOMENTUM INDICATORS ===",
        f"  RSI-14:       {f'{rsi_val:.1f}' if rsi_val is not None else 'N/A'}  ({rsi_interp if rsi_interp else 'N/A'})",
        f"  MACD line:    {f'{macd_line:.4f}' if macd_line is not None else 'N/A'}",
        f"  Signal line:  {f'{macd_signal:.4f}' if macd_signal is not None else 'N/A'}",
        f"  Histogram:    {f'{macd_hist_v:.4f}' if macd_hist_v is not None else 'N/A'}  ({cross_status if cross_status else 'N/A'})",
        "",
        "=== RECENT PRICE HISTORY (Last 30 Sessions) ===",
        f"{'Date':<12}  {'Open':>10}  {'High':>10}  {'Low':>10}  {'Close':>10}  {'Volume':>10}",
    ]

    for row in tech_data.get("ohlcv_rows", []):
        lines.append(
            f"{row['date']:<12}  "
            f"{_p(row['open']):>10}  "
            f"{_p(row['high']):>10}  "
            f"{_p(row['low']):>10}  "
            f"{_p(row['close']):>10}  "
            f"{_vol(row['volume']):>10}"
        )

    season = tech_data.get("seasonality_by_month", {})
    if season:
        month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        lines.append("")
        lines.append("=== 5-YEAR AVERAGE MONTHLY SEASONALITY ===")
        row_parts = []
        for m in range(1, 13):
            val = season.get(m)
            row_parts.append(f"{month_labels[m-1]}: {val:+.1f}%" if val is not None else f"{month_labels[m-1]}: N/A")
        lines.append("  " + "  |  ".join(row_parts))

    ticker_ref = ticker or "this ticker"
    lines += [
        "",
        f"IMPORTANT: Indicator values and price levels above are authoritative — computed",
        f"from yfinance price history. Do NOT search the web for {ticker_ref}'s moving averages,",
        f"price targets, or any price-specific data not listed above.",
        "=========================================",
    ]
    return "\n".join(lines)


def fmt_volume(v) -> str:
    """Format a share-count volume without a dollar prefix."""
    if v is None:
        return "—"
    if v >= 1e9:
        return f"{v / 1e9:.2f}B"
    if v >= 1e6:
        return f"{v / 1e6:.2f}M"
    if v >= 1e3:
        return f"{v / 1e3:.0f}K"
    return f"{v:,.0f}"


def generate_chart_image(tech_data: dict | None, ticker: str = "") -> io.BytesIO | None:
    """
    Render a candlestick chart with SMA overlays and volume subplot.

    Uses mplfinance with a TradingView Light-inspired style.
    Returns a BytesIO PNG buffer on success, None on any error.
    """
    if tech_data is None:
        return None

    df = tech_data.get("ohlcv_df")
    if df is None or df.empty:
        return None

    try:
        import mplfinance as mpf
        import pandas as pd

        df = df.copy()
        for col in ("Open", "High", "Low", "Close", "Volume"):
            if col not in df.columns:
                return None

        if hasattr(df.index, "tz") and df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        try:
            warmup = yf.Ticker(ticker, session=get_yf_session()).history(period="2y") if ticker else df
            if warmup.empty or len(warmup) <= len(df):
                warmup = df
            if hasattr(warmup.index, "tz") and warmup.index.tz is not None:
                warmup.index = warmup.index.tz_localize(None)
        except Exception:
            warmup = df

        sma_addplots = []
        sma_configs = [
            (20,  "#2962FF", "SMA-20"),
            (50,  "#FF6D00", "SMA-50"),
            (200, "#6600CC", "SMA-200"),
        ]
        for period, color, label in sma_configs:
            sma_full = warmup["Close"].rolling(period).mean()
            sma_sliced = sma_full.reindex(df.index)
            if sma_sliced.notna().any():
                sma_addplots.append(
                    mpf.make_addplot(sma_sliced, color=color, width=1.2, label=label)
                )

        mc = mpf.make_marketcolors(
            up="#26A69A", down="#EF5350",
            wick={"up": "#26A69A", "down": "#EF5350"},
            volume={"up": "#26A69A", "down": "#EF5350"},
            edge="inherit",
        )
        style = mpf.make_mpf_style(
            marketcolors=mc,
            facecolor="#FFFFFF",
            gridcolor="#F0F3FA",
            gridstyle="-",
            gridaxis="both",
            edgecolor="#CCCCCC",
            figcolor="#FFFFFF",
            rc={
                "axes.spines.top":   False,
                "axes.spines.right": False,
                "xtick.labelsize":   7,
                "ytick.labelsize":   7,
                "legend.fontsize":   7,
            },
        )

        rsi_display = None
        try:
            delta = warmup["Close"].diff()
            gain  = delta.clip(lower=0).rolling(14).mean()
            loss  = (-delta.clip(upper=0)).rolling(14).mean()
            rs    = gain / loss
            rsi_full = 100 - (100 / (1 + rs))
            rsi_display = rsi_full.reindex(df.index)
        except Exception:
            rsi_display = None

        rsi_has_data = rsi_display is not None and rsi_display.notna().any()

        macd_line_series = macd_signal_series = macd_hist_series = None
        macd_has_data = False
        try:
            ema12 = warmup["Close"].ewm(span=12, adjust=False).mean()
            ema26 = warmup["Close"].ewm(span=26, adjust=False).mean()
            macd_raw     = ema12 - ema26
            signal_raw   = macd_raw.ewm(span=9, adjust=False).mean()
            macd_line_series   = macd_raw.reindex(df.index)
            macd_signal_series = signal_raw.reindex(df.index)
            macd_hist_series   = (macd_raw - signal_raw).reindex(df.index)
            macd_has_data = macd_line_series.notna().any()
        except Exception:
            pass

        additional_plots = list(sma_addplots)
        if rsi_has_data:
            additional_plots.append(mpf.make_addplot(
                rsi_display, panel=2, color='#7B1FA2', width=1.0, ylabel='RSI(14)'
            ))
            additional_plots.append(mpf.make_addplot(
                pd.Series([70] * len(df), index=df.index),
                panel=2, color='#EF5350', linestyle='--', width=0.6, secondary_y=False
            ))
            additional_plots.append(mpf.make_addplot(
                pd.Series([30] * len(df), index=df.index),
                panel=2, color='#26A69A', linestyle='--', width=0.6, secondary_y=False
            ))

        if macd_has_data:
            additional_plots.append(mpf.make_addplot(
                macd_hist_series, panel=3, type='bar',
                color=['#26A69A' if v >= 0 else '#EF5350' for v in macd_hist_series.fillna(0)],
                alpha=0.6, width=0.8, ylabel='MACD'
            ))
            additional_plots.append(mpf.make_addplot(
                macd_line_series, panel=3, color='#2962FF', width=0.9, secondary_y=False
            ))
            additional_plots.append(mpf.make_addplot(
                macd_signal_series, panel=3, color='#FF6D00', width=0.9,
                linestyle='--', secondary_y=False
            ))

        if rsi_has_data and macd_has_data:
            figsize  = (8.5, 7.0)
            p_ratios = (5, 1.5, 2, 2)
        elif rsi_has_data:
            figsize  = (8.5, 5.6)
            p_ratios = (5, 2, 2)
        else:
            figsize  = (8.5, 4.2)
            p_ratios = (0.70, 0.30)

        plot_kwargs = dict(
            type="candle",
            style=style,
            volume=True,
            figsize=figsize,
            panel_ratios=p_ratios,
            returnfig=True,
            warn_too_much_data=len(df) + 1,
            tight_layout=True,
        )
        if additional_plots:
            plot_kwargs["addplot"] = additional_plots

        fig, axes = mpf.plot(df, **plot_kwargs)

        if sma_addplots:
            axes[0].legend(loc="upper left", fontsize=7, framealpha=0.7)

        import matplotlib.pyplot as plt
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf

    except Exception as e:
        print(f"  (Warning: chart generation failed — {e})")
        return None


def generate_seasonality_chart(ticker: str, tech_data: dict | None = None) -> "io.BytesIO | None":
    """
    Render a 12-bar chart of 5-year average monthly returns for *ticker*.
    If tech_data is provided, reads pre-computed seasonality_by_month to avoid
    a redundant yfinance fetch. Returns a BytesIO PNG buffer on success, None on error.
    """
    try:
        import matplotlib.pyplot as plt

        labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        # Use pre-computed data if available, avoiding a redundant yfinance call
        season = (tech_data or {}).get("seasonality_by_month", {})
        if season:
            values = [float(season.get(m, 0.0)) for m in range(1, 13)]
        else:
            hist = yf.Ticker(ticker, session=get_yf_session()).history(period="5y")
            if hist.empty or len(hist) < 50:
                return None
            monthly = hist["Close"].resample("ME").last().pct_change().dropna()
            by_month = monthly.groupby(monthly.index.month).mean() * 100
            values = [float(by_month.get(m, 0.0)) for m in range(1, 13)]

        bar_colors = ["#26A69A" if v >= 0 else "#EF5350" for v in values]

        fig, ax = plt.subplots(figsize=(8.5, 2.8))
        ax.bar(labels, values, color=bar_colors, width=0.65, edgecolor="none")
        ax.axhline(0, color="#888888", linewidth=0.7)

        ax.set_axisbelow(True)
        ax.grid(axis="y", color="#F0F3FA", linestyle="-", linewidth=0.8)
        ax.spines["left"].set_color("#CCCCCC")
        ax.spines["bottom"].set_color("#CCCCCC")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        ax.set_ylabel("Avg Return (%)", fontsize=7)
        ax.set_title(
            f"{ticker} — 5-Year Average Monthly Returns (Jan–Dec)",
            fontsize=9, fontweight="bold", pad=6,
        )
        ax.tick_params(axis="both", labelsize=7)
        ax.set_facecolor("#FFFFFF")
        fig.patch.set_facecolor("#FFFFFF")

        for i, v in enumerate(values):
            va   = "bottom" if v >= 0 else "top"
            ypos = v + (0.05 if v >= 0 else -0.05)
            ax.text(i, ypos, f"{v:+.1f}%", ha="center", va=va,
                    fontsize=6.5, color="#444444")

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        buf.seek(0)
        return buf
    except Exception as e:
        print(f"  (Warning: seasonality chart generation failed — {e})")
        return None
