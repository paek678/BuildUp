# Player Classification Weights

Two systems classify player behavior at runtime: **PlayerArchetypeClassifier** (broad archetype) and **PlayerBiasTracker** (granular bias vector). Both feed into the boss adaptive AI pipeline.

---

## 0. Revision Log (2026-05-27)

BT 봇 실제 교전 거리 및 학습 데이터 9,134판 대조 검증 후 수정.

**발견된 문제:**
1. Melee 임계값 5m이 BT Melee봇 교전거리(5-10m)보다 낮아 Melee가 Melee로 분류되지 않음
2. 5-10m 구간이 Melee도 Ranged도 아닌 사각지대 → CC/Hybrid 봇 분류 불안정
3. Ranged 봇이 SealChain(CC태그)으로 CC점수 획득 → Ranged↔CC 혼동
4. CC 봇이 ErosionField/RuptureMag(range>8)으로 Ranged점수 획득 → CC↔Ranged 혼동
5. "Melee hit ≥ 5m → Ranged +0.5" — 6m에서 근접공격하는 건 Ranged가 아님
6. Decay ×0.3이 너무 공격적 → 짧은 위치 변화에 분류가 흔들림

---

## 1. PlayerArchetypeClassifier

**Eval interval:** 180 seconds  
**Decay per eval:** ×0.5 *(변경: 0.3 → 0.5, 분류 안정성 확보)*  
**Minimum total weight:** 5.0 (below this → Hybrid)

### 1.1 Weight Buckets

Three accumulator buckets: **Melee [0]**, **Ranged [1]**, **CC [2]**

| Event | Condition | Bucket | Weight | 변경사항 |
|-------|-----------|--------|--------|----------|
| Melee hit landed | Distance < **12m** | Melee | +1.0 | ✏️ 5m → 12m (Melee봇 OptimalMax=10에 여유) |
| Melee hit landed | Distance **12~20m** | Melee | +0.3 | ✏️ 신규 (중거리 근접공격 = 약한 Melee 신호) |
| Melee hit landed | Distance **> 20m** | Ranged | +0.5 | ✏️ ≥5m → >20m (진짜 원거리에서만 Ranged) |
| Skill cast | CC or Silence tagged | CC | +1.5 | 유지 |
| Skill cast | CC태그 AND range > 8f | CC | +1.5 *(Ranged 미적용)* | ✏️ 신규 — CC스킬은 사거리 무관 CC로만 |
| Skill cast | Range > **15f** AND CC태그 아님 | Ranged | +1.0 | ✏️ 8f → 15f (CC중거리 스킬 제외) |
| Skill cast | Range 8~15f AND CC태그 아님, dist > 10m | Ranged | +0.5 | ✏️ 신규 — 중거리 DPS를 약한 Ranged 신호로 |
| Skill cast | Distance < **12m** (non-CC) | Melee | +1.0 | ✏️ 5m → 12m |
| Parry success | — | Melee | +**1.5** | ✏️ 2.0 → 1.5 (단일 이벤트 스파이크 완화) |
| Passive distance sample (every 0.5s) | Distance < **12m** | Melee | +0.05 | ✏️ 5m → 12m |
| Passive distance sample (every 0.5s) | Distance **12~20m** | *(없음)* | 0 | 사각지대 해소: 중립 구간 |
| Passive distance sample (every 0.5s) | Distance > **20m** | Ranged | +0.05 | ✏️ 10m → 20m |
| Slot CC bonus (recomputed each eval) | Per CC/Silence tagged skill in loadout | CC | +**0.8** each | ✏️ 0.5 → 0.8 (CC 분류력 강화) |

### 1.2 Classification Thresholds

After accumulating weights over 180s, the system normalizes and classifies:

```
total = Melee + Ranged + CC + slotCCBonus
ratio[i] = bucket[i] / total

dominant    = max(ratio[0], ratio[1], ratio[2])
secondary   = second highest ratio
```

| Condition | Result | 변경사항 |
|-----------|--------|----------|
| total < 5.0 | **Hybrid** (insufficient data) | 유지 |
| dominant ≥ **0.50** | Assign dominant archetype | ✏️ 0.55 → 0.50 |
| dominant ≥ **0.40** AND secondary < 0.30 | Assign dominant archetype (semi-dominant) | ✏️ 0.45 → 0.40 |
| Otherwise | **Hybrid** | 유지 |

### 1.3 Archetype Enum

| Value | Name | Meaning |
|-------|------|---------|
| 0 | Hybrid | No clear specialization |
| 1 | Melee | Close-range focused |
| 2 | Ranged | Long-range focused |
| 3 | CC | Crowd-control focused |

### 1.4 Log Output

```
[Archetype] client={id} M={melee:F1} R={ranged:F1} C={cc:F1} (slotCC={bonus:F1}, total={sum:F1}) → {type}
```

---

## 2. PlayerBiasTracker

**Eval interval:** 0.5 seconds (코드 기준, 문서 5s → 실제 0.5s)  
**Log window:** 18 seconds  
**Team distance sampling:** every 0.5s (코루틴)

### 2.1 Bias Indices (9 dimensions)

| Index | Name | 코드 변수 | 실제 계산 방식 (코드 기준) | Range |
|-------|------|-----------|--------------------------|-------|
| 0 | MeleePrefer | meleeRatio | avgDist(P1,P2→Boss) < **12m** 비율 | 0–1 |
| 1 | RangeKeep | rangedRatio | avgDist(P1,P2→Boss) > **25m** 비율 | 0–1 |
| 2 | AttackFocus | attackRatio | attackCount / totalActions | 0–1 |
| 3 | SurvivalFirst | evadeRatio | evadeCount / totalActions | 0–1 |
| 4 | ParryDepend | — | 미구현, naturalDecay(-0.01)로 0 수렴 | 0–1 |
| 5 | RopeManeuver | — | 미구현, naturalDecay(-0.01)로 0 수렴 | 0–1 |
| 6 | SkillCentric | skillRatio | skillCount / totalActions | 0–1 |
| 7 | TeamCluster | closeTeamRatio | P1↔P2 거리 < **10m** 비율 | 0–1 |
| 8 | TeamSpread | farTeamRatio | P1↔P2 거리 > **25m** 비율 | 0–1 |

### 2.2 BiasTracker 코드 vs 문서 불일치 (검증 결과)

| 항목 | 문서 (기존) | 코드 (실제) | 상태 |
|------|------------|------------|------|
| Eval interval | 5초 | **0.5초** (_updateInterval) | ⚠️ 불일치 |
| Counter reset | 매 eval 후 리셋 | **리셋 안 함** (18s 윈도우 큐) | ⚠️ 불일치 |
| Distance sampling | FixedUpdate | **0.5s 코루틴** | ⚠️ 불일치 |
| Melee 기준 거리 | 문서 없음 | **12m** (_meleeThreshold) | 문서 누락 |
| Ranged 기준 거리 | 문서 없음 | **25m** (_rangedThreshold) | 문서 누락 |
| Rise/Fall 방식 | ratio 직접 대입 | **Delta 기반** (±0.02~0.05) | ⚠️ 불일치 |

### 2.3 BiasTracker 임계값 검증

**현재 코드 임계값:**
- `_meleeThreshold = 12m` — avgDist < 12m → MeleePrefer 상승
- `_rangedThreshold = 25m` — avgDist > 25m → RangeKeep 상승

**BT 봇 예상 avgDist:**
| 매치업 | P1 거리 | P2 거리 | avgDist | MeleePrefer | RangeKeep |
|--------|---------|---------|---------|-------------|-----------|
| M×M | 5-10m | 5-10m | 5-10m | ✅ < 12m 충족 | ✗ |
| M×R | 5-10m | 20-30m | 12.5-20m | ⚠️ 경계~미달 | ✗ |
| M×CC | 5-10m | 8-14m | 6.5-12m | ✅ < 12m 가끔 충족 | ✗ |
| R×R | 20-30m | 20-30m | 20-30m | ✗ | ✅ > 25m 가끔 충족 |
| R×CC | 20-30m | 8-14m | 14-22m | ✗ | ✗ 사각지대 |
| CC×H | 8-14m | 6-30m | 7-22m | ⚠️ 가끔 충족 | ✗ |
| H×H | 6-30m | 6-30m | 6-30m | 가변 | 가변 |

**⚠️ 문제:** R×CC (avgDist 14-22m)는 MeleePrefer도 RangeKeep도 안 올라가는 사각지대.

### 2.4 BiasTracker 수정 권장

| 항목 | 현재 | 권장 | 이유 |
|------|------|------|------|
| `_meleeThreshold` | 12m | **15m** | CC봇(8-14m) 포함, M×CC avgDist(~12m) 커버 |
| `_rangedThreshold` | 25m | **20m** | R×CC avgDist(14-22m) 사각지대 해소 |
| `_teamCloseThreshold` | 10m | 10m (유지) | 적절 |
| `_teamFarThreshold` | 25m | **20m** | Ranged+CC 분산 감지 개선 |

### 2.5 Log Output

```
[Bias] client={id} M={[0]:F2} R={[1]:F2} AF={[2]:F2} S={[3]:F2} P={[4]:F2} Rp={[5]:F2} SF={[6]:F2} TC={[7]:F2} TS={[8]:F2}
```

---

## 3. How Classification Feeds Into Boss AI

### 3.1 Archetype → Boss Variant Selection (BossAdaptiveWeights)

`PlayerArchetypeClassifier` outputs are used by `BossAIPoolManager` to select the boss ONNX model variant. Two player archetypes form a **normalized pair** (smaller enum value first), mapped to one of 10 pair indices:

| Pair | Index | ONNX variant |
|------|-------|-------------|
| Hybrid + Hybrid | 0 | H×H |
| Hybrid + Melee | 1 | M×H |
| Hybrid + Ranged | 2 | R×H |
| Hybrid + CC | 3 | CC×H |
| Melee + Melee | 4 | M×M |
| Melee + Ranged | 5 | M×R |
| Melee + CC | 6 | M×CC |
| Ranged + Ranged | 7 | R×R |
| Ranged + CC | 8 | R×CC |
| CC + CC | 9 | CC×CC (fallback to H×H) |

**Pair index formula:** `lo × 4 − lo × (lo − 1) / 2 + (hi − lo)`

### 3.2 Archetype → Boss Draft Skill Selection (BossDraftManager)

`BossDraftManager` uses the same pair index to look up **matchup weights** from `BossDraftWeightTable`. Each boss skill has a weight for each of the 10 pair combinations.

**Scoring formula:**
```
score = matchupWeight[pairIndex] × phaseMultiplier + reactiveBonus
```

### 3.3 Biases → Reactive Bonus (BossDraftManager)

`PlayerBiasTracker` biases are checked by `BossDraftManager.EvaluateCondition()` for reactive draft bonuses:

| Reactive Condition | Bias Check | 검증 결과 |
|-------------------|------------|-----------|
| SurvivalBiasModerate | biases[3] > 0.15 | ⚠️ BT봇은 회피(Evade) 없음 → biases[3] 항상 0 수렴, **절대 트리거 안 됨** |
| SurvivalBiasHigh | biases[3] > 0.20 | ⚠️ 위와 동일, **사실상 사문 조건** |
| AggressionBiasHigh | biases[2] > 0.50 | ✅ attack+skill 이벤트로 작동 가능 |
| PlayersCloseProximity | biases[7] > 0.50 | ✅ M×M(5-10m 간격) 시 트리거 가능 |

**수정 권장:**
- SurvivalBias → 실제 플레이어 대상에서만 유효. BT 봇에서는 트리거 불가하므로, **회피 외 생존 행동도 카운트하도록 확장 필요:** 생존스킬(SurvivalPulse, FortressArmor 등) 사용 시에도 biases[3] 상승시켜야 함
- AggressionBiasHigh 0.50 → Delta 방식(0.02/0.05 증감)에서 0.50 도달이 어려움. **0.35로 하향 권장**
- PlayersCloseProximity 0.50 → M×M에서도 P1↔P2 간격이 10m 미만인 경우가 반반. **0.40으로 하향 권장**

Other conditions (BossSilenced, BossStaggered, PlayerLowHP, BossLowHP) check entity status directly rather than biases.

### 3.4 Biases → Adaptive Weights (BossAdaptiveWeights)

`BossAdaptiveWeights` reads the full 9-dimension bias vector from `PlayerBiasTracker.GetAverageBiases()` to tune ML observation channels, adjusting boss behavior in real-time beyond the initial variant selection.

---

## 4. Timing Summary

| System | Interval | Scope |
|--------|----------|-------|
| PlayerArchetypeClassifier | 180s eval + 0.5s distance sample | Per-client |
| PlayerBiasTracker | **0.5s** eval + 0.5s distance sample *(문서 수정)* | Per-client |
| BossDraftManager | On draft round end (event-driven) | Server-only |
| BossAIPoolManager variant swap | On archetype change (event-driven) | Server-only |

---

## 5. 검증 요약 — 아키타입별 분류 예상 (수정 전 vs 후)

### 수정 전 (현재): 시뮬레이션 예상

| BT 봇 | 예상 분류 | 정확도 | 주요 원인 |
|--------|----------|--------|----------|
| **Melee** | Hybrid/Ranged 오분류 | ❌ | OptimalMin=5m인데 임계값=5m → 대부분 miss |
| **Ranged** | Ranged~CC 혼동 | ⚠️ | SealChain CC태그가 CC점수 부풀림 |
| **CC** | CC~Ranged 혼동 | ⚠️ | ErosionField/RuptureMag이 Ranged점수 축적 |
| **Hybrid** | Hybrid (맞음) | ✅ | 넓은 교전거리로 어느 쪽에도 편중 안 됨 |

### 수정 후: 시뮬레이션 예상

| BT 봇 | 예상 Melee | 예상 Ranged | 예상 CC | 예상 분류 | 이유 |
|--------|-----------|------------|---------|----------|------|
| **Melee** | ★★★★ | ★ | ☆ | ✅ Melee | 12m 임계값으로 5-10m 교전 전부 포착 |
| **Ranged** | ☆ | ★★★★ | ★★ | ✅ Ranged | 15m+ 스킬만 Ranged, SealChain은 CC로만 |
| **CC** | ★ | ★ | ★★★★ | ✅ CC | CC태그 우선, 중거리 스킬 Ranged 기여 ↓, slotCC +0.8 |
| **Hybrid** | ★★ | ★★ | ☆ | ✅ Hybrid | 분산된 점수로 dominant < 0.50 |

### 핵심 수정사항 요약

| # | 변경 | 기존 | 수정 | 영향 |
|---|------|------|------|------|
| 1 | **Melee 거리 임계값** | 5m | **12m** | Melee봇 정확 분류 (가장 큰 영향) |
| 2 | **Ranged 스킬 기준** | range > 8f | **range > 15f** (CC 아닌 것만) | CC↔Ranged 혼동 해소 |
| 3 | **CC태그 스킬 우선** | CC +1.5 그리고 range>8이면 Ranged도 | **CC만 적용, Ranged 미적용** | CC 분류 순도 ↑ |
| 4 | **Passive Ranged 임계값** | > 10m | **> 20m** | 중거리(10-20m) CC구간을 중립으로 |
| 5 | **Decay** | ×0.3 | **×0.5** | 분류 흔들림 감소 |
| 6 | **Dominant threshold** | ≥ 0.55 | **≥ 0.50** | 순수 아키타입 분류 확률 ↑ |
| 7 | **Slot CC bonus** | +0.5 | **+0.8** | CC봇 3-4개 CC스킬로 확실한 차별화 |
| 8 | **Parry 가중치** | +2.0 | **+1.5** | 단일 이벤트 분류 뒤집힘 방지 |
| 9 | **BiasTracker meleeThreshold** | 12m | **15m** | CC교전거리(8-14m) 포함 |
| 10 | **BiasTracker rangedThreshold** | 25m | **20m** | R×CC 사각지대 해소 |
| 11 | **SurvivalBias** | Evade만 | **생존 스킬 사용도 포함** 권장 | BT봇 회피없음 대응 |
| 12 | **AggressionBias 임계값** | 0.50 | **0.35** | Delta 방식에서 도달 가능한 수준 |
