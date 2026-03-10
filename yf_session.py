"""
====================================================================
  YF_SESSION — Provides a shared requests.Session with browser-like
  headers for all yfinance calls.

  Yahoo Finance aggressively rate-limits/blocks requests coming from
  cloud datacenter IPs (AWS, GCP, Azure — including Streamlit Cloud).
  Attaching a session with realistic browser headers bypasses this.
====================================================================
"""

import requests

_SESSION: requests.Session | None = None


def get_yf_session() -> requests.Session:
    """
    Return a module-level cached requests.Session configured with
    browser-like headers so Yahoo Finance does not block cloud IPs.
    """
    global _SESSION
    if _SESSION is None:
        s = requests.Session()
        s.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;"
                    "q=0.9,image/avif,image/webp,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0",
            }
        )
        _SESSION = s
    return _SESSION
