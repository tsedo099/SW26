"""
Эрэмбэлэлт: гурван тусдаа хичээлийн PDF үүсгэгч (түвшин: ойлголт + нэг хэрэгжүүлэлт).

Ажиллуулах:  python erembelelt_pdf.py
Шаардлага:   pip install reportlab matplotlib
Гаралт:      Erembelelt_1_Selection_sort.pdf, Erembelelt_2_Insertion_sort.pdf,
             Erembelelt_3_Merge_sort.pdf (энэ файлтай нэг хавтсанд)
"""

import contextlib
import io
import keyword
import math
import os
import random
import re
import sys
import textwrap
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.fonts import addMapping
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

# Консол UTF-8 биш бол монгол үсэг хэвлэхэд унахгүй
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_SELECTION = os.path.join(HERE, "Erembelelt_1_Selection_sort.pdf")
OUT_INSERTION = os.path.join(HERE, "Erembelelt_2_Insertion_sort.pdf")
OUT_MERGE = os.path.join(HERE, "Erembelelt_3_Merge_sort.pdf")

LEVEL = "Ойлголт + хэрэгжүүлэлт"

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
# Өнгө (Big O, Хайлт хичээлүүдтэй ижил палитр)
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
HEAD_BG = "#f0efec"
OK_ROW = "#e6f3ea"
MISS_ROW = "#fdf0e3"

# Big O хичээлийн ангиллын өнгө: O(n) = ногоон, O(n log n) = шар, O(n²) = ягаан
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
C_SEL = SERIES[4]      # selection sort — O(n²)
C_INS = SERIES[0]      # insertion sort
C_MERGE = SERIES[3]    # merge sort — O(n log n)
C_PY = SERIES[5]       # Python sorted()
C_IN_SORTED = SERIES[2]   # эрэмбэлэгдсэн оролт — O(n)
C_IN_RANDOM = SERIES[0]
C_IN_REV = SERIES[4]      # урвуу оролт — O(n²)

# Зургийн нүднүүд
BOX_ACTIVE = "#d6e6fa"   # эрэмбэлэгдээгүй хэсэг
BOX_OFF = "#f0efec"      # ашиглагдсан / хаягдсан
BOX_MID = ACCENT_DARK    # одоо анхаарч буй элемент (min, key)
BOX_FOUND = "#008300"    # эцсийн үр дүн
SORTED_BG = "#d4ecdc"    # эрэмбэлэгдсэн хэсэг
SORTED_INK = "#0f6b37"
SHIFT_BG = "#fde3cf"     # дөнгөж шилжсэн
C_ARROW = "#eb6834"      # солих / оруулах сум

# Буруу / зөв кодын хайрцаг
BAD_BG, BAD_INK = "#fbeeec", "#b3261e"
GOOD_BG, GOOD_INK = "#ebf6ef", "#0f7a3d"

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
st_body_k = ParagraphStyle("bodyK", parent=st_body, keepWithNext=1)
st_h1 = ParagraphStyle("H1", fontName="Arial-Bold", fontSize=20, leading=25,
                       textColor=HexColor(INK), spaceBefore=18, spaceAfter=10,
                       keepWithNext=1)
st_h2 = ParagraphStyle("H2", fontName="Arial-Bold", fontSize=13, leading=17,
                       textColor=HexColor(INK), spaceBefore=12, spaceAfter=5,
                       keepWithNext=1)
st_bullet = ParagraphStyle("bullet", parent=st_body, leftIndent=16,
                           bulletIndent=4, spaceAfter=3)
st_step = ParagraphStyle("step", parent=st_body, leftIndent=0, spaceAfter=3,
                         keepWithNext=1)
st_caption = ParagraphStyle("caption", fontName="Arial", fontSize=8.5,
                            leading=12, textColor=HexColor(TEXT2),
                            spaceBefore=3, spaceAfter=12)
st_small = ParagraphStyle("small", fontName="Arial", fontSize=8.5, leading=12,
                          textColor=HexColor(TEXT2))
st_formula = ParagraphStyle("formula", parent=st_body, alignment=TA_CENTER,
                            fontSize=12, leading=18, spaceBefore=4, spaceAfter=10)
st_cell = ParagraphStyle("cell", fontName="Arial", fontSize=9.3, leading=12.5,
                         textColor=HexColor(INK))
st_cell_b = ParagraphStyle("cellb", parent=st_cell, fontName="Arial-Bold")
st_cell_h = ParagraphStyle("cellh", parent=st_cell, fontName="Arial-Bold",
                           textColor=HexColor(TEXT2), fontSize=8.8)
st_cell_c = ParagraphStyle("cellc", parent=st_cell, alignment=TA_CENTER)
st_cell_hc = ParagraphStyle("cellhc", parent=st_cell_h, alignment=TA_CENTER)
st_code = ParagraphStyle("code", fontName="Consolas", fontSize=8.8, leading=12.2,
                         textColor=HexColor(INK))
st_callout_t = ParagraphStyle("calloutT", fontName="Arial-Bold", fontSize=10,
                              leading=14, textColor=HexColor(ACCENT_DARK),
                              spaceAfter=2)
st_callout = ParagraphStyle("callout", parent=st_body, spaceAfter=0)
st_card_head = ParagraphStyle("cardHead", fontName="Arial-Bold", fontSize=12.5,
                              leading=16, textColor=HexColor(INK), spaceAfter=0)
st_tag = ParagraphStyle("tag", fontName="Arial-Bold", fontSize=8.5, leading=11)


def P(text, style=st_body):
    # «:»-ээр төгссөн догол мөр дараагийн блоктойгоо нэг хуудсанд үлдэнэ
    if style is st_body and text.rstrip().endswith(":"):
        style = st_body_k
    return Paragraph(text, style)


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def c(code):
    """Мөр доторх код."""
    return f'<font face="Consolas" color="{ACCENT_DARK}">{_esc(str(code))}</font>'


def bullets(items, style=st_bullet):
    return [Paragraph(t, style, bulletText="•") for t in items]


def numbered(items):
    return [Paragraph(t, st_bullet, bulletText=f"{i}.") for i, t in enumerate(items, 1)]


def fmt(v):
    return f"{v:,.0f}".replace(",", " ")


def human_ms(ms):
    """Миллисекундийг уншихад хялбар нэгж рүү."""
    if ms < 1:
        return f"{ms * 1000:.0f} мкс"
    if ms < 10:
        return f"{ms:.1f} мс"
    if ms < 1000:
        return f"{ms:.0f} мс"
    s = ms / 1000
    if s < 60:
        return f"{s:.1f} сек"
    if s < 3600:
        return f"{s / 60:.0f} мин"
    if s < 86400:
        return f"{s / 3600:.1f} цаг"
    return f"{s / 86400:.1f} хоног"


# ----------------------------------------------------------------------------
# Python кодын тодруулга
# ----------------------------------------------------------------------------
BUILTINS = {"print", "len", "range", "enumerate", "sorted", "list", "random",
            "reversed", "min", "max", "open", "int", "str"}
TOKEN = re.compile(
    r"(?P<com>#.*)"
    r"|(?P<doc>\"\"\"[^\n]*?\"\"\")"
    r"|(?P<str>f?\"[^\"\n]*\"|f?'[^'\n]*')"
    r"|(?P<num>\b\d[\d_]*(?:\.\d+)?\b)"
    r"|(?P<word>\b[A-Za-z_]\w*\b)"
)


def highlight(src):
    out, pos = [], 0
    for m in TOKEN.finditer(src):
        out.append(_esc(src[pos:m.start()]))
        pos = m.end()
        kind, text = m.lastgroup, _esc(m.group())
        if kind == "com":
            out.append(f'<font color="{C_COM}"><i>{text}</i></font>')
        elif kind in ("str", "doc"):
            out.append(f'<font color="{C_STR}">{text}</font>')
        elif kind == "num":
            out.append(f'<font color="{C_NUM}">{text}</font>')
        elif kind == "word" and m.group() in keyword.kwlist:
            out.append(f'<font color="{C_KW}"><b>{text}</b></font>')
        elif kind == "word" and m.group() in BUILTINS:
            out.append(f'<font color="{C_BUILTIN}">{text}</font>')
        else:
            out.append(text)
    out.append(_esc(src[pos:]))
    return "".join(out)


def code_block(src, width=CW, bg=CODE_BG, border=RULE, after=0, plain=False):
    src = textwrap.dedent(src).strip("\n")
    body = _esc(src) if plain else highlight(src)
    t = Table([[XPreformatted(body, st_code)]], colWidths=[width], spaceAfter=after)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(bg)),
        ("BOX", (0, 0), (-1, -1), 0.6, HexColor(border)),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    return t


def code(src, after=10):
    return code_block(src, after=after)


def callout(title, text, color=ACCENT, bg=CALLOUT_BG, title_color=ACCENT_DARK):
    ts = ParagraphStyle("ct", parent=st_callout_t, textColor=HexColor(title_color))
    content = [Paragraph(title, ts)]
    for t in ([text] if isinstance(text, str) else text):
        content.append(Paragraph(t, st_callout) if isinstance(t, str) else t)
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


def warn(title, text):
    return callout(title, text, color="#eb6834", bg=WARN_BG, title_color="#a8431a")


def data_table(rows, col_widths, header=True, zebra=False, center_cols=(),
               row_bg=None):
    """rows: жагсаалтын жагсаалт (str эсвэл Flowable).
    row_bg: {мөрийн дугаар: өнгө} — тодруулах мөрүүд."""
    body = []
    for r_i, row in enumerate(rows):
        cells = []
        for c_i, v in enumerate(row):
            if not isinstance(v, str):
                cells.append(v)
            elif header and r_i == 0:
                cells.append(Paragraph(v, st_cell_hc if c_i in center_cols else st_cell_h))
            elif c_i in center_cols:
                cells.append(Paragraph(v, st_cell_c))
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
            ("BACKGROUND", (0, 0), (-1, 0), HexColor(HEAD_BG)),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, HexColor("#cfcec8")),
        ]
    if zebra:
        for i in range(1 if header else 0, len(rows)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), HexColor("#f8f8f6")))
    for i, color in (row_bg or {}).items():
        style.append(("BACKGROUND", (0, i), (-1, i), HexColor(color)))
    t.setStyle(TableStyle(style))
    return t


def tag(text, color):
    return Paragraph(f'<font color="{color}">{text}</font>', st_tag)


def swatch(color, text):
    return f'<font color="{color}">■</font>&nbsp;{text}'


def section(num, title, need=170):
    return [
        CondPageBreak(need),
        Paragraph(f'<font color="{ACCENT}">{num:02d}</font>&nbsp;&nbsp;{title}', st_h1),
    ]


def step(num, text):
    """«Алхам N» гэсэн шошготой мөр."""
    return Paragraph(f'<font color="{ACCENT}"><b>Алхам {num}.</b></font>&nbsp; {text}', st_step)


def image_from_fig(fig, width=CW):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=250, facecolor=SURFACE)
    plt.close(fig)
    buf.seek(0)
    w_in, h_in = fig.get_size_inches()
    return Image(buf, width=width, height=width * h_in / w_in)


def figure(img, caption, head=None):
    parts = [P(head, st_h2)] if head else []
    return KeepTogether(parts + [img, P(caption, st_caption)])


def lst(a):
    """Жагсаалтыг мөр доторх код болгоно."""
    return c(str(list(a)))


# ----------------------------------------------------------------------------
# Хичээлд гарах алгоритмууд (PDF-д харуулсан кодтой яг ижил)
# ----------------------------------------------------------------------------
def selection_sort(items):
    n = len(items)
    for i in range(n - 1):
        min_i = i
        for j in range(i + 1, n):
            if items[j] < items[min_i]:
                min_i = j
        items[i], items[min_i] = items[min_i], items[i]


def bubble_sort(items):
    n = len(items)
    for i in range(n - 1):
        for j in range(n - 1 - i):
            if items[j] > items[j + 1]:
                items[j], items[j + 1] = items[j + 1], items[j]


def insertion_sort(items):
    for i in range(1, len(items)):
        key = items[i]
        j = i - 1
        while j >= 0 and items[j] > key:
            items[j + 1] = items[j]
            j -= 1
        items[j + 1] = key


def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


def merge_sort(items):
    if len(items) <= 1:
        return items[:]
    mid = len(items) // 2
    left = merge_sort(items[:mid])
    right = merge_sort(items[mid:])
    return merge(left, right)


def merge_sort_traced(items, depth=0):
    pad = "    " * depth
    print(pad + f"merge_sort({items})")
    if len(items) <= 1:
        return items[:]
    mid = len(items) // 2
    left = merge_sort_traced(items[:mid], depth + 1)
    right = merge_sort_traced(items[mid:], depth + 1)
    result = merge(left, right)
    print(pad + f"merge → {result}")
    return result


# Тогтвортой байдлыг харуулах: (нэр, оноо) хосыг зөвхөн оноогоор нь эрэмбэлнэ
def selection_sort_by_score(items):
    n = len(items)
    for i in range(n - 1):
        min_i = i
        for j in range(i + 1, n):
            if items[j][1] < items[min_i][1]:
                min_i = j
        items[i], items[min_i] = items[min_i], items[i]


def insertion_sort_by_score(items, ge=False):
    for i in range(1, len(items)):
        key = items[i]
        j = i - 1
        while j >= 0 and (items[j][1] >= key[1] if ge else items[j][1] > key[1]):
            items[j + 1] = items[j]
            j -= 1
        items[j + 1] = key


# --- Дасгалын хариу ----------------------------------------------------------
def selection_sort_desc(items):
    n = len(items)
    for i in range(n - 1):
        max_i = i
        for j in range(i + 1, n):
            if items[j] > items[max_i]:
                max_i = j
        items[i], items[max_i] = items[max_i], items[i]


def smallest_k(items, k):
    a = items[:]
    n = len(a)
    for i in range(k):
        min_i = i
        for j in range(i + 1, n):
            if a[j] < a[min_i]:
                min_i = j
        a[i], a[min_i] = a[min_i], a[i]
    return a[:k]


def insertion_sort_desc(items):
    for i in range(1, len(items)):
        key = items[i]
        j = i - 1
        while j >= 0 and items[j] < key:
            items[j + 1] = items[j]
            j -= 1
        items[j + 1] = key


def insert_sorted(items, x):
    items.append(x)
    j = len(items) - 2
    while j >= 0 and items[j] > x:
        items[j + 1] = items[j]
        j -= 1
    items[j + 1] = x


def merge_desc(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] >= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


def merge_sort_desc(items):
    if len(items) <= 1:
        return items[:]
    mid = len(items) // 2
    return merge_desc(merge_sort_desc(items[:mid]), merge_sort_desc(items[mid:]))


def common(a, b):
    result = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            result.append(a[i])
            i += 1
            j += 1
        elif a[i] < b[j]:
            i += 1
        else:
            j += 1
    return result


MN = "абвгдеёжзийклмноөпрстуүфхцчшщъыьэюя"


def mn_key(word):
    return [MN.find(ch) for ch in word.lower()]


# --- Алдаатай хувилбарууд (тестээр илрүүлэхэд) --------------------------------
class Hang(Exception):
    pass


def sel_bug_min0(items):                       # min_i = 0
    n = len(items)
    for i in range(n - 1):
        min_i = 0
        for j in range(i + 1, n):
            if items[j] < items[min_i]:
                min_i = j
        items[i], items[min_i] = items[min_i], items[i]


def sel_bug_cmp_i(items):                      # items[i]-тэй харьцуулах
    n = len(items)
    for i in range(n - 1):
        min_i = i
        for j in range(i + 1, n):
            if items[j] < items[i]:
                min_i = j
        items[i], items[min_i] = items[min_i], items[i]


def sel_bug_inner_range(items):                # range(i + 1, n - 1) — дасгал
    n = len(items)
    for i in range(n - 1):
        min_i = i
        for j in range(i + 1, n - 1):
            if items[j] < items[min_i]:
                min_i = j
        items[i], items[min_i] = items[min_i], items[i]


def ins_bug_no_key(items):                     # key хадгалаагүй
    for i in range(1, len(items)):
        j = i - 1
        while j >= 0 and items[j] > items[i]:
            items[j + 1] = items[j]
            j -= 1
        items[j + 1] = items[i]


def ins_bug_j(items):                          # items[j] = key
    for i in range(1, len(items)):
        key = items[i]
        j = i - 1
        while j >= 0 and items[j] > key:
            items[j + 1] = items[j]
            j -= 1
        items[j] = key


def ins_bug_if(items):                         # while-ийн оронд if
    for i in range(1, len(items)):
        key = items[i]
        j = i - 1
        if j >= 0 and items[j] > key:
            items[j + 1] = items[j]
            j -= 1
        items[j + 1] = key


def merge_no_rest(left, right):                # үлдэгдлийг мартсан
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    return result


def ms_bug_rest(items):
    if len(items) <= 1:
        return items[:]
    mid = len(items) // 2
    return merge_no_rest(ms_bug_rest(items[:mid]), ms_bug_rest(items[mid:]))


def ms_bug_base(items):                        # if len(items) == 0
    if len(items) == 0:
        return []
    mid = len(items) // 2
    left = ms_bug_base(items[:mid])
    right = ms_bug_base(items[mid:])
    return merge(left, right)


def ms_bug_ignore(items):                      # буцаасан утгыг хаясан
    if len(items) <= 1:
        return items[:]
    mid = len(items) // 2
    left, right = items[:mid], items[mid:]
    ms_bug_ignore(left)
    ms_bug_ignore(right)
    return merge(left, right)


def run_inplace(fn, items):
    a = list(items)
    fn(a)
    return a


# ----------------------------------------------------------------------------
# Тоолуур (харьцуулалт, солилт, шилжилт)
# ----------------------------------------------------------------------------
def selection_counts(items):
    a = list(items)
    n = len(a)
    comps = swaps = 0
    for i in range(n - 1):
        min_i = i
        for j in range(i + 1, n):
            comps += 1
            if a[j] < a[min_i]:
                min_i = j
        if min_i != i:
            swaps += 1
        a[i], a[min_i] = a[min_i], a[i]
    return comps, swaps


def bubble_counts(items):
    a = list(items)
    n = len(a)
    comps = swaps = 0
    for i in range(n - 1):
        for j in range(n - 1 - i):
            comps += 1
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                swaps += 1
    return comps, swaps


def insertion_counts(items):
    a = list(items)
    comps = shifts = 0
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0:
            comps += 1
            if a[j] > key:
                a[j + 1] = a[j]
                j -= 1
                shifts += 1
            else:
                break
        a[j + 1] = key
    return comps, shifts


def merge_count(left, right):
    result, comps = [], 0
    i = j = 0
    while i < len(left) and j < len(right):
        comps += 1
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result, comps


def merge_sort_comparisons(items):
    if len(items) <= 1:
        return items[:], 0
    mid = len(items) // 2
    left, cl = merge_sort_comparisons(items[:mid])
    right, cr = merge_sort_comparisons(items[mid:])
    result, cm = merge_count(left, right)
    return result, cl + cr + cm


def inversions(items):
    n = len(items)
    return sum(1 for i in range(n) for j in range(i + 1, n) if items[i] > items[j])


# ----------------------------------------------------------------------------
# Мөрдөлт (хүснэгт, зурагт)
# ----------------------------------------------------------------------------
def selection_trace(vals):
    """[(i, өмнөх төлөв, min_i, дараах төлөв, харьцуулалт)]"""
    a = list(vals)
    n = len(a)
    rows = []
    for i in range(n - 1):
        before = list(a)
        min_i = i
        for j in range(i + 1, n):
            if a[j] < a[min_i]:
                min_i = j
        a[i], a[min_i] = a[min_i], a[i]
        rows.append((i, before, min_i, list(a), n - 1 - i))
    return rows


def selection_inner(state, i):
    """Нэг эргэлтийн дотоод давталт: [(j, items[j], items[min_i], бага уу, шинэ min_i)]"""
    min_i = i
    rows = []
    for j in range(i + 1, len(state)):
        less = state[j] < state[min_i]
        rows.append((j, state[j], state[min_i], less, j if less else min_i))
        if less:
            min_i = j
    return rows, min_i


def insertion_trace(vals):
    """[(i, key, өмнөх төлөв, байр, шилжилт, харьцуулалт, дараах төлөв)]"""
    a = list(vals)
    rows = []
    for i in range(1, len(a)):
        before = list(a)
        key = a[i]
        j = i - 1
        shifts = comps = 0
        while j >= 0:
            comps += 1
            if a[j] > key:
                a[j + 1] = a[j]
                j -= 1
                shifts += 1
            else:
                break
        a[j + 1] = key
        rows.append((i, key, before, j + 1, shifts, comps, list(a)))
    return rows


def insertion_inner(vals, i):
    """i-р эргэлтийн while давталт (жинхэнэ жагсаалтын төлөвтэй)."""
    a = list(vals)
    key = a[i]
    j = i - 1
    rows = []
    while j >= 0:
        if a[j] > key:
            a[j + 1] = a[j]
            rows.append((j, a[j], True, f"items[{j + 1}] = {a[j]}", list(a)))
            j -= 1
        else:
            rows.append((j, a[j], False, "давталт зогсоно", list(a)))
            break
    a[j + 1] = key
    return rows, j + 1, a


def merge_steps(left, right):
    """[(i, j, сонгосон тал, утга, result)] + үлдэгдэл."""
    result, steps = [], []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            steps.append((i, j, "L", left[i]))
            result.append(left[i])
            i += 1
        else:
            steps.append((i, j, "R", right[j]))
            result.append(right[j])
            j += 1
    return steps, i, j


# ----------------------------------------------------------------------------
# Шалгалт ба хэмжилт (бодитоор ажиллуулна)
# ----------------------------------------------------------------------------
STUDENTS = [("Бат", 85), ("Дорж", 85), ("Сараа", 70)]
PAIRS_EX = [("Ану", 3), ("Бат", 1), ("Цэцэг", 3), ("Дорж", 1)]
WORDS = ["үзэм", "тоор", "өвс", "алим"]


def self_check():
    """PDF-д бичсэн бүх үр дүнг энд баталгаажуулна."""
    v = [29, 10, 14, 37, 13]
    assert run_inplace(selection_sort, v) == [10, 13, 14, 29, 37]
    assert run_inplace(insertion_sort, v) == [10, 13, 14, 29, 37]
    assert merge_sort([38, 27, 43, 3, 9, 82, 10, 15]) == [3, 9, 10, 15, 27, 38, 43, 82]
    nums = [5, 2, 9, 1, 7]
    assert sorted(nums) == [1, 2, 5, 7, 9] and nums.sort() is None and nums == [1, 2, 5, 7, 9]
    # Selection: мөрдөлт
    tr = selection_trace(v)
    assert [r[2] for r in tr] == [1, 4, 2, 4] and sum(r[4] for r in tr) == 10
    assert selection_counts(v) == (10, 3)
    inner, m = selection_inner([10, 29, 14, 37, 13], 1)
    assert m == 4 and [r[4] for r in inner] == [2, 2, 4]
    # Selection: алдаа
    assert run_inplace(sel_bug_min0, [3, 1, 2]) == [3, 1, 2]
    assert run_inplace(sel_bug_cmp_i, [5, 3, 1, 4]) == [4, 1, 3, 5]
    assert run_inplace(sel_bug_inner_range, [3, 2, 1]) == [2, 3, 1]
    for n in (10, 100):
        assert selection_counts(list(range(n)))[0] == n * (n - 1) // 2
    # Selection: дасгал
    assert run_inplace(selection_sort, [5, 1, 4, 2, 3]) == [1, 2, 3, 4, 5]
    assert selection_counts([5, 1, 4, 2, 3]) == (10, 4)
    assert run_inplace(selection_sort_desc, [3, 8, 1, 9, 4]) == [9, 8, 4, 3, 1]
    assert selection_counts(list(range(6)))[0] == 15
    assert smallest_k([29, 10, 14, 37, 13], 2) == [10, 13]
    # Insertion: мөрдөлт
    it = insertion_trace(v)
    assert [r[4] for r in it] == [1, 1, 0, 3] and sum(r[5] for r in it) == 8
    assert insertion_counts(v) == (8, 5) and inversions(v) == 5
    rows, pos, after = insertion_inner([10, 14, 29, 37, 13], 4)
    assert pos == 1 and after == [10, 13, 14, 29, 37]
    assert rows[0][4] == [10, 14, 29, 37, 37] and rows[2][4] == [10, 14, 14, 29, 37]
    # Insertion: алдаа
    assert run_inplace(ins_bug_no_key, [29, 10, 14]) == [29, 29, 29]
    assert run_inplace(ins_bug_j, [29, 10, 14]) == [29, 29, 10]
    assert run_inplace(ins_bug_if, [3, 2, 1]) == [2, 1, 3]
    # Insertion: тоолол
    assert insertion_counts(list(range(1000))) == (999, 0)
    assert insertion_counts(list(range(1000, 0, -1))) == (499500, 499500)
    # Тогтвортой байдал
    s1, s2 = list(STUDENTS), list(STUDENTS)
    selection_sort_by_score(s1)
    insertion_sort_by_score(s2)
    assert [x[0] for x in s1] == ["Сараа", "Дорж", "Бат"]
    assert [x[0] for x in s2] == ["Сараа", "Бат", "Дорж"]
    s3 = list(STUDENTS)
    insertion_sort_by_score(s3, ge=True)
    assert [x[0] for x in s3] == ["Сараа", "Дорж", "Бат"]
    # Insertion: дасгал
    assert run_inplace(insertion_sort, [4, 3, 5, 1, 2]) == [1, 2, 3, 4, 5]
    assert run_inplace(insertion_sort_desc, [3, 8, 1, 9, 4]) == [9, 8, 4, 3, 1]
    assert [insertion_counts(x)[1] for x in ([1, 2, 3, 4, 5], [5, 4, 3, 2, 1],
                                             [2, 1, 4, 3, 6, 5])] == [0, 10, 3]
    a = [10, 14, 29, 37]
    insert_sorted(a, 13)
    assert a == [10, 13, 14, 29, 37]
    b = []
    insert_sorted(b, 5)
    assert b == [5]
    # Merge
    assert merge([3, 27, 38, 43], [9, 10, 15, 82]) == [3, 9, 10, 15, 27, 38, 43, 82]
    st, i, j = merge_steps([3, 27, 38, 43], [9, 10, 15, 82])
    assert len(st) == 7 and (i, j) == (4, 3)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        merge_sort_traced([38, 27, 43, 3])
    assert out.getvalue().splitlines()[-1] == "merge → [3, 27, 38, 43]"
    nums = [38, 27, 43, 3]
    assert merge_sort(nums) == [3, 27, 38, 43] and nums == [38, 27, 43, 3]
    assert merge_no_rest([1, 5], [2, 3]) == [1, 2, 3]
    assert ms_bug_rest([38, 27, 43, 3]) == [3]
    assert ms_bug_ignore([38, 27, 43, 3]) == [38, 27, 43, 3]
    try:
        ms_bug_base([5])
        raise AssertionError("ms_bug_base RecursionError шидэх ёстой")
    except RecursionError:
        pass
    # Merge: дасгал
    assert merge_count([1, 4, 9], [2, 3, 10, 12]) == ([1, 2, 3, 4, 9, 10, 12], 5)
    assert merge_sort([5, 2, 4, 7, 1, 3, 2, 6]) == [1, 2, 2, 3, 4, 5, 6, 7]
    assert merge_sort_desc([3, 8, 1, 9, 4]) == [9, 8, 4, 3, 1]
    assert [math.ceil(math.log2(n)) for n in (16, 1000, 1_000_000)] == [4, 10, 20]
    assert common([1, 3, 4, 7, 9], [2, 3, 7, 8, 9]) == [3, 7, 9]
    # Python sorted()
    assert sorted([38, 27, 43, 3, 9], reverse=True) == [43, 38, 27, 9, 3]
    assert sorted(["банана", "алим", "үзэм", "лийр"], key=len) == ["алим", "үзэм", "лийр", "банана"]
    st_ = [("Бат", 85), ("Сараа", 92), ("Дорж", 85)]
    assert sorted(st_, key=lambda s: s[1], reverse=True) == [("Сараа", 92), ("Бат", 85), ("Дорж", 85)]
    assert sorted(WORDS) == ["алим", "тоор", "үзэм", "өвс"]
    assert sorted(WORDS, key=mn_key) == ["алим", "өвс", "тоор", "үзэм"]


def test_edges():
    for items in ([], [5], [1, 2, 3], [3, 2, 1], [7, 7, 7], [2, 1, 2, 1]):
        for fn in (selection_sort, insertion_sort, bubble_sort):
            assert run_inplace(fn, items) == sorted(items), (fn.__name__, items)
        assert merge_sort(items) == sorted(items)


def sort_cases(trials, seed=2026):
    rnd = random.Random(seed)
    return [[rnd.randint(0, 9) for _ in range(rnd.randint(0, 12))] for _ in range(trials)]


def run_random_tests(trials=10_000):
    for items in sort_cases(trials):
        expected = sorted(items)
        assert run_inplace(selection_sort, items) == expected, items
        assert run_inplace(insertion_sort, items) == expected, items
        assert run_inplace(bubble_sort, items) == expected, items
        original = items[:]
        assert merge_sort(items) == expected and items == original, items
    # Тогтвортой байдал: оноо давхардсан (оноо, анхны байр) хосууд
    rnd = random.Random(7)
    for _ in range(2000):
        pairs = [(f"x{k}", rnd.randint(0, 3)) for k in range(rnd.randint(0, 10))]
        a = list(pairs)
        insertion_sort_by_score(a)
        assert a == sorted(pairs, key=lambda p: p[1])
    return trials


def bug_report(fns, inplace=True, trials=1000):
    """Алдаатай хувилбар бүр санамсаргүй тестийн хэдэд нь бүтэлгүйтэхийг тоолж,
    бүтэлгүйтсэн хамгийн богино жишээг хадгална."""
    cases = sort_cases(trials, seed=99)
    out = []
    for fn in fns:
        failed, best, kinds = 0, None, set()
        for items in cases:
            a = list(items)
            try:
                res = fn(a)
                got = a if inplace else res
                if got == sorted(items):
                    continue
                kind, shown = "буруу хариу", str(got)
            except RecursionError:
                kind, shown = "RecursionError", "RecursionError"
            except IndexError:
                kind, shown = "IndexError", "IndexError"
            failed += 1
            kinds.add(kind)
            key = (len(items), items)
            if best is None or key < best[0]:
                best = (key, f"{items} → {shown}")
        out.append((failed, best[1] if best else "—", kinds))
    return out


def time_sort(fn, data, repeat=3):
    best = float("inf")
    for _ in range(repeat):
        a = list(data)
        t0 = time.perf_counter()
        fn(a)
        best = min(best, time.perf_counter() - t0)
    return best * 1000  # мс


def measure():
    rnd = random.Random(2026)

    def rand_list(n):
        return [rnd.randint(0, 10 * n) for _ in range(n)]

    m = {}
    ns = [200 * k for k in range(1, 11)]
    m["ns"] = ns
    print("  selection / insertion, n = 200 … 2000")
    data = {n: rand_list(n) for n in ns}
    m["sel"] = [time_sort(selection_sort, data[n]) for n in ns]
    m["ins_random"] = [time_sort(insertion_sort, data[n]) for n in ns]
    m["ins_sorted"] = [time_sort(insertion_sort, list(range(n)), 5) for n in ns]
    m["ins_rev"] = [time_sort(insertion_sort, list(range(n, 0, -1))) for n in ns]
    n = ns[-1]
    m["sel_sorted_2000"] = time_sort(selection_sort, list(range(n)))
    m["sel_rev_2000"] = time_sort(selection_sort, list(range(n, 0, -1)))

    ns3 = [1000 * k for k in range(1, 6)]
    m["ns3"] = ns3
    print("  гурван алгоритм, n = 1000 … 5000")
    data3 = {n: rand_list(n) for n in ns3}
    m["c_sel"] = [time_sort(selection_sort, data3[n], 2) for n in ns3]
    m["c_ins"] = [time_sort(insertion_sort, data3[n], 2) for n in ns3]
    m["c_merge"] = [time_sort(merge_sort, data3[n], 5) for n in ns3]
    m["c_py"] = [time_sort(sorted, data3[n], 20) for n in ns3]

    print("  merge_sort / sorted(), n = 100 000, 1 000 000")
    big = {}
    for n, rep in ((100_000, 3), (1_000_000, 1)):
        d = rand_list(n)
        big[n] = (time_sort(merge_sort, d, rep), time_sort(sorted, d, 3))
    m["big"] = big
    d = list(range(1_000_000))
    m["py_presorted_1m"] = time_sort(sorted, d, 3)

    # Тоолол (хугацаанаас хамааралгүй)
    r1000 = rand_list(1000)
    m["sel_counts"] = {"sorted": selection_counts(list(range(1000))),
                       "random": selection_counts(r1000),
                       "rev": selection_counts(list(range(1000, 0, -1)))}
    m["bub_counts_random"] = bubble_counts(r1000)
    near = list(range(1000))
    for _ in range(10):
        i = rnd.randrange(0, 990)
        k = rnd.randint(1, 9)
        near[i], near[i + k] = near[i + k], near[i]
    m["ins_counts"] = {"sorted": insertion_counts(list(range(1000))),
                       "near": insertion_counts(near),
                       "random": insertion_counts(r1000),
                       "rev": insertion_counts(list(range(1000, 0, -1)))}
    m["merge_cmp_1000"] = merge_sort_comparisons(r1000)[1]
    m["sel_cmp_1000"] = selection_counts(r1000)[0]
    return m


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

UNIT_IN = 0.268  # нэг нүдний өргөн (инч) — бүх зурагт ижил хэмжээтэй харагдуулна


def _box(ax, x, y, val, fc, tc, bold=False, dashed=False):
    if dashed:
        ax.add_patch(FancyBboxPatch((x + 0.06, y + 0.06), 0.88, 0.88,
                                    boxstyle="round,pad=0,rounding_size=0.12",
                                    fc="none", ec="#b9b8b2", lw=0.9, ls=(0, (2, 2))))
    else:
        ax.add_patch(FancyBboxPatch((x + 0.06, y + 0.06), 0.88, 0.88,
                                    boxstyle="round,pad=0,rounding_size=0.12",
                                    fc=fc, ec="none"))
    if val is not None and val != "":
        ax.text(x + 0.5, y + 0.5, str(val), ha="center", va="center", fontsize=8.5,
                color=tc, fontweight="bold" if bold else "normal")


def _fig_for(units_w, rows_h):
    fig, ax = plt.subplots(figsize=(units_w * UNIT_IN, rows_h * UNIT_IN))
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.set_axis_off()
    return fig, ax


def _index_row(ax, n):
    for i in range(n):
        ax.text(i + 0.5, 1.22, str(i), ha="center", va="center", fontsize=7.5, color=MUTED)
    ax.text(-0.3, 1.22, "индекс", ha="right", va="center", fontsize=7.5, color=MUTED)


def _arc(ax, x_from, x_to, y, both=False, rad=-0.35):
    """Нүдний доод талаар муруй сум."""
    ax.annotate("", xy=(x_to, y), xytext=(x_from, y),
                arrowprops=dict(arrowstyle="<|-|>" if both else "-|>", color=C_ARROW,
                                lw=1.2, shrinkA=0, shrinkB=0, mutation_scale=7,
                                connectionstyle=f"arc3,rad={rad}"))


def _scaled(fig, units_w):
    return image_from_fig(fig, width=CW * min(1.0, units_w * UNIT_IN / 6.7))


def chart_selection_trace(vals):
    steps = selection_trace(vals)
    n = len(vals)
    row_h = 1.8
    left, right = 2.4, 8.2
    n_rows = len(steps) + 1
    fig, ax = _fig_for(left + n + right, n_rows * row_h + 0.1)
    _index_row(ax, n)
    for r, (i, before, m, _after, _cmp) in enumerate(steps):
        y = -r * row_h
        for k, v in enumerate(before):
            if k < i:
                _box(ax, k, y, v, SORTED_BG, SORTED_INK)
            elif k == m:
                _box(ax, k, y, v, BOX_MID, "white", bold=True)
            else:
                _box(ax, k, y, v, BOX_ACTIVE, INK)
        if m != i:
            _arc(ax, m + 0.5, i + 0.5, y + 0.04, both=True)
            note = f"min = {before[m]}  → {i} ↔ {m} солино"
        else:
            note = f"min = {before[m]}  → аль хэдийн байрандаа"
        ax.text(-0.3, y + 0.5, f"i = {i}", ha="right", va="center", fontsize=8.5, color=TEXT2)
        ax.text(n + 0.35, y + 0.5, note, ha="left", va="center", fontsize=8.5, color=INK)
    y = -len(steps) * row_h
    for k, v in enumerate(steps[-1][3]):
        _box(ax, k, y, v, BOX_FOUND, "white", bold=True)
    ax.text(-0.3, y + 0.5, "Дууслаа", ha="right", va="center", fontsize=8.5, color=TEXT2)
    ax.text(n + 0.35, y + 0.5, "эрэмбэлэгдлээ", ha="left", va="center", fontsize=8.5,
            color=INK, fontweight="bold")
    ax.set_xlim(-left, n + right)
    ax.set_ylim(y - 0.1, 1.5)
    return _scaled(fig, left + n + right)


def chart_insertion_trace(vals):
    steps = insertion_trace(vals)
    n = len(vals)
    row_h = 1.8
    left, right = 2.4, 10.2
    n_rows = len(steps) + 1
    fig, ax = _fig_for(left + n + right, n_rows * row_h + 0.1)
    _index_row(ax, n)
    for r, (i, key, before, pos, shifts, _cmp, _after) in enumerate(steps):
        y = -r * row_h
        for k, v in enumerate(before):
            if k < i:
                _box(ax, k, y, v, SORTED_BG, SORTED_INK)
            elif k == i:
                _box(ax, k, y, v, BOX_MID, "white", bold=True)
            else:
                _box(ax, k, y, v, BOX_ACTIVE, INK)
        if shifts:
            _arc(ax, i + 0.5, pos + 0.5, y + 0.04)
            note = f"key = {key}: {shifts} элемент шилжинэ → {pos}-р байр"
        else:
            note = f"key = {key}: {before[i - 1]} ≤ {key} → байрандаа"
        ax.text(-0.3, y + 0.5, f"i = {i}", ha="right", va="center", fontsize=8.5, color=TEXT2)
        ax.text(n + 0.35, y + 0.5, note, ha="left", va="center", fontsize=8.5, color=INK)
    y = -len(steps) * row_h
    for k, v in enumerate(steps[-1][6]):
        _box(ax, k, y, v, BOX_FOUND, "white", bold=True)
    ax.text(-0.3, y + 0.5, "Дууслаа", ha="right", va="center", fontsize=8.5, color=TEXT2)
    ax.text(n + 0.35, y + 0.5, "эрэмбэлэгдлээ", ha="left", va="center", fontsize=8.5,
            color=INK, fontweight="bold")
    ax.set_xlim(-left, n + right)
    ax.set_ylim(y - 0.1, 1.5)
    return _scaled(fig, left + n + right)


def chart_insertion_closeup(vals, i):
    """Нэг эргэлтийг ойроос: key-г гаргаж, их элементүүдийг шилжүүлж, оруулна."""
    a = list(vals)
    key = a[i]
    disp = list(a)
    disp[i] = None
    hole = i
    rows = [(list(disp), None, f"key = items[{i}] = {key} гэж хадгална", True)]
    j = i - 1
    while j >= 0 and a[j] > key:
        disp[hole], disp[j] = disp[j], None
        rows.append((list(disp), hole, f"j = {j}: {a[j]} > {key}  → баруун тийш", True))
        a[j + 1] = a[j]
        hole = j
        j -= 1
    if j >= 0:
        last = f"j = {j}: {a[j]} > {key} худал  → items[{j + 1}] = key"
    else:
        last = f"j = −1: эхэнд хүрлээ  → items[0] = key"
    disp[hole] = key
    rows.append((list(disp), hole, last, False))

    n = len(vals)
    row_h = 1.55
    left, right = 3.0, 9.4
    fig, ax = _fig_for(left + n + right, len(rows) * row_h - 0.4)
    for r, (state, mark, note, has_key) in enumerate(rows):
        y = -r * row_h
        final = r == len(rows) - 1
        for k, v in enumerate(state):
            if v is None:
                _box(ax, k, y, "", None, None, dashed=True)
            elif final and k == mark:
                _box(ax, k, y, v, BOX_FOUND, "white", bold=True)
            elif k == mark:
                _box(ax, k, y, v, SHIFT_BG, INK, bold=True)
            else:
                _box(ax, k, y, v, SORTED_BG, SORTED_INK)
        if mark is not None and not final:
            _arc(ax, mark - 0.5, mark + 0.5, y + 0.04, rad=-0.6)
        if has_key:
            _box(ax, -1.6, y, key, BOX_MID, "white", bold=True)
            ax.text(-1.75, y + 0.5, "key", ha="right", va="center", fontsize=8.5, color=TEXT2)
        ax.text(n + 0.35, y + 0.5, note, ha="left", va="center", fontsize=8.5,
                color=INK, fontweight="bold" if final else "normal")
    ax.set_xlim(-left, n + right)
    ax.set_ylim(-(len(rows) - 1) * row_h - 0.35, 1.05)
    return _scaled(fig, left + n + right)


def chart_merge_steps(left_l, right_l):
    steps, end_i, end_j = merge_steps(left_l, right_l)
    nl, nr = len(left_l), len(right_l)
    x_r = nl + 1.0
    x_res = x_r + nr + 1.3
    total = nl + nr
    lab_w = 4.4
    width = x_res + total
    row_h = 1.45
    n_rows = len(steps) + 1
    fig, ax = _fig_for(lab_w + width + 0.2, n_rows * row_h + 0.55)
    for x, t in ((nl / 2, "left"), (x_r + nr / 2, "right"), (x_res + total / 2, "result")):
        ax.text(x, 1.3, t, ha="center", va="center", fontsize=8.5, color=TEXT2,
                family="Consolas")
    result = []
    for r, (i, j, side, val) in enumerate(steps):
        y = -r * row_h
        for k, v in enumerate(left_l):
            if k < i:
                _box(ax, k, y, v, BOX_OFF, "#b3b2ac")
            elif k == i:
                _box(ax, k, y, v, BOX_MID if side == "L" else BOX_ACTIVE,
                     "white" if side == "L" else INK, bold=True)
            else:
                _box(ax, k, y, v, BOX_ACTIVE, INK)
        for k, v in enumerate(right_l):
            if k < j:
                _box(ax, x_r + k, y, v, BOX_OFF, "#b3b2ac")
            elif k == j:
                _box(ax, x_r + k, y, v, BOX_MID if side == "R" else BOX_ACTIVE,
                     "white" if side == "R" else INK, bold=True)
            else:
                _box(ax, x_r + k, y, v, BOX_ACTIVE, INK)
        result.append(val)
        for k in range(total):
            if k < len(result) - 1:
                _box(ax, x_res + k, y, result[k], SORTED_BG, SORTED_INK)
            elif k == len(result) - 1:
                _box(ax, x_res + k, y, result[k], BOX_MID, "white", bold=True)
            else:
                _box(ax, x_res + k, y, "", None, None, dashed=True)
        a, b = left_l[i], right_l[j]
        txt = f"{a} ≤ {b} → {a}" if side == "L" else f"{a} > {b} → {b}"
        ax.text(-0.3, y + 0.5, txt, ha="right", va="center", fontsize=8.5, color=INK)
    y = -len(steps) * row_h
    rest = left_l[end_i:] + right_l[end_j:]
    for k, v in enumerate(left_l):
        _box(ax, k, y, v, BOX_OFF if k < end_i else SHIFT_BG, "#b3b2ac" if k < end_i else INK)
    for k, v in enumerate(right_l):
        _box(ax, x_r + k, y, v, BOX_OFF if k < end_j else SHIFT_BG,
             "#b3b2ac" if k < end_j else INK)
    full = result + rest
    for k, v in enumerate(full):
        _box(ax, x_res + k, y, v, BOX_FOUND, "white", bold=True)
    ax.text(-0.3, y + 0.5, f"үлдэгдэл:\n{rest} → extend", ha="right", va="center",
            fontsize=8.5, color=INK, fontweight="bold", linespacing=1.2)
    ax.set_xlim(-lab_w, width + 0.2)
    ax.set_ylim(y - 0.1, 1.6)
    return _scaled(fig, lab_w + width + 0.2)


def chart_merge_tree(vals):
    n = len(vals)
    gap = 0.6
    rows = []
    g = n
    while True:
        rows.append(("split", g, [vals[s:s + g] for s in range(0, n, g)]))
        if g == 1:
            break
        g //= 2
    g = 2
    while g <= n:
        groups = [merge_sort(vals[s:s + g]) for s in range(0, n, g)]
        rows.append(("merge", g, groups))
        g *= 2

    def center(start, size):
        return ((start * (1 + gap) + 0.5) + ((start + size - 1) * (1 + gap) + 0.5)) / 2

    width = n * (1 + gap) - gap
    left, right = 3.3, 8.2
    row_h = 1.75
    fig, ax = _fig_for(left + width + right, len(rows) * row_h - 0.6)
    for r, (kind, g, groups) in enumerate(rows):
        y = -r * row_h
        final = r == len(rows) - 1
        for gi, grp in enumerate(groups):
            x0 = center(gi * g, g) - g / 2
            for k, v in enumerate(grp):
                if final:
                    _box(ax, x0 + k, y, v, BOX_FOUND, "white", bold=True)
                elif kind == "merge" or g == 1:
                    _box(ax, x0 + k, y, v, SORTED_BG, SORTED_INK)
                else:
                    _box(ax, x0 + k, y, v, BOX_ACTIVE, INK)
        # Дараагийн мөртэй холбох шугам
        if r + 1 < len(rows):
            g2 = rows[r + 1][1]
            big, small = max(g, g2), min(g, g2)
            for s in range(0, n, small):
                parent = (s // big) * big
                ax.plot([center(s, small) if g == small else center(parent, big),
                         center(s, small) if g2 == small else center(parent, big)],
                        [y + 0.02, y - row_h + 0.98], color="#c9c8c2", lw=0.8, zorder=0)
        if kind == "split" and g > 1:
            label, note = "Хуваах", f"{g} → {g // 2} + {g // 2}"
        elif kind == "split":
            label, note = "Суурь", "1 элемент = эрэмбэлэгдсэн"
        else:
            label, note = "Нийлүүлэх", f"{len(groups)} merge · нийт {n} элемент"
        ax.text(-0.3, y + 0.5, label, ha="right", va="center", fontsize=8.5, color=TEXT2)
        ax.text(width + 0.35, y + 0.5, note, ha="left", va="center", fontsize=8.5,
                color=INK, fontweight="bold" if final else "normal")
    ax.set_xlim(-left, width + right)
    ax.set_ylim(-(len(rows) - 1) * row_h - 0.1, 1.05)
    return _scaled(fig, left + width + right)


def _end_labels(ax, x, items, min_gap):
    """Шугамын төгсгөлийн шошгууд давхцахгүй байхаар доороос дээш байрлуулна."""
    y_prev = None
    for y, text in sorted(items):
        if y_prev is not None and y - y_prev < min_gap:
            y = y_prev + min_gap
        ax.text(x, y, text, color=INK, fontsize=8.8, fontweight="bold", va="center",
                clip_on=False, linespacing=1.25)
        y_prev = y


def _line(ax, x, y, color, label=None):
    ax.plot(x, y, color=color, lw=2, marker="o", ms=5.5, mec=SURFACE, mew=1.2, label=label)


def _axes(ax, xmax, ymax, xlabel, ylabel):
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)


def chart_selection_timing(ns, t):
    """Ганц цуваа: legend шаардлагагүй, тайлбар нь нэрлэнэ."""
    fig, ax = plt.subplots(figsize=(6.7, 3.0))
    fig.subplots_adjust(left=0.09, right=0.80, top=0.94, bottom=0.17)
    _axes(ax, ns[-1] * 1.05, max(t) * 1.18, "n — элементийн тоо", "Эрэмбэлэх хугацаа (мс)")
    _line(ax, ns, t, C_SEL)
    for k in (4, 9):
        ax.annotate(f"{t[k]:.0f} мс", (ns[k], t[k]), xytext=(-8, 10),
                    textcoords="offset points", ha="right", fontsize=8.5, color=INK,
                    fontweight="bold")
    ax.text(ns[-1] * 1.07, t[-1], "selection_sort\nO(n²)", color=INK, fontsize=9,
            fontweight="bold", va="center", clip_on=False)
    return image_from_fig(fig)


def chart_insertion_inputs(ns, ts, tr, tv):
    fig, ax = plt.subplots(figsize=(6.7, 3.2))
    fig.subplots_adjust(left=0.09, right=0.76, top=0.94, bottom=0.16)
    ymax = max(tv) * 1.12
    _axes(ax, ns[-1] * 1.05, ymax, "n — элементийн тоо", "Эрэмбэлэх хугацаа (мс)")
    _line(ax, ns, tv, C_IN_REV, "урвуу")
    _line(ax, ns, tr, C_IN_RANDOM, "санамсаргүй")
    _line(ax, ns, ts, C_IN_SORTED, "эрэмбэлэгдсэн")
    _end_labels(ax, ns[-1] * 1.07, [
        (tv[-1], f"урвуу · O(n²)\n{tv[-1]:.0f} мс"),
        (tr[-1], f"санамсаргүй · O(n²)\n{tr[-1]:.0f} мс"),
        (ts[-1], f"эрэмбэлэгдсэн · O(n)\n{ts[-1]:.2f} мс"),
    ], ymax * 0.16)
    ax.legend(loc="upper left", frameon=False, fontsize=8.5)
    return image_from_fig(fig)


def chart_compare(ns, t_sel, t_ins, t_merge, t_py):
    fig, ax = plt.subplots(figsize=(6.7, 3.3))
    fig.subplots_adjust(left=0.09, right=0.76, top=0.94, bottom=0.16)
    ymax = max(t_sel + t_ins) * 1.12
    _axes(ax, ns[-1] * 1.05, ymax, "n — элементийн тоо", "Эрэмбэлэх хугацаа (мс)")
    _line(ax, ns, t_sel, C_SEL, "selection_sort")
    _line(ax, ns, t_ins, C_INS, "insertion_sort")
    _line(ax, ns, t_merge, C_MERGE, "merge_sort")
    _line(ax, ns, t_py, C_PY, "sorted()")
    _end_labels(ax, ns[-1] * 1.07, [
        (t_sel[-1], f"selection · O(n²)\n{human_ms(t_sel[-1])}"),
        (t_ins[-1], f"insertion · O(n²)\n{human_ms(t_ins[-1])}"),
        (t_merge[-1], f"merge · O(n log n)\n{human_ms(t_merge[-1])}"),
        (t_py[-1], f"sorted() · O(n log n)\n{human_ms(t_py[-1])}"),
    ], ymax * 0.15)
    ax.legend(loc="upper left", frameon=False, fontsize=8.5)
    return image_from_fig(fig)


# ----------------------------------------------------------------------------
# Хуудасны чимэглэл
# ----------------------------------------------------------------------------
BAND_H = 300
DECO_X0 = PAGE_W * 0.585
DECO_X1 = PAGE_W - 34
DECO_BASE = PAGE_H - BAND_H + 52
DECO_H = BAND_H - 118
DECO_LABEL = "#9ec5f4"
D_DIM, D_BLUE, D_GREEN = "#34445f", "#3987e5", "#3fae6e"


def _bars(canv, vals, colors, x0, x1, y0, h, vmax, gaps=()):
    """Босоо баганууд. gaps: тэр индексийн өмнө нэмэлт зай."""
    extra = 6
    cell = (x1 - x0 - extra * len(gaps)) / len(vals)
    xs = []
    x = x0
    for i, (v, col) in enumerate(zip(vals, colors)):
        if i in gaps:
            x += extra
        canv.setFillColor(HexColor(col))
        canv.roundRect(x + 1.1, y0, cell - 2.2, max(3, h * v / vmax), 1.6, stroke=0, fill=1)
        xs.append(x + cell / 2)
        x += cell
    return xs


def _deco_arc(canv, xa, xb, y, depth, both):
    canv.setStrokeColor(HexColor(DECO_LABEL))
    canv.setFillColor(HexColor(DECO_LABEL))
    canv.setLineWidth(1.2)
    k = depth * 1.33
    canv.bezier(xa, y, xa, y - k, xb, y - k, xb, y)
    for x, on in ((xb, True), (xa, both)):
        if on:
            p = canv.beginPath()
            p.moveTo(x, y)
            p.lineTo(x - 3.2, y - 6)
            p.lineTo(x + 3.2, y - 6)
            p.close()
            canv.drawPath(p, stroke=0, fill=1)


def deco_selection(canv):
    # 5 эргэлтийн дараа: зүүн тал эрэмбэлэгдсэн, баруунаас хамгийн бага (6)-г сонгож солих нь
    vals = [1, 2, 3, 4, 5, 11, 7, 14, 9, 16, 6, 13, 10, 15, 8, 12]
    cols = [D_BLUE] * 5 + [D_DIM] * 11
    cols[10] = D_GREEN
    xs = _bars(canv, vals, cols, DECO_X0, DECO_X1, DECO_BASE, DECO_H, 16)
    _deco_arc(canv, xs[10], xs[5], DECO_BASE - 4, 16, both=True)
    canv.setFillColor(HexColor(DECO_LABEL))
    canv.setFont("Arial", 8)
    canv.drawString(xs[0] - 5, DECO_BASE - 30, "эрэмбэлэгдсэн")
    canv.drawCentredString(xs[10], DECO_BASE - 30, "min")


def deco_insertion(canv):
    # Зүүн 8 нь хоорондоо эрэмбэлэгдсэн; key = 7 (ногоон) 3-р байранд орох нь
    vals = [2, 4, 5, 8, 10, 12, 13, 15, 7, 11, 3, 16, 1, 14, 6, 9]
    cols = [D_BLUE] * 8 + [D_GREEN] + [D_DIM] * 7
    xs = _bars(canv, vals, cols, DECO_X0, DECO_X1, DECO_BASE, DECO_H, 16)
    _deco_arc(canv, xs[8], (xs[2] + xs[3]) / 2, DECO_BASE - 4, 16, both=False)
    canv.setFillColor(HexColor(DECO_LABEL))
    canv.setFont("Arial", 8)
    canv.drawString(xs[0] - 5, DECO_BASE - 30, "эрэмбэлэгдсэн хэсэг")
    canv.drawCentredString(xs[8], DECO_BASE - 30, "key")


def deco_merge(canv):
    # 4 × 4 → 2 × 8 → 1 × 16: эрэмбэлэгдсэн хэсгүүд нийлсээр нэг болох нь
    perm = [11, 3, 16, 7, 1, 14, 9, 5, 12, 2, 8, 15, 6, 13, 4, 10]
    top = PAGE_H - 52
    row_h = (BAND_H - 92) / 3
    bar_h = row_h - 16
    for r, (g, col) in enumerate(((4, D_DIM), (8, D_BLUE), (16, D_GREEN))):
        vals = [x for s in range(0, 16, g) for x in sorted(perm[s:s + g])]
        y0 = top - (r + 1) * row_h + 8
        _bars(canv, vals, [col] * 16, DECO_X0, DECO_X1, y0, bar_h, 16,
              gaps=[s for s in range(g, 16, g)])
        canv.setFillColor(HexColor(DECO_LABEL))
        canv.setFont("Arial", 8)
        canv.drawRightString(DECO_X0 - 8, y0 + 2, f"{16 // g} × {g}")


def make_cover(kicker, big, sub, lines, deco):
    def draw(canv, doc):
        canv.saveState()
        canv.setFillColor(HexColor(SURFACE))
        canv.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
        top = PAGE_H
        canv.setFillColor(HexColor("#101a2b"))
        canv.rect(0, top - BAND_H, PAGE_W, BAND_H, stroke=0, fill=1)
        deco(canv)
        canv.setFillColor(HexColor("#9ec5f4"))
        canv.setFont("Arial-Bold", 10)
        canv.drawString(MARGIN_X, top - 62, kicker)
        canv.setFillColor(HexColor("#ffffff"))
        size = 58
        while MARGIN_X + pdfmetrics.stringWidth(big, "Arial-Bold", size) > DECO_X0 - 24:
            size -= 2
        canv.setFont("Arial-Bold", size)
        canv.drawString(MARGIN_X, top - 135, big)
        canv.setFont("Arial", 30)
        canv.drawString(MARGIN_X, top - 175, sub)
        canv.setFillColor(HexColor("#c3c2b7"))
        canv.setFont("Arial", 12)
        for k, line in enumerate(lines):
            canv.drawString(MARGIN_X, top - 215 - 17 * k, line)
        canv.restoreState()
    return draw


def make_page(header_left):
    def draw(canv, doc):
        canv.saveState()
        canv.setFillColor(HexColor(SURFACE))
        canv.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
        canv.setStrokeColor(HexColor(RULE))
        canv.setLineWidth(0.6)
        canv.line(MARGIN_X, PAGE_H - 14 * mm, PAGE_W - MARGIN_X, PAGE_H - 14 * mm)
        canv.setFont("Arial", 8)
        canv.setFillColor(HexColor(MUTED))
        canv.drawString(MARGIN_X, PAGE_H - 12 * mm, header_left)
        canv.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 12 * mm, f"Түвшин: {LEVEL}")
        canv.drawCentredString(PAGE_W / 2, 10 * mm, str(doc.page))
        canv.restoreState()
    return draw


class LessonDoc(BaseDocTemplate):
    def __init__(self, filename, on_cover, on_page, **kw):
        super().__init__(filename, pagesize=A4, leftMargin=MARGIN_X,
                         rightMargin=MARGIN_X, **kw)
        cover_frame = Frame(MARGIN_X, 18 * mm, CW, PAGE_H - BAND_H - 18 * mm - 26,
                            id="cover", leftPadding=0, rightPadding=0,
                            topPadding=0, bottomPadding=0)
        body_frame = Frame(MARGIN_X, 18 * mm, CW, PAGE_H - 18 * mm - 22 * mm,
                           id="body", leftPadding=0, rightPadding=0,
                           topPadding=0, bottomPadding=0)
        self.addPageTemplates([
            PageTemplate("cover", [cover_frame], onPage=on_cover),
            PageTemplate("normal", [body_frame], onPage=on_page),
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
# Тусгай блокууд
# ----------------------------------------------------------------------------
def front_page(prereq, goals, toc, summary_title, summary_lines):
    s = []
    chip_style = ParagraphStyle("chip", parent=st_cell, fontSize=9.5, alignment=TA_CENTER)
    chips = Table([[P(f"<b>Түвшин:</b> {LEVEL}", chip_style),
                    P("<b>Жишээ:</b> Python 3", chip_style),
                    P(f"<b>Урьдчилсан мэдлэг:</b> {prereq}", chip_style)]],
                  colWidths=[CW * 0.36, CW * 0.19, CW * 0.45], hAlign="LEFT")
    chips.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(HEAD_BG)),
        ("ROUNDEDCORNERS", [10, 10, 10, 10]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEAFTER", (0, 0), (1, 0), 1.5, HexColor(SURFACE)),
    ]))
    s += [chips, Spacer(1, 16)]
    s.append(P("Энэ хичээлийг уншсаны дараа та:", st_h2))
    s += bullets(goals)
    s.append(Spacer(1, 6))
    s.append(P("Агуулга", st_h2))
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
    s.append(Spacer(1, 12))
    s.append(callout(summary_title, summary_lines))
    s += [NextPageTemplate("normal"), PageBreak()]
    return s


def bug_card(num, title, wrong, right, what, why):
    """Буруу ба зөв кодыг зэрэгцүүлж, юу болохыг тайлбарлах карт."""
    inner = CW - 30
    half = (inner - 10) / 2
    pair = Table([
        [tag("БУРУУ", BAD_INK), tag("ЗӨВ", GOOD_INK)],
        [code_block(wrong, width=half, bg=BAD_BG, border="#f1d3cf"),
         code_block(right, width=half, bg=GOOD_BG, border="#cfe8d8")],
    ], colWidths=[half + 5, half + 5])
    pair.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (1, 0), (1, -1), 5),
        ("RIGHTPADDING", (0, 0), (0, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 3),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    rows = [
        [P(f'<font color="#a8431a">Алдаа {num}</font>&nbsp;&nbsp;·&nbsp;&nbsp;{title}',
           st_card_head)],
        [pair],
        [P(f"<b>Юу болох вэ:</b> {what}", st_callout)],
        [P(f"<b>Яагаад:</b> {why}", st_callout)],
    ]
    t = Table(rows, colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(CARD_BG)),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor(RULE)),
        ("LINEBEFORE", (0, 0), (0, -1), 4, HexColor("#eb6834")),
        ("LEFTPADDING", (0, 0), (-1, -1), 15),
        ("RIGHTPADDING", (0, 0), (-1, -1), 15),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 7),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 11),
    ]))
    return KeepTogether([t, Spacer(1, 12)])


def exercise_card(num, title, text, src=None):
    rows = [[P(f'<font color="{ACCENT}">Дасгал {num}</font>&nbsp;&nbsp;·&nbsp;&nbsp;{title}',
               st_card_head)],
            [P(text, st_callout)]]
    if src:
        rows.append([code_block(src, width=CW - 30)])
    t = Table(rows, colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(CARD_BG)),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor(RULE)),
        ("LINEBEFORE", (0, 0), (0, -1), 4, HexColor(ACCENT)),
        ("LEFTPADDING", (0, 0), (-1, -1), 15),
        ("RIGHTPADDING", (0, 0), (-1, -1), 15),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 11),
    ]))
    return KeepTogether([t, Spacer(1, 10)])


def bug_table(names, results, ok_name):
    rows = [["Хувилбар", "1 000 тестээс бүтэлгүйтсэн", "Хамгийн богино жишээ", "Алдааны төрөл"]]
    for name, (failed, example, kinds) in zip(names, results):
        rows.append([P(name, st_cell), f"<b>{failed}</b>", P(c(example), st_cell),
                     ", ".join(sorted(kinds))])
    rows.append([P(ok_name, st_cell), "<b>0</b>", "—", "—"])
    return data_table(rows, [CW * 0.3, CW * 0.18, CW * 0.32, CW * 0.2], center_cols=(1,),
                      row_bg={len(rows) - 1: OK_ROW})


def two_cards(left, right):
    half_w = (CW - 12) / 2
    gt = Table([[left(half_w), right(half_w)]], colWidths=[half_w + 6, half_w + 6])
    gt.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, -1), 6),
        ("LEFTPADDING", (1, 0), (1, -1), 6),
        ("RIGHTPADDING", (1, 0), (1, -1), 0),
    ]))
    return gt


def facts_card(title, color, rows):
    """Хураангуйн баруун карт: шинж — утга."""
    def build(w):
        t = data_table([[P(k, st_cell), P(v, st_cell_b)] for k, v in rows],
                       [w * 0.52, w * 0.48], header=False)
        return [P(f'<font color="{color}">■</font>&nbsp;<b>{title}</b>', st_cell_b),
                Spacer(1, 4), t]
    return build


def code_card(title, color, src):
    def build(w):
        return [P(f'<font color="{color}">■</font>&nbsp;<b>{title}</b>', st_cell_b),
                Spacer(1, 4), code_block(src, width=w)]
    return build


# ============================================================================
# ХИЧЭЭЛ 1: SELECTION SORT
# ============================================================================
def build_selection(m, n_tests):
    bugs = bug_report([sel_bug_min0, sel_bug_cmp_i])
    s = front_page(
        "list, for давталт, Linear search, Big O",
        [
            "Эрэмбэлэлт гэж юу болох, <b>яагаад</b> хэрэгтэйг ойлгоно.",
            "Selection sort-ийн санааг <b>зураг, хүснэгтээр</b> тайлбарлана.",
            "Selection sort-ийг <b>өөрөө бичиж</b>, гараар мөрдөж шалгана.",
            "Яагаад <b>O(n²)</b> болохыг харьцуулалтын тоогоор тооцож, бодит хэмжилтээр харна.",
            f"3 түгээмэл алдааг таньж, кодоо {c('sorted()')}-тэй харьцуулж <b>тестлэнэ</b>.",
        ],
        ["Эрэмбэлэлт гэж юу вэ?", "Санаа", "Код", "Гараар мөрдөх", "Түгээмэл алдаа",
         "Хэр хурдан бэ?", "Тестлэх", "Дасгал", "Хураангуй"],
        "Нэг өгүүлбэрээр",
        ["<b>Selection sort</b> (сонгон эрэмбэлэлт): эрэмбэлэгдээгүй хэсгээс хамгийн багыг "
         "<b>сонгож</b>, тэр хэсгийн эхэнд тавь; үүнийг n − 1 удаа давт."],
    )

    # ------------------------------------------------------------- 1
    s += section(1, "Эрэмбэлэлт гэж юу вэ?")
    s.append(P("Эрэмбэлэх гэдэг нь элементүүдийг тодорхой дарааллаар — ихэвчлэн <b>өсөхөөр</b> "
               "(багаас их рүү) — байрлуулах явдал. Тоо, үг, оноо, огноо… харьцуулж болох бүх зүйлийг "
               "эрэмбэлж болно:"))
    s.append(data_table([
        ["Өмнө", "Дараа", "Юугаар"],
        [P(c("[5, 2, 9, 1, 7]"), st_cell), P(c("[1, 2, 5, 7, 9]"), st_cell), "тоо, өсөхөөр"],
        [P(c("[5, 2, 9, 1, 7]"), st_cell), P(c("[9, 7, 5, 2, 1]"), st_cell), "тоо, буурахаар"],
        [P(c('["Сараа", "Бат", "Дорж"]'), st_cell), P(c('["Бат", "Дорж", "Сараа"]'), st_cell),
         "үг, цагаан толгойгоор"],
    ], [CW * 0.36, CW * 0.36, CW * 0.28]))
    s.append(Spacer(1, 6))
    s.append(P("Яагаад эрэмбэлэх вэ?", st_h2))
    s += bullets([
        "<b>Хурдан хайх.</b> Binary search зөвхөн эрэмбэлэгдсэн жагсаалт дээр ажилладаг (Хайлт 2/2). "
        "Нэг удаа эрэмбэлээд дараа нь олон удаа O(log n)-ээр хайна.",
        "<b>Хүмүүст ойлгомжтой.</b> Онооны жагсаалт, үнээр нь эрэмбэлсэн бараа, утасны дэвтэр.",
        "<b>Бусад бодлогыг хялбарчлах.</b> Хамгийн бага/их k элемент, медиан, давхардал олох — "
        "эрэмбэлсний дараа хөрш элементүүдийг харахад л хангалттай.",
    ])
    s.append(P("Python-д бэлэн байгаа", st_h2))
    s.append(code("""
        nums = [5, 2, 9, 1, 7]

        new = sorted(nums)     # ШИНЭ жагсаалт буцаана, nums өөрчлөгдөхгүй
        print(new)             # [1, 2, 5, 7, 9]

        nums.sort()            # БАЙРАНДАА эрэмбэлнэ, None буцаана
        print(nums)            # [1, 2, 5, 7, 9]
    """))
    s.append(callout("Тэгвэл яагаад өөрсдөө бичих вэ?",
                     "Ажлын кодонд бэлэн функцийг хэрэглэнэ. Харин эрэмбэлэх алгоритм бол алгоритмын "
                     "сэтгэлгээний хамгийн сайн дасгал: давталт, индекс, солих үйлдэл, Big O — бүгд нэг дор. "
                     "Энэ цувралд 3 алгоритм үзнэ: <b>Selection sort</b> (энэ хичээл), <b>Insertion sort</b>, "
                     "<b>Merge sort</b>. Эхний хоёр нь энгийн боловч O(n²), гурав дахь нь O(n log n)."))
    s.append(P(f"Бидний бичих {c('selection_sort(items)')} функц {c('list.sort()')}-ийн адил жагсаалтыг "
               f"<b>байрандаа</b> өсөхөөр эрэмбэлж, юу ч буцаахгүй."))

    # ------------------------------------------------------------- 2
    s += section(2, "Санаа", need=360)
    s.append(P("<b>Зүйрлэл:</b> биеийн тамирын багш сурагчдыг намаас өндөр рүү жагсаана. Бүгдээс хамгийн "
               "намыг нь олж 1-р байранд, үлдсэнээс хамгийн намыг нь 2-р байранд… гэж <b>сонгосоор</b> "
               "байна."))
    s.append(P("Жагсаалтыг үргэлж хоёр хэсэгтэй гэж бод:"))
    s += bullets([
        "<b>Зүүн хэсэг</b> — эрэмбэлэгдсэн, <b>эцсийн</b> байрандаа орсон элементүүд. Эхэндээ хоосон.",
        "<b>Баруун хэсэг</b> — эрэмбэлэгдээгүй. Эхэндээ бүх жагсаалт.",
    ])
    s.append(P("Эргэлт бүрт баруун хэсгээс хамгийн багыг олж (linear search шиг нэг бүрчлэн харна), "
               "баруун хэсгийн эхний элементтэй <b>байрыг нь солино</b>. Ингэснээр зүүн хэсэг нэгээр "
               "томорно."))
    s.append(figure(chart_selection_trace([29, 10, 14, 37, 13]),
                    "Зураг 1. [29, 10, 14, 37, 13]-ийг selection sort-оор эрэмбэлэх нь. Ногоон — "
                    "эрэмбэлэгдсэн хэсэг, хар хөх — олдсон хамгийн бага, цайвар хөх — эрэмбэлэгдээгүй хэсэг, "
                    "улбар шар нум — байраа солих хоёр элемент. 5 элементэд 4 эргэлт."))
    s.append(callout("Яагаад n − 1 эргэлт хангалттай вэ?",
                     "n − 1 элемент эцсийн байрандаа орсны дараа үлдсэн ганц элемент нь хамгийн их нь "
                     "байх нь гарцаагүй — түүний байр аль хэдийн зөв."))

    # ------------------------------------------------------------- 3
    s += section(3, "Код", need=330)
    s.append(step(1, f"Эрэмбэлэгдээгүй хэсгийн эхлэл {c('i')} 0-ээс n − 2 хүртэл гүйнэ: "
                     f"{c('for i in range(n - 1):')}"))
    s.append(step(2, f"Хамгийн багыг одоохондоо эхний элемент гэж үзнэ: {c('min_i = i')} — "
                     "<b>индексийг</b> нь хадгална (утгыг биш), учир нь дараа нь солих хэрэгтэй."))
    s.append(step(3, f"Үлдсэн элементүүдийг нэг бүрчлэн харж, илүү багыг олбол индексийг шинэчилнэ: "
                     f"{c('for j in range(i + 1, n):')}"))
    s.append(step(4, f"Дотоод давталт дууссаны <b>дараа</b> ганц удаа солино: "
                     f"{c('items[i], items[min_i] = items[min_i], items[i]')}"))
    s.append(Spacer(1, 6))
    s.append(code("""
        def selection_sort(items):
            n = len(items)
            for i in range(n - 1):              # 1. эрэмбэлэгдээгүй хэсгийн эхлэл
                min_i = i                       # 2. хамгийн багын ИНДЕКС
                for j in range(i + 1, n):       # 3. үлдсэнийг нэг бүрчлэн харна
                    if items[j] < items[min_i]:
                        min_i = j
                items[i], items[min_i] = items[min_i], items[i]   # 4. солино

        nums = [29, 10, 14, 37, 13]
        selection_sort(nums)        # байрандаа эрэмбэлнэ — юу ч буцаахгүй
        print(nums)                 # [10, 13, 14, 29, 37]
    """))
    s.append(P("Python-д хоёр утгыг солих", st_h2))
    s.append(P("Ихэнх хэлэнд солихын тулд түр хувьсагч хэрэгтэй. Python-д нэг мөрөөр болно: баруун тал "
               "эхлээд бүхэлдээ бодогдож, дараа нь зүүн талд оноогдоно."))
    s.append(two_cards(
        code_card("Түр хувьсагчтай (бусад хэлэнд)", MUTED, """
            tmp = a
            a = b
            b = tmp
        """),
        code_card("Python-д", ACCENT, """
            a, b = b, a
            # жагсаалтын хоёр элемент:
            items[i], items[k] = items[k], items[i]
        """)))
    s.append(Spacer(1, 8))
    s.append(callout("Linear search-тэй холбоо",
                     "3-р алхам бол «хамгийн багыг олох» linear search: үлдсэн хэсгийг эхнээс нь дуустал "
                     "харна. Тэгэхээр selection sort = «хамгийн багыг хайх»-ыг n − 1 удаа давтах."))

    # ------------------------------------------------------------- 4
    s += section(4, "Гараар мөрдөх", need=330)
    tr = selection_trace([29, 10, 14, 37, 13])
    state1 = tr[1][1]
    inner, min1 = selection_inner(state1, 1)
    s.append(P(f"Эхлээд нэг эргэлтийн дотоод давталтыг нарийвчлан мөрдье: {c('i = 1')}, жагсаалт "
               f"{lst(state1)}. {c('min_i')} нь {c('1')}-ээс (утга {state1[1]}) эхэлнэ."))
    rows = [["j", "items[j]", "items[min_i]", "items[j] &lt; items[min_i] ?", "min_i"]]
    for j, vj, vm, less, new_m in inner:
        rows.append([str(j), str(vj), str(vm), "<b>True</b>" if less else "False",
                     f"<b>{new_m}</b>" if less else str(new_m)])
    after1 = tr[1][3]
    rows.append(["—", "", "", f"<b>{c(f'items[1] ↔ items[{min1}]')}</b>", P(lst(after1), st_cell)])
    s.append(KeepTogether([data_table(rows, [CW * 0.08, CW * 0.14, CW * 0.18, CW * 0.32, CW * 0.28],
                                      center_cols=(0, 1, 2, 3, 4), row_bg={len(rows) - 1: OK_ROW})]))
    s.append(Spacer(1, 4))
    s.append(P(f"Хамгийн бага 13 нь индекс {min1}-т байжээ. Эргэлтийн төгсгөлд нэг удаа солиход "
               "зүүн хэсэг [10, 13] болж томорлоо."))
    s.append(P("Бүтэн эрэмбэлэлт", st_h2))
    rows = [["i", "Эргэлтийн өмнө", "min (индекс)", "Солих", "Эргэлтийн дараа", "Харьц."]]
    for i, before, mi, after, cmp_ in tr:
        rows.append([str(i), P(lst(before), st_cell), f"{before[mi]} ({mi})",
                     f"{i} ↔ {mi}" if mi != i else "солихгүй", P(lst(after), st_cell), str(cmp_)])
    total_cmp = sum(r[4] for r in tr)
    n_swaps = sum(1 for r in tr if r[2] != r[0])
    rows.append(["", "", "", "", "<b>Нийт</b>", f"<b>{total_cmp}</b>"])
    s.append(KeepTogether([data_table(rows, [CW * 0.06, CW * 0.27, CW * 0.14, CW * 0.13,
                                             CW * 0.27, CW * 0.13],
                                      center_cols=(0, 2, 3, 5), row_bg={len(rows) - 1: OK_ROW})]))
    s.append(Spacer(1, 4))
    s.append(P(f"Нийт харьцуулалт: 4 + 3 + 2 + 1 = <b>{total_cmp}</b>. Жинхэнэ солилт: <b>{n_swaps}</b> — "
               "i = 2 үед хамгийн бага нь аль хэдийн байрандаа байсан тул солих мөр элементийг "
               "өөртэй нь солиод юу ч өөрчлөөгүй."))
    s.append(callout("Зөвлөгөө: компьютерээр мөрдүүлэх",
                     ["Гадна давталтын төгсгөлд нэг мөр нэмбэл хүснэгтийн баруун баганыг Python өөрөө "
                      "хэвлэнэ:",
                      Spacer(1, 4),
                      code_block("""
                          items[i], items[min_i] = items[min_i], items[i]
                          print(f"i={i}  min={items[i]}  {items}")
                      """, width=CW - 28)]))

    # ------------------------------------------------------------- 5
    s += section(5, "Түгээмэл алдаа", need=300)
    s.append(P("Эхлэгчдийн хамгийн их гаргадаг 3 алдаа. Бүгдийг бодитоор ажиллуулж шалгав."))
    r1 = run_inplace(sel_bug_min0, [3, 1, 2])
    s.append(bug_card(
        1, "min_i-г 0-ээс эхлүүлэх",
        """
        for i in range(n - 1):
            min_i = 0
            ...
        """,
        """
        for i in range(n - 1):
            min_i = i
            ...
        """,
        f"{c('selection_sort([3, 1, 2])')}-ийн дараа жагсаалт {lst(r1)} — <b>огт өөрчлөгдөөгүй</b>!",
        "i = 1 үед хайлт 0-р байрнаас эхэлнэ. Тэнд аль хэдийн байрандаа орсон хамгийн бага элемент "
        "байгаа тул түүнээс бага юм олдохгүй — min_i = 0 хэвээр үлдэж, 0-р элемент i-тэй солигдоод "
        "эрэмбэлэгдсэн хэсгийг эвдэнэ. Хамгийн багыг зөвхөн <b>эрэмбэлэгдээгүй</b> хэсгээс хайна."))
    r2 = run_inplace(sel_bug_cmp_i, [5, 3, 1, 4])
    s.append(bug_card(
        2, "items[min_i]-ийн оронд items[i]-тэй харьцуулах",
        """
        for j in range(i + 1, n):
            if items[j] < items[i]:
                min_i = j
        """,
        """
        for j in range(i + 1, n):
            if items[j] < items[min_i]:
                min_i = j
        """,
        f"{c('selection_sort([5, 3, 1, 4])')} → {lst(r2)}.",
        "Энэ нь items[i]-ээс бага <b>сүүлийн</b> элементийг олдог, хамгийн багыг биш: 3, 1, 4 "
        "гурвуулаа 5-аас бага тул min_i эцэст нь 4-ийн индекс болно. Одоогийн хамгийн багатай "
        "(items[min_i]) харьцуулах ёстой."))
    s.append(bug_card(
        3, "Үр дүнг хувьсагчид оноох",
        """
        nums = selection_sort(nums)
        print(nums)
        """,
        """
        selection_sort(nums)
        print(nums)
        """,
        f"{c('None')} хэвлэгдэнэ — эрэмбэлсэн жагсаалт алга болно.",
        f"Функц байрандаа эрэмбэлээд юу ч буцаадаггүй ({c('return')}-гүй функц {c('None')} буцаана). "
        f"{c('nums.sort()')} мөн адил: {c('nums = nums.sort()')} бол түгээмэл алдаа. Шинэ жагсаалт "
        f"хэрэгтэй бол {c('sorted(nums)')}."))

    # ------------------------------------------------------------- 6
    s += section(6, "Хэр хурдан бэ?", need=330)
    s.append(P(f"Ажлыг <b>харьцуулалтын тоогоор</b> тоолъё. {c('i')}-р эргэлтэд дотоод давталт "
               f"n − 1 − i удаа харьцуулна:"))
    s.append(P("(n − 1) + (n − 2) + … + 2 + 1  =  <b>n(n − 1) / 2  ≈  n² / 2</b>", st_formula))
    s.append(data_table([
        ["n", "Харьцуулалт n(n − 1) / 2", "Солилт (хамгийн ихдээ n − 1)"],
        ["10", "45", "9"],
        ["100", "4 950", "99"],
        ["1 000", "499 500", "999"],
        ["1 000 000", "499 999 500 000  (≈ 5 · 10¹¹)", "999 999"],
    ], [CW * 0.2, CW * 0.44, CW * 0.36], center_cols=(0, 1, 2), zebra=True))
    s.append(Spacer(1, 6))
    s.append(P("Коэффициентийг хаяхад <b>O(n²)</b> (Big O хичээлийн «давталт дотор давталт» дүрэм). "
               "Анхаарах зүйл: жагсаалт аль хэдийн эрэмбэлэгдсэн байсан ч selection sort яг <b>ижил</b> "
               "тооны харьцуулалт хийнэ — хамгийн багыг олохын тулд үлдсэнийг заавал бүгдийг харах ёстой. "
               "1 000 элементтэй гурван жагсаалт дээр тоолуулсан нь:"))
    sc = m["sel_counts"]
    s.append(KeepTogether([data_table([
        ["Оролт", "Харьцуулалт", "Жинхэнэ солилт"],
        ["эрэмбэлэгдсэн", fmt(sc["sorted"][0]), fmt(sc["sorted"][1])],
        ["санамсаргүй", fmt(sc["random"][0]), fmt(sc["random"][1])],
        ["урвуу", fmt(sc["rev"][0]), fmt(sc["rev"][1])],
    ], [CW * 0.34, CW * 0.33, CW * 0.33], center_cols=(1, 2))]))
    s.append(Spacer(1, 6))
    s.append(P("Хамгийн сайн, дундаж, хамгийн муу — гурвуулаа <b>O(n²)</b>. Бодитоор хэмжиж шалгая:"))
    ns, t = m["ns"], m["sel"]
    s.append(figure(chart_selection_timing(ns, t),
                    "Зураг 2. selection_sort-ийн хугацаа, санамсаргүй жагсаалт. Энэ PDF-ийг үүсгэх үед "
                    "бодитоор хэмжсэн (3 давталтын хамгийн бага утга). Таны компьютер дээр тоо нь өөр гарах "
                    "ч хэлбэр нь ижил — шулуун биш, дээшээ <b>муруйсан</b> шугам."))
    est_1m = t[-1] * (1_000_000 / ns[-1]) ** 2
    py_1m = m["big"][1_000_000][1]
    s.append(P(f"1 000 элементэд <b>{t[4]:.0f} мс</b>, 2 000 элементэд <b>{t[9]:.0f} мс</b> — "
               f"<b>{t[9] / t[4]:.1f} дахин</b>. O(n²): n 2 дахин → ажил 2² = 4 дахин. Энэ хурдаар "
               f"1 сая элемент эрэмбэлэхэд ойролцоогоор <b>{human_ms(est_1m)}</b> шаардлагатай (тооцоолсон). "
               f"Харьцуулахад Python-ий {c('sorted()')} сая элементийг <b>{human_ms(py_1m)}</b>-д "
               "эрэмбэлэв (хэмжсэн) — яагаад гэдгийг 3/3 хичээлд үзнэ."))
    bc, scr = m["bub_counts_random"], sc["random"]
    s.append(callout("Bubble sort-ийг сонссон уу?",
                     ["Хөрш хоёр элементийг харьцуулж, буруу дараалалтай бол солино; том нь «бөмбөлөг» шиг "
                      "төгсгөл рүү хөвнө. Энэ ч бас O(n²):",
                      Spacer(1, 4),
                      code_block("""
                          def bubble_sort(items):
                              n = len(items)
                              for i in range(n - 1):
                                  for j in range(n - 1 - i):
                                      if items[j] > items[j + 1]:
                                          items[j], items[j + 1] = items[j + 1], items[j]
                      """, width=CW - 28),
                      Spacer(1, 6),
                      f"Харьцуулалтын тоо ижил ({fmt(bc[0])}), гэхдээ 1 000 элементтэй санамсаргүй "
                      f"жагсаалтад bubble sort <b>{fmt(bc[1])}</b> удаа, selection sort ердөө "
                      f"<b>{fmt(scr[1])}</b> удаа солив. Солих үйлдэл цөөн нь selection sort-ийн давуу тал."]))

    # ------------------------------------------------------------- 7
    s += section(7, "Тестлэх", need=300)
    s.append(P(f"Эрэмбэлэлтийг тестлэх хамгийн хялбар арга: Python-ий {c('sorted()')}-ийг «зөв хариу» "
               "болгож, мянга мянган санамсаргүй жагсаалт дээр харьцуулах."))
    s.append(code("""
        import random

        def test_random(trials=10_000):
            for _ in range(trials):
                items = [random.randint(0, 9)           # 0–9: давхардал их гарна
                         for _ in range(random.randint(0, 12))]
                expected = sorted(items)                # «зөв хариу»
                selection_sort(items)                   # байрандаа эрэмбэлнэ
                assert items == expected, expected
            print(trials, "санамсаргүй тест: OK")
    """))
    s.append(P("Захын тохиолдлуудыг (edge cases) тусад нь шалгана — алдаа ихэвчлэн хил дээр нуугддаг:"))
    s.append(code("""
        def test_edges():
            for items in ([], [5], [1, 2, 3], [3, 2, 1], [7, 7, 7], [2, 1, 2, 1]):
                #         хоосон, ганц, эрэмбэлэгдсэн, урвуу, бүгд ижил, давхардалтай
                expected = sorted(items)
                selection_sort(items)
                assert items == expected, expected
            print("Захын тохиолдлууд: OK")
    """))
    names = [f"Алдаа 1: {c('min_i = 0')}", f"Алдаа 2: {c('items[j] < items[i]')}"]
    s.append(KeepTogether([
        P(f"Энэ PDF-ийг үүсгэх үед зөв хувилбарыг <b>{fmt(n_tests)}</b> санамсаргүй тестээр шалгахад бүгд "
          "амжилттай давлаа. Харин 5-р бүлгийн алдаатай хувилбаруудыг ижил тестэд оруулахад:"),
        bug_table(names, bugs, f"Зөв {c('selection_sort')}"),
    ]))
    s.append(Spacer(1, 8))
    s.append(callout("Дүгнэлт",
                     f"1 000 тестээс зөв хариу өгсөн нь: алдаа 1 — <b>{1000 - bugs[0][0]}</b>, алдаа 2 — "
                     f"<b>{1000 - bugs[1][0]}</b>. Алдаатай код ч хоосон, ганц элементтэй эсвэл аз таарсан "
                     "жагсаалт дээр «зөв» ажилладаг. Тиймээс ганц хоёр жишээгээр биш, санамсаргүй олон тестээр "
                     "шалга. «Хамгийн богино жишээ» баганын жагсаалтыг гараар мөрдвөл алдаа хурдан ойлгогдоно."))

    # ------------------------------------------------------------- 8
    s += section(8, "Дасгал", need=200)
    s.append(P("Эхлээд өөрөө бодож, кодоо 7-р бүлгийн аргаар тестлээрэй. Хариуг дараагийн хуудаснаас шалга."))
    s.append(exercise_card(
        1, "Гараар мөрдөх",
        f"{c('selection_sort([5, 1, 4, 2, 3])')}: эргэлт бүрийн дараах жагсаалтыг бич. Нийт хэдэн "
        "харьцуулалт, хэдэн жинхэнэ солилт хийх вэ?"))
    s.append(exercise_card(
        2, "Буурахаар",
        f"{c('selection_sort_desc(items)')} бич: жагсаалтыг <b>буурахаар</b> эрэмбэлнэ. Кодонд хамгийн "
        "бага өөрчлөлт хэд вэ?",
        """
        nums = [3, 8, 1, 9, 4]
        selection_sort_desc(nums)
        print(nums)                # [9, 8, 4, 3, 1]
        """))
    s.append(exercise_card(
        3, "Тооцоо",
        "6 элементтэй санамсаргүй жагсаалтад selection sort хэдэн харьцуулалт хийх вэ? Жагсаалт аль "
        "хэдийн эрэмбэлэгдсэн байвал? 100 элементтэй бол?"))
    s.append(exercise_card(
        4, "Алдааг ол",
        f"Доорх код {c('[3, 2, 1]')}-ийг юу болгох вэ? Яагаад? Хэрхэн засах вэ?",
        """
        def selection_sort(items):
            n = len(items)
            for i in range(n - 1):
                min_i = i
                for j in range(i + 1, n - 1):
                    if items[j] < items[min_i]:
                        min_i = j
                items[i], items[min_i] = items[min_i], items[i]
        """))
    s.append(exercise_card(
        5, "Хамгийн бага k",
        f"{c('smallest_k(items, k)')}: хамгийн бага k элементийг өсөхөөр буцаа. Selection sort-ийн "
        "зөвхөн эхний k эргэлтийг хий; эх жагсаалтыг өөрчилж болохгүй. Цагийн төвөгшил нь хэд вэ?",
        """
        smallest_k([29, 10, 14, 37, 13], 2)    # [10, 13]
        """))

    s.append(PageBreak())
    s.append(P("Дасгалын хариу", st_h1))
    s.append(P("Бүх хариуг энэ PDF-ийг үүсгэх үед жишээн дээр нь ажиллуулж шалгасан.", st_small))
    ex = selection_trace([5, 1, 4, 2, 3])
    ex_cmp, ex_sw = selection_counts([5, 1, 4, 2, 3])
    s.append(P(f"1. Гараар мөрдөх — {ex_cmp} харьцуулалт, {ex_sw} солилт", st_h2))
    rows = [["i", "min (индекс)", "Эргэлтийн дараа"]]
    for i, before, mi, after, _ in ex:
        rows.append([str(i), f"{before[mi]} ({mi})", P(lst(after), st_cell)])
    s.append(data_table(rows, [CW * 0.12, CW * 0.28, CW * 0.6], center_cols=(0, 1)))
    s.append(Spacer(1, 4))
    s.append(P("Энэ жишээнд эргэлт бүрт жинхэнэ солилт гарсан: 4 = n − 1 — selection sort-ийн солилтын "
               "дээд хязгаар. Харьцуулалт ч мөн үргэлжийн адил n(n − 1) / 2 = 10."))
    s.append(P("2. Буурахаар — ганц тэмдэгт", st_h2))
    s.append(code("""
        def selection_sort_desc(items):
            n = len(items)
            for i in range(n - 1):
                max_i = i                           # одоо хамгийн ИХийг хайна
                for j in range(i + 1, n):
                    if items[j] > items[max_i]:     # <  →  >
                        max_i = j
                items[i], items[max_i] = items[max_i], items[i]
    """))
    s.append(P("3. Тооцоо", st_h2))
    s.append(P(f"6 · 5 / 2 = <b>15</b>. Эрэмбэлэгдсэн байсан ч мөн <b>15</b> — selection sort оролтоос "
               f"хамаарахгүй. 100 элементэд 100 · 99 / 2 = <b>4 950</b>."))
    r4 = run_inplace(sel_bug_inner_range, [3, 2, 1])
    s.append(P(f"4. Алдааг ол — {lst(r4)}", st_h2))
    s.append(P(f"{c('range(i + 1, n - 1)')} нь сүүлийн индекс n − 1-ийг хэзээ ч шалгахгүй. [3, 2, 1]-д "
               "хамгийн бага 1 нь яг сүүлд байгаа тул хэзээ ч сонгогдохгүй. Засвар: "
               f"{c('range(i + 1, n)')}. Энэ бол Хайлт 1/2-оос танил «нэгээр зөрөх» (off-by-one) алдаа."))
    s.append(P("5. Хамгийн бага k — O(k · n)", st_h2))
    s.append(code("""
        def smallest_k(items, k):
            a = items[:]                        # хуулбар: эх жагсаалт өөрчлөгдөхгүй
            n = len(a)
            for i in range(k):                  # n - 1 биш, ердөө k эргэлт
                min_i = i
                for j in range(i + 1, n):
                    if a[j] < a[min_i]:
                        min_i = j
                a[i], a[min_i] = a[min_i], a[i]
            return a[:k]
    """))
    s.append(P("k жижиг бол бүтэн эрэмбэлэхээс (O(n²)) хамаагүй хурдан. Selection sort-ийн онцлог: k эргэлтийн "
               "дараа эхний k элемент <b>эцсийн</b> байрандаа орсон байдаг.", st_small))

    # ------------------------------------------------------------- 9
    s += section(9, "Хураангуй", need=470)
    s.append(P("Загвар — цээжлэх биш, ойлгож бич", st_h2))
    s.append(two_cards(
        code_card("Selection sort", C_SEL, """
            def selection_sort(items):
                n = len(items)
                for i in range(n - 1):
                    min_i = i
                    for j in range(i + 1, n):
                        if items[j] < items[min_i]:
                            min_i = j
                    items[i], items[min_i] = \\
                        items[min_i], items[i]
        """),
        facts_card("Гол тоонууд", C_SEL, [
            ("Харьцуулалт", "n(n − 1) / 2 — үргэлж"),
            ("Солилт", "≤ n − 1"),
            ("Цаг (сайн / муу)", "O(n²) / O(n²)"),
            ("Санах ой", "O(1) — байрандаа"),
            ("Тогтвортой юу?", "Үгүй (2/3-т үзнэ)"),
        ])))
    s.append(Spacer(1, 6))
    s.append(P("Selection sort бичихдээ шалгах 4 зүйл", st_h2))
    s += numbered([
        f"{c('min_i = i')} — хайлт <b>эрэмбэлэгдээгүй</b> хэсгээс эхэлж байна уу?",
        f"{c('items[min_i]')}-тэй (одоогийн хамгийн багатай) харьцуулж байна уу?",
        f"{c('range(i + 1, n)')} — сүүлийн элементийг хамарч байна уу?",
        "Солилт дотоод давталтын <b>гадна</b>, эргэлтэд нэг удаа байна уу?",
    ])
    s.append(P("Санаж үлдэх зүйлс", st_h2))
    s += bullets([
        "Зүүн хэсэг — эрэмбэлэгдсэн, эцсийн байрандаа; баруунаас хамгийн багыг <b>сонгож</b> залгана.",
        "Цаг: үргэлж <b>O(n²)</b>; n 2 дахин → хугацаа 4 дахин. Санах ой: O(1).",
        f"{c('sort()')} ба бидний функц байрандаа эрэмбэлж {c('None')} буцаана; шинэ жагсаалт — {c('sorted()')}.",
        f"Эрэмбэлэлтийг {c('sorted()')}-тэй харьцуулсан санамсаргүй тестээр шалга.",
    ])
    s.append(callout("Дараагийн алхам: Insertion sort",
                     "Хөзөр тоглохдоо гартаа ирсэн хөзрийг эрэмбэлсэн хөзрүүдийнхээ дунд зөв байранд нь "
                     "оруулдаг. Энэ санаа аль хэдийн бараг эрэмбэлэгдсэн жагсаалтад <b>маш хурдан</b> — "
                     "«Эрэмбэлэлт 2/3: Insertion sort» хичээлийн сэдэв."))

    doc = LessonDoc(OUT_SELECTION,
                    make_cover("АЛГОРИТМЫН ҮНДЭС  ·  PYTHON  ·  ЭРЭМБЭЛЭЛТ 1/3", "Selection", "sort",
                               ["Сонгон эрэмбэлэлт: хамгийн багыг", "сонгож, урд нь тавих"],
                               deco_selection),
                    make_page("Эрэмбэлэлт 1/3 — Selection sort"),
                    title="Эрэмбэлэлт 1/3 — Selection sort",
                    subject=f"Selection sort: {LEVEL.lower()}")
    doc.build(s)
    return bugs


# ============================================================================
# ХИЧЭЭЛ 2: INSERTION SORT
# ============================================================================
def build_insertion(m, n_tests):
    bugs = bug_report([ins_bug_no_key, ins_bug_j, ins_bug_if])
    s = front_page(
        "Selection sort, while давталт, Big O",
        [
            "Insertion sort-ийн санааг <b>хөзрийн</b> жишээгээр ойлгоно.",
            "«Шилжүүлэх» алхмыг зураг, хүснэгтээр <b>мөрдөж</b>, insertion sort-ийг өөрөө бичнэ.",
            "Яагаад эрэмбэлэгдсэн жагсаалтад <b>O(n)</b>, урвуу жагсаалтад <b>O(n²)</b> болохыг тайлбарлана.",
            "<b>Тогтвортой</b> (stable) эрэмбэлэлт гэж юу болохыг мэднэ.",
            "Selection sort-тэй харьцуулж, аль нь хэзээ илүүг хэлнэ.",
        ],
        ["Санаа", "Код", "Гараар мөрдөх", "Түгээмэл алдаа ба тест", "Хэр хурдан бэ?",
         "Тогтвортой эрэмбэлэлт", "Selection sort-тэй харьцуулах", "Дасгал", "Хураангуй"],
        "Нэг өгүүлбэрээр",
        ["<b>Insertion sort</b> (оруулан эрэмбэлэлт): дараагийн элементийг ав, зүүн талын эрэмбэлэгдсэн "
         "хэсэгт түүнээс их элементүүдийг баруун тийш шилжүүлж, чөлөөлөгдсөн байранд нь <b>оруул</b>."],
    )

    # ------------------------------------------------------------- 1
    s += section(1, "Санаа")
    s.append(callout("Өмнөх хичээлээс (Эрэмбэлэлт 1/3: Selection sort)",
                     "Жагсаалтыг эрэмбэлэгдсэн (зүүн) ба эрэмбэлэгдээгүй (баруун) хэсэгт хувааж, баруунаас "
                     "хамгийн багыг сонгож зүүн хэсэгт залгадаг. Үргэлж n(n − 1)/2 харьцуулалт — O(n²). "
                     "Insertion sort ч мөн хоёр хэсэгт хуваана, гэхдээ ажлаа эсрэгээр нь хийдэг."))
    s.append(P("<b>Зүйрлэл:</b> хөзөр тоглохдоо ширээнээс хөзрөө нэг нэгээр нь авч, гартаа аль хэдийн "
               "эрэмбэлсэн хөзрүүдийнхээ дунд <b>зөв байранд нь</b> оруулдаг. Шинэ хөзрөөс том хөзрүүд "
               "баруун тийш нэг зай шилжиж зай тавьж өгнө."))
    s.append(P("Ялгааг анзаар:"))
    s += bullets([
        "<b>Selection sort:</b> баруун хэсгээс <b>аль</b> элементийг авахаа сонгоход хүч зарцуулна "
        "(хамгийн багыг хайна); зүүн хэсэгт залгах нь хялбар.",
        "<b>Insertion sort:</b> баруун хэсгийн <b>дараагийн</b> элементийг шууд авна; харин зүүн хэсэгт "
        "<b>хаана</b> оруулахаа олоход хүч зарцуулна.",
        "Тиймээс insertion sort-ийн зүүн хэсэг эрэмбэлэгдсэн ч элементүүд нь <b>эцсийн байрандаа биш</b> "
        "— дараа нь ирэх бага элемент тэднийг баруун тийш түлхэж болно.",
    ])
    s.append(figure(chart_insertion_trace([29, 10, 14, 37, 13]),
                    "Зураг 1. [29, 10, 14, 37, 13]-ийг insertion sort-оор эрэмбэлэх нь. Ногоон — "
                    "эрэмбэлэгдсэн зүүн хэсэг, хар хөх — оруулах элемент (key), цайвар хөх — хараахан "
                    "ороогүй хэсэг, улбар шар сум — key орох байр."))

    # ------------------------------------------------------------- 2
    s += section(2, "Код", need=380)
    s.append(P("Кодын гол хэсэг бол нэг эргэлт: key-г гаргаж аваад, түүнээс их элементүүдийг нэг нэгээр "
               "баруун тийш шилжүүлж, гарсан «нүх»-нд key-г тавих. Сүүлийн эргэлтийг ойроос харъя:"))
    s.append(figure(chart_insertion_closeup([10, 14, 29, 37, 13], 4),
                    "Зураг 2. Нэг эргэлтийг ойроос (i = 4, key = 13). Тасархай — чөлөөтэй «нүх», улбар "
                    "шар — дөнгөж баруун тийш шилжсэн элемент. Нүх зүүн тийш явсаар key-ийн зөв байранд "
                    "хүрнэ."))
    s.append(P("Алхам алхмаар бичье", st_h2))
    s.append(step(1, f"0-р элементийг ганцаараа «эрэмбэлэгдсэн» гэж үзээд 1-р индексээс эхэлнэ: "
                     f"{c('for i in range(1, len(items)):')}"))
    s.append(step(2, f"Оруулах элементийг <b>хадгална</b> — шилжүүлэлтэд дарагдаж алга болох тул: "
                     f"{c('key = items[i]')}"))
    s.append(step(3, f"Зүүн тийш явж, key-ээс их элемент бүрийг нэг байр баруун тийш шилжүүлнэ: "
                     f"{c('while j >= 0 and items[j] > key:')}"))
    s.append(step(4, f"Давталт зогсоход {c('j')} нь key-ээс их биш элемент дээр (эсвэл −1) байна. "
                     f"key-ийн байр бол түүний <b>дараагийнх</b>: {c('items[j + 1] = key')}"))
    s.append(Spacer(1, 6))
    s.append(code("""
        def insertion_sort(items):
            for i in range(1, len(items)):          # 1. 0-р элемент ганцаараа эрэмбэлэгдсэн
                key = items[i]                      # 2. оруулах элементийг хадгална
                j = i - 1
                while j >= 0 and items[j] > key:    # 3. key-ээс их бол…
                    items[j + 1] = items[j]         #    …баруун тийш шилжүүлнэ
                    j -= 1
                items[j + 1] = key                  # 4. чөлөөлөгдсөн байранд оруулна

        nums = [29, 10, 14, 37, 13]
        insertion_sort(nums)
        print(nums)                                 # [10, 13, 14, 29, 37]
    """))
    s.append(callout("Яагаад for биш while вэ?",
                     "Дотоод давталт хэдэн удаа эргэхийг урьдчилж мэдэхгүй: key-ээс их биш элемент "
                     "тааралдмагц, эсвэл жагсаалтын эхэнд хүрмэгц зогсоно. Ийм хоёр нөхцөлтэй давталтад "
                     f"{c('while')} тохиромжтой. {c('j >= 0')} шалгалт эхэнд байх ёстой — эс бөгөөс j = −1 үед "
                     f"{c('items[-1]')} буюу <b>сүүлийн</b> элементийг дэмий уншина (Хайлт 1/2-ийн анхааруулгыг "
                     "сана); C, Java зэрэг хэлэнд энэ нь шууд алдаа."))

    # ------------------------------------------------------------- 3
    s += section(3, "Гараар мөрдөх", need=330)
    tr = insertion_trace([29, 10, 14, 37, 13])
    rows = [["i", "key", "Эргэлтийн өмнө", "Шилжилт", "Харьц.", "Эргэлтийн дараа"]]
    for i, key, before, pos, sh, cmp_, after in tr:
        rows.append([str(i), str(key), P(lst(before), st_cell), str(sh), str(cmp_),
                     P(lst(after), st_cell)])
    tot_sh = sum(r[4] for r in tr)
    tot_cmp = sum(r[5] for r in tr)
    rows.append(["", "", "<b>Нийт</b>", f"<b>{tot_sh}</b>", f"<b>{tot_cmp}</b>", ""])
    s.append(KeepTogether([data_table(rows, [CW * 0.06, CW * 0.08, CW * 0.3, CW * 0.12,
                                             CW * 0.1, CW * 0.34],
                                      center_cols=(0, 1, 3, 4), row_bg={len(rows) - 1: OK_ROW})]))
    s.append(Spacer(1, 4))
    s.append(P(f"i = 3 үед key = 37 зүүн хөрш 29-өөсөө их тул <b>ганц</b> харьцуулаад байрандаа үлдлээ. "
               f"Insertion sort-ийн хурдны нууц үүнд бий (5-р бүлэг)."))
    inner, pos, after = insertion_inner([10, 14, 29, 37, 13], 4)
    s.append(P(f"Дотоод давталт: {c('i = 4')}, {c('key = 13')}", st_h2))
    rows = [["j", "items[j]", "items[j] &gt; 13 ?", "Үйлдэл", "Жагсаалт (жинхэнэ төлөв)"]]
    for j, vj, more, act, state in inner:
        rows.append([str(j), str(vj), "<b>True</b>" if more else "False",
                     P(c(act) if more else act, st_cell), P(lst(state), st_cell)])
    rows.append(["—", "", "", P(c(f"items[{pos}] = 13"), st_cell), P(f"<b>{lst(after)}</b>", st_cell)])
    s.append(KeepTogether([data_table(rows, [CW * 0.07, CW * 0.12, CW * 0.18, CW * 0.27, CW * 0.36],
                                      center_cols=(0, 1, 2), row_bg={len(rows) - 1: OK_ROW})]))
    s.append(Spacer(1, 4))
    s.append(callout("Анхаар: түр зуурын давхардал",
                     f"Шилжүүлэх явцад жагсаалтад нэг утга хоёр удаа харагдана ({lst(inner[2][4])}). "
                     f"Энэ алдаа биш: 13 нь {c('key')} хувьсагчид аюулгүй хадгалагдсан бөгөөд эцэст нь "
                     "давхардсан байрын нэгэнд бичигдэнэ. Зураг 2-ын «нүх» бол яг энэ байр."))

    # ------------------------------------------------------------- 4
    s += section(4, "Түгээмэл алдаа ба тест", need=300)
    r1 = run_inplace(ins_bug_no_key, [29, 10, 14])
    s.append(bug_card(
        1, "key-г хадгалахгүй байх",
        """
        j = i - 1
        while j >= 0 and items[j] > items[i]:
            items[j + 1] = items[j]
            j -= 1
        items[j + 1] = items[i]
        """,
        """
        key = items[i]
        j = i - 1
        while j >= 0 and items[j] > key:
            items[j + 1] = items[j]
            j -= 1
        items[j + 1] = key
        """,
        f"{c('[29, 10, 14]')} → {lst(r1)} — 10, 14 <b>алга болсон</b>!",
        f"Эхний шилжилт {c('items[i]')}-г дарж бичнэ ({c('j + 1 == i')}). Үүний дараа {c('items[i]')} "
        "нь оруулах гэсэн элемент биш, шилжсэн элемент болсон тул оруулах утга мөнхөд алдагдана."))
    r2 = run_inplace(ins_bug_j, [29, 10, 14])
    s.append(bug_card(
        2, "items[j + 1]-ийн оронд items[j]-д оруулах",
        """
        while j >= 0 and items[j] > key:
            items[j + 1] = items[j]
            j -= 1
        items[j] = key
        """,
        """
        while j >= 0 and items[j] > key:
            items[j + 1] = items[j]
            j -= 1
        items[j + 1] = key
        """,
        f"{c('[29, 10, 14]')} → {lst(r2)}.",
        f"Давталт зогсоход {c('items[j]')} нь key-ээс их <b>биш</b> элемент — түүнийг дарах ёсгүй. Хамгийн "
        f"аюултай нь j = −1 үед {c('items[-1] = key')} алдаагүй ажиллаж <b>сүүлийн</b> элементийг "
        "чимээгүй дарна."))
    r3 = run_inplace(ins_bug_if, [3, 2, 1])
    s.append(bug_card(
        3, "while-ийн оронд if",
        """
        if j >= 0 and items[j] > key:
            items[j + 1] = items[j]
            j -= 1
        items[j + 1] = key
        """,
        """
        while j >= 0 and items[j] > key:
            items[j + 1] = items[j]
            j -= 1
        items[j + 1] = key
        """,
        f"{c('[3, 2, 1]')} → {lst(r3)}.",
        "key ердөө нэг байр л зүүн тийш явна. 1 нь хоёр байр явах ёстой байсан. Хэдэн удаа "
        "шилжихийг урьдчилж мэдэхгүй тул давталт хэрэгтэй."))
    s.append(P("Тест", st_h2))
    s.append(P(f"Selection sort-ийн тестийг (1/3, 7-р бүлэг) функцийн нэрийг л сольж ашиглана: "
               f"{c('sorted()')}-тэй харьцуулсан санамсаргүй тест + захын тохиолдлууд."))
    names = [f"Алдаа 1: key хадгалаагүй", f"Алдаа 2: {c('items[j] = key')}",
             f"Алдаа 3: {c('if')} (while биш)"]
    s.append(KeepTogether([
        P(f"Зөв хувилбар <b>{fmt(n_tests)}</b> санамсаргүй тестийг бүгдийг давсан. Алдаатай хувилбарууд:"),
        bug_table(names, bugs, f"Зөв {c('insertion_sort')}"),
    ]))
    s.append(Spacer(1, 8))

    # ------------------------------------------------------------- 5
    s += section(5, "Хэр хурдан бэ?", need=330)
    s.append(P("Selection sort-оос ялгаатай нь insertion sort-ийн ажил <b>өгөгдлөөс</b> хамаарна:"))
    s.append(data_table([
        ["Тохиолдол", "Оролтын жишээ", "Харьцуулалт", "Шилжилт", "Big O"],
        ["Хамгийн сайн", P(f"эрэмбэлэгдсэн {c('[1, 2, 3, 4, 5]')}", st_cell), "n − 1", "0", "<b>O(n)</b>"],
        ["Дундаж", "санамсаргүй", "≈ n² / 4", "≈ n² / 4", "O(n²)"],
        ["Хамгийн муу", P(f"урвуу {c('[5, 4, 3, 2, 1]')}", st_cell), "n(n − 1) / 2", "n(n − 1) / 2",
         "O(n²)"],
    ], [CW * 0.16, CW * 0.38, CW * 0.17, CW * 0.16, CW * 0.13], center_cols=(2, 3, 4), zebra=True))
    s.append(Spacer(1, 6))
    s.append(P("Эрэмбэлэгдсэн жагсаалтад key бүр зүүн хөрштэйгээ <b>ганц</b> удаа харьцуулагдаад шууд "
               "зогсоно. Урвуу жагсаалтад key бүр эрэмбэлэгдсэн хэсгийг бүхэлд нь туулж эхэнд хүрнэ. "
               "1 000 элементтэй жагсаалтууд дээр тоолуулбал:"))
    ic = m["ins_counts"]
    s.append(KeepTogether([data_table([
        ["Оролт", "Харьцуулалт", "Шилжилт"],
        ["эрэмбэлэгдсэн", fmt(ic["sorted"][0]), fmt(ic["sorted"][1])],
        ["бараг эрэмбэлэгдсэн (10 хос ойрхон элемент сольсон)", fmt(ic["near"][0]), fmt(ic["near"][1])],
        ["санамсаргүй", fmt(ic["random"][0]), fmt(ic["random"][1])],
        ["урвуу", fmt(ic["rev"][0]), fmt(ic["rev"][1])],
    ], [CW * 0.5, CW * 0.25, CW * 0.25], center_cols=(1, 2))]))
    s.append(Spacer(1, 6))
    ns = m["ns"]
    ts, tr_, tv = m["ins_sorted"], m["ins_random"], m["ins_rev"]
    s.append(figure(chart_insertion_inputs(ns, ts, tr_, tv),
                    "Зураг 3. insertion_sort-ийн хугацаа гурван төрлийн оролт дээр. Энэ PDF-ийг үүсгэх үед "
                    "бодитоор хэмжсэн. Эрэмбэлэгдсэн оролтын шугам тэг дээр хэвтэж байна — O(n)."))
    s.append(P(f"n = 2 000 үед: эрэмбэлэгдсэн — <b>{ts[-1]:.2f} мс</b>, санамсаргүй — <b>{tr_[-1]:.0f} мс</b>, "
               f"урвуу — <b>{tv[-1]:.0f} мс</b>. Ижил функц, ижил n — гэтэл <b>{tv[-1] / ts[-1]:.0f} дахин</b> "
               "зөрүүтэй."))
    s.append(callout("Шилжилтийн тоо = «буруу хос»-ын тоо",
                     "Жагсаалтад өмнө байгаа нь хойно байгаагаасаа их байх хосыг <b>инверс</b> (inversion) "
                     "гэдэг. Нэг шилжилт яг нэг инверсийг арилгадаг тул шилжилтийн тоо = инверсийн тоо. "
                     f"[29, 10, 14, 37, 13]-д 5 инверс бий: (29, 10), (29, 14), (29, 13), (14, 13), (37, 13) "
                     f"— 3-р бүлгийн хүснэгтийн нийт шилжилт ч яг {tot_sh}. Бараг эрэмбэлэгдсэн жагсаалтад "
                     "инверс цөөн тул insertion sort бараг O(n)."))

    # ------------------------------------------------------------- 6
    s += section(6, "Тогтвортой эрэмбэлэлт", need=330)
    s.append(P("Ижил түлхүүртэй (жишээ нь ижил оноотой) элементүүд эрэмбэлсний дараа <b>анхны "
               "дарааллаа хадгалвал</b> тэр эрэмбэлэлтийг <b>тогтвортой</b> (stable) гэнэ."))
    s.append(P(f"Сурагчдыг оноогоор нь өсөхөөр эрэмбэлье. Бат, Дорж хоёр ижил 85 оноотой бөгөөд анхны "
               f"жагсаалтад Бат түрүүлж байна. Харьцуулалтыг {c('items[j][1]')} (оноо) болгож өөрчилсөн хоёр "
               "алгоритмын үр дүн:"))
    s1, s2 = list(STUDENTS), list(STUDENTS)
    selection_sort_by_score(s1)
    insertion_sort_by_score(s2)

    def who(a):
        return ", ".join(f"{n} {sc}" for n, sc in a)

    s.append(KeepTogether([data_table([
        ["", "Үр дүн", "Бат Доржоос өмнө үү?"],
        ["Анхны жагсаалт", who(STUDENTS), "Тийм"],
        ["Selection sort", who(s1), f'<font color="{BAD_INK}"><b>Үгүй — солигдсон</b></font>'],
        ["Insertion sort", who(s2), f'<font color="{GOOD_INK}"><b>Тийм — хадгалагдсан</b></font>'],
    ], [CW * 0.24, CW * 0.44, CW * 0.32], row_bg={2: MISS_ROW, 3: OK_ROW})]))
    s.append(Spacer(1, 8))
    s += bullets([
        "<b>Selection sort холын зайд солидог.</b> Сараа 0-р байр руу орохдоо тэнд байсан Батыг 2-р "
        "байр руу — Доржийн ард шидэв. Ийм холын солилт ижил элементүүдийн дарааллыг эвддэг.",
        f"<b>Insertion sort хөршөө л шилжүүлдэг.</b> key зөвхөн өөрөөсөө <b>хатуу их</b> ({c('>')}) "
        "элементийн хажуугаар өнгөрдөг тул ижил оноотойгоо хэзээ ч гүйцэж түрүүлэхгүй.",
    ])
    s3 = list(STUDENTS)
    insertion_sort_by_score(s3, ge=True)
    s.append(warn(f"{c('>')}-ийн оронд {c('>=')} бичвэл",
                  f"Insertion sort зөв эрэмбэлсээр байгаа ч <b>тогтвортой байхаа болино</b>: {who(s3)}. "
                  "Нэмээд ижил элементүүдийг дэмий шилжүүлж удаашрна."))
    s.append(callout("Хэзээ хэрэгтэй вэ?",
                     "Олон шатлалтай эрэмбэлэлт: эхлээд нэрээр, дараа нь оноогоор эрэмбэлэхэд тогтвортой "
                     "алгоритм ижил оноотой сурагчдыг <b>нэрийн дарааллаар</b> нь үлдээнэ. Python-ий "
                     f"{c('sorted()')} ба {c('list.sort()')} тогтвортой."))

    # ------------------------------------------------------------- 7
    s += section(7, "Selection sort-тэй харьцуулах", need=360)
    s.append(data_table([
        ["Шинж", swatch(C_SEL, "Selection sort"), swatch(C_INS, "Insertion sort")],
        ["Санаа", "Хамгийн багыг сонгож урд нь тавина", "Дараагийнхыг авч зөв байранд оруулна"],
        ["Харьцуулалт (эрэмбэлэгдсэн)", "n(n − 1) / 2", "<b>n − 1</b>"],
        ["Харьцуулалт (урвуу)", "n(n − 1) / 2", "n(n − 1) / 2"],
        ["Бичих үйлдэл", "<b>≤ n − 1 солилт</b>", "≤ n(n − 1) / 2 шилжилт"],
        ["Цаг (сайн / муу)", "O(n²) / O(n²)", "<b>O(n)</b> / O(n²)"],
        ["Санах ой", "O(1)", "O(1)"],
        ["Тогтвортой", "Үгүй", "<b>Тийм</b>"],
    ], [CW * 0.3, CW * 0.35, CW * 0.35], zebra=True))
    s.append(Spacer(1, 8))
    s.append(P("n = 2 000 элемент дээр хэмжсэн хугацаа:"))
    s.append(KeepTogether([data_table([
        ["Оролт", "selection_sort", "insertion_sort"],
        ["эрэмбэлэгдсэн", human_ms(m["sel_sorted_2000"]), f"<b>{human_ms(ts[-1])}</b>"],
        ["санамсаргүй", human_ms(m["sel"][-1]), human_ms(tr_[-1])],
        ["урвуу", human_ms(m["sel_rev_2000"]), human_ms(tv[-1])],
    ], [CW * 0.34, CW * 0.33, CW * 0.33], center_cols=(1, 2))]))
    s.append(Spacer(1, 8))
    def vs(t_ins, t_sel, why=""):
        r = t_ins / t_sel
        if r < 0.75:
            return f"insertion sort <b>{1 / r:.0f} дахин хурдан</b>"
        if r > 1.33:
            return f"insertion sort <b>{r:.1f} дахин удаан</b>{why}"
        return "хоёулаа <b>ойролцоо</b>"

    s.append(P(f"Хэмжилтээс: санамсаргүй өгөгдөлд {vs(tr_[-1], m['sel'][-1])}, урвуу өгөгдөлд "
               f"{vs(tv[-1], m['sel_rev_2000'], ' (шилжилт олон)')}, харин эрэмбэлэгдсэн өгөгдөлд "
               f"{vs(ts[-1], m['sel_sorted_2000'])}."))
    s.append(P("Бодит амьдрал дээрх өгөгдөл ихэвчлэн <b>бараг эрэмбэлэгдсэн</b> байдаг (эрэмбэлсэн жагсаалтад "
               "хэдэн шинэ мөр нэмэгдсэн гэх мэт), мөн insertion sort тогтвортой — тиймээс практикт "
               f"ихэвчлэн insertion sort-ийг сонгодог. Python-ий {c('sorted()')} хүртэл жижиг хэсгүүдийг "
               "(32–64 элемент) insertion sort-ийн хувилбараар эрэмбэлдэг. Selection sort-ийн давуу тал — "
               "бичих үйлдэл цөөн."))
    s.append(callout("Дараагийн алхам: Merge sort",
                     "Хоёулаа O(n²) — сая элементэд хэдэн цаг. Эрэмбэлэгдсэн хоёр жагсаалтыг нэгтгэх нь "
                     "маш хурдан гэдгийг ашиглан <b>O(n log n)</b> хүрч болно. Энэ бол «Эрэмбэлэлт 3/3: "
                     "Merge sort» хичээлийн сэдэв."))

    # ------------------------------------------------------------- 8
    s += section(8, "Дасгал", need=200)
    s.append(P("Эхлээд өөрөө бодож, кодоо тестлээрэй. Хариуг дараагийн хуудаснаас шалга."))
    s.append(exercise_card(
        1, "Гараар мөрдөх",
        f"{c('insertion_sort([4, 3, 5, 1, 2])')}: эргэлт бүрийн key, шилжилтийн тоо, эргэлтийн дараах "
        "жагсаалтыг бич."))
    s.append(exercise_card(
        2, "Буурахаар",
        f"{c('insertion_sort_desc(items)')} бич: жагсаалтыг <b>буурахаар</b> эрэмбэлнэ.",
        """
        nums = [3, 8, 1, 9, 4]
        insertion_sort_desc(nums)
        print(nums)                # [9, 8, 4, 3, 1]
        """))
    s.append(exercise_card(
        3, "Шилжилт тоол",
        f"Код ажиллуулалгүйгээр: {c('[1, 2, 3, 4, 5]')}, {c('[5, 4, 3, 2, 1]')}, "
        f"{c('[2, 1, 4, 3, 6, 5]')} тус бүрд хэдэн шилжилт хийх вэ? (Зөвлөгөө: инверс тоол.)"))
    s.append(exercise_card(
        4, "Эрэмбэлэгдсэн жагсаалтад нэмэх",
        f"{c('insert_sorted(items, x)')}: эрэмбэлэгдсэн {c('items')}-д x-ийг дарааллыг нь эвдэлгүй "
        "байрандаа нэмнэ. Insertion sort-ийн нэг эргэлт л хангалттай. Цагийн төвөгшил нь хэд вэ?",
        """
        nums = [10, 14, 29, 37]
        insert_sorted(nums, 13)
        print(nums)                # [10, 13, 14, 29, 37]
        """))
    ex5_gt, ex5_ge = list(PAIRS_EX), list(PAIRS_EX)
    insertion_sort_by_score(ex5_gt)
    insertion_sort_by_score(ex5_ge, ge=True)
    s.append(exercise_card(
        5, "Тогтвортой юу?",
        f"{c(str(PAIRS_EX))}-ийг тоогоор нь insertion sort-оор эрэмбэлэв. {c('>')} хэрэглэвэл ямар "
        f"дараалал гарах вэ? {c('>=')} хэрэглэвэл?"))

    s.append(PageBreak())
    s.append(P("Дасгалын хариу", st_h1))
    s.append(P("Бүх хариуг энэ PDF-ийг үүсгэх үед жишээн дээр нь ажиллуулж шалгасан.", st_small))
    ex = insertion_trace([4, 3, 5, 1, 2])
    s.append(P(f"1. Гараар мөрдөх — нийт {sum(r[4] for r in ex)} шилжилт", st_h2))
    rows = [["i", "key", "Шилжилт", "Эргэлтийн дараа"]]
    for i, key, before, pos, sh, cmp_, after in ex:
        rows.append([str(i), str(key), str(sh), P(lst(after), st_cell)])
    s.append(data_table(rows, [CW * 0.1, CW * 0.12, CW * 0.18, CW * 0.6], center_cols=(0, 1, 2)))
    s.append(P("2. Буурахаар — ганц тэмдэгт", st_h2))
    s.append(code("""
        def insertion_sort_desc(items):
            for i in range(1, len(items)):
                key = items[i]
                j = i - 1
                while j >= 0 and items[j] < key:    # >  →  <
                    items[j + 1] = items[j]
                    j -= 1
                items[j + 1] = key
    """))
    s.append(P("3. Шилжилт тоол", st_h2))
    s.append(P(f"{c('[1, 2, 3, 4, 5]')} — <b>0</b> (инверсгүй). {c('[5, 4, 3, 2, 1]')} — <b>10</b> "
               f"(хос бүр инверс: 5 · 4 / 2). {c('[2, 1, 4, 3, 6, 5]')} — <b>3</b> ((2, 1), (4, 3), (6, 5))."))
    s.append(P("4. Эрэмбэлэгдсэн жагсаалтад нэмэх — O(n)", st_h2))
    s.append(code("""
        def insert_sorted(items, x):
            items.append(x)                     # төгсгөлд нэг зай гаргана
            j = len(items) - 2                  # x-ийн өмнөх элемент
            while j >= 0 and items[j] > x:
                items[j + 1] = items[j]
                j -= 1
            items[j + 1] = x
    """))
    s.append(P(f"Хамгийн муу үед бүх элементийг шилжүүлнэ — O(n). Python-д бэлэн нь: "
               f"{c('bisect.insort(items, x)')} (Хайлт 2/2) — байрыг O(log n)-ээр олдог ч шилжүүлэлт нь "
               "мөн O(n).", st_small))
    s.append(P("5. Тогтвортой юу?", st_h2))
    s.append(P(f"{c('>')}: {c(str(ex5_gt))} — Бат Доржоос, Ану Цэцэгээс өмнө хэвээр: <b>тогтвортой</b>. "
               f"{c('>=')}: {c(str(ex5_ge))} — ижил тоотой хосууд байраа сольсон: <b>тогтворгүй</b>."))

    # ------------------------------------------------------------- 9
    s += section(9, "Хураангуй", need=470)
    s.append(P("Загвар — цээжлэх биш, ойлгож бич", st_h2))
    s.append(two_cards(
        code_card("Insertion sort", C_INS, """
            def insertion_sort(items):
                for i in range(1, len(items)):
                    key = items[i]
                    j = i - 1
                    while j >= 0 and items[j] > key:
                        items[j + 1] = items[j]
                        j -= 1
                    items[j + 1] = key
        """),
        facts_card("Гол тоонууд", C_INS, [
            ("Сайн (эрэмбэлэгдсэн)", "n − 1 харьцуулалт · O(n)"),
            ("Муу (урвуу)", "n(n − 1) / 2 · O(n²)"),
            ("Шилжилт", "= инверсийн тоо"),
            ("Санах ой", "O(1) — байрандаа"),
            ("Тогтвортой юу?", f"Тийм ({c('>')} үед)"),
        ])))
    s.append(Spacer(1, 6))
    s.append(P("Insertion sort бичихдээ шалгах 4 зүйл", st_h2))
    s += numbered([
        f"{c('key = items[i]')} — оруулах элементийг шилжүүлэхээс <b>өмнө</b> хадгалсан уу?",
        f"{c('j >= 0')} шалгалт {c('items[j]')}-ээс <b>өмнө</b> байна уу?",
        f"{c('while')} (if биш), {c('j -= 1')} давталт дотор байна уу?",
        f"key-г {c('items[j + 1]')}-д (items[j] биш) оруулж байна уу?",
    ])
    s.append(P("Санаж үлдэх зүйлс", st_h2))
    s += bullets([
        "Зүүн хэсэг эрэмбэлэгдсэн боловч эцсийн биш; key-ээс их элементүүд баруун тийш <b>шилжинэ</b>.",
        "Ажил өгөгдлөөс хамаарна: эрэмбэлэгдсэн — <b>O(n)</b>, урвуу — <b>O(n²)</b>.",
        f"Тогтвортой: ижил элементүүдийн дараалал хадгалагдана ({c('>')}, {c('>=')} биш).",
        "Жижиг эсвэл бараг эрэмбэлэгдсэн өгөгдөлд — insertion sort; том өгөгдөлд — O(n log n) (3/3).",
    ])

    doc = LessonDoc(OUT_INSERTION,
                    make_cover("АЛГОРИТМЫН ҮНДЭС  ·  PYTHON  ·  ЭРЭМБЭЛЭЛТ 2/3", "Insertion", "sort",
                               ["Оруулан эрэмбэлэлт: хөзөр гартаа", "эрэмбэлдэг шиг"],
                               deco_insertion),
                    make_page("Эрэмбэлэлт 2/3 — Insertion sort"),
                    title="Эрэмбэлэлт 2/3 — Insertion sort",
                    subject=f"Insertion sort: {LEVEL.lower()}")
    doc.build(s)
    return bugs


# ============================================================================
# ХИЧЭЭЛ 3: MERGE SORT
# ============================================================================
def build_merge(m, n_tests):
    bugs = bug_report([ms_bug_rest, ms_bug_base, ms_bug_ignore], inplace=False)
    s = front_page(
        "Insertion sort, функц, рекурс, Big O",
        [
            "Эрэмбэлэгдсэн хоёр жагсаалтыг <b>нийлүүлэх</b> (merge) функцийг өөрөө бичнэ.",
            "«Хувааж ял» (divide and conquer) санааг ойлгож, merge sort-ийг <b>рекурсээр</b> бичнэ.",
            "Рекурсын модыг зурж, кодоо гараар мөрдөнө.",
            "Яагаад <b>O(n log n)</b> болохыг тайлбарлаж, O(n²)-тэй бодит хэмжилтээр харьцуулна.",
            f"Python-ий {c('sorted()')}-ийг {c('key=')}, {c('reverse=')}-тэй зөв хэрэглэнэ.",
        ],
        ["Санаа: хувааж ял", "Нийлүүлэх (merge)", "Merge sort", "Рекурсын мод",
         "Яагаад O(n log n) вэ?", "Түгээмэл алдаа ба тест", "Гурван алгоритмыг хэмжих",
         "Python-ий sorted()", "Дасгал", "Хураангуй"],
        "Нэг өгүүлбэрээр",
        ["<b>Merge sort</b> (нийлүүлэн эрэмбэлэлт): жагсаалтыг хоёр хуваа, хагас бүрийг ижил аргаар "
         "эрэмбэл, дараа нь эрэмбэлэгдсэн хоёр хагасыг нэг болгон <b>нийлүүл</b>."],
    )

    # ------------------------------------------------------------- 1
    s += section(1, "Санаа: хувааж ял")
    s.append(callout("Өмнөх хичээлүүдээс",
                     "Selection, insertion sort хоёулаа O(n²): n = 1 000 000 бол ≈ 5 · 10¹¹ харьцуулалт. "
                     "Binary search хагасаар хуваах замаар O(n)-ийг O(log n) болгосныг санаарай (Хайлт 2/2). "
                     "Merge sort ч мөн хуваах санааг ашиглана."))
    s.append(P("<b>Зүйрлэл:</b> багш 32 сурагчийн шалгалтын хуудсыг нэрээр нь эрэмбэлэх хэрэгтэй. Хуудсыг "
               "хоёр туслахдаа хувааж өгнө; тэд бас хуваагаад цааш нь өгнө… Хүн бүр <b>ганц</b> хуудастай "
               "болоход эрэмбэлэх юм үлдэхгүй. Дараа нь эрэмбэлэгдсэн овоонуудыг хоёр хоёроор нь "
               "<b>нийлүүлсээр</b> буцаад нэг овоо болгоно."))
    s.append(P("Энэ бол <b>хувааж ял</b> (divide and conquer) арга — гурван алхамтай:"))
    s += numbered([
        "<b>Хуваах:</b> жагсаалтыг дундуур нь хоёр хагас болгоно.",
        "<b>Шийдэх:</b> хагас бүрийг <b>мөн merge sort-оор</b> эрэмбэлнэ (рекурс). 0 эсвэл 1 элементтэй "
        "жагсаалт аль хэдийн эрэмбэлэгдсэн — энэ бол <b>суурь тохиолдол</b>.",
        "<b>Нийлүүлэх:</b> эрэмбэлэгдсэн хоёр хагасыг нэг эрэмбэлэгдсэн жагсаалт болгоно.",
    ])
    s.append(P("Бүх ажлын гол нь 3-р алхам. Тиймээс эхлээд нийлүүлэх функцээ бичье."))

    # ------------------------------------------------------------- 2
    s += section(2, "Нийлүүлэх (merge)", need=360)
    s.append(P("Эрэмбэлэгдсэн хоёр овоо хуудас ширээн дээр байна, хамгийн бага нь дээрээ. Шинэ овоонд "
               "дараагийн хуудсыг тавихын тулд <b>хоёр дээд</b> хуудсыг л харьцуулахад хангалттай — бага нь "
               "үлдсэн бүх хуудаснаас хамгийн бага нь гарцаагүй."))
    L, R = [3, 27, 38, 43], [9, 10, 15, 82]
    s.append(figure(chart_merge_steps(L, R),
                    "Зураг 1. merge([3, 27, 38, 43], [9, 10, 15, 82]). Мөр бүр нэг харьцуулалт: хар хөх — "
                    "сонгогдсон бага нь (result-д нэмэгдэнэ), саарал — аль хэдийн авсан, улбар шар — "
                    "үлдэгдэл. 7 харьцуулалтын дараа left дуусч, 82-ыг шууд залгав."))
    s.append(code("""
        def merge(left, right):
            result = []
            i = j = 0                                   # хоёр овооны «дээд хуудас»
            while i < len(left) and j < len(right):     # хоёуланд элемент үлдсэн үед
                if left[i] <= right[j]:                 # бага нь → result
                    result.append(left[i])
                    i += 1
                else:
                    result.append(right[j])
                    j += 1
            result.extend(left[i:])                     # аль нэг нь дуусав:
            result.extend(right[j:])                    # үлдсэнийг бүгдийг нь залгана
            return result

        merge([3, 27, 38, 43], [9, 10, 15, 82])     # [3, 9, 10, 15, 27, 38, 43, 82]
    """))
    s.append(P("Харьцуулалт бүр нэг элементийг result руу шилжүүлдэг тул нийт n элементтэй үед merge "
               "хамгийн ихдээ n − 1 харьцуулалт хийнэ — <b>O(n)</b>."))
    s.append(callout("Яагаад &lt; биш &lt;= вэ?",
                     "Тэнцүү үед <b>зүүн</b> талынхыг түрүүлж авна. Зүүн хагас анхны жагсаалтад өмнө нь "
                     "байсан тул ижил элементүүдийн дараалал хадгалагдана — merge sort <b>тогтвортой</b> "
                     "(Эрэмбэлэлт 2/3-ийг сана)."))
    s.append(callout("Үлдэгдэл",
                     "Давталт аль нэг жагсаалт дуусахад зогсоно. Нөгөөд нь үлдсэн элементүүд эрэмбэлэгдсэн "
                     "бөгөөд result-ийн бүх элементээс их тул шууд залгана. Хоёр extend-ийн нэг нь үргэлж "
                     "хоосон жагсаалт залгадаг — энэ нь зүгээр."))

    # ------------------------------------------------------------- 3
    s += section(3, "Merge sort", need=330)
    s.append(step(1, "Суурь тохиолдол: 0 эсвэл 1 элемент бол эрэмбэлэх юм алга — хуулбарыг буцаана."))
    s.append(step(2, f"Дундуур нь хуваана: {c('mid = len(items) // 2')}"))
    s.append(step(3, "Хагас бүрийг <b>өөрөөр нь</b> (рекурс) эрэмбэлнэ."))
    s.append(step(4, f"Эрэмбэлэгдсэн хоёр хагасыг {c('merge')}-ээр нийлүүлж буцаана."))
    s.append(Spacer(1, 6))
    s.append(code("""
        def merge_sort(items):
            if len(items) <= 1:                 # 1. суурь тохиолдол
                return items[:]                 #    (хуулбар)
            mid = len(items) // 2               # 2. хуваана
            left = merge_sort(items[:mid])      # 3. зүүн хагасыг эрэмбэлнэ
            right = merge_sort(items[mid:])     #    баруун хагасыг эрэмбэлнэ
            return merge(left, right)           # 4. нийлүүлнэ

        nums = [38, 27, 43, 3, 9, 82, 10, 15]
        print(merge_sort(nums))     # [3, 9, 10, 15, 27, 38, 43, 82]
        print(nums)                 # [38, 27, 43, 3, 9, 82, 10, 15] — өөрчлөгдөөгүй
    """))
    s.append(callout("Байрандаа биш — шинэ жагсаалт",
                     f"Selection, insertion sort {c('list.sort()')} шиг байрандаа эрэмбэлдэг байсан. Энэ "
                     f"merge_sort нь {c('sorted()')} шиг <b>шинэ</b> жагсаалт буцаадаг, эх жагсаалт хэвээр "
                     f"үлдэнэ. Тиймээс үр дүнг заавал {c('result = merge_sort(nums)')} гэж хүлээж авна. "
                     "Үнэ нь — O(n) нэмэлт санах ой."))
    s.append(callout("Рекурс хэзээ зогсох вэ?",
                     "Дуудлага бүр жагсаалтыг хоёр хуваадаг тул урт нь 8 → 4 → 2 → 1 гэж багассаар суурь "
                     "тохиолдолд <b>заавал</b> хүрнэ. Суурь тохиолдол буруу бол рекурс хэзээ ч зогсохгүй "
                     "(6-р бүлэг)."))

    # ------------------------------------------------------------- 4
    s += section(4, "Рекурсын мод", need=360)
    tree_vals = [38, 27, 43, 3, 9, 82, 10, 15]
    s.append(figure(chart_merge_tree(tree_vals),
                    "Зураг 2. merge_sort([38, 27, 43, 3, 9, 82, 10, 15])-ийн мод. Дээрээс доош — хуваах "
                    "(merge_sort дуудлагууд), доороос дээш — нийлүүлэх (merge). Цайвар хөх — эрэмбэлэгдээгүй, "
                    "ногоон — эрэмбэлэгдсэн хэсэг."))
    s.append(P("Python модыг мөр мөрөөр биш, <b>зүүнээс эхэлж гүн рүү</b> гүйцэтгэдэг: эхлээд зүүн хагасыг "
               "бүрэн эрэмбэлж дуусаад дараа нь баруун хагас руу орно. Үүнийг харахын тулд дуудлага бүрийг "
               "гүнээр нь догол мөр болгон хэвлэе:"))
    s.append(code("""
        def merge_sort(items, depth=0):
            pad = "    " * depth                    # гүн бүрд 4 зай догол
            print(pad + f"merge_sort({items})")
            if len(items) <= 1:
                return items[:]
            mid = len(items) // 2
            left = merge_sort(items[:mid], depth + 1)
            right = merge_sort(items[mid:], depth + 1)
            result = merge(left, right)
            print(pad + f"merge → {result}")
            return result

        merge_sort([38, 27, 43, 3])
    """, after=4))
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        merge_sort_traced([38, 27, 43, 3])
    s.append(P("Гаралт (бодитоор ажиллуулсан):", st_small))
    s.append(Spacer(1, 3))
    s.append(code_block(out.getvalue(), plain=True, after=10))

    # ------------------------------------------------------------- 5
    s += section(5, "Яагаад O(n log n) вэ?", need=360)
    s.append(P("Модыг <b>түвшнээр</b> нь тоолъё (Зураг 2):"))
    s += bullets([
        "<b>Түвшин бүрийн ажил ≈ n.</b> Нэг түвшний бүх merge нийлээд яг n элементийг нэг нэг удаа "
        "result руу хийнэ: 4 merge × 2 = 2 merge × 4 = 1 merge × 8 = 8 элемент.",
        "<b>Түвшний тоо ≈ log<sub>2</sub> n.</b> Түвшин бүрт жагсаалт хоёр хуваагдана: 8 → 4 → 2 → 1 бол "
        "3 түвшин. Binary search-ийнх шиг сая элементэд ердөө 20.",
        "<b>Нийт ажил ≈ n · log<sub>2</sub> n</b> → <b>O(n log n)</b>. Хамгийн сайн, дундаж, хамгийн муу "
        "тохиолдол бүгд ижил.",
    ])
    rows = [["n", "Түвшин", "merge sort ≈ n · log<sub>2</sub> n", "selection sort n(n − 1) / 2",
             "Хэд дахин цөөн"]]
    for n in (10, 1000, 1_000_000):
        nl = n * math.log2(n)
        sel = n * (n - 1) // 2
        rows.append([fmt(n), str(math.ceil(math.log2(n))), fmt(nl),
                     fmt(sel) if n < 10**6 else "≈ 5 · 10¹¹",
                     f"≈ {sel / nl:.1f}" if sel / nl < 10 else f"≈ {fmt(sel / nl)}"])
    s.append(KeepTogether([data_table(rows, [CW * 0.16, CW * 0.12, CW * 0.26, CW * 0.26, CW * 0.2],
                                      center_cols=(0, 1, 2, 3, 4), zebra=True)]))
    s.append(Spacer(1, 6))
    s.append(P(f"Бодитоор тоолбол: 1 000 элементтэй санамсаргүй жагсаалтад merge_sort "
               f"<b>{fmt(m['merge_cmp_1000'])}</b> харьцуулалт хийв, selection sort — "
               f"<b>{fmt(m['sel_cmp_1000'])}</b>."))
    s.append(callout("Үнэ: санах ой",
                     "Merge sort нэмэлт O(n) санах ой хэрэглэдэг (шинэ жагсаалтууд). Selection, insertion "
                     "sort — O(1). Ихэнх тохиолдолд хурд нь илүү чухал."))

    # ------------------------------------------------------------- 6
    s += section(6, "Түгээмэл алдаа ба тест", need=300)
    s.append(bug_card(
        1, "Үлдэгдлийг мартах",
        """
        while i < len(left) and j < len(right):
            ...
        return result
        """,
        """
        while i < len(left) and j < len(right):
            ...
        result.extend(left[i:])
        result.extend(right[j:])
        return result
        """,
        f"{c('merge([1, 5], [2, 3])')} → {lst(merge_no_rest([1, 5], [2, 3]))} — 5 алга. "
        f"{c('merge_sort([38, 27, 43, 3])')} → {lst(ms_bug_rest([38, 27, 43, 3]))}!",
        "Давталт аль нэг жагсаалт дуусахад зогсдог. Нөгөөд нь үлдсэн элементүүдийг залгахгүй бол алдагдана. "
        "Түвшин бүрт алдагдсаар 4 элементээс 1 л үлдлээ."))
    s.append(bug_card(
        2, "Суурь тохиолдол буруу",
        """
        if len(items) == 0:
            return []
        """,
        """
        if len(items) <= 1:
            return items[:]
        """,
        f"{c('merge_sort([5])')} → {c('RecursionError')}.",
        "1 элементтэй жагсаалтыг хуваахад mid = 0: зүүн хагас [], баруун хагас [5] — яг өмнөхтэйгөө ижил! "
        "Жагсаалт багасахгүй тул рекурс зогсохгүй, Python ≈ 1 000 гүнд алдаа шиднэ."))
    s.append(bug_card(
        3, "Буцаасан утгыг хаях",
        """
        left, right = items[:mid], items[mid:]
        merge_sort(left)
        merge_sort(right)
        return merge(left, right)
        """,
        """
        left = merge_sort(items[:mid])
        right = merge_sort(items[mid:])
        return merge(left, right)
        """,
        f"{c('merge_sort([38, 27, 43, 3])')} → {lst(ms_bug_ignore([38, 27, 43, 3]))} — эрэмбэлэгдээгүй.",
        "merge_sort шинэ жагсаалт буцаадаг, left-ийг өөрийг нь өөрчилдөггүй. Үр дүнг хаясан тул merge "
        "эрэмбэлэгдээгүй хагасуудыг авч, «хоёр дээд хуудас» гэсэн таамаг эвдэрнэ."))
    s.append(P("Тест", st_h2))
    s.append(P(f"Өмнөх хичээлүүдийн адил {c('sorted()')}-тэй харьцуулна. Нэмээд эх жагсаалт "
               "<b>өөрчлөгдөөгүйг</b> шалгана:"))
    s.append(code("""
        for _ in range(10_000):
            items = [random.randint(0, 9) for _ in range(random.randint(0, 12))]
            original = items[:]
            assert merge_sort(items) == sorted(items)
            assert items == original              # эх жагсаалт хэвээр
    """))
    names = ["Алдаа 1: үлдэгдэл мартсан", f"Алдаа 2: {c('len(items) == 0')}",
             "Алдаа 3: буцаасан утгыг хаясан"]
    s.append(KeepTogether([
        P(f"Зөв хувилбар <b>{fmt(n_tests)}</b> санамсаргүй тестийг бүгдийг давсан. Алдаатай хувилбарууд:"),
        bug_table(names, bugs, f"Зөв {c('merge_sort')}"),
    ]))
    s.append(Spacer(1, 8))

    # ------------------------------------------------------------- 7
    s += section(7, "Гурван алгоритмыг хэмжих", need=360)
    ns3 = m["ns3"]
    s.append(figure(chart_compare(ns3, m["c_sel"], m["c_ins"], m["c_merge"], m["c_py"]),
                    "Зураг 3. Санамсаргүй жагсаалтыг эрэмбэлэх хугацаа. Энэ PDF-ийг үүсгэх үед ижил өгөгдөл "
                    "дээр бодитоор хэмжсэн. O(n²) хоёр алгоритм дээшээ муруйж, O(n log n) хоёр нь тэг "
                    "орчимд хэвтэнэ.",
                    head="n = 1 000 … 5 000"))
    t5 = {"sel": m["c_sel"][-1], "ins": m["c_ins"][-1], "merge": m["c_merge"][-1], "py": m["c_py"][-1]}
    n5 = ns3[-1]
    rows = [["n", swatch(C_SEL, "selection_sort"), swatch(C_INS, "insertion_sort"),
             swatch(C_MERGE, "merge_sort"), swatch(C_PY, "sorted()")]]
    rows.append([fmt(n5), human_ms(t5["sel"]), human_ms(t5["ins"]), human_ms(t5["merge"]),
                 human_ms(t5["py"])])
    for n, (tm, tp) in sorted(m["big"].items()):
        k = (n / n5) ** 2
        rows.append([fmt(n), f"≈ {human_ms(t5['sel'] * k)}", f"≈ {human_ms(t5['ins'] * k)}",
                     f"<b>{human_ms(tm)}</b>", f"<b>{human_ms(tp)}</b>"])
    s.append(KeepTogether([
        P("Том n дээр", st_h2),
        data_table(rows, [CW * 0.16, CW * 0.21, CW * 0.21, CW * 0.21, CW * 0.21],
                   center_cols=(0, 1, 2, 3, 4)),
        P("≈ — O(n²) хоёрыг n = 5 000-ийн хэмжилтээс n²-аар үржүүлж <b>тооцоолсон</b> (тэд ингэж удаан "
          "ажиллах тул хэмжээгүй). Бусад нь бодит хэмжилт.", st_caption),
    ]))
    big1m = m["big"][1_000_000]
    s.append(P(f"Сая элементэд merge sort <b>{human_ms(big1m[0])}</b>, selection sort бол ойролцоогоор "
               f"<b>{human_ms(t5['sel'] * (1_000_000 / n5) ** 2)}</b>. Энэ бол Big O хичээлийн гол санаа: "
               "<b>сайн алгоритм хурдан компьютерээс илүү чухал</b>. Харин {c} нь merge sort-оос ч "
               f"≈ {big1m[0] / big1m[1]:.0f} дахин хурдан — C хэл дээр бичигдсэн, илүү ухаалаг алгоритм."
               .replace("{c}", c("sorted()"))))

    # ------------------------------------------------------------- 8
    s += section(8, "Python-ий sorted()", need=300)
    s.append(P("Ажлын кодонд өөрийн эрэмбэлэлтийг бараг бичихгүй — бэлэн функц хурдан, тогтвортой, "
               "алдаагүй. Харин яаж <b>зөв</b> хэрэглэхийг мэдэх хэрэгтэй:"))
    s.append(code("""
        nums = [38, 27, 43, 3, 9]
        sorted(nums)                     # [3, 9, 27, 38, 43] — шинэ жагсаалт
        sorted(nums, reverse=True)       # [43, 38, 27, 9, 3] — буурахаар
        nums.sort()                      # байрандаа, None буцаана

        words = ["банана", "алим", "үзэм", "лийр"]
        sorted(words, key=len)           # үгийн уртаар: ['алим', 'үзэм', 'лийр', 'банана']

        students = [("Бат", 85), ("Сараа", 92), ("Дорж", 85)]
        sorted(students, key=lambda s: s[1], reverse=True)
        # [('Сараа', 92), ('Бат', 85), ('Дорж', 85)] — тогтвортой: Бат Доржоос өмнө хэвээр
    """))
    s.append(P(f"{c('key=')} нь элемент бүрээс «юугаар нь харьцуулахыг» гаргаж өгөх функц. Ижил "
               "түлхүүртэй элементүүдийн анхны дараалал хадгалагдана (тогтвортой)."))
    s.append(warn("Анхаар: монгол үгийг эрэмбэлэх",
                  [f"{c('sorted()')} үсгийг Unicode кодоор нь харьцуулдаг. Ө, Ү үсгийн код Я-гаас ч их тул "
                   "цагаан толгойн дараалал алдагдана. Засахын тулд өөрийн key функц бичнэ:",
                   Spacer(1, 4),
                   code_block("""
                       MN = "абвгдеёжзийклмноөпрстуүфхцчшщъыьэюя"

                       def mn_key(word):
                           return [MN.find(ch) for ch in word.lower()]   # үсэг бүрийн байр

                       words = ["үзэм", "тоор", "өвс", "алим"]
                       sorted(words)               # ['алим', 'тоор', 'үзэм', 'өвс']  ← буруу!
                       sorted(words, key=mn_key)   # ['алим', 'өвс', 'тоор', 'үзэм']
                   """, width=CW - 28)]))
    big_rand_py = m["big"][1_000_000][1]
    s.append(callout(f"{c('sorted()')} дотор юу байдаг вэ?",
                     "<b>Timsort</b> (Python 3.11-ээс хойш түүний сайжруулсан хувилбар) — merge sort ба "
                     "insertion sort-ийн эрлийз. Жагсаалтаас аль хэдийн эрэмбэлэгдсэн хэсгүүдийг олж, богино "
                     "хэсгүүдийг insertion sort-оор эрэмбэлээд, merge sort шиг нийлүүлдэг. Тиймээс хамгийн муу "
                     "үед O(n log n), эрэмбэлэгдсэн өгөгдөлд O(n), тогтвортой — энэ цувралын 2/3, 3/3 "
                     f"хичээлийн санаанууд нийлсэн. Сая элементийг санамсаргүй бол <b>{human_ms(big_rand_py)}</b>, "
                     f"аль хэдийн эрэмбэлэгдсэн бол <b>{human_ms(m['py_presorted_1m'])}</b>-д эрэмбэлэв."))

    # ------------------------------------------------------------- 9
    s += section(9, "Дасгал", need=200)
    s.append(P("Эхлээд өөрөө бодож, кодоо тестлээрэй. Хариуг дараагийн хуудаснаас шалга."))
    s.append(exercise_card(
        1, "merge-ийг мөрдөх",
        f"{c('merge([1, 4, 9], [2, 3, 10, 12])')}: алхам бүрт аль элемент result руу орохыг бич. "
        "Нийт хэдэн харьцуулалт хийх вэ?"))
    s.append(exercise_card(
        2, "Мод зурах",
        f"{c('merge_sort([5, 2, 4, 7, 1, 3, 2, 6])')}-ийн модыг Зураг 2 шиг зур: хуваах ба нийлүүлэх "
        "түвшин бүрийг бич."))
    s.append(exercise_card(
        3, "Буурахаар",
        f"{c('merge_sort_desc(items)')} бич. Тогтвортой хэвээр байлгахын тулд merge дахь харьцуулалтыг "
        "юу болгох вэ?",
        """
        merge_sort_desc([3, 8, 1, 9, 4])    # [9, 8, 4, 3, 1]
        """))
    s.append(exercise_card(
        4, "Түвшний тоо",
        "16, 1 000, 1 000 000 элементтэй жагсаалтын рекурсын мод хэдэн нийлүүлэх түвшинтэй вэ?"))
    s.append(exercise_card(
        5, "Нийтлэг элемент",
        f"{c('common(a, b)')}: эрэмбэлэгдсэн (давхардалгүй) хоёр жагсаалтын <b>хоёуланд</b> байгаа "
        "элементүүдийг буцаа. merge-ийн «хоёр заагч» санааг ашиглаж O(n + m)-д бич.",
        """
        common([1, 3, 4, 7, 9], [2, 3, 7, 8, 9])    # [3, 7, 9]
        """))

    s.append(PageBreak())
    s.append(P("Дасгалын хариу", st_h1))
    s.append(P("Бүх хариуг энэ PDF-ийг үүсгэх үед жишээн дээр нь ажиллуулж шалгасан.", st_small))
    res1, cmp1 = merge_count([1, 4, 9], [2, 3, 10, 12])
    st1, i1, j1 = merge_steps([1, 4, 9], [2, 3, 10, 12])
    order = []
    for i, j, side, val in st1:
        a, b = [1, 4, 9][i], [2, 3, 10, 12][j]
        order.append(f"{a} ≤ {b} → {a}" if side == "L" else f"{a} &gt; {b} → {b}")
    rest1 = [1, 4, 9][i1:] + [2, 3, 10, 12][j1:]
    s.append(P(f"1. merge-ийг мөрдөх — {cmp1} харьцуулалт", st_h2))
    s.append(P(";&nbsp; ".join(order) + f"; left дуусав → үлдэгдэл {lst(rest1)}. "
               f"Үр дүн: {lst(res1)}."))
    s.append(P("2. Мод зурах", st_h2))
    v2 = [5, 2, 4, 7, 1, 3, 2, 6]
    lines = []
    g = len(v2)
    while g >= 1:
        lines.append(("Хуваах" if g > 1 else "Суурь", [v2[k:k + g] for k in range(0, len(v2), g)]))
        g //= 2
    g = 2
    while g <= len(v2):
        lines.append(("Нийлүүлэх", [merge_sort(v2[k:k + g]) for k in range(0, len(v2), g)]))
        g *= 2
    s.append(data_table([[lab, P("&nbsp;&nbsp;".join(lst(x) for x in grp), st_cell)]
                         for lab, grp in lines],
                        [CW * 0.2, CW * 0.8], header=False, row_bg={len(lines) - 1: OK_ROW}))
    s.append(Spacer(1, 6))
    s.append(P("3. Буурахаар — &gt;= хэрэглэнэ", st_h2))
    s.append(code("""
        def merge_desc(left, right):
            ...
                if left[i] >= right[j]:         # <=  →  >= : тэнцүү үед ЗҮҮНийг авна
            ...

        def merge_sort_desc(items):
            if len(items) <= 1:
                return items[:]
            mid = len(items) // 2
            return merge_desc(merge_sort_desc(items[:mid]), merge_sort_desc(items[mid:]))
    """))
    s.append(P(f"{c('>')} бичвэл тэнцүү үед <b>баруун</b> талынх түрүүлж, тогтвортой байдал алдагдана.",
               st_small))
    s.append(P("4. Түвшний тоо — log<sub>2</sub> n, дээш бүхэлчилсэн", st_h2))
    s.append(P("16 → <b>4</b>, 1 000 → <b>10</b> (2<sup>10</sup> = 1 024), 1 000 000 → <b>20</b> "
               "(2<sup>20</sup> ≈ 1 сая). Binary search-ийн алхмын тоотой яг ижил."))
    s.append(P("5. Нийтлэг элемент — O(n + m)", st_h2))
    s.append(code("""
        def common(a, b):
            result = []
            i = j = 0
            while i < len(a) and j < len(b):
                if a[i] == b[j]:                # хоёуланд байна
                    result.append(a[i])
                    i += 1
                    j += 1
                elif a[i] < b[j]:               # бага нь нөгөөд байхгүй — алгасна
                    i += 1
                else:
                    j += 1
            return result
    """))

    # ------------------------------------------------------------- 10
    s += section(10, "Хураангуй", need=640)
    s.append(P("Загвар — цээжлэх биш, ойлгож бич", st_h2))
    s.append(two_cards(
        code_card("merge · O(n)", C_MERGE, """
            def merge(left, right):
                result = []
                i = j = 0
                while i < len(left) and j < len(right):
                    if left[i] <= right[j]:
                        result.append(left[i])
                        i += 1
                    else:
                        result.append(right[j])
                        j += 1
                result.extend(left[i:])
                result.extend(right[j:])
                return result
        """),
        code_card("merge_sort · O(n log n)", C_MERGE, """
            def merge_sort(items):
                if len(items) <= 1:
                    return items[:]
                mid = len(items) // 2
                left = merge_sort(items[:mid])
                right = merge_sort(items[mid:])
                return merge(left, right)
        """)))
    s.append(Spacer(1, 6))
    s.append(P("Цувралын харьцуулалт", st_h2))
    s.append(data_table([
        ["Алгоритм", "Санаа", "Сайн", "Муу", "Санах ой", "Тогтвортой"],
        [swatch(C_SEL, "Selection"), "хамгийн багыг сонгож урд тавина", "O(n²)", "O(n²)", "O(1)", "Үгүй"],
        [swatch(C_INS, "Insertion"), "дараагийнхыг зөв байранд оруулна", "O(n)", "O(n²)", "O(1)", "Тийм"],
        [swatch(C_MERGE, "Merge"), "хоёр хувааж, эрэмбэлж, нийлүүлнэ", "O(n log n)", "O(n log n)",
         "O(n)", "Тийм"],
        [swatch(C_PY, "sorted()"), "Timsort: merge + insertion", "O(n)", "O(n log n)", "O(n)", "Тийм"],
    ], [CW * 0.15, CW * 0.33, CW * 0.12, CW * 0.13, CW * 0.12, CW * 0.15],
        center_cols=(2, 3, 4, 5), zebra=True))
    s.append(P("Санаж үлдэх зүйлс", st_h2))
    s += bullets([
        "<b>Хувааж ял:</b> хуваа → хагас бүрийг рекурсээр шийд → нийлүүл. Суурь тохиолдол: ≤ 1 элемент.",
        f"merge нь хоёр «дээд элемент»-ийг харьцуулна; дуусахад <b>үлдэгдлийг</b> залга; {c('<=')} → тогтвортой.",
        "log<sub>2</sub> n түвшин × түвшин бүрт n ажил = <b>O(n log n)</b>; нэмэлт санах ой O(n).",
        f"merge_sort шинэ жагсаалт буцаана — {c('result = merge_sort(nums)')}.",
        f"Ажлын кодонд {c('sorted()')} / {c('list.sort()')}; {c('key=')}, {c('reverse=')}-ийг ашигла; "
        "монгол үгэнд өөрийн key хэрэгтэй.",
    ])

    doc = LessonDoc(OUT_MERGE,
                    make_cover("АЛГОРИТМЫН ҮНДЭС  ·  PYTHON  ·  ЭРЭМБЭЛЭЛТ 3/3", "Merge", "sort",
                               ["Нийлүүлэн эрэмбэлэлт: хувааж,", "эрэмбэлж, нийлүүлэх"],
                               deco_merge),
                    make_page("Эрэмбэлэлт 3/3 — Merge sort"),
                    title="Эрэмбэлэлт 3/3 — Merge sort",
                    subject=f"Merge sort: {LEVEL.lower()}")
    doc.build(s)
    return bugs


def build():
    print("Өөрийгөө шалгаж байна…")
    self_check()
    test_edges()
    n_tests = run_random_tests(10_000)
    print("Хэмжилт хийж байна (≈ 30 сек)…")
    m = measure()
    sel_bugs = build_selection(m, n_tests)
    print("Бэлэн:", OUT_SELECTION)
    ins_bugs = build_insertion(m, n_tests)
    print("Бэлэн:", OUT_INSERTION)
    ms_bugs = build_merge(m, n_tests)
    print("Бэлэн:", OUT_MERGE)
    print(f"selection@2000: {m['sel'][-1]:.1f} ms, insertion@2000 sorted/random/rev: "
          f"{m['ins_sorted'][-1]:.2f}/{m['ins_random'][-1]:.1f}/{m['ins_rev'][-1]:.1f} ms")
    print("big:", {n: tuple(round(x, 1) for x in v) for n, v in m["big"].items()})
    print("selection bugs:", sel_bugs)
    print("insertion bugs:", ins_bugs)
    print("merge bugs:", ms_bugs)


if __name__ == "__main__":
    build()
