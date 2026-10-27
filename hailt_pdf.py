"""
Хайлт: хоёр тусдаа хичээлийн PDF үүсгэгч (түвшин: хэрэгжүүлэх).

Ажиллуулах:  python hailt_pdf.py
Шаардлага:   pip install reportlab matplotlib numpy
Гаралт:      Hailt_1_Linear_search.pdf, Hailt_2_Binary_search.pdf (энэ файлтай нэг хавтсанд)
"""

import bisect
import io
import keyword
import os
import random
import re
import textwrap
import timeit

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

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_LINEAR = os.path.join(HERE, "Hailt_1_Linear_search.pdf")
OUT_BINARY = os.path.join(HERE, "Hailt_2_Binary_search.pdf")

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
# Өнгө (Big O хичээлтэй ижил палитр)
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

# Big O хичээлийн ангиллын өнгө: O(log n) = улбар шар, O(n) = ногоон
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
C_LINEAR = SERIES[2]
C_BINARY = SERIES[1]

# Зургийн нүднүүд
BOX_ACTIVE = "#d6e6fa"   # одоогийн хайх хүрээ / хараахан шалгаагүй
BOX_OFF = "#f0efec"      # хаягдсан / шалгагдсан
BOX_MID = ACCENT_DARK    # шалгаж буй элемент
BOX_FOUND = "#008300"    # олдсон

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
    return f'<font face="Consolas" color="{ACCENT_DARK}">{_esc(code)}</font>'


def bullets(items, style=st_bullet):
    return [Paragraph(t, style, bulletText="•") for t in items]


def numbered(items):
    return [Paragraph(t, st_bullet, bulletText=f"{i}.") for i, t in enumerate(items, 1)]


def fmt(v):
    return f"{v:,.0f}".replace(",", " ")


# ----------------------------------------------------------------------------
# Python кодын тодруулга
# ----------------------------------------------------------------------------
BUILTINS = {"print", "len", "range", "enumerate", "sorted", "list", "set",
            "random", "bisect", "bisect_left", "bisect_right", "insort",
            "reversed", "min", "max", "open"}
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


def code_block(src, width=CW, bg=CODE_BG, border=RULE, after=0):
    src = textwrap.dedent(src).strip("\n")
    t = Table([[XPreformatted(highlight(src), st_code)]], colWidths=[width],
              spaceAfter=after)
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


# ----------------------------------------------------------------------------
# Хичээлд гарах алгоритмууд (PDF-д харуулсан кодтой яг ижил)
# ----------------------------------------------------------------------------
def linear_search(items, target):
    for i in range(len(items)):
        if items[i] == target:
            return i
    return -1


def linear_search_last(items, target):
    for i in range(len(items) - 1, -1, -1):
        if items[i] == target:
            return i
    return -1


def find_all(items, target):
    result = []
    for i, x in enumerate(items):
        if x == target:
            result.append(i)
    return result


def first_failing(scores):
    for i, score in enumerate(scores):
        if score < 60:
            return i
    return -1


def reference(items, target):
    return items.index(target) if target in items else -1


# --- Linear search-ийн алдаатай хувилбарууд -----------------------------------
def lin_bug_else(items, target):                 # return -1 давталт дотор
    for i in range(len(items)):
        if items[i] == target:
            return i
        else:
            return -1


def lin_bug_value(items, target):                # индексийн оронд утга
    for x in items:
        if x == target:
            return x
    return -1


def lin_bug_skip_last(items, target):            # range(len(items) - 1)
    for i in range(len(items) - 1):
        if items[i] == target:
            return i
    return -1


def binary_search(items, target):
    lo, hi = 0, len(items) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if items[mid] == target:
            return mid
        elif items[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def binary_search_rec(items, target, lo=0, hi=None):
    if hi is None:
        hi = len(items) - 1
    if lo > hi:
        return -1
    mid = (lo + hi) // 2
    if items[mid] == target:
        return mid
    if items[mid] < target:
        return binary_search_rec(items, target, mid + 1, hi)
    return binary_search_rec(items, target, lo, mid - 1)


def first_occurrence(items, target):
    lo, hi = 0, len(items) - 1
    result = -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if items[mid] == target:
            result = mid
            hi = mid - 1
        elif items[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return result


def last_occurrence(items, target):
    lo, hi = 0, len(items) - 1
    result = -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if items[mid] == target:
            result = mid
            lo = mid + 1
        elif items[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return result


def lower_bound(items, target):
    lo, hi = 0, len(items)
    while lo < hi:
        mid = (lo + hi) // 2
        if items[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo


def binary_search_bisect(items, target):
    i = bisect.bisect_left(items, target)
    if i < len(items) and items[i] == target:
        return i
    return -1


def isqrt(n):
    lo, hi = 0, n
    ans = 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if mid * mid <= n:
            ans = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return ans


# --- Дасгалын хариу ----------------------------------------------------------
def count_occurrences(items, target):
    count = 0
    for x in items:
        if x == target:
            count += 1
    return count


def second_occurrence(items, target):
    seen = 0
    for i, x in enumerate(items):
        if x == target:
            seen += 1
            if seen == 2:
                return i
    return -1


def first_greater(items, x):
    for i, v in enumerate(items):
        if v > x:
            return i
    return -1


def count_in_range(items, a, b):
    return bisect.bisect_right(items, b) - bisect.bisect_left(items, a)


def closest(items, x):
    i = bisect.bisect_left(items, x)
    if i == 0:
        return items[0]
    if i == len(items):
        return items[-1]
    before, after = items[i - 1], items[i]
    return before if x - before <= after - x else after


# --- Binary search-ийн алдаатай хувилбарууд (тестээр илрүүлэхэд) ---------------
class Hang(Exception):
    pass


def bug_lt(items, target):                       # while lo < hi
    lo, hi = 0, len(items) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if items[mid] == target:
            return mid
        elif items[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def bug_lo_mid(items, target):                   # lo = mid
    lo, hi = 0, len(items) - 1
    for _ in range(200):
        if lo > hi:
            return -1
        mid = (lo + hi) // 2
        if items[mid] == target:
            return mid
        elif items[mid] < target:
            lo = mid
        else:
            hi = mid - 1
    raise Hang


def bug_hi_len(items, target):                   # hi = len(items)
    lo, hi = 0, len(items)
    while lo <= hi:
        mid = (lo + hi) // 2
        if items[mid] == target:
            return mid
        elif items[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def bug_float(items, target):                    # mid = (lo + hi) / 2
    lo, hi = 0, len(items) - 1
    while lo <= hi:
        mid = (lo + hi) / 2
        if items[mid] == target:
            return mid
        elif items[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


# ----------------------------------------------------------------------------
# Шалгалт ба хэмжилт (бодитоор ажиллуулна)
# ----------------------------------------------------------------------------
def self_check():
    """PDF-д бичсэн бүх үр дүнг энд баталгаажуулна."""
    # Linear
    nums = [7, 3, 9, 4, 1, 8]
    assert linear_search(nums, 4) == 3 and linear_search(nums, 5) == -1
    assert linear_search_last([5, 2, 5, 7, 5, 1], 5) == 4
    assert find_all([5, 2, 5, 7, 5, 1], 5) == [0, 2, 4]
    assert first_failing([88, 75, 54, 91, 42]) == 2
    assert lin_bug_else([7, 3, 9, 4], 9) == -1
    assert lin_bug_value([7, 3, 9, 4], 9) == 9
    assert lin_bug_skip_last([4, 6, 8], 8) == -1
    assert linear_search([2, 7, 2], 2) == 0
    assert count_occurrences([1, 2, 2, 5, 2], 2) == 3
    assert linear_search([5, 8, 2, 9, 2], 2) == 2 and linear_search([5, 8, 2, 9, 2], 7) == -1
    assert lin_bug_else([4, 6, 8], 8) == -1
    assert second_occurrence([5, 2, 5, 7, 5], 5) == 2 and second_occurrence([5, 2], 5) == -1
    assert first_greater([3, 9, 4, 12, 7], 5) == 1 and first_greater([1, 2], 5) == -1
    # Binary
    v16 = [2, 5, 8, 12, 16, 23, 38, 41, 56, 61, 67, 72, 80, 85, 91, 99]
    assert binary_search(v16, 67) == 10 and binary_search(v16, 40) == -1
    assert binary_search_rec(v16, 67) == 10 and binary_search_rec(v16, 40) == -1
    assert lower_bound(v16, 40) == 7
    d = [1, 3, 3, 3, 5, 8]
    assert binary_search(d, 3) == 2
    assert first_occurrence(d, 3) == 1 and last_occurrence(d, 3) == 3
    assert [lower_bound(d, t) for t in (3, 4, 9, 0)] == [1, 4, 6, 0]
    assert bisect.bisect_left(d, 3) == 1 and bisect.bisect_right(d, 3) == 4
    d2 = d.copy()
    bisect.insort(d2, 4)
    assert d2 == [1, 3, 3, 3, 4, 5, 8]
    assert isqrt(50) == 7 and isqrt(1_000_000) == 1000 and isqrt(0) == 0
    assert bug_lt([5], 5) == -1 and bug_lt([1, 3], 3) == -1
    try:
        bug_lo_mid([1, 3], 3)
        raise AssertionError("bug_lo_mid гацах ёстой")
    except Hang:
        pass
    for fn, exc in ((bug_hi_len, IndexError), (bug_float, TypeError)):
        try:
            fn([1, 3, 5], 9 if fn is bug_hi_len else 3)
            raise AssertionError(fn.__name__)
        except exc:
            pass
    assert binary_search([9, 2, 7, 4, 1], 9) == -1
    assert binary_search([3, 8, 15, 21, 30, 42, 57], 30) == 4
    assert count_in_range([1, 3, 3, 5, 8, 13], 3, 8) == 4
    assert closest([2, 5, 9, 14], 11) == 9 and closest([2, 5, 9, 14], 1) == 2
    assert closest([2, 5, 9, 14], 20) == 14


def test_edges_linear():
    assert linear_search([], 5) == -1
    assert linear_search([5], 5) == 0
    assert linear_search([5], 3) == -1
    assert linear_search([4, 6, 8], 4) == 0
    assert linear_search([4, 6, 8], 8) == 2
    assert linear_search([4, 6, 8], 7) == -1
    assert linear_search([2, 7, 2], 2) == 0


def test_edges_binary():
    assert binary_search([], 5) == -1
    assert binary_search([5], 5) == 0
    assert binary_search([5], 3) == -1
    assert binary_search([1, 3, 5, 7], 1) == 0
    assert binary_search([1, 3, 5, 7], 7) == 3
    assert binary_search([1, 3, 5, 7], 0) == -1
    assert binary_search([1, 3, 5, 7], 9) == -1
    assert binary_search([1, 3, 5, 7], 4) == -1
    assert binary_search([1, 3, 5], 5) == 2


def linear_cases(trials, seed=2026):
    rnd = random.Random(seed)
    return [([rnd.randint(0, 9) for _ in range(rnd.randint(0, 15))], rnd.randint(-2, 11))
            for _ in range(trials)]


def binary_cases(trials, seed=2026):
    rnd = random.Random(seed)
    cases = []
    for _ in range(trials):
        n = rnd.randint(0, 20)
        items = sorted(rnd.sample(range(50), n))
        target = rnd.randint(-5, 55)
        cases.append((items, target))
    return cases


def run_random_tests(trials=10_000):
    for items, target in linear_cases(trials):
        assert linear_search(items, target) == reference(items, target), (items, target)
    for items, target in binary_cases(trials):
        assert binary_search(items, target) == linear_search(items, target), (items, target)
        assert binary_search_rec(items, target) == linear_search(items, target)
        assert binary_search_bisect(items, target) == linear_search(items, target)
    return trials


def bug_report(fns, cases, expected):
    """Алдаатай хувилбар бүр санамсаргүй тестийн хэдэд нь бүтэлгүйтэхийг тоолно."""
    out = []
    for fn in fns:
        failed, first, kinds = 0, None, set()
        for k, (items, target) in enumerate(cases, 1):
            try:
                ok = fn(items, target) == expected(items, target)
                if not ok:
                    kinds.add("буруу хариу")
            except Hang:
                ok = False
                kinds.add("гацсан")
            except IndexError:
                ok = False
                kinds.add("IndexError")
            except TypeError:
                ok = False
                kinds.add("TypeError")
            if not ok:
                failed += 1
                first = first or k
        out.append((failed, first, kinds))
    return out


def measure_search():
    ns = [100_000 * i for i in range(1, 11)]
    t_lin, t_bin = [], []
    for n in ns:
        a = list(range(n))
        target = n  # байхгүй утга → хоёуланд нь хамгийн муу тохиолдол
        tl = min(timeit.repeat(lambda: linear_search(a, target), number=2, repeat=3)) / 2
        tb = min(timeit.repeat(lambda: binary_search(a, target), number=3000, repeat=5)) / 3000
        t_lin.append(tl * 1000)  # мс
        t_bin.append(tb * 1000)
    return ns, t_lin, t_bin


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
    if val != "":
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


def chart_linear_trace(vals, target):
    found = vals.index(target) if target in vals else None
    n_rows = (found + 1) if found is not None else len(vals)
    row_h = 1.3
    left, right = 3.2, 7.4
    fig, ax = _fig_for(left + len(vals) + right, n_rows * row_h + 0.55)
    _index_row(ax, len(vals))
    for r in range(n_rows):
        y = -r * row_h
        hit = r == found
        for i, v in enumerate(vals):
            if i < r:
                _box(ax, i, y, v, BOX_OFF, "#b3b2ac")
            elif i == r:
                _box(ax, i, y, v, BOX_FOUND if hit else BOX_MID, "white", bold=True)
            else:
                _box(ax, i, y, v, BOX_ACTIVE, INK)
        ax.text(-0.3, y + 0.5, f"{r + 1}-р алхам\ni = {r}", ha="right", va="center",
                fontsize=8.5, color=TEXT2, linespacing=1.25)
        if hit:
            note = f"{vals[r]} = {target}  → олдлоо, return {r}"
        elif found is None and r == n_rows - 1:
            note = f"{vals[r]} ≠ {target}  → дууслаа, return -1"
        else:
            note = f"{vals[r]} ≠ {target}  → дараагийнх руу"
        last = r == n_rows - 1
        ax.text(len(vals) + 0.35, y + 0.5, note, ha="left", va="center", fontsize=8.5,
                color=INK, fontweight="bold" if last else "normal")
    ax.set_xlim(-left, len(vals) + right)
    ax.set_ylim(-(n_rows - 1) * row_h - 0.05, 1.5)
    w = (left + len(vals) + right) * UNIT_IN
    return image_from_fig(fig, width=CW * min(1.0, w / 6.7))


def bs_steps(vals, target):
    steps = []
    lo, hi = 0, len(vals) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if vals[mid] == target:
            steps.append((lo, hi, mid, "found"))
            return steps, (lo, hi)
        if vals[mid] < target:
            steps.append((lo, hi, mid, "right"))
            lo = mid + 1
        else:
            steps.append((lo, hi, mid, "left"))
            hi = mid - 1
    return steps, (lo, hi)


def chart_binary_trace(vals, target):
    steps, (end_lo, end_hi) = bs_steps(vals, target)
    not_found = steps[-1][3] != "found"
    row_h = 1.85
    left, right = 3.4, 6.1
    n_rows = len(steps) + (1 if not_found else 0)
    fig, ax = _fig_for(left + len(vals) + right, n_rows * row_h + 0.2)
    _index_row(ax, len(vals))

    def pointers(y, marks):
        by_idx = {}
        for name, idx in marks:
            by_idx.setdefault(idx, []).append(name)
        for idx, names in by_idx.items():
            ax.text(idx + 0.5, y - 0.12, "↑", ha="center", va="top", fontsize=7.5, color=TEXT2)
            ax.text(idx + 0.5, y - 0.48, "=".join(names), ha="center", va="top",
                    fontsize=7.5, color=INK, fontweight="bold")

    for r, (lo, hi, mid, kind) in enumerate(steps):
        y = -r * row_h
        for i, v in enumerate(vals):
            if i == mid:
                _box(ax, i, y, v, BOX_FOUND if kind == "found" else BOX_MID, "white", bold=True)
            elif lo <= i <= hi:
                _box(ax, i, y, v, BOX_ACTIVE, INK)
            else:
                _box(ax, i, y, v, BOX_OFF, "#b3b2ac")
        pointers(y, [("lo", lo), ("mid", mid), ("hi", hi)])
        ax.text(-0.3, y + 0.5, f"{r + 1}-р эргэлт\n{hi - lo + 1} элемент", ha="right",
                va="center", fontsize=8.5, color=TEXT2, linespacing=1.25)
        m = vals[mid]
        if kind == "found":
            note = f"{m} = {target}  → return {mid}"
        elif kind == "right":
            note = f"{m} < {target}  → lo = {mid + 1}"
        else:
            note = f"{m} > {target}  → hi = {mid - 1}"
        ax.text(len(vals) + 0.35, y + 0.5, note, ha="left", va="center", fontsize=8.5,
                color=INK, fontweight="bold" if kind == "found" else "normal")

    if not_found:
        y = -len(steps) * row_h
        for i, v in enumerate(vals):
            _box(ax, i, y, v, BOX_OFF, "#b3b2ac")
        pointers(y, [("hi", end_hi), ("lo", end_lo)])
        ax.plot([end_lo, end_lo], [y - 0.05, y + 1.05], color=C_BINARY, lw=2,
                solid_capstyle="round")
        ax.text(-0.3, y + 0.5, "Давталт\nдуусав", ha="right", va="center", fontsize=8.5,
                color=TEXT2, linespacing=1.25)
        ax.text(len(vals) + 0.35, y + 0.5, f"lo > hi  → return -1\n({target}-ийн байр = {end_lo})",
                ha="left", va="center", fontsize=8.5, color=INK, fontweight="bold",
                linespacing=1.3)

    ax.set_xlim(-left, len(vals) + right)
    ax.set_ylim(-(n_rows - 1) * row_h - 0.75, 1.5)
    return image_from_fig(fig)


def chart_ranges():
    """[lo, hi] ба [lo, hi) хоёр загварын эхлэх төлөв."""
    vals = [1, 3, 3, 3, 5, 8]
    left, right = 6.2, 6.3
    row_h = 2.15
    fig, ax = _fig_for(left + len(vals) + 1 + right, 2 * row_h + 0.25)
    rows = [
        ("Хаалттай [lo, hi]\nbinary_search", 0, len(vals) - 1, False,
         "hi = len − 1 = 5\nwhile lo <= hi"),
        ("Хагас нээлттэй [lo, hi)\nlower_bound", 0, len(vals), True,
         "hi = len = 6 (гадна)\nwhile lo < hi"),
    ]
    for r, (label, lo, hi, half_open, note) in enumerate(rows):
        y = -r * row_h
        for i, v in enumerate(vals):
            _box(ax, i, y, v, BOX_ACTIVE, INK)
        if half_open:
            _box(ax, len(vals), y, "", None, None, dashed=True)
        for name, idx in (("lo", lo), ("hi", hi)):
            ax.text(idx + 0.5, y - 0.12, "↑", ha="center", va="top", fontsize=7.5, color=TEXT2)
            ax.text(idx + 0.5, y - 0.48, name, ha="center", va="top", fontsize=7.5,
                    color=INK, fontweight="bold")
        ax.text(-0.3, y + 0.5, label, ha="right", va="center", fontsize=8.5,
                color=INK, linespacing=1.3)
        ax.text(len(vals) + 1.35, y + 0.5, note, ha="left", va="center", fontsize=8.5,
                color=TEXT2, linespacing=1.3, family="Consolas")
    ax.set_xlim(-left, len(vals) + 1 + right)
    ax.set_ylim(-row_h - 0.8, 1.05)
    w = (left + len(vals) + 1 + right) * UNIT_IN
    return image_from_fig(fig, width=CW * min(1.0, w / 6.7))


def chart_linear_timing(ns, t_lin):
    """Ганц цуваа: legend шаардлагагүй, гарчиг нь нэрлэнэ."""
    x = [v / 1000 for v in ns]
    fig, ax = plt.subplots(figsize=(6.7, 3.0))
    fig.subplots_adjust(left=0.09, right=0.80, top=0.94, bottom=0.17)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.plot(x, t_lin, color=C_LINEAR, lw=2, marker="o", ms=6, mec=SURFACE, mew=1.2)
    ax.set_xlim(0, 1050)
    ax.set_ylim(0, max(t_lin) * 1.15)
    ax.set_xticks([0, 200, 400, 600, 800, 1000])
    ax.set_xlabel("n — элементийн тоо (мянгаар)")
    ax.set_ylabel("Нэг хайлтын хугацаа (мс)")
    for k in (4, 9):  # 500 мянга ба 1 сая
        ax.annotate(f"{t_lin[k]:.1f} мс", (x[k], t_lin[k]), xytext=(-8, 10),
                    textcoords="offset points", ha="right", fontsize=8.5, color=INK,
                    fontweight="bold")
    ax.text(1070, t_lin[-1], "linear_search\nO(n)", color=INK, fontsize=9,
            fontweight="bold", va="center", clip_on=False)
    return image_from_fig(fig)


def chart_timing(ns, t_lin, t_bin):
    x = [v / 1000 for v in ns]
    fig, ax = plt.subplots(figsize=(6.7, 3.2))
    fig.subplots_adjust(left=0.09, right=0.78, top=0.94, bottom=0.16)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.plot(x, t_lin, color=C_LINEAR, lw=2, marker="o", ms=6, mec=SURFACE,
            mew=1.2, label="linear_search")
    ax.plot(x, t_bin, color=C_BINARY, lw=2, marker="o", ms=6, mec=SURFACE,
            mew=1.2, label="binary_search")
    ax.set_xlim(0, 1050)
    ax.set_ylim(0, max(t_lin) * 1.12)
    ax.set_xticks([0, 200, 400, 600, 800, 1000])
    ax.set_xlabel("n — элементийн тоо (мянгаар)")
    ax.set_ylabel("Нэг хайлтын хугацаа (мс)")
    ax.text(1070, t_lin[-1], f"linear_search\nO(n) · {t_lin[-1]:.1f} мс",
            color=INK, fontsize=9, fontweight="bold", va="center", clip_on=False)
    ax.text(1070, max(t_lin) * 0.07, f"binary_search\nO(log n) · ≈{t_bin[-1] * 1000:.1f} мкс",
            color=INK, fontsize=9, fontweight="bold", va="center", clip_on=False)
    ax.legend(loc="upper left", frameon=False, fontsize=8.5)
    return image_from_fig(fig)


# ----------------------------------------------------------------------------
# Хуудасны чимэглэл
# ----------------------------------------------------------------------------
BAND_H = 300
DECO_N = 16


def _deco_grid(canv, rows_colors, labels=None):
    """Нүүрний баруун талын нүднүүд: rows_colors[r][i] = өнгө."""
    x0, x1 = PAGE_W * 0.585, PAGE_W - 34
    cell = (x1 - x0) / DECO_N
    gap = 2.2
    y_top = PAGE_H - 58
    row_step = (BAND_H - 92) / (len(rows_colors) - 1)
    for r, colors in enumerate(rows_colors):
        y = y_top - r * row_step
        for i, col in enumerate(colors):
            canv.setFillColor(HexColor(col))
            canv.roundRect(x0 + i * cell + gap / 2, y - cell + gap / 2,
                           cell - gap, cell - gap, 2.2, stroke=0, fill=1)
        if labels and labels.get(r):
            canv.setFillColor(HexColor("#9ec5f4"))
            canv.setFont("Arial", 8)
            canv.drawRightString(x0 - 8, y - cell + 3, labels[r])


def deco_linear(canv):
    # Зүүнээс баруун тийш нэг бүрчлэн: шалгасан (бүдэг) → одоогийнх (цэнхэр) → олдсон (ногоон)
    rows = []
    for k in (0, 3, 6, 9, 11):
        row = []
        for i in range(DECO_N):
            if i < k:
                row.append("#34445f")
            elif i == k:
                row.append("#3fae6e" if k == 11 else "#3987e5")
            else:
                row.append("#22314a")
        rows.append(row)
    _deco_grid(canv, rows, {0: "i = 0", 4: "i = 11"})


def deco_binary(canv):
    # 16 нүднээс хагасаар нарийссаар 1 нүд үлдэх
    hits = [(0, 15), (8, 15), (8, 11), (10, 11), (10, 10)]
    rows = []
    for r, (lo, hi) in enumerate(hits):
        rows.append([("#3fae6e" if r == len(hits) - 1 else "#3987e5") if lo <= i <= hi
                     else "#22314a" for i in range(DECO_N)])
    _deco_grid(canv, rows, {0: "16", 4: "1"})


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
        canv.setFont("Arial-Bold", 58)
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
        canv.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 12 * mm, "Түвшин: Хэрэгжүүлэх")
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
    chips = Table([[P("<b>Түвшин:</b> Хэрэгжүүлэх", chip_style),
                    P("<b>Жишээ:</b> Python 3", chip_style),
                    P(f"<b>Урьдчилсан мэдлэг:</b> {prereq}", chip_style)]],
                  colWidths=[CW * 0.27, CW * 0.21, CW * 0.48], hAlign="LEFT")
    chips.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(HEAD_BG)),
        ("ROUNDEDCORNERS", [10, 10, 10, 10]),
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


def linear_trace_table(rows, target, final_color):
    header = ["i", "items[i]", f"items[i] == {target} ?", "Юу болох вэ"]
    return KeepTogether([data_table([header] + rows, [CW * 0.1, CW * 0.16, CW * 0.24, CW * 0.5],
                                    center_cols=(0, 1, 2), row_bg={len(rows): final_color})])


def binary_trace_table(rows, final_color):
    header = ["Эргэлт", "lo", "hi", "mid", "items[mid]", "Харьцуулалт", "Үйлдэл"]
    widths = [0.11, 0.08, 0.08, 0.08, 0.15, 0.22, 0.28]
    return KeepTogether([data_table([header] + rows, [CW * w for w in widths],
                                    center_cols=(0, 1, 2, 3, 4),
                                    row_bg={len(rows): final_color})])


def bug_table(names, results, ok_name):
    rows = [["Хувилбар", "1 000 тестээс бүтэлгүйтсэн", "Анхны алдаа", "Алдааны төрөл"]]
    for name, (failed, first, kinds) in zip(names, results):
        rows.append([P(name, st_cell), f"<b>{failed}</b>", f"{first}-р тест",
                     ", ".join(sorted(kinds))])
    rows.append([P(ok_name, st_cell), "<b>0</b>", "—", "—"])
    return data_table(rows, [CW * 0.34, CW * 0.24, CW * 0.16, CW * 0.26], center_cols=(1, 2),
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


# ============================================================================
# ХИЧЭЭЛ 1: LINEAR SEARCH
# ============================================================================
def build_linear(ns, t_lin, n_tests):
    lin_bugs = bug_report([lin_bug_else, lin_bug_value, lin_bug_skip_last],
                          linear_cases(1000), reference)
    s = front_page(
        "list, for давталт, функц",
        [
            "Linear search-ийг <b>өөрөө бичиж</b>, мөр бүр юу хийдгийг тайлбарлана.",
            "Кодоо цаасан дээр <b>мөрдөж</b> (trace), алхам бүрийг хүснэгтээр гаргана.",
            "Linear search-ийн <b>3 түгээмэл алдааг</b> таньж засна.",
            "Сүүлийн тохиолдол, бүх байрлал, нөхцөлөөр хайх гэх мэт <b>хувилбаруудыг</b> бичнэ.",
            "Кодоо <b>тестээр</b> шалгаж, linear search-ийг хэзээ хэрэглэх, хэзээ хэрэглэхгүйг мэднэ.",
        ],
        ["Хайлтын бодлого", "Санаа ба код", "Гараар мөрдөх", "Түгээмэл алдаа",
         "Хэр хурдан бэ?", "Хувилбарууд", "Тестлэх", "Хэзээ хэрэглэх вэ?",
         "Дасгал", "Хураангуй"],
        "Нэг өгүүлбэрээр",
        ["<b>Linear search</b> (шугаман хайлт): жагсаалтыг эхнээс нь нэг бүрчлэн хар, олдмогц зогс; "
         "бүгдийг хараад олдоогүй бол — байхгүй."],
    )

    # ------------------------------------------------------------- 1
    s += section(1, "Хайлтын бодлого")
    s.append(P("Хайлт гэдэг нь цуглуулгаас тодорхой нэг утгыг олох бодлого. Бичихээсээ өмнө функц "
               "юу авч, юу буцаахыг тохиролцъё — үүнийг функцийн <b>гэрээ</b> (contract) гэдэг:"))
    s.append(data_table([
        ["", "Тайлбар", "Жишээ"],
        [P("<b>Оролт</b>", st_cell), f"{c('items')} — жагсаалт; {c('target')} — хайж буй утга",
         P(c("items = [7, 3, 9, 4]"), st_cell)],
        [P("<b>Олдвол</b>", st_cell), f"{c('target')}-ийн <b>индекс</b> (0-ээс эхэлж тоолно)",
         P(c("search(items, 9)  →  2"), st_cell)],
        [P("<b>Олдохгүй бол</b>", st_cell), P(f"{c('-1')}", st_cell),
         P(c("search(items, 5)  →  -1"), st_cell)],
    ], [CW * 0.18, CW * 0.44, CW * 0.38]))
    s.append(Spacer(1, 10))
    s.append(callout("Яагаад −1 вэ?",
                     "Жинхэнэ индекс 0, 1, 2, … гэж үргэлж 0 ба түүнээс их байдаг. Тиймээс −1 хэзээ ч жинхэнэ "
                     "индекстэй андуурагдахгүй — «олдсонгүй» гэдгийг илэрхийлэхэд тохиромжтой. Python-ий "
                     f"{c('str.find()')} яг ингэж −1 буцаадаг бол {c('list.index()')} олдохгүй үед "
                     f"{c('ValueError')} алдаа шиддэг."))
    s.append(warn("Анхаар: Python-д items[-1] бол сүүлийн элемент",
                  f"Буцсан утгыг шалгалгүй {c('items[idx]')} гэж хэрэглэвэл олдоогүй үед ч алдаа гарахгүй, "
                  f"чимээгүйхэн <b>сүүлийн</b> элементийг авна. Үргэлж {c('if idx != -1:')} гэж шалгаарай."))

    # ------------------------------------------------------------- 2
    s += section(2, "Санаа ба код", need=330)
    s.append(P("<b>Зүйрлэл:</b> 6 шүүгээний алинд нь түлхүүрээ хийснээ мартжээ. Шүүгээг зүүнээс нь "
               "нэг нэгээр онгойлгоно: олдвол тэр даруй зогсоно. Бүгдийг онгойлгоод олдохгүй бол — "
               "түлхүүр шүүгээнд <b>байхгүй</b> гэсэн үг."))
    s.append(figure(chart_linear_trace([7, 3, 9, 4, 1, 8], 4),
                    "Зураг 1. [7, 3, 9, 4, 1, 8] жагсаалтаас 4-ийг хайх нь. Хар хөх — одоо шалгаж буй, "
                    "саарал — аль хэдийн шалгасан, цайвар хөх — хараахан шалгаагүй. 4 алхамд олдлоо."))
    s.append(P("Алхам алхмаар бичье", st_h2))
    s.append(step(1, f"Индекс бүрээр давтана: {c('for i in range(len(items)):')}"))
    s.append(step(2, f"Тухайн элементийг хайж буй утгатай харьцуулна: {c('if items[i] == target:')}"))
    s.append(step(3, f"Таарвал индексийг <b>тэр даруй</b> буцаана: {c('return i')} — функц шууд "
                     "дуусна, үлдсэнийг харахгүй."))
    s.append(step(4, f"Давталт бүтэн дуусвал (бүгдийг харсан, олдоогүй) {c('return -1')} — "
                     "давталтын <b>гадна</b>!"))
    s.append(Spacer(1, 6))
    s.append(code("""
        def linear_search(items, target):
            for i in range(len(items)):     # 1. индекс бүрээр давтана
                if items[i] == target:      # 2. харьцуулна
                    return i                # 3. олдлоо → шууд гарна
            return -1                       # 4. бүгдийг харсан, олдсонгүй

        nums = [7, 3, 9, 4, 1, 8]
        print(linear_search(nums, 4))       # 3
        print(linear_search(nums, 5))       # -1
    """))
    s.append(P(f"Python-д илүү түгээмэл бичиглэл бол {c('enumerate')} — индекс ба утгыг зэрэг өгдөг. "
               "Үр дүн нь яг ижил:"))
    s.append(code("""
        def linear_search(items, target):
            for i, x in enumerate(items):   # i — индекс, x — утга
                if x == target:
                    return i
            return -1
    """))
    s.append(callout("Яагаад индекс буцаадаг вэ?",
                     "Утга нь бидэнд аль хэдийн байгаа — target-ийг өөрөө өгсөн. Харин <b>хаана</b> байгаа нь "
                     f"шинэ мэдээлэл: индексээр нь тэр элементийг өөрчлөх ({c('items[i] = ...')}), устгах "
                     f"({c('del items[i]')}), хөршийг нь харах ({c('items[i + 1]')}) боломжтой."))

    # ------------------------------------------------------------- 3
    s += section(3, "Гараар мөрдөх (trace)", need=300)
    s.append(P("Код бичсэний дараах хамгийн сайн шалгалт бол цаасан дээр <b>мөрдөх</b>: хүснэгт зурж, "
               "давталтын эргэлт бүрт хувьсагчдын утгыг бичнэ. Хоёр тохиолдлыг мөрдье."))
    s.append(P(f"Тохиолдол 1: {c('linear_search([7, 3, 9, 4, 1, 8], 4)')} — олдоно", st_h2))
    s.append(linear_trace_table([
        ["0", "7", "False", "дараагийн эргэлт рүү"],
        ["1", "3", "False", "дараагийн эргэлт рүү"],
        ["2", "9", "False", "дараагийн эргэлт рүү"],
        ["3", "4", "<b>True</b>", f"<b>{c('return 3')}</b> — функц дуусна"],
    ], 4, OK_ROW))
    s.append(Spacer(1, 4))
    s.append(P("4 харьцуулалт хийлээ. 1, 8 гэсэн үлдсэн элементийг <b>огт хараагүй</b> — "
               f"{c('return')} функцийг шууд дуусгадаг."))
    s.append(figure(chart_linear_trace([7, 3, 9, 4], 5),
                    "Зураг 2. [7, 3, 9, 4] жагсаалтаас 5-ыг хайх нь. Бүх элементийг шалгаж дуусаад л "
                    "−1 буцаана.",
                    head=f"Тохиолдол 2: {c('linear_search([7, 3, 9, 4], 5)')} — байхгүй"))
    s.append(linear_trace_table([
        ["0", "7", "False", "дараагийн эргэлт рүү"],
        ["1", "3", "False", "дараагийн эргэлт рүү"],
        ["2", "9", "False", "дараагийн эргэлт рүү"],
        ["3", "4", "False", "давталт дууслаа"],
        ["—", "", "", f"<b>{c('return -1')}</b> — давталтын дараах мөр"],
    ], 5, MISS_ROW))
    s.append(Spacer(1, 8))
    s.append(callout("Зөвлөгөө: компьютерээр мөрдүүлэх",
                     [f"Давталт дотор нэг мөр {c('print')} нэмбэл хүснэгтийг Python өөрөө хэвлэнэ. "
                      "Код буруу ажиллаж байвал хамгийн түрүүнд үүнийг хий:",
                      Spacer(1, 4),
                      code_block("""
                          for i in range(len(items)):
                              print(f"i={i}  items[i]={items[i]}  тэнцүү юу: {items[i] == target}")
                              ...
                      """, width=CW - 28)]))

    # ------------------------------------------------------------- 4
    s += section(4, "Түгээмэл алдаа", need=300)
    s.append(P("Linear search ердөө 4 мөр ч эхлэгчид доорх 3 алдааг байнга гаргадаг. Бүгдийг нь "
               "бодитоор ажиллуулж шалгав."))
    s.append(bug_card(
        1, "return -1-ийг давталт дотор бичих",
        """
        for i in range(len(items)):
            if items[i] == target:
                return i
            else:
                return -1
        """,
        """
        for i in range(len(items)):
            if items[i] == target:
                return i
        return -1
        """,
        f"{c('linear_search([7, 3, 9, 4], 9)')} → <b>−1</b>, гэтэл 9 индекс 2-т байна!",
        "Эхний элемент 7 ≠ 9 болмогц else салаа ажиллаж функц дуусчихна — бусад элементийг огт "
        "харахгүй. «Олдсонгүй» гэж зөвхөн <b>бүгдийг</b> харсны дараа хэлж болно."))
    s.append(bug_card(
        2, "Индексийн оронд утга буцаах",
        """
        for x in items:
            if x == target:
                return x
        return -1
        """,
        """
        for i, x in enumerate(items):
            if x == target:
                return i
        return -1
        """,
        f"{c('linear_search([7, 3, 9, 4], 9)')} → <b>9</b> (индекс 2 биш).",
        f"{c('x')} нь утга, индекс биш. Буцаасан 9 нь бидний аль хэдийн мэдэх target өөрөө — "
        f"ямар ч шинэ мэдээлэл өгөхгүй. Индекс хэрэгтэй бол {c('enumerate')} эсвэл {c('range(len(items))')}."))
    s.append(bug_card(
        3, "Сүүлийн элементийг алгасах",
        """
        for i in range(len(items) - 1):
            ...
        """,
        """
        for i in range(len(items)):
            ...
        """,
        f"{c('linear_search([4, 6, 8], 8)')} → <b>−1</b>.",
        f"{c('range(n)')} нь 0, 1, …, n−1 гэж аль хэдийн <b>сүүлийн индекс хүртэл</b> гүйдэг. "
        f"{c('- 1')} нэмбэл сүүлийн элемент (индекс 2) шалгагдахгүй. Ийм «нэгээр зөрөх» "
        "(off-by-one) алдаа маш түгээмэл."))

    # ------------------------------------------------------------- 5
    s += section(5, "Хэр хурдан бэ?", need=300)
    s.append(P("Хурдыг секундээр биш, <b>харьцуулалтын тоогоор</b> хэмжье. n элементтэй жагсаалтад:"))
    s.append(data_table([
        ["Тохиолдол", "Хэзээ", "Харьцуулалт", "Big O"],
        ["Хамгийн сайн", "target эхний байранд", "1", "O(1)"],
        ["Дундаж", "target санамсаргүй байранд", "≈ n / 2", "O(n)"],
        ["Хамгийн муу", "target сүүлд эсвэл <b>байхгүй</b>", "n", "<b>O(n)</b>"],
        ["Санах ой", "хэдхэн хувьсагч (i)", "—", "O(1)"],
    ], [CW * 0.2, CW * 0.38, CW * 0.2, CW * 0.22], zebra=True))
    s.append(Spacer(1, 6))
    s.append(P("Big O нь ихэвчлэн <b>хамгийн муу</b> тохиолдлыг хэлдэг тул linear search бол <b>O(n)</b>: "
               "жагсаалт 2 дахин томорвол ажил 2 дахин нэмэгдэнэ. Бодитоор хэмжиж шалгая — 100 000 … "
               "1 000 000 элементтэй жагсаалтаас <b>байхгүй</b> утга хайлгав (хамгийн муу тохиолдол):"))
    s.append(figure(chart_linear_timing(ns, t_lin),
                    "Зураг 3. linear_search-ийн нэг хайлтын хугацаа. Энэ PDF-ийг үүсгэх үед бодитоор "
                    "хэмжсэн (хэд хэдэн давталтын хамгийн бага утга). Таны компьютер дээр тоо нь өөр "
                    "гарах ч хэлбэр нь ижил — шулуун шугам."))
    s.append(P(f"500 000 элементэд <b>{t_lin[4]:.1f} мс</b>, 1 000 000 элементэд <b>{t_lin[9]:.1f} мс</b> — "
               f"бараг яг <b>{t_lin[9] / t_lin[4]:.1f} дахин</b>. Энэ бол O(n)-ийн «n 2 дахин → ажил 2 дахин» "
               "гэдгийн бодит нотолгоо."))

    # ------------------------------------------------------------- 6
    s += section(6, "Хувилбарууд", need=250)
    s.append(P("«Давт → шалга → буцаа» гэсэн загварыг бага зэрэг өөрчлөөд олон бодлого бодож болно. "
               "Өөрчлөгдсөн хэсгийг тайлбараар тэмдэглэв."))
    s.append(P("а) Сүүлийн тохиолдлыг олох", st_h2))
    s.append(code("""
        def linear_search_last(items, target):
            for i in range(len(items) - 1, -1, -1):   # ← араас нь урагш: n-1, n-2, …, 0
                if items[i] == target:
                    return i
            return -1

        linear_search_last([5, 2, 5, 7, 5, 1], 5)     # 4
    """))
    s.append(P(f"{c('range(start, stop, step)')}: {c('stop')} өөрөө орохгүй тул 0 хүртэл явахын тулд "
               f"{c('-1')} гэж бичнэ.", st_small))
    s.append(P("б) Бүх байрлалыг олох", st_h2))
    s.append(code("""
        def find_all(items, target):
            result = []                     # ← олдсон бүрийг цуглуулна
            for i, x in enumerate(items):
                if x == target:
                    result.append(i)        # ← буцаахгүй, үргэлжлүүлнэ
            return result                   # олдоогүй бол хоосон жагсаалт []

        find_all([5, 2, 5, 7, 5, 1], 5)     # [0, 2, 4]
    """))
    s.append(P("в) Нөхцөлөөр хайх", st_h2))
    s.append(P("Тэнцүү байхыг биш, <b>ямар нэг нөхцөл</b> хангахыг шалгаж болно — энэ бол linear search-ийн "
               "том давуу тал (binary search үүнийг ерөнхий тохиолдолд чадахгүй)."))
    s.append(code("""
        def first_failing(scores):
            for i, score in enumerate(scores):
                if score < 60:              # ← == биш, дурын нөхцөл
                    return i
            return -1

        first_failing([88, 75, 54, 91, 42])   # 2
    """))
    s.append(P("г) Объектын жагсаалтаас хайх", st_h2))
    s.append(code("""
        students = [
            {"name": "Бат", "score": 88},
            {"name": "Сараа", "score": 95},
            {"name": "Тэмүүлэн", "score": 72},
        ]

        def find_student(students, name):
            for s in students:
                if s["name"] == name:       # ← зөвхөн нэрээр нь харьцуулна
                    return s                # индекс биш, объектыг өөрийг нь буцаалаа
            return None                     # олдоогүй: объект буцаадаг үед None нь тохиромжтой

        find_student(students, "Сараа")     # {'name': 'Сараа', 'score': 95}
    """))
    s.append(P("д) Файлаас хайх", st_h2))
    s.append(P("Linear search-д индексээр «үсрэх» шаардлагагүй, зөвхөн дарааллаар нь уншихад л хангалттай. "
               "Тиймээс бүхэлд нь санах ойд ачаалахгүйгээр том файлаас ч хайж чадна:"))
    s.append(code("""
        def find_line(path, word):
            with open(path, encoding="utf-8") as f:
                for no, line in enumerate(f, 1):    # мөрийг нэг нэгээр уншина, 1-ээс дугаарлана
                    if word in line:
                        return no
            return -1
    """))
    s.append(P("Python-д бэлэн байгаа linear search-үүд", st_h2))
    s.append(data_table([
        ["Код", "Буцаах утга", "Цаг"],
        [P(c("x in items"), st_cell), "True / False", "O(n)"],
        [P(c("items.index(x)"), st_cell), f"эхний индекс; олдохгүй бол {c('ValueError')}", "O(n)"],
        [P(c("items.count(x)"), st_cell), "хэдэн удаа байгаа (үргэлж бүгдийг харна)", "O(n)"],
    ], [CW * 0.3, CW * 0.52, CW * 0.18], zebra=True))
    s.append(Spacer(1, 6))
    s.append(callout("Санамж",
                     "Эдгээр нь дотроо яг манай давталтыг хийдэг. Тиймээс давталт дотор "
                     f"{c('x in list')} бичвэл нийтдээ <b>O(n²)</b> болно (Big O хичээлийн «нуугдмал давталт»)."))

    # ------------------------------------------------------------- 7
    s += section(7, "Тестлэх", need=300)
    s.append(P("«Ажиллаж байх шиг байна» гэж орхиж болохгүй — 4-р бүлгийн алдаанууд зарим жишээн дээр "
               "зөв хариу өгдөг! Хоёр төрлийн тест бичье."))
    s.append(P("1. Захын тохиолдлууд (edge cases)", st_h2))
    s.append(P("Алдаа ихэвчлэн хил дээр нуугддаг: хоосон, ганц элемент, эхний ба сүүлийн байр."))
    s.append(code("""
        def test_edges():
            assert linear_search([], 5) == -1           # хоосон жагсаалт
            assert linear_search([5], 5) == 0           # ганц элемент, байгаа
            assert linear_search([5], 3) == -1          # ганц элемент, байхгүй
            assert linear_search([4, 6, 8], 4) == 0     # эхний элемент
            assert linear_search([4, 6, 8], 8) == 2     # сүүлийн элемент  ← алдаа 1, 3 энд баригдана
            assert linear_search([4, 6, 8], 7) == -1    # байхгүй
            assert linear_search([2, 7, 2], 2) == 0     # давхардсан → ЭХНИЙХ
            print("Захын тохиолдлууд: OK")
    """))
    s.append(P(f"{c('assert')} нь нөхцөл худал бол {c('AssertionError')} шиднэ, үнэн бол юу ч хийхгүй."))
    s.append(P("2. Санамсаргүй тест: бэлэн функцтэй харьцуулах", st_h2))
    s.append(P(f"Python-ий {c('in')} ба {c('index')}-ээр «зөв хариу» гаргаж, мянга мянган санамсаргүй "
               "жагсаалт дээр өөрийн функцтэйгээ харьцуулна:"))
    s.append(code("""
        import random

        def reference(items, target):           # бэлэн функцээр «зөв хариу»
            return items.index(target) if target in items else -1

        def test_random(trials=10_000):
            for _ in range(trials):
                items = [random.randint(0, 9) for _ in range(random.randint(0, 15))]
                target = random.randint(-2, 11)  # заримдаа байхгүй утга
                assert linear_search(items, target) == reference(items, target), \\
                    (items, target)              # бүтэлгүйтвэл жишээг хэвлэнэ
            print(trials, "санамсаргүй тест: OK")
    """))
    names = [f"Алдаа 1: {c('else: return -1')}", f"Алдаа 2: {c('return x')}",
             f"Алдаа 3: {c('range(len(items) - 1)')}"]
    s.append(KeepTogether([
        P(f"Энэ PDF-ийг үүсгэх үед зөв хувилбарыг <b>{fmt(n_tests)}</b> санамсаргүй тестээр шалгахад бүгд "
          "амжилттай давлаа. Харин 4-р бүлгийн алдаатай хувилбаруудыг ижил тестэд оруулахад:"),
        bug_table(names, lin_bugs, f"Зөв {c('linear_search')}"),
    ]))
    s.append(Spacer(1, 8))
    rare = lin_bugs[2]
    s.append(KeepTogether([P(
        f"Анхаар: 3-р алдаа 1 000 тестээс ердөө <b>{rare[0]}</b>-д илэрсэн — target <b>зөвхөн "
        "сүүлийн</b> байранд байх үед л буруу ажилладаг. Ийм ховор алдааг санамсаргүй тест олохгүй "
        "өнгөрч болох тул захын тохиолдлын тест («сүүлийн элемент») заавал хэрэгтэй.")]))
    s.append(callout("Дүгнэлт",
                     "Захын тохиолдлын тест + бэлэн функцтэй харьцуулах санамсаргүй тест = хэрэгжүүлэлтдээ "
                     f"итгэх хамгийн хялбар арга. Алдаа бүр эхний {max(b[1] for b in lin_bugs)} тестийн "
                     "дотор илэрсэн."))

    # ------------------------------------------------------------- 8
    s += section(8, "Хэзээ хэрэглэх вэ?", need=300)
    s.append(data_table([
        ["Давуу тал", "Сул тал"],
        ["Ямар ч жагсаалт дээр ажиллана — <b>эрэмбэлэх шаардлагагүй</b>",
         "Том жагсаалтад удаан: сая элементэд сая хүртэл харьцуулалт"],
        ["Дурын нөхцөлөөр хайж чадна (эхний тэгш тоо, 60-аас бага оноо…)",
         "Олон удаа хайхад ажил нь давтагдсаар байна: k хайлт → k · n"],
        ["Файл, генератор гэх мэт зөвхөн дарааллаар уншдаг өгөгдөлд тохирно", ""],
        ["4 мөр — алдаа гаргахад хэцүү, уншихад амархан", ""],
    ], [CW * 0.5, CW * 0.5]))
    s.append(P("Шийдвэрийн жагсаалт", st_h2))
    s += numbered([
        "Жагсаалт <b>жижиг</b> (хэдэн арав, хэдэн зуу) эсвэл <b>ганцхан удаа</b> хайх уу? → "
        "<b>Linear search</b>. Энгийн, хангалттай хурдан.",
        "<b>Дурын нөхцөлөөр</b> хайх уу? → <b>Linear search</b>.",
        "Өгөгдөл <b>файл, сүлжээ</b> зэргээс дарааллаар ирж байна уу? → <b>Linear search</b>.",
        f"Зөвхөн «байгаа юу?» гэж <b>олон удаа</b> асуух уу? → {c('set')} эсвэл {c('dict')}: дунджаар O(1) "
        "(Big O хичээлийн 5-р бүлэг).",
        "<b>Эрэмбэлэгдсэн</b> том жагсаалтаас олон удаа хайх уу? → <b>Binary search</b> — дараагийн хичээл.",
    ])
    s.append(callout("Дараагийн алхам: Binary search",
                     "Утасны дэвтрийг эхний хуудаснаас нь нэг бүрчлэн уншдаггүй — дундаас нь нээгээд хагасыг "
                     "нь хаядаг. Жагсаалт <b>эрэмбэлэгдсэн</b> бол яг ингэж сая элементээс <b>20</b> алхамд "
                     "олж болно. Энэ бол «Хайлт 2/2: Binary search» хичээлийн сэдэв."))

    # ------------------------------------------------------------- 9
    s += section(9, "Дасгал", need=180)
    s.append(P("Эхлээд өөрөө бодож, кодоо 7-р бүлгийн аргаар тестлээрэй. Хариуг дараагийн хуудаснаас шалга."))
    s.append(exercise_card(
        1, "Тоолох",
        f"{c('count_occurrences(items, target)')} функц бич: target хэдэн удаа байгааг буцаана. "
        f"{c('count()')} хэрэглэхгүй. Цагийн төвөгшил нь хэд вэ?",
        "count_occurrences([1, 2, 2, 5, 2], 2)    # 3"))
    s.append(exercise_card(
        2, "Гараар мөрдөх",
        f"{c('linear_search([5, 8, 2, 9, 2], 2)')} ба {c('linear_search([5, 8, 2, 9, 2], 7)')} хоёрыг "
        f"3-р бүлгийн хүснэгтээр мөрд. Тус бүр хэдэн харьцуулалт хийж, юу буцаах вэ?"))
    s.append(exercise_card(
        3, "Алдааг ол",
        f"Доорх код {c('linear_search([4, 6, 8], 8)')}-д юу буцаах вэ? Яагаад? Хэрхэн засах вэ?",
        """
        def linear_search(items, target):
            for i in range(len(items)):
                if items[i] == target:
                    return i
                else:
                    return -1
        """))
    s.append(exercise_card(
        4, "Хоёр дахь тохиолдол",
        f"{c('second_occurrence(items, target)')}: target-ийн <b>хоёр дахь</b> удаа гарсан индексийг "
        "буцаа, тийм байхгүй бол −1.",
        """
        second_occurrence([5, 2, 5, 7, 5], 5)    # 2
        second_occurrence([5, 2], 5)             # -1
        """))
    s.append(exercise_card(
        5, "Нөхцөлөөр хайх",
        f"{c('first_greater(items, x)')}: x-ээс <b>их</b> эхний элементийн индексийг буцаа (жагсаалт "
        "эрэмбэгүй байж болно).",
        """
        first_greater([3, 9, 4, 12, 7], 5)    # 1   (9 > 5)
        first_greater([1, 2], 5)              # -1
        """))

    s.append(PageBreak())
    s.append(P("Дасгалын хариу", st_h1))
    s.append(P("Бүх хариуг энэ PDF-ийг үүсгэх үед жишээн дээр нь ажиллуулж шалгасан.", st_small))
    s.append(P("1. Тоолох — O(n)", st_h2))
    s.append(code("""
        def count_occurrences(items, target):
            count = 0
            for x in items:
                if x == target:
                    count += 1              # буцаахгүй — тоолоод үргэлжлүүлнэ
            return count                    # O(n): бүгдийг заавал харна
    """))
    s.append(P("2. Гараар мөрдөх", st_h2))
    s.append(P(f"target = 2: <b>3</b> харьцуулалт, {c('2')} буцаана. target = 7: <b>5</b> харьцуулалт "
               f"(бүгдийг), {c('-1')} буцаана."))
    s.append(data_table([
        ["i", "items[i]", "== 2 ?", "== 7 ?"],
        ["0", "5", "False", "False"],
        ["1", "8", "False", "False"],
        ["2", "2", f"<b>True → {c('return 2')}</b>", "False"],
        ["3", "9", "—", "False"],
        ["4", "2", "—", "False"],
        ["—", "", "", f"<b>{c('return -1')}</b>"],
    ], [CW * 0.12, CW * 0.18, CW * 0.35, CW * 0.35], center_cols=(0, 1, 2, 3)))
    s.append(P("3. Алдааг ол — −1 буцаана", st_h2))
    s.append(P(f"Эхний элемент 4 ≠ 8 тул else салаа ажиллаж шууд {c('return -1')} хийнэ — 6, 8-ыг огт "
               f"харахгүй. Засвар: else-ийг устгаад {c('return -1')}-ийг давталтын <b>гадна</b> (for-той "
               "ижил догол) бичнэ. Энэ бол 4-р бүлгийн 1-р алдаа."))
    s.append(P("4. Хоёр дахь тохиолдол — O(n)", st_h2))
    s.append(code("""
        def second_occurrence(items, target):
            seen = 0                            # хэд дэх удаагаа олж байгааг тоолно
            for i, x in enumerate(items):
                if x == target:
                    seen += 1
                    if seen == 2:
                        return i
            return -1
    """))
    s.append(P("5. Нөхцөлөөр хайх — O(n)", st_h2))
    s.append(code("""
        def first_greater(items, x):
            for i, v in enumerate(items):
                if v > x:                       # «== target»-ийн оронд нөхцөл
                    return i
            return -1
    """))

    # ------------------------------------------------------------- 10
    s += section(10, "Хураангуй", need=420)
    s.append(P("Загвар — цээжлэх биш, ойлгож бич", st_h2))

    def lin_card(w):
        return [P(f'<font color="{C_LINEAR}">■</font>&nbsp;<b>Linear search</b> · O(n)', st_cell_b),
                Spacer(1, 4),
                code_block("""
                    def linear_search(items, target):
                        for i in range(len(items)):
                            if items[i] == target:
                                return i
                        return -1   # давталтын ГАДНА
                """, width=w)]

    def lin_card2(w):
        return [P("<b>Ижил санаа, enumerate-тэй</b>", st_cell_b),
                Spacer(1, 4),
                code_block("""
                    def linear_search(items, target):
                        for i, x in enumerate(items):
                            if x == target:
                                return i
                        return -1
                """, width=w)]

    s.append(two_cards(lin_card, lin_card2))
    s.append(Spacer(1, 6))
    s.append(P("Linear search бичихдээ шалгах 4 зүйл", st_h2))
    s += numbered([
        f"<b>Бүх</b> индексийг хамарч байна уу? {c('range(len(items))')} — {c('- 1')}-гүй.",
        f"Олдмогц <b>индексийг</b> (утгыг биш) {c('return')} хийж байна уу?",
        f"{c('return -1')} давталтын <b>гадна</b> байна уу?",
        "Захын тохиолдлуудаар (хоосон, 1 элемент, эхний, сүүлийн, байхгүй, давхардсан) <b>тестэлсэн</b> үү?",
    ])
    s.append(P("Санаж үлдэх зүйлс", st_h2))
    s += bullets([
        f"Олдохгүй бол {c('-1')}; хэрэглэхээсээ өмнө {c('if idx != -1')} гэж шалга.",
        "«Олдсонгүй» гэж зөвхөн <b>бүгдийг</b> харсны дараа хэлнэ.",
        "Цаг: хамгийн муу үед <b>O(n)</b>; санах ой: <b>O(1)</b>. n 2 дахин → ажил 2 дахин.",
        f"{c('in')}, {c('index()')}, {c('count()')} бол бэлэн linear search — давталт дотор хэрэглэхдээ болгоомжил.",
        "Эрэмбэгүй, жижиг, нөхцөлөөр хайх, дарааллаар ирэх өгөгдөлд — linear search.",
        "Том, эрэмбэлэгдсэн жагсаалтаас олон удаа хайх бол — <b>binary search</b> (Хайлт 2/2).",
    ])

    doc = LessonDoc(OUT_LINEAR,
                    make_cover("АЛГОРИТМЫН ҮНДЭС  ·  PYTHON  ·  ХАЙЛТ 1/2", "Linear", "search",
                               ["Шугаман хайлт: бичих, мөрдөх,", "хувилбарууд, тестлэх"],
                               deco_linear),
                    make_page("Хайлт 1/2 — Linear search"),
                    title="Хайлт 1/2 — Linear search",
                    subject="Linear search: хэрэгжүүлэх түвшин")
    doc.build(s)
    return lin_bugs


# ============================================================================
# ХИЧЭЭЛ 2: BINARY SEARCH
# ============================================================================
def build_binary(ns, t_lin, t_bin, n_tests):
    bin_bugs = bug_report([bug_lt, bug_lo_mid, bug_hi_len, bug_float],
                          binary_cases(1000), linear_search)
    ratio = t_lin[-1] / t_bin[-1]
    s = front_page(
        "Linear search, while, Big O",
        [
            "Binary search-ийг цээжлэлгүйгээр, <b>учир шалтгаанаас нь</b> гаргаж бичнэ: "
            f"{c('lo')}, {c('hi')}, {c('mid')}, {c('+1')}, {c('-1')} яагаад гэдгийг тайлбарлана.",
            "Кодоо цаасан дээр <b>мөрдөж</b> (trace), эргэлт бүрийн хувьсагчдыг хүснэгтээр гаргана.",
            "Binary search-ийн <b>5 түгээмэл алдааг</b> таньж засна, кодоо <b>тестээр</b> баталгаажуулна.",
            f"Давхардал, оруулах байр зэрэг хувилбаруудыг бичиж, Python-ий {c('bisect')} модулийг хэрэглэнэ.",
            "Linear ба binary search-ийн аль нэгийг <b>хэзээ</b> сонгохоо мэднэ.",
        ],
        ["Санаа", "Алхам алхмаар бичих", "Гараар мөрдөх (trace)", "Түгээмэл алдаа ба засвар",
         "Давхардал, оруулах байр, bisect", "Тестлэх", "Linear search-тэй харьцуулах",
         "Дасгал", "Хураангуй"],
        "Нэг өгүүлбэрээр",
        ["<b>Binary search</b> (хоёртын хайлт): жагсаалт <b>эрэмбэлэгдсэн</b> бол дундахыг нь хар, "
         "хэрэггүй хагасыг нь хая, үлдсэн хагаст давт."],
    )

    # ------------------------------------------------------------- 1
    s += section(1, "Санаа")
    s.append(callout("Өмнөх хичээлээс (Хайлт 1/2: Linear search)",
                     f"Хайлтын функц {c('items')}, {c('target')} авч, олдвол <b>индексийг</b>, олдохгүй бол "
                     f"{c('-1')}-ийг буцаана. Linear search элемент бүрийг шалгадаг тул <b>O(n)</b>: сая элементэд "
                     "сая хүртэл харьцуулалт. Binary search ижил гэрээтэй, гэхдээ хамаагүй хурдан."))
    s.append(P("<b>Тоглоом:</b> найз чинь 1-ээс 100-ын хооронд тоо бодсон. Чи таах бүрт тэр "
               "«их», «бага» эсвэл «зөв» гэж хариулна. Хамгийн ухаалаг стратеги бол үргэлж "
               "<b>дундах</b> тоог хэлэх. Бодсон тоо 37 бол:"))
    s.append(data_table([
        ["Таалт", "Боломжит хүрээ", "Хэлсэн тоо", "Хариу", "Шинэ хүрээ"],
        ["1", "1 … 100", "50", "«их»", "1 … 49"],
        ["2", "1 … 49", "25", "«бага»", "26 … 49"],
        ["3", "26 … 49", "37", "<b>«зөв»</b>", "—"],
    ], [CW * 0.12, CW * 0.24, CW * 0.18, CW * 0.18, CW * 0.28], center_cols=(0, 1, 2, 3, 4),
        row_bg={3: OK_ROW}))
    s.append(Spacer(1, 8))
    s.append(P("Таалт бүр боломжит хүрээг <b>хагасаар</b> багасгаж байна. 100 тооноос дээд тал нь "
               "7 таалтаар заавал олно. Нэг нэгээр нь тааж эхэлбэл 100 хүртэл таалт хэрэгтэй."))
    s.append(callout("Заавал байх нөхцөл: өгөгдөл эрэмбэлэгдсэн байх",
                     "50 «их» гэвэл бодсон тоо 50-аас <b>доош</b> гэдгийг бид мэднэ — тиймээс 51…100-г шалгалгүйгээр "
                     "хаяж чадна. Энэ нь тоонууд <b>дарааллаараа</b> байгаа учраас л боломжтой. Эрэмбэгүй "
                     "жагсаалтын дунд элемент бусад элементийн талаар юу ч хэлж өгөхгүй."))
    s.append(P("Гурван хувьсагч", st_h2))
    s.append(P("Жагсаалт дээр «боломжит хүрээ»-г хоёр индексээр хадгална:"))
    s.append(data_table([
        ["Хувьсагч", "Утга", "Эхлэх утга"],
        [P(c("lo"), st_cell), "Хүрээний зүүн хил (энэ индекс хүрээнд <b>багтана</b>)", P(c("0"), st_cell)],
        [P(c("hi"), st_cell), "Хүрээний баруун хил (энэ индекс ч <b>багтана</b>)",
         P(c("len(items) - 1"), st_cell)],
        [P(c("mid"), st_cell), "Хүрээний дунд — одоо шалгах элемент", P(c("(lo + hi) // 2"), st_cell)],
    ], [CW * 0.16, CW * 0.56, CW * 0.28]))
    s.append(Spacer(1, 8))
    s.append(callout("Гол санаа (invariant — үргэлж үнэн байх зүйл)",
                     f"Хэрэв target жагсаалтад байгаа бол тэр заавал {c('items[lo]')} … {c('items[hi]')} "
                     "хооронд байна. Эргэлт бүр энэ хүрээг хагас болгоно. Хүрээ хоосон болбол "
                     f"({c('lo > hi')}) — target <b>байхгүй</b>."))
    steps_tbl = data_table([
        ["n (элементийн тоо)", "Linear: хамгийн ихдээ", "Binary: хамгийн ихдээ"],
        ["10", "10", "4"],
        ["100", "100", "7"],
        ["1 000", "1 000", "10"],
        ["1 000 000", "1 000 000", "<b>20</b>"],
        ["1 000 000 000", "1 000 000 000", "<b>30</b>"],
    ], [CW * 0.34, CW * 0.33, CW * 0.33], center_cols=(0, 1, 2), zebra=True)
    s.append(KeepTogether([
        P("Хэдэн алхам хийх вэ?", st_h2),
        P("n элементийг хагасалсаар 1 болгоход log<sub>2</sub> n орчим алхам хэрэгтэй. Яг "
          "тоо нь log<sub>2</sub> n-ийн <b>бүхэл хэсэг + 1</b>:"),
        steps_tbl,
        Spacer(1, 8),
        P("Элементийн тоо <b>1000 дахин</b> өсөхөд binary search ердөө <b>10 алхмаар</b> нэмэгдэж байна."),
    ]))

    # ------------------------------------------------------------- 2
    s += section(2, "Алхам алхмаар бичих", need=300)
    s.append(P("Кодыг цээжлэх шаардлагагүй — 1-р бүлгийн санаанаас мөр бүрийг гаргаж авъя."))
    s.append(step(1, f"Хүрээг бүх жагсаалтаар эхлүүл: {c('lo, hi = 0, len(items) - 1')} &nbsp;— "
                     f"{c('hi')} бол сүүлийн <b>индекс</b>, урт биш."))
    s.append(step(2, f"Хүрээ хоосон биш байх хооронд давт: {c('while lo <= hi:')} &nbsp;— "
                     f"{c('lo == hi')} үед 1 элемент үлдсэн, түүнийг ч шалгах ёстой тул {c('<=')}."))
    s.append(step(3, f"Дундыг ол: {c('mid = (lo + hi) // 2')} &nbsp;— {c('//')} бол бүхэл хуваалт, "
                     "индекс бүхэл тоо байх ёстой."))
    s.append(step(4, "Гурван тохиолдлыг шалга:"))
    s.append(data_table([
        ["Нөхцөл", "Утга нь", "Хийх зүйл"],
        [P(c("items[mid] == target"), st_cell), "олдлоо", P(c("return mid"), st_cell)],
        [P(c("items[mid] < target"), st_cell), "target <b>баруун</b> талд байна",
         P(c("lo = mid + 1"), st_cell)],
        [P(c("items[mid] > target"), st_cell), "target <b>зүүн</b> талд байна",
         P(c("hi = mid - 1"), st_cell)],
    ], [CW * 0.34, CW * 0.36, CW * 0.30]))
    s.append(Spacer(1, 6))
    s.append(step(5, f"Давталтаас гарвал хүрээ хоосон болсон гэсэн үг: {c('return -1')}."))
    s.append(Spacer(1, 6))
    s.append(code("""
        def binary_search(items, target):
            lo, hi = 0, len(items) - 1          # 1. хүрээ = бүх жагсаалт
            while lo <= hi:                     # 2. хүрээ хоосон биш байхад
                mid = (lo + hi) // 2            # 3. дунд индекс
                if items[mid] == target:        # 4а. олдлоо
                    return mid
                elif items[mid] < target:       # 4б. баруун талд байна
                    lo = mid + 1
                else:                           # 4в. зүүн талд байна
                    hi = mid - 1
            return -1                           # 5. хүрээ хоосон → байхгүй

        nums = [2, 5, 8, 12, 16, 23, 38, 41, 56, 61, 67, 72, 80, 85, 91, 99]
        print(binary_search(nums, 67))          # 10
        print(binary_search(nums, 40))          # -1
    """))
    s.append(callout("Яагаад mid + 1, mid − 1 гэж?",
                     f"{c('items[mid]')}-ийг бид дөнгөж шалгаад таараагүйг мэдсэн. Тиймээс түүнийг дараагийн "
                     "хүрээнд дахин оруулах шаардлагагүй. Энэ ±1 нь хүрээг эргэлт бүрт <b>заавал</b> "
                     "багасгадаг — эс тэгвээс давталт мөнхөрч болно (4-р бүлгийн 2-р алдаа)."))
    s.append(P("Рекурсив хувилбар", st_h2))
    s.append(P(f"Ижил санааг рекурсээр бичиж болно: {c('lo')}, {c('hi')} нь параметр болж, "
               "«хүрээ хоосон» нь суурь тохиолдол болно:"))
    s.append(code("""
        def binary_search_rec(items, target, lo=0, hi=None):
            if hi is None:
                hi = len(items) - 1             # анхны дуудлага: бүх жагсаалт
            if lo > hi:                         # суурь тохиолдол: хүрээ хоосон
                return -1
            mid = (lo + hi) // 2
            if items[mid] == target:
                return mid
            if items[mid] < target:
                return binary_search_rec(items, target, mid + 1, hi)
            return binary_search_rec(items, target, lo, mid - 1)
    """))
    s.append(P("Давталттай хувилбар O(1) санах ой ашигладаг бол рекурсив хувилбар дуудлагын стек дээр "
               "<b>O(log n)</b> зай эзэлнэ (сая элементэд ердөө 20 давхар — асуудалгүй)."))
    s.append(warn("Зүсэлт (slice) хэрэглэж болохгүй",
                  f"{c('binary_search_rec(items[mid + 1:], target)')} гэж бичвэл: (1) зүсэлт бүр шинэ хуулбар "
                  "үүсгэдэг тул нийт <b>O(n)</b> болж binary search-ийн бүх ашиг алга болно; "
                  "(2) шинэ жагсаалтын индекс 0-ээс эхэлдэг тул буцаасан индекс <b>буруу</b> болно. "
                  f"Тиймээс {c('lo')}, {c('hi')} индексийг дамжуулдаг."))

    # ------------------------------------------------------------- 3
    s += section(3, "Гараар мөрдөх (trace)", need=360)
    s.append(P("Код бичсэний дараах хамгийн сайн шалгалт бол цаасан дээр <b>мөрдөх</b>: хүснэгт зурж, "
               "давталтын эргэлт бүрт хувьсагчдын утгыг бичнэ. Хоёр тохиолдлыг мөрдье — олдох ба олдохгүй."))
    v16 = [2, 5, 8, 12, 16, 23, 38, 41, 56, 61, 67, 72, 80, 85, 91, 99]
    s.append(figure(chart_binary_trace(v16, 67), head="Тохиолдол 1: 67-г хайх (олдоно)",
                    caption="Зураг 1. Цайвар хөх — одоогийн хүрээ [lo, hi], хар хөх — шалгаж буй items[mid], "
                            "саарал — хаягдсан хэсэг. 16 элементээс 4 эргэлтэд олдлоо. Linear search бол "
                            "11 харьцуулалт хийх байсан."))
    s.append(binary_trace_table([
        ["1", "0", "15", "7", "41", "41 &lt; 67", f"баруун тийш: {c('lo = 8')}"],
        ["2", "8", "15", "11", "72", "72 &gt; 67", f"зүүн тийш: {c('hi = 10')}"],
        ["3", "8", "10", "9", "61", "61 &lt; 67", f"баруун тийш: {c('lo = 10')}"],
        ["4", "10", "10", "10", "67", "<b>67 == 67</b>", f"<b>{c('return 10')}</b>"],
    ], OK_ROW))
    s.append(Spacer(1, 6))
    s.append(figure(chart_binary_trace(v16, 40), head="Тохиолдол 2: 40-ийг хайх (байхгүй)",
                    caption="Зураг 2. Сүүлийн эргэлтийн дараа lo = 7, hi = 6 болж бие биеэ «гаталсан» тул "
                            "хүрээ хоосон. Анхаар: lo нь 40-ийг оруулах байрлалыг яг зааж байна (5-р бүлэг)."))
    s.append(binary_trace_table([
        ["1", "0", "15", "7", "41", "41 &gt; 40", f"зүүн тийш: {c('hi = 6')}"],
        ["2", "0", "6", "3", "12", "12 &lt; 40", f"баруун тийш: {c('lo = 4')}"],
        ["3", "4", "6", "5", "23", "23 &lt; 40", f"баруун тийш: {c('lo = 6')}"],
        ["4", "6", "6", "6", "38", "38 &lt; 40", f"баруун тийш: {c('lo = 7')}"],
        ["—", "7", "6", "", "", f"<b>{c('lo > hi')}</b>", f"<b>{c('return -1')}</b>"],
    ], MISS_ROW))
    s.append(Spacer(1, 8))
    s.append(callout("Зөвлөгөө: компьютерээр мөрдүүлэх",
                     [f"Давталтын эхэнд нэг мөр {c('print')} нэмбэл хүснэгтийг Python өөрөө хэвлэнэ. "
                      "Код буруу ажиллаж байвал хамгийн түрүүнд үүнийг хий:",
                      Spacer(1, 4),
                      code_block("""
                          while lo <= hi:
                              mid = (lo + hi) // 2
                              print(f"lo={lo:2}  hi={hi:2}  mid={mid:2}  items[mid]={items[mid]}")
                              ...
                      """, width=CW - 28)]))

    # ------------------------------------------------------------- 4
    s += section(4, "Түгээмэл алдаа ба засвар", need=300)
    s.append(P("Binary search ердөө 10 мөр боловч алдаа гаргахад маш амархан. Жон Бентли «Programming "
               "Pearls» номдоо мэргэжлийн програмистуудын ихэнх нь үүнийг анх удаа алдаагүй бичиж "
               "чадаагүйг тэмдэглэсэн байдаг. Доорх 5 алдааг бүгдийг нь бодитоор ажиллуулж шалгав."))
    s.append(bug_card(
        1, "Давталтын нөхцөлд = мартах",
        "while lo < hi:",
        "while lo <= hi:",
        f"{c('binary_search([5], 5)')} → <b>−1</b>. {c('binary_search([1, 3], 3)')} → <b>−1</b>.",
        f"{c('lo == hi')} үед 1 элемент үлдсэн байхад давталт түүнийг шалгалгүй гарна."))
    s.append(bug_card(
        2, "Хүрээг багасгахгүй байх",
        "lo = mid",
        "lo = mid + 1",
        f"{c('binary_search([1, 3], 3)')} → програм <b>гацна</b> (мөнхийн давталт).",
        f"lo = 0, hi = 1 → mid = 0 → 1 &lt; 3 → lo = 0. Хүрээ өөрчлөгдөхгүй тул ижил эргэлт "
        f"дахин дахин давтагдана. {c('hi = mid')} гэвэл мөн адил."))
    s.append(bug_card(
        3, "hi-г уртаар эхлүүлэх",
        "lo, hi = 0, len(items)",
        "lo, hi = 0, len(items) - 1",
        f"{c('binary_search([1, 3, 5], 9)')} → <b>IndexError: list index out of range</b>.",
        f"3 элементтэй жагсаалтын сүүлийн индекс 2. hi = 3 үед {c('items[3]')}-д хандахыг оролдоно."))
    s.append(bug_card(
        4, "Энгийн хуваалт хэрэглэх",
        "mid = (lo + hi) / 2",
        "mid = (lo + hi) // 2",
        f"{c('binary_search([1, 3, 5], 3)')} → <b>TypeError: list indices must be integers or "
        "slices, not float</b>.",
        f"Python 3-т {c('/')} үргэлж бутархай ({c('1.0')}) буцаадаг. Индекс бүхэл байх ёстой."))
    s.append(bug_card(
        5, "Эрэмбэгүй жагсаалтад хэрэглэх",
        "binary_search([9, 2, 7, 4, 1], 9)",
        "items.sort()\nbinary_search(items, 9)",
        "Алдаа <b>гарахгүй</b>, гэхдээ <b>−1</b> буцаана — 9 индекс 0-д байгаа ч!",
        "Дунд элемент 7 &lt; 9 тул «9 баруун талд» гэж дүгнээд зүүн хагасыг хаясан. Энэ бол хамгийн "
        "аюултай алдаа: програм унахгүй, зүгээр л буруу хариу өгнө. Эрэмбэлэх боломжгүй бол linear "
        "search хэрэглэ."))
    s.append(callout("Python-д байхгүй, бусад хэлэнд байдаг алдаа",
                     f"Java, C++ зэрэгт {c('lo + hi')} нь бүхэл тооны хязгаараас хэтэрч (overflow) сөрөг "
                     f"болж болдог тул {c('mid = lo + (hi - lo) // 2')} гэж бичдэг. Python-ий бүхэл тоо "
                     "хязгааргүй тул энд санаа зовох хэрэггүй, гэхдээ бусад хэлэнд шилжихдээ санаарай."))

    # ------------------------------------------------------------- 5
    s += section(5, "Давхардал, оруулах байр, bisect", need=300)
    s.append(P("Давхардсан утга: аль индексийг буцаах вэ?", st_h2))
    s.append(P(f"{c('binary_search([1, 3, 3, 3, 5, 8], 3)')} нь <b>2</b> буцаана — 3 гэсэн утга мөн, "
               "гэхдээ <b>эхний</b> 3 (индекс 1) биш. Үндсэн хувилбар «аль нэг тохирох индексийг» л "
               "олдог. Эхнийхийг олохын тулд <b>2 мөр</b> өөрчилнө: олдмогц зогсохгүй, санаж аваад "
               "зүүн тийш үргэлжлүүлэн хайна:"))
    s.append(code("""
        def first_occurrence(items, target):
            lo, hi = 0, len(items) - 1
            result = -1
            while lo <= hi:
                mid = (lo + hi) // 2
                if items[mid] == target:
                    result = mid                # ← олдлоо: санаж аваад
                    hi = mid - 1                # ← зүүн талд дахиад байгаа эсэхийг хайна
                elif items[mid] < target:
                    lo = mid + 1
                else:
                    hi = mid - 1
            return result

        first_occurrence([1, 3, 3, 3, 5, 8], 3)     # 1
    """))
    s.append(P(f"<b>Сүүлийн</b> тохиолдлыг олохын тулд {c('hi = mid - 1')}-ийн оронд {c('lo = mid + 1')} "
               "гэж бичнэ (8-р бүлгийн дасгал). Тэгвэл <b>хэдэн удаа</b> байгааг "
               f"{c('last - first + 1')} гэж O(log n)-д олно — {c('count()')} бол O(n)."))
    s.append(P("Оруулах байр (lower bound)", st_h2))
    s.append(P("3-р бүлгийн 2-р тохиолдолд давталт дуусахад <b>lo нь 40-ийг оруулах байрыг</b> зааж байсан. "
               "Үүнийг тусдаа функц болгоё: «target-ээс бага биш (≥) эхний элементийн индекс». "
               "Энэ нь давхардалтай үед эхний тохиолдлыг, байхгүй үед оруулах байрыг өгнө:"))
    s.append(code("""
        def lower_bound(items, target):
            lo, hi = 0, len(items)              # ← hi = len: «жагсаалтын гадна» гэсэн байр
            while lo < hi:                      # ← хүрээ [lo, hi) хоосон биш байхад
                mid = (lo + hi) // 2
                if items[mid] < target:
                    lo = mid + 1
                else:
                    hi = mid                    # ← mid өөрөө хариу байж болох тул хасахгүй
            return lo

        nums = [1, 3, 3, 3, 5, 8]
        lower_bound(nums, 3)    # 1  — эхний 3
        lower_bound(nums, 4)    # 4  — 4-ийг 5-ын өмнө оруулна
        lower_bound(nums, 9)    # 6  — хамгийн төгсгөлд
    """))
    s.append(figure(chart_ranges(),
                    "Зураг 3. Хоёр загварын эхлэх төлөв. Хагас нээлттэй загварт hi нь жагсаалтын "
                    "гаднах «хоосон» байрыг заадаг — тэнд оруулах боломжтой учраас."))
    s.append(warn("Хоёр загварыг бүү холь", [
        f"Энд {c('hi = len(items)')}, {c('while lo < hi')}, {c('hi = mid')} гэж бичсэн — эдгээр нь 4-р "
        "бүлэгт «алдаа» байсан! Гэвч энд хүрээг <b>[lo, hi)</b> — hi-г <b>оруулахгүйгээр</b> тодорхойлсон "
        "тул бүгд зөв. Нэг загвар сонгоод <b>бүх мөрийг</b> түүнд тааруул:",
        Spacer(1, 4),
        data_table([
            ["", "Хаалттай [lo, hi]", "Хагас нээлттэй [lo, hi)"],
            ["Эхлэл", P(c("hi = len(items) - 1"), st_cell), P(c("hi = len(items)"), st_cell)],
            ["Давталт", P(c("while lo <= hi"), st_cell), P(c("while lo < hi"), st_cell)],
            ["Зүүн тийш", P(c("hi = mid - 1"), st_cell), P(c("hi = mid"), st_cell)],
            ["Баруун тийш", P(c("lo = mid + 1"), st_cell), P(c("lo = mid + 1"), st_cell)],
        ], [(CW - 28) * 0.26, (CW - 28) * 0.37, (CW - 28) * 0.37]),
    ]))
    s.append(P("Python-ий bisect модуль", st_h2))
    s.append(P("Python-д хагас нээлттэй загвар бэлэн байдаг. Бодит төсөлд үүнийг хэрэглэ — "
               "шалгагдсан бөгөөд C хэл дээр бичигдсэн тул хурдан."))
    s.append(code("""
        import bisect

        nums = [1, 3, 3, 3, 5, 8]
        bisect.bisect_left(nums, 3)     # 1  ← манай lower_bound-тай яг ижил
        bisect.bisect_right(nums, 3)    # 4  ← 3-аас ИХ эхний элементийн индекс
        bisect.bisect_right(nums, 3) - bisect.bisect_left(nums, 3)    # 3 → 3 гурван удаа байна

        bisect.insort(nums, 4)          # эрэмбийг эвдэлгүй оруулна
        print(nums)                     # [1, 3, 3, 3, 4, 5, 8]
    """))
    s.append(P(f"{c('bisect')} ашиглан бидний гэрээтэй (индекс эсвэл −1) хайлт бичих нь:"))
    s.append(code("""
        from bisect import bisect_left

        def binary_search(items, target):
            i = bisect_left(items, target)              # оруулах байр
            if i < len(items) and items[i] == target:   # тэр байранд target өөрөө байна уу?
                return i
            return -1
    """))
    s.append(P(f"Анхаар: {c('insort')} нь байрыг O(log n)-д олдог ч бусад элементийг шилжүүлж оруулдаг "
               "тул нийтдээ <b>O(n)</b>.", st_small))
    s.append(P("Хариуг хайх: жагсаалтгүй binary search", st_h2))
    s.append(P(f"Binary search-д жагсаалт заавал биш. «{c('mid * mid <= n')} үнэн үү?» гэсэн асуулт "
               "0, 1, 2, 3, … дээр <b>үнэн, үнэн, …, үнэн, худал, худал, …</b> гэж зөвхөн <b>нэг удаа</b> "
               "солигддог. Ийм (монотон) асуултын «солигдох цэг»-ийг binary search-ээр олно:"))
    s.append(code("""
        def isqrt(n):
            \"\"\"k * k <= n байх хамгийн их бүхэл k (бүхэл квадрат язгуур).\"\"\"
            lo, hi = 0, n
            ans = 0
            while lo <= hi:
                mid = (lo + hi) // 2
                if mid * mid <= n:
                    ans = mid                   # mid тохирно — илүү томыг хайя
                    lo = mid + 1
                else:
                    hi = mid - 1
            return ans

        isqrt(50)           # 7   (7 * 7 = 49 <= 50,  8 * 8 = 64 > 50)
        isqrt(1_000_000)    # 1000 — ердөө 20 орчим алхамд
    """))

    # ------------------------------------------------------------- 6
    s += section(6, "Тестлэх", need=300)
    s.append(P("«Ажиллаж байх шиг байна» гэж орхиж болохгүй — 4-р бүлгийн алдаанууд ихэнх жишээн дээр "
               "зөв хариу өгдөг! Хоёр төрлийн тест бичье."))
    s.append(P("1. Захын тохиолдлууд (edge cases)", st_h2))
    s.append(P("Алдаа ихэвчлэн хил дээр нуугддаг: хоосон, ганц элемент, эхний ба сүүлийн байр."))
    s.append(code("""
        def test_edges():
            assert binary_search([], 5) == -1             # хоосон жагсаалт
            assert binary_search([5], 5) == 0             # ганц элемент, байгаа
            assert binary_search([5], 3) == -1            # ганц элемент, байхгүй
            assert binary_search([1, 3, 5, 7], 1) == 0    # эхний элемент
            assert binary_search([1, 3, 5, 7], 7) == 3    # сүүлийн элемент
            assert binary_search([1, 3, 5, 7], 0) == -1   # бүгдээс бага
            assert binary_search([1, 3, 5, 7], 9) == -1   # бүгдээс их
            assert binary_search([1, 3, 5, 7], 4) == -1   # хооронд нь, байхгүй
            assert binary_search([1, 3, 5], 5) == 2       # сондгой урттай
            print("Захын тохиолдлууд: OK")
    """))
    s.append(P(f"{c('assert')} нь нөхцөл худал бол {c('AssertionError')} шиднэ, үнэн бол юу ч хийхгүй."))
    s.append(P("2. Санамсаргүй тест: linear search-тэй харьцуулах", st_h2))
    s.append(P("Linear search маш энгийн тул бараг алдаагүй. Тиймээс түүнийг «зөв хариу» болгон ашиглаж, "
               "мянга мянган санамсаргүй жагсаалт дээр binary search-тэй харьцуулна:"))
    s.append(code("""
        import random

        def test_random(trials=10_000):
            for _ in range(trials):
                n = random.randint(0, 20)
                items = sorted(random.sample(range(50), n))   # эрэмбэлэгдсэн, давхардалгүй
                target = random.randint(-5, 55)               # заримдаа байхгүй утга
                assert binary_search(items, target) == linear_search(items, target), \\
                    (items, target)                           # бүтэлгүйтвэл жишээг хэвлэнэ
            print(trials, "санамсаргүй тест: OK")
    """))
    s.append(P(f"Яагаад <b>давхардалгүй</b>? Давхардалтай үед хоёр функц өөр өөр (гэхдээ хоёулаа зөв) индекс "
               f"буцааж болно — жишээ нь 3-ыг хайхад linear нь 1, binary нь 2. {c('random.sample')} "
               "давхардалгүй утга сонгодог."))
    names = [f"Алдаа {i}: {c(code_)}" for i, code_ in enumerate(
        ["while lo < hi", "lo = mid", "hi = len(items)", "mid = (lo + hi) / 2"], 1)]
    s.append(KeepTogether([
        P(f"Энэ PDF-ийг үүсгэх үед зөв хувилбарыг <b>{fmt(n_tests)}</b> санамсаргүй тестээр шалгахад бүгд "
          "амжилттай давлаа. Харин 4-р бүлгийн алдаатай хувилбаруудыг ижил тестэд оруулахад:"),
        bug_table(names, bin_bugs, f"Зөв {c('binary_search')}"),
    ]))
    s.append(Spacer(1, 8))
    s.append(callout("Дүгнэлт",
                     "Захын тохиолдлын тест + энгийн хувилбартай харьцуулах санамсаргүй тест = "
                     f"хэрэгжүүлэлтдээ итгэх хамгийн хялбар арга. Алдаа бүр эхний "
                     f"{max(b[1] for b in bin_bugs)} тестийн дотор илэрсэн."))

    # ------------------------------------------------------------- 7
    s += section(7, "Linear search-тэй харьцуулах", need=380)
    s.append(P("Хоёр функцийг 100 000 … 1 000 000 элементтэй жагсаалт дээр <b>байхгүй</b> утга "
               "хайлгаж (хамгийн муу тохиолдол) хэмжив:"))
    s.append(figure(chart_timing(ns, t_lin, t_bin),
                    "Зураг 4. Энэ PDF-ийг үүсгэх үед бодитоор хэмжсэн үр дүн (хэд хэдэн давталтын "
                    "хамгийн бага утга). Таны компьютер дээр тоо нь өөр гарах ч хэлбэр нь ижил."))
    s.append(P(f"n = 1 000 000 үед linear search <b>{t_lin[-1]:.1f} мс</b>, binary search "
               f"<b>{t_bin[-1] * 1000:.1f} микросекунд</b> — ойролцоогоор "
               f"<b>{fmt(float(f'{ratio:.2g}'))} дахин</b> ялгаатай. Binary search-ийн шугам бараг хэвтээ: "
               "сая элементэд ч ердөө 20 харьцуулалт хийдэг."))
    s.append(P("Бүрэн харьцуулалт", st_h2))
    s.append(data_table([
        ["", "Linear search", "Binary search"],
        [P("<b>Урьдчилсан нөхцөл</b>", st_cell), "Байхгүй", "<b>Эрэмбэлэгдсэн</b> байх"],
        [P("<b>Цаг (хамгийн муу)</b>", st_cell), "O(n)", "O(log n)"],
        [P("<b>Санах ой</b>", st_cell), "O(1)", "O(1) давталттай, O(log n) рекурсив"],
        [P("<b>Өгөгдлийн бүтэц</b>", st_cell), "Ямар ч дараалал: list, файлын мөр, генератор",
         "Индексээр шууд хандах боломжтой (list)"],
        [P("<b>Хайх нөхцөл</b>", st_cell), "Дурын нөхцөл (тэгш тоо, 60-аас бага…)",
         "Эрэмбэтэй уялдсан нөхцөл (≥ x, ≤ x…)"],
        [P("<b>Код</b>", st_cell), "4 мөр, алдаа гаргахад хэцүү", "10 мөр, ±1 алдаа түгээмэл"],
    ], [CW * 0.24, CW * 0.38, CW * 0.38], zebra=True))
    s.append(P("Эрэмбэлээд хайх нь ашигтай юу?", st_h2))
    s.append(P(f"Эрэмбэлэх ({c('sort()')}) өөрөө <b>O(n log n)</b> — нэг linear search-ээс илүү үнэтэй. "
               "Тэгэхээр хэдэн удаа хайхаас шалтгаална. n = 1 000 000 үед (log n ≈ 20) нийт алхмыг ойролцоогоор "
               "тооцъё:"))

    def steps_row(k):
        lin = k * 1_000_000
        binr = 1_000_000 * 20 + k * 20
        win = "Linear" if lin < binr else "Эрэмбэлээд binary"
        return [fmt(k), fmt(lin), fmt(binr), f"<b>{win}</b>"]

    s.append(data_table([
        ["Хайлтын тоо (k)", "Linear: k · n", "Эрэмбэлэх + binary: n log n + k log n", "Ялагч"],
        steps_row(1), steps_row(10), steps_row(100), steps_row(10_000),
    ], [CW * 0.18, CW * 0.24, CW * 0.36, CW * 0.22], center_cols=(0,), zebra=True))
    s.append(Spacer(1, 6))
    s.append(P("Ойролцоогоор <b>20-оос олон</b> удаа хайх бол нэг удаа эрэмбэлээд binary search хэрэглэх нь ашигтай."))
    s.append(P("Аль нь вэ? Шийдвэрийн жагсаалт", st_h2))
    s += numbered([
        "<b>Жагсаалт жижиг</b> (хэдэн арав) эсвэл <b>ганцхан удаа</b> хайх уу? → <b>Linear</b>. Энгийн, хангалттай хурдан.",
        "<b>Дурын нөхцөлөөр</b> хайх уу (эхний тэгш тоо, 60-аас бага оноо)? → <b>Linear</b>.",
        f"Өгөгдөл <b>эрэмбэлэгдсэн</b> эсвэл <b>олон удаа</b> хайх уу? → <b>Binary</b> ({c('bisect')}).",
        "«x-ээс их эхний», «a ба b хооронд хэд», «хамгийн ойр утга» гэх мэт асуулт уу? → <b>Binary</b> "
        f"({c('bisect_left')}, {c('bisect_right')}).",
        f"Зөвхөн «байгаа юу?» гэж асуух, эрэмбэ хамаагүй юу? → {c('set')} эсвэл {c('dict')}: дунджаар O(1) "
        "(Big O хичээлийн 5-р бүлэг).",
    ])

    # ------------------------------------------------------------- 8
    s += section(8, "Дасгал", need=260)
    s.append(P("Эхлээд өөрөө бодож, кодоо 6-р бүлгийн аргаар тестлээрэй. Хариуг дараагийн хуудаснаас шалга."))
    s.append(exercise_card(
        1, "Гараар мөрдөх",
        f"{c('binary_search([3, 8, 15, 21, 30, 42, 57], 30)')}-ийг 3-р бүлгийн хүснэгтээр мөрд: "
        f"эргэлт бүрийн {c('lo')}, {c('hi')}, {c('mid')}, {c('items[mid]')}. Хэдэн эргэлт хийж, юу буцаах вэ?"))
    s.append(exercise_card(
        2, "Алдааг ол",
        f"Доорх кодоор {c('[1, 3]')}-аас 0-ийг хайхад юу болох вэ? Яагаад? Хэрхэн засах вэ?",
        """
        def binary_search(items, target):
            lo, hi = 0, len(items) - 1
            while lo <= hi:
                mid = (lo + hi) // 2
                if items[mid] == target:
                    return mid
                elif items[mid] < target:
                    lo = mid + 1
                else:
                    hi = mid
            return -1
        """))
    s.append(exercise_card(
        3, "Сүүлийн тохиолдол",
        f"{c('last_occurrence(items, target)')}-ийг O(log n)-д бич. Зааварчилгаа: 5-р бүлгийн "
        f"{c('first_occurrence')}-оос нэг мөр өөрчилнө.",
        "last_occurrence([1, 3, 3, 3, 5, 8], 3)   # 3"))
    s.append(exercise_card(
        4, "Хүрээнд хэд байна?",
        f"Эрэмбэлэгдсэн жагсаалтад {c('a <= x <= b')} байх утга хэд байгааг O(log n)-д тоол. "
        f"{c('bisect')} ашиглаж болно.",
        "count_in_range([1, 3, 3, 5, 8, 13], 3, 8)   # 4   (3, 3, 5, 8)"))
    s.append(exercise_card(
        5, "Хамгийн ойр утга",
        f"Эрэмбэлэгдсэн, хоосон биш жагсаалтаас {c('x')}-д хамгийн ойр утгыг буцаа. Тэнцүү зайтай "
        f"бол багыг нь. Зааварчилгаа: {c('bisect_left')}-ийн өгсөн байр ба түүний өмнөх элементийг харьцуул.",
        "closest([2, 5, 9, 14], 11)   # 9   (11 - 9 = 2,  14 - 11 = 3)"))

    s.append(PageBreak())
    s.append(P("Дасгалын хариу", st_h1))
    s.append(P("Бүх хариуг энэ PDF-ийг үүсгэх үед жишээн дээр нь ажиллуулж шалгасан.", st_small))
    s.append(P("1. Гараар мөрдөх — 3 эргэлт, 4 буцаана", st_h2))
    s.append(binary_trace_table([
        ["1", "0", "6", "3", "21", "21 &lt; 30", f"{c('lo = 4')}"],
        ["2", "4", "6", "5", "42", "42 &gt; 30", f"{c('hi = 4')}"],
        ["3", "4", "4", "4", "30", "<b>30 == 30</b>", f"<b>{c('return 4')}</b>"],
    ], OK_ROW))
    s.append(P("2. Алдааг ол — мөнхийн давталт", st_h2))
    s.append(P(f"lo = 0, hi = 1 → mid = 0, 1 &gt; 0 → hi = 0. Дараа нь lo = 0, hi = 0 → mid = 0, 1 &gt; 0 → "
               f"hi = 0 … хүрээ өөрчлөгдөхгүй тул програм гацна. Засвар: {c('hi = mid - 1')} "
               f"(хаалттай загварт {c('while lo <= hi')}-тэй хамт заавал ±1)."))
    s.append(P("3. Сүүлийн тохиолдол — O(log n)", st_h2))
    s.append(code("""
        def last_occurrence(items, target):
            lo, hi = 0, len(items) - 1
            result = -1
            while lo <= hi:
                mid = (lo + hi) // 2
                if items[mid] == target:
                    result = mid
                    lo = mid + 1            # ← баруун талд дахиад байгаа эсэхийг хайна
                elif items[mid] < target:
                    lo = mid + 1
                else:
                    hi = mid - 1
            return result
    """))
    s.append(P("4. Хүрээнд хэд байна — O(log n)", st_h2))
    s.append(code("""
        from bisect import bisect_left, bisect_right

        def count_in_range(items, a, b):
            # b-ээс их эхний байр  −  a-аас бага биш эхний байр
            return bisect_right(items, b) - bisect_left(items, a)
    """))
    s.append(P("5. Хамгийн ойр утга — O(log n)", st_h2))
    s.append(code("""
        from bisect import bisect_left

        def closest(items, x):
            i = bisect_left(items, x)           # x-ээс бага биш эхний байр
            if i == 0:
                return items[0]                 # x бүгдээс бага (эсвэл тэнцүү)
            if i == len(items):
                return items[-1]                # x бүгдээс их
            before, after = items[i - 1], items[i]
            return before if x - before <= after - x else after
    """))

    # ------------------------------------------------------------- 9
    s += section(9, "Хураангуй", need=520)
    s.append(P("Хоёр загвар — цээжлэх биш, ойлгож бич", st_h2))

    def closed_card(w):
        return [P(f'<font color="{C_BINARY}">■</font>&nbsp;<b>Хаалттай [lo, hi]</b> · хайлт', st_cell_b),
                Spacer(1, 4),
                code_block("""
                    def binary_search(items, target):
                        lo, hi = 0, len(items) - 1
                        while lo <= hi:
                            mid = (lo + hi) // 2
                            if items[mid] == target:
                                return mid
                            elif items[mid] < target:
                                lo = mid + 1
                            else:
                                hi = mid - 1
                        return -1
                """, width=w),
                Spacer(1, 6),
                P("Олдвол индекс, олдохгүй бол −1.<br/>Сая элементэд 20 харьцуулалт.", st_small)]

    def half_open_card(w):
        return [P(f'<font color="{C_BINARY}">■</font>&nbsp;<b>Хагас нээлттэй [lo, hi)</b> · байр', st_cell_b),
                Spacer(1, 4),
                code_block("""
                    def lower_bound(items, target):
                        lo, hi = 0, len(items)
                        while lo < hi:
                            mid = (lo + hi) // 2
                            if items[mid] < target:
                                lo = mid + 1
                            else:
                                hi = mid
                        return lo
                """, width=w),
                Spacer(1, 6),
                P("target-ээс бага биш эхний байр.<br/>= bisect.bisect_left", st_small)]

    s.append(two_cards(closed_card, half_open_card))
    s.append(Spacer(1, 6))
    s.append(P("Binary search бичихдээ шалгах 5 зүйл", st_h2))
    s += numbered([
        "Жагсаалт <b>эрэмбэлэгдсэн</b> үү?",
        f"{c('hi = len(items) - 1')} ба {c('while lo <= hi')} — хоёулаа <b>хаалттай</b> [lo, hi] загвар уу?",
        f"{c('mid = (lo + hi) // 2')} — <b>бүхэл</b> хуваалт уу?",
        f"{c('lo = mid + 1')}, {c('hi = mid - 1')} — хүрээ эргэлт бүрт <b>заавал</b> багасаж байна уу?",
        "Захын тохиолдлуудаар (хоосон, 1 элемент, эхний, сүүлийн, байхгүй) <b>тестэлсэн</b> үү?",
    ])
    s.append(P("Санаж үлдэх зүйлс", st_h2))
    s += bullets([
        f"Гол санаа: target байгаа бол заавал {c('items[lo..hi]')} дотор; хүрээ хоосон болбол — байхгүй.",
        "Эргэлт бүр хүрээг <b>хагас</b> болгодог тул <b>O(log n)</b>: n 1000 дахин → +10 алхам.",
        "Кодоо <b>хүснэгтээр мөрд</b>; ойлгомжгүй бол давталт дотор print нэм.",
        f"Давхардал, оруулах байр, хүрээнд тоолох → {c('bisect_left')} / {c('bisect_right')}.",
        "Шинэ хэрэгжүүлэлтээ <b>linear search-тэй</b> санамсаргүй тестээр харьцуул.",
        "Эрэмбэгүй, жижиг, нөхцөлөөр хайх бол — linear search хангалттай.",
    ])

    doc = LessonDoc(OUT_BINARY,
                    make_cover("АЛГОРИТМЫН ҮНДЭС  ·  PYTHON  ·  ХАЙЛТ 2/2", "Binary", "search",
                               ["Хоёртын хайлт: бичих, мөрдөх,", "алдаагүй хэрэгжүүлэх"],
                               deco_binary),
                    make_page("Хайлт 2/2 — Binary search"),
                    title="Хайлт 2/2 — Binary search",
                    subject="Binary search: хэрэгжүүлэх түвшин")
    doc.build(s)
    return bin_bugs


def build():
    print("Өөрийгөө шалгаж байна…")
    self_check()
    test_edges_linear()
    test_edges_binary()
    n_tests = run_random_tests(10_000)
    print("Хэмжилт хийж байна…")
    ns, t_lin, t_bin = measure_search()
    lin_bugs = build_linear(ns, t_lin, n_tests)
    print("Бэлэн:", OUT_LINEAR)
    bin_bugs = build_binary(ns, t_lin, t_bin, n_tests)
    print("Бэлэн:", OUT_BINARY)
    print(f"linear@500k: {t_lin[4]:.3f} ms, @1M: {t_lin[-1]:.3f} ms, binary@1M: {t_bin[-1] * 1000:.3f} us")
    print("linear bugs:", lin_bugs)
    print("binary bugs:", bin_bugs)


if __name__ == "__main__":
    build()
