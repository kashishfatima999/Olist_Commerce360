"""Shared styles and helpers for the Phase 1 PDF documents (reportlab platypus)."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

import model_spec as m

import os

from reportlab import rl_config
from reportlab.lib.fonts import addMapping

rl_config.invariant = 1  # fixed creation date / document ID -> byte-identical rebuilds

# PHASE1_OUTDIR lets CI rebuild into a temporary folder and compare with the committed files.
OUTDIR = Path(os.environ.get("PHASE1_OUTDIR", Path(__file__).resolve().parents[1]))

# Calibri on Windows; Carlito (metric-compatible with Calibri, same line breaks) on Linux CI.
FONT_CANDIDATES = [
    ("Calibri", Path("C:/Windows/Fonts"), ("calibri.ttf", "calibrib.ttf", "calibrii.ttf", "calibriz.ttf")),
    ("Carlito", Path(os.environ.get("CARLITO_DIR", "/usr/share/fonts/truetype/crosextra")),
     ("Carlito-Regular.ttf", "Carlito-Bold.ttf", "Carlito-Italic.ttf", "Carlito-BoldItalic.ttf")),
]
if os.environ.get("PHASE1_FONT"):  # e.g. PHASE1_FONT=Carlito to reproduce the CI build on Windows
    FONT_CANDIDATES = [c for c in FONT_CANDIDATES if c[0] == os.environ["PHASE1_FONT"]]

FONT_FAMILY = "Helvetica"
BODY, BOLD = "Helvetica", "Helvetica-Bold"
for family, folder, files in FONT_CANDIDATES:
    if all((folder / f).exists() for f in files):
        for face, f in zip(("Body", "Body-Bold", "Body-Italic", "Body-BoldItalic"), files):
            pdfmetrics.registerFont(TTFont(face, str(folder / f)))
        addMapping("Body", 0, 0, "Body")
        addMapping("Body", 1, 0, "Body-Bold")
        addMapping("Body", 0, 1, "Body-Italic")
        addMapping("Body", 1, 1, "Body-BoldItalic")
        FONT_FAMILY, BODY, BOLD = family, "Body", "Body-Bold"
        break

NAVY = colors.HexColor("#1F3864")
LIGHT = colors.HexColor("#DDEBF7")
GRID = colors.HexColor("#A6A6A6")

_ss = getSampleStyleSheet()
S = {
    "title": ParagraphStyle("title", fontName=BOLD, fontSize=20, leading=24, alignment=TA_CENTER, textColor=NAVY, spaceAfter=6),
    "subtitle": ParagraphStyle("subtitle", fontName=BODY, fontSize=12, leading=15, alignment=TA_CENTER, spaceAfter=4),
    "doc": ParagraphStyle("doc", fontName=BOLD, fontSize=14, leading=18, alignment=TA_CENTER, spaceBefore=8, spaceAfter=10),
    "h1": ParagraphStyle("h1", fontName=BOLD, fontSize=14, leading=17, textColor=NAVY, spaceBefore=12, spaceAfter=5, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName=BOLD, fontSize=11.5, leading=14, textColor=NAVY, spaceBefore=8, spaceAfter=3, keepWithNext=1),
    "body": ParagraphStyle("body", fontName=BODY, fontSize=10, leading=13.2, spaceAfter=5),
    "bullet": ParagraphStyle("bullet", fontName=BODY, fontSize=10, leading=13, leftIndent=14, bulletIndent=4, spaceAfter=2),
    "cell": ParagraphStyle("cell", fontName=BODY, fontSize=8.5, leading=10.2),
    "cellb": ParagraphStyle("cellb", fontName=BOLD, fontSize=8.5, leading=10.2, textColor=colors.white),
    "small": ParagraphStyle("small", fontName=BODY, fontSize=8, leading=10, textColor=colors.HexColor("#555555")),
    "note": ParagraphStyle("note", fontName=BODY, fontSize=9, leading=11.5, leftIndent=8, borderPadding=4,
                           backColor=colors.HexColor("#F2F2F2"), spaceBefore=3, spaceAfter=6),
}


def P(text, style="body"):
    return Paragraph(text, S[style])


def bullets(items):
    return [Paragraph(t, S["bullet"], bulletText="•") for t in items]


def table(header, rows, widths, font_size=None, zebra=True):
    """Grid table with wrapped Paragraph cells. widths in cm."""
    cs = S["cell"] if font_size is None else ParagraphStyle("c2", parent=S["cell"], fontSize=font_size, leading=font_size * 1.2)
    hs = S["cellb"] if font_size is None else ParagraphStyle("h2c", parent=S["cellb"], fontSize=font_size, leading=font_size * 1.2)
    data = [[Paragraph(str(h), hs) for h in header]]
    for r in rows:
        data.append([Paragraph(str(v), cs) for v in r])
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]
    if zebra:
        for i in range(2, len(data), 2):
            style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F3F6FA")))
    t.setStyle(TableStyle(style))
    return t


def kv_table(rows, widths=(4.2, 12.8)):
    """Two-column key/value table."""
    data = [[Paragraph(f"<b>{k}</b>", S["cell"]), Paragraph(str(v), S["cell"])] for k, v in rows]
    t = Table(data, colWidths=[w * cm for w in widths])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("BACKGROUND", (0, 0), (0, -1), LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


# Team details as supplied by Kashish Fatima on 2026-10-24 (see decision log DEC-026).
TEAM = [  # (name, roll number)
    ("Kashish Fatima", "24L-2605"),
    ("Khadija Faiz", "24L-2554"),
    ("Aliyah Rasheed", "24L-2544"),
]
SECTION = "BDS5A"
INSTRUCTOR = "Esha Tur Razia Babar"
SUBMISSION_DATE = "25 October 2026"

TEAM_ROWS = [(f"Team member {i}", f"{name} ({roll})") for i, (name, roll) in enumerate(TEAM, 1)] + [
    ("Course / section", f"{m.COURSE} - Section {SECTION}"),
    ("Instructor", INSTRUCTOR),
    ("Submission date", SUBMISSION_DATE),
]


def cover(doc_title, doc_code, extra=None):
    out = [Spacer(1, 1.2 * cm), P(m.PROJECT, "title"), P(m.SUBTITLE, "subtitle"),
           P(f"{doc_code} - {doc_title}", "doc"), Spacer(1, 0.3 * cm), kv_table(TEAM_ROWS, (7, 10))]
    if extra:
        out += [Spacer(1, 0.3 * cm), kv_table(extra)]
    return out


def build(filename, title, story):
    path = OUTDIR / filename

    def on_page(c, d):
        c.saveState()
        c.setFont(BODY, 8)
        c.setFillColor(colors.HexColor("#666666"))
        c.drawString(2 * cm, 1.2 * cm, f"{m.PROJECT} | DL3004 Phase 1 | {title}")
        c.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {d.page}")
        c.restoreState()

    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=1.8 * cm, bottomMargin=2 * cm, title=f"{m.PROJECT} - {title}",
                            author="Olist Commerce360 team")
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return path


__all__ = ["P", "S", "bullets", "table", "kv_table", "cover", "build", "Spacer", "PageBreak", "KeepTogether",
           "Image", "cm", "m", "OUTDIR"]
