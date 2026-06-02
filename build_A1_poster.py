"""
기존 포스터 docx → A1 3단 칼럼 포스터 재구성
- 제목: 전체 너비
- 본문: 3단 칼럼 (테이블 기반)
- 참고문헌: 전체 너비 하단
"""
import sys, copy
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document
from docx.shared import Pt, Cm, Emu
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

SRC = r'C:\Users\paek6\Downloads\매치업별 특화 강화학습을 활용한 적응형 보스 AI 설계 및 분석_포스터.docx'
DST = r'C:\Users\paek6\Downloads\Buildup\Buildup\poster_output\BossAI_Poster_A1_3col.docx'

FONT_SCALE = 2.5
TITLE_FONT_SCALE = 5.0
AUTHOR_FONT_SCALE = 3.5
AFFIL_FONT_SCALE = 3.0
TABLE_FONT_SCALE = 2.0
REF_FONT_SCALE = 2.0
SECTION_HEADER_PT = 26
CONTENT_W_CM = 55.4      # 59.4 - 2*2.0
COL_GAP_CM = 0.8
COL_W_CM = (CONTENT_W_CM - 2 * COL_GAP_CM) / 3  # ~17.93

# ═══════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════

def scale_fonts(el, scale):
    for tag_name in ['w:sz', 'w:szCs']:
        for sz_el in el.iter(qn(tag_name)):
            val = sz_el.get(qn('w:val'))
            if val:
                try:
                    sz_el.set(qn('w:val'), str(max(int(int(val) * scale), 2)))
                except ValueError:
                    pass

def scale_images(el, max_width_emu):
    for extent in el.iter(qn('wp:extent')):
        cx = int(extent.get('cx', 0))
        cy = int(extent.get('cy', 0))
        if cx > 0 and cy > 0:
            ratio = max_width_emu / cx
            new_cx = int(cx * ratio)
            new_cy = int(cy * ratio)
            extent.set('cx', str(new_cx))
            extent.set('cy', str(new_cy))
    for ext_el in el.iter():
        tag = ext_el.tag
        if (tag.endswith('}ext') or tag.endswith('}chExt')) and ext_el.get('cx'):
            cx = int(ext_el.get('cx', 0))
            cy = int(ext_el.get('cy', 0))
            if cx > 0 and cy > 0:
                ratio = max_width_emu / cx
                ext_el.set('cx', str(int(cx * ratio)))
                ext_el.set('cy', str(int(cy * ratio)))

def make_p(text, size_pt, bold=False, color_hex=None, align='left',
           bg_hex=None, font_name='Malgun Gothic', space_before=0, space_after=0):
    p = OxmlElement('w:p')
    pPr = OxmlElement('w:pPr')
    p.append(pPr)

    jc = OxmlElement('w:jc')
    jc.set(qn('w:val'), align)
    pPr.append(jc)

    if bg_hex:
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), bg_hex)
        pPr.append(shd)

    sp = OxmlElement('w:spacing')
    sp.set(qn('w:before'), str(space_before))
    sp.set(qn('w:after'), str(space_after))
    sp.set(qn('w:line'), str(int(size_pt * 2 * 20 * 1.2)))
    pPr.append(sp)

    r = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    r.append(rPr)

    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), font_name)
    rFonts.set(qn('w:eastAsia'), font_name)
    rFonts.set(qn('w:hAnsi'), font_name)
    rPr.append(rFonts)

    sz = OxmlElement('w:sz')
    sz.set(qn('w:val'), str(size_pt * 2))
    rPr.append(sz)
    szCs = OxmlElement('w:szCs')
    szCs.set(qn('w:val'), str(size_pt * 2))
    rPr.append(szCs)

    if bold:
        b = OxmlElement('w:b')
        rPr.append(b)
    if color_hex:
        clr = OxmlElement('w:color')
        clr.set(qn('w:val'), color_hex)
        rPr.append(clr)

    t = OxmlElement('w:t')
    t.text = text
    t.set(qn('xml:space'), 'preserve')
    r.append(t)
    p.append(r)
    return p

def make_layout_table(col_widths_twips, cell_pad_twips=227):
    tbl = OxmlElement('w:tbl')
    tblPr = OxmlElement('w:tblPr')
    tbl.append(tblPr)

    tblW = OxmlElement('w:tblW')
    tblW.set(qn('w:w'), '5000')
    tblW.set(qn('w:type'), 'pct')
    tblPr.append(tblW)

    tblLayout = OxmlElement('w:tblLayout')
    tblLayout.set(qn('w:type'), 'fixed')
    tblPr.append(tblLayout)

    tblBorders = OxmlElement('w:tblBorders')
    for bname in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        b = OxmlElement(f'w:{bname}')
        b.set(qn('w:val'), 'none')
        b.set(qn('w:sz'), '0')
        b.set(qn('w:space'), '0')
        b.set(qn('w:color'), 'auto')
        tblBorders.append(b)
    tblPr.append(tblBorders)

    tblCellMar = OxmlElement('w:tblCellMar')
    for side in ['top', 'left', 'bottom', 'right']:
        mar = OxmlElement(f'w:{side}')
        mar.set(qn('w:w'), str(cell_pad_twips))
        mar.set(qn('w:type'), 'dxa')
        tblCellMar.append(mar)
    tblPr.append(tblCellMar)

    tblGrid = OxmlElement('w:tblGrid')
    for w in col_widths_twips:
        gc = OxmlElement('w:gridCol')
        gc.set(qn('w:w'), str(w))
        tblGrid.append(gc)
    tbl.append(tblGrid)

    tr = OxmlElement('w:tr')
    cells = []
    for ci, w in enumerate(col_widths_twips):
        tc = OxmlElement('w:tc')
        tcPr = OxmlElement('w:tcPr')
        tcW = OxmlElement('w:tcW')
        tcW.set(qn('w:w'), str(w))
        tcW.set(qn('w:type'), 'dxa')
        tcPr.append(tcW)
        vAlign = OxmlElement('w:vAlign')
        vAlign.set(qn('w:val'), 'top')
        tcPr.append(vAlign)
        tc.append(tcPr)
        tc.append(OxmlElement('w:p'))  # required empty p
        tr.append(tc)
        cells.append(tc)
    tbl.append(tr)
    return tbl, cells

# ═══════════════════════════════════════════════════════════
# Load document
# ═══════════════════════════════════════════════════════════
print(f'Loading: {SRC}')
doc = Document(SRC)

for section in doc.sections:
    section.page_width = Cm(59.4)
    section.page_height = Cm(84.1)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)
    section.top_margin = Cm(1.5)
    section.bottom_margin = Cm(1.5)

body = doc.element.body
sectPr = body.find(qn('w:sectPr'))

# Collect body-level elements
children = list(body)
paras = []
tbls = []
for c in children:
    local_tag = c.tag.split('}')[-1] if '}' in c.tag else c.tag
    if local_tag == 'p':
        paras.append(c)
    elif local_tag == 'tbl':
        tbls.append(c)

print(f'Paragraphs: {len(paras)}, Tables: {len(tbls)}')

# Debug: show interleaving to verify table positions
child_order = []
pi, ti = 0, 0
for c in children:
    lt = c.tag.split('}')[-1] if '}' in c.tag else c.tag
    if lt == 'p':
        txt = ''
        for t_el in c.iter(qn('w:t')):
            if t_el.text:
                txt += t_el.text
        child_order.append(('p', pi, txt[:60]))
        pi += 1
    elif lt == 'tbl':
        child_order.append(('tbl', ti, ''))
        ti += 1

# Print table positions
for item in child_order:
    if item[0] == 'tbl':
        prev_items = [x for x in child_order if child_order.index(x) < child_order.index(item)]
        last_para = [x for x in prev_items if x[0] == 'p']
        if last_para:
            lp = last_para[-1]
            print(f'  Table {item[1]} appears after para {lp[1]}: "{lp[2]}"')

# Remove all from body except sectPr
for c in children:
    if c is not sectPr:
        body.remove(c)

# ═══════════════════════════════════════════════════════════
# EMU calculations
# ═══════════════════════════════════════════════════════════
COL_W_TWIPS = int(COL_W_CM * 567)
COL_IMG_EMU = int(Cm(COL_W_CM - 1.0))   # column image width
FULL_IMG_EMU = int(Cm(CONTENT_W_CM))      # full-width image

def before_sectPr(element):
    idx = list(body).index(sectPr)
    body.insert(idx, element)

def section_header(cell, text):
    h = make_p(text, SECTION_HEADER_PT, bold=True, color_hex='FFFFFF',
               bg_hex='1F4E79', space_before=120, space_after=80)
    cell.append(h)

def add_para(cell, idx, font_scale=FONT_SCALE, img_emu=None):
    if idx >= len(paras):
        return
    el = paras[idx]
    scale_fonts(el, font_scale)
    if img_emu is None:
        img_emu = COL_IMG_EMU
    scale_images(el, img_emu)
    cell.append(el)

def add_tbl(cell, idx, font_scale=TABLE_FONT_SCALE):
    if idx >= len(tbls):
        return
    el = tbls[idx]
    scale_fonts(el, font_scale)
    cell.append(el)

def spacer(cell, pts=6):
    cell.append(make_p('', pts))

def clean_empty_p(cell):
    """Remove the initial empty paragraph from a cell (keep at least 1)."""
    ps = cell.findall(qn('w:p'))
    if len(ps) > 1:
        # Remove the first one if it's empty
        first = ps[0]
        has_content = False
        for t_el in first.iter(qn('w:t')):
            if t_el.text and t_el.text.strip():
                has_content = True
        if not has_content and len(first.findall(qn('w:drawing'))) == 0:
            cell.remove(first)

# ═══════════════════════════════════════════════════════════
# BUILD POSTER
# ═══════════════════════════════════════════════════════════

# ─── TITLE BANNER (full width) ───────────────────────────
# Para 0: logo
el = paras[0]
scale_images(el, FULL_IMG_EMU)
before_sectPr(el)

# Para 1: title
el = paras[1]
scale_fonts(el, TITLE_FONT_SCALE)
before_sectPr(el)

# Para 2: authors (Korean)
el = paras[2]
scale_fonts(el, AUTHOR_FONT_SCALE)
before_sectPr(el)

# Para 3: authors (English)
el = paras[3]
scale_fonts(el, AUTHOR_FONT_SCALE)
before_sectPr(el)

# Para 4: affiliation
el = paras[4]
scale_fonts(el, AFFIL_FONT_SCALE)
before_sectPr(el)

# Title separator bar
sep = make_p(' ', 4, bg_hex='1F4E79', space_before=80, space_after=80)
before_sectPr(sep)

# ─── 3-COLUMN LAYOUT TABLE ───────────────────────────────
layout_tbl, cells = make_layout_table(
    [COL_W_TWIPS, COL_W_TWIPS, COL_W_TWIPS],
    cell_pad_twips=int(COL_GAP_CM / 2 * 567)
)
before_sectPr(layout_tbl)
cell1, cell2, cell3 = cells

# ─── COLUMN 1: 서론 + 방법론 ─────────────────────────────
section_header(cell1, '1. 서론 (Introduction)')
add_para(cell1, 8)   # intro paragraph 1
add_para(cell1, 9)   # intro paragraph 2

spacer(cell1)
section_header(cell1, 'Key Findings Preview')
add_para(cell1, 10)
add_para(cell1, 11)

spacer(cell1)
section_header(cell1, '2. 연구 문제 (Research Questions)')
add_para(cell1, 15)  # RQ1
add_para(cell1, 16)  # RQ2
add_para(cell1, 17)  # RQ3

spacer(cell1)
section_header(cell1, '3. 실험 설계 (Methodology)')
# Fig 1 images
add_para(cell1, 20)  # Fig 1 left
add_para(cell1, 22)  # Fig 1 right
add_para(cell1, 23)  # Fig 1 caption

spacer(cell1, 4)
# Experimental Setup
add_para(cell1, 25)  # "Experimental Setup:"
add_para(cell1, 26)  # setup item 1
add_para(cell1, 27)  # setup item 2
add_para(cell1, 28)  # setup item 3
add_para(cell1, 29)  # setup item 4

spacer(cell1, 4)
add_para(cell1, 30)  # "Player Archetypes:"
add_tbl(cell1, 1)    # Table 1: Player Archetypes (5x4)

spacer(cell1, 4)
add_para(cell1, 32)  # "Curriculum Stages:"
add_tbl(cell1, 2)    # Table 2: Curriculum Stages (4x4)

# ─── COLUMN 2: RQ1 + RQ2 결과 ────────────────────────────
section_header(cell2, '4. RQ1 — 행동 다양성 분석')
add_para(cell2, 35)  # Fig 2A
add_para(cell2, 36)  # Fig 2B
add_para(cell2, 37)  # Fig 2 caption

spacer(cell2, 4)
add_para(cell2, 39)  # "Key Findings:"
add_para(cell2, 40)
add_para(cell2, 41)
add_para(cell2, 42)
add_para(cell2, 43)

spacer(cell2, 4)
add_tbl(cell2, 0)    # Table 0: Key comparison (5x5)

spacer(cell2)
section_header(cell2, '5. RQ2 — 과학습 분석')
add_para(cell2, 46)  # Fig 3A
add_para(cell2, 47)  # Fig 3B
add_para(cell2, 48)  # Fig 3 caption

spacer(cell2, 4)
add_para(cell2, 50)  # "Key Findings:"
add_para(cell2, 51)
add_para(cell2, 52)
add_para(cell2, 53)
add_para(cell2, 54)
add_para(cell2, 55)
add_para(cell2, 56)

# ─── COLUMN 3: RQ3 + 토의 + 결론 ─────────────────────────
section_header(cell3, '6. RQ3 — 승률의 한계')
add_para(cell3, 59)  # Fig 4A
add_para(cell3, 60)  # Fig 4B
add_para(cell3, 61)  # Fig 4 caption
add_para(cell3, 62)  # "Key Findings:"
add_para(cell3, 63)
add_para(cell3, 64)
add_para(cell3, 65)

spacer(cell3, 4)
add_para(cell3, 66)  # "Outcome Distribution Analysis"
add_para(cell3, 67)  # Fig 5
add_para(cell3, 68)  # Fig 5 caption
add_para(cell3, 69)  # "추가 발견:"
add_para(cell3, 70)
add_para(cell3, 71)
add_para(cell3, 72)

spacer(cell3)
section_header(cell3, '7. 토의 (Discussion)')
add_para(cell3, 76)  # Q1
add_para(cell3, 77)
add_para(cell3, 78)  # Q2
add_para(cell3, 79)
add_para(cell3, 80)  # Q3
add_para(cell3, 81)

spacer(cell3)
section_header(cell3, '8. 결론 (Conclusions)')
add_para(cell3, 85)  # Finding 1
add_para(cell3, 86)
add_para(cell3, 87)  # Finding 2
add_para(cell3, 88)
add_para(cell3, 89)  # Finding 3
add_para(cell3, 90)

spacer(cell3)
section_header(cell3, '향후 과제 (Future Work)')
add_para(cell3, 94)
add_para(cell3, 95)
add_para(cell3, 96)
add_para(cell3, 97)

# Clean initial empty paragraphs from cells
for c in cells:
    clean_empty_p(c)

# ─── FOOTER: Appendix + References ───────────────────────
footer_sep = make_p(' ', 4, bg_hex='1F4E79', space_before=60, space_after=60)
before_sectPr(footer_sep)

# Appendix - two tables side by side
footer_tbl, footer_cells = make_layout_table(
    [int(CONTENT_W_CM * 0.35 * 567), int(CONTENT_W_CM * 0.65 * 567)],
    cell_pad_twips=170
)

add_para(footer_cells[0], 105, font_scale=TABLE_FONT_SCALE)  # "Table A1..."
add_tbl(footer_cells[0], 3, font_scale=TABLE_FONT_SCALE * 0.85)  # PPO params

add_para(footer_cells[1], 107, font_scale=TABLE_FONT_SCALE)  # "Table A2..."
add_tbl(footer_cells[1], 4, font_scale=TABLE_FONT_SCALE * 0.85)  # Performance
add_para(footer_cells[1], 109, font_scale=TABLE_FONT_SCALE * 0.85)  # Stats line

for fc in footer_cells:
    clean_empty_p(fc)

before_sectPr(footer_tbl)

# References header
ref_h = make_p('References', 20, bold=True, color_hex='1F4E79',
               space_before=120, space_after=60)
before_sectPr(ref_h)

for idx in [113, 114, 115, 116, 117, 118]:
    el = paras[idx]
    scale_fonts(el, REF_FONT_SCALE)
    before_sectPr(el)

# ═══════════════════════════════════════════════════════════
# Save & Verify
# ═══════════════════════════════════════════════════════════
import os
os.makedirs(os.path.dirname(DST), exist_ok=True)
doc.save(DST)
print(f'\nSaved: {DST}')

# Quick verification
doc2 = Document(DST)
s = doc2.sections[0]
print(f'Page: {s.page_width.cm:.1f} x {s.page_height.cm:.1f} cm')
print(f'Paragraphs: {len(doc2.paragraphs)}, Tables: {len(doc2.tables)}')

for i, p in enumerate(doc2.paragraphs[:8]):
    if p.text.strip() and p.runs:
        sz = p.runs[0].font.size
        sz_str = f'{sz.pt:.0f}pt' if sz else 'inh'
        print(f'  [{i}] {sz_str}: {p.text[:70]}')
