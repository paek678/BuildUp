"""Generate a clean A1 research poster using python-pptx."""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu, Cm
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import os

# ── A1 dimensions (portrait): 594mm × 841mm ──
W_MM, H_MM = 594, 841
W = Cm(W_MM / 10)
H = Cm(H_MM / 10)

# ── Colors ──
DARK_BLUE  = RGBColor(0x1A, 0x23, 0x5B)
MED_BLUE   = RGBColor(0x2E, 0x4A, 0x8E)
LIGHT_BLUE = RGBColor(0x3B, 0x6F, 0xC4)
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
BLACK      = RGBColor(0x1A, 0x1A, 0x1A)
GRAY       = RGBColor(0x44, 0x44, 0x44)
LIGHT_GRAY = RGBColor(0xF0, 0xF2, 0xF5)
ACCENT     = RGBColor(0xE8, 0x6C, 0x00)

FIG_DIR = os.path.join(os.path.dirname(__file__), "figures_v10")
OUT_PATH = os.path.join(os.path.dirname(__file__), "BossAI_Poster_A1_clean.pptx")

# ── Layout constants (cm) ──
MARGIN    = 1.5   # page margin
COL_GAP   = 1.2   # gap between columns
COL_W_CM  = (W_MM/10 - 2*MARGIN - COL_GAP) / 2  # ~28.8cm each

TITLE_H   = 6.0   # title area height
AUTHOR_H  = 2.0   # author area
HDR_H     = 1.2   # section header height
BODY_PAD  = 0.3   # padding inside body boxes
SEC_GAP   = 0.5   # gap between sections


def cm(v):
    return Cm(v)

def add_rect(slide, left, top, width, height, fill_color):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, cm(left), cm(top), cm(width), cm(height))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.fill.background()
    return shape

def add_textbox(slide, left, top, width, height, text, font_size=11,
                bold=False, color=BLACK, align=PP_ALIGN.LEFT, font_name="맑은 고딕"):
    txBox = slide.shapes.add_textbox(cm(left), cm(top), cm(width), cm(height))
    txBox.text_frame.word_wrap = True
    txBox.text_frame.auto_size = None
    p = txBox.text_frame.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = font_name
    p.alignment = align
    return txBox

def add_rich_textbox(slide, left, top, width, height, lines, default_size=11):
    """lines: list of (text, font_size, bold, color) tuples or just str."""
    txBox = slide.shapes.add_textbox(cm(left), cm(top), cm(width), cm(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    for i, item in enumerate(lines):
        if isinstance(item, str):
            text, sz, bold, color = item, default_size, False, GRAY
        else:
            text, sz, bold, color = item
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = text
        p.font.size = Pt(sz)
        p.font.bold = bold
        p.font.color.rgb = color
        p.font.name = "맑은 고딕"
        p.space_after = Pt(4)
        p.space_before = Pt(1)
    return txBox

def add_section_header(slide, left, top, width, text, number=""):
    add_rect(slide, left, top, width, HDR_H, MED_BLUE)
    label = f"{number}. {text}" if number else text
    add_textbox(slide, left + 0.3, top + 0.1, width - 0.6, HDR_H - 0.2,
                label, font_size=16, bold=True, color=WHITE)
    return top + HDR_H

def add_figure(slide, left, top, width, filename, caption=""):
    path = os.path.join(FIG_DIR, filename)
    if not os.path.exists(path):
        return top + 2
    pic = slide.shapes.add_picture(path, cm(left), cm(top), cm(width))
    pic_h_cm = pic.height / 360000
    bottom = top + pic_h_cm
    if caption:
        add_textbox(slide, left, bottom + 0.1, width, 0.8,
                    caption, font_size=8, color=GRAY, align=PP_ALIGN.CENTER)
        bottom += 0.9
    return bottom


def build_poster():
    prs = Presentation()
    prs.slide_width = W
    prs.slide_height = H
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank

    # ── Background ──
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = WHITE

    LX = MARGIN           # left column x
    RX = MARGIN + COL_W_CM + COL_GAP  # right column x
    CW = COL_W_CM         # column width
    PAGE_W = W_MM / 10    # 59.4

    # ════════════════════════════════════════════════════════════
    # TITLE AREA
    # ════════════════════════════════════════════════════════════
    add_rect(slide, 0, 0, PAGE_W, TITLE_H + AUTHOR_H + 0.5, DARK_BLUE)

    # Title (Korean)
    add_textbox(slide, MARGIN, 0.8, PAGE_W - 2*MARGIN, 2.0,
                "매치업별 특화 강화학습을 활용한 보스전 적응 AI 설계 및 분석",
                font_size=28, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    # Title (English)
    add_textbox(slide, MARGIN, 3.0, PAGE_W - 2*MARGIN, 1.5,
                "Adaptive Boss AI Design and Analysis through Matchup-Specialized Reinforcement Learning",
                font_size=14, bold=False, color=RGBColor(0xBB, 0xCC, 0xEE), align=PP_ALIGN.CENTER)

    # Authors
    add_textbox(slide, MARGIN, 4.8, PAGE_W - 2*MARGIN, 1.0,
                "백성열   홍채영   곽다영   김지형*",
                font_size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    add_textbox(slide, MARGIN, 5.8, PAGE_W - 2*MARGIN, 1.0,
                "금오공과대학교 (Kumoh National Institute of Technology)  *kimjihyung@kumoh.ac.kr",
                font_size=10, bold=False, color=RGBColor(0x99, 0xAA, 0xDD), align=PP_ALIGN.CENTER)

    # Keywords strip
    kw_top = TITLE_H + AUTHOR_H + 0.5
    add_rect(slide, 0, kw_top, PAGE_W, 1.0, LIGHT_BLUE)
    add_textbox(slide, MARGIN, kw_top + 0.1, PAGE_W - 2*MARGIN, 0.8,
                "Unity ML-Agents  |  PPO  |  9 Matchups  |  55M Steps  |  3-Stage Curriculum  |  9,134 Episodes",
                font_size=11, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    content_top = kw_top + 1.0 + SEC_GAP

    # ════════════════════════════════════════════════════════════
    # LEFT COLUMN
    # ════════════════════════════════════════════════════════════
    y = content_top

    # ── 1. Introduction ──
    y = add_section_header(slide, LX, y, CW, "Introduction", "1")
    y += 0.2
    intro_lines = [
        ("액션 게임에서 보스 AI가 매번 동일하게 행동하면 플레이어의 흥미가 빠르게 감소한다. "
         "기존 보스 AI는 Behavior Tree 등 규칙 기반 방식에 의존하므로 전투 패턴이 고정되고, "
         "다양한 플레이어 조합에 유연하게 대응하기 어렵다.", 11, False, GRAY),
        ("본 연구에서는 PPO 알고리즘으로 CC×CC를 제외한 9종 매치업에 대해 "
         "보스에게 5가지 이동 행동(Idle/Forward/Turn L/Turn R/Retreat)을 부여하고 "
         "총 55M steps를 학습시켰다.", 11, False, GRAY),
    ]
    add_rich_textbox(slide, LX + BODY_PAD, y, CW - 2*BODY_PAD, 4.5, intro_lines)
    y += 4.0 + SEC_GAP

    # ── 2. Research Objectives ──
    y = add_section_header(slide, LX, y, CW, "Research Objectives", "2")
    y += 0.2
    obj_lines = [
        ("• RQ1. 9종 매치업별 전투 방식 차이 확인 (→ Fig. 2)", 11, False, GRAY),
        ("• RQ2. 과학습 현상의 유형별 분류 (→ Fig. 3)", 11, False, GRAY),
        ("• RQ3. 승률 단일 지표의 한계 검증 (→ Fig. 4)", 11, False, GRAY),
    ]
    add_rich_textbox(slide, LX + BODY_PAD, y, CW - 2*BODY_PAD, 2.5, obj_lines)
    y += 2.5 + SEC_GAP

    # ── 3. Method ──
    y = add_section_header(slide, LX, y, CW, "Method", "3")
    y += 0.2

    method_lines = [
        ("3-Stage Curriculum Pipeline", 12, True, BLACK),
        ("• Stage 1 — Approach (5M steps / 30s): 플레이어에게 접근 학습", 10, False, GRAY),
        ("• Stage 2 — Engage (10M steps / 90s): 교전 거리 유지 학습", 10, False, GRAY),
        ("• Stage 3 — Combat (40M steps / 720s): 실전 전투 학습", 10, False, GRAY),
        ("", 6, False, GRAY),
        ("Observation (129ch) & Action Space (5)", 12, True, BLACK),
        ("• Boss State (18ch): HP, Position, Phase, Animation", 10, False, GRAY),
        ("• Player 1 & 2 (32ch each): HP, Position, Skills, Cooldowns", 10, False, GRAY),
        ("• Relational (38ch): Distances, Angles, Dominance", 10, False, GRAY),
        ("• Temporal (9ch): Round, Elapsed, Phase Progress", 10, False, GRAY),
        ("• Actions: 0.Idle / 1.Forward / 2.Turn L / 3.Turn R / 4.Retreat (70% speed)", 10, False, GRAY),
    ]
    add_rich_textbox(slide, LX + BODY_PAD, y, CW - 2*BODY_PAD, 7.0, method_lines)
    y += 5.5

    # Method figure
    y = add_figure(slide, LX + 1, y, CW - 2, "fig01_method.png",
                   "Fig. 1. 3-Stage Curriculum pipeline (left) and observation/action space (right).")
    y += SEC_GAP

    # Player Archetypes table
    arch_lines = [
        ("Player Archetypes (BT Bot)", 12, True, BLACK),
        ("• Melee: Close-range burst, 5–10m, ExecutionSpike / CrushingBarrage", 10, False, GRAY),
        ("• Ranged: Long-range kite, 20–50m, PiercingShot / RuptureMagazine", 10, False, GRAY),
        ("• CC: Crowd control, 8–14m, SealChain / CollapseRoar", 10, False, GRAY),
        ("• Hybrid: Flexible survivor, 8–50m, SurvivalPulse / OverchargeMode", 10, False, GRAY),
    ]
    add_rich_textbox(slide, LX + BODY_PAD, y, CW - 2*BODY_PAD, 3.5, arch_lines)
    y += 3.5 + SEC_GAP

    # ── RQ1 ──
    y = add_section_header(slide, LX, y, CW, "RQ1: Adaptive Combat Behavior", "")
    y += 0.2
    rq1_lines = [
        ("Key Findings:", 11, True, BLACK),
        ("• 9종 매치업 모두 보상이 양(+)으로 수렴.", 10, False, GRAY),
        ("• Melee 상대 → Forward 위주, Ranged 상대 → Retreat+Rotation 위주 전략 차이.", 10, False, GRAY),
        ("• M×M의 Idle 19% vs CC×Hybrid 2.4%로 정반대.", 10, False, GRAY),
        ("→ 보스는 상대 조합에 따라 다른 조합 전략을 학습한다.", 10, True, DARK_BLUE),
    ]
    add_rich_textbox(slide, LX + BODY_PAD, y, CW - 2*BODY_PAD, 3.5, rq1_lines)
    y += 3.2

    y = add_figure(slide, LX, y, CW, "fig02_learning.png",
                   "Fig. 2. (A) Group reward curves. (B) Final action distribution by matchup.")

    # ════════════════════════════════════════════════════════════
    # RIGHT COLUMN
    # ════════════════════════════════════════════════════════════
    y = content_top

    # ── RQ2 ──
    y = add_section_header(slide, RX, y, CW, "RQ2: Overfitting Patterns", "")
    y += 0.2

    rq2_lines = [
        ("강화학습에서 과학습(overfitting)이란 과도한 학습으로 인해 "
         "오히려 성능이 저하되는 현상이다. 본 실험에서 3가지 유형이 관찰되었다:", 10, False, GRAY),
        ("• Type 1 — Sharp Drop (R×R): 승률 급격 하락 후 불완전 회복", 10, False, GRAY),
        ("• Type 2 — Double Dip (H×H): 반복적 성능 하락", 10, False, GRAY),
        ("• Type 3 — Gradual Decay (H×R): 점진적 저하, 탐지 어려움", 10, False, GRAY),
        ("• Control — Stable (C×H): 안정적 학습 완료", 10, False, GRAY),
        ("→ 유사 유형 → 단조로운 행동 → 과적합. BT 봇의 고정된 행동 패턴이 과적합 가속.", 10, True, DARK_BLUE),
    ]
    add_rich_textbox(slide, RX + BODY_PAD, y, CW - 2*BODY_PAD, 5.0, rq2_lines)
    y += 4.5

    y = add_figure(slide, RX, y, CW, "fig03_overfitting.png",
                   "Fig. 3. Reward/WR trends for 4 representative matchups. Overfitting causes mid-training drops.")
    y += SEC_GAP

    # ── RQ3 ──
    y = add_section_header(slide, RX, y, CW, "RQ3: Win Rate Is Not Enough", "")
    y += 0.2

    rq3_lines = [
        ("Key Findings:", 11, True, BLACK),
        ("• M×M, M×H 둘 다 WR 82%이나 Idle 19% vs 2.4%로 정반대.", 10, False, GRAY),
        ("• WR과 Idle 간 유의미한 상관 없음 (r=−0.23, n.s.).", 10, False, GRAY),
        ("• 전체 9,134판 중 PlayerWin = 0건 (BT봇 회피 불가 → 승률 과대 측정).", 10, False, GRAY),
        ("• H×H Timeout 9.5%로 최고 (과학습과 직결).", 10, False, GRAY),
        ("→ WR + Idle Ratio + Timeout Rate 최소 3가지 지표 병행 필요.", 10, True, DARK_BLUE),
    ]
    add_rich_textbox(slide, RX + BODY_PAD, y, CW - 2*BODY_PAD, 4.5, rq3_lines)
    y += 4.0

    y = add_figure(slide, RX, y, CW, "fig04_idle.png",
                   "Fig. 4. (A) Idle ratio trends. (B) WR vs Idle scatter (r=−0.23, n.s.).")
    y += SEC_GAP

    # ── 4. Discussion ──
    y = add_section_header(slide, RX, y, CW, "Discussion", "4")
    y += 0.2
    disc_lines = [
        ("Q1. 유사 매치업의 overfitting 원인?", 11, True, BLACK),
        ("유사 유형 → 단조로운 행동 → 과적합. 반면 C×H처럼 다양한 조합에서는 "
         "방어/공격 전략 전환이 과적합을 방지한다.", 10, False, GRAY),
        ("Q2. 실제 게임 적용 시?", 11, True, BLACK),
        ("BT 봇은 회피 불가 → 실제 플레이어 대상 밸런스 조정(보스 HP 하향) 필요. "
         "Early stopping으로 과학습 방지.", 10, False, GRAY),
    ]
    add_rich_textbox(slide, RX + BODY_PAD, y, CW - 2*BODY_PAD, 4.5, disc_lines)
    y += 4.0 + SEC_GAP

    # ── 5. Conclusion ──
    y = add_section_header(slide, RX, y, CW, "Conclusion", "5")
    y += 0.2
    conc_lines = [
        ("• Finding 1: 상대 유형별 상이한 전투 행동 학습 확인", 11, False, BLACK),
        ("• Finding 2: 3가지 overfitting 패턴 발견 (유사 유형 집중)", 11, False, BLACK),
        ("• Finding 3: 같은 WR 82%에서 Idle 19% vs 2.4%", 11, False, BLACK),
        ("", 6, False, GRAY),
        ("Future Work:", 11, True, BLACK),
        ("• Early stopping 도입으로 overfitting 방지", 10, False, GRAY),
        ("• 실제 플레이어 대상 밸런스 조정 (보스 HP 하향)", 10, False, GRAY),
        ("• 스킬 타이밍까지 학습하도록 행동 공간 확장", 10, False, GRAY),
    ]
    add_rich_textbox(slide, RX + BODY_PAD, y, CW - 2*BODY_PAD, 5.0, conc_lines)
    y += 4.5 + SEC_GAP

    # ── References ──
    y = add_section_header(slide, RX, y, CW, "References", "")
    y += 0.2
    refs_lines = [
        ("[1] Millington and J. Funge, AI for Games, CRC Press, 3rd ed., 2025.", 8, False, GRAY),
        ("[2] D. Vinyals et al., Grandmaster level in StarCraft II using multi-agent RL, Nature, 575, 2019.", 8, False, GRAY),
        ("[3] C. Berner et al., Dota 2 with large scale deep RL, arXiv:1912.06680, 2019.", 8, False, GRAY),
        ("[4] J. Schulman et al., Proximal policy optimization algorithms, arXiv:1707.06347, 2017.", 8, False, GRAY),
        ("[5] A. Seri et al., The effects of reward misspecification, Proc. ICML, 2021.", 8, False, GRAY),
        ("[6] A. Juliani et al., Unity: A general platform for intelligent agents, arXiv:1809.02627, 2020.", 8, False, GRAY),
    ]
    add_rich_textbox(slide, RX + BODY_PAD, y, CW - 2*BODY_PAD, 4.0, refs_lines, default_size=8)

    # ════════════════════════════════════════════════════════════
    # Save
    # ════════════════════════════════════════════════════════════
    prs.save(OUT_PATH)
    print(f"Saved: {OUT_PATH}")


if __name__ == "__main__":
    build_poster()
