"""
====================================================================
  ORCHESTRATOR — Runs the full pipeline end-to-end.
  This is the only file that knows the order of operations.
====================================================================
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from config import AGENTS, OPENROUTER_MODEL
from agents import run_agent, run_cio
from market_data import fetch_stock_overview, compute_technical_data, format_snapshot_for_prompt, fmt_price
from text_utils import strip_redundant_content
from pdf_builder import build_pdf


def _report_progress(callback, step: int, total: int, label: str) -> None:
    """Call progress_callback safely; silently skip if None."""
    if callback is not None:
        try:
            callback(step, total, label)
        except Exception:
            pass  # never let a UI glitch abort the pipeline


def generate_report(
    ticker: str,
    api_key: str = None,
    output_path: str = None,
    progress_callback=None,
    model: str = OPENROUTER_MODEL,
) -> str:
    """
    Run all five research agents, the CIO synthesis, and build the PDF.
    Returns the path to the saved PDF.

    progress_callback, if provided, is called as:
        callback(step: int, total: int, label: str)
    where step goes from 1 to total (8) at each checkpoint.
    """
    ticker = ticker.upper().strip()
    now = datetime.now()
    if output_path is None:
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M")
        report_dir = os.path.join("Reports", date_str, ticker)
        os.makedirs(report_dir, exist_ok=True)
        output_path = os.path.join(report_dir, f"{ticker}_Report_{date_str}_{time_str}.pdf")

    print(f"\n{'='*60}")
    print(f"  INVESTMENT RESEARCH SYSTEM  —  {ticker}")
    print(f"{'='*60}")
    print(f"  Date    : {now.strftime('%B %d, %Y %H:%M')}")
    print(f"  Model   : {model}")
    print(f"  Via     : OpenRouter")
    print(f"  Output  : {output_path}")
    print(f"{'='*60}\n")

    resolved_key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not resolved_key:
        try:
            key_path = os.path.join(os.path.dirname(__file__), "key.txt")
            with open(key_path, "r") as f:
                resolved_key = f.read().strip()
        except FileNotFoundError:
            pass
    if not resolved_key:
        raise ValueError(
            "No OpenRouter API key found. "
            "Put your key in key.txt, set $env:OPENROUTER_API_KEY, "
            "or pass --api-key YOUR_KEY. "
            "Get a free key at: https://openrouter.ai/keys"
        )

    start_time = time.time()
    step_times: dict[str, float] = {}

    # Step 0: Live stock data
    print("STEP 0: Fetching stock overview data...\n")
    t0 = time.time()
    overview_data = fetch_stock_overview(ticker)
    if overview_data is not None:
        overview_data["ticker"] = ticker
    step_times["Step 0 (market data)"] = time.time() - t0
    if overview_data is not None:
        current_price = overview_data.get('current_price')
        low_52w = overview_data.get('low_52w')
        high_52w = overview_data.get('high_52w')
        currency = overview_data.get('currency', 'USD')
        if current_price is not None and low_52w is not None and high_52w is not None:
            print(
                f"  Current: {fmt_price(current_price, currency)} | "
                f"52W: {fmt_price(low_52w, currency)}–{fmt_price(high_52w, currency)}\n"
            )
    else:
        print("  (Overview data unavailable; section will be omitted.)\n")

    technical_data = compute_technical_data(ticker)
    if technical_data:
        print("  Technical indicators computed.\n")
    else:
        print("  (Technical data unavailable.)\n")

    # Reconcile current_price: use overview's canonical price in the technical block
    if overview_data and technical_data and overview_data.get("current_price"):
        cp = overview_data["current_price"]
        technical_data["current_price"] = cp
        for sma_key, dist_key in [
            ("sma20", "dist20"), ("sma50", "dist50"),
            ("sma100", "dist100"), ("sma200", "dist200"),
        ]:
            sma = technical_data.get(sma_key)
            if sma:
                technical_data[dist_key] = (cp - sma) / sma * 100

    # Pre-compute snapshot block once so all agents share the same timestamp (H-8)
    snapshot_block = format_snapshot_for_prompt(overview_data) if overview_data else ""

    _report_progress(progress_callback, 1, 8, "Market data fetched")

    # Step 1: Five specialized research agents (run concurrently — H-2)
    print("STEP 1: Running specialized research agents (parallel)...\n")
    agent_reports = {}
    t1 = time.time()
    agent_keys = ["technical", "macro", "flow", "narrative", "fundamental"]

    futures: dict = {}
    completed_count = 0
    with ThreadPoolExecutor(max_workers=5) as executor:
        for agent_key in agent_keys:
            agent_name = AGENTS[agent_key]["name"]
            print(f"  [{agent_key.upper()}] {agent_name} — submitting...")
            future = executor.submit(
                run_agent, resolved_key, agent_key, ticker,
                technical_data=technical_data,
                model=model,
                snapshot_block=snapshot_block,
            )
            futures[future] = agent_key

        for future in as_completed(futures):
            agent_key = futures[future]
            agent_name = AGENTS[agent_key]["name"]
            completed_count += 1
            try:
                report = future.result()
                agent_reports[agent_key] = strip_redundant_content(report)
                print(f"  [{agent_key.upper()}] done. ({len(report.split())} words)")
            except Exception as e:
                print(f"  WARNING: {agent_name} failed: {e}")
                agent_reports[agent_key] = f"[Agent failed: {e}]"
            _report_progress(progress_callback, 1 + completed_count, 8, f"{agent_name} done")

    step_times["Step 1 (5 agents)"] = time.time() - t1

    # Step 2: CIO synthesis
    print("\nSTEP 2: CIO synthesis...\n")
    t2 = time.time()
    try:
        cio_report = run_cio(
            resolved_key, ticker, agent_reports,
            model=model, snapshot_block=snapshot_block,
        )
        cio_report = strip_redundant_content(cio_report)
        print(f"  Done. ({len(cio_report.split())} words)\n")
    except Exception as e:
        print(f"  WARNING: CIO synthesis failed: {e}")
        cio_report = f"[CIO synthesis failed: {e}]"
    step_times["Step 2 (CIO synthesis)"] = time.time() - t2
    _report_progress(progress_callback, 7, 8, "CIO synthesis done")

    # Step 3: Build PDF
    print("\nSTEP 3: Building PDF...\n")
    t3 = time.time()
    try:
        build_pdf(
            ticker, agent_reports, cio_report, output_path,
            overview_data=overview_data, tech_data=technical_data, model=model,
        )
    except Exception as e:
        raise Exception(f"PDF build failed for '{output_path}': {e}") from e
    step_times["Step 3 (PDF build)"] = time.time() - t3
    _report_progress(progress_callback, 8, 8, "PDF built")

    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"  DONE!  Open your report: {output_path}")
    print(f"  Total time: {elapsed / 60:.1f} min ({elapsed:.0f}s)")
    print(f"  Per-step breakdown:")
    for step, secs in step_times.items():
        print(f"    {step}: {secs:.1f}s")
    print(f"{'='*60}\n")

    return output_path
