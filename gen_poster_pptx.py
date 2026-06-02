"""
A1 포스터 PPTX — 정밀 배치 버전
모든 요소를 Y 커서로 순차 배치, 이미지 실측 높이 사용
"""
import os, sys, math
sys.stdout.reconfigure(encoding='utf-8')

from pptx import Presentation
from pptx.util import Cm, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(BASE, 'poster_output', 'figures_v10')
BANNER_DIR = os.path.join(BASE, 'poster_output', 'banners_A1')
OUT_DIR = os.path.join(BASE, 'poster_output')

A1_W = 59.4
A1_H = 84.1
MARGIN = 1.5
GAP = 0.8
CONTENT_W = A1_W - 2 * MARGIN
COL_W = (CONTENT_W - GAP) / 2
FIG_W = COL_W - 0.4

PRIMARY = RGBColor(0x1B, 0x3A, 0x5C)
ACCENT = RGBColor(0x4A, 0x90, 0xD9)
GRAY = RGBColor(0x50, 0x50, 0x50)
DARK = RGBColor(0x1A, 0x1A, 0x1A)
CAPTION_BLUE = RGBColor(0x30, 0x57, 0xB9)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
SEP_COLOR = RGBColor(0xA8, 0xC8, 0xE8)
LIGHT_BG = RGBColor(0xED, 0xF3, 0xFA)
TBL_HEADER_BG = RGBColor(0x1B, 0x3A, 0x5C)

KR = 'Malgun Gothic'
EN = 'Calibri'
X = '×'

# 폰트 크기별 줄 높이 추정 (cm) — 폰트크기 + 행간
def line_h(pt_size):
    return pt_size * 0.042  # 1pt ≈ 0.035cm, ×1.2 행간

def text_height(n_lines, pt_size=11):
    return n_lines * line_h(pt_size) + 0.15  # padding

def img_height(fig_name, width_cm, directory=FIG_DIR):
    path = os.path.join(directory, fig_name)
    if not os.path.exists(path):
        return 2.0
    img = Image.open(path)
    return width_cm * (img.height / img.width)

def banner_height(banner_name, width_cm):
    return img_height(banner_name, width_cm, BANNER_DIR)


class Column:
    def __init__(self, slide, x_cm, width_cm, start_y):
        self.slide = slide
        self.x = x_cm
        self.w = width_cm
        self.y = start_y

    def add_banner(self, banner_name):
        path = os.path.join(BANNER_DIR, banner_name)
        if not os.path.exists(path):
            self.y += 1.0
            return
        h = banner_height(banner_name, self.w)
        self.slide.shapes.add_picture(path, Cm(self.x), Cm(self.y), Cm(self.w), Cm(h))
        self.y += h + 0.1

    def add_image(self, fig_name, caption=''):
        path = os.path.join(FIG_DIR, fig_name)
        if not os.path.exists(path):
            self.y += 1.0
            return
        w = self.w - 0.4
        h = img_height(fig_name, w)
        self.slide.shapes.add_picture(path, Cm(self.x + 0.2), Cm(self.y), Cm(w), Cm(h))
        self.y += h + 0.1
        if caption:
            self._add_caption(caption)

    def _add_caption(self, text):
        h = text_height(2, 9)
        tb = self.slide.shapes.add_textbox(Cm(self.x), Cm(self.y), Cm(self.w), Cm(h))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.space_before = Pt(0)
        p.space_after = Pt(1)
        r = p.add_run()
        r.text = text
        r.font.size = Pt(9)
        r.font.bold = True
        r.font.color.rgb = CAPTION_BLUE
        r.font.name = EN
        self.y += h

    def add_text_block(self, lines):
        """lines: list of (text, kwargs) tuples"""
        total_lines = 0
        max_pt = 11
        for text, kw in lines:
            pt = kw.get('size', 11)
            if pt > max_pt:
                max_pt = pt
            chars_per_line = max(1, int(self.w * 2.8 / (pt * 0.04)))
            n = max(1, math.ceil(len(text) / chars_per_line))
            total_lines += n

        h = text_height(total_lines, max_pt) + 0.1
        tb = self.slide.shapes.add_textbox(Cm(self.x), Cm(self.y), Cm(self.w), Cm(h))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.paragraphs[0].text = ''

        for text, kw in lines:
            is_bullet = kw.pop('bullet', False)
            size = Pt(kw.get('size', 11))
            bold = kw.get('bold', False)
            color = kw.get('color', DARK)
            font = kw.get('font', KR)

            p = tf.add_paragraph()
            p.space_before = Pt(1)
            p.space_after = Pt(1)
            p.alignment = PP_ALIGN.LEFT

            if is_bullet:
                r1 = p.add_run()
                r1.text = '  •  '
                r1.font.size = size
                r1.font.bold = True
                r1.font.color.rgb = ACCENT
                r1.font.name = KR

            r = p.add_run()
            r.text = text
            r.font.size = size
            r.font.bold = bold
            r.font.color.rgb = color
            r.font.name = font

        self.y += h

    def add_mixed_para(self, runs_data):
        """runs_data: list of (text, kwargs)"""
        total_len = sum(len(t) for t, _ in runs_data)
        n_lines = max(1, math.ceil(total_len / 65))
        h = text_height(n_lines, 11) + 0.05
        tb = self.slide.shapes.add_textbox(Cm(self.x), Cm(self.y), Cm(self.w), Cm(h))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.space_before = Pt(1)
        p.space_after = Pt(1)
        for text, kw in runs_data:
            r = p.add_run()
            r.text = text
            r.font.size = Pt(kw.get('size', 11))
            r.font.bold = kw.get('bold', False)
            r.font.color.rgb = kw.get('color', DARK)
            r.font.name = kw.get('font', KR)
        self.y += h

    def add_separator(self):
        from pptx.util import Emu
        connector = self.slide.shapes.add_connector(
            1,  # MSO_CONNECTOR_TYPE.STRAIGHT
            Cm(self.x), Cm(self.y + 0.1),
            Cm(self.x + self.w), Cm(self.y + 0.1))
        connector.line.color.rgb = SEP_COLOR
        connector.line.width = Pt(0.5)
        self.y += 0.25

    def add_table(self, headers, rows, title=''):
        if title:
            h = text_height(1, 11)
            tb = self.slide.shapes.add_textbox(Cm(self.x), Cm(self.y), Cm(self.w), Cm(h))
            tf = tb.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]
            r = p.add_run(); r.text = title
            r.font.size = Pt(11); r.font.bold = True; r.font.color.rgb = DARK; r.font.name = KR
            self.y += h

        n_rows = 1 + len(rows)
        n_cols = len(headers)
        row_h = 0.55
        tbl_h = n_rows * row_h

        tbl_shape = self.slide.shapes.add_table(
            n_rows, n_cols, Cm(self.x), Cm(self.y), Cm(self.w), Cm(tbl_h))
        tbl = tbl_shape.table

        for j, hdr in enumerate(headers):
            cell = tbl.cell(0, j)
            cell.text = ''
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            r = p.add_run(); r.text = hdr
            r.font.size = Pt(9); r.font.bold = True; r.font.color.rgb = WHITE; r.font.name = EN
            cell.fill.solid()
            cell.fill.fore_color.rgb = TBL_HEADER_BG

        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                cell = tbl.cell(i + 1, j)
                cell.text = ''
                p = cell.text_frame.paragraphs[0]
                p.alignment = PP_ALIGN.CENTER
                r = p.add_run(); r.text = str(val)
                r.font.size = Pt(9); r.font.color.rgb = DARK; r.font.name = EN
                if i % 2 == 0:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = LIGHT_BG

        self.y += tbl_h + 0.15

    def gap(self, cm=0.1):
        self.y += cm


def main():
    prs = Presentation()
    prs.slide_width = Cm(A1_W)
    prs.slide_height = Cm(A1_H)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = WHITE

    L_X = MARGIN
    R_X = MARGIN + COL_W + GAP

    # ── Title banner ──
    print('Title banner...')
    y = 2.5
    title_h = img_height('title_banner_2col.png', CONTENT_W, BANNER_DIR)
    title_path = os.path.join(BANNER_DIR, 'title_banner_2col.png')
    if os.path.exists(title_path):
        slide.shapes.add_picture(title_path, Cm(MARGIN), Cm(y), Cm(CONTENT_W), Cm(title_h))
    y += title_h + 0.3
    start_y = y

    # ══════════════════════════════════════
    # LEFT COLUMN
    # ══════════════════════════════════════
    print('Left column...')
    L = Column(slide, L_X, COL_W, start_y)

    # Introduction
    L.add_banner('sec2_intro.png')
    L.add_text_block([
        (' 액션 게임에서 보스 AI가 매번 동일하게 행동할 경우 플레이어의 흥미가 빠르게 감소한다. '
         '기존 보스 AI는 Behavior Tree 등 규칙 기반 방식에 의존하므로 전투 패턴이 고정되기 쉽고, '
         '다양한 플레이어 조합에 유연하게 대응하기 어렵다.', {}),
        (f' 본 연구에서는 강화학습(RL)을 활용하여 보스 AI가 스스로 전투 방법을 학습할 수 있는지 분석한다. '
         f'보스에게 5가지 행동(Idle/Forward/Retreat/Turn L/Turn R)을 부여하고, '
         f'PPO 알고리즘으로 CC{X}CC를 제외한 9종 매치업, 총 55M steps를 학습시켰다.', {}),
        (' 핵심 기여: (1) 매치업별 상이한 전투 행동의 자연발생 실증, '
         '(2) 과학습 유형 3가지 분류, (3) 승률 단일 지표의 한계 정량적 입증.', {}),
    ])
    L.add_mixed_para([
        ('Key Findings Preview: ', {'bold': True, 'color': PRIMARY, 'font': EN}),
        ('같은 승률 82%인 두 매치업에서 대기 비율이 19% vs 2.4%로 완전히 상이. '
         '승률만으로는 학습 품질을 판단할 수 없음.', {}),
    ])
    L.add_separator()

    # Research Objectives
    L.add_banner('sec2_rq.png')
    L.add_text_block([
        ('RQ1. 9종 매치업별 전투 방식 차이 확인 (→ Fig. 2)', {'bullet': True}),
        ('RQ2. 과학습 현상의 유형별 분류 (→ Fig. 3)', {'bullet': True}),
        ('RQ3. 승률 단일 지표의 한계 검증 (→ Fig. 4)', {'bullet': True}),
    ])
    L.add_separator()

    # Method
    L.add_banner('sec2_method.png')
    L.add_image('fig01_method.png',
                'Fig. 1. Curriculum pipeline (left) and observation/action space (right).')
    L.gap(0.1)
    L.add_text_block([
        ('Experimental Setup:', {'bold': True}),
        ('Unity 6 3D 톱다운 액션 게임, 보스 1 vs 플레이어 2(BT 봇)', {'bullet': True}),
        ('PPO, 129채널 관측(HP/거리/스킬 쿨다운 등), 5가지 이산 행동', {'bullet': True}),
        ('Touch(5M)→Engage(10M)→Combat(40M), 총 55M steps', {'bullet': True}),
        ('매치업당 ~1,000판, 마지막 100판 평균 평가', {'bullet': True}),
        ('보상 설계: 거리 보상 + 공격 적중 + 승리 보너스의 가중합', {'bullet': True}),
    ])
    L.add_separator()

    L.add_table(
        ['Archetype', 'Role', 'Range', 'Key Skills'],
        [
            ['Melee', 'Close-range burst', '5-10m', 'ExecutionSpike, CrushingBarrage'],
            ['Ranged', 'Long-range kite', '20-30m', 'PiercingShot, RuptureMagazine'],
            ['CC', 'Crowd control', '8-14m', 'SealChain, CollapseRoar'],
            ['Hybrid', 'Flexible survivor', '6-30m', 'SurvivalPulse, OverchargeMode'],
        ],
        title='Player Archetypes:')
    L.add_text_block([
        (f' 4종 아키타입 조합 중 CC{X}CC는 교착 상태로 제외, 총 9종 매치업 학습.',
         {'size': 10}),
    ])
    L.add_separator()

    # RQ1
    L.add_banner('sec2_rq1.png')
    L.add_image('fig02_learning.png',
                'Fig. 2. (A) Group reward curves. (B) Final action distribution by matchup.')
    L.gap(0.1)
    L.add_text_block([
        ('Key Findings:', {'bold': True}),
        ('9종 매치업 모두 보상이 양(+)으로 수렴.', {'bullet': True}),
        ('Melee 상대 → Forward 위주, Ranged 상대 → Retreat+Rotation 위주. 유형별 이동 전략 차이.', {'bullet': True}),
        (f'M{X}M Idle 19% vs CC/Hybrid 상대 2~3%. 순수 전투형에는 "대기 후 반격" 전략.', {'bullet': True}),
        ('결론: 상대 조합에 따라 다른 전투 행동 학습 확인.', {'bullet': True}),
    ])
    L.add_mixed_para([
        ('Action Distribution: ', {'bold': True, 'color': PRIMARY, 'font': EN, 'size': 10}),
        (f'Melee 조합 Forward 40%+, Ranged 조합 Retreat 30%+Turn 25%. 행동 분포가 명확히 분리됨.',
         {'size': 10}),
    ])

    print(f'  Left column ends at y={L.y:.1f}cm')

    # ══════════════════════════════════════
    # RIGHT COLUMN
    # ══════════════════════════════════════
    print('Right column...')
    R = Column(slide, R_X, COL_W, start_y)

    # RQ2
    R.add_banner('sec2_rq2.png')
    R.add_image('fig03_overfitting.png',
                'Fig. 3. Reward/WR trends for 4 representative matchups. Overfitting causes mid-training drops.')
    R.gap(0.1)
    R.add_text_block([
        ('Key Findings:', {'bold': True}),
        ('강화학습에서 과학습(overfitting)이란 과도한 학습으로 인해 오히려 성능이 저하되는 현상이다. '
         '본 실험에서 3가지 유형이 관찰되었다:', {}),
        (f'Type 1 — Sharp Drop (R{X}R): 승률 급락 후 일부 회복', {'bullet': True}),
        (f'Type 2 — Double Dip (H{X}H): 반복적 성능 하락', {'bullet': True}),
        (f'Type 3 — Gradual Decay (H{X}R): 점진적 하락, 탐지 어려움', {'bullet': True}),
        (f'Control — Stable (C{X}H): 안정적 학습 완료', {'bullet': True}),
    ])
    R.add_text_block([
        (f'→ 유사 유형 조합(R{X}R, H{X}H)에서 overfitting 집중 발생. '
         f'상대 행동이 단순할수록 해당 패턴에만 과적합.', {'bold': True}),
    ])
    R.add_separator()

    # RQ3
    R.add_banner('sec2_rq3.png')
    R.add_image('fig04_idle.png',
                'Fig. 4. (A) Idle ratio trends. (B) WR vs Idle scatter (r=-0.23, n.s.).')
    R.gap(0.1)
    R.add_text_block([
        ('Key Findings:', {'bold': True}),
        (f'M{X}M, M{X}H 둘 다 WR 82%이나 Idle 19% vs 2.4%로 정반대.', {'bullet': True}),
        ('WR과 Idle 간 유의미한 상관 없음 (r=-0.23, n.s.).', {'bullet': True}),
        ('높은 승률이 반드시 적극적 전투를 의미하지 않음.', {'bullet': True}),
    ])
    R.add_separator()

    # Discussion
    R.add_banner('sec2_disc.png')
    R.add_text_block([
        ('Q1. 유사 유형 매치업의 overfitting 원인?', {'bold': True}),
        (f' 유사 유형 → 단조로운 행동 → 과적합. '
         f'반면 C{X}H처럼 다양한 조합에서는 범용적 전략 학습. '
         f'BT 봇의 고정된 행동 패턴이 과적합을 가속화.', {}),
        ('Q2. 실제 게임 적용 시?', {'bold': True}),
        (' BT 봇 회피 불가로 승률 과대 측정. 실제 플레이어 대상 시 보스 HP 하향 및 '
         'Early Stopping과 다중 지표 모니터링 병행 필수.', {}),
    ])
    R.add_separator()

    # Conclusion
    R.add_banner('sec2_conc.png')
    R.add_text_block([
        ('Finding 1: 상대 유형별 상이한 전투 행동 학습 확인', {'bullet': True}),
        ('Finding 2: 3가지 overfitting 패턴 발견 (유사 유형 집중)', {'bullet': True}),
        ('Finding 3: 같은 WR 82%에서 Idle 19% vs 2.4%', {'bullet': True}),
    ])
    R.gap(0.1)
    R.add_text_block([
        ('Future Work:', {'bold': True}),
        ('Early stopping 도입으로 overfitting 방지', {'bullet': True}),
        ('실제 플레이어 대상 밸런스 조정 (보스 HP 하향)', {'bullet': True}),
        ('스킬 타이밍까지 행동 공간 확장', {'bullet': True}),
    ])
    R.add_separator()

    # References
    R.add_banner('sec2_ref.png')
    R.add_text_block([
        ('[1] I. Millington and J. Funge, "AI for Games," CRC Press, 3rd ed., 2019.', {'size': 8, 'color': GRAY, 'font': EN}),
        ('[2] O. Vinyals et al., "Grandmaster level in StarCraft II using multi-agent RL," Nature, 575, 2019.', {'size': 8, 'color': GRAY, 'font': EN}),
        ('[3] C. Berner et al., "Dota 2 with large scale deep RL," arXiv:1912.06680, 2019.', {'size': 8, 'color': GRAY, 'font': EN}),
        ('[4] J. Schulman et al., "Proximal policy optimization algorithms," arXiv:1707.06347, 2017.', {'size': 8, 'color': GRAY, 'font': EN}),
        ('[5] A. Pan et al., "The effects of reward misspecification," Proc. ICLR, 2022.', {'size': 8, 'color': GRAY, 'font': EN}),
        ('[6] A. Juliani et al., "Unity: A general platform for intelligent agents," arXiv:1809.02627, 2020.', {'size': 8, 'color': GRAY, 'font': EN}),
    ])

    print(f'  Right column ends at y={R.y:.1f}cm')
    print(f'  Page height: {A1_H}cm')

    # Save
    for name in ['BossAI_Poster_A1.pptx', 'BossAI_Poster_A1_v2.pptx', 'BossAI_Poster_A1_v3.pptx']:
        out = os.path.join(OUT_DIR, name)
        try:
            prs.save(out)
            print(f'\nDone: {out}')
            break
        except PermissionError:
            continue


if __name__ == '__main__':
    main()
