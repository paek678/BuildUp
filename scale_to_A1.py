"""
기존 포스터 docx → A1 크기로 스케일 변환
- 페이지: Letter → A1 (59.4 × 84.1 cm)
- 폰트: ~2.8x 스케일
- 이미지: 가용 너비에 맞춰 스케일
- 여백: 비례 확대
- 테이블: 폰트 + 셀 크기 스케일
"""
import copy, sys, os
sys.stdout.reconfigure(encoding='utf-8')

from docx import Document
from docx.shared import Pt, Cm, Emu, Inches
from docx.oxml.ns import qn
from lxml import etree

SRC = r'C:\Users\paek6\Downloads\매치업별 특화 강화학습을 활용한 적응형 보스 AI 설계 및 분석_포스터.docx'
DST = r'C:\Users\paek6\Downloads\Buildup\Buildup\poster_output\BossAI_Poster_A1_scaled.docx'

# A1 dimensions
A1_W = Cm(59.4)
A1_H = Cm(84.1)

# Scale factor (Letter width → A1 width)
LETTER_W = 21.6  # cm
A1_W_CM = 59.4
SCALE = A1_W_CM / LETTER_W  # ≈ 2.75

# Original content: 18.6 x 25.5 cm → A1 content: 54.4 x 80.1 cm
# Width scale: 2.93x, Height scale: 3.14x
FONT_SCALE = 2.85
IMG_SCALE = 2.9

MARGIN_CM = 2.5  # A1 여백

def scale_font_size(run, scale):
    """Run의 폰트 크기를 스케일링"""
    if run.font.size:
        new_size = int(run.font.size * scale)
        run.font.size = new_size

def scale_paragraph_spacing(para, scale):
    """단락 간격 스케일링"""
    pf = para.paragraph_format
    if pf.space_before and pf.space_before > 0:
        pf.space_before = int(pf.space_before * scale)
    if pf.space_after and pf.space_after > 0:
        pf.space_after = int(pf.space_after * scale)

def scale_run_fonts(runs, scale):
    for run in runs:
        scale_font_size(run, scale)

def process_paragraph(para, font_scale, img_scale, max_width_emu):
    """단락 내 폰트 스케일 + 이미지 스케일"""
    scale_paragraph_spacing(para, font_scale)

    for run in para.runs:
        scale_font_size(run, font_scale)

        # 이미지 처리
        for drawing in run._element.findall(qn('w:drawing')):
            for inline in drawing.findall(qn('wp:inline')):
                extent = inline.find(qn('wp:extent'))
                if extent is not None:
                    cx = int(extent.get('cx', 0))
                    cy = int(extent.get('cy', 0))
                    if cx > 0 and cy > 0:
                        new_cx = int(cx * img_scale)
                        new_cy = int(cy * img_scale)
                        # 최대 너비 제한
                        if new_cx > max_width_emu:
                            ratio = max_width_emu / new_cx
                            new_cx = int(new_cx * ratio)
                            new_cy = int(new_cy * ratio)
                        extent.set('cx', str(new_cx))
                        extent.set('cy', str(new_cy))

                        # graphic 내부 extent도 업데이트
                        for graphic in inline.iter():
                            if graphic.tag.endswith('}ext') or graphic.tag.endswith('}chExt'):
                                if graphic.get('cx'):
                                    graphic.set('cx', str(new_cx))
                                if graphic.get('cy'):
                                    graphic.set('cy', str(new_cy))

            # anchor 타입 이미지도 처리
            for anchor in drawing.findall(qn('wp:anchor')):
                extent = anchor.find(qn('wp:extent'))
                if extent is not None:
                    cx = int(extent.get('cx', 0))
                    cy = int(extent.get('cy', 0))
                    if cx > 0 and cy > 0:
                        new_cx = int(cx * img_scale)
                        new_cy = int(cy * img_scale)
                        if new_cx > max_width_emu:
                            ratio = max_width_emu / new_cx
                            new_cx = int(new_cx * ratio)
                            new_cy = int(new_cy * ratio)
                        extent.set('cx', str(new_cx))
                        extent.set('cy', str(new_cy))

def process_table(table, font_scale, img_scale, max_width_emu):
    """테이블 내 모든 셀의 폰트/이미지 스케일링"""
    for row in table.rows:
        # 행 높이 스케일
        tr = row._tr
        trPr = tr.find(qn('w:trPr'))
        if trPr is not None:
            trHeight = trPr.find(qn('w:trHeight'))
            if trHeight is not None:
                val = trHeight.get(qn('w:val'))
                if val:
                    try:
                        new_val = int(int(val) * font_scale)
                        trHeight.set(qn('w:val'), str(new_val))
                    except ValueError:
                        pass

        for cell in row.cells:
            for para in cell.paragraphs:
                process_paragraph(para, font_scale, img_scale, max_width_emu)

            # 셀 너비 스케일
            tc = cell._tc
            tcPr = tc.find(qn('w:tcPr'))
            if tcPr is not None:
                tcW = tcPr.find(qn('w:tcW'))
                if tcW is not None:
                    w_val = tcW.get(qn('w:w'))
                    if w_val:
                        try:
                            new_w = int(int(w_val) * SCALE)
                            tcW.set(qn('w:w'), str(new_w))
                        except ValueError:
                            pass

def main():
    print(f'Loading: {SRC}')
    doc = Document(SRC)

    # 1. 페이지 크기 변경
    for section in doc.sections:
        section.page_width = A1_W
        section.page_height = A1_H
        section.left_margin = Cm(MARGIN_CM)
        section.right_margin = Cm(MARGIN_CM)
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)

    content_w = A1_W_CM - 2 * MARGIN_CM  # cm
    max_width_emu = int(Cm(content_w))

    print(f'Page: A1 ({A1_W_CM}x84.1cm), Margins: {MARGIN_CM}cm')
    print(f'Font scale: {FONT_SCALE}x, Image scale: {IMG_SCALE}x')
    print(f'Content width: {content_w}cm')

    # 2. 본문 단락 처리
    para_count = 0
    for para in doc.paragraphs:
        process_paragraph(para, FONT_SCALE, IMG_SCALE, max_width_emu)
        para_count += 1
    print(f'Processed {para_count} paragraphs')

    # 3. 테이블 처리
    tbl_count = 0
    for table in doc.tables:
        process_table(table, FONT_SCALE, IMG_SCALE, max_width_emu)

        # 테이블 전체 너비도 스케일
        tbl_element = table._tbl
        tblPr = tbl_element.find(qn('w:tblPr'))
        if tblPr is not None:
            tblW = tblPr.find(qn('w:tblW'))
            if tblW is not None:
                w_val = tblW.get(qn('w:w'))
                if w_val:
                    try:
                        new_w = int(int(w_val) * SCALE)
                        tblW.set(qn('w:w'), str(new_w))
                    except ValueError:
                        pass

            # 테이블 들여쓰기 스케일
            tblInd = tblPr.find(qn('w:tblInd'))
            if tblInd is not None:
                w_val = tblInd.get(qn('w:w'))
                if w_val:
                    try:
                        new_w = int(int(w_val) * SCALE)
                        tblInd.set(qn('w:w'), str(new_w))
                    except ValueError:
                        pass

        # tblGrid 컬럼 너비 스케일
        tblGrid = tbl_element.find(qn('w:tblGrid'))
        if tblGrid is not None:
            for gridCol in tblGrid.findall(qn('w:gridCol')):
                w_val = gridCol.get(qn('w:w'))
                if w_val:
                    try:
                        new_w = int(int(w_val) * SCALE)
                        gridCol.set(qn('w:w'), str(new_w))
                    except ValueError:
                        pass

        tbl_count += 1
    print(f'Processed {tbl_count} tables')

    # 4. 헤더/푸터 처리
    for section in doc.sections:
        for hf in [section.header, section.footer]:
            if hf and hf.paragraphs:
                for para in hf.paragraphs:
                    process_paragraph(para, FONT_SCALE, IMG_SCALE, max_width_emu)

    # 5. 저장
    doc.save(DST)
    print(f'\nDone: {DST}')

    # 검증
    doc2 = Document(DST)
    for section in doc2.sections:
        print(f'Verify — Page: {section.page_width.cm:.1f} x {section.page_height.cm:.1f} cm')

    # 페이지 수 추정 (단락/이미지 기반)
    print(f'Paragraphs: {len(doc2.paragraphs)}, Tables: {len(doc2.tables)}')

    # 첫 몇 단락의 폰트 크기 확인
    for i, p in enumerate(doc2.paragraphs[:5]):
        if p.text.strip() and p.runs:
            sz = p.runs[0].font.size
            sz_str = f'{sz.pt:.0f}pt' if sz else 'inherit'
            print(f'  [{i}] {sz_str}: {p.text[:60]}')

if __name__ == '__main__':
    main()
