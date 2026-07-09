# BuildUp 포트폴리오 추출 가이드

## 목적

이 문서는 `BuildUp` 프로젝트 내부 세션에서 포트폴리오에 필요한 내용을 뽑기 위한 기준 문서다.

이 프로젝트는 단순 Unity ML-Agents 테스트가 아니라, 다음 주제로 정리하는 것이 가장 좋다.

```text
2인 협동 보스전의 플레이어 행동과 전투 상태를 관측해 보스 이동 판단을 학습하는 ML-Agents PPO 학습 환경
```

## 포트폴리오에서 잡을 핵심 주제

### 1. 메인 프로젝트 카드

```text
BuildUp ML Training
Unity ML-Agents PPO를 사용해 2인 협동 보스전의 보스 이동 AI를 학습하고, 학습 결과를 ONNX 모델로 실제 Arena Combat 런타임에 연동하기 위한 실험/분석 프로젝트
```

### 2. 케이스스터디 후보

1. ML-Agents 기반 보스 이동 AI 학습 환경 구축
2. 129채널 observation / 5개 discrete action 설계
3. 규칙 기반 플레이어 봇을 이용한 반복 학습 환경 구성
4. matchup별 승률/행동 패턴 분석
5. 학습 결과 ONNX drop-in 구조 설계

## 반드시 확인할 문서

우선 아래 문서를 읽고 내용을 뽑는다.

```text
ML_TRAINING_HANDOFF.md
TRAINING_ANALYSIS.md
FINAL_REPORT.md
GAME_DESIGN.md
BOSS_SKILL_PRIORITY_ANALYSIS.md
PLAYER_CLASSIFICATION_WEIGHTS.md
STATE_MANAGER_DESIGN.md
Assets/ML_TRAINING_SCHEDULE.md
Assets/Scripts/AI/AI_SYSTEM.md
Assets/Scripts/AI/BOSS_CURRICULUM.md
Assets/Scripts/Skill/SKILL_SYSTEM.md
Assets/Scripts/Skill/SKILL_SYSTEM_README.md
results/DATA_MANAGEMENT.md
```

## 반드시 확인할 코드 영역

```text
Assets/Scripts/AI/BossAI/
Assets/Scripts/AI/BossAI/Agents/
Assets/Scripts/AI/BossAI/Observation/
Assets/Scripts/AI/BossAI/Training/
Assets/Scripts/Skill/
Assets/Scripts/State/
results/
*.yaml
```

주요 클래스:

```text
BossInferenceAgent
BossAgent
SpecializedBossAgent
SkillIntroAgent
DualTargetAgent
VsMeleeAgent
BossObservationCollector
PlayerBiasTracker
BossActionWeightCalculator
TrainingSkillManager
SkillTelegraphTable
BossAutoCastHelper
StateManager
SkillManager
```

## 뽑아야 할 내용

### 1. 프로젝트 개요

아래 질문에 답한다.

- 무엇을 학습시키는 프로젝트인가?
- 왜 보스 전체 AI가 아니라 movement만 ML로 학습했는가?
- 스킬 선택은 왜 규칙/SkillManager 쪽에 남겼는가?
- 학습 프로젝트와 실제 게임 프로젝트(ArenaCombat_server)는 어떻게 연결되는가?

포트폴리오용 핵심 문장 예시:

```text
2인 협동 보스전에서 보스의 이동 판단을 ML-Agents PPO로 학습시키기 위해, 플레이어 위치/HP/스킬 상태/행동 편향을 129채널 observation으로 구성하고 5개 discrete action으로 이동 정책을 학습하는 환경을 구축했습니다.
```

### 2. 학습 목표 / 문제 정의

반드시 뽑을 내용:

- 규칙 기반 보스 AI의 한계
- 플레이어가 패턴을 외우면 긴장감이 떨어지는 문제
- 2인 협동 구조에서 플레이어 위치 관계와 행동 편향이 중요하다는 점
- 보스가 어떤 상황에서 접근/후퇴/회전/대기해야 하는지 학습하는 목표

정리 형식:

```text
문제:
규칙 기반 보스 AI는 반복 플레이에서 패턴이 쉽게 읽히고, 2명의 플레이어가 만드는 위치/행동 조합을 유연하게 반영하기 어렵다.

해결:
보스의 이동 판단만 ML-Agents PPO로 학습시키고, 스킬 발동과 전투 규칙은 기존 서버 권위 SkillManager 구조에 남기는 하이브리드 AI 구조를 설계했다.

결과:
학습 모델은 전투 거리, 플레이어 상태, 스킬 슬롯, 행동 편향을 바탕으로 보스의 이동 방향을 선택할 수 있게 되었다.
```

### 3. ML-Agents 설계

반드시 포함:

- PPO 사용
- BossInferenceAgent
- BehaviorParameters
- Action branch `[5]`
- VectorObservationSize `129`
- NumStackedVectorObservations `1`
- ONNX export / drop-in 목표
- production과 training의 spec 일치 필요

### 4. Observation 129채널

`ML_TRAINING_HANDOFF.md`의 observation 구성을 기준으로 뽑는다.

섹션별로 정리:

```text
1. Position relations: 11 channels
2. Boss/player state: 4 channels
3. Boss skill slots: 35 channels
4. Touch flags: 2 channels
5. Player skill slots: 70 channels
6. Extra battle context: 7 channels
합계: 129 channels
```

포트폴리오에서 강조할 점:

```text
단순 위치만 넣은 것이 아니라, 플레이어 스킬 슬롯, 보스 스킬 슬롯, 캐스팅 여부, 이동 속도, 잠금 해제 슬롯 수, 최근 burst damage까지 관측해 실제 전투 판단에 가까운 입력을 설계했다.
```

### 5. Action 5개

반드시 정리:

```text
0 idle
1 forward
2 turn left
3 turn right
4 backward
```

포인트:

- movement만 ML로 학습
- 스킬 선택은 ML action에서 제거
- backward는 forward의 70% 속도
- 갑작스러운 복잡도 증가를 막기 위해 action space를 작게 유지

### 6. Reward 설계 방향

문서와 코드를 보고 아래 항목을 뽑는다.

- boss damage reward
- boss damage taken penalty
- skill range / timing reward
- episode time penalty
- phase transition 관련 설계
- player 처치 / 생존 / timeout 처리

정확한 수치가 불명확하면 `확인 필요`로 표시한다.

### 7. 학습 결과 / 실험 수치

`TRAINING_ANALYSIS.md`에서 반드시 뽑는다.

핵심 수치:

```text
분석 기준: 2026-05-25
대상: 5개 archetype matchup
총 episode: 2,585

Hybrid x CC: 252 episodes, BossWin 168, win rate 66.7%, recent 50ep 68.0%, grade S
Hybrid x Hybrid: 1,464 episodes, BossWin 931, win rate 63.6%, recent 50ep 64.0%, grade A
Ranged x CC: 192 episodes, BossWin 102, win rate 53.1%, recent 50ep 58.0%, grade B
Ranged x Hybrid: 134 episodes, BossWin 63, win rate 47.0%, recent 50ep 54.0%, grade C+
Ranged x Ranged: 543 episodes, BossWin 208, win rate 38.3%, recent 50ep 58.0%, grade B-
```

강조할 인사이트:

- Ranged x Ranged는 초반 22%에서 최근 58%까지 개선
- Hybrid x CC가 가장 안정적인 성능
- Phase 3 진입 후 승률이 크게 떨어짐
- Ranged 계열은 후퇴 비율이 패배와 연결되는 경향
- 스킬 드래프트 수와 승률 사이의 패턴이 있음

### 8. 행동 분석

다음 항목을 뽑는다.

- idle / forward / rotation / backward 비율
- matchup별 평균 이동거리
- win/lose별 행동 차이
- episode 진행에 따른 행동 변화
- 후퇴 비율과 패배 상관
- Phase별 성능 변화

정리 형식:

```text
관찰:

해석:

포트폴리오에서 쓸 문장:

확인 필요:
```

### 9. ONNX / 실제 게임 연동

반드시 뽑을 내용:

- 학습 프로젝트에서 ONNX 모델 생성
- ArenaCombat_server의 BossInferenceAgent에서 추론할 수 있게 spec을 맞춤
- movement는 ML, skill은 production SkillManager
- observation/action size 불일치 시 drop-in 실패
- results 폴더의 모델/로그/설정 파일 관리

## 클로드/코덱스 세션에 넣을 요청 프롬프트

```text
이 프로젝트의 PORTFOLIO_EXTRACTION_GUIDE.md를 기준으로 BuildUp 프로젝트를 개발자 포트폴리오용으로 분석해줘.

목표:
이 프로젝트를 "Unity ML-Agents PPO 기반 보스 이동 AI 학습 환경과 전투 데이터 분석 프로젝트"로 정리하고 싶다.

반드시 확인할 문서:
- ML_TRAINING_HANDOFF.md
- TRAINING_ANALYSIS.md
- FINAL_REPORT.md
- GAME_DESIGN.md
- BOSS_SKILL_PRIORITY_ANALYSIS.md
- PLAYER_CLASSIFICATION_WEIGHTS.md
- Assets/Scripts/AI/AI_SYSTEM.md
- Assets/Scripts/AI/BOSS_CURRICULUM.md

반드시 확인할 코드:
- Assets/Scripts/AI/BossAI/Agents/
- Assets/Scripts/AI/BossAI/Observation/
- Assets/Scripts/AI/BossAI/Training/
- Assets/Scripts/Skill/
- *.yaml
- results/

산출물 형식:

[프로젝트 한 줄 요약]

[포트폴리오용 프로젝트 설명]

[내 역할로 정리 가능한 내용]

[기술 스택]

[학습 환경 구조]

[Observation 129채널 설명]

[Action 5개 설명]

[Reward 설계 방향]

[학습 결과/수치]

[행동 분석 인사이트]

[ONNX -> ArenaCombat_server 연동 흐름]

[문제 해결 사례 5개]
- 문제:
- 원인:
- 해결:
- 결과:
- 관련 파일:

[GitHub README용 요약]

[Notion 포트폴리오 카드용 요약]

[확인 필요 / 과장 위험 문장]

[스크린샷 또는 영상으로 남기면 좋은 장면]
```

## 외부 포트폴리오에 넣을 때의 우선순위

가장 중요:

1. ML-Agents PPO 학습 환경
2. 129채널 observation 설계
3. 5개 discrete action 설계
4. 학습 결과 수치와 분석
5. ONNX 모델을 실제 게임에 연결하는 구조
6. 플레이어 행동/매치업 분석 인사이트

덜 중요:

- 단순 에셋 import
- 포스터 생성 스크립트
- 임시 실험 파일
- 미완성 학습 설정
- 단순 시각화 코드

## 과장 금지

아래는 구현 상태를 확인하지 않고 단정하지 않는다.

- "완성된 상용 AI"
- "사람과 구분 불가능한 보스 AI"
- "모든 매치업에서 높은 성능"
- "실제 유저 데이터로 학습"
- "강화학습이 모든 보스 판단을 담당"

대신 이렇게 쓴다.

```text
보스의 전체 행동을 모두 ML로 처리하지 않고, 이동 판단은 ML-Agents PPO로 학습하고 스킬 발동은 규칙 기반 SkillManager로 분리한 하이브리드 AI 구조를 설계했습니다.
```
