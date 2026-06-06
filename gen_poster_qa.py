"""포스터 발표 대비 — 상세 Q&A 레퍼런스 문서 생성"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()
style = doc.styles['Normal']
style.font.name = 'Malgun Gothic'
style.font.size = Pt(10)

def h1(text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.size = Pt(14)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x1B, 0x3A, 0x5C)
    r.font.name = 'Malgun Gothic'
    r._element.rPr.rFonts.set(qn('w:eastAsia'), 'Malgun Gothic')

def h2(text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.size = Pt(12)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x2E, 0x6B, 0x9E)
    r.font.name = 'Malgun Gothic'
    r._element.rPr.rFonts.set(qn('w:eastAsia'), 'Malgun Gothic')

def body(text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.size = Pt(10)
    r.font.name = 'Malgun Gothic'
    r._element.rPr.rFonts.set(qn('w:eastAsia'), 'Malgun Gothic')

def qa(q, a):
    p = doc.add_paragraph()
    rq = p.add_run(f'Q: {q}')
    rq.font.size = Pt(10)
    rq.font.bold = True
    rq.font.name = 'Malgun Gothic'
    rq._element.rPr.rFonts.set(qn('w:eastAsia'), 'Malgun Gothic')
    doc.add_paragraph()
    p2 = doc.add_paragraph()
    ra = p2.add_run(f'A: {a}')
    ra.font.size = Pt(10)
    ra.font.name = 'Malgun Gothic'
    ra._element.rPr.rFonts.set(qn('w:eastAsia'), 'Malgun Gothic')
    doc.add_paragraph()

X = chr(215)  # ×

# ═══════════════════════════════════════
h1('포스터 발표 대비 — 상세 레퍼런스 문서')
body('논문: Adaptive Boss AI Design and Analysis through Matchup-Specialized Reinforcement Learning')
body('저자: 백성열, 홍채영, 곽다영, 김지형* (국립금오공과대학교)')
body('학회: 2026 한국정보기술학회 하계 종합학술대회')
doc.add_paragraph()

# ═══════════════════════════════════════
h1('1. 연구 개요')
# ═══════════════════════════════════════

h2('1.1 연구 배경 및 동기')
body('• 기존 보스 AI는 Behavior Tree(BT), 유한상태기계(FSM) 등 규칙 기반 방식으로 설계됨')
body('• 규칙 기반의 한계: 전투 패턴 고정 → 플레이어가 패턴 학습 후 긴장감 저하')
body('• 멀티플레이 환경에서는 플레이어 조합이 매번 달라짐 → 고정 패턴으로는 대응 불가')
body('• 강화학습(RL) 기반 게임 AI 선행연구: AlphaStar(StarCraft II), OpenAI Five(Dota 2)')
body('  - 그러나 이들은 대규모 컴퓨팅 자원 전제, 상용 게임 환경 직접 적용에 제약')
body('• 본 연구: 비교적 적은 자원으로 보스 AI가 매치업에 따라 다른 전투 행동을 학습하는지 분석')

h2('1.2 핵심 기여 (3가지)')
body('(1) 매치업별 상이한 전투 행동이 강화학습만으로 자연발생함을 실증')
body('(2) 학습 과정에서 나타나는 과학습 현상을 Sharp Drop, Double Dip, Gradual Decay 3가지 패턴으로 관찰 및 유형화')
body('(3) 동일 승률 82%에서 대기 비율 19% vs 2.4% → 승률 단일 지표의 한계 정량 입증')

h2('1.3 연구 질문 (Research Questions)')
body(f'RQ1. 보스 AI가 9종 매치업별로 서로 다른 전투 행동을 학습하는가?')
body(f'RQ2. 학습 과정에서 어떤 과학습 패턴이 발생하는가?')
body(f'RQ3. 승률만으로 학습 품질을 평가할 수 있는가?')
doc.add_paragraph()

# ═══════════════════════════════════════
h1('2. 실험 환경 및 방법')
# ═══════════════════════════════════════

h2('2.1 게임 환경')
body('• 게임: 테네브리스(Tenebris) — Unity 6 기반 3D 톱다운 액션 게임')
body('• 전투 구성: 보스 1체 vs 플레이어 BT 봇 2체')
body('• 아레나: 반지름 약 50m 원형')
body('• 에피소드 종료 조건: 플레이어 전원 사망(보스 승리), 보스 사망(보스 패배), 시간 초과(Timeout)')

h2('2.2 관측 공간 (129채널)')
body('• 보스 자신 상태: HP, Phase 등 (4ch)')
body('• 보스 스킬: 5슬롯 × 7ch = 35ch')
body('• 플레이어 1 상태 + 스킬: 위치/거리/각도 + 5슬롯 × 7ch')
body('• 플레이어 2 상태 + 스킬: 동일 구조')
body('• 관계 정보: 거리, 각도, 접촉 여부 등')
body('• 추가 정보: 캐스팅 상태, 이동속도, 스킬 해금, 버스트 상태 등 (7ch)')
body('• 총 129채널 — 초기에는 더 적었으나 Phase 2 이후 스킬 정보 + 후퇴 행동 추가로 확장')

h2('2.3 행동 공간 (5가지 이산 행동)')
body('• 0 = Idle (대기)')
body('• 1 = Forward (전진)')
body('• 2 = Turn Left (좌회전)')
body('• 3 = Turn Right (우회전)')
body('• 4 = Retreat (후퇴)')
body('• DecisionPeriod = 5 (5프레임마다 1회 결정)')
body('※ 스킬 사용은 ML이 아닌 서버 측 로직(BossAdaptiveWeights)이 담당')

h2('2.4 PPO 하이퍼파라미터')
body('• Batch Size: 1,024')
body('• Buffer Size: 10,240')
body('• Learning Rate: 0.0003 (linear schedule)')
body('• Beta (엔트로피): 0.005')
body('• Epsilon (클리핑): 0.2')
body('• Lambda: 0.95')
body('• Gamma: 0.995')
body('• Num Epoch: 3')
body('• Hidden Units: 256, Num Layers: 3')
body('• Max Steps: 40,000,000 (40M)')
body('• Time Horizon: 1,024')

h2('2.5 3단계 커리큘럼 학습')
body('• Stage 1 — Touch (5M steps): 보스가 플레이어에게 접근하는 기본 움직임 학습')
body('• Stage 2 — Engage (10M steps): 교전 거리 유지 행동 학습')
body('• Stage 3 — Combat (40M steps): 실제 전투 환경에서 최종 전략 학습')
body('• 각 단계는 이전 단계 체크포인트를 initialize-from으로 이어받음')
body('• 총 55M steps (5M + 10M + 40M)')

h2('2.6 보상 설계')
body('• 거리 보상: 플레이어와의 적정 거리 유지')
body('• 공격 적중 보상: 보스 공격이 플레이어에게 명중 시')
body('• 승리 보너스: 에피소드 승리 시 추가 보상')
body('• 가중합 방식으로 통합')

h2('2.7 플레이어 아키타입 (4종)')
body(f'• Melee: 근접 버스트 딜러 (5-10m) — ExecutionSpike, CrushingBarrage')
body(f'• Ranged: 원거리 카이팅 (20-30m) — PiercingShot, RuptureMagazine')
body(f'• CC: 군중제어 (8-14m) — SealChain, CollapseRoar')
body(f'• Hybrid: 유연한 생존자 (6-30m) — SurvivalPulse, OverchargeMode')

h2('2.8 매치업 구성')
body(f'• 4종 아키타입의 2인 조합: 4{X}4 = 16종')
body(f'• CC{X}CC 제외 (교착 상태 발생으로 학습 수렴 불가) → 9종 매치업')
body(f'  - CC 포함 아닌 실제 학습 대상: H{X}C, H{X}H, R{X}C, R{X}H, R{X}R + Melee 조합들')
body(f'• 매치업당 약 1,000판, 전체 9,134판 평가 데이터')
doc.add_paragraph()

# ═══════════════════════════════════════
h1('3. 실험 결과 — 상세 수치')
# ═══════════════════════════════════════

h2('3.1 전체 매치업별 성적 (9,134판, episodes_BossInference.csv)')
body(f'매치업          | 판수   | 승률')
body(f'Melee{X}Melee   | 1,031 | 85.4%')
body(f'Melee{X}Hybrid  |   513 | 69.2%')
body(f'Melee{X}CC      |   479 | 69.9%')
body(f'Melee{X}Ranged  | 1,040 | 46.0%')
body(f'Hybrid{X}Melee  |   487 | 69.6%')
body(f'Hybrid{X}CC     |   489 | 67.3%')
body(f'Hybrid{X}Hybrid | 1,000 | 57.4%')
body(f'Hybrid{X}Ranged |   502 | 63.9%')
body(f'CC{X}Hybrid     |   511 | 65.2%')
body(f'CC{X}Melee      |   521 | 69.5%')
body(f'CC{X}Ranged     |   504 | 62.7%')
body(f'Ranged{X}CC     |   496 | 61.1%')
body(f'Ranged{X}Hybrid |   498 | 61.8%')
body(f'Ranged{X}Ranged | 1,000 | 62.8%')
body(f'CC{X}CC         |    37 | 54.1% (제외 대상)')
body(f'※ PlayerWin 0건 — BT 봇이 보스 공격 회피 능력 부족으로 승률 과대 측정')

h2('3.2 포스터 그래프용 5종 매치업 (개별 CSV)')
body(f'매치업 | 판수  | 전체WR | 최근100판 | Idle비율')
body(f'H{X}C  | 1,000 | 64.4%  | 62%      | 38.9%')
body(f'H{X}H  | 1,464 | 63.6%  | 66%      | 35.1%')
body(f'R{X}C  | 1,000 | 55.1%  | 55%      | 29.8%')
body(f'R{X}H  | 1,000 | 49.3%  | 59%      | 28.9%')
body(f'R{X}R  | 1,000 | 46.9%  | 60%      | 23.3%')

h2('3.3 RQ1 — 매치업별 행동 분포')
body(f'• 9종 매치업 모두 보상이 양(+)으로 수렴 → 전투 개입이 유리함을 학습')
body(f'• Melee 상대: Forward 비율 40%+ (적극 접근)')
body(f'• Ranged 상대: Retreat 30% + Turn 25% (거리 유지 + 회전)')
body(f'• M{X}M: Idle 19% — 순수 근접 상대에게 "대기 후 반격" 전략')
body(f'• CC/Hybrid 상대: Idle 2~3% — 거의 쉬지 않고 적극 전투')
body(f'• 결론: 상대 조합에 따라 명확히 다른 행동 분포 → 적응적 전투 행동 학습 확인')

h2('3.4 RQ2 — 과학습 패턴 (3가지 관찰)')
body('※ 아래 명칭은 본 실험에서 관찰된 곡선 패턴에 대한 서술적 명명이며, 기존 RL 문헌의 공식 분류 체계가 아님.')
body('※ RL에서 학습 후반부 성능 하락은 policy collapse, catastrophic forgetting 등으로 알려진 현상임.')
body('')
body(f'Type 1 — Sharp Drop (R{X}R):')
body(f'  학습 중반(25M~30M steps) 이후 승률 급격 하락, 이후 일부 회복')
body(f'  원인 추정: 단조로운 원거리 상대 패턴에 과도하게 특화')
body('')
body(f'Type 2 — Double Dip (H{X}H):')
body(f'  학습 과정에서 성능 하락이 2회 반복 발생')
body(f'  Timeout 비율 9.5%로 전 매치업 중 최고 → 확실한 승리 실패')
body('')
body(f'Type 3 — Gradual Decay (H{X}R):')
body(f'  성능이 급격히 떨어지지 않고 서서히 하락')
body(f'  학습 곡선만으로는 탐지 어려움 → 가장 위험한 유형')
body('')
body(f'Control — Stable (C{X}H):')
body(f'  비교적 안정적으로 학습 완료된 사례')
body('')
body(f'공통점: 유사 유형끼리 구성된 매치업(R{X}R, H{X}H)에서 과학습 집중')
body(f'해석: 상대 행동이 단조로울수록 특정 패턴에만 과적합')
body(f'과학습 발생 시점: 평균 25M~35M steps 구간')

h2('3.5 RQ3 — 승률의 한계')
body(f'핵심 사례:')
body(f'  M{X}M: WR 82%, Idle 19% (전투 시간의 1/5을 대기)')
body(f'  M{X}H: WR 82%, Idle 2.4% (거의 쉬지 않고 적극 전투)')
body(f'  → 동일 승률이지만 행동 전략은 정반대')
body('')
body(f'통계 분석:')
body(f'  WR과 Idle 간 상관계수: r = -0.23 (유의미하지 않음, n.s.)')
body(f'  → 승률이 높다고 적극적 전투를 의미하지 않음')
body('')
body(f'Outcome 분석 (포스터에는 미포함, 질문 대비):')
body(f'  전체 9,134판 중 PlayerWin = 0건')
body(f'  → BT 봇 회피 능력 부족으로 보스 승률 과대 측정')
body(f'  H{X}H Timeout 비율 9.5% (전 매치업 중 최고)')
body(f'  → 이중 하락형 과학습과 직접 연결')
body('')
body(f'결론: WR + Idle Ratio + Timeout Rate 등 다중 지표 병행 분석 필요')
doc.add_paragraph()

# ═══════════════════════════════════════
h1('4. Discussion 핵심 논점')
# ═══════════════════════════════════════

h2('4.1 유사 유형 매치업의 overfitting 원인')
body(f'• 유사 유형 → 상대 행동 패턴 단조 → 특정 패턴에만 과적합')
body(f'• 반면 C{X}H처럼 이질적 조합에서는 다양한 상황 경험 → 범용적 전략 학습')
body(f'• BT 봇의 고정된 행동 패턴 자체가 과적합을 가속화하는 요인')

h2('4.2 실제 게임 적용 시 고려사항')
body('• BT 봇 회피 불가 → 승률 과대 측정 → 실제 플레이어 대상 시 보스 HP 하향 필요')
body('• Early Stopping 필수: 25M~35M steps에서 과학습 감지 시 자동 중단')
body('• 다중 지표 모니터링: WR뿐 아니라 Idle Ratio, Timeout Rate 함께 관찰')

h2('4.3 ML의 역할 분리')
body('• ML(ONNX 모델): 이동 행동만 담당 (5가지 이산 행동)')
body('• 서버 로직(BossAdaptiveWeights): 스킬 선택, 타이밍 담당')
body('• 이유: 스킬까지 ML에 넣으면 행동 공간이 너무 커져 학습 수렴 어려움')
doc.add_paragraph()

# ═══════════════════════════════════════
h1('5. 결론 및 향후 연구')
# ═══════════════════════════════════════

h2('5.1 결론')
body('Finding 1: 상대 유형별 상이한 전투 행동 학습 확인 (RQ1)')
body('Finding 2: 3가지 과학습 패턴 관찰 — 유사 유형 매치업에서 집중 발생 (RQ2)')
body('Finding 3: 같은 WR 82%에서 Idle 19% vs 2.4% — 승률만으로 평가 불충분 (RQ3)')

h2('5.2 향후 연구')
body('• Early Stopping 도입으로 overfitting 방지')
body('• 실제 플레이어 대상 밸런스 조정 (보스 HP 하향)')
body('• 스킬 사용 타이밍까지 행동 공간 확장')
body('• 3인 이상 혼합 매치업 시나리오 연구')
doc.add_paragraph()

# ═══════════════════════════════════════
h1('6. 예상 질문 & 답변 (확장판)')
# ═══════════════════════════════════════

qa(f'왜 CC{X}CC 조합은 제외했나요?',
   f'CC{X}CC는 양쪽 플레이어가 모두 제어기 중심이라 의미 있는 전투 상황이 안정적으로 발생하지 않았습니다. 실제로 37판만 수집되었고 승률도 54.1%로 불안정했습니다. 학습이 제대로 수렴하지 않아 최종 분석에서 제외했습니다.')

qa('실제 플레이어를 상대로도 같은 결과가 나올 수 있나요?',
   '현재 BT 봇은 보스 공격 회피 능력이 부족해서 보스 승률이 과대 측정되었습니다 (PlayerWin 0건). 실제 플레이어는 회피 능력이 있으므로 보스 승률이 크게 낮아질 것으로 예상됩니다. 따라서 보스 HP 하향, 공격 패턴 조정 등 밸런싱이 추가로 필요합니다.')

qa('왜 PPO 알고리즘을 사용했나요?',
   'PPO는 학습 안정성이 높고 Unity ML-Agents에서 기본 지원됩니다. 본 연구의 행동 공간은 5가지 이산 행동이므로, 연속 행동에 적합한 SAC보다 PPO가 더 적합합니다. 또한 PPO의 클리핑 메커니즘(epsilon=0.2)이 급격한 정책 변화를 방지하여 안정적 학습이 가능합니다.')

qa('왜 SAC가 아닌 PPO인가요? (심화)',
   'SAC(Soft Actor-Critic)는 연속 행동 공간에 최적화된 off-policy 알고리즘입니다. 본 연구의 행동 공간은 이산(Discrete) 5가지이므로 PPO가 자연스럽습니다. Unity ML-Agents에서도 이산 행동에는 PPO를 권장하고 있습니다.')

qa('129채널 관측 정보가 너무 많은 것은 아닌가요?',
   '초기에는 더 적은 채널을 사용했지만, Phase 2 이후 스킬 쿨다운, 후퇴 행동 관련 정보가 추가되면서 129채널로 확장되었습니다. 은닉층을 256유닛 × 3레이어로 구성하여 충분한 표현력을 확보했으며, 학습 수렴에 문제가 없었습니다.')

qa('과학습 유형 명칭(Sharp Drop 등)은 기존 문헌에 있는 건가요?',
   '아닙니다. Sharp Drop, Double Dip, Gradual Decay는 본 실험에서 관찰된 학습 곡선 패턴에 대해 저희가 부여한 서술적 명칭입니다. RL 문헌에서 학습 후반부 성능 하락은 policy collapse, catastrophic forgetting 등으로 알려져 있으며, 저희는 이러한 현상이 매치업 유형에 따라 다른 양상으로 나타남을 관찰하고 유형화한 것입니다.')

qa('과학습은 어떻게 방지할 수 있나요?',
   '가장 현실적인 방법은 Early Stopping입니다. 승률이나 보상이 25M~35M steps 이후 하락 패턴을 보이면 자동으로 학습을 중단합니다. 추가로 매치업별 별도 모델 관리, 평가 시 승률 외에 Idle Ratio와 Timeout Rate를 함께 모니터링하는 방법도 효과적입니다.')

qa('왜 이동 행동만 학습시키고 스킬은 포함하지 않았나요?',
   '스킬까지 행동 공간에 포함하면 조합 수가 급격히 증가하여 학습 수렴이 어려워집니다. 현재 5가지 이동 행동만으로도 매치업별 전략 차이가 명확히 나타났으므로, 이동 행동의 학습 가능성을 먼저 검증하는 것이 본 연구의 범위입니다. 스킬 타이밍 학습은 향후 연구 과제입니다.')

qa('Timeout이 발생하는 이유는 무엇인가요?',
   f'보스가 학습 과정에서 적극적 전투보다 회피나 대기 위주 전략을 학습한 경우 에피소드가 시간 초과로 종료됩니다. 특히 H{X}H에서 Timeout 9.5%로 가장 높았으며, 이는 이중 하락형 과학습과 연결됩니다. 보스가 확실하게 승리하지 못하고 전투가 길어지는 패턴입니다.')

qa('3단계 커리큘럼 학습의 효과는 어떻게 검증했나요?',
   '각 단계별 학습 곡선을 모니터링했습니다. Touch 단계에서 접근 행동 학습, Engage에서 교전 거리 유지, Combat에서 실전 전략 학습이 순차적으로 이루어졌습니다. initialize-from 방식으로 이전 단계 지식을 이어받아 학습 효율이 향상되었습니다.')

qa('9종 매치업을 동시에 학습시킨 건가요, 따로 학습시킨 건가요?',
   '따로 학습시켰습니다. 각 매치업별로 독립적인 학습 세션을 진행했습니다. 다만 일부 매치업은 다른 매치업의 체크포인트를 initialize-from으로 이어받아 전이학습 효과를 활용했습니다.')

qa('승률이 가장 높은/낮은 매치업은?',
   f'가장 높은 승률: M{X}M 85.4% — 근접 상대에게 보스가 가장 효과적으로 학습\n'
   f'가장 낮은 승률: M{X}Ranged 46.0% — 원거리 상대에게 근접 보스가 접근 어려움')

qa('r=-0.23이 통계적으로 유의미하지 않다는 근거는?',
   '피어슨 상관계수 r=-0.23은 약한 음의 상관을 보이지만, 9종 매치업(n=9)으로는 통계적 유의수준(p<0.05)에 도달하지 못합니다. 즉, 승률과 Idle 비율 사이에 체계적인 관계가 있다고 단정할 수 없습니다.')

qa('BT 봇의 행동 패턴은 어떻게 구성했나요?',
   'Melee 봇: 적에게 5-10m까지 돌진하여 근접 스킬 사용\n'
   'Ranged 봇: 20-30m 거리를 유지하며 원거리 스킬로 카이팅\n'
   'CC 봇: 8-14m 중거리에서 군중제어 스킬 사용\n'
   'Hybrid 봇: 6-30m 범위에서 상황에 따라 거리 전환\n'
   '모든 봇은 Behavior Tree 기반이며 보스 공격에 대한 회피 능력은 없습니다.')

qa('Unity ML-Agents 버전은?',
   'Unity ML-Agents 1.2.0 (Release 21), 학습 프레임워크는 PyTorch 2.2.2+cu121 기반입니다.')

qa('학습에 사용한 하드웨어와 소요 시간은?',
   '로컬 PC에서 Unity Editor 연동으로 학습했습니다. time_scale=20으로 가속하여 매치업당 약 6~8시간 소요되었습니다. 전체 9종 매치업 55M steps는 약 3~4일 소요되었습니다.')

qa('왜 normalize를 false로 설정했나요?',
   '관측값의 범위가 이미 알려져 있고(HP는 0~1, 거리는 정규화), 추가적인 running normalization이 학습 초기 불안정을 유발할 수 있어 false로 설정했습니다.')

qa('Gamma를 0.995로 높게 설정한 이유는?',
   '보스 전투는 에피소드가 길고(평균 300~450초), 승리 보상은 에피소드 종료 시점에 주어집니다. 먼 미래의 보상을 충분히 반영하기 위해 감쇠율을 0.995로 설정했습니다.')

qa('포스터에 Outcome 분석(Fig. 5)이 빠진 이유는?',
   '포스터 공간 제약으로 Fig. 5를 제외했습니다. 핵심 메시지(승률만으로 부족)는 Fig. 4의 Idle 분석으로 충분히 전달됩니다. Outcome 분석의 핵심 수치: PlayerWin 0건, H{X}H Timeout 9.5%입니다.')

# ═══════════════════════════════════════
h1('7. References')
# ═══════════════════════════════════════
body('[1] I. Millington and J. Funge, "AI for Games," CRC Press, 3rd ed., 2019.')
body('[2] O. Vinyals et al., "Grandmaster level in StarCraft II using multi-agent RL," Nature, 575, 2019.')
body('[3] C. Berner et al., "Dota 2 with large scale deep RL," arXiv:1912.06680, 2019.')
body('[4] J. Schulman et al., "Proximal policy optimization algorithms," arXiv:1707.06347, 2017.')
body('[5] A. Pan et al., "The effects of reward misspecification," Proc. ICLR, 2022.')
body('[6] A. Juliani et al., "Unity: A general platform for intelligent agents," arXiv:1809.02627, 2020.')

# 저장
out = r'C:\Users\paek6\Desktop\포스터 Q&A 레퍼런스.docx'
try:
    doc.save(out)
except PermissionError:
    out = r'C:\Users\paek6\Desktop\포스터 Q&A 레퍼런스_v2.docx'
    doc.save(out)
print(f'Done: {out}')
