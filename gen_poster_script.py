"""포스터 발표 스크립트 — 2단 A1 포스터 최종본 기준 업데이트"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn

doc = Document()
style = doc.styles['Normal']
style.font.name = 'Malgun Gothic'
style.font.size = Pt(11)

def add_bold(text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.bold = True
    r.font.size = Pt(11)
    r.font.name = 'Malgun Gothic'
    r._element.rPr.rFonts.set(qn('w:eastAsia'), 'Malgun Gothic')

def add_normal(text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.size = Pt(11)
    r.font.name = 'Malgun Gothic'
    r._element.rPr.rFonts.set(qn('w:eastAsia'), 'Malgun Gothic')

def blank():
    doc.add_paragraph()

X = '×'

add_bold(f'논문: Adaptive Boss AI Design and Analysis through Matchup-Specialized Reinforcement Learning\n발표 시간: 약 5분\n발표자: 백성열')
blank()

# ─── 왼쪽 컬럼 ───
add_bold('[왼쪽 컬럼] Introduction + Research Objectives + Method + RQ1')
blank()

add_normal('안녕하십니까.\n발표를 맡은 국립금오공과대학교 백성열입니다.')
blank()

add_normal('저희 연구는 강화학습 기반 보스 AI가 플레이어 조합에 따라 서로 다른 전투 행동을 학습할 수 있는지를 분석한 연구입니다.')

add_normal('기존 게임의 보스 AI는 주로 Behavior Tree와 같은 규칙 기반 방식으로 설계됩니다. '
           '이러한 방식은 개발자가 의도한 패턴을 안정적으로 구현할 수 있다는 장점이 있지만, '
           '전투 패턴이 고정되기 쉽고 다양한 플레이어 조합에 유연하게 대응하기 어렵다는 한계가 있습니다. '
           '특히 멀티플레이 환경에서는 플레이어 조합이 다양하게 변화하므로, '
           '보스 AI가 특정 패턴만 반복하면 전략적 깊이와 리플레이 가치가 크게 떨어집니다.')

add_normal(f'저희는 이 문제를 해결하기 위해 PPO 기반 강화학습을 적용했습니다. '
           f'보스에게는 대기, 전진, 좌회전, 우회전, 후퇴라는 5가지 이동 행동만 제공하고, '
           f'플레이어 조합에 따라 스스로 전투 방식을 학습하도록 설계했습니다. '
           f'전체 학습은 총 55M steps 동안 진행되었으며, CC{X}CC를 제외한 9종 매치업을 대상으로 분석했습니다.')

add_normal(f'먼저 핵심 문제의식을 말씀드리면, 예를 들어 Melee{X}Melee와 Melee{X}Hybrid는 모두 승률이 82%로 동일합니다. '
           f'하지만 대기 비율은 각각 19%와 2.4%로 큰 차이를 보입니다. '
           f'즉, 승률만 보면 두 모델이 비슷하게 학습된 것처럼 보이지만, 실제 행동 전략은 완전히 다르게 나타났습니다.')

add_normal('따라서 본 연구의 목표는 세 가지입니다.\n'
           '첫째, 보스 AI가 상대 조합에 따라 서로 다른 전투 행동을 학습하는지 확인하는 것입니다.\n'
           '둘째, 학습 과정에서 나타나는 과학습 패턴을 분류하는 것입니다.\n'
           '셋째, 승률만으로 보스 AI의 학습 품질을 평가하는 것이 충분한지 검증하는 것입니다.')
blank()

# Method
add_bold('[Method — Fig. 1 참조]')

add_normal('다음은 연구 방법입니다.\n그림 1은 전체 학습 구조와 보스 AI의 관측 및 행동 공간을 보여줍니다.')

add_normal('먼저 왼쪽은 3단계 커리큘럼 학습 파이프라인입니다.\n'
           '1단계 Touch에서는 보스가 플레이어에게 접근하는 기본 움직임을 5M steps 동안 학습합니다.\n'
           '2단계 Engage에서는 교전 거리를 유지하는 행동을 10M steps 동안 학습합니다.\n'
           '마지막 3단계 Combat에서는 실제 전투 환경에서 보상과 승률을 기반으로 40M steps 동안 최종 전투 전략을 학습합니다.')

add_normal('각 단계는 독립적으로 시작하지 않고, 이전 단계에서 학습된 체크포인트를 이어받는 방식으로 구성했습니다. '
           '이를 통해 보스가 단순 이동에서 시작해 점진적으로 전투 행동을 학습하도록 설계했습니다.')

add_normal('오른쪽은 보스의 관측 정보와 행동 공간입니다.\n'
           '보스는 총 129채널의 관측 정보를 입력받습니다. '
           '여기에는 보스 자신의 상태, 두 명의 플레이어 상태, 거리, 각도, 스킬 쿨다운과 같은 정보가 포함됩니다.')

add_normal('행동 공간은 비교적 단순하게 구성했습니다.\n보스가 선택할 수 있는 행동은 대기, 전진, 좌회전, 우회전, 후퇴 총 5가지입니다.')

add_normal(f'실험 환경은 Unity 6 기반으로 제작한 3D 톱다운 액션 게임 테네브리스입니다.\n'
           f'플레이어는 Melee, Ranged, CC, Hybrid 4가지 유형의 Behavior Tree 봇으로 구성했으며, '
           f'이 중 CC{X}CC를 제외한 9종 조합을 대상으로 실험을 진행했습니다.\n'
           f'보상은 거리 보상, 공격 적중, 승리 보너스의 가중합으로 설계했습니다.')
blank()

# RQ1
add_bold('[RQ1: Adaptive Combat Behavior — Fig. 2 참조]')

add_normal('첫 번째 연구 질문은 보스 AI가 상대 조합에 따라 다른 전투 행동을 학습하는가입니다.')

add_normal('그림 2의 위쪽 그래프는 그룹별 학습 곡선을 보여주고, 아래 그래프는 최종 학습 후의 행동 분포를 보여줍니다.')

add_normal('먼저 학습 곡선을 보면, 9종 매치업 모두에서 보상이 양수 방향으로 수렴했습니다. '
           '이는 보스가 단순히 가만히 있는 것보다, 전진하거나 회전하거나 후퇴하는 방식으로 전투에 적극적으로 개입하는 것이 더 유리하다는 점을 학습했다는 의미입니다.')

add_normal('행동 분포를 보면 상대 유형에 따른 차이가 더 명확하게 나타납니다.\n'
           'Melee 계열 상대에게는 전진 비율이 40% 이상으로 높게 나타났고, '
           'Ranged 계열 상대에게는 후퇴 30%와 회전 25% 비율이 상대적으로 높게 나타났습니다. '
           '즉, 보스가 모든 상대에게 같은 방식으로 행동한 것이 아니라, 상대 조합에 따라 다른 이동 전략을 학습했다는 것을 확인할 수 있습니다.')

add_normal(f'특히 Melee{X}Melee 매치업에서는 대기 비율이 19%로 높게 나타났습니다. '
           f'반면 CC나 Hybrid가 포함된 조합에서는 대기 비율이 2~3% 수준으로 낮았습니다.\n'
           f'이는 순수 근접 전투 조합을 상대로는 무조건 접근하기보다, 일정 시간 기다린 뒤 반격하는 전략이 더 효과적으로 학습되었기 때문으로 해석할 수 있습니다.')

add_normal('따라서 RQ1에 대해서는, 보스 AI가 플레이어 조합에 따라 서로 다른 전투 행동을 학습했다고 볼 수 있습니다.')
blank()

# ─── 오른쪽 컬럼 ───
add_bold('[오른쪽 컬럼] RQ2 + RQ3 + Discussion + Conclusion')
blank()

# RQ2
add_bold('[RQ2: Overfitting Patterns — Fig. 3 참조]')

add_normal('두 번째 연구 질문은 학습 과정에서 어떤 과학습 패턴이 발생하는가입니다.')

add_normal('그림 3은 대표적인 4종 매치업의 보상과 승률 변화를 보여줍니다.\n분석 결과, 저희는 총 3가지 과학습 패턴을 확인했습니다.')

add_normal(f'첫 번째는 급격한 하락형(Sharp Drop)입니다.\n'
           f'Ranged{X}Ranged 매치업에서 나타난 패턴으로, 학습 중반 이후 승률이 급격하게 떨어지고, 이후 일부만 회복되는 형태를 보였습니다.')

add_normal(f'두 번째는 이중 하락형(Double Dip)입니다.\n'
           f'Hybrid{X}Hybrid 매치업에서 나타났으며, 학습 과정에서 성능 하락이 한 번이 아니라 두 차례 반복적으로 발생했습니다.')

add_normal(f'세 번째는 점진적 저하형(Gradual Decay)입니다.\n'
           f'Hybrid{X}Ranged 매치업에서 나타난 패턴으로, 성능이 급격히 떨어지지 않고 서서히 나빠지는 형태입니다. '
           f'이 유형은 학습 곡선만 보면 쉽게 놓칠 수 있기 때문에 가장 탐지하기 어려운 과학습 유형이라고 볼 수 있습니다.')

add_normal(f'반면 CC{X}Hybrid 매치업은 비교적 안정적으로 학습이 완료된 사례였습니다.')

add_normal(f'이 결과에서 중요한 점은, 과학습이 모든 조합에서 동일하게 발생한 것이 아니라는 점입니다.\n'
           f'특히 Ranged{X}Ranged, Hybrid{X}Hybrid처럼 비슷한 유형끼리 구성된 매치업에서 과학습이 집중적으로 나타났습니다.')

add_normal('이는 상대 행동 패턴이 단조롭거나 유사할수록, 보스가 다양한 상황에 대응하는 전략을 배우기보다 '
           '특정 행동 패턴에 과도하게 적응했기 때문으로 해석할 수 있습니다.')
blank()

# RQ3
add_bold('[RQ3: Win Rate Is Not Enough — Fig. 4 참조]')

add_normal('세 번째 연구 질문은 승률만으로 학습 품질을 평가할 수 있는가입니다.')

add_normal('일반적으로 강화학습 결과를 평가할 때 승률이 높으면 좋은 모델이라고 판단하기 쉽습니다. '
           '하지만 본 연구에서는 승률만으로는 보스 AI의 학습 품질을 충분히 설명할 수 없다는 결과가 나타났습니다.')

add_normal(f'그림 4를 보시면, Melee{X}Melee와 Melee{X}Hybrid는 모두 승률이 82%로 동일합니다.\n'
           f'하지만 두 매치업의 행동 분포는 크게 다릅니다. '
           f'Melee{X}Melee는 대기 비율이 19%인 반면, Melee{X}Hybrid는 2.4%에 불과합니다.')

add_normal('즉, 두 모델은 같은 승률을 기록했지만, 하나는 전투 시간의 약 5분의 1을 대기하면서 반격하는 전략을 사용했고, '
           '다른 하나는 거의 쉬지 않고 적극적으로 움직이는 전략을 사용했습니다.')

add_normal('또한 통계적으로도 승률과 대기 비율 사이에는 유의미한 상관관계가 나타나지 않았습니다(r=-0.23, n.s.).\n'
           '이는 승률이 높다고 해서 반드시 적극적이고 안정적인 전투 행동을 학습했다고 볼 수 없다는 의미입니다.')

add_normal('따라서 본 연구에서는 보스 AI의 학습 품질을 평가할 때 단순히 Win Rate만 볼 것이 아니라, '
           'Idle Ratio와 같은 행동 지표를 함께 분석해야 한다고 판단했습니다.')
blank()

# Discussion + Conclusion
add_bold('[Discussion + Conclusion]')

add_normal('마지막으로 결론입니다.')

add_normal('본 연구의 기여는 세 가지로 정리할 수 있습니다.')

add_normal('첫째, 강화학습 기반 보스 AI가 상대 플레이어 조합에 따라 서로 다른 전투 행동을 학습한다는 것을 확인했습니다.')

add_normal('둘째, 학습 과정에서 과학습이 단일한 형태로 나타나는 것이 아니라, '
           '급격한 하락형, 이중 하락형, 점진적 저하형의 세 가지 패턴으로 나타난다는 것을 확인했습니다. '
           '특히 유사한 유형끼리 구성된 매치업에서 과학습이 집중되는 경향을 보였습니다.')

add_normal('셋째, 승률만으로는 보스 AI의 학습 품질을 충분히 평가할 수 없으며, '
           '행동 분포를 함께 분석해야 한다는 점을 실험적으로 보였습니다.')

add_normal('향후 연구에서는 과학습을 방지하기 위한 Early Stopping을 도입하고, '
           '실제 플레이어를 대상으로 밸런스를 조정할 계획입니다. '
           '또한 현재는 이동 행동만 학습 대상으로 삼았지만, '
           '이후에는 스킬 사용 타이밍까지 행동 공간에 포함하여 보다 복합적인 보스 AI를 설계할 예정입니다.')

add_normal('이상으로 발표를 마치겠습니다.\n감사합니다. 질문 있으시면 말씀해 주십시오.')
blank()
blank()

# ─── 예상 질문 ───
add_bold('예상 질문 및 답변')
blank()

add_normal(f'Q1. 왜 CC{X}CC 조합은 제외했나요?')
add_normal(f'CC{X}CC 조합은 양쪽 플레이어가 모두 제어기 중심으로 구성되어 있어서, '
           f'의미 있는 전투 상황이 안정적으로 발생하지 않았습니다. '
           f'그 결과 학습이 제대로 수렴하지 않았기 때문에, 최종 분석 대상에서는 제외했습니다.')
blank()

add_normal('Q2. 실제 플레이어를 상대로도 같은 결과가 나올 수 있나요?')
add_normal('현재 실험에서는 BT 봇을 사용했기 때문에 실제 플레이어와는 차이가 있습니다. '
           '특히 현재 BT 봇은 보스 공격을 인식하고 회피하는 능력이 부족해서 보스 승률이 과대 측정된 측면이 있습니다. '
           '실제 플레이어를 대상으로 적용할 경우에는 보스 HP나 공격 성능을 조정하는 밸런싱 과정이 추가로 필요합니다.')
blank()

add_normal('Q3. 왜 PPO 알고리즘을 사용했나요?')
add_normal('PPO는 학습 안정성이 높고, Unity ML-Agents에서 가장 기본적으로 지원되는 강화학습 알고리즘입니다. '
           '본 연구의 행동 공간은 대기, 전진, 회전, 후퇴처럼 이산 행동으로 구성되어 있기 때문에, '
           'SAC보다 PPO가 더 적합하다고 판단했습니다.')
blank()

add_normal('Q4. 129채널 관측 정보가 너무 많은 것은 아닌가요?')
add_normal('초기 실험에서는 더 적은 관측 채널을 사용했지만, '
           'Phase 2 이후 스킬 관련 정보와 후퇴 행동이 추가되면서 관측 정보가 129채널로 확장되었습니다. '
           '다만 은닉층 구조를 256×3으로 구성했기 때문에, 해당 관측 정보를 처리하는 데에는 문제가 없었습니다.')
blank()

add_normal('Q5. 과학습은 어떻게 방지할 수 있나요?')
add_normal('가장 현실적인 방법은 Early Stopping입니다. '
           '학습 중 승률이나 보상이 일정 시점 이후 하락하는 패턴이 감지되면 자동으로 학습을 중단하는 방식입니다. '
           '추가적으로는 매치업별로 별도 모델을 관리하거나, '
           '평가 지표에 승률뿐 아니라 대기 비율을 함께 반영하는 방식도 고려할 수 있습니다.')
blank()

add_normal('Q6. 포스터에서 Outcome 분석(Fig. 5)이 빠져 있는데, 관련 질문이 나오면?')
add_normal(f'전체 9,134회 평가에서 PlayerWin은 0건이었습니다. '
           f'이는 BT 봇이 보스 공격 회피 능력이 부족하여 승률이 과대 측정된 것입니다. '
           f'또한 Hybrid{X}Hybrid에서 Timeout 비율이 9.5%로 가장 높았으며, '
           f'이는 이중 하락형 과학습과 직접 연결됩니다. '
           f'따라서 WR, Idle Ratio, Timeout Rate 3지표를 병행 분석해야 한다는 것이 저희의 주장입니다.')

out = r'C:\Users\paek6\Desktop\포스터 스크립트.docx'
try:
    doc.save(out)
except PermissionError:
    out = r'C:\Users\paek6\Desktop\포스터 스크립트_v2.docx'
    doc.save(out)
print(f'Done: {out}')
