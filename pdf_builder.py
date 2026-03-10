"""
====================================================================
  PDF BUILDER — Assembles the final investment research PDF.
====================================================================
"""

import os
import re
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable, Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from config import OPENROUTER_MODEL, PDF_COLOR_DARK_BLUE, PDF_COLOR_ACCENT, PDF_COLOR_LIGHT_BG, AGENTS, GLOSSARY
from market_data import fmt_dollar, fmt_pct, fmt_price, fmt_volume, generate_chart_image, generate_seasonality_chart
from text_utils import extract_citations_and_clean

# Pre-compiled glossary patterns — built once at module load, not per PDF.
_GLOSSARY_PATTERNS = {
    term: re.compile(r'\b' + re.escape(term), re.IGNORECASE)
    for term in GLOSSARY
}


# ── CJK font registration ─────────────────────────────────────────
# Try to register a system font capable of rendering Chinese/Japanese/Korean.
# Used exclusively for the References section so Chinese source titles display
# correctly. Body text has CJK stripped before reaching the PDF builder.

def _try_register_cjk_font() -> str | None:
    """
    Attempt to register a CJK-capable TrueType font from the Windows font
    directory. Returns the registered font name on success, None on failure.
    The caller falls back to Helvetica (which renders CJK as squares) when
    this returns None.
    """
    candidates = [
        # Single TTF files are the most reliable with ReportLab
        ("SimHei",   r"C:\Windows\Fonts\simhei.ttf",  None),
        # TrueType Collections: specify subfontIndex=0 for the first face
        ("MSYaHei",  r"C:\Windows\Fonts\msyh.ttc",    0),
        ("SimSun",   r"C:\Windows\Fonts\simsun.ttc",   0),
    ]
    for name, path, subfont_idx in candidates:
        if not os.path.exists(path):
            continue
        try:
            if subfont_idx is not None:
                pdfmetrics.registerFont(TTFont(name, path, subfontIndex=subfont_idx))
            else:
                pdfmetrics.registerFont(TTFont(name, path))
            return name
        except Exception:
            continue
    return None


_CJK_FONT: str | None = _try_register_cjk_font()


def _try_register_body_font() -> tuple[str, str, str]:
    """
    Try to register a Unicode-capable TrueType body font.
    Returns (regular, bold, italic) font names.
    Falls back to Helvetica built-ins if no suitable font is found.
    """
    candidates = [
        {
            "regular": ("Arial",          r"C:\Windows\Fonts\arial.ttf"),
            "bold":    ("Arial-Bold",     r"C:\Windows\Fonts\arialbd.ttf"),
            "italic":  ("Arial-Italic",   r"C:\Windows\Fonts\ariali.ttf"),
        },
    ]
    # Also try DejaVu Sans from matplotlib in the local .venv
    import sys
    for sp in sys.path:
        deja_dir = os.path.join(sp, "matplotlib", "mpl-data", "fonts", "ttf")
        if os.path.isdir(deja_dir):
            candidates.append({
                "regular": ("DejaVuSans",        os.path.join(deja_dir, "DejaVuSans.ttf")),
                "bold":    ("DejaVuSans-Bold",    os.path.join(deja_dir, "DejaVuSans-Bold.ttf")),
                "italic":  ("DejaVuSans-Oblique", os.path.join(deja_dir, "DejaVuSans-Oblique.ttf")),
            })
            break

    for c in candidates:
        reg_name,  reg_path  = c["regular"]
        bold_name, bold_path = c["bold"]
        ital_name, ital_path = c["italic"]
        if not (os.path.exists(reg_path) and os.path.exists(bold_path) and os.path.exists(ital_path)):
            continue
        try:
            pdfmetrics.registerFont(TTFont(reg_name,  reg_path))
            pdfmetrics.registerFont(TTFont(bold_name, bold_path))
            pdfmetrics.registerFont(TTFont(ital_name, ital_path))
            return reg_name, bold_name, ital_name
        except Exception:
            continue
    return "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"


_BODY_FONT, _BODY_FONT_BOLD, _BODY_FONT_ITALIC = _try_register_body_font()


def _has_cjk(text: str) -> bool:
    """Return True if *text* contains any CJK / Hangul / kana codepoints."""
    return bool(re.search(
        r"[\u3000-\u9fff\uf900-\ufaff\u3040-\u30ff\uac00-\ud7af]", text
    ))


# ── Colour palette (sourced from config.py) ───────────────────────

_DARK_BLUE = colors.HexColor(PDF_COLOR_DARK_BLUE)
_ACCENT    = colors.HexColor(PDF_COLOR_ACCENT)
_LIGHT_BG  = colors.HexColor(PDF_COLOR_LIGHT_BG)

# ── Verdict colour mapping ─────────────────────────────────────────

_VERDICT_COLORS = {
    "BULLISH": {
        "banner_bg":  colors.HexColor("#1A6B3C"),
        "rationale_bg": colors.HexColor("#EAF4EE"),
    },
    "BEARISH": {
        "banner_bg":  colors.HexColor("#8B1A1A"),
        "rationale_bg": colors.HexColor("#FAE8E8"),
    },
    "NEUTRAL": {
        "banner_bg":  colors.HexColor("#4A4A6A"),
        "rationale_bg": colors.HexColor("#EEEEF5"),
    },
}


# ── Markdown / HTML helpers ───────────────────────────────────────

def _clean_markdown(text: str) -> str:
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.+?)__',     r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*',     r'<i>\1</i>', text)
    text = re.sub(r'_(.+?)_',       r'<i>\1</i>', text)
    text = re.sub(r'^#{1,6}\s*',    '',            text)
    return text.strip()


def _escape_url(url: str) -> str:
    return url.replace("&", "&amp;").replace('"', "&quot;")


def _escape_text(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ── Style factory ─────────────────────────────────────────────────

def _build_styles():
    base = getSampleStyleSheet()
    return {
        "confidential": ParagraphStyle(
            "confidential", parent=base["Normal"],
            fontSize=8, textColor=colors.HexColor("#888888"),
            alignment=TA_CENTER, spaceAfter=2,
            fontName=_BODY_FONT,
        ),
        "title": ParagraphStyle(
            "main_title", parent=base["Title"],
            fontSize=22, textColor=_DARK_BLUE,
            alignment=TA_CENTER, spaceAfter=14, leading=28,
            fontName=_BODY_FONT_BOLD,
        ),
        "section_header": ParagraphStyle(
            "section_header", parent=base["Heading1"],
            fontSize=13, textColor=colors.white, backColor=_DARK_BLUE,
            spaceBefore=14, spaceAfter=6, leftIndent=-6, rightIndent=-6,
            leading=18, borderPadding=(4, 6, 4, 6),
            fontName=_BODY_FONT_BOLD,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"],
            fontSize=9.5, leading=15, textColor=colors.HexColor("#222222"),
            spaceAfter=6, alignment=TA_LEFT,
            fontName=_BODY_FONT,
        ),
        "bullet": ParagraphStyle(
            "bullet", parent=base["Normal"],
            fontSize=9.5, leading=15, leftIndent=14,
            bulletIndent=4, spaceAfter=3, textColor=colors.HexColor("#222222"),
            fontName=_BODY_FONT,
        ),
        "label": ParagraphStyle(
            "label", parent=base["Normal"],
            fontSize=9, textColor=colors.HexColor("#666666"), spaceAfter=2,
            fontName=_BODY_FONT,
        ),
        "source": ParagraphStyle(
            "source", parent=base["Normal"],
            fontSize=9, leading=14, textColor=colors.HexColor("#222222"),
            spaceAfter=4,
            fontName=_BODY_FONT,
        ),
        # Used for reference lines whose title contains CJK characters.
        # Falls back to Helvetica when no CJK font was registered (renders as squares,
        # same as the old behaviour — graceful degradation).
        "source_cjk": ParagraphStyle(
            "source_cjk", parent=base["Normal"],
            fontSize=9, leading=14, textColor=colors.HexColor("#222222"),
            spaceAfter=4,
            fontName=_CJK_FONT or "Helvetica",
        ),
        "disclaimer": ParagraphStyle(
            "disclaimer", parent=base["Normal"],
            fontSize=8.5, textColor=colors.HexColor("#888888"), alignment=TA_CENTER,
            fontName=_BODY_FONT,
        ),
    }


# ── Text → ReportLab flowables ────────────────────────────────────

def _text_to_paragraphs(text: str, body_style, bullet_style) -> list:
    subheading_style = ParagraphStyle(
        "subheading", parent=body_style,
        fontSize=11.5, leading=17,
        textColor=_DARK_BLUE,
        spaceBefore=8, spaceAfter=4,
        fontName=_BODY_FONT_BOLD,
    )
    elements = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            elements.append(Spacer(1, 4))
            continue

        is_md_header          = bool(re.match(r'^#{1,6}\s', stripped))
        is_bullet             = stripped.startswith(("* ", "- ", "• "))
        has_letter            = bool(re.search(r'[A-Za-z]', stripped))
        is_all_caps_hdr       = (
            has_letter
            and stripped == stripped.upper()
            and len(stripped.split()) >= 3
            and len(stripped) <= 120
        )
        _num_match              = bool(re.match(r'^\d+\.\s+\S', stripped))
        is_numbered_section_hdr = _num_match and not stripped.endswith('.')
        is_numbered_list_item   = _num_match and stripped.endswith('.')

        cleaned = _clean_markdown(stripped)
        if not cleaned:
            continue

        if is_bullet or is_numbered_list_item:
            cleaned = re.sub(r'^[*\-•\s]+|\d+[.)]\s*', '', cleaned, count=1).lstrip()
            elements.append(Paragraph(f"• {cleaned}", bullet_style))
        elif is_numbered_section_hdr or is_md_header or is_all_caps_hdr:
            elements.append(Paragraph(cleaned, subheading_style))
        else:
            elements.append(Paragraph(cleaned, body_style))

    return elements


# ── Verdict extraction & rendering ───────────────────────────────

def _extract_verdict(text: str) -> tuple:
    """
    Pull the VERDICT line out of agent text.
    Returns (verdict_word, rationale, body_without_verdict).
    verdict_word is 'BULLISH', 'BEARISH', or 'NEUTRAL' (or '' if not found).
    """
    pattern = re.compile(
        r'VERDICT:\s*(BULLISH|BEARISH|NEUTRAL)\s*[—–\-]+\s*(.+?)(?:\n|$)',
        re.IGNORECASE,
    )
    m = pattern.search(text)
    if not m:
        # Fallback: bare verdict word with no dash/rationale
        m2 = re.search(r'VERDICT:\s*(BULLISH|BEARISH|NEUTRAL)\b', text, re.IGNORECASE)
        if m2:
            verdict_word = m2.group(1).upper()
            cleaned = (text[: m2.start()].rstrip() + "\n" + text[m2.end():]).strip()
            return verdict_word, "", cleaned
        return "", "", text
    verdict_word = m.group(1).upper()
    rationale    = m.group(2).strip()
    cleaned      = (text[: m.start()].rstrip() + "\n" + text[m.end():]).strip()
    return verdict_word, rationale, cleaned


def _build_verdict_box(verdict_word: str, rationale: str) -> list:
    """Return a list of flowables rendering a left-border accent verdict card.

    Layout: light tinted background + thick coloured left border.
    The verdict word is bold in the accent colour; rationale is italic below,
    separated by a thin rule. No heavy full-width banner.
    """
    vc = _VERDICT_COLORS.get(verdict_word, _VERDICT_COLORS["NEUTRAL"])

    label_style = ParagraphStyle(
        "verdict_label", fontSize=11, fontName=_BODY_FONT_BOLD,
        textColor=vc["banner_bg"], alignment=TA_LEFT,
    )
    rationale_style = ParagraphStyle(
        "verdict_rationale", fontSize=9.5, fontName=_BODY_FONT_ITALIC,
        textColor=colors.HexColor("#444444"), alignment=TA_LEFT, leading=15,
    )

    tbl = Table(
        [
            [Paragraph(f"VERDICT: {verdict_word}", label_style)],
            [Paragraph(_escape_text(rationale), rationale_style)],
        ],
        colWidths=[7.0 * inch],
    )
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), vc["rationale_bg"]),
        # Thick left accent border spanning both rows
        ("LINEBEFORE",    (0, 0), (0, -1), 4, vc["banner_bg"]),
        # Thin divider between verdict word and rationale
        ("LINEBELOW",     (0, 0), (0, 0), 0.5, colors.HexColor("#CCCCCC")),
        ("TOPPADDING",    (0, 0), (0, 0), 10),
        ("BOTTOMPADDING", (0, 0), (0, 0), 6),
        ("TOPPADDING",    (0, 1), (0, 1), 6),
        ("BOTTOMPADDING", (0, 1), (0, 1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))
    return [tbl, Spacer(1, 10)]


# ── Public entry point ────────────────────────────────────────────

def build_pdf(
    ticker: str,
    agent_reports: dict,
    cio_report: str,
    output_path: str,
    overview_data: dict | None = None,
    tech_data: dict | None = None,
    model: str = OPENROUTER_MODEL,
) -> None:
    """Assemble and write the full investment research PDF."""

    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        rightMargin=0.75 * inch, leftMargin=0.75 * inch,
        topMargin=0.75 * inch,  bottomMargin=0.75 * inch,
    )

    styles = _build_styles()

    all_sources: list[tuple[str, str]] = []
    seen_urls: set[str] = set()
    total_citations = 0
    total_chars_removed = 0

    def _process(text: str) -> str:
        nonlocal total_citations, total_chars_removed
        cleaned, citations, metrics = extract_citations_and_clean(text)
        total_citations += metrics["citations_extracted"]
        total_chars_removed += metrics["chars_removed"]
        for label, url in citations:
            if url not in seen_urls:
                seen_urls.add(url)
                all_sources.append((label, url))
        return cleaned

    story = []
    today = datetime.now().strftime("%B %d, %Y")

    story.append(Paragraph("CONFIDENTIAL", styles["confidential"]))
    story.append(HRFlowable(width="100%", thickness=2, color=_ACCENT, spaceAfter=10))
    company_label = overview_data.get("company_name") if overview_data else None
    title_line = f"{company_label} ({ticker})" if company_label else ticker
    story.append(Paragraph(
        f"{title_line} <br/>Investment Research Report",
        styles["title"],
    ))
    story.append(Spacer(1, 3))

    # Meta table
    meta_rows = [
        ["Date:", today,  "Generated by:", "Multi-Agent AI Research System"],
        ["Purpose:", "Informational", "Model:", model],
    ]
    meta_table = Table(meta_rows, colWidths=[0.9 * inch, 2.5 * inch, 1.1 * inch, 2.5 * inch])
    meta_table.setStyle(TableStyle([
        ("FONTSIZE",       (0, 0), (-1, -1), 9),
        ("TEXTCOLOR",      (0, 0), (0, -1),  colors.HexColor("#666666")),
        ("TEXTCOLOR",      (2, 0), (2, -1),  colors.HexColor("#666666")),
        ("FONTNAME",       (0, 0), (0, -1),  _BODY_FONT_BOLD),
        ("FONTNAME",       (2, 0), (2, -1),  _BODY_FONT_BOLD),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [_LIGHT_BG, colors.white]),
        ("TOPPADDING",     (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 8),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(HRFlowable(width="100%", thickness=1, color=_ACCENT, spaceBefore=10, spaceAfter=8))

    # Stock overview
    if overview_data:
        story.append(Paragraph("Stock Overview", styles["section_header"]))
        story.append(Spacer(1, 3))
        o = overview_data
        _currency = o.get("currency", "USD") or "USD"
        _GREEN = colors.HexColor("#1A7A4A")
        _RED   = colors.HexColor("#C0392B")

        def _pct_color(val):
            if val is None:
                return None
            try:
                return _GREEN if float(val) >= 0 else _RED
            except (TypeError, ValueError):
                return None

        overview_rows = [
            ["Current Price", fmt_price(o['current_price'], _currency), "1D Change",  fmt_pct(o.get("change_1d_pct"))],
            ["5D Change",     fmt_pct(o.get("change_5d_pct")),           "YTD Change", fmt_pct(o.get("change_ytd_pct"))],
            ["52W High",      fmt_price(o['high_52w'], _currency),       "52W Low",    fmt_price(o['low_52w'], _currency)],
        ]
        change_cells = [
            (0, 3, o.get("change_1d_pct")),
            (1, 1, o.get("change_5d_pct")),
            (1, 3, o.get("change_ytd_pct")),
        ]
        if o.get("market_cap") or o.get("volume"):
            overview_rows.append([
                "Market Cap", fmt_dollar(o.get("market_cap"), _currency),
                "Volume",     fmt_volume(o.get("volume")),
            ])
        ov_table = Table(overview_rows, colWidths=[1.4 * inch, 1.8 * inch, 1.4 * inch, 1.8 * inch])
        ov_style_cmds = [
            ("FONTSIZE",       (0, 0), (-1, -1), 10),
            ("TEXTCOLOR",      (0, 0), (0, -1),  colors.HexColor("#666666")),
            ("TEXTCOLOR",      (2, 0), (2, -1),  colors.HexColor("#666666")),
            ("FONTNAME",       (1, 0), (1, -1),  _BODY_FONT_BOLD),
            ("FONTNAME",       (3, 0), (3, -1),  _BODY_FONT_BOLD),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [_LIGHT_BG, colors.white]),
            ("TOPPADDING",     (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
            ("LEFTPADDING",    (0, 0), (-1, -1), 8),
        ]
        for row, col, val in change_cells:
            c = _pct_color(val)
            if c:
                ov_style_cmds.append(("TEXTCOLOR", (col, row), (col, row), c))
        ov_table.setStyle(TableStyle(ov_style_cmds))
        story.append(ov_table)
        story.append(Spacer(1, 8))

        chart_buf = generate_chart_image(tech_data, ticker)
        if chart_buf is not None:
            chart_img = Image(chart_buf, width=6.5 * inch, height=4.8 * inch)
            chart_img.hAlign = "CENTER"
            story.append(chart_img)
            story.append(Spacer(1, 6))

        # Seasonality chart
        season_buf = generate_seasonality_chart(ticker, tech_data=tech_data)
        if season_buf:
            story.append(Spacer(1, 6))
            story.append(Image(season_buf, width=6.5 * inch, height=2.2 * inch, hAlign="CENTER"))
            story.append(Spacer(1, 14))

    agent_sections = [
        ("technical",   "Technical Agent Report",   AGENTS["technical"]["description"]),
        ("macro",       "Macro Agent Report",       AGENTS["macro"]["description"]),
        ("flow",        "Flow Agent Report",        AGENTS["flow"]["description"]),
        ("narrative",   "Narrative Agent Report",   AGENTS["narrative"]["description"]),
        ("fundamental", "Fundamental Agent Report", AGENTS["fundamental"]["description"]),
    ]
    for agent_key, header_text, persona_desc in agent_sections:
        raw_text = _process(agent_reports[agent_key])
        verdict_word, rationale, body_text = _extract_verdict(raw_text)

        story.append(Paragraph(header_text, styles["section_header"]))
        story.append(Paragraph(f"<i>Persona: {persona_desc}</i>", styles["label"]))
        story.append(Spacer(1, 6))
        if verdict_word:
            story.extend(_build_verdict_box(verdict_word, rationale))
        story.extend(_text_to_paragraphs(body_text, styles["body"], styles["bullet"]))
        story.append(Spacer(1, 8))

    story.append(PageBreak())
    story.append(Paragraph("CIO Synthesis", styles["section_header"]))
    story.append(Spacer(1, 6))
    story.extend(_text_to_paragraphs(_process(cio_report), styles["body"], styles["bullet"]))

    full_text = " ".join(agent_reports.values()) + " " + cio_report
    matched_terms = sorted(
        term for term, pat in _GLOSSARY_PATTERNS.items()
        if pat.search(full_text)
    )
    if matched_terms:
        story.append(PageBreak())
        story.append(Paragraph("Glossary: Terms Explained", styles["section_header"]))
        story.append(Spacer(1, 8))
        term_label_style = ParagraphStyle(
            "gloss_term", parent=styles["body"],
            fontSize=10, fontName=_BODY_FONT_BOLD,
            textColor=_DARK_BLUE, spaceAfter=2, spaceBefore=6,
        )
        term_def_style = ParagraphStyle(
            "gloss_def", parent=styles["body"],
            fontSize=9.5, leftIndent=15, spaceAfter=4,
        )
        for term in matched_terms:
            story.append(Paragraph(_escape_text(term), term_label_style))
            story.append(Paragraph(_escape_text(GLOSSARY[term]), term_def_style))

    if all_sources:
        story.append(PageBreak())
        story.append(Paragraph("Relevant References & Sources", styles["section_header"]))
        story.append(Spacer(1, 6))
        for i, (label, url) in enumerate(all_sources, 1):
            # Use the CJK-capable style for titles that contain Chinese/Japanese/Korean.
            # This lets Chinese source names display correctly instead of as squares.
            ref_style = styles["source_cjk"] if _has_cjk(label) else styles["source"]
            link_html = f'<a href="{_escape_url(url)}" color="{PDF_COLOR_DARK_BLUE}">{_escape_text(label)}</a>'
            story.append(Paragraph(f"{i}. {link_html}", ref_style))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CCCCCC")))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "This report was generated automatically by a multi-agent AI research system via OpenRouter "
        "and reviewed by the CIO synthesis layer. "
        "It is for informational purposes only and does not constitute financial advice. "
        "Always conduct your own due diligence before making investment decisions.",
        styles["disclaimer"],
    ))

    try:
        doc.build(story)
    except Exception as e:
        raise Exception(f"ReportLab doc.build() failed for '{output_path}': {e}") from e

    print(f"\n  PDF saved to: {output_path}")
    print(f"  Citations extracted: {total_citations} | Chars cleaned: {total_chars_removed}")
