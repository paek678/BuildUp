# [POSTER] Adaptive Boss AI Design and Analysis through Matchup-Specialized Reinforcement Learning

> **A1 (59.4 × 84.1 cm) 2단 컬럼 학술 포스터 — 최종본**
> 파일: `poster_output/BossAI_Poster_A1_2col_v4.docx`
> 생성 스크립트: `gen_poster_A1_2col.py`
> 최종 갱신: 2026-05-29

---

## 포스터 사양

| 항목 | 값 |
|------|-----|
| 용지 | A1 (59.4 × 84.1 cm) |
| 레이아웃 | 2단 컬럼 (각 27.8cm), 간격 0.8cm |
| 여백 | 좌우 1.5cm, 상 2.5cm, 하 1.0cm |
| 본문 폰트 | 11pt (맑은 고딕 / Calibri) |
| 불릿 | 11pt, 캡션 9pt, 테이블 9pt, 소형 10pt |
| 줄간격 | 1.1 |
| 디자인 | 파랑 계열 그라데이션 배너 + 구분선 |

---

## 타이틀 배너 (전체 폭)

```
Adaptive Boss AI Design and Analysis through Matchup-Specialized Reinforcement Learning
매치업별 특화 강화학습을 활용한 보스전 적응 AI 설계 및 분석

백성열    홍채영    곽다영    김지형*
국립금오공과대학교 (Kumoh National Institute of Technology)    *kimjihyung@kumoh.ac.kr
```

- 교신저자: 김지형* (별표는 김지형에만)
- 우측에 금오공과대학교 로고 삽입 (사용자 수동 배치)
- 로고 파일: `poster_output/figures_v10/kumoh_logo_transparent.png` (투명배경)

---

## 왼쪽 컬럼

### 1. Introduction

액션 게임에서 보스 AI가 매번 동일하게 행동할 경우 플레이어의 흥미가 빠르게 감소한다. 기존 보스 AI는 Behavior Tree 등 규칙 기반 방식에 의존하므로 전투 패턴이 고정되기 쉽고, 다양한 플레이어 조합에 유연하게 대응하기 어렵다.

본 연구에서는 강화학습(RL)을 활용하여 보스 AI가 스스로 전투 방법을 학습할 수 있는지 분석한다. 보스에게 5가지 행동(Idle/Forward/Retreat/Turn L/Turn R)을 부여하고, PPO 알고리즘으로 CC×CC를 제외한 9종 매치업, 총 55M steps를 학습시켰다.

핵심 기여: (1) 매치업별 상이한 전투 행동의 자연발생 실증, (2) 과학습 유형 3가지 분류, (3) 승률 단일 지표의 한계 정량적 입증.

**Key Findings Preview:** 같은 승률 82%인 두 매치업에서 대기 비율이 19% vs 2.4%로 완전히 상이. 승률만으로는 학습 품질을 판단할 수 없음.

---

### 2. Research Objectives

- **RQ1.** 9종 매치업별 전투 방식 차이 확인 (→ Fig. 2)
- **RQ2.** 과학습 현상의 유형별 분류 (→ Fig. 3)
- **RQ3.** 승률 단일 지표의 한계 검증 (→ Fig. 4)

---

### 3. Method

**[Fig. 1]** Curriculum pipeline (left) and observation/action space (right).
- 파일: `poster_output/figures_v10/fig01_method.png`

**Experimental Setup:**
- Unity 6 3D 톱다운 액션 게임, 보스 1 vs 플레이어 2(BT 봇)
- PPO, 129채널 관측(HP/거리/스킬 쿨다운 등), 5가지 이산 행동
- Touch(5M)→Engage(10M)→Combat(40M), 총 55M steps
- 매치업당 ~1,000판, 마지막 100판 평균 평가
- 보상 설계: 거리 보상 + 공격 적중 + 승리 보너스의 가중합

**Player Archetypes:**

| Archetype | Role | Range | Key Skills |
|-----------|------|-------|------------|
| Melee | Close-range burst | 5-10m | ExecutionSpike, CrushingBarrage |
| Ranged | Long-range kite | 20-30m | PiercingShot, RuptureMagazine |
| CC | Crowd control | 8-14m | SealChain, CollapseRoar |
| Hybrid | Flexible survivor | 6-30m | SurvivalPulse, OverchargeMode |

4종 아키타입 조합 중 CC×CC는 교착 상태로 제외, 총 9종 매치업 학습.

---

### RQ1: Adaptive Combat Behavior

**[Fig. 2]** (A) Group reward curves. (B) Final action distribution by matchup.
- 파일: `poster_output/figures_v10/fig02_learning.png`

**Key Findings:**
- 9종 매치업 모두 보상이 양(+)으로 수렴.
- Melee 상대 → Forward 위주, Ranged 상대 → Retreat+Rotation 위주. 유형별 이동 전략 차이.
- M×M Idle 19% vs CC/Hybrid 상대 2~3%. 순수 전투형에는 "대기 후 반격" 전략.
- 결론: 상대 조합에 따라 다른 전투 행동 학습 확인.

**Action Distribution:** Melee 조합 Forward 40%+, Ranged 조합 Retreat 30%+Turn 25%. 행동 분포가 명확히 분리됨.

---

## 오른쪽 컬럼

### RQ2: Overfitting Patterns

**[Fig. 3]** Reward/WR trends for 4 representative matchups. Overfitting causes mid-training drops.
- 파일: `poster_output/figures_v10/fig03_overfitting.png`

**Key Findings:**

강화학습에서 과학습(overfitting)이란 과도한 학습으로 인해 오히려 성능이 저하되는 현상이다. 본 실험에서 3가지 유형이 관찰되었다:

- **Type 1 — Sharp Drop (R×R):** 승률 급락 후 일부 회복
- **Type 2 — Double Dip (H×H):** 반복적 성능 하락
- **Type 3 — Gradual Decay (H×R):** 점진적 하락, 탐지 어려움
- **Control — Stable (C×H):** 안정적 학습 완료

**→ 유사 유형 조합(R×R, H×H)에서 overfitting 집중 발생. 상대 행동이 단순할수록 해당 패턴에만 과적합.**

---

### RQ3: Win Rate Is Not Enough

**[Fig. 4]** (A) Idle ratio trends. (B) WR vs Idle scatter (r=-0.23, n.s.).
- 파일: `poster_output/figures_v10/fig04_idle.png`

**Key Findings:**
- M×M, M×H 둘 다 WR 82%이나 Idle 19% vs 2.4%로 정반대.
- WR과 Idle 간 유의미한 상관 없음 (r=-0.23, n.s.).
- 높은 승률이 반드시 적극적 전투를 의미하지 않음.

---

### 4. Discussion

**Q1. 유사 유형 매치업의 overfitting 원인?**
유사 유형 → 단조로운 행동 → 과적합. 반면 C×H처럼 다양한 조합에서는 범용적 전략 학습. BT 봇의 고정된 행동 패턴이 과적합을 가속화.

**Q2. 실제 게임 적용 시?**
BT 봇 회피 불가로 승률 과대 측정. 실제 플레이어 대상 시 보스 HP 하향 및 Early Stopping과 다중 지표 모니터링 병행 필수.

---

### 5. Conclusion

- **Finding 1:** 상대 유형별 상이한 전투 행동 학습 확인
- **Finding 2:** 3가지 overfitting 패턴 발견 (유사 유형 집중)
- **Finding 3:** 같은 WR 82%에서 Idle 19% vs 2.4%

**Future Work:**
- Early stopping 도입으로 overfitting 방지
- 실제 플레이어 대상 밸런스 조정 (보스 HP 하향)
- 스킬 타이밍까지 행동 공간 확장

---

### References

1. I. Millington and J. Funge, "AI for Games," CRC Press, 3rd ed., 2019.
2. O. Vinyals et al., "Grandmaster level in StarCraft II using multi-agent RL," Nature, 575, 2019.
3. C. Berner et al., "Dota 2 with large scale deep RL," arXiv:1912.06680, 2019.
4. J. Schulman et al., "Proximal policy optimization algorithms," arXiv:1707.06347, 2017.
5. A. Pan et al., "The effects of reward misspecification," Proc. ICLR, 2022.
6. A. Juliani et al., "Unity: A general platform for intelligent agents," arXiv:1809.02627, 2020.

---

## 그림/표 목록

| ID | 파일 | 설명 | 위치 |
|----|------|------|------|
| Fig. 1 | fig01_method.png | 커리큘럼 파이프라인 + 관측/행동 공간 | 왼쪽 - Method |
| Fig. 2 | fig02_learning.png | 그룹별 보상 곡선 + 매치업별 행동 분포 | 왼쪽 - RQ1 |
| Fig. 3 | fig03_overfitting.png | 4개 대표 매치업 보상/승률 추이 | 오른쪽 - RQ2 |
| Fig. 4 | fig04_idle.png | Idle 비율 추이 + WR vs Idle 산점도 | 오른쪽 - RQ3 |
| 표 1 | (스크립트 생성) | Player Archetypes (4종) | 왼쪽 - Method |

## 배너 파일 (자동 생성)

모든 배너는 `poster_output/banners_A1/` 에 생성:
- `title_banner_2col.png` — 타이틀 (전체 폭)
- `sec2_intro.png` — 1. Introduction
- `sec2_rq.png` — 2. Research Objectives
- `sec2_method.png` — 3. Method
- `sec2_rq1.png` — RQ1: Adaptive Combat Behavior
- `sec2_rq2.png` — RQ2: Overfitting Patterns
- `sec2_rq3.png` — RQ3: Win Rate Is Not Enough
- `sec2_disc.png` — 4. Discussion
- `sec2_conc.png` — 5. Conclusion
- `sec2_ref.png` — References

## 로고 파일

| 파일 | 용도 |
|------|------|
| `poster_output/figures_v10/kumoh_logo_official.png` | 원본 (배경 있음) |
| `poster_output/figures_v10/kumoh_logo_transparent.png` | 누끼 (투명배경) |
| `poster_output/figures_v10/kumoh_logo_white.png` | 흰색 (배너 위 배치용) |

---

## 이전 버전 대비 변경점

| 항목 | POSTER_A4x6.md (이전) | 본 문서 (최종) |
|------|----------------------|---------------|
| 용지 | A4 × 6 패널 | A1 단일 |
| 레이아웃 | 6패널 개별 | 2단 컬럼 |
| 매치업 수 | 5종 (Hybrid/Ranged 조합) | 9종 (CC×CC 제외 전체) |
| 관측 공간 | 55ch → 129ch 혼재 | 129ch 통일 |
| 학습 단계 | 2단계 전이학습 | 3단계 커리큘럼 (Touch→Engage→Combat, 55M) |
| 핵심 분석 | 승률/DPS/Phase별 | 행동 분포 + 과학습 유형 + 승률 한계 |
| 저자 표기 | 홍채영*, 곽다영*, 백성열*, 김지형** | 백성열 홍채영 곽다영 김지형* |
| 소속 | 금오공과대학교 컴퓨터공학과 | 국립금오공과대학교 |
