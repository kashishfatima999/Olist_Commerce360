"""Build P1_06_Star_Schema.pdf / .png and P1_06_Star_Schema.dbml from model_spec.py.

Page 1: physical star schema (all tables, columns, types, PK/FK, measures, grain, cardinality).
Page 2: conceptual model (business processes and dimensions) and bus matrix.
"""
import os
import textwrap
from pathlib import Path

import pymupdf
from reportlab.lib import colors
from reportlab.pdfgen import canvas

import model_spec as m

OUTDIR = Path(os.environ.get("PHASE1_OUTDIR", Path(__file__).resolve().parents[1]))
PDF = OUTDIR / "P1_06_Star_Schema.pdf"
PNG = OUTDIR / "P1_06_Star_Schema.png"
PNG_CONCEPT = OUTDIR / "P1_06_Conceptual_Model.png"
DBML = OUTDIR / "P1_06_Star_Schema.dbml"

W, H = 1684, 1191  # A2 landscape (points)
ROW = 10.5
FACT_HEAD = colors.HexColor("#C55A11")
DIM_HEAD = colors.HexColor("#1F3864")
FACT_BG = colors.HexColor("#FDF1E9")
DIM_BG = colors.HexColor("#EEF3FA")
TAG_COLORS = {"PK": "#B00020", "FK": "#1F5FBF", "NK": "#6A1B9A", "DD": "#555555", "M": "#2E7D32", "A": "#000000"}
DIM_LINE = {
    "dim_date": "#7030A0", "dim_customer": "#1F77B4", "dim_product": "#2CA02C",
    "dim_seller": "#D62728", "dim_order_status": "#8C564B", "dim_payment_type": "#E377C2",
}


def grain_lines(t, width):
    return textwrap.wrap("Grain: " + t["grain"], int(width / 3.3))


def box_height(t, w):
    return 30 + len(grain_lines(t, w)) * 8.5 + 4 + len(t["columns"]) * ROW + 6


def draw_box(c, t, x, top, w):
    h = box_height(t, w)
    fact = t["kind"] == "fact"
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.setFillColor(FACT_BG if fact else DIM_BG)
    c.rect(x, top - h, w, h, fill=1)
    c.setFillColor(FACT_HEAD if fact else DIM_HEAD)
    c.rect(x, top - 18, w, 18, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x + 5, top - 13, f"{m.SCHEMA}.{t['name']}")
    c.setFont("Helvetica", 7)
    c.drawRightString(x + w - 5, top - 13, t.get("est_rows", "") + " rows")
    y = top - 27
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(x + 5, y, t["type"])
    c.setFont("Helvetica-Oblique", 6.3)
    for gl in grain_lines(t, w):
        y -= 8.5
        c.drawString(x + 5, y, gl)
    y -= 4
    c.setStrokeColor(colors.HexColor("#999999"))
    c.line(x, y, x + w, y)
    for col in t["columns"]:
        name, typ, role, nullable, *_rest = col
        add = col[8]
        y -= ROW
        c.setFillColor(colors.HexColor(TAG_COLORS[role]))
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(x + 4, y + 2, role if role != "A" else "")
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold" if role in ("PK", "NK") else "Helvetica", 7.2)
        c.drawString(x + 22, y + 2, name)
        c.setFont("Helvetica", 6.5)
        c.setFillColor(colors.HexColor("#444444"))
        suffix = "" if not add else {"Additive": " (A)", "Non-additive": " (NA)", "Semi-additive": " (SA)"}[add]
        c.drawRightString(x + w - 4, y + 2, typ + ("" if nullable else " NN") + suffix)
    return h


def crow(c, x, y, direction):
    """Crow's foot (many) at fact edge y; direction +1: fact above the line, -1: fact below."""
    # toes touch the fact edge at y; apex sits 8pt away from the box (on the line side)
    apex = y - 8 * direction
    c.line(x, apex, x - 5, y)
    c.line(x, apex, x + 5, y)
    c.line(x, apex, x, y)


def one_bar(c, x, y, direction):
    d = 6 * direction
    c.line(x - 4, y + d, x + 4, y + d)


def page_physical(c):
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, H - 40, f"{m.PROJECT} - Physical Dimensional Model (Star Schema, schema '{m.SCHEMA}')")
    c.setFont("Helvetica", 9)
    c.drawString(40, H - 56, "4 fact tables share 6 conformed dimensions (fact constellation). Every relationship is "
                 "dimension (1) to fact (many); every FK is mandatory (unknown member key = -1). "
                 "dim_date is role-playing: the FK name gives the role.")

    fw, dw = 300, 285
    fx = [110, 480, 880, 1270]
    facts = ["fact_order_items", "fact_orders", "fact_payments", "fact_reviews"]
    ftop = 760
    fpos = {}
    for name, x in zip(facts, fx):
        h = draw_box(c, m.TABLE[name], x, ftop, fw)
        fpos[name] = (x, ftop, fw, h)

    dtop = H - 80
    top_dims = {"dim_product": 110, "dim_seller": 430, "dim_date": 950}
    bottom_dims = {"dim_order_status": 110, "dim_customer": 640, "dim_payment_type": 1270}
    dpos = {}
    for name, x in top_dims.items():
        h = draw_box(c, m.TABLE[name], x, dtop, dw)
        dpos[name] = (x, dtop, dw, h)
    btop = 330
    for name, x in bottom_dims.items():
        h = draw_box(c, m.TABLE[name], x, btop, dw)
        dpos[name] = (x, btop, dw, h)

    # connection plan: dim -> [(fact, attach x)], lane y
    top_lanes = {"dim_product": 838, "dim_seller": 815, "dim_date": 792}
    bot_lanes = {"dim_customer": 365, "dim_order_status": 352, "dim_payment_type": 339}
    attach_top = {
        "dim_product": {"fact_order_items": fx[0] + 70},
        "dim_seller": {"fact_order_items": fx[0] + 150},
        "dim_date": {"fact_order_items": fx[0] + 240, "fact_orders": fx[1] + 150,
                     "fact_payments": fx[2] + 150, "fact_reviews": fx[3] + 150},
    }
    attach_bot = {
        "dim_customer": {"fact_order_items": fx[0] + 200, "fact_orders": fx[1] + 120,
                         "fact_payments": fx[2] + 100, "fact_reviews": fx[3] + 120},
        "dim_order_status": {"fact_order_items": fx[0] + 100, "fact_orders": fx[1] + 200,
                             "fact_payments": fx[2] + 180},
        "dim_payment_type": {"fact_payments": fx[2] + 250},
    }
    bm = m.bus_matrix()
    c.setLineWidth(1.4)
    for dim, targets in attach_top.items():
        x, top, w, h = dpos[dim]
        sx, sy = x + w / 2, top - h
        lane = top_lanes[dim]
        col = colors.HexColor(DIM_LINE[dim])
        c.setStrokeColor(col)
        xs = list(targets.values()) + [sx]
        c.line(sx, sy, sx, lane)
        c.line(min(xs), lane, max(xs), lane)
        one_bar(c, sx, sy, -1)
        for fact, ax in targets.items():
            assert dim in bm[fact], (dim, fact)
            c.line(ax, lane, ax, ftop)
            crow(c, ax, ftop, -1)
            roles = bm[fact][dim]
            if len(roles) > 1:
                c.setFillColor(col)
                c.setFont("Helvetica", 6.5)
                c.drawString(ax + 3, lane - 9, f"{len(roles)} roles")
    for dim, targets in attach_bot.items():
        x, top, w, h = dpos[dim]
        sx, sy = x + w / 2, top
        lane = bot_lanes[dim]
        col = colors.HexColor(DIM_LINE[dim])
        c.setStrokeColor(col)
        xs = list(targets.values()) + [sx]
        c.line(sx, sy, sx, lane)
        c.line(min(xs), lane, max(xs), lane)
        one_bar(c, sx, sy, 1)
        for fact, ax in targets.items():
            assert dim in bm[fact], (dim, fact)
            fxx, ft, fwid, fh = fpos[fact]
            fb = ft - fh
            c.line(ax, lane, ax, fb)
            crow(c, ax, fb, 1)

    # completeness check: every relationship in the spec has been drawn
    drawn = {(f, d) for d, t in {**attach_top, **attach_bot}.items() for f in t}
    expected = {(f, d) for f, ds in bm.items() for d in ds}
    assert drawn == expected, expected ^ drawn

    # legend
    lx, ly = 1270, H - 80
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.8)
    c.setFillColor(colors.white)
    c.rect(lx, ly - 205, 380, 205, fill=1)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(lx + 8, ly - 14, "Legend")
    c.setFont("Helvetica", 7.5)
    items = [("PK", "Primary key"), ("NK", "Natural / business key (unique)"), ("FK", "Foreign key to a dimension"),
             ("DD", "Degenerate dimension"), ("M", "Measure")]
    yy = ly - 28
    for tag, txt in items:
        c.setFillColor(colors.HexColor(TAG_COLORS[tag]))
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(lx + 10, yy, tag)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 7.5)
        c.drawString(lx + 34, yy, txt)
        yy -= 11
    for txt in ["NN = NOT NULL;  (A) additive, (NA) non-additive measure",
                "Orange header = fact table;  blue header = dimension",
                "Line ends: bar = one (dimension), crow's foot = many (fact)",
                "Line colour identifies the dimension",
                "PK of facts = degenerate source key (composite where shown)",
                "All dimensions carry an 'Unknown' row with key -1",
                "Star schema: no dimension-to-dimension joins",
                "No fact-to-fact joins: facts are combined only through",
                "   shared dimensions or pre-aggregated order measures"]:
        c.drawString(lx + 10, yy, txt)
        yy -= 11
    c.setFont("Helvetica", 7)
    c.drawString(40, 20, "Generated from 01_Project_Documentation/phase1/build/model_spec.py - matches P1_07_Data_Dictionary.xlsx")


def page_conceptual(c):
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, H - 40, f"{m.PROJECT} - Conceptual Dimensional Model and Bus Matrix")
    c.setFont("Helvetica", 9)
    c.drawString(40, H - 56, "Business processes (facts) and the business entities (dimensions) that describe them. "
                 "No attributes or data types at this level.")
    procs = [("Sales\n(order line items)", "fact_order_items"), ("Order fulfilment\nlifecycle", "fact_orders"),
             ("Payment\ntransactions", "fact_payments"), ("Customer\nreviews", "fact_reviews")]
    dims = [("Date", "dim_date"), ("Customer", "dim_customer"), ("Product", "dim_product"),
            ("Seller", "dim_seller"), ("Order status", "dim_order_status"), ("Payment type", "dim_payment_type")]
    py = 960
    ppos = {}
    for i, (label, name) in enumerate(procs):
        x = 140 + i * 360
        c.setFillColor(FACT_BG)
        c.setStrokeColor(FACT_HEAD)
        c.setLineWidth(2)
        c.roundRect(x, py, 260, 80, 14, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 13)
        for j, ln in enumerate(label.split("\n")):
            c.drawCentredString(x + 130, py + 52 - j * 16, ln)
        c.setFont("Helvetica", 8)
        c.drawCentredString(x + 130, py + 12, name)
        ppos[name] = (x + 130, py)
    dy = 700
    dpos = {}
    for i, (label, name) in enumerate(dims):
        x = 110 + i * 250
        c.setFillColor(DIM_BG)
        c.setStrokeColor(DIM_HEAD)
        c.roundRect(x, dy, 190, 60, 10, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(x + 95, dy + 32, label)
        c.setFont("Helvetica", 8)
        c.drawCentredString(x + 95, dy + 12, name)
        dpos[name] = (x + 95, dy + 60)
    bm = m.bus_matrix()
    c.setLineWidth(1.1)
    for f, ds in bm.items():
        for d in ds:
            c.setStrokeColor(colors.HexColor(DIM_LINE[d]))
            c.line(ppos[f][0], ppos[f][1], dpos[d][0], dpos[d][1])

    # bus matrix
    cols = [d[1] for d in dims]
    x0, y0, cw0, cw = 140, 600, 230, 170
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.black)
    c.drawString(x0, y0 + 14, "Enterprise bus matrix (X = fact uses dimension; n roles = role-playing date)")
    c.setFont("Helvetica-Bold", 9)
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.6)
    rh = 24
    c.setFillColor(DIM_HEAD)
    c.rect(x0, y0 - rh, cw0 + cw * len(cols), rh, fill=1)
    c.setFillColor(colors.white)
    c.drawString(x0 + 6, y0 - 16, "Fact table (process)")
    for i, d in enumerate(cols):
        c.drawCentredString(x0 + cw0 + cw * i + cw / 2, y0 - 16, d)
    for r, (label, f) in enumerate(procs):
        y = y0 - rh * (r + 2)
        c.setFillColor(colors.white)
        c.rect(x0, y, cw0 + cw * len(cols), rh, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        c.drawString(x0 + 6, y + 8, f"{f} ({label.replace(chr(10), ' ')})")
        for i, d in enumerate(cols):
            if d in bm[f]:
                n = len(bm[f][d])
                c.drawCentredString(x0 + cw0 + cw * i + cw / 2, y + 8, "X" if n == 1 else f"X ({n} roles)")
    c.setFont("Helvetica", 9)
    notes = [
        "Fact types: fact_order_items, fact_payments and fact_reviews are transaction facts; fact_orders is an accumulating snapshot",
        "(one row per order, milestone dates filled in as the order progresses).",
        "Conformed dimensions: dim_date and dim_customer are shared by all four facts; dim_order_status by three facts.",
        "Drill-across between facts is done by aggregating each fact separately to a shared dimension level, never by joining facts row-to-row.",
    ]
    for i, n in enumerate(notes):
        c.drawString(x0, y0 - rh * 7 - i * 13, n)


def write_dbml():
    out = [f"// {m.PROJECT} - generated from model_spec.py (paste into dbdiagram.io)", ""]
    for t in m.TABLES:
        out.append(f'Table {t["name"]} [note: "{t["grain"]}"] {{')
        pks = [c[0] for c in t["columns"] if c[2] == "PK"]
        for c in t["columns"]:
            attrs = []
            if c[2] == "PK" and len(pks) == 1:
                attrs.append("pk")
            if c[2] == "NK":
                attrs.append("unique")
            if not c[3]:
                attrs.append("not null")
            attrs.append(f'note: "{c[4]}"'.replace('"', "'").replace("note: '", 'note: "').rstrip("'") + '"')
            out.append(f"  {c[0]} {c[1].replace(' ', '')} [{', '.join(attrs)}]")
        if len(pks) > 1:
            out.append("  indexes {")
            out.append(f"    ({', '.join(pks)}) [pk]")
            out.append("  }")
        out.append("}")
        out.append("")
    for f, fk, d, pk, _ in m.relationships():
        out.append(f"Ref: {f}.{fk} > {d}.{pk}")
    DBML.write_text("\n".join(out) + "\n", encoding="utf-8")


def main():
    c = canvas.Canvas(str(PDF), pagesize=(W, H), invariant=1)  # reproducible bytes
    c.setTitle(f"{m.PROJECT} - Star Schema")
    page_physical(c)
    c.showPage()
    page_conceptual(c)
    c.showPage()
    c.save()
    doc = pymupdf.open(PDF)
    doc[0].get_pixmap(dpi=150).save(PNG)
    doc[1].get_pixmap(dpi=130, clip=pymupdf.Rect(20, 20, W - 20, 830)).save(PNG_CONCEPT)  # crop to content
    write_dbml()
    print("wrote", PDF, PNG, PNG_CONCEPT, DBML)


if __name__ == "__main__":
    main()
