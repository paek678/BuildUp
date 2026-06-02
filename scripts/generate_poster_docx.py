"""
Generate A4 6-page academic poster DOCX for Tenebris project.
Output: poster_output/Tenebris_Poster_A4x6.docx
"""
import os, sys
from pathlib import Path

from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "poster_figures"
OUT_DIR = ROOT / "poster_output"
OUT_DIR.mkdir(exist_ok=True)

# ── colour constants ──
NAVY   = RGBColor(0x1A, 0x23, 0x7E)
BLUE   = RGBColor(0x02, 0x77, 0xBD)
ORANGE = RGBColor(0xFF, 0x6F, 0x00)
BLACK  = RGBColor(0x00, 0x00, 0x00)
GRAY   = RGBColor(0x55, 0x55, 0x55)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)

HEADER_BG = "1A237E"
SUBHEADER_BG = "E3F2FD"
ACCENT_BG = "FFF3E0"

def set_cell_bg(cell, color_hex):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)

def set_cell_text(cell, text, bold=False, size=9, color=BLACK, align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.name = "Malgun Gothic"
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)

def add_heading(doc, text, level=1):
    """Custom heading with navy color."""
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.name = "Malgun Gothic"
    if level == 0:
        run.font.size = Pt(20)
        run.font.color.rgb = NAVY
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
    elif level == 1:
        run.font.size = Pt(13)
        run.font.color.rgb = NAVY
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(2)
    elif level == 2:
        run.font.size = Pt(10.5)
        run.font.color.rgb = BLUE
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(2)
    return p

def add_body(doc, text, size=9, bold=False, color=BLACK, align=WD_ALIGN_PARAGRAPH.LEFT):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.size = Pt(size)
    run.font.name = "Malgun Gothic"
    run.font.color.rgb = color
    run.bold = bold
    p.alignment = align
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)
    return p

def add_figure(doc, filename, caption, width_inches=6.0):
    fig_path = FIG_DIR / filename
    if not fig_path.exists():
        add_body(doc, f"[{caption} - {filename} not found]", size=8, color=GRAY)
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run()
    run.add_picture(str(fig_path), width=Inches(width_inches))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_before = Pt(1)
    cap.paragraph_format.space_after = Pt(4)
    r = cap.add_run(caption)
    r.font.size = Pt(8)
    r.font.color.rgb = GRAY
    r.font.name = "Malgun Gothic"
    r.italic = True

def add_page_break(doc):
    doc.add_page_break()

def add_separator(doc):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run("─" * 60)
    run.font.size = Pt(6)
    run.font.color.rgb = RGBColor(0xBD, 0xBD, 0xBD)

def build_table(doc, headers, rows, col_widths=None):
    """Create a styled table."""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Table Grid'

    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        set_cell_text(cell, h, bold=True, size=8, color=WHITE, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell_bg(cell, HEADER_BG)

    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = table.rows[ri + 1].cells[ci]
            align = WD_ALIGN_PARAGRAPH.CENTER if ci > 0 else WD_ALIGN_PARAGRAPH.LEFT
            set_cell_text(cell, str(val), size=8, align=align)
            if ri % 2 == 1:
                set_cell_bg(cell, "F5F5F5")

    if col_widths:
        for ri, row in enumerate(table.rows):
            for ci, w in enumerate(col_widths):
                row.cells[ci].width = Cm(w)

    return table


# ═══════════════════════════════════════════════════════════
#  PAGE 1: Title + Introduction + Research Goals
# ═══════════════════════════════════════════════════════════
def page1(doc):
    add_separator(doc)

    # Title
    add_heading(doc, "매치업별 특화 강화학습을 활용한", level=0)
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run("적응형 보스 AI 설계 및 분석")
    run.bold = True
    run.font.size = Pt(20)
    run.font.color.rgb = NAVY
    run.font.name = "Malgun Gothic"
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # English subtitle
    add_body(doc,
        "Adaptive Boss AI Design and Analysis through Matchup-Specialized Reinforcement Learning",
        size=10, color=GRAY, align=WD_ALIGN_PARAGRAPH.CENTER)

    add_separator(doc)

    # Authors
    add_body(doc, "홍채영*, 곽다영*, 백성열*, 김지형**", size=10, bold=True,
             align=WD_ALIGN_PARAGRAPH.CENTER)
    add_body(doc, "*금오공과대학교 컴퓨터공학과  **금오공과대학교 컴퓨터공학과(지도교수)",
             size=8, color=GRAY, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_body(doc, "2026 한국정보기술학회 하계 종합학술대회",
             size=9, color=BLUE, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)

    add_separator(doc)

    # Research background
    add_heading(doc, "1. 연구 배경", level=1)
    add_body(doc, "최근 게임 AI 분야에서 강화학습(RL)은 AlphaStar, OpenAI Five 등의 사례를 통해 "
                  "인간 수준 이상의 의사결정 능력을 보여주고 있다. 그러나 이러한 성과는 수천 GPU-시간의 "
                  "대규모 자원을 전제로 하며, 소규모 프로젝트에 직접 적용하기 어렵다.", size=9)

    bullets = [
        "기존 보스 AI: 행동트리(BT)/유한상태기계(FSM) 기반으로 패턴이 반복되어 전투 몰입도가 저하된다.",
        "2인 협동 보스전: 플레이어 2명의 위치, 스킬 선택, CC(군중제어) 등 복합 요인이 작용하는 비대칭 다자 환경이다.",
        "본 연구의 목표: 매치업별 특화 PPO 학습 + 런타임 적응형 시스템으로 소규모에서도 효과적인 보스 AI를 구현한다."
    ]
    for b in bullets:
        add_body(doc, f"  • {b}", size=9)

    # Research goals
    add_heading(doc, "2. 연구 목적", level=1)
    add_body(doc, "본 연구는 다음 네 가지 목적을 달성하고자 한다.", size=9)
    goals = [
        "플레이어 빌드(Ranged/Melee/Hybrid/CC) 4종 분류 체계를 설계하여 플레이어 행동 패턴을 실시간으로 식별한다.",
        "매치업별 보상 함수를 분리 설계하고, PPO 기반 개별 정책을 학습하여 각 매치업에 특화된 보스 행동을 생성한다.",
        "3단계 커리큘럼(Touch→Engage→Combat) + 전이학습을 도입하여 제한된 학습 자원으로도 안정적인 수렴을 달성한다.",
        "런타임에서 플레이어 분류 → ONNX 모델 선택 → 적응형 스킬 가중치 조절을 통합하는 적응형 파이프라인을 구축한다."
    ]
    for i, g in enumerate(goals, 1):
        p = add_body(doc, f"  {i}. {g}", size=9)

    # Game screenshot placeholder

    add_body(doc,
        "[그림 1] 테네브리스(Tenebris) 전투 환경 — 반지름 50m 원형 아레나, 보스 1체 vs 플레이어 봇 2체",
        size=8, color=GRAY, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_body(doc, "(Unity Editor 게임 스크린샷 삽입 위치)",
             size=9, color=ORANGE, align=WD_ALIGN_PARAGRAPH.CENTER)


# ═══════════════════════════════════════════════════════════
#  PAGE 2: System Architecture + Observation/Action Space
# ═══════════════════════════════════════════════════════════
def page2(doc):
    add_page_break(doc)

    add_heading(doc, "3. 시스템 아키텍처", level=1)
    add_body(doc, "본 시스템은 학습(Training), 모델(ONNX), 런타임(Runtime) 3단계로 구성된다. "
                  "학습 환경에서는 Unity ML-Agents와 BT 기반 플레이어 봇으로 PPO 정책을 학습하고, "
                  "학습된 정책은 ONNX 포맷으로 변환되어 런타임에서 추론에 사용된다. "
                  "ML 모델은 보스의 이동/타겟팅만 결정하며, 스킬 선택은 서버 로직이 별도로 처리한다.", size=9)
    add_figure(doc, "fig_B_architecture.png",
               "[그림 2] 전체 시스템 아키텍처 (학습 → ONNX → 런타임)",
               width_inches=6.5)

    # Observation space
    add_heading(doc, "4. 관측 공간 (129 채널)", level=1)
    add_body(doc, "보스 에이전트는 매 결정 주기(DecisionPeriod=5)마다 129차원의 정규화된 관측 벡터를 수집한다. "
                  "관측 공간의 81%를 스킬 정보(Boss 5슬롯 + P1 5슬롯 + P2 5슬롯 = 105ch)가 차지하며, "
                  "각 슬롯은 쿨다운, 사거리, 형태 등 7개 특성으로 구성된다.", size=9)

    # Obs donut chart
    add_figure(doc, "fig_extra_obs_donut.png",
               "[그림 3] 129채널 관측 공간 구성 비율",
               width_inches=4.2)

    # Observation table
    add_heading(doc, "표 1. 129채널 관측 구조", level=2)
    headers = ["Section", "Channels", "Index", "내용"]
    rows = [
        ["Position",   "11ch", "#0–10",    "P1/P2 방향벡터, 거리(정규화), 각도"],
        ["Boss State", "4ch",  "#11–14",   "HP, Phase, 이동속도, 캐스팅"],
        ["Boss Skills", "35ch", "#15–49",  "5슬롯 × 7ch (쿨다운,사거리,형태)"],
        ["Touch",      "2ch",  "#50–51",   "P1/P2 근접 접촉 여부"],
        ["P1 Skills",  "35ch", "#52–86",   "5슬롯 × 7ch"],
        ["P2 Skills",  "35ch", "#87–121",  "5슬롯 × 7ch"],
        ["Extra",      "7ch",  "#122–128", "캐스팅,이속,해금수,버스트DMG"],
        ["Total",      "129ch","#0–128",   ""]
    ]
    build_table(doc, headers, rows, col_widths=[2.5, 1.5, 2.0, 5.5])

    # Action space
    add_heading(doc, "5. 행동 공간", level=1)
    add_body(doc, "행동 공간은 Discrete Branch 1개(Size 5)로 구성된다. 보스는 매 결정 시 "
                  "정지(Idle), 전진(Forward), 좌/우 회전(Left/Right Rotate), 후퇴(Backward) 중 하나를 선택한다. "
                  "스킬 사용은 ML 모델이 아닌 서버 로직에서 별도로 처리되므로, "
                  "모델은 순수 이동/타겟팅에만 집중하도록 설계하였다.", size=9)
    add_body(doc, "DecisionPeriod=5, TakeActionsBetweenDecisions=true, NumStackedVectors=1", size=8, color=GRAY)

    # PPO algorithm rationale
    add_heading(doc, "6. 강화학습 알고리즘 선정", level=1)
    add_heading(doc, "6.1 PPO(Proximal Policy Optimization) 선정 근거", level=2)
    add_body(doc, "본 연구는 보스 AI의 학습 알고리즘으로 PPO(Schulman et al., 2017)를 선정하였다. "
                  "게임 AI 학습에 활용되는 주요 강화학습 알고리즘을 비교 검토한 결과, "
                  "다음의 이유로 PPO가 본 연구 환경에 가장 적합하다고 판단하였다.", size=9)


    ppo_reasons = [
        "학습 안정성: PPO는 Clipped Surrogate Objective를 통해 정책 업데이트 폭을 제한한다. "
        "이는 기존 Policy Gradient 계열(REINFORCE, A3C)에서 빈번히 발생하는 정책 붕괴(policy collapse)를 방지하며, "
        "비대칭 다자 환경(보스 1 vs 플레이어 2)에서도 안정적 수렴을 가능하게 한다.",
        "이산 행동 공간 적합성: 본 연구의 행동 공간은 Discrete Branch 1개(Size 5)로 구성된다. "
        "SAC(Soft Actor-Critic)는 본래 연속 행동 공간에 최적화되어 있고, "
        "이산 환경에서는 추가 적응(Discrete SAC)이 필요하다. PPO는 이산/연속 모두에 네이티브로 대응한다.",
        "소규모 자원 효율성: AlphaStar(약 12,000 CPU 코어)나 OpenAI Five(수천 GPU-시간) 같은 "
        "대규모 분산 학습과 달리, PPO는 단일 GPU + CPU 환경에서도 4~6M steps 내에 수렴이 가능하다. "
        "본 연구의 단일 매치업 학습은 RTX 3060 기준 약 8~12시간 내에 완료되었다.",
        "Unity ML-Agents 네이티브 지원: Unity ML-Agents Toolkit은 PPO를 1급(first-class) 알고리즘으로 지원한다. "
        "학습 파이프라인, ONNX 변환, 커리큘럼 학습, initialize-from 전이학습 등 "
        "본 연구에 필요한 모든 기능이 PPO 기반으로 검증되어 있다.",
    ]
    for b in ppo_reasons:
        add_body(doc, f"  • {b}", size=9)

    add_heading(doc, "6.2 PPO 핵심 메커니즘", level=2)
    add_body(doc, "PPO의 핵심은 Clipped Surrogate Objective로, 정책 비율 r(θ) = π_new/π_old에 대해 "
                  "clip(r(θ), 1-ε, 1+ε)을 적용하여 한 번의 업데이트에서 정책이 과도하게 변하는 것을 방지한다. "
                  "ε=0.2로 설정하여 ±20% 범위 내에서만 정책 변경을 허용하였다.", size=9)
    add_body(doc, "또한 GAE(Generalized Advantage Estimation, λ=0.95)를 통해 "
                  "편향-분산 트레이드오프(bias-variance tradeoff)를 조절하며, "
                  "엔트로피 보너스(β=0.005)를 추가하여 탐색(exploration)과 활용(exploitation)의 균형을 유지한다. "
                  "γ=0.995의 높은 감가율은 720초(12분) 최대 전투 시간에서 장기적 보상을 충분히 반영하기 위함이다.", size=9)

    # Algorithm comparison table
    add_heading(doc, "표 2. 강화학습 알고리즘 비교", level=2)
    headers_algo = ["알고리즘", "정책 유형", "행동 공간", "학습 안정성", "자원 요구", "본 연구 적합도"]
    rows_algo = [
        ["DQN",  "Off-policy", "이산 전용",   "중",   "낮음",   "△ (연속 행동 미지원)"],
        ["A3C",  "On-policy",  "이산/연속",   "낮음", "중간",   "△ (정책 붕괴 위험)"],
        ["SAC",  "Off-policy", "연속 최적화", "높음", "중간",   "△ (이산 적응 필요)"],
        ["PPO",  "On-policy",  "이산/연속",   "높음", "낮음",   "◎ (선정)"],
        ["MAPPO","On-policy",  "이산/연속",   "높음", "높음",   "△ (다중 에이전트 과잉)"],
    ]
    build_table(doc, headers_algo, rows_algo, col_widths=[1.8, 1.8, 2.0, 1.8, 1.5, 3.0])



    # PPO hyperparams
    add_heading(doc, "표 3. PPO 하이퍼파라미터", level=2)
    headers2 = ["Parameter", "Value", "Parameter", "Value"]
    rows2 = [
        ["Batch Size",    "1,024",  "Hidden Units", "256 × 3"],
        ["Buffer Size",   "10,240", "Max Steps",    "40M"],
        ["Learning Rate", "3e-4",   "Time Horizon",  "1,024"],
        ["Beta (Entropy)","0.005",  "Gamma",         "0.995"],
        ["Epsilon (Clip)","0.2",    "Lambda (GAE)",  "0.95"],
        ["Epochs",        "3",      "Normalize",     "True"],
    ]
    build_table(doc, headers2, rows2, col_widths=[3.0, 2.0, 3.0, 2.0])


# ═══════════════════════════════════════════════════════════
#  PAGE 3: Curriculum + Matchup Design + Transfer Learning
# ═══════════════════════════════════════════════════════════
def page3(doc):
    add_page_break(doc)

    add_heading(doc, "7. 3단계 커리큘럼 학습", level=1)
    add_body(doc, "강화학습 에이전트가 복잡한 전투 행동을 처음부터 학습하는 것은 보상 희소성(reward sparsity) 문제로 인해 "
                  "수렴이 어렵다. 이를 해결하기 위해 본 연구에서는 3단계 커리큘럼 학습을 설계하였다. "
                  "각 단계는 ML-Agents의 initialize-from 옵션으로 이전 단계의 가중치를 계승하여 학습 효율을 극대화한다.", size=9)
    add_figure(doc, "fig_C_curriculum.png",
               "[그림 4] 커리큘럼 학습 파이프라인 (Touch → Engage → Combat)",
               width_inches=6.5)

    add_body(doc, "Stage 1(Touch): 11ch 관측으로 P1/P2 접촉 학습 — 보스가 플레이어에게 접근하는 기초 이동 패턴을 습득한다. "
                  "Stage 2(Engage): 35ch 관측으로 거리 유지 및 공격 학습 — DangerRange 기반으로 적정 교전 거리를 유지하며 공격한다. "
                  "Stage 3(Combat): 129ch 관측으로 매치업별 전투 특화 — 각 플레이어 조합에 최적화된 전투 정책을 학습한다.", size=9)

    # BT Player profiles
    add_heading(doc, "8. BT 플레이어 프로필", level=1)
    add_body(doc, "학습 환경에서 보스의 상대역을 수행하는 BT(행동트리) 플레이어 봇 4종을 설계하였다. "
                  "각 타입은 DangerRange(위험 거리)와 OptimalRange(적정 교전 거리)가 다르며, "
                  "이에 따라 보스가 학습해야 하는 이동 패턴이 매치업마다 달라진다.", size=9)
    add_heading(doc, "표 4. 4종 BT 플레이어 프로필", level=2)
    headers = ["BT 타입", "DangerRange", "OptimalRange", "평균거리", "전략"]
    rows = [
        ["Melee",  "15m", "3–6m",  "~4.5m",  "근접 돌진"],
        ["CC",     "6m",  "8–14m", "~11m",   "중거리 CC"],
        ["Hybrid", "5m",  "6–30m", "~18m",   "거리 전환"],
        ["Ranged", "16m", "20–30m","~25m",   "원거리 카이팅"],
    ]
    build_table(doc, headers, rows, col_widths=[2.0, 2.2, 2.2, 1.8, 2.5])

    # 5 matchups
    add_heading(doc, "9. 학습 매치업 구성", level=1)
    add_body(doc, "P1과 P2 아키타입 조합으로 총 5개 매치업을 학습하였다. "
                  "Hybrid x Hybrid 매치업을 기본 학습으로 가장 많은 에피소드(1,464ep)를 할당하였으며, "
                  "이 가중치를 전이학습 소스로 활용하여 나머지 매치업의 학습 비용을 절감하였다. "
                  "전체 4,464 에피소드가 수행되었다.", size=9)
    add_heading(doc, "표 5. 5개 학습 매치업", level=2)
    headers2 = ["매치업", "P1 타입", "P2 타입", "에피소드", "Steps", "비고"]
    rows2 = [
        ["Hybrid × CC",     "Hybrid", "CC",     "1,000", "~4.2M",  "전이학습 (HxH→HxC)"],
        ["Hybrid × Hybrid", "Hybrid", "Hybrid", "1,464", "~6.1M",  "기본 학습 (최다)"],
        ["Ranged × CC",     "Ranged", "CC",     "1,000", "~4.4M",  ""],
        ["Ranged × Hybrid", "Ranged", "Hybrid", "1,000", "~5.1M",  ""],
        ["Ranged × Ranged", "Ranged", "Ranged", "1,000", "~4.6M",  ""],
        ["합계",                 "",       "",       "4,464", "",       ""],
    ]
    build_table(doc, headers2, rows2, col_widths=[2.5, 1.5, 1.5, 1.5, 1.5, 3.0])

    # Transfer learning
    add_heading(doc, "10. 전이학습 효과", level=1)
    add_body(doc, "Hybrid × Hybrid (6.1M steps, 63.6%) → initialize-from → Hybrid × CC (4.2M steps, 64.4%)", size=9, bold=True)
    add_body(doc, "Hybrid x Hybrid에서 학습한 가중치를 Hybrid x CC에 전이한 결과, "
                  "초기 250 에피소드에서 이미 56%의 승률을 달성하여 전이학습의 빠른 수렴을 확인하였다. "
                  "이후 1,000 에피소드까지 학습을 지속하여 전체 최고 승률(64.4%)에 도달하였다. "
                  "이는 유사한 거리 패턴(근~중거리)을 갖는 매치업 간에 전이학습이 효과적임을 의미하며, "
                  "추가 매치업 학습 시에도 동일 전략을 적용할 수 있음을 시사한다.", size=9)


# ═══════════════════════════════════════════════════════════
#  PAGE 4: Results (Win Rate + Trend + Action Distribution)
# ═══════════════════════════════════════════════════════════
def page4(doc):
    add_page_break(doc)

    add_heading(doc, "11. 실험 결과", level=1)
    add_body(doc, "5개 매치업에 대해 총 4,464 에피소드를 학습한 후 최종 성능을 분석하였다. "
                  "승률(Win Rate)은 보스가 플레이어 2명을 모두 처치하면 BossWin, "
                  "보스 HP가 0이 되면 BossLose, 720초 내 미결판 시 Timeout으로 판정한다.", size=9)

    # Performance summary table
    add_heading(doc, "표 6. 매치업별 최종 성적 요약", level=2)
    headers = ["매치업", "에피소드", "Win", "Lose", "Timeout", "승률", "최근50ep"]
    rows = [
        ["Hybrid × CC",     "1,000", "644", "284", "72", "64.4%", "62%"],
        ["Hybrid × Hybrid", "1,464", "931", "441", "92", "63.6%", "64%"],
        ["Ranged × CC",     "1,000", "551", "430", "19", "55.1%", "60%"],
        ["Ranged × Hybrid", "1,000", "493", "438", "69", "49.3%", "58%"],
        ["Ranged × Ranged", "1,000", "469", "459", "72", "46.9%", "60%"],
    ]
    build_table(doc, headers, rows, col_widths=[2.5, 1.3, 1.0, 1.0, 1.2, 1.2, 1.3])

    # Win rate bar chart
    add_body(doc, "그림 5는 각 매치업의 전체 승률과 최근 50 에피소드 승률을 비교한다. "
                  "Hybrid x CC(64.4%)가 최고 성능을 보이며, "
                  "거리가 가까운 매치업일수록 승률이 높은 경향이 관찰된다. "
                  "또한 대부분의 매치업에서 최근 승률이 전체 승률보다 높아 학습이 수렴 단계에 있음을 확인하였다.", size=9)
    add_figure(doc, "fig_D_winrate_bar.png",
               "[그림 5] 매치업별 보스 승률 비교 (전체 vs 최근 50 에피소드)",
               width_inches=6.5)

    # Win rate trend
    add_body(doc, "그림 6은 100 에피소드 슬라이딩 윈도우로 측정한 승률 추이이다. "
                  "모든 매치업에서 학습 초기 대비 후기의 승률 상승이 관찰되며, "
                  "특히 Ranged x Ranged는 초기 27%에서 후기 60%로 가장 큰 개선폭(+33%p)을 보였다. "
                  "Hybrid x CC는 초기부터 높은 성능을 보이나 중후반에 약간의 변동이 있어, "
                  "장기 학습 시 과적합 가능성을 시사한다.", size=9)
    add_figure(doc, "fig_E_winrate_trend.png",
               "[그림 6] 승률 추이 (100 에피소드 윈도우)",
               width_inches=6.5)

    # Action distribution
    add_body(doc, "그림 7은 매치업별 보스 행동 분포이다. "
                  "원거리 매치업(RxR)에서는 후퇴(Backward) 비율이 48%로 최대이며, "
                  "근거리 매치업(HxC)에서는 15%로 최소이다. "
                  "보스가 매치업 특성에 맞게 이동 전략을 차별화한 것을 확인할 수 있다.", size=9)
    add_figure(doc, "fig_F_action_dist.png",
               "[그림 7] 매치업별 보스 행동 분포 (Idle/Forward/Rotation/Backward)",
               width_inches=6.2)

    # Key metrics highlight
    add_heading(doc, "핵심 수치", level=2)
    metrics = [
        "DPS: 승리 시 6.6–7.3/s vs 패배 시 4.1–4.9/s (+43∼69% 차이)",
        "Phase 0–1: 99–100% → Phase 2: 53–93% → Phase 3: 30–47% 급락",
        "비대칭 킬(스킬 합 홀수): 55–86% 승률 — 1인 빠른 처치가 핵심"
    ]
    for m in metrics:
        add_body(doc, f"  ▶ {m}", size=9, bold=True, color=ORANGE)


# ═══════════════════════════════════════════════════════════
#  PAGE 5: Deep Analysis
# ═══════════════════════════════════════════════════════════
def page5(doc):
    add_page_break(doc)

    add_heading(doc, "12. 심층 분석", level=1)
    add_body(doc, "학습 결과를 거리, 스킬 언락, 페이즈 진행도, DPS 등 다각도로 분석하여 "
                  "보스 승패를 결정짓는 핵심 요인을 도출하였다.", size=9)

    # Distance vs Win Rate
    add_heading(doc, "12.1 DangerRange vs 승률 상관관계", level=2)
    add_body(doc, "각 매치업의 P1+P2 합산 평균 교전 거리와 보스 승률 간의 관계를 분석하였다. "
                  "피어슨 상관계수 r = -0.90로 강한 음의 상관관계를 보이며, "
                  "이는 플레이어가 가까울수록 보스의 공격 기회가 증가하기 때문으로 해석된다.", size=9)
    add_figure(doc, "fig_G_distance_scatter.png",
               "[그림 8] P1+P2 합산 평균거리 vs 보스 승률 (r = -0.90)",
               width_inches=5.5)
    add_body(doc, "DangerRange가 작은 Hybrid/CC 조합(합산 29m)에서 64.4%, "
                  "Ranged × Ranged(합산 50m)에서 46.9%로, "
                  "거리가 보스 성능의 결정적 변수임을 확인하였다. "
                  "이 결과는 런타임에서 ONNX 모델 선택 시 거리 기반 라우팅의 타당성을 뒷받침한다.", size=9)

    # Skill Heatmap
    add_heading(doc, "12.2 스킬 언락 수 vs 승률", level=2)
    add_body(doc, "P1+P2의 스킬 언락 합계(Skill Sum)와 보스 승률의 관계를 히트맵으로 분석하였다. "
                  "스킬 합이 홀수(3,5,7)인 경우는 한쪽 플레이어가 먼저 처치된 '비대칭 킬' 상태를 의미하며, "
                  "짝수(4,6,8)인 경우는 양쪽 모두 생존한 상태를 나타낸다.", size=9)
    add_figure(doc, "fig_H_skill_heatmap.png",
               "[그림 9] P1+P2 스킬 합별 보스 승률 히트맵",
               width_inches=5.8)
    add_body(doc, "홀수 스킬 합에서 55–86%, 짝수 합에서 39–59%로 뚜렷한 차이가 나타난다. "
                  "이는 보스가 '1인 빠른 처치 → 2:1 구도 전환'이라는 핵심 전략을 학습했음을 보여준다.", size=9)

    # Phase analysis
    add_heading(doc, "12.3 페이즈별 승률", level=2)
    add_body(doc, "보스의 페이즈(Phase)는 받은 누적 피해에 따라 0→1→2→3으로 전환된다. "
                  "각 페이즈 전환 시 플레이어 스킬이 추가 해금되므로, "
                  "페이즈가 올라갈수록 보스에게 불리한 환경이 형성된다.", size=9)
    add_figure(doc, "fig_I_phase_winrate.png",
               "[그림 10] 보스 페이즈 진행도별 승률",
               width_inches=6.2)
    add_body(doc, "Phase 0–1 도달 시 99–100%, Phase 2에서 53–93%, "
                  "Phase 3 진입 시 30–47%로 급락한다. "
                  "이 결과는 보스가 Phase 2 이전에 최소 1명을 처치하는 것이 승리의 핵심 조건임을 입증한다.", size=9)

    # DPS comparison
    add_heading(doc, "12.4 승리/패배 DPS 비교", level=2)
    add_body(doc, "승리 시와 패배 시의 보스 DPS(초당 피해량)를 비교하였다. "
                  "승리 시 평균 6.6–7.3 DPS, 패배 시 4.1–4.9 DPS로, "
                  "승리 에피소드에서 43–69% 높은 DPS가 관찰되었다. "
                  "이는 보스가 근접 교전에서의 공격 기회를 효과적으로 활용하고 있음을 시사한다.", size=9)
    add_figure(doc, "fig_extra_dps.png",
               "[그림 11] 매치업별 승리/패배 시 보스 DPS 비교",
               width_inches=5.8)


# ═══════════════════════════════════════════════════════════
#  PAGE 6: Runtime Design + Conclusions + Future Work
# ═══════════════════════════════════════════════════════════
def page6(doc):
    add_page_break(doc)

    add_heading(doc, "13. 런타임 적응형 시스템 설계", level=1)
    add_body(doc, "학습된 ONNX 모델을 실제 게임에 적용하기 위해 런타임 적응형 파이프라인을 설계하였다. "
                  "핵심은 ML 모델(이동/타겟팅)과 서버 로직(스킬 선택)의 역할 분리이다.", size=9)
    add_figure(doc, "fig_J_runtime_pipeline.png",
               "[그림 12] 런타임 데이터 파이프라인 (분류 → 라우팅 → 적응 가중치)",
               width_inches=6.2)

    add_body(doc, "런타임 파이프라인은 3개 모듈로 구성된다: "
                  "(1) PlayerArchetypeClassifier — 플레이어의 스킬 사용 패턴을 실시간 분석하여 "
                  "Melee/Ranged/Hybrid/CC 4종으로 분류한다 (가중치 기반, 30초 윈도우, 감쇠 ×0.3). "
                  "(2) ONNX Model Router — 분류 결과와 플레이어 거리 패턴을 기반으로 "
                  "5개 학습 모델 중 최적 ONNX를 실시간 선택한다. "
                  "(3) BossAdaptiveWeights — 9개 바이어스 인덱스(BiasResponseMap)를 통해 "
                  "매치업별 보스 스킬 선택 가중치를 서버에서 조절한다.", size=9)

    # ONNX model selection guide
    add_heading(doc, "표 7. 런타임 매치업 → ONNX 모델 매핑", level=2)
    headers = ["플레이어 조합", "추천 ONNX", "선택 근거"]
    rows = [
        ["Melee × Melee",      "Hybrid_CC",      "최근접 거리, 최고 성능 모델"],
        ["Melee × CC/Hybrid",  "Hybrid_CC",      "근/중거리 혼합"],
        ["CC × CC",            "Hybrid_CC",      "중거리 대칭"],
        ["Hybrid × Hybrid",    "Hybrid_Hybrid",  "직접 학습 매치업"],
        ["Ranged × Ranged",    "Ranged_Ranged",  "직접 학습 매치업"],
        ["비대칭 (원거리+근거리)",   "Ranged_CC",      "거리 차이 대응"],
    ]
    build_table(doc, headers, rows, col_widths=[3.5, 2.5, 4.5])

    # Conclusions
    add_heading(doc, "14. 결론", level=1)
    add_body(doc, "본 연구를 통해 다음 5가지 핵심 결론을 도출하였다.", size=9)
    conclusions = [
        ("DangerRange가 승률의 결정적 요인",
         "플레이어 교전 거리와 승률 간 r = -0.90의 강한 음의 상관관계를 확인하였다."),
        ("비대칭 킬 전략이 가장 효과적",
         "스킬 합 홀수(한쪽 먼저 처치) 시 55–86% 승률로, 2:1 구도 전환이 보스 승리의 핵심이다."),
        ("Phase 2 이전 처치가 필수",
         "Phase 0–1에서 99–100% 승률이 Phase 3 진입 시 30–47%로 급락한다."),
        ("전이학습으로 학습 효율성 확보",
         "6.1M steps 학습 가중치를 전이하여 초기 250ep에서 56% 달성, 1,000ep에서 최고 성능(64.4%)에 수렴하였다."),
        ("ML + 서버 역할 분리로 런타임 적응 달성",
         "모델은 이동만, 서버는 스킬 선택만 담당하여 학습-운영 간 정합성을 확보하였다."),
    ]
    for i, (title, detail) in enumerate(conclusions, 1):
        add_body(doc, f"  {i}. {title} — {detail}", size=9)

    # Future work
    add_heading(doc, "15. 향후 연구", level=1)
    add_body(doc, "현재 시스템의 한계를 보완하기 위한 향후 연구 방향은 다음과 같다.", size=9)
    futures = [
        "미학습 매치업 5종(Melee 포함) 추가 학습으로 전체 10종 커버리지 확보",
        "CC 분류 가중치 리밸런싱 (cc_skill_cast ×2.5 이상 상향) — 현재 CC 분류 정확도 부족 해소",
        "실제 플레이어 대상 체감 평가 (난이도 적절성, AI 자연스러움 설문 + 플레이 테스트)",
        "관측 40ch → 129ch 런타임 정합성 검증 및 ONNX 추론 성능 최적화"
    ]
    for f in futures:
        add_body(doc, f"  • {f}", size=9)

    # References
    add_heading(doc, "참고문헌", level=1)
    refs = [
        '[1] Millington & Funge, "AI for Games," CRC Press, 3rd ed., 2019.',
        '[2] Vinyals et al., "Grandmaster level in StarCraft II using multi-agent RL," Nature 575, 2019.',
        '[3] Berner et al., "Dota 2 with Large Scale Deep RL," arXiv:1912.06680, 2019.',
        '[4] Schulman et al., "Proximal Policy Optimization Algorithms," arXiv:1707.06347, 2017.',
        '[5] Schulman et al., "High-Dimensional Continuous Control Using Generalized Advantage Estimation," ICLR, 2016.',
        '[6] Mnih et al., "Asynchronous Methods for Deep RL (A3C)," ICML, 2016.',
        '[7] Haarnoja et al., "Soft Actor-Critic: Off-Policy Maximum Entropy Deep RL," ICML, 2018.',
        '[8] Pan et al., "The Effects of Reward Misspecification," ICLR, 2022.',
        '[9] Juliani et al., "Unity: A General Platform for Intelligent Agents," arXiv:1809.02627, 2020.',
    ]
    for r in refs:
        add_body(doc, r, size=7, color=GRAY)


# ═══════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════
def main():
    doc = Document()

    # ── Page setup: A4, narrow margins ──
    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(1.5)
        section.bottom_margin = Cm(1.5)
        section.left_margin = Cm(1.8)
        section.right_margin = Cm(1.8)

    # ── Default font ──
    style = doc.styles['Normal']
    font = style.font
    font.name = "Malgun Gothic"
    font.size = Pt(9)
    style.paragraph_format.space_before = Pt(1)
    style.paragraph_format.space_after = Pt(1)

    # Build pages
    page1(doc)
    page2(doc)
    page3(doc)
    page4(doc)
    page5(doc)
    page6(doc)

    out_path = OUT_DIR / "Tenebris_Poster_A4x6_v3.docx"
    doc.save(str(out_path))
    print(f"Saved: {out_path}")
    print(f"Size: {out_path.stat().st_size / 1024:.0f} KB")

if __name__ == "__main__":
    main()
