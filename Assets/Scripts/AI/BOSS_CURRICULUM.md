# Boss AI 분화 학습 커리큘럼 (Tenebris)

보스 ML-Agents 학습을 **점진적 관측값/행동/보상 확장** 방식으로 진행.
각 Phase는 **이전 Phase의 학습 모델을 `--initialize-from` 으로 이어서** 추가 학습한다.

> 관측 Space 가 Phase 마다 커지므로, 모델 재사용 시 네트워크 입력 레이어 호환성이 문제가 될 수 있다.
> 대응: **Phase N용 Agent는 Phase N의 고정 관측 크기**로 선언한 뒤, ML-Agents CLI의 `--initialize-from=<prev_run>` 로
> 호환 가능한 공통 레이어(특히 hidden layer) 가중치만 상속받는다. 입력/출력 크기가 달라지면 해당 레이어는 재초기화된다.

---

## Phase 분화 순서

| 순서 | 이름             | 알고리즘  | Observation | Action                      | 보스 AI 분류              | 상태 |
|------|------------------|-----------|-------------|-----------------------------|---------------------------|------|
| 1    | BasicMove        | PPO       | 6           | B0: 이동 4                  | —                         | 완료 |
| 2    | DualTarget       | PPO       | 11          | B0: 이동 4                  | 7 분산 / 8 밀집           | 대기 |
| 3    | SkillIntro       | PPO       | 17          | B0: 이동 4 / B1: 스킬 5     | 1 근접 / 2 원거리 / 7 / 8 | 대기 |
| 4    | ReactiveSkill    | PPO       | 21          | B0: 이동 4 / B1: 스킬 8     | 3 패링 / 5 폭딜 / 6 생존  | 대기 |
| 5    | AdaptivePattern  | PPO       | 30          | B0: 이동 4 / B1: 스킬 8     | 9 적응형 변칙             | 대기 |
| 6    | 2인 자동 대전     | MA-POCA   | 30          | B0: 이동 4 / B1: 스킬 8     | 1~9 전체                  | 대기 |

---

## 전체 관측값 매핑 (누적)

| Phase | Index   | 관측값                | 설명                            | 비고         |
|-------|---------|-----------------------|---------------------------------|--------------|
| 1     | 0~1     | dirToP1.x/z           | P1 방향 (정규화)                |              |
| 1     | 2       | distToP1              | P1 거리 (정규화)                |              |
| 1     | 3~4     | forward.x/z           | 보스 전방                       |              |
| 1     | 5       | dotForwardP1          | 전방↔P1 정렬도                  |              |
| 2     | 6~7     | dirToP2.x/z           | P2 방향                         |              |
| 2     | 8       | distToP2              | P2 거리                         |              |
| 2     | 9       | distP1P2              | P1↔P2 거리                      |              |
| 2     | 10      | dotForwardP2          | 전방↔P2 정렬도                  |              |
| 3     | 11~13   | bossHp / p1Hp / p2Hp  | HP 비율 3종                     |              |
| 3     | 14~16   | skill0~2Cooldown      | 스킬 쿨다운 3종                 |              |
| 3     | 17      | bossPhase             | 보스 페이즈 (0/1/2 정규화)      | **신규**     |
| 4     | 18      | recentParryCount      | 최근 5초 패링 횟수              | 기존#17→#18  |
| 4     | 19      | recentBurstDamage     | 최근 1초 수신 피해량            | 기존#18→#19  |
| 4     | 20~21   | p1/p2AvgMoveSpeed     | P1·P2 평균 이동속도             | 기존#19~20→#20~21 |
| 4     | 22      | p1IsCasting           | P1 스킬 시전 중 여부 (0/1)      | **신규**     |
| 4     | 23      | p2IsCasting           | P2 스킬 시전 중 여부 (0/1)      | **신규**     |
| 5     | 24~26   | lastSkill[0~2]        | 직전 3회 스킬 (정규화)          | 기존#21~23→#24~26 |
| 5     | 27~29   | skillHitRate[0~2]     | 스킬별 명중률                   | 기존#24~26→#27~29 |
| 5     | 30~32   | skillUseCount[0~2]    | 스킬별 사용 비율                | 기존#27~29→#30~32 |

---

## 전체 보상 매핑 (누적)

| Phase | 조건                             | 보상                    | 비고                       |
|-------|----------------------------------|-------------------------|----------------------------|
| 1     | P1 접촉                          | +1.0                    |                            |
| 1     | 벽 충돌 Enter                    | -0.05                   |                            |
| 1     | 벽 접촉 Stay                     | -0.01 × fixedDt         |                            |
| 1     | 매 스텝                          | -0.001                  |                            |
| 1     | P1 근접 (거리 비례)              | 0.005 × (1 - distP1/max)|                            |
| 1     | P1 방향 정렬 (dot > 0.8)         | +0.002                  | **신규**                   |
| 2     | P1·P2 동시 접촉                  | +1.5                    | 수식 복구 + 상향           |
| 2     | 양쪽 모두 접근 유지              | 0.005 × (closeP1+closeP2)/2 | 수식 복구              |
| 2     | 타겟 전환 시                     | +0.08                   | **신규**                   |
| 3     | 거리 적합 스킬 명중              | +0.15                   |                            |
| 3     | 사거리 밖 스킬 낭비              | -0.05                   |                            |
| 3     | 광역기 2명 동시 명중             | +0.25                   |                            |
| 3     | 쿨타임 만료 후 3초 이상 미사용   | -0.02                   | **신규**                   |
| 4     | 패링 실패 유도 성공              | +0.15                   | 판정 기준 명확화           |
| 4     | 무적 발동 후 생존                | +0.1                    |                            |
| 4     | 장판 위 체류 피해 누적           | +0.05                   |                            |
| 4     | 방어적 플레이어 이동 강제        | +0.1                    |                            |
| 4     | 캐스팅 중 적중 (침묵/경직)       | +0.12                   | **신규**                   |
| 5     | 동일 스킬 3회 연속               | -0.05                   | 상향 (-0.02→-0.05)         |
| 5     | 미사용 스킬 전환                 | +0.05                   |                            |
| 5     | 명중률 낮은 스킬 교체            | +0.03                   |                            |
| 5     | 플레이어 킬 (HP→0)               | +2.0                    | **신규**                   |

---

## Phase 1 — BasicMove (완료)

### 관측 6개
| # | 관측값 | 설명 |
|---|--------|------|
| 0~1 | dirToP1.x/z | P1 방향 정규화 |
| 2 | distToP1 | P1 거리 정규화 |
| 3~4 | forward.x/z | 보스 전방 |
| 5 | dotForwardP1 | 전방↔P1 정렬도 |

### 행동 4개 (Discrete B0)
0: 대기 / 1: 전진 / 2: 좌회전 / 3: 우회전

### 보상
- P1 접촉: +1.0 → EndEpisode
- 벽 Enter: -0.05, 벽 Stay: -0.01×fixedDt
- 매 스텝: -0.001
- 근접 보상: 0.005 × (1 - distP1/max)

**산출물:** `Assets/Scripts/AI/BossAI/BasicMove.onnx`

---

## Phase 2 — DualTarget (이번 학습)

### 목적
두 명의 플레이어 좌표를 **동시에** 관측하고, 두 플레이어 모두를 단시간 내에 접촉하는 "밀집 유도" 혹은 "연속 타격" 전략을 학습.
보스 AI 분류 7(분산) / 8(밀집) 의 기반.

### 이어서 학습 (Transfer)
```bash
mlagents-learn DualTarget_config.yaml \
  --initialize-from=BasicMove_run_id \
  --run-id=DualTarget_001
```

### 관측 11개
Phase 1의 0~5 유지 + P2 관련 5개 추가.

| # | 관측값 | 설명 |
|---|--------|------|
| 0~1 | dirToP1.x/z | P1 방향 |
| 2 | distToP1 | P1 거리 |
| 3~4 | forward.x/z | 보스 전방 |
| 5 | dotForwardP1 | 전방↔P1 |
| 6~7 | dirToP2.x/z | P2 방향 |
| 8 | distToP2 | P2 거리 |
| 9 | distP1P2 | P1↔P2 거리 |
| 10 | dotForwardP2 | 전방↔P2 |

### 행동 (Phase 1 유지)
B0: 이동 4 (0 대기 / 1 전진 / 2 좌 / 3 우)

### 보상
| 조건 | 값 | 비고 |
|------|-----|-----|
| 매 스텝 | -0.001 | Phase1 |
| 벽 Enter / Stay | -0.05 / -0.01×fixedDt | Phase1 |
| 양쪽 접근 유지 | 0.005 × (closeP1+closeP2)/2 | Phase2 |
| dot > 0.8 정렬 (any) | +0.002 | Phase1 신규 |
| 타겟 전환 (dominant 변경) | +0.08 | Phase2 신규 |
| P1 or P2 단일 접촉 | +0.5 | |
| 양쪽 2초 내 연속 접촉 | +0.5 추가 (총 1.5) | Phase2 목표 |
| 양쪽 접촉 완료 | EndEpisode | |

### BehaviorParameters
- Behavior Name: `DualTarget`
- Vector Observation Size: **11**
- Discrete Branches: 1, Branch 0 Size: **4**

### 산출물
`Assets/Scripts/AI/BossAI/DualTargetAgent.cs`

---

## Phase 3 — SkillIntro (예정)

### 신규 관측 (6개 추가 → 총 17)
`bossHp / p1Hp / p2Hp / skill0~2Cooldown / bossPhase`

### 행동 확장
B1: 스킬 5 (미사용 / 스킬0 / 스킬1 / 스킬2 / 광역기) 등

### 보상 주안점
- 거리 적합 스킬 명중: +0.15
- 사거리 밖 스킬 낭비: -0.05
- 광역기 2명 동시 명중: +0.25
- 쿨 만료 후 3초+ 미사용: -0.02

### 대응 보스 분류
1 근접 / 2 원거리 / 7 분산 / 8 밀집

---

## Phase 4 — ReactiveSkill (예정)

### 신규 관측 (4개 추가 → 총 21)
`recentParryCount / recentBurstDamage / p1p2AvgMoveSpeed / p1IsCasting / p2IsCasting`

### 행동
B1: 스킬 8 (방어/무적/장판 등 반응형 스킬 포함)

### 보상 주안점
- 패링 실패 유도 성공: +0.15
- 무적 발동 후 생존: +0.1
- 장판 위 체류 피해 누적: +0.05
- 방어적 플레이어 이동 강제: +0.1
- 캐스팅 중 적중 (침묵/경직): +0.12

### 대응 보스 분류
3 패링 / 5 폭딜 / 6 생존

---

## Phase 5 — AdaptivePattern (예정)

### 신규 관측 (9개 추가 → 총 30)
`lastSkill[0~2] / skillHitRate[0~2] / skillUseCount[0~2]`

### 보상 주안점
- 동일 스킬 3연속: -0.05
- 미사용 스킬 전환: +0.05
- 명중률 낮은 스킬 교체: +0.03
- 플레이어 킬: +2.0

### 대응 보스 분류
9 적응형 변칙

---

## Phase 6 — 2인 자동 대전 (MA-POCA)

Phase 5의 관측/행동 공간을 그대로 사용하되 알고리즘을 **MA-POCA**(멀티 에이전트)로 전환.
플레이어 2명과 보스 1명을 동시에 학습시켜 완전 자동 대전을 가능하게 한다.

### 대응 보스 분류
1~9 전체

---

## 공통 설계 원칙

1. **관측 정규화:** 거리는 `Clamp01(d / _maxDistance)` 으로, 방향은 `.normalized` 로 통일.
2. **보스 좌표는 LocalSpace 기준:** 병렬 학습 환경 복제 시 월드 위치가 달라도 일관되게 동작.
3. **보상 스케일:** 누적 reward 한 에피소드 기준 [-2, +2.5] 내로 유지 → PPO value function 안정.
4. **에피소드 종료 조건 (Phase 별):**
   - Phase 1: P1 접촉
   - Phase 2: P1·P2 양쪽 접촉
   - Phase 3+: 보스 HP 0 / 플레이어 전원 HP 0 / 타임아웃
5. **MaxStep:** 기본 5000, 스킬 포함 Phase 에서는 8000 권장.
6. **Behavior Parameters:** 각 Phase 마다 Behavior Name 을 다르게 지정하면 tensorboard/onnx 가 분리됨.

---

## 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-04-11 | BasicMove (Phase 1) 완료, BasicMove.onnx 산출 |
| 2026-04-12 | DualTarget (Phase 2) Agent 스크립트 작성, 커리큘럼 문서 초안 |
