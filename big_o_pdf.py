"""
Big O — зөн совин: хичээлийн PDF үүсгэгч.

Ажиллуулах:  python big_o_pdf.py
Шаардлага:   pip install reportlab matplotlib numpy
Гаралт:      BigO_zon_sovin.pdf (энэ файлтай нэг хавтсанд)
"""

import io
import keyword
import os
import re
import textwrap
import time
import timeit
from functools import lru_cache

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    CondPageBreak,
    Frame,
    Image,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    XPreformatted,
)
from reportlab.lib.fonts import addMapping

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "BigO_zon_sovin.pdf")

# ----------------------------------------------------------------------------
# Фонт (кирилл + Ө, Ү үсэгтэй)
# ----------------------------------------------------------------------------
FONT_DIR = r"C:\Windows\Fonts"
for name, file in [
    ("Arial", "arial.ttf"),
    ("Arial-Bold", "arialbd.ttf"),
    ("Arial-Italic", "ariali.ttf"),
    ("Arial-BoldItalic", "arialbi.ttf"),
    ("Consolas", "consola.ttf"),
    ("Consolas-Bold", "consolab.ttf"),
    ("Consolas-Italic", "consolai.ttf"),
    ("Consolas-BoldItalic", "consolaz.ttf"),
]:
    pdfmetrics.registerFont(TTFont(name, os.path.join(FONT_DIR, file)))
for fam in ("Arial", "Consolas"):
    addMapping(fam, 0, 0, fam)
    addMapping(fam, 1, 0, fam + "-Bold")
    addMapping(fam, 0, 1, fam + "-Italic")
    addMapping(fam, 1, 1, fam + "-BoldItalic")

# ----------------------------------------------------------------------------
# Өнгө (dataviz лавлах палитр, гэрэл горим)
# ----------------------------------------------------------------------------
SURFACE = "#fcfcfb"
INK = "#1b1b19"
TEXT2 = "#52514e"
MUTED = "#8a8984"
RULE = "#e2e1dc"
GRID = "#ecebe7"
CODE_BG = "#f5f4f0"
CARD_BG = "#fafaf8"
CALLOUT_BG = "#eef4fc"
WARN_BG = "#fdf3e7"
ACCENT = "#2a78d6"
ACCENT_DARK = "#1c5cab"

# 6 ангиллын өнгө: категорийн дараалал 1→6, баримт бичиг даяар ижил
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
CLASSES = ["O(1)", "O(log n)", "O(n)", "O(n log n)", "O(n²)", "O(2ⁿ)"]

# Кодын тодруулга
C_KW = "#7a3eb0"
C_BUILTIN = "#1c5cab"
C_STR = "#0f7a52"
C_NUM = "#b4441a"
C_COM = "#7d7c76"

PAGE_W, PAGE_H = A4
MARGIN_X = 20 * mm
CW = PAGE_W - 2 * MARGIN_X  # агуулгын өргөн

# ----------------------------------------------------------------------------
# Загварууд
# ----------------------------------------------------------------------------
st_body = ParagraphStyle("body", fontName="Arial", fontSize=10.5, leading=15.5,
                         textColor=HexColor(INK), spaceAfter=6)
st_lead = ParagraphStyle("lead", parent=st_body, fontSize=12, leading=18,
                         textColor=HexColor(TEXT2), spaceAfter=10)
st_h1 = ParagraphStyle("H1", fontName="Arial-Bold", fontSize=20, leading=25,
                       textColor=HexColor(INK), spaceBefore=4, spaceAfter=10,
                       keepWithNext=1)
st_h2 = ParagraphStyle("H2", fontName="Arial-Bold", fontSize=13, leading=17,
                       textColor=HexColor(INK), spaceBefore=12, spaceAfter=5,
                       keepWithNext=1)
st_bullet = ParagraphStyle("bullet", parent=st_body, leftIndent=16,
                           bulletIndent=4, spaceAfter=3)
st_caption = ParagraphStyle("caption", fontName="Arial", fontSize=8.5,
                            leading=12, textColor=HexColor(TEXT2),
                            spaceBefore=3, spaceAfter=12)
st_small = ParagraphStyle("small", fontName="Arial", fontSize=8.5, leading=12,
                          textColor=HexColor(TEXT2))
st_cell = ParagraphStyle("cell", fontName="Arial", fontSize=9.3, leading=12.5,
                         textColor=HexColor(INK))
st_cell_b = ParagraphStyle("cellb", parent=st_cell, fontName="Arial-Bold")
st_cell_h = ParagraphStyle("cellh", parent=st_cell, fontName="Arial-Bold",
                           textColor=HexColor(TEXT2), fontSize=8.8)
st_cell_c = ParagraphStyle("cellc", parent=st_cell, alignment=TA_CENTER)
st_code = ParagraphStyle("code", fontName="Consolas", fontSize=8.8, leading=12.2,
                         textColor=HexColor(INK))
st_callout_t = ParagraphStyle("calloutT", fontName="Arial-Bold", fontSize=10,
                              leading=14, textColor=HexColor(ACCENT_DARK),
                              spaceAfter=2)
st_callout = ParagraphStyle("callout", parent=st_body, spaceAfter=0)
st_card_head = ParagraphStyle("cardHead", fontName="Arial-Bold", fontSize=15,
                              leading=19, textColor=HexColor(INK), spaceAfter=2)


def P(text, style=st_body):
    return Paragraph(text, style)


def c(code):
    """Мөр доторх код."""
    code = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<font face="Consolas" color="{ACCENT_DARK}">{code}</font>'


def bullets(items, style=st_bullet):
    return [Paragraph(t, style, bulletText="•") for t in items]


def numbered(items):
    return [Paragraph(t, st_bullet, bulletText=f"{i}.") for i, t in enumerate(items, 1)]


# ----------------------------------------------------------------------------
# Python кодын тодруулга
# ----------------------------------------------------------------------------
BUILTINS = {"print", "len", "range", "set", "list", "dict", "sorted", "sum",
            "min", "max", "enumerate", "lru_cache"}
TOKEN = re.compile(
    r"(?P<com>#.*)"
    r"|(?P<str>f?\"[^\"\n]*\"|f?'[^'\n]*')"
    r"|(?P<dec>@\w+)"
    r"|(?P<num>\b\d[\d_]*(?:\.\d+)?\b)"
    r"|(?P<word>\b[A-Za-z_]\w*\b)"
)


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def highlight(src):
    out, pos = [], 0
    for m in TOKEN.finditer(src):
        out.append(_esc(src[pos:m.start()]))
        pos = m.end()
        kind, text = m.lastgroup, _esc(m.group())
        if kind == "com":
            out.append(f'<font color="{C_COM}"><i>{text}</i></font>')
        elif kind == "str":
            out.append(f'<font color="{C_STR}">{text}</font>')
        elif kind == "num":
            out.append(f'<font color="{C_NUM}">{text}</font>')
        elif kind == "dec":
            out.append(f'<font color="{C_KW}">{text}</font>')
        elif kind == "word" and m.group() in keyword.kwlist:
            out.append(f'<font color="{C_KW}"><b>{text}</b></font>')
        elif kind == "word" and m.group() in BUILTINS:
            out.append(f'<font color="{C_BUILTIN}">{text}</font>')
        else:
            out.append(text)
    out.append(_esc(src[pos:]))
    return "".join(out)


def code_block(src, width=CW):
    src = textwrap.dedent(src).strip("\n")
    t = Table([[XPreformatted(highlight(src), st_code)]], colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(CODE_BG)),
        ("BOX", (0, 0), (-1, -1), 0.6, HexColor(RULE)),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    return t


def callout(title, text, color=ACCENT, bg=CALLOUT_BG, title_color=ACCENT_DARK):
    ts = ParagraphStyle("ct", parent=st_callout_t, textColor=HexColor(title_color))
    content = [Paragraph(title, ts)]
    content += [Paragraph(t, st_callout) for t in ([text] if isinstance(text, str) else text)]
    t = Table([[content]], colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(bg)),
        ("LINEBEFORE", (0, 0), (0, -1), 3.5, HexColor(color)),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return KeepTogether([Spacer(1, 4), t, Spacer(1, 10)])


def data_table(rows, col_widths, header=True, align_right_from=None, swatch_col=None,
               zebra=False):
    """rows: жагсаалтын жагсаалт (str эсвэл Flowable)."""
    body = []
    for r_i, row in enumerate(rows):
        cells = []
        for c_i, v in enumerate(row):
            if not isinstance(v, str):
                cells.append(v)
                continue
            if header and r_i == 0:
                cells.append(Paragraph(v, st_cell_h))
            else:
                cells.append(Paragraph(v, st_cell))
        body.append(cells)
    t = Table(body, colWidths=col_widths, repeatRows=1 if header else 0)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, HexColor(RULE)),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, HexColor("#cfcec8")),
    ]
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#f0efec")),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, HexColor("#cfcec8")),
        ]
    if zebra:
        for i in range(1 if header else 0, len(rows)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), HexColor("#f8f8f6")))
    t.setStyle(TableStyle(style))
    return t


def swatch(i, text, bold=True):
    """Ангиллын өнгөт тэмдэг + бичвэр (өнгө ганцаараа биш, үргэлж нэртэй)."""
    font = "Arial-Bold" if bold else "Arial"
    return Paragraph(f'<font color="{SERIES[i]}" size="11">■</font>&nbsp;'
                     f'<font name="{font}">{text}</font>', st_cell)


def section(num, title, need=170):
    return [
        CondPageBreak(need),
        Paragraph(f'<font color="{ACCENT}">{num:02d}</font>&nbsp;&nbsp;{title}', st_h1),
    ]


def image_from_fig(fig, width=CW):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=250, facecolor=SURFACE)
    plt.close(fig)
    buf.seek(0)
    w_in, h_in = fig.get_size_inches()
    return Image(buf, width=width, height=width * h_in / w_in)


# ----------------------------------------------------------------------------
# Хэмжилтүүд (бодитоор ажиллуулна)
# ----------------------------------------------------------------------------
def measure_list_vs_set():
    ns = [100_000 * i for i in range(1, 11)]
    t_list, t_set = [], []
    for n in ns:
        a = list(range(n))
        s = set(a)
        target = -1  # байхгүй утга → хамгийн муу тохиолдол
        tl = min(timeit.repeat(lambda: target in a, number=5, repeat=5)) / 5
        ts = min(timeit.repeat(lambda: target in s, number=20000, repeat=5)) / 20000
        t_list.append(tl * 1000)  # мс
        t_set.append(ts * 1000)
    return ns, t_list, t_set


def fib_naive(n):
    if n < 2:
        return n
    return fib_naive(n - 1) + fib_naive(n - 2)


@lru_cache(maxsize=None)
def fib_memo(n):
    if n < 2:
        return n
    return fib_memo(n - 1) + fib_memo(n - 2)


def measure_fib(n=30):
    t0 = time.perf_counter()
    fib_naive(n)
    t1 = time.perf_counter()
    fib_memo.cache_clear()
    t2 = time.perf_counter()
    fib_memo(n)
    t3 = time.perf_counter()
    return t1 - t0, t3 - t2


# ----------------------------------------------------------------------------
# Графикууд
# ----------------------------------------------------------------------------
plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 9,
    "axes.edgecolor": "#b9b8b2",
    "axes.labelcolor": TEXT2,
    "axes.linewidth": 0.8,
    "xtick.color": TEXT2,
    "ytick.color": TEXT2,
    "xtick.major.size": 0,
    "ytick.major.size": 0,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.facecolor": SURFACE,
    "figure.facecolor": SURFACE,
})


def chart_growth():
    n = np.linspace(1, 20, 800)
    ys = [np.ones_like(n), np.log2(n), n, n * np.log2(n), n ** 2, 2 ** n]
    YMAX = 100
    fig, ax = plt.subplots(figsize=(6.7, 3.7))
    fig.subplots_adjust(left=0.08, right=0.86, top=0.95, bottom=0.25)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for i, (y, label) in enumerate(zip(ys, CLASSES)):
        ax.plot(n, y, color=SERIES[i], lw=2, label=label, solid_capstyle="round")
    ax.set_xlim(1, 20)
    ax.set_ylim(0, YMAX)
    ax.set_xticks([1, 5, 10, 15, 20])
    ax.set_xlabel("n — оролтын хэмжээ")
    ax.set_ylabel("Алхмын тоо")

    # Шууд шошго: дээд ирмэгээр гарсан шугамууд
    for i, x_exit in [(5, np.log2(YMAX)), (4, np.sqrt(YMAX))]:
        ax.plot([x_exit], [YMAX], "o", ms=5.5, color=SERIES[i], mec=SURFACE,
                mew=1.2, clip_on=False, zorder=5)
        ax.text(x_exit + 0.35, YMAX - 4, CLASSES[i], color=INK, fontsize=9,
                fontweight="bold", va="top")
    # Баруун захын шошго (давхцахгүйгээр зайлуулна)
    ends = [(i, ys[i][-1]) for i in (0, 1, 2, 3)]
    ends.sort(key=lambda t: t[1])
    placed = []
    for i, y in ends:
        y_lab = y if not placed else max(y, placed[-1] + 7)
        placed.append(y_lab)
        ax.plot([20], [y], "o", ms=5.5, color=SERIES[i], mec=SURFACE, mew=1.2,
                clip_on=False, zorder=5)
        ax.text(20.6, y_lab, CLASSES[i], color=INK, fontsize=9,
                fontweight="bold", va="center")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=6,
              frameon=False, fontsize=8.5, handlelength=1.6, columnspacing=1.4)
    return image_from_fig(fig)


def chart_list_vs_set(ns, t_list, t_set):
    x = [v / 1000 for v in ns]
    fig, ax = plt.subplots(figsize=(6.7, 3.3))
    fig.subplots_adjust(left=0.09, right=0.80, top=0.94, bottom=0.16)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.plot(x, t_list, color=SERIES[2], lw=2, marker="o", ms=6, mec=SURFACE,
            mew=1.2, label="x in list")
    ax.plot(x, t_set, color=SERIES[0], lw=2, marker="o", ms=6, mec=SURFACE,
            mew=1.2, label="x in set")
    ax.set_xlim(0, 1050)
    ax.set_ylim(0, max(t_list) * 1.12)
    ax.set_xticks([0, 200, 400, 600, 800, 1000])
    ax.set_xlabel("n — элементийн тоо (мянгаар)")
    ax.set_ylabel("Нэг хайлтын хугацаа (мс)")
    ax.text(1070, t_list[-1], f"x in list\nO(n) · {t_list[-1]:.1f} мс",
            color=INK, fontsize=9, fontweight="bold", va="center", clip_on=False)
    ax.text(1070, max(t_list) * 0.07, f"x in set\nO(1) · ≈{t_set[-1] * 1000:.2f} мкс",
            color=INK, fontsize=9, fontweight="bold", va="center", clip_on=False)
    ax.legend(loc="upper left", frameon=False, fontsize=8.5)
    return image_from_fig(fig)


def chart_binary_search():
    vals = [2, 5, 8, 12, 16, 23, 38, 41, 56, 61, 67, 72, 80, 85, 91, 99]
    target = 67
    steps = []
    lo, hi = 0, len(vals) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        steps.append((lo, hi, mid))
        if vals[mid] == target:
            break
        if vals[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1

    fig, ax = plt.subplots(figsize=(6.7, 2.75))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.97, bottom=0.03)
    ax.set_axis_off()
    row_h = 1.35
    for r, (lo, hi, mid) in enumerate(steps):
        y = -r * row_h
        last = r == len(steps) - 1
        for i, v in enumerate(vals):
            if i == mid:
                fc, tc, fw = ("#008300" if last else ACCENT_DARK), "white", "bold"
            elif lo <= i <= hi:
                fc, tc, fw = "#d6e6fa", INK, "normal"
            else:
                fc, tc, fw = "#f0efec", "#b3b2ac", "normal"
            ax.add_patch(FancyBboxPatch((i + 0.06, y + 0.06), 0.88, 0.88,
                                        boxstyle="round,pad=0,rounding_size=0.12",
                                        fc=fc, ec="none"))
            ax.text(i + 0.5, y + 0.5, str(v), ha="center", va="center",
                    fontsize=8.5, color=tc, fontweight=fw)
        size = hi - lo + 1
        ax.text(-0.3, y + 0.5, f"{r + 1}-р алхам\n{size} элемент", ha="right",
                va="center", fontsize=8.5, color=TEXT2, linespacing=1.25)
        m = vals[mid]
        if m == target:
            note = f"{m} = {target}  → олдлоо!"
        elif m < target:
            note = f"{m} < {target}  → баруун хагас"
        else:
            note = f"{m} > {target}  → зүүн хагас"
        ax.text(16.35, y + 0.5, note, ha="left", va="center", fontsize=8.5,
                color=INK, fontweight="bold" if last else "normal")
    ax.set_xlim(-3.4, 21.6)
    ax.set_ylim(-(len(steps) - 1) * row_h - 0.1, 1.05)
    return image_from_fig(fig)


# ----------------------------------------------------------------------------
# Хуудасны чимэглэл
# ----------------------------------------------------------------------------
BAND_H = 300


def draw_cover(canv, doc):
    canv.saveState()
    canv.setFillColor(HexColor(SURFACE))
    canv.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    # Дээд хар хөх зурвас
    top = PAGE_H
    canv.setFillColor(HexColor("#101a2b"))
    canv.rect(0, top - BAND_H, PAGE_W, BAND_H, stroke=0, fill=1)

    # Чимэглэлийн өсөлтийн муруйнууд (баруун талд)
    dark = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#2fa52f"]
    x0, x1 = PAGE_W * 0.56, PAGE_W - 34
    y0, y1 = top - BAND_H + 34, top - 40
    canv.setStrokeColor(HexColor("#2a3850"))
    canv.setLineWidth(0.6)
    for k in range(5):
        yy = y0 + (y1 - y0) * k / 4
        canv.line(x0, yy, x1, yy)
    ns = np.linspace(1, 20, 160)
    funcs = [np.ones_like(ns), np.log2(ns), ns, ns * np.log2(ns), ns ** 2, 2 ** ns]
    canv.setLineWidth(2.2)
    canv.setLineCap(1)
    for col, f in zip(dark, funcs):
        pts = [(x0 + (x1 - x0) * (n_ - 1) / 19, y0 + (y1 - y0) * min(v, 100) / 100)
               for n_, v in zip(ns, f) if v <= 100]
        canv.setStrokeColor(HexColor(col))
        p = canv.beginPath()
        p.moveTo(*pts[0])
        for pt in pts[1:]:
            p.lineTo(*pt)
        canv.drawPath(p, stroke=1, fill=0)

    # Гарчиг
    canv.setFillColor(HexColor("#9ec5f4"))
    canv.setFont("Arial-Bold", 10)
    canv.drawString(MARGIN_X, top - 62, "АЛГОРИТМЫН ҮНДЭС  ·  PYTHON")
    canv.setFillColor(HexColor("#ffffff"))
    canv.setFont("Arial-Bold", 58)
    canv.drawString(MARGIN_X, top - 135, "Big O")
    canv.setFont("Arial", 30)
    canv.drawString(MARGIN_X, top - 175, "зөн совин")
    canv.setFillColor(HexColor("#c3c2b7"))
    canv.setFont("Arial", 12)
    canv.drawString(MARGIN_X, top - 215, "Цаг ба санах ойн төвөгшил,")
    canv.drawString(MARGIN_X, top - 232, "өсөлтийн харьцуулалт")
    canv.restoreState()


def draw_page(canv, doc):
    canv.saveState()
    canv.setFillColor(HexColor(SURFACE))
    canv.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    canv.setStrokeColor(HexColor(RULE))
    canv.setLineWidth(0.6)
    canv.line(MARGIN_X, PAGE_H - 14 * mm, PAGE_W - MARGIN_X, PAGE_H - 14 * mm)
    canv.setFont("Arial", 8)
    canv.setFillColor(HexColor(MUTED))
    canv.drawString(MARGIN_X, PAGE_H - 12 * mm, "Big O — зөн совин")
    canv.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 12 * mm, "Түвшин: Ойлголт")
    canv.drawCentredString(PAGE_W / 2, 10 * mm, str(doc.page))
    canv.restoreState()


class LessonDoc(BaseDocTemplate):
    def __init__(self, filename, **kw):
        super().__init__(filename, pagesize=A4, **kw)
        cover_frame = Frame(MARGIN_X, 18 * mm, CW, PAGE_H - BAND_H - 18 * mm - 26,
                            id="cover", leftPadding=0, rightPadding=0,
                            topPadding=0, bottomPadding=0)
        body_frame = Frame(MARGIN_X, 18 * mm, CW, PAGE_H - 18 * mm - 22 * mm,
                           id="body", leftPadding=0, rightPadding=0,
                           topPadding=0, bottomPadding=0)
        self.addPageTemplates([
            PageTemplate("cover", [cover_frame], onPage=draw_cover),
            PageTemplate("normal", [body_frame], onPage=draw_page),
        ])
        self._outline_i = 0

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "H1":
            key = f"s{self._outline_i}"
            self._outline_i += 1
            text = re.sub(r"<[^>]+>", "", flowable.text).replace("&nbsp;", " ")
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=0)


# ----------------------------------------------------------------------------
# Агуулга
# ----------------------------------------------------------------------------
def class_card(i, name, meaning, analogy, code, growth, extra=None):
    color = SERIES[i]
    rows = [
        [Paragraph(f'{CLASSES[i]}<font name="Arial" size="12" color="{TEXT2}">'
                   f'&nbsp;&nbsp;·&nbsp;&nbsp;{name}</font>', st_card_head)],
        [P(f"<b>Утга:</b> {meaning}", st_callout)],
        [P(f"<b>Зүйрлэл:</b> {analogy}", st_callout)],
        [code_block(code, width=CW - 30)],
        [P(f'<b>n 2 дахин томорвол →</b> {growth}', st_callout)],
    ]
    if extra:
        rows.append([P(extra, st_small)])
    t = Table(rows, colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(CARD_BG)),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor(RULE)),
        ("LINEBEFORE", (0, 0), (0, -1), 4, HexColor(color)),
        ("LEFTPADDING", (0, 0), (-1, -1), 15),
        ("RIGHTPADDING", (0, 0), (-1, -1), 15),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("TOPPADDING", (0, 3), (-1, 3), 6),
        ("BOTTOMPADDING", (0, 3), (-1, 3), 6),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 11),
    ]))
    return KeepTogether([t, Spacer(1, 12)])


def build():
    print("Хэмжилт хийж байна…")
    ns, t_list, t_set = measure_list_vs_set()
    fib_slow, fib_fast = measure_fib(30)
    ratio = t_list[-1] / t_set[-1]

    s = []  # story

    # ------------------------------------------------------------- Нүүр хуудас
    chip_style = ParagraphStyle("chip", parent=st_cell, fontSize=9.5, alignment=TA_CENTER)
    chips = Table([[P("<b>Түвшин:</b> Ойлголт", chip_style),
                    P("<b>Жишээ:</b> Python 3", chip_style),
                    P("<b>Урьдчилсан мэдлэг:</b> for давталт, функц", chip_style)]],
                  colWidths=[CW * 0.24, CW * 0.24, CW * 0.44], hAlign="LEFT")
    chips.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#f0efec")),
        ("ROUNDEDCORNERS", [10, 10, 10, 10]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEAFTER", (0, 0), (1, 0), 1.5, HexColor(SURFACE)),
    ]))
    s += [chips, Spacer(1, 18)]

    s.append(P("Энэ хичээлийг уншсаны дараа та:", st_h2))
    s += bullets([
        "Big O <b>юуг</b> хэмждэг, <b>юуг</b> хэмждэггүйг энгийн үгээр тайлбарлаж чадна.",
        "Python код хараад түүний <b>цагийн</b> ба <b>санах ойн</b> төвөгшлийг таамаглана.",
        "O(1), O(log n), O(n), O(n log n), O(n²), O(2ⁿ) -ийг өсөлтийн хурдаар нь эрэмбэлнэ.",
        "Хурд ба санах ойн хоорондох <b>солилцоог</b> (trade-off) ойлгоно.",
    ])
    s.append(Spacer(1, 10))
    s.append(P("Агуулга", st_h2))
    toc = [
        "Big O гэж юу вэ?", "Алхам тоолох ба хялбарчлах дүрэм",
        "Түгээмэл 6 ангилал", "Өсөлтийн харьцуулалт",
        "Python дээр өөрсдөө хэмжиж үзье", "Санах ойн төвөгшил",
        "Цаг ба санах ойн солилцоо", "Python үйлдлүүдийн хуудас",
        "Түгээмэл андуурал", "Дасгал", "Хураангуй",
    ]
    half = (len(toc) + 1) // 2
    toc_st = ParagraphStyle("toc", parent=st_body, spaceAfter=0, leading=17)
    toc_rows = []
    for r in range(half):
        row = []
        for col in (0, 1):
            k = r + col * half
            row.append(P(f'<font color="{ACCENT}"><b>{k + 1:02d}</b></font>&nbsp;&nbsp;{toc[k]}',
                         toc_st) if k < len(toc) else "")
        toc_rows.append(row)
    toc_t = Table(toc_rows, colWidths=[CW / 2, CW / 2])
    toc_t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0),
                               ("TOPPADDING", (0, 0), (-1, -1), 1),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    s.append(toc_t)
    s.append(Spacer(1, 16))
    s.append(callout("Нэг өгүүлбэрээр",
                     "Big O нь «оролт томрох тусам програмын ажил хэр <b>хурдан өсөх</b> вэ» "
                     "гэсэн асуултад хариулдаг."))
    s += [NextPageTemplate("normal"), PageBreak()]

    # ------------------------------------------------------------- 1
    s += section(1, "Big O гэж юу вэ?")
    s.append(P("Нэг асуудлыг шийддэг хоёр програм байлаа гэж бодъё. Аль нь илүү вэ? "
               "Секундээр хэмжиж харьцуулах нь хамгийн энгийн санаа мэт боловч найдвартай биш: "
               "хариу нь компьютер, програмчлалын хэл, тэр үед ажиллаж буй бусад програм гээд "
               "олон зүйлээс хамаарна. Big O үүний оронд <b>өөр асуулт</b> тавьдаг:", st_body))
    s.append(callout("Big O-гийн асуулт",
                     "<font size=12><b>Оролт томрох тусам ажлын хэмжээ хэрхэн өсөх вэ?</b></font>"))
    s.append(P("Жишээ: утасны дэвтрээс нэр хайх", st_h2))
    s.append(P("1 000 хуудастай утасны дэвтрээс «Тэмүүлэн» гэдэг нэрийг хайж байна гэж төсөөл. "
               "Нэрс цагаан толгойн дарааллаар байгаа.", st_body))
    s.append(data_table([
        ["", "Арга А: эхнээс нь нэг бүрчлэн", "Арга Б: дундаас нь нээх"],
        [P("<b>Яаж?</b>", st_cell), "Хуудас бүрийг дарааллаар нь харна.",
         "Дунд хуудсыг нээж, нэр өмнө нь уу, хойно нь уу гэдгийг хараад хагасыг нь хаяна. "
         "Үлдсэн хагаст дахин давтана."],
        [P("<b>1 000 хуудас</b>", st_cell), "≈ 1 000 алхам", "≈ 10 алхам"],
        [P("<b>2 000 хуудас</b>", st_cell), "≈ 2 000 алхам", "≈ 11 алхам"],
        [P("<b>1 000 000 хуудас</b>", st_cell), "≈ 1 000 000 алхам", "≈ 20 алхам"],
        [P("<b>Big O</b>", st_cell), swatch(2, "O(n)"), swatch(1, "O(log n)")],
    ], [CW * 0.2, CW * 0.38, CW * 0.42]))
    s.append(Spacer(1, 10))
    s.append(P("Дэвтэр 2 дахин зузаарахад А аргын ажил <b>2 дахин</b> нэмэгдсэн бол Б аргынх "
               "ердөө <b>1 алхмаар</b> нэмэгдлээ. Big O яг энэ ялгааг барьж авдаг. "
               "Цаашид <b>n</b> гэдэг нь <b>оролтын хэмжээ</b>: жагсаалтын урт, тэмдэгт мөрийн урт, "
               "хуудасны тоо гэх мэт.", st_body))
    s.append(callout("Гол санаа",
                     "Big O бол <b>хурд биш, өсөлтийн хэлбэр</b>. Энэ нь «n томрох үед юу болох вэ» "
                     "гэдгийг л хэлнэ. Тиймээс бид секунд биш, <b>алхам</b> тоолно."))
    s.append(P("Цаг ба санах ой", st_h2))
    s.append(P("Big O-г хоёр зүйлд хэрэглэдэг:", st_body))
    s += bullets([
        "<b>Цагийн төвөгшил</b> (time complexity): n-ээс хамаарч хэдэн алхам хийх вэ?",
        "<b>Санах ойн төвөгшил</b> (space complexity): n-ээс хамаарч хэр их <i>нэмэлт</i> санах ой эзлэх вэ?",
    ])
    s.append(P("Хоёулаа ижил дүрмээр тооцогддог. Эхлээд цагийг үзээд, 6-р бүлэгт санах ой руу шилжинэ.",
               st_body))

    # ------------------------------------------------------------- 2
    s += section(2, "Алхам тоолох ба хялбарчлах дүрэм")
    s.append(P("Big O-г олохын тулд код хэдэн <b>энгийн алхам</b> (нэмэх, харьцуулах, утга оноох, "
               "индексээр хандах…) хийхийг n-ээр илэрхийлнэ.", st_body))
    s.append(code_block("""
        def niilber(items):
            total = 0              # 1 удаа
            for x in items:        # n удаа эргэнэ
                total += x         # n удаа
            return total           # 1 удаа
    """))
    s.append(Spacer(1, 8))
    s.append(P("Нийт ≈ <b>2n + 2</b> алхам. Гэвч бид үүнийг зүгээр л <b>O(n)</b> гэж бичнэ. Яагаад?",
               st_body))
    s += bullets([
        "<b>«+2» хаягдана:</b> n = 1 000 000 үед 2 000 002 ба 2 000 000 бараг ялгаагүй. "
        "Жижиг нэмэгдэхүүн том n дээр ач холбогдлоо алддаг.",
        "<b>«×2» хаягдана:</b> Энэ коэффициент компьютер, хэлнээс хамаарч өөрчлөгддөг. Харин "
        "«n-тэй хамт шулуунаар өсдөг» гэдэг <b>хэлбэр</b> нь хаана ч ижил.",
    ])
    s.append(P("5 хялбарчлах дүрэм", st_h2))
    s.append(data_table([
        ["#", "Дүрэм", "Жишээ"],
        ["1", "Тогтмол коэффициентийг хая", "O(3n) → O(n);   O(500) → O(1)"],
        ["2", "Хамгийн хурдан өсөх гишүүнийг л үлдээ", "O(n² + n + 100) → O(n²)"],
        ["3", "Дараалсан хэсгүүдийг <b>нэм</b>", "давталтын араас давталт: O(n + n) = O(n)"],
        ["4", "Үүрлэсэн (дотор нь) давталтыг <b>үржүүл</b>", "давталт дотор давталт: O(n · n) = O(n²)"],
        ["5", "Өөр оролтод өөр үсэг", "a, b хоёр жагсаалт: O(a + b) эсвэл O(a · b)"],
    ], [CW * 0.06, CW * 0.44, CW * 0.50], zebra=True))
    s.append(Spacer(1, 10))
    s.append(P("3 ба 4-р дүрмийг нэг жишээн дээр:", st_body))
    s.append(code_block("""
        def jishee(items):
            for x in items:            # (1) n алхам
                print(x)

            for x in items:            # (2) гадна давталт: n удаа
                for y in items:        #     дотор давталт: n удаа  → n · n
                    print(x, y)

        # Нийт: n + n²  →  хамгийн хурдан өсөх гишүүн  →  O(n²)
    """))
    s.append(Spacer(1, 4))
    s.append(callout("Анхаар: 5-р дүрэм",
                     "Хоёр <b>өөр</b> жагсаалт дээр давталт хийвэл O(n²) гэж бичих нь буруу. "
                     f"{c('for x in a: for y in b:')} нь <b>O(a · b)</b>. Хэрэв a = 10, b = 1 000 000 "
                     "бол энэ нь 10 сая, харин O(n²) гэвэл утгагүй их тоо гарна."))

    # ------------------------------------------------------------- 3
    s += section(3, "Түгээмэл 6 ангилал")
    s.append(P("Ихэнх кодын төвөгшил дараах 6 ангиллын аль нэгд багтдаг. "
               "<b>Сайнаас муу руу</b> эрэмбэлэв. Ангилал бүрийн өнгө баримт бичиг даяар ижил байна.",
               st_body))
    s.append(Spacer(1, 4))
    s.append(class_card(
        0, "Тогтмол",
        "Оролт хэдэн ч том байсан алхмын тоо <b>өөрчлөгдөхгүй</b>.",
        "Номын тавиурын дугаар, байрлалыг нь мэддэг номоо шууд очиж авах.",
        """
        def ehnii_element(items):
            return items[0]          # 10 элемент ч, 10 сая ч — 1 алхам

        nas = {"Бат": 20, "Сараа": 19}
        print(nas["Сараа"])          # dict-ээс түлхүүрээр авах: O(1)
        """,
        "ажил <b>өөрчлөгдөхгүй</b>."))
    s.append(class_card(
        1, "Логарифм",
        "Алхам бүрт асуудал <b>хоёр дахин багасна</b>. "
        "log<sub>2</sub> n гэдэг нь «n-ийг хэдэн удаа 2-т хуваахад 1 болох вэ» гэсэн тоо.",
        "Утасны дэвтрийг дундаас нь нээх; «1-ээс 100-ын хооронд бодсон тоог таа» тоглоом.",
        """
        def binary_search(items, target):     # items эрэмбэлэгдсэн байх ёстой!
            lo, hi = 0, len(items) - 1
            while lo <= hi:
                mid = (lo + hi) // 2
                if items[mid] == target:
                    return mid
                elif items[mid] < target:
                    lo = mid + 1              # зүүн хагасыг хаяна
                else:
                    hi = mid - 1              # баруун хагасыг хаяна
            return -1
        """,
        "ердөө <b>+1 алхам</b>.",
        "log<sub>2</sub> 1 000 000 ≈ 20. Сая элементтэй эрэмбэлэгдсэн жагсаалтаас 20 орчим алхамд олно!"))
    s.append(KeepTogether([
        chart_binary_search(),
        P("Зураг 1. 16 элементтэй жагсаалтаас 67-г хайх нь. Алхам бүрт хайх хүрээ (цэнхэр) "
          "хагасаар багасаж, 4 алхамд олдлоо. Энгийн хайлт бол 11 алхам хийх байсан.", st_caption),
    ]))
    s.append(class_card(
        2, "Шугаман",
        "Элемент бүрийг <b>нэг удаа</b> (эсвэл тогтмол хэдэн удаа) харна.",
        "Ангийн хүүхэд бүрт нэг нэг чихэр тараах.",
        """
        def hamgiin_ih(items):
            best = items[0]
            for x in items:          # n удаа
                if x > best:
                    best = x
            return best
        """,
        "ажил <b>2 дахин</b>."))
    s.append(class_card(
        3, "«n лог n»",
        "Хамгийн сайн ерөнхий <b>эрэмбэлэх</b> алгоритмуудын төвөгшил. "
        "n элемент бүрийг log n «давхарга»-аар дамжуулна гэж төсөөл.",
        "Хөзрийн багцыг хоёр хувааж, тус бүрийг эрэмбэлээд, буцааж нийлүүлэх (merge sort).",
        """
        onoo = [72, 95, 61, 88, 79]
        erembelsen = sorted(onoo)    # Python-ий Timsort: O(n log n)
        onoo.sort()                  # байрандаа эрэмбэлэх: мөн O(n log n)
        """,
        "ажил <b>2-оос арай илүү</b> дахин (≈ 2.2)."))
    s.append(class_card(
        4, "Квадрат",
        "Элемент бүрийг <b>бусад бүх</b> элементтэй харьцуулна. Ихэвчлэн давталт дотор давталт.",
        "Ангийн хүүхэд бүр бусад бүх хүүхэдтэй гар барих.",
        """
        def davhardsan_bii_yu(items):
            n = len(items)
            for i in range(n):               # n удаа
                for j in range(i + 1, n):    #   дотор нь ≈ n/2 удаа
                    if items[i] == items[j]:
                        return True
            return False
        """,
        "ажил <b>4 дахин</b>!",
        "n(n−1)/2 харьцуулалт → n²/2 → коэффициентийг хаяхад O(n²)."))
    s.append(class_card(
        5, "Экспоненциал",
        "n-ийг <b>1-ээр</b> нэмэхэд л ажил <b>2 дахин</b> өснө. "
        "Бүх боломжит хослолыг шалгахад ихэвчлэн гардаг.",
        "n ширхэг гэрлийн унтраалгын бүх асаах/унтраах хослолыг туршиж үзэх: 2ⁿ хувилбар.",
        """
        def fib(n):
            if n < 2:
                return n
            return fib(n - 1) + fib(n - 2)   # дуудлага бүр 2 болж салаална
        """,
        "ажил <b>квадрат зэрэгт</b> өснө: 2ⁿ → 2²ⁿ = (2ⁿ)².",
        "fib(40)-ийг ингэж бодоход 331 160 281 удаа функц дуудагдана! "
        "7-р бүлэгт үүнийг хэрхэн хурдасгахыг үзнэ."))

    # ------------------------------------------------------------- 4
    s += section(4, "Өсөлтийн харьцуулалт", need=420)
    s.append(P("Зургийн хэлбэрээр харвал ялгаа нь шууд мэдрэгдэнэ. Доорх график n = 1…20 гэсэн "
               "<b>маш жижиг</b> оролт дээр ч гэсэн 2ⁿ ба n² хэр хурдан «тааз» руу хөөрч байгааг харуулна.",
               st_body))
    s.append(KeepTogether([
        chart_growth(),
        P("Зураг 2. Алхмын тоо, n = 1…20. Тэнхлэгийг 100-аар таслав: O(2ⁿ) нь n ≈ 6.6, O(n²) нь "
          "n = 10 үед л 100-г давна. Доод талын O(1), O(log n) бараг хэвтээ хэвээр.", st_caption),
    ]))
    s.append(P("Тоогоор харьцуулбал", st_h2))

    def fmt(v):
        return f"{v:,.0f}".replace(",", " ")

    s.append(data_table([
        ["Ангилал", "Нэр", "n = 10", "n = 100", "n = 1 000", "n 2 дахин → ажил"],
        [swatch(0, CLASSES[0]), "Тогтмол", "1", "1", "1", "өөрчлөгдөхгүй"],
        [swatch(1, CLASSES[1]), "Логарифм", "3", "7", "10", "+1 алхам"],
        [swatch(2, CLASSES[2]), "Шугаман", "10", "100", "1 000", "×2"],
        [swatch(3, CLASSES[3]), "n лог n", fmt(10 * np.log2(10)), fmt(100 * np.log2(100)),
         fmt(1000 * np.log2(1000)), "×2-оос арай их"],
        [swatch(4, CLASSES[4]), "Квадрат", "100", "10 000", "1 000 000", "<b>×4</b>"],
        [swatch(5, CLASSES[5]), "Экспоненциал", "1 024", "≈ 1.3 × 10<super>30</super>",
         "≈ 1.1 × 10<super>301</super>", "<b>квадрат зэрэгт</b>"],
    ], [CW * 0.17, CW * 0.18, CW * 0.10, CW * 0.16, CW * 0.17, CW * 0.22], zebra=True))
    s.append(Spacer(1, 12))
    time_block = [P("Энэ нь хугацааны хувьд юу гэсэн үг вэ?", st_h2)]
    time_block.append(P("Компьютер секундэд <b>100 сая</b> (10<super>8</super>) энгийн алхам хийдэг гэж үзээд "
               "<b>n = 1 000 000</b> элемент боловсруулахад хэр удах вэ гэдгийг тооцъё. "
               "(Python үүнээс хэд дахин удаан байж болох ч харьцаа нь ижил.)", st_body))
    time_block.append(data_table([
        ["Ангилал", "Алхмын тоо", "Хугацаа"],
        [swatch(0, CLASSES[0]), "1", "агшин зуур"],
        [swatch(1, CLASSES[1]), "≈ 20", "0.0000002 сек"],
        [swatch(2, CLASSES[2]), "1 000 000", "0.01 сек"],
        [swatch(3, CLASSES[3]), "≈ 20 000 000", "0.2 сек"],
        [swatch(4, CLASSES[4]), "10<super>12</super>", "<b>≈ 2.8 цаг</b>"],
        [swatch(5, CLASSES[5]), "≈ 10<super>301 030</super>",
         "<b>Орчлон ертөнцийн наснаас ч хэмжээлшгүй урт</b>"],
    ], [CW * 0.2, CW * 0.3, CW * 0.5], zebra=True))
    s.append(KeepTogether(time_block))
    s.append(Spacer(1, 6))
    s.append(callout("Зөн совин",
                     "<b>Сайн алгоритм хурдан компьютерээс илүү чухал.</b> O(n²) кодыг 100 дахин хурдан "
                     "компьютер дээр ажиллуулсан ч n хангалттай том болоход O(n log n) код ялна."))

    # ------------------------------------------------------------- 5
    s += section(5, "Python дээр өөрсдөө хэмжиж үзье")
    s.append(P(f"Онол бодит байдалтай таарч байна уу? {c('x in list')} ба {c('x in set')} хоёрыг "
               "харьцуулъя. Жагсаалтаас (list) хайхад Python элемент бүрийг дарааллаар нь шалгадаг — "
               "<b>O(n)</b>. Харин олонлог (set) нь <i>hash хүснэгт</i> ашиглан тухайн утгын байрлалыг "
               "шууд тооцоолж очдог — дунджаар <b>O(1)</b>.", st_body))
    s.append(code_block("""
        import timeit

        for n in [100_000, 500_000, 1_000_000]:
            a = list(range(n))       # жагсаалт
            s = set(a)               # олонлог (hash хүснэгт)
            target = -1              # байхгүй утга → хамгийн муу тохиолдол

            t_list = timeit.timeit(lambda: target in a, number=20) / 20
            t_set = timeit.timeit(lambda: target in s, number=20) / 20
            print(f"n={n:>9,}  list: {t_list*1000:8.3f} мс   set: {t_set*1000:.5f} мс")
    """))
    s.append(Spacer(1, 10))
    s.append(KeepTogether([
        chart_list_vs_set(ns, t_list, t_set),
        P("Зураг 3. Энэ PDF-ийг үүсгэх үед бодитоор хэмжсэн үр дүн (n = 100 000 … 1 000 000, "
          "5 давталтын хамгийн бага утга).", st_caption),
    ]))
    s.append(P(f"Манай хэмжилтээр n = 1 000 000 үед list-ээс хайхад <b>{t_list[-1]:.2f} мс</b>, "
               f"set-ээс хайхад <b>{t_set[-1] * 1000:.3f} микросекунд</b> зарцуулсан — "
               f"ойролцоогоор <b>{fmt(float(f'{ratio:.2g}'))} дахин</b> ялгаа. Таны компьютер дээрх тоо өөр гарах ч "
               "<b>хэлбэр</b> нь ижил: list шулуун шугамаар өсөж, set хэвтээ хэвээр байна.", st_body))
    s.append(callout("Практик зөвлөгөө",
                     f"Олон удаа «байгаа юу?» гэж шалгах бол өгөгдлөө <b>set</b> (эсвэл dict) болго. "
                     f"Энэ ганц өөрчлөлт л ихэнхдээ програмыг олон зуу дахин хурдасгадаг."))

    # ------------------------------------------------------------- 6
    s += section(6, "Санах ойн төвөгшил")
    s.append(P("Санах ойн төвөгшил гэдэг нь алгоритм ажиллахдаа оролтоос <b>гадна нэмэлтээр</b> "
               "хэр их санах ой эзлэх вэ гэдэг. Дүрэм нь цагийнхтай яг адилхан.", st_body))
    s.append(P("O(1) санах ой — хэдэн ч элемент байсан цөөн хувьсагч", st_h2))
    s.append(code_block("""
        def niilber(items):
            total = 0                # ганц хувьсагч
            for x in items:
                total += x
            return total             # нэмэлт санах ой: O(1)
    """))
    s.append(P("O(n) санах ой — оролттой адил хэмжээтэй шинэ бүтэц", st_h2))
    s.append(code_block("""
        def hoyor_dahin(items):
            result = []
            for x in items:
                result.append(x * 2)
            return result            # n элементтэй шинэ жагсаалт: O(n)
    """))
    s.append(P("O(n) санах ой — рекурсийн стек", st_h2))
    s.append(code_block("""
        def toololt(n):
            if n == 0:
                return 0
            return 1 + toololt(n - 1)   # n ширхэг дуудлага зэрэг «хүлээж» стек дээр байна
    """))
    s.append(Spacer(1, 6))
    s.append(P("Рекурс шинэ жагсаалт үүсгээгүй ч дуудлага бүр стек дээр зай эзэлдэг. Python "
               f"рекурсийн гүнийг анхдагчаар ≈1000-аар хязгаарладаг тул {c('toololt(5000)')} нь "
               f"{c('RecursionError')} өгнө — санах ойн төвөгшлийн бодит жишээ!", st_body))
    s.append(P("Нуугдмал санах ой", st_h2))
    s.append(data_table([
        ["Код", "Санах ой", "Яагаад?"],
        [P(c("items[1:]"), st_cell), "O(k)", "Зүсэлт шинэ хуулбар үүсгэнэ (k = зүссэн хэсгийн урт)."],
        [P(c("[x * 2 for x in items]"), st_cell), "O(n)", "List comprehension шинэ жагсаалт үүсгэнэ."],
        [P(c("(x * 2 for x in items)"), st_cell), "O(1)", "Генератор: нэг удаад зөвхөн нэг утга."],
        [P(c("sorted(items)"), st_cell), "O(n)", "Шинэ эрэмбэлэгдсэн жагсаалт буцаана."],
        [P(c("items.sort()"), st_cell), "≈ O(1)*", "Байрандаа эрэмбэлнэ (шинэ жагсаалт үүсгэхгүй)."],
    ], [CW * 0.33, CW * 0.15, CW * 0.52], zebra=True))
    s.append(P("* Timsort дотроо түр санах ой (хамгийн муу үед n/2 хүртэл) ашиглаж болох ч шинэ "
               "жагсаалт буцаадаггүй.", st_caption))

    # ------------------------------------------------------------- 7
    s += section(7, "Цаг ба санах ойн солилцоо")
    s.append(P("Ихэнхдээ <b>нэмэлт санах ой зарцуулж хугацаа хэмнэж</b> болдог. 3-р бүлгийн "
               "«давхардсан элемент байгаа юу?» асуудлыг өөр аргаар бодъё:", st_body))
    s.append(code_block("""
        def davhardsan_bii_yu_hurdan(items):
            harsan = set()               # аль хэдийн харсан утгууд
            for x in items:              # n удаа
                if x in harsan:          # set-ээс хайх: O(1)
                    return True
                harsan.add(x)            # O(1)
            return False
    """))
    s.append(Spacer(1, 10))
    s.append(data_table([
        ["Арга", "Цаг", "Санах ой", "n = 100 000 үед"],
        ["А: хоёр давталт (3-р бүлэг)", swatch(4, "O(n²)"), swatch(0, "O(1)"),
         "≈ 5 000 000 000 харьцуулалт"],
        ["Б: set ашиглах", swatch(2, "O(n)"), swatch(2, "O(n)"), "≈ 100 000 шалгалт"],
    ], [CW * 0.32, CW * 0.16, CW * 0.16, CW * 0.36]))
    s.append(Spacer(1, 6))
    s.append(P("Б арга 100 000 утга хадгалах санах ой «зардал» гаргаж, оронд нь 50 000 дахин бага "
               "алхам хийж байна. Энэ бол маш ашигтай наймаа.", st_body))
    s.append(P("Өөр нэг жишээ: «санаж авах» (memoization)", st_h2))
    s.append(P(f"3-р бүлгийн {c('fib')} нэг ижил утгыг дахин дахин боддог байсан. Бодсон хариугаа "
               "санаж авбал:", st_body))
    s.append(code_block("""
        from functools import lru_cache

        @lru_cache(maxsize=None)          # бодсон хариуг санах ойд хадгална
        def fib(n):
            if n < 2:
                return n
            return fib(n - 1) + fib(n - 2)

        # Цаг: O(2ⁿ) → O(n)       Санах ой: O(n)
    """))
    s.append(Spacer(1, 6))
    s.append(P(f"Манай хэмжилтээр <b>fib(30)</b>: энгийн хувилбар <b>{fib_slow:.2f} сек</b>, санах ойтой "
               f"хувилбар <b>{fib_fast * 1e6:.0f} микросекунд</b>. fib(40) нь ≈123 дахин олон дуудлага "
               f"хийдэг тул энгийн хувилбар ≈ <b>{fib_slow * 123:.0f} сек</b> болох бол санах ойтой "
               "нь мөн л агшин зуур.", st_body))
    s.append(callout("Дүгнэлт",
                     "Санах ой хангалттай бол хурдыг сонгох нь ихэвчлэн зөв. Гэхдээ маш том өгөгдөл "
                     "дээр санах ой дуусах эрсдэлтэйг үргэлж бодоорой."))

    # ------------------------------------------------------------- 8
    s += section(8, "Python үйлдлүүдийн хуудас")
    s.append(P("Өдөр тутам хэрэглэдэг үйлдлүүдийн цагийн төвөгшил. Нуугдмал O(n)-ийг олоход хэрэгтэй.",
               st_body))

    def op(name, code, cost_i, cost, note):
        return [name, P(c(code), st_cell), swatch(cost_i, cost), note]

    rows = [["Үйлдэл", "Код", "Цаг", "Тайлбар"]]
    group_rows = []

    def group(title):
        group_rows.append(len(rows))
        rows.append([P(f"<b>{title}</b>", st_cell), "", "", ""])

    group("list (жагсаалт)")
    rows += [
        op("Индексээр авах", "a[i]", 0, "O(1)", "Байрлал нь шууд тооцоологдоно"),
        op("Төгсгөлд нэмэх", "a.append(x)", 0, "O(1)*", ""),
        op("Төгсгөлөөс авах", "a.pop()", 0, "O(1)", ""),
        op("Эхнээс авах", "a.pop(0)", 2, "O(n)", "Бусад бүх элемент нэг байр шилжинэ"),
        op("Эхэнд оруулах", "a.insert(0, x)", 2, "O(n)", "Мөн адил шилжүүлэлт"),
        op("Хайх", "x in a", 2, "O(n)", "Нэг бүрчлэн шалгана"),
        op("Урт", "len(a)", 0, "O(1)", "Урт нь хадгалагдсан байдаг"),
        op("Зүсэх", "a[i:j]", 2, "O(k)", "k = j − i; шинэ хуулбар"),
        op("Эрэмбэлэх", "a.sort()", 3, "O(n log n)", ""),
        op("Нийлбэр, хамгийн их/бага", "sum(a), max(a)", 2, "O(n)", ""),
    ]
    group("set ба dict")
    rows += [
        op("Хайх", "x in s,  k in d", 0, "O(1)*", "hash ашиглана"),
        op("Нэмэх", "s.add(x),  d[k] = v", 0, "O(1)*", ""),
        op("Түлхүүрээр авах", "d[k]", 0, "O(1)*", ""),
    ]
    group("collections.deque")
    rows += [
        op("Хоёр талаас нэмэх/авах", "dq.appendleft(x), dq.popleft()", 0, "O(1)",
           "Дараалалд (queue) list-ийн оронд хэрэглэ"),
    ]
    t = data_table(rows, [CW * 0.25, CW * 0.27, CW * 0.17, CW * 0.31])
    extra = []
    for r in group_rows:
        extra += [("SPAN", (0, r), (-1, r)), ("BACKGROUND", (0, r), (-1, r), HexColor("#f6f5f2"))]
    t.setStyle(TableStyle(extra))
    s.append(t)
    s.append(P("* Дундаж тохиолдолд. Ховор тохиолдолд (жишээ нь list дотоод санах ойгоо томруулах үед) "
               "нэг үйлдэл удаан байж болох ч нийтдээ O(1) гэж тооцно.", st_caption))

    # ------------------------------------------------------------- 9
    s += section(9, "Түгээмэл андуурал")
    myths = [
        ("«O(1) гэдэг нь маш хурдан гэсэн үг»",
         "Үгүй. O(1) гэдэг нь <b>n-ээс хамаарахгүй</b> гэсэн үг. Үргэлж 2 секунд зарцуулдаг үйлдэл ч O(1)."),
        ("«O(n) үргэлж O(n²)-аас хурдан»",
         "Том n дээр тийм. Харин жижиг n дээр тогтмол коэффициентээс шалтгаалан эсрэгээрээ байж болно. "
         "Python-ий sort хүртэл жижиг хэсгүүдийг O(n²) «оруулах эрэмбэлэлт»-ээр эрэмбэлдэг — учир нь "
         "жижиг n дээр тэр нь илүү хурдан."),
        ("«Ганц л давталт байгаа тул O(n)»",
         f"Давталт дотор <b>нуугдмал давталт</b> байж болно: list дээрх {c('in')}, {c('.index()')}, "
         f"{c('.count()')}, {c('insert(0, x)')}, зүсэлт."),
        ("«Big O = яг хугацаа»",
         "Big O нь өсөлтийн <b>дээд хязгаар</b> бөгөөд ихэвчлэн <b>хамгийн муу тохиолдлыг</b> хэлдэг. "
         "Шугаман хайлт азтай бол 1 алхамд олно, гэхдээ хамгийн муу үед n алхам → O(n)."),
    ]
    for i, (title, text) in enumerate(myths, 1):
        s.append(callout(f"Андуурал {i}: {title}", text, color="#eb6834", bg=WARN_BG,
                         title_color="#a8431a"))
        if i == 3:
            s.append(code_block("""
                def niitleg(a, b):
                    result = []
                    for x in a:            # n удаа
                        if x in b:         # b нь list бол → бас n удаа!   →  O(n²)
                            result.append(x)
                    return result

                def niitleg_hurdan(a, b):
                    b_set = set(b)         # O(n) — нэг удаа хөрвүүлнэ
                    return [x for x in a if x in b_set]   # O(n) · O(1)  →  O(n)
            """))
            s.append(Spacer(1, 12))

    # ------------------------------------------------------------- 10
    s.append(PageBreak())
    s += section(10, "Дасгал")
    s.append(P("Функц бүрийн <b>цагийн</b> төвөгшлийг тодорхойл (n = оролтын урт). "
               "5-р дасгалд <b>санах ойн</b> төвөгшлийг ч бод. "
               "Хариуг дараагийн хуудаснаас шалга — эхлээд өөрөө бодоорой!", st_body))
    exercises = [
        """
        def f1(items):
            return len(items) > 0
        """,
        """
        def f2(items):
            for x in items:
                print(x)
            for x in items:
                print(x * 2)
        """,
        """
        def f3(n):
            i = 1
            while i < n:
                i = i * 2
        """,
        """
        def f4(a, b):
            for x in a:
                for y in b:
                    print(x, y)
        """,
        """
        def f5(items):
            result = []
            for x in items:
                if x not in result:
                    result.append(x)
            return result
        """,
        """
        def f6(items):
            items.sort()
            return items[len(items) // 2]
        """,
    ]
    half_w = (CW - 12) / 2
    ex_cells = []
    for i, ex in enumerate(exercises, 1):
        ex_cells.append([P(f"<b>Дасгал {i}</b>", st_cell_b), Spacer(1, 3),
                         code_block(ex, width=half_w)])
    grid = []
    for r in range(0, len(ex_cells), 2):
        grid.append([ex_cells[r], ex_cells[r + 1]])
    gt = Table(grid, colWidths=[half_w + 6, half_w + 6])
    gt.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, -1), 6),
        ("LEFTPADDING", (1, 0), (1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    s.append(gt)

    s.append(PageBreak())
    s.append(P("Дасгалын хариу", st_h2))
    answers = [
        (0, "O(1)", f"{c('len()')} жагсаалтын уртыг хадгалж байдаг тул шууд буцаана."),
        (2, "O(n)", "Дараалсан хоёр давталт: n + n = 2n → коэффициентийг хаявал O(n)."),
        (1, "O(log n)", "i нь 1, 2, 4, 8, … гэж <b>2 дахин</b> өсөж n-д хүрнэ → log<sub>2</sub> n удаа."),
        (4, "O(a · b)", "Гадна давталт a удаа, дотор нь b удаа. a = b = n бол O(n²)."),
        (4, "O(n²)", f"{c('x not in result')} нь list дотор <b>нуугдмал давталт</b>. Санах ой: O(n). "
                     "Сайжруулалт: харсан утгаа set-д хадгалвал цаг O(n) болно."),
        (3, "O(n log n)", f"{c('sort()')} давамгайлна; индексээр авах нь O(1). n log n + 1 → O(n log n)."),
    ]
    ans_rows = [["#", "Хариу", "Тайлбар"]]
    for i, (ci, big, why) in enumerate(answers, 1):
        ans_rows.append([str(i), swatch(ci, big), why])
    s.append(data_table(ans_rows, [CW * 0.06, CW * 0.2, CW * 0.74], zebra=True))
    s.append(Spacer(1, 16))

    # ------------------------------------------------------------- 11
    s += section(11, "Хураангуй")
    s.append(P("Сайнаас муу руу:", st_body))
    labels = ["Гайхалтай", "Маш сайн", "Сайн", "Боломжийн", "Том n дээр удаан", "Зөвхөн жижиг n"]
    ladder_head = [Paragraph(f'<font name="Arial-Bold" size="11">{CLASSES[i]}</font>',
                             ParagraphStyle("lh", parent=st_cell_c)) for i in range(6)]
    ladder_lab = [Paragraph(labels[i], ParagraphStyle("ll", parent=st_cell_c, fontSize=8.5,
                                                      textColor=HexColor(TEXT2)))
                  for i in range(6)]
    lt = Table([ladder_head, ladder_lab], colWidths=[CW / 6] * 6)
    lst = [
        ("TOPPADDING", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 9),
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(CARD_BG)),
    ]
    for i in range(6):
        lst.append(("LINEABOVE", (i, 0), (i, 0), 5, HexColor(SERIES[i])))
        if i < 5:
            lst.append(("LINEAFTER", (i, 0), (i, -1), 2, HexColor(SURFACE)))
    lt.setStyle(TableStyle(lst))
    s.append(lt)
    s.append(Spacer(1, 14))
    s.append(P("Код харахдаа өөрөөсөө асуух 4 асуулт", st_h2))
    s += numbered([
        "<b>Давталт хэдэн удаа эргэх вэ?</b> n удаа → O(n); алхам бүрт хагасаар багасвал → O(log n).",
        "<b>Давталт дотор давталт байна уу?</b> Байвал үржүүл → O(n²), O(a · b).",
        f"<b>Дуудаж буй функц дотроо давталттай юу?</b> {c('x in list')}, {c('sort()')}, "
        f"зүсэлт, {c('insert(0, x)')}.",
        "<b>Шинэ бүтэц үүсгэж байна уу, рекурс хэр гүн очих вэ?</b> → санах ойн төвөгшил.",
    ])
    s.append(P("Санаж үлдэх зүйлс", st_h2))
    s += bullets([
        "Big O бол <b>өсөлтийн хэлбэр</b>, секунд биш.",
        "Тогтмол коэффициент, жижиг гишүүнийг <b>хаяна</b>.",
        "Дараалсан хэсгийг <b>нэмнэ</b>, үүрлэсэн хэсгийг <b>үржүүлнэ</b>.",
        "«n 2 дахин томорвол юу болох вэ?» гэсэн <b>2 дахин тест</b> бол хамгийн хүчтэй зөн совин.",
        "Хайлт олон бол <b>set/dict</b>; эрэмбэлэгдсэн өгөгдөл бол <b>binary search</b>.",
        "Хурд ба санах ой хоёрын хооронд ихэвчлэн <b>солилцоо</b> бий.",
    ])

    doc = LessonDoc(OUT, title="Big O — зөн совин",
                    subject="Цаг ба санах ойн төвөгшил, өсөлтийн харьцуулалт",
                    leftMargin=MARGIN_X, rightMargin=MARGIN_X)
    doc.build(s)
    print("Бэлэн:", OUT)
    print(f"list@1M: {t_list[-1]:.3f} ms, set@1M: {t_set[-1] * 1000:.4f} us, "
          f"fib30 naive {fib_slow:.3f}s memo {fib_fast * 1e6:.1f}us")


if __name__ == "__main__":
    build()
