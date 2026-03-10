"""
====================================================================
  YF_SESSION — Provides a shared session for all yfinance calls.

  Yahoo Finance blocks requests from cloud datacenter IPs (AWS/GCP/
  Azure — including Streamlit Cloud) at multiple layers:
    1. IP range detection
    2. TLS fingerprint detection (identifies non-browser clients)
    3. User-Agent / header checks

  A plain requests.Session with browser headers fixes layer 3 but
  not layers 1-2. curl_cffi impersonates a real Chrome browser at
  the TLS level, bypassing all three checks reliably.
====================================================================
"""

_SESSION = None


def get_yf_session():
    """
    Return a module-level cached curl_cffi Session that impersonates
    Chrome, bypassing Yahoo Finance's cloud IP and TLS fingerprint
    blocking. Falls back to a plain requests.Session if curl_cffi is
    not installed.
    """
    global _SESSION
    if _SESSION is None:
        try:
            from curl_cffi import requests as curl_requests
            _SESSION = curl_requests.Session(impersonate="chrome")
        except ImportError:
            # Fallback: plain requests session with browser headers.
            # Works locally; may still be blocked on cloud servers.
            import requests
            s = requests.Session()
            s.headers.update({
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
            })
            _SESSION = s
    return _SESSION
