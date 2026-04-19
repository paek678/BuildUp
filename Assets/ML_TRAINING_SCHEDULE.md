# 보스 AI 강화학습 분화 스케줄

> 기준: Unity ML-Agents 4.0.2 / PPO → MA-POCA
> 각 Phase는 이전 Phase의 .onnx를 init_path로 이어받아 학습

---

## Phase 개요

| Phase | 이름 | 알고리즘 | Space Size | Action Branches | 대응 보스 AI 분류 | 상태 |
|-------|------|----------|------------|-----------------|-------------------|------|
| 1 | BasicMove | PPO | 6 | B0: 이동 4 | — | ✅ 완료 |
| 2 | DualTarget | PPO | 11 | B0: 이동 4 | 7 분산 / 8 밀집 | ⬜ 대기 |
| 3 | SkillIntro | PPO | 17 | B0: 이동 4 / B1: 스킬 5 | 1 근접 / 2 원거리 / 7 / 8 | ⬜ 대기 |
| 4 | ReactiveSkill | PPO | 21 | B0: 이동 4 / B1: 스킬 8 | 3 패링 / 5 폭딜 / 6 생존 압박 | ⬜ 대기 |
| 5 | AdaptivePattern | PPO | 30 | B0: 이동 4 / B1: 스킬 8 | 9 적응형 변칙 | ⬜ 대기 |
| 6 | MA-POCA | MA-POCA | 30 | B0: 이동 4 / B1: 스킬 8 | 1 ~ 9 전체 | ⬜ 대기 |

---

## Phase 1 — BasicMove `✅ 완료`

### 목표
단일 플레이어 추적 + 벽 회피 기초 이동 학습

### 관측값 (Space Size: 6)
| # | 관측값 | 설명 |
|---|--------|------|
| 0 | dirToP1.x | P1 방향 X (정규화) |
| 1 | dirToP1.z | P1 방향 Z (정규화) |
| 2 | distToP1 | P1까지 거리 (정규화) |
| 3 | forward.x | 보스 전방 X |
| 4 | forward.z | 보스 전방 Z |
| 5 | dotForwardP1 | 전방↔P1 방향 정렬도 |

### 행동 (Branch 0)
| 값 | 행동 |
|----|------|
| 0 | 대기 |
| 1 | 전진 |
| 2 | 좌회전 |
| 3 | 우회전 |

### 보상
| 조건 | 보상 |
|------|------|
| P1 접촉 | +1.0 |
| 벽 충돌 (Enter) | -0.05 |
| 벽 접촉 유지 (Stay) | -0.01 × fixedDeltaTime |
| 매 스텝 | -0.001 |
| P1 근접 (거리 비례) | +0.005 × (1 - dist/maxDist) |

---

## Phase 2 — DualTarget `⬜ 대기`

### 목표
2인 플레이어 동시 인식 — 분산/밀집 상황 판단

### 추가 관측값 (+5, Space Size: 11)
| # | 관측값 | 설명 |
|---|--------|------|
| 6 | dirToP2.x | P2 방향 X |
| 7 | dirToP2.z | P2 방향 Z |
| 8 | distToP2 | P2까지 거리 |
| 9 | distP1P2 | P1↔P2 사이 거리 |
| 10 | dotForwardP2 | 전방↔P2 방향 정렬도 |

### 추가 보상
| 조건 | 보상 |
|------|------|
| P1·P2 동시 접촉 | +0.3 추가 |
| P1↔P2 멀 때 양쪽 모두 접근 유지 | +0.005/스텝 |

### 설정
```yaml
init_path: results/BasicMove2/BasicMove/BasicMove.onnx
max_steps: 500000
```

---

## Phase 3 — SkillIntro `⬜ 대기`

### 목표
거리/상황에 따른 스킬 종류 선택 학습

### 추가 관측값 (+6, Space Size: 17)
| # | 관측값 | 설명 |
|---|--------|------|
| 11 | bossHpRatio | 보스 HP 비율 |
| 12 | p1HpRatio | P1 HP 비율 |
| 13 | p2HpRatio | P2 HP 비율 |
| 14 | skill0Cooldown | 근접 스킬 쿨다운 |
| 15 | skill1Cooldown | 원거리 스킬 쿨다운 |
| 16 | skill2Cooldown | 장판 스킬 쿨다운 |

### 추가 행동 (Branch 1)
| 값 | 행동 | 대응 스킬 |
|----|------|-----------|
| 0 | 스킬 없음 | — |
| 1 | 근접 광역 | 붕괴 포효 |
| 2 | 원거리 단발 | 방벽 파쇄 |
| 3 | 장판 생성 | 침식 장판 |
| 4 | 다방향 투사체 | 파열 탄창 |

### 추가 보상
| 조건 | 보상 |
|------|------|
| 거리 적합 스킬 명중 | +0.15 |
| 사거리 밖 스킬 낭비 | -0.05 |
| 광역기로 2명 동시 명중 | +0.25 |

### 설정
```yaml
init_path: results/DualTarget/BasicMove/BasicMove.onnx
max_steps: 700000
```

---

## Phase 4 — ReactiveSkill `⬜ 대기`

### 목표
플레이어 행동 패턴 감지 후 카운터 스킬 선택

### 추가 관측값 (+4, Space Size: 21)
| # | 관측값 | 설명 |
|---|--------|------|
| 17 | recentParryCount | 최근 5초 패링 횟수 (정규화) |
| 18 | recentBurstDamage | 최근 1초 수신 피해량 (정규화) |
| 19 | p1AvgMoveSpeed | P1 평균 이동속도 |
| 20 | p2AvgMoveSpeed | P2 평균 이동속도 |

### Branch 1 확장 (+3종)
| 값 | 행동 | 대응 스킬 | 용도 |
|----|------|-----------|------|
| 5 | 카운터 패턴 | 봉쇄 사슬 | 패링 빈도 높을 때 |
| 6 | 무적 발동 | 거울 반격 | 폭딜 수신 시 |
| 7 | 생존 회복 | 생존 맥동 | HP 위기 시 |

### 추가 보상
| 조건 | 보상 |
|------|------|
| 패링 실패 유도 성공 | +0.15 |
| 무적 발동 후 생존 | +0.10 |
| 장판 위 플레이어 체류 피해 | +0.05 |
| 방어적 플레이어 이동 강제 | +0.10 |

### 설정
```yaml
init_path: results/SkillIntro/BasicMove/BasicMove.onnx
max_steps: 700000
```

---

## Phase 5 — AdaptivePattern `⬜ 대기`

### 목표
패턴 반복 회피 — 같은 스킬 연속 사용 시 자동 전환 학습

### 추가 관측값 (+9, Space Size: 30)
| # | 관측값 | 설명 |
|---|--------|------|
| 21~23 | lastSkill[0~2] | 직전 3회 사용 스킬 one-hot |
| 24~26 | skillHitRate[0~2] | 스킬별 최근 명중률 |
| 27~29 | skillUseCount[0~2] | 스킬별 누적 사용 비율 |

### 추가 보상
| 조건 | 보상 |
|------|------|
| 동일 스킬 3회 연속 사용 | -0.02 |
| 오래 미사용 스킬 전환 | +0.05 |
| 명중률 낮은 스킬 교체 | +0.03 |

### 설정
```yaml
init_path: results/ReactiveSkill/BasicMove/BasicMove.onnx
max_steps: 1000000
```

---

## Phase 6 — MA-POCA `⬜ 대기`

### 목표
실제 플레이어 에이전트(2인)와 대전 학습 — 전체 보스 AI 분류 통합

### 전제 조건
- 플레이어 에이전트 별도 학습 완료 (PlayerAgent Phase 1~3)
- trainer_type을 `poca`로 변경

### 설정 변경
```yaml
trainer_type: poca
init_path: results/AdaptivePattern/BasicMove/BasicMove.onnx
max_steps: 2000000
self_play: null  # 보스는 self_play 미사용, 플레이어 에이전트와 대전
```

### 보스 AI 분류 전체 활성
| 분류 | 감지 조건 |
|------|-----------|
| 1 근접 압박형 | P1 or P2 거리 < 3m |
| 2 원거리 견제형 | P1 and P2 거리 > 7m |
| 3 패링 견제형 | 최근 패링 횟수 > 2 |
| 4 로프 대응형 | 로프 사용 횟수 > 1 |
| 5 폭딜 대응형 | 최근 1초 피해 > 임계값 |
| 6 생존 압박형 | 플레이어 이동속도 < 임계값 |
| 7 분산 대응형 | P1↔P2 거리 > 8m |
| 8 밀집 대응형 | P1↔P2 거리 < 3m |
| 9 적응형 변칙형 | 동일 패턴 반복 감지 |

---

## 전체 흐름

```
[Phase 1] BasicMove          ✅ 완료
     ↓ init_path
[Phase 2] DualTarget         ⬜ 다음
     ↓ init_path
[Phase 3] SkillIntro         ⬜
     ↓ init_path
[Phase 4] ReactiveSkill      ⬜
     ↓ init_path
[Phase 5] AdaptivePattern    ⬜
     ↓ init_path
[Phase 6] MA-POCA            ⬜ 최종
```

> 각 Phase 완료 기준: TensorBoard에서 Mean Reward 수렴 + 목표 행동 육안 확인
