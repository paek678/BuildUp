"""
A1 학술 포스터 생성기 — 2단 레이아웃
- A1 (59.4 × 84.1 cm), 2-column
- 글씨 축소 + 그림 확대 버전
"""
import os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

BASE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(BASE, 'poster_output', 'figures_v10')
OUT_DIR = os.path.join(BASE, 'poster_output')
BANNER_DIR = os.path.join(OUT_DIR, 'banners_A1')
os.makedirs(BANNER_DIR, exist_ok=True)

# A1
A1_W_CM = 59.4
A1_H_CM = 84.1
MARGIN_CM = 1.5
COL_GAP_CM = 0.8
CONTENT_W = A1_W_CM - 2 * MARGIN_CM  # 56.4cm
COL_W = (CONTENT_W - COL_GAP_CM) / 2  # ~27.8cm

# Colors
PRIMARY = '#1B3A5C'
SECONDARY = '#2E6B9E'
ACCENT = '#4A90D9'
LIGHT_BG = '#EDF3FA'
WHITE = '#FFFFFF'
DARK_TEXT = '#1A1A1A'
GRAY_TEXT = '#505050'

# Font sizes — 2단용 축소
BODY_SZ = 11
SMALL_SZ = 10
CAPTION_SZ = 9
BULLET_SZ = 11
TABLE_SZ = 9

# Spacing — 촘촘하게
SEC_GAP_BEFORE = 8
SEC_GAP_AFTER = 3
PARA_AFTER = 2
BULLET_GAP = 1
FIG_GAP = 3
LINE_SP = 1.1
SEP_COLOR = 'A8C8E8'

KR_FONT = 'Malgun Gothic'
EN_FONT = 'Calibri'
X = '×'

# ══════════════════════════════════════════════════════════════
# 배너
# ══════════════════════════════════════════════════════════════

def make_title_banner():
    fig, ax = plt.subplots(figsize=(CONTENT_W * 0.394, 2.6))
    grad = np.linspace(0, 1, 256).reshape(1, -1)
    cmap = LinearSegmentedColormap.from_list('t', ['#3A6FA0', '#5A96C8', '#7AB4E0'])
    ax.imshow(grad, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    ax.text(0.48, 0.75,
            'Adaptive Boss AI Design and Analysis through Matchup-Specialized Reinforcement Learning',
            ha='center', va='center', fontsize=22, color='white', fontweight='bold', family=EN_FONT)
    ax.text(0.48, 0.48,
            '매치업별 특화 강화학습을 활용한 보스전 적응 AI 설계 및 분석',
            ha='center', va='center', fontsize=16, color='#E8F0FA', family=KR_FONT)
    ax.text(0.48, 0.22, '백성열    홍채영    곽다영    김지형*',
            ha='center', va='center', fontsize=13, color='white', fontweight='bold', family=KR_FONT)
    ax.text(0.48, 0.06,
            '국립금오공과대학교 (Kumoh National Institute of Technology)    *kimjihyung@kumoh.ac.kr',
            ha='center', va='center', fontsize=10, color='#D0E4F6', family=KR_FONT)
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    path = os.path.join(BANNER_DIR, 'title_banner_2col.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', pad_inches=0)
    plt.close()
    return path


def make_section_banner(text, filename):
    w = COL_W
    fig, ax = plt.subplots(figsize=(w * 0.394, 0.38))
    grad = np.linspace(0, 1, 256).reshape(1, -1)
    cmap = LinearSegmentedColormap.from_list('s', ['#4A90D9', '#6BB5F0', '#8CC8F8'])
    ax.imshow(grad, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    ax.text(0.02, 0.5, text, ha='left', va='center',
            fontsize=12, color='white', fontweight='bold', family=EN_FONT)
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    path = os.path.join(BANNER_DIR, filename)
    fig.savefig(path, dpi=200, bbox_inches='tight', pad_inches=0)
    plt.close()
    return path


# ══════════════════════════════════════════════════════════════
# docx 헬퍼
# ══════════════════════════════════════════════════════════════

def set_cell_bg(cell, color_hex):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex.lstrip("#")}"/>')
    cell._tc.get_or_add_tcPr().append(shading)

def set_cell_margins(cell, top=0, bottom=0, left=80, right=80):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'  <w:top w:w="{top}" w:type="dxa"/>'
        f'  <w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'  <w:left w:w="{left}" w:type="dxa"/>'
        f'  <w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>')
    tcPr.append(tcMar)

def no_border(cell):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'  <w:top w:val="none" w:sz="0" w:color="auto"/>'
        f'  <w:bottom w:val="none" w:sz="0" w:color="auto"/>'
        f'  <w:left w:val="none" w:sz="0" w:color="auto"/>'
        f'  <w:right w:val="none" w:sz="0" w:color="auto"/>'
        f'</w:tcBorders>')
    tcPr.append(borders)

def add_run(para, text, sz=BODY_SZ, bold=False, color=None, font=KR_FONT):
    run = para.add_run(text)
    run.font.size = Pt(sz)
    run.font.name = font
    run._element.rPr.rFonts.set(qn('w:eastAsia'), KR_FONT)
    if bold: run.font.bold = True
    if color: run.font.color.rgb = RGBColor.from_string(color.lstrip('#'))
    return run

def add_para(cell, text='', sz=BODY_SZ, bold=False, color=None, align='left',
             space_before=0, space_after=PARA_AFTER, font=KR_FONT):
    p = cell.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = LINE_SP
    if align == 'center': pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == 'right': pf.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if text: add_run(p, text, sz=sz, bold=bold, color=color, font=font)
    return p

def add_banner(cell, banner_path):
    p = cell.add_paragraph()
    p.paragraph_format.space_before = Pt(SEC_GAP_BEFORE)
    p.paragraph_format.space_after = Pt(SEC_GAP_AFTER)
    p.add_run().add_picture(banner_path, width=Cm(COL_W))

def add_figure(cell, fig_name, width=None, caption=''):
    fig_path = os.path.join(FIG_DIR, fig_name)
    if not os.path.exists(fig_path):
        add_para(cell, f'[Missing: {fig_name}]', sz=SMALL_SZ, color='FF0000')
        return
    p = cell.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    w = width or Cm(COL_W - 0.4)
    p.add_run().add_picture(fig_path, width=w)
    if caption:
        cp = add_para(cell, '', sz=CAPTION_SZ, color=GRAY_TEXT, align='left',
                       space_before=1, space_after=FIG_GAP)
        add_run(cp, caption, sz=CAPTION_SZ, bold=True, color='3057B9')

def add_bullet(cell, text, sz=BULLET_SZ):
    p = add_para(cell, '', sz=sz, space_before=1, space_after=BULLET_GAP)
    add_run(p, '  •  ', sz=sz, bold=True, color=ACCENT)
    add_run(p, text, sz=sz)

def add_table_in_cell(cell, headers, rows):
    tbl = cell.add_table(rows=1 + len(rows), cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(headers):
        c = tbl.cell(0, j); c.text = ''
        p = c.paragraphs[0]
        add_run(p, h, sz=TABLE_SZ, bold=True, color='FFFFFF')
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cell_bg(c, PRIMARY)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = tbl.cell(i + 1, j); c.text = ''
            p = c.paragraphs[0]
            add_run(p, str(val), sz=TABLE_SZ)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_cell_bg(c, LIGHT_BG if i % 2 == 0 else WHITE)
    return tbl

def add_separator(cell, space=6):
    p = cell.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(space)
    pf.space_after = Pt(space)
    pPr = p._p.get_or_add_pPr()
    pBdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}>'
        f'  <w:bottom w:val="single" w:sz="2" w:color="{SEP_COLOR}" w:space="1"/>'
        f'</w:pBdr>')
    pPr.append(pBdr)


# ══════════════════════════════════════════════════════════════
# 메인
# ══════════════════════════════════════════════════════════════

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print('Generating 2-col A1 banners...')
    title_path = make_title_banner()
    banners = {}
    for text, fname in [
        ('1. Introduction', 'sec2_intro.png'),
        ('2. Research Objectives', 'sec2_rq.png'),
        ('3. Method', 'sec2_method.png'),
        ('RQ1: Adaptive Combat Behavior', 'sec2_rq1.png'),
        ('RQ2: Overfitting Patterns', 'sec2_rq2.png'),
        ('RQ3: Win Rate Is Not Enough', 'sec2_rq3.png'),
        ('4. Discussion', 'sec2_disc.png'),
        ('5. Conclusion', 'sec2_conc.png'),
        ('References', 'sec2_ref.png'),
    ]:
        banners[fname] = make_section_banner(text, fname)
    print('  Banners done.')

    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(A1_W_CM)
    section.page_height = Cm(A1_H_CM)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(1.0)
    section.left_margin = Cm(MARGIN_CM)
    section.right_margin = Cm(MARGIN_CM)

    # 타이틀
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(6)
    p.add_run().add_picture(title_path, width=Cm(CONTENT_W))

    # 2단 테이블
    tbl = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    for row in tbl.rows:
        for cell in row.cells:
            cell.width = Cm(COL_W)
            no_border(cell)
            set_cell_margins(cell, top=40, bottom=40, left=80, right=80)
            if cell.paragraphs:
                cell.paragraphs[0].text = ''

    L = tbl.cell(0, 0)
    R = tbl.cell(0, 1)

    # ══════════════════════════════════════════════
    # 왼쪽: Intro → RQ → Method → RQ1
    # ══════════════════════════════════════════════
    print('  Building left column...')

    # Introduction
    add_banner(L, banners['sec2_intro.png'])
    add_para(L, ' 액션 게임에서 보스 AI가 매번 동일하게 행동할 경우 플레이어의 흥미가 빠르게 감소한다. '
             '기존 보스 AI는 Behavior Tree 등 규칙 기반 방식에 의존하므로 전투 패턴이 고정되기 쉽고, '
             '다양한 플레이어 조합에 유연하게 대응하기 어렵다.',
             sz=BODY_SZ, space_before=3, space_after=2)
    add_para(L, f' 본 연구에서는 강화학습(RL)을 활용하여 보스 AI가 스스로 전투 방법을 학습할 수 있는지 분석한다. '
             f'보스에게 5가지 행동(Idle/Forward/Retreat/Turn L/Turn R)을 부여하고, '
             f'PPO 알고리즘으로 CC{X}CC를 제외한 9종 매치업, 총 55M steps를 학습시켰다.',
             sz=BODY_SZ, space_after=2)
    add_para(L, ' 핵심 기여: (1) 매치업별 상이한 전투 행동의 자연발생 실증, '
             '(2) 과학습 유형 3가지 분류, (3) 승률 단일 지표의 한계 정량적 입증.',
             sz=BODY_SZ, space_after=2)

    p = add_para(L, '', sz=BODY_SZ, space_before=2, space_after=2)
    add_run(p, 'Key Findings Preview: ', sz=BODY_SZ, bold=True, color=PRIMARY, font=EN_FONT)
    add_run(p, '같은 승률 82%인 두 매치업에서 대기 비율이 19% vs 2.4%로 완전히 상이. '
            '승률만으로는 학습 품질을 판단할 수 없음.', sz=BODY_SZ)
    add_separator(L)

    # Research Objectives
    add_banner(L, banners['sec2_rq.png'])
    add_bullet(L, f'RQ1. 9종 매치업별 전투 방식 차이 확인 (→ Fig. 2)')
    add_bullet(L, f'RQ2. 과학습 현상의 유형별 분류 (→ Fig. 3)')
    add_bullet(L, f'RQ3. 승률 단일 지표의 한계 검증 (→ Fig. 4)')
    add_separator(L)

    # Method
    add_banner(L, banners['sec2_method.png'])
    add_figure(L, 'fig01_method.png', caption='Fig. 1. Curriculum pipeline (left) and observation/action space (right).')

    p = add_para(L, '', sz=BODY_SZ, space_before=3, space_after=2)
    add_run(p, 'Experimental Setup:', sz=BODY_SZ, bold=True)
    add_bullet(L, f'Unity 6 3D 톱다운 액션 게임, 보스 1 vs 플레이어 2(BT 봇)')
    add_bullet(L, f'PPO, 129채널 관측(HP/거리/스킬 쿨다운 등), 5가지 이산 행동')
    add_bullet(L, f'Touch(5M)→Engage(10M)→Combat(40M), 총 55M steps')
    add_bullet(L, f'매치업당 ~1,000판, 마지막 100판 평균 평가')
    add_bullet(L, f'보상 설계: 거리 보상 + 공격 적중 + 승리 보너스의 가중합')
    add_separator(L, space=2)

    p = add_para(L, '', sz=BODY_SZ, space_before=3, space_after=2)
    add_run(p, 'Player Archetypes:', sz=BODY_SZ, bold=True)
    add_table_in_cell(L,
        ['Archetype', 'Role', 'Range', 'Key Skills'],
        [
            ['Melee', 'Close-range burst', '5-10m', 'ExecutionSpike, CrushingBarrage'],
            ['Ranged', 'Long-range kite', '20-30m', 'PiercingShot, RuptureMagazine'],
            ['CC', 'Crowd control', '8-14m', 'SealChain, CollapseRoar'],
            ['Hybrid', 'Flexible survivor', '6-30m', 'SurvivalPulse, OverchargeMode'],
        ])
    add_para(L, f' 4종 아키타입 조합 중 CC{X}CC는 교착 상태로 제외, 총 9종 매치업 학습.',
             sz=SMALL_SZ, space_before=2, space_after=2)
    add_separator(L)

    # RQ1
    add_banner(L, banners['sec2_rq1.png'])
    add_figure(L, 'fig02_learning.png', caption='Fig. 2. (A) Group reward curves. (B) Final action distribution by matchup.')

    p = add_para(L, '', sz=BODY_SZ, space_before=3, space_after=2)
    add_run(p, 'Key Findings:', sz=BODY_SZ, bold=True)
    add_bullet(L, '9종 매치업 모두 보상이 양(+)으로 수렴.')
    add_bullet(L, 'Melee 상대 → Forward 위주, Ranged 상대 → Retreat+Rotation 위주. 유형별 이동 전략 차이.')
    add_bullet(L, f'M{X}M Idle 19% vs CC/Hybrid 상대 2~3%. 순수 전투형에는 "대기 후 반격" 전략.')
    add_bullet(L, '결론: 상대 조합에 따라 다른 전투 행동 학습 확인.')

    p = add_para(L, '', sz=SMALL_SZ, space_before=3, space_after=2)
    add_run(p, 'Action Distribution: ', sz=SMALL_SZ, bold=True, color=PRIMARY, font=EN_FONT)
    add_run(p, f'Melee 조합 Forward 40%+, Ranged 조합 Retreat 30%+Turn 25%. '
            f'행동 분포가 명확히 분리됨.', sz=SMALL_SZ)

    # ══════════════════════════════════════════════
    # 오른쪽: RQ2 → RQ3 → Discussion → Conclusion → Ref
    # ══════════════════════════════════════════════
    print('  Building right column...')

    # RQ2
    add_banner(R, banners['sec2_rq2.png'])
    add_figure(R, 'fig03_overfitting.png', caption='Fig. 3. Reward/WR trends for 4 representative matchups. Overfitting causes mid-training drops.')

    p = add_para(R, '', sz=BODY_SZ, space_before=3, space_after=2)
    add_run(p, 'Key Findings:', sz=BODY_SZ, bold=True)
    add_para(R, '강화학습에서 과학습(overfitting)이란 과도한 학습으로 인해 오히려 성능이 저하되는 현상이다. '
             '본 실험에서 3가지 유형이 관찰되었다:', sz=BODY_SZ, space_after=2)
    add_bullet(R, f'Type 1 — Sharp Drop (R{X}R): 승률 급락 후 일부 회복')
    add_bullet(R, f'Type 2 — Double Dip (H{X}H): 반복적 성능 하락')
    add_bullet(R, f'Type 3 — Gradual Decay (H{X}R): 점진적 하락, 탐지 어려움')
    add_bullet(R, f'Control — Stable (C{X}H): 안정적 학습 완료')
    add_separator(R, space=2)
    add_para(R, f'→ 유사 유형 조합(R{X}R, H{X}H)에서 overfitting 집중 발생. '
             f'상대 행동이 단순할수록 해당 패턴에만 과적합.',
             sz=BODY_SZ, bold=True, space_before=2, space_after=2)
    add_separator(R)

    # RQ3
    add_banner(R, banners['sec2_rq3.png'])
    add_figure(R, 'fig04_idle.png', caption='Fig. 4. (A) Idle ratio trends. (B) WR vs Idle scatter (r=-0.23, n.s.).')

    p = add_para(R, '', sz=BODY_SZ, space_before=3, space_after=2)
    add_run(p, 'Key Findings:', sz=BODY_SZ, bold=True)
    add_bullet(R, f'M{X}M, M{X}H 둘 다 WR 82%이나 Idle 19% vs 2.4%로 정반대.')
    add_bullet(R, 'WR과 Idle 간 유의미한 상관 없음 (r=-0.23, n.s.).')
    add_bullet(R, '높은 승률이 반드시 적극적 전투를 의미하지 않음.')
    add_separator(R)

    # Discussion
    add_banner(R, banners['sec2_disc.png'])
    p = add_para(R, '', sz=BODY_SZ, space_before=3, space_after=2)
    add_run(p, 'Q1. 유사 유형 매치업의 overfitting 원인?', sz=BODY_SZ, bold=True)
    add_para(R, f' 유사 유형 → 단조로운 행동 → 과적합. '
             f'반면 C{X}H처럼 다양한 조합에서는 범용적 전략 학습. '
             f'BT 봇의 고정된 행동 패턴이 과적합을 가속화.',
             sz=BODY_SZ, space_after=2)
    add_separator(R, space=2)
    p = add_para(R, '', sz=BODY_SZ, space_before=2, space_after=2)
    add_run(p, 'Q2. 실제 게임 적용 시?', sz=BODY_SZ, bold=True)
    add_para(R, ' BT 봇 회피 불가로 승률 과대 측정. 실제 플레이어 대상 시 보스 HP 하향 및 '
             'Early Stopping과 다중 지표 모니터링 병행 필수.',
             sz=BODY_SZ, space_after=2)
    add_separator(R)

    # Conclusion
    add_banner(R, banners['sec2_conc.png'])
    add_bullet(R, 'Finding 1: 상대 유형별 상이한 전투 행동 학습 확인')
    add_bullet(R, 'Finding 2: 3가지 overfitting 패턴 발견 (유사 유형 집중)')
    add_bullet(R, 'Finding 3: 같은 WR 82%에서 Idle 19% vs 2.4%')
    add_separator(R, space=2)

    p = add_para(R, '', sz=BODY_SZ, space_before=3, space_after=2)
    add_run(p, 'Future Work:', sz=BODY_SZ, bold=True)
    add_bullet(R, 'Early stopping 도입으로 overfitting 방지')
    add_bullet(R, '실제 플레이어 대상 밸런스 조정 (보스 HP 하향)')
    add_bullet(R, '스킬 타이밍까지 행동 공간 확장')
    add_separator(R)

    # References
    add_banner(R, banners['sec2_ref.png'])
    refs = [
        '[1] I. Millington and J. Funge, "AI for Games," CRC Press, 3rd ed., 2019.',
        '[2] O. Vinyals et al., "Grandmaster level in StarCraft II using multi-agent RL," Nature, 575, 2019.',
        '[3] C. Berner et al., "Dota 2 with large scale deep RL," arXiv:1912.06680, 2019.',
        '[4] J. Schulman et al., "Proximal policy optimization algorithms," arXiv:1707.06347, 2017.',
        '[5] A. Pan et al., "The effects of reward misspecification," Proc. ICLR, 2022.',
        '[6] A. Juliani et al., "Unity: A general platform for intelligent agents," arXiv:1809.02627, 2020.',
    ]
    for ref in refs:
        add_para(R, ref, sz=10, space_before=1, space_after=2, font=EN_FONT)

    # 테이블 외곽선 제거
    tblPr = tbl._tbl.tblPr if tbl._tbl.tblPr is not None else parse_xml(f'<w:tblPr {nsdecls("w")}/>')
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="none" w:sz="0" w:color="auto"/>'
        f'  <w:bottom w:val="none" w:sz="0" w:color="auto"/>'
        f'  <w:left w:val="none" w:sz="0" w:color="auto"/>'
        f'  <w:right w:val="none" w:sz="0" w:color="auto"/>'
        f'  <w:insideH w:val="none" w:sz="0" w:color="auto"/>'
        f'  <w:insideV w:val="none" w:sz="0" w:color="auto"/>'
        f'</w:tblBorders>')
    tblPr.append(borders)

    # 저장
    for name in ['BossAI_Poster_A1_2col.docx', 'BossAI_Poster_A1_2col_v2.docx', 'BossAI_Poster_A1_2col_v3.docx', 'BossAI_Poster_A1_2col_v4.docx']:
        out_path = os.path.join(OUT_DIR, name)
        try:
            doc.save(out_path)
            break
        except PermissionError:
            continue
    print(f'\nDone: {out_path}')


if __name__ == '__main__':
    main()
