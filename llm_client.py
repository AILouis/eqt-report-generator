"""
====================================================================
  LLM CLIENT — Raw HTTP caller for the OpenRouter API.
  Knows nothing about agents, tickers, or reports.
  All retry logic lives here.
====================================================================
"""

import time

import requests

from config import (
    OPENROUTER_MODEL, OPENROUTER_ENDPOINT,
    LLM_MAX_RETRIES, LLM_TIMEOUT_S,
    LLM_RETRY_WAIT_BASE, LLM_RATE_LIMIT_WAIT_BASE,
    LLM_HTTP_REFERER, LLM_WEB_SEARCH_MAX_RESULTS,
)


# ── Custom exceptions ─────────────────────────────────────────────

class OpenRouterError(Exception):
    """Base exception for all OpenRouter API errors."""


class OpenRouterHTTPError(OpenRouterError):
    """Non-200 HTTP response from OpenRouter."""


class OpenRouterEmptyResponseError(OpenRouterError):
    """API returned an empty or malformed response."""


class OpenRouterMaxRetriesError(OpenRouterError):
    """All retry attempts exhausted."""


def call_openrouter(
    api_key: str,
    messages: list,
    temperature: float = 0.3,
    max_tokens: int = 3000,
    use_web_search: bool = False,
    model: str = OPENROUTER_MODEL,
) -> str:
    """
    POST to OpenRouter and return the assistant reply as a plain string.

    Retries up to 3 times on:
      - Rate limit (429)          — exponential back-off starting at 10 s
      - Server errors (5xx)       — exponential back-off starting at 5 s
      - Network failures          — exponential back-off starting at 5 s

    use_web_search enables the OpenRouter web-search plugin (models with
    the :online suffix support this natively).
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": LLM_HTTP_REFERER,
    }

    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if use_web_search:
        body["plugins"] = [{"id": "web", "max_results": LLM_WEB_SEARCH_MAX_RESULTS}]

    for attempt in range(LLM_MAX_RETRIES):
        try:
            response = requests.post(
                OPENROUTER_ENDPOINT, headers=headers, json=body, timeout=LLM_TIMEOUT_S
            )
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            if attempt < LLM_MAX_RETRIES - 1:
                wait = LLM_RETRY_WAIT_BASE * (2 ** attempt)
                print(f"  Network error ({exc.__class__.__name__}), retrying in {wait}s...")
                time.sleep(wait)
                continue
            raise

        if response.status_code == 429 and attempt < LLM_MAX_RETRIES - 1:
            wait = LLM_RATE_LIMIT_WAIT_BASE * (2 ** attempt)
            print(f"  Rate limited (429), retrying in {wait}s...")
            time.sleep(wait)
            continue

        if response.status_code >= 500 and attempt < LLM_MAX_RETRIES - 1:
            wait = LLM_RETRY_WAIT_BASE * (2 ** attempt)
            print(f"  Server error ({response.status_code}), retrying in {wait}s...")
            time.sleep(wait)
            continue

        if response.status_code != 200:
            raise OpenRouterHTTPError(
                f"HTTP {response.status_code}: {response.text[:500]}"
            )

        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise OpenRouterEmptyResponseError(
                f"Empty choices in API response: {str(data)[:200]}"
            )
        content = (choices[0].get("message") or {}).get("content")
        if content is None:
            raise OpenRouterEmptyResponseError(
                f"Null content in API response: {str(data)[:200]}"
            )
        if not content.strip():
            raise OpenRouterEmptyResponseError(
                "Empty LLM response (whitespace-only content)"
            )
        return content.strip()

    # Exponential back-off exhausted: 429 → 10×2^n s, 5xx → 5×2^n s
    raise OpenRouterMaxRetriesError(
        "OpenRouter call failed after maximum retries."
    )
