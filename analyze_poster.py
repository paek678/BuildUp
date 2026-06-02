import sys
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document
from docx.shared import Pt, Inches, Cm

doc = Document(r'C:\Users\paek6\Downloads\매치업별 특화 강화학습을 활용한 적응형 보스 AI 설계 및 분석_포스터.docx')

for section in doc.sections:
    w = section.page_width
    h = section.page_height
    print(f'Page: {w.cm:.1f}cm x {h.cm:.1f}cm')
    print(f'Margins: L={section.left_margin.cm:.1f} R={section.right_margin.cm:.1f} T={section.top_margin.cm:.1f} B={section.bottom_margin.cm:.1f}')

print(f'Paragraphs: {len(doc.paragraphs)}, Tables: {len(doc.tables)}')
print()

# Check images
from docx.opc.constants import RELATIONSHIP_TYPE as RT
img_count = 0
for rel in doc.part.rels.values():
    if "image" in rel.reltype:
        img_count += 1
print(f'Images: {img_count}')
print()

for i, p in enumerate(doc.paragraphs):
    if p.text.strip():
        sz = None
        bold = False
        color = None
        if p.runs:
            r = p.runs[0]
            sz = r.font.size
            bold = r.font.bold
            if r.font.color and r.font.color.rgb:
                color = str(r.font.color.rgb)
        sz_str = f'{sz.pt:.0f}pt' if sz else 'inh'
        bl = 'B' if bold else ' '
        cl = color if color else '-'
        txt = p.text[:120]
        print(f'[{i:3d}] {sz_str:>5s} {bl} {cl:8s} | {txt}')

print('\n--- Tables ---')
for ti, table in enumerate(doc.tables):
    rows = len(table.rows)
    cols = len(table.columns)
    first_cell = table.cell(0, 0).text[:50] if rows > 0 and cols > 0 else ''
    print(f'Table {ti}: {rows}x{cols} | first cell: {first_cell}')
