"""
====================================================================
  ENTRY POINT — CLI interface for the Investment Research System.

  Usage (PowerShell):
    $key = Get-Content key.txt
    python main.py --ticker NVDA --api-key $key

  Or set environment variable:
    $env:OPENROUTER_API_KEY = Get-Content key.txt
    python main.py --ticker NVDA

  Ticker formats accepted (all resolved automatically):
    NVDA          plain US ticker
    NVDA US       Bloomberg space notation  → NVDA
    SHEL LN       Bloomberg space notation  → SHEL.L
    7203 JP       Bloomberg space notation  → 7203.T
    0700 HK       Bloomberg space notation  → 0700.HK
    NVDA.O        Reuters notation          → NVDA
    NVDA.US       dot notation              → NVDA
====================================================================
"""

import sys
import argparse

from orchestrator import generate_report
from ticker_resolver import resolve_ticker


def _confirm_ticker(raw: str) -> str:
    """
    Normalise *raw*, look up the company name, and ask the user to confirm.
    Loops until the user accepts or enters a replacement ticker.
    Returns the confirmed yfinance-format ticker string.
    """
    current = raw
    while True:
        print(f"\n  Looking up '{current}'...", end=" ", flush=True)
        resolved, company_name = resolve_ticker(current)

        # Show the translation when the symbol changed
        if resolved != current.upper().replace(" ", ""):
            print(f"\n  Interpreted as: {resolved}")
        else:
            print()

        if company_name:
            prompt = f"  Found: {company_name} ({resolved}). Is this correct? [Y/n]: "
            answer = input(prompt).strip().lower()
            if answer in ("", "y", "yes"):
                return resolved
        else:
            print(f"  Warning: '{resolved}' was not found in market data.")
            print("  Price data may be unavailable, but the AI agents can still run.")
            prompt = f"  Proceed with '{resolved}' anyway? [Y/n]: "
            answer = input(prompt).strip().lower()
            if answer in ("", "y", "yes"):
                return resolved

        # User declined — ask for a new ticker
        current = input(
            "\n  Please enter the correct ticker "
            "(e.g. NVDA, SHEL LN, 0700 HK, 7203 JP): "
        ).strip()
        if not current:
            print("  No ticker entered. Exiting.")
            sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Multi-agent investment research report generator (OpenRouter edition)."
    )
    parser.add_argument(
        "--ticker", "-t", type=str,
        help="Stock ticker — plain (NVDA), Bloomberg (NVDA US / SHEL LN), or yfinance (SHEL.L)",
    )
    parser.add_argument("--output",  "-o", type=str, default=None, help="Output PDF filename")
    parser.add_argument("--api-key",       type=str, default=None, help="OpenRouter API key")
    args = parser.parse_args()

    raw_ticker = args.ticker
    if not raw_ticker:
        raw_ticker = input(
            "Enter stock ticker (e.g. NVDA, SHEL LN, 0700 HK, 7203 JP): "
        ).strip()
    if not raw_ticker:
        print("No ticker provided. Exiting.")
        sys.exit(1)

    confirmed_ticker = _confirm_ticker(raw_ticker)

    try:
        generate_report(ticker=confirmed_ticker, api_key=args.api_key, output_path=args.output)
    except Exception as e:
        print(f"\nERROR: Report generation failed: {e}")
        sys.exit(1)
