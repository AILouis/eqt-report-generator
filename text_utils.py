"""
====================================================================
  TEXT UTILS — Citation extraction and text cleaning utilities.
  Pure string-in / string-out functions. No I/O, no LLM calls,
  no third-party dependencies.
====================================================================
"""

import re
from urllib.parse import urlparse


def _domain_from_url(url: str) -> str:
    """Extract a short display label from a URL (e.g. 'reuters.com')."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split("/")[0]
        if domain.startswith("www."):
            domain = domain[4:]
        return domain or url[:50]
    except Exception:
        return url[:50]


def extract_citations_and_clean(
    text: str,
) -> tuple[str, list[tuple[str, str]], dict]:
    """
    Strip all URLs, markdown links, and bracketed citation artifacts from *text*.

    Handles all known patterns the model may produce:
      • Well-formed markdown links: [text](url)
      • Split-line links: [Title]\\n(https://url)
      • Bare URLs in parentheses: (https://...)  — including truncated ones
      • Truncated protocol-only fragments: (https or (http without ://
      • Bare URLs inline: https://...
      • Unclosed brackets: [Title not closed at token limit
      • Bracketed citations without URL: [Title - domain.com]
      • Entire SOURCES / REFERENCES block appended at the end

    Returns:
        cleaned   — body text with zero URL/citation content
        citations — ordered list of (display_label, url), unique by url
        metrics   — dict with keys: citations_extracted, chars_removed
    """
    citations: list[tuple[str, str]] = []
    seen_urls: set[str] = set()
    original_len = len(text)

    def _collect(match):
        display, url = match.group(1).strip(), match.group(2).strip()
        if url and url not in seen_urls:
            seen_urls.add(url)
            label = display if display else _domain_from_url(url)
            citations.append((label, url))
        return ""

    # 1. Well-formed markdown links [text](url) on the same line — collect and remove.
    cleaned = re.sub(r"\[([^\]]*)\]\(\s*([^)]+)\s*\)", _collect, text, flags=re.DOTALL)

    # 1b. Split-line variant: [Title] on one line, (https://url) on the very next line.
    #     Only matches when the parenthesised content starts with http — avoids accidentally
    #     consuming parenthetical prose like "(confirmed by analysts)".
    cleaned = re.sub(
        r"\[([^\]\n]+)\][ \t]*\n[ \t]*\(\s*(https?://[^\s)]+)\s*\)",
        _collect,
        cleaned,
    )

    # 2. Safety-net: strip the entire SOURCES / REFERENCES block if present.
    #    The heading must occupy its own line (only decoration chars after the keyword)
    #    so normal sentences like "Sources of revenue…" are NOT affected.
    cleaned = re.sub(
        r"\n[^\S\n]*(?:[#*\-]{0,3}\s*)?"
        r"(SOURCES?|REFERENCES?|CITATIONS?|BIBLIOGRAPHY)"
        r"[:\-*#\s]*\n.*",
        "",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # 3. Bracketed citations without a URL: [Title - domain.com]
    cleaned = re.sub(
        r"\[\s*[^\]]+?\s*-\s*[a-zA-Z0-9][a-zA-Z0-9.-]*\.(com|org|net|io|co|fyi|info)\s*\]",
        "",
        cleaned,
    )

    # 4. Remove ALL remaining [text] brackets unconditionally.
    #    Steps 1/1b already collected every legitimate [text](url) pair, so anything
    #    still enclosed in brackets at this point is an unwanted artifact — a bare
    #    citation title, an inline reference marker, etc.  No lookahead is needed.
    cleaned = re.sub(r"\[[^\]\n]{0,300}\]", "", cleaned)

    # 5. Unclosed brackets: text cut off at token limit, e.g. "[Title that never closed
    cleaned = re.sub(r"\[[^\]\n]{0,300}$", "", cleaned, flags=re.MULTILINE)

    # 6. Bare URLs in parentheses — handles all forms:
    #    • (https://url)       — fully-formed
    #    • (https://url        — missing closing paren (token-limit truncation)
    #    • (https              — truncated before :// (no protocol separator present)
    #    Note: removing the requirement for :// prevents (https stubs from leaking through.
    cleaned = re.sub(r"\(\s*https?[^\s)]*\)?", "", cleaned)

    # 6b. Remove leftover (, YYYY-MM-DD) shells — remnants of ([Link](url), Date) inline citations
    #     after the markdown link portion was stripped in step 1.
    cleaned = re.sub(r"\(\s*,\s*\d{4}-\d{2}-\d{2}\s*\)", "", cleaned)

    # 6c. Remove inline author-date citations: (Source Name, YYYY-MM-DD)
    #     e.g. (MarketMinute, 2026-03-03), (IFM Investors, 2026-03-05),
    #     (Silicon Valley Capital Partners, 2026-02-28).
    #     The YYYY-MM-DD date format is specific enough to avoid false positives
    #     on normal parenthetical prose.
    cleaned = re.sub(r"\([^()]{2,80},\s*\d{4}-\d{2}-\d{2}\s*\)", "", cleaned)

    # 7. Any remaining bare https:// or http:// URLs
    cleaned = re.sub(r"https?://\S*", "", cleaned)

    # 8. Clean up whitespace artifacts left after removals
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r" \.", ".", cleaned)
    cleaned = re.sub(r",\s*,", ",", cleaned)
    cleaned = re.sub(r"\(\s*\)", "", cleaned)   # empty () left behind
    cleaned = re.sub(r"\s+\.\s*", ". ", cleaned)

    # 8b. Remove lines that now consist entirely of stray punctuation / parentheses.
    #     These are artifacts left when a truncated or split-line URL reference was
    #     only partially stripped (e.g. a lone "(" or ")" remaining on its own line).
    cleaned = re.sub(r"^\s*[\(\)\[\].,;:]+\s*$", "", cleaned, flags=re.MULTILINE)

    # 9. Drop lines that are now empty or only contain bare bullet markers
    lines_out = []
    for ln in cleaned.split("\n"):
        if re.match(r"^\s*[*•\-]+\s*$", ln):
            continue
        lines_out.append(ln)

    # 10. Collapse 3+ consecutive blank lines into a single blank line
    out = "\n".join(lines_out).strip()
    out = re.sub(r"\n{3,}", "\n\n", out)

    # 11. Strip CJK characters from body text — report content must be English-only.
    #     Citation labels are returned separately and will be rendered in the
    #     References section using a CJK-capable font, so they are NOT touched here.
    #     Ranges covered: CJK symbols/ideographs (Chinese), Hiragana/Katakana (Japanese),
    #     Korean Hangul, and CJK compatibility/extension blocks.
    out = re.sub(
        r"[\u3000-\u9fff\uf900-\ufaff\u3040-\u30ff\uac00-\ud7af]+",
        "",
        out,
    )
    # Re-clean artifacts left by CJK removal (empty quotes, empty parens, extra spaces)
    out = re.sub(r'["\u201c]\s*["\u201d]', "", out)  # empty straight or curly quotes
    out = re.sub(r"\(\s*\)", "", out)                 # () → remove
    out = re.sub(r"[ \t]{2,}", " ", out)  # collapse spaces
    out = re.sub(r"\n{3,}", "\n\n", out)
    final = out.strip()
    metrics = {
        "citations_extracted": len(citations),
        "chars_removed": original_len - len(final),
    }
    return final, citations, metrics


def strip_redundant_content(text: str) -> str:
    """
    Remove memo headers, repeated date lines, and boilerplate that
    agents sometimes prepend even when instructed not to.
    """
    lines = text.split("\n")
    result = []
    skip_next_if_empty = False

    for line in lines:
        stripped = line.strip()

        # Drop memo-style headers (To:, From:, Date:, Subject:)
        if re.match(r"^(To|From|Date|Subject):\s*.+$", stripped, re.IGNORECASE):
            continue
        # Drop standalone memo titles
        if re.match(r"^(Macro\s+)?Memorandum\s*$", stripped, re.IGNORECASE):
            continue
        # Drop redundant CIO/committee headers the model might still emit
        if re.match(r"^(INVESTMENT\s+COMMITTEE\s+SYNTHESIS|CIO\s+SYNTHESIS):?\s*.*$", stripped):
            continue
        if re.match(r"^DATE:\s*.+$", stripped, re.IGNORECASE):
            continue
        # Drop inline References/Sources headings (citations go in the PDF section)
        bare = re.sub(r"[*_#>\s]", "", stripped)
        if re.match(r"^(References?|Sources?|Citations?|Bibliography):?$", bare, re.IGNORECASE):
            continue

        # Strip "As of [date]," from paragraph openings
        cleaned_line = re.sub(r"^As of [^.]{5,60},?\s*", "", stripped, flags=re.IGNORECASE)
        cleaned_line = re.sub(r"^As of [A-Za-z]+\s+\d{1,2},?\s+\d{4}\s+", "", cleaned_line)
        cleaned_line = re.sub(
            r"^As of (late |early )?[A-Za-z]+\s+\d{4},?\s*", "", cleaned_line, flags=re.IGNORECASE
        )

        if not cleaned_line:
            if not skip_next_if_empty:
                result.append("")
                skip_next_if_empty = True
            continue
        skip_next_if_empty = False
        result.append(cleaned_line)

    out = "\n".join(result)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()
