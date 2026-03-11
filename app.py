"""
====================================================================
  app.py — Streamlit web UI for the Equity Research Report Generator.

  Run locally:
    streamlit run app.py

  How Streamlit works:
    - This file is re-executed from top to bottom on every user action
      (button click, text input change, etc.)
    - st.session_state is a dictionary that survives between re-runs,
      so we use it to remember the resolved ticker and generated PDF.
====================================================================
"""

import io
import os
import tempfile
import contextlib

import streamlit as st
import streamlit.components.v1 as _components

from ticker_resolver import resolve_ticker
from orchestrator import generate_report
from config import AVAILABLE_MODELS
from market_data import (
    fetch_stock_overview,
    compute_technical_data,
    generate_chart_image,
    fmt_pct,
    fmt_dollar,
    fmt_price,
    fmt_volume,
)


# ── Page setup ────────────────────────────────────────────────────

st.set_page_config(
    page_title="Equity Research Generator",
    page_icon="📊",
    layout="centered",
)

st.title("Equity Research Report Generator")


# ── Sidebar: API key + model selector ────────────────────────────

with st.sidebar:
    st.header("Settings")
    api_key = st.text_input(
        "OpenRouter API Key",
        type="password",
        placeholder="sk-or-...",
        help="Get a free key at openrouter.ai/keys · Never stored, only used for this session.",
    )
    _custom_active = bool(st.session_state.get("custom_model_id", "").strip())
    selected_model = st.selectbox(
        "Model",
        options=AVAILABLE_MODELS,
        index=0,
        disabled=_custom_active,
        help="All models use OpenRouter's :online suffix for real-time web search.",
    )
    custom_model = st.text_input(
        "Custom model ID",
        key="custom_model_id",
        placeholder="e.g. mistralai/mistral-small:online",
        help="Type any OpenRouter model ID to override the dropdown above.",
    )
    if custom_model.strip():
        selected_model = custom_model.strip()
    st.divider()
    st.markdown(
        "**About**\n\n"
        "Generates a multi-section PDF with macro, flow, technical, "
        "narrative, and fundamental analysis, plus a CIO synthesis.\n\n"
        "Each report takes ~2-3 minutes.\n\n"
        "Reach out to imlouislai@gmail.com for feedback."
    )


st.caption(f"Multi-agent AI research powered by OpenRouter · {selected_model}")

# ── Phase 1: Ticker input + lookup ───────────────────────────────

st.subheader("Step 1 — Enter a ticker")

with st.form("ticker_form", clear_on_submit=False):
    col1, col2 = st.columns([3, 1])
    with col1:
        raw_ticker = st.text_input(
            "Ticker",
            placeholder="e.g. NVDA, SHEL LN, 0700 HK, 7203 JP",
            label_visibility="collapsed",
        )
    with col2:
        lookup_clicked = st.form_submit_button("Look Up", width='stretch')

if lookup_clicked:
    if not raw_ticker.strip():
        st.error("Please enter a ticker first.")
    else:
        try:
            with st.spinner("Resolving ticker..."):
                resolved, company_name = resolve_ticker(raw_ticker.strip())
        except Exception as e:
            st.error(f"Failed to resolve ticker: {e}")
            resolved, company_name = None, None
        if resolved:
            raw_upper = raw_ticker.strip().upper()
            st.session_state["ticker_translation"] = (
                f"Interpreted '{raw_ticker.strip()}' as '{resolved}'" if resolved != raw_upper else None
            )
            st.session_state["resolved"] = resolved
            st.session_state["company_name"] = company_name
            for key in ("pdf_bytes", "pdf_filename", "generation_log",
                        "overview_data", "tech_data", "dashboard_chart_bytes"):
                st.session_state.pop(key, None)


# ── Phase 2: Confirm + Generate ───────────────────────────────────
# This block only runs if we have a resolved ticker in session state.

if "resolved" in st.session_state:
    resolved = st.session_state["resolved"]
    company_name = st.session_state["company_name"]

    _translation_msg = st.session_state.get("ticker_translation")
    if _translation_msg:
        st.info(_translation_msg)

    st.subheader("Step 2 — Confirm and generate")

    if company_name:
        st.success(f"Found: **{company_name}** ({resolved})")
    else:
        st.warning(
            f"Ticker **{resolved}** was not found in market data. "
            "Price data may be missing, but the AI agents can still run."
        )

    if "overview_data" not in st.session_state:
        try:
            with st.spinner("Loading market data..."):
                overview_data = fetch_stock_overview(resolved)
                _td = compute_technical_data(resolved)
                st.session_state["overview_data"] = overview_data
                st.session_state["tech_data"] = _td
                if _td:
                    _chart = generate_chart_image(_td, resolved)
                    st.session_state["dashboard_chart_bytes"] = _chart.getvalue() if _chart else None
                else:
                    st.session_state["dashboard_chart_bytes"] = None
        except Exception as e:
            st.warning(f"Could not load market data: {e}")
            st.session_state["overview_data"] = None
            st.session_state["tech_data"] = None
            st.session_state["dashboard_chart_bytes"] = None

    overview_data = st.session_state.get("overview_data")
    chart_bytes   = st.session_state.get("dashboard_chart_bytes")

    if overview_data:
        st.markdown("---")
        price     = overview_data.get("current_price", 0)
        d1        = overview_data.get("change_1d_pct")
        _currency = overview_data.get("currency", "USD") or "USD"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Price",      fmt_price(price, _currency),
                  delta=f"{d1:+.2f}%" if d1 is not None else None)
        c2.metric("5D Change",  fmt_pct(overview_data.get("change_5d_pct")))
        c3.metric("YTD Change", fmt_pct(overview_data.get("change_ytd_pct")))
        c4.metric("Market Cap", fmt_dollar(overview_data.get("market_cap"), _currency))

        c5, c6, c7, _ = st.columns(4)
        c5.metric("52W High", fmt_price(overview_data.get("high_52w"), _currency))
        c6.metric("52W Low",  fmt_price(overview_data.get("low_52w"), _currency))
        c7.metric("Volume",   fmt_volume(overview_data.get("volume")))

    if chart_bytes:
        st.image(chart_bytes, width='stretch',
                 caption=f"{resolved} — 1 Year Price, Volume & RSI(14)")

    st.markdown("---")

    generate_clicked = st.button("Generate Report", type="primary", width='stretch')

    if generate_clicked:
        api_key = api_key.strip()
        if not api_key:
            st.error("Please enter your OpenRouter API key in the sidebar first.")
        elif not api_key.startswith("sk-or-"):
            st.warning("API key doesn't look like an OpenRouter key (expected prefix: sk-or-). Double-check it before proceeding.")
        else:
            progress_bar = st.progress(0, text="Starting...")
            status_text = st.empty()
            log_buffer = io.StringIO()

            STEPS = [
                ("", ""),                         # 0 — unused (0% is "Starting")
                ("Fetching market data",    "Grabbing the freshest prices off the exchange floor..."),
                ("Technical analyst",       "Squinting at candlesticks and muttering about support levels..."),
                ("Macro strategist",        "Consulting the global macro crystal ball (it's cloudy, as always)..."),
                ("Flow & positioning",      "Tracking where the smart money is hiding..."),
                ("Narrative analyst",       "Reading every headline so you don't have to..."),
                ("Fundamental analyst",     "Crunching earnings, margins, and that one footnote nobody reads..."),
                ("CIO synthesis",           "The CIO is brewing coffee and synthesising all of the above..."),
                ("Building PDF",            "Typesetting your report — almost there, promise!"),
            ]

            def on_progress(step: int, total: int, label: str) -> None:
                fraction = step / total
                pct = int(fraction * 100)
                step_label, quip = STEPS[step] if step < len(STEPS) else ("", "")
                progress_bar.progress(
                    fraction,
                    text=f"{pct}% — {step_label} ({step}/{total})",
                )
                if quip:
                    status_text.caption(quip)
                else:
                    status_text.empty()

            try:
                with tempfile.TemporaryDirectory() as tmp_dir:
                    pdf_path = os.path.join(tmp_dir, f"{resolved}_report.pdf")

                    with contextlib.redirect_stdout(log_buffer):
                        generate_report(
                            ticker=resolved,
                            api_key=api_key,
                            output_path=pdf_path,
                            progress_callback=on_progress,
                            model=selected_model,
                        )

                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()

                st.session_state["pdf_bytes"] = pdf_bytes
                st.session_state["pdf_filename"] = f"{resolved}_Report.pdf"

                progress_bar.progress(1.0, text="100% — Done!")
                status_text.empty()

            except Exception as e:
                progress_bar.empty()
                status_text.error(f"Report generation failed: {e}")

            log_text = log_buffer.getvalue()
            if log_text.strip():
                st.session_state["generation_log"] = log_text


# ── Phase 3: Download button + persistent log ─────────────────────

if "pdf_bytes" in st.session_state:
    st.divider()
    st.download_button(
        label="⬇ Download PDF Report",
        data=st.session_state["pdf_bytes"],
        file_name=st.session_state["pdf_filename"],
        mime="application/pdf",
        width='stretch',
    )

if "generation_log" in st.session_state:
    with st.expander("View generation log", expanded=True):
        st.text(st.session_state["generation_log"])

# ── Scroll preservation ───────────────────────────────────────────
_components.html("""
<script>
(function () {
    const KEY = "eqt_scroll";
    const main = window.parent.document.querySelector("section.main");
    if (!main) return;

    // Restore saved position on every re-render
    const saved = sessionStorage.getItem(KEY);
    if (saved) main.scrollTop = parseInt(saved, 10);

    // Save position continuously while the user scrolls
    main.addEventListener("scroll", function () {
        sessionStorage.setItem(KEY, main.scrollTop);
    });
})();
</script>
""", height=0)
