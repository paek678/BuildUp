# 교차 프로젝트 동기화 검증 프롬프트

> **용도**: 이 프롬프트를 다른 Claude 세션(학습 환경 관리)에 붙여넣어서, 해당 세션의 코드가 아래 운영 측 사양과 정확히 일치하는지 검증.
> **작성 기준**: 운영 프로젝트(Buildup) 소스코드 직접 추출 (2026-05-26)

---

## 검증 요청

아래 항목들을 **당신의 학습 프로젝트 소스코드**와 하나씩 대조해 주세요.
각 항목마다 ✅ 일치 / ❌ 불일치 / ⚠️ 확인불가 로 표시하고,
불일치 시 **당신 쪽 실제 값**과 **어느 파일 몇 번째 줄**인지 명시해 주세요.

---

## A. BehaviorParameters (ONNX drop-in 필수 일치)

| 항목 | 운영 값 |
|------|---------|
| VectorObservationSize | **129** |
| NumStackedVectorObservations | **1** |
| BranchSizes | **[5]** (1 branch, discrete) |
| NumContinuousActions | **0** |

---

## B. 정규화 상수 (BossObservationCollector 필드)

```
_maxDistance  = 55
_maxCooldown = 30
_maxSpeed    = 16
_maxBurstDmg = 80
_maxBossPhase = 4
```

추가 상수:
```
TouchRange = 5f  (const)
BossSkillSlots = 5  (const)
ChannelsPerSlot = 7  (const)
SpeedSmooth = 0.15f  (const, EMA 평활)
```

---

## C. Observation 129ch 정확한 채널 매핑

### Section 1: Position (11ch, #0-10)

```
#0   dirP1.x           = (P1.pos - boss.pos).normalized.x
#1   dirP1.z           = (P1.pos - boss.pos).normalized.z
#2   distP1_norm       = Clamp01(distP1 / 55)
#3   bossFwd.x         = transform.forward.x
#4   bossFwd.z         = transform.forward.z
#5   dotP1             = Dot(forward, dirP1)
#6   dirP2.x           = (P2.pos - boss.pos).normalized.x
#7   dirP2.z           = (P2.pos - boss.pos).normalized.z
#8   distP2_norm       = Clamp01(distP2 / 55)
#9   distPP_norm       = Clamp01(Distance(P1, P2) / 55)
#10  dotP2             = Dot(forward, dirP2)
```

### Section 2: Boss state (4ch, #11-14)

```
#11  bossHpPct         = bossStatManager.GetHPPercent()    [0~1]
#12  p1HpPct           = p1StatManager.GetHPPercent()      [0~1]
#13  p2HpPct           = p2StatManager.GetHPPercent()      [0~1]
#14  phaseNorm         = Clamp01((float)(phase + 1) / _maxBossPhase)
```

**⚠️ 주의**: #14는 `(phase + 1) / 4` 입니다. `phase / 4`가 아님.
- Phase 0 → 0.25, Phase 1 → 0.5, Phase 2 → 0.75, Phase 3 → 1.0

### Section 3: Boss skill slots (35ch, #15-49)

5 슬롯 × 7ch. 각 슬롯의 7ch 구조 (`AddSlotObservation`):

```
+0  remCD      = Clamp01(executor.GetRemainingCooldown(skill) / 30)
+1  effectCD   = Clamp01(executor.GetEffectiveCooldown(skill) / 30)
+2  range      = Clamp01(skill.Range / 55)
+3  coneAoE    = Clamp01(
                   if Directional: skill.AIHint_ConeOrAoE / 180
                   if AoE:         skill.AIHint_ConeOrAoE / 25
                   else:           0
                 )
+4  cat_dir    = (AIHint_Category == Directional) ? 1 : 0
+5  cat_aoe    = (AIHint_Category == AoE) ? 1 : 0
+6  cat_proj   = (AIHint_Category == Projectile) ? 1 : 0
```

빈 슬롯(skill == null): 7ch 모두 0.

채널 매핑:
- slot 0: #15-21
- slot 1: #22-28
- slot 2: #29-35
- slot 3: #36-42
- slot 4: #43-49

### Section 4: Touch (2ch, #50-51)

```
#50  p1Touch = (distP1 < 5f) ? 1 : 0
#51  p2Touch = (distP2 < 5f) ? 1 : 0
```

### Section 5: Player skill slots (70ch, #52-121)

P1 5슬롯 (#52-86) + P2 5슬롯 (#87-121).

**⚠️ 핵심**: `AddPlayerSlots`는 보스 슬롯과 **완전히 동일한** `AddSlotObservation`을 호출합니다.
즉 순서는: remCD, effectCD, range, coneAoE, cat_dir, cat_aoe, cat_proj

(HANDOFF 문서 §5에서 Player 슬롯 순서가 range, remCD, maxCD로 적혀있으나, **코드 기준으로 boss와 동일 순서**가 맞습니다.)

### Section 6: Extra (7ch, #122-128)

```
#122  p1Casting     = (p1StatManager.IsCasting) ? 1 : 0
#123  p2Casting     = (p2StatManager.IsCasting) ? 1 : 0
#124  p1AvgSpeed    = Clamp01(_p1AvgSpeed / 16)
#125  p2AvgSpeed    = Clamp01(_p2AvgSpeed / 16)
#126  p1Unlocked    = Clamp01((float)p1UnlockedCount / 5)
#127  p2Unlocked    = Clamp01((float)p2UnlockedCount / 5)
#128  burstDmg      = Clamp01(_recentDamageSum / 80)
```

`_p1AvgSpeed` 계산: EMA `Lerp(prev, instantSpeed, 0.15f)`, instantSpeed = `Distance(curPos, prevPos) / Max(deltaTime, 0.001f)`

### 합계 확인
```
11 (Position) + 4 (BossState) + 35 (BossSkills) + 2 (Touch) + 35 (P1Skills) + 35 (P2Skills) + 7 (Extra) = 129 ✓
```

---

## D. Action Space

| Index | 의미 | 구현 |
|-------|------|------|
| 0 | idle | 아무것도 안 함 |
| 1 | forward | `position += forward * moveSpeed * phaseSpeedScale * dt` |
| 2 | turnLeft | `Rotate(0, -540 * dt, 0)` |
| 3 | turnRight | `Rotate(0, +540 * dt, 0)` |
| 4 | backward | `position -= forward * moveSpeed * 0.7 * phaseSpeedScale * dt` |

- **BackwardSpeedScale = 0.7f** (const)
- **_moveSpeed = 8.4f**
- **_rotationSpeed = 540f**
- **IsCasting 중 이동 마스킹**: action 1~4 비활성 (idle만 허용)

---

## E. Game Specs

| 항목 | 값 |
|------|-----|
| Boss HP | 6000 |
| Player HP | 150 |
| Boss base speed | 8.4 m/s |
| Player speed | 14 m/s |
| Boss rotation speed | 540°/s |
| Episode duration | 720s (12분) |
| Phase thresholds | HP 75%/50%/25% → Phase 1/2/3 |

---

## F. Phase Multipliers (배열 인덱스 = Phase 번호)

```csharp
_phaseSpeedScale    = { 1f, 1f, 1.1f, 1.2f }
_phaseCooldownScale = { 1f, 0.85f, 0.7f, 0.5f }
_phaseDamageScale   = { 1f, 1.08f, 1.16f, 1.25f }
```

결과:
| Phase | Speed | Cooldown | Damage |
|-------|-------|----------|--------|
| 0 (100-75% HP) | 8.4 | ×1.0 | ×1.0 |
| 1 (75-50% HP) | 8.4 | ×0.85 | ×1.08 |
| 2 (50-25% HP) | 9.24 | ×0.7 | ×1.16 |
| 3 Enrage (<25% HP) | 10.08 | ×0.5 | ×1.25 |

---

## G. Skill Unlock Cadence

```csharp
// Boss: initial 1, max 5, interval 175s
_trainingSkillManager.SetUnlockConfig(1, 5, 175f);

// Player: initial 1, max 4, interval 180s
_p1TrainingSkillMgr.SetUnlockConfig(1, 4, 180f);
_p2TrainingSkillMgr.SetUnlockConfig(1, 4, 180f);
```

---

## H. Combat Reward Parameters (현재 코드 기본값)

```csharp
_winReward          = 1.5f    // 양쪽 사망 시
_lossPenalty        = 1f      // 보스 사망 시 (-1)
_timeoutPenalty     = 0.5f    // 720s 초과 시 (-0.5)
_dmgDealtScale      = 0.0015f // 보스→플레이어 데미지 × scale
_dmgTakenScale      = 0.0003f // 플레이어→보스 데미지 × -scale
_phaseReward        = 0.05f   // 페이즈 진행 보상 (각 1회)
_stepPenalty        = 0.0001f // 매 step
_playerKillReward   = 0.3f    // 플레이어 1명 사망 시
_approachRewardScale = 0.002f // 접근 포텐셜 보상
_hitDeadPenalty     = 0.01f   // 사망 플레이어 향해 이동 패널티
_hitDeadRange       = 8f      // 위 패널티 적용 범위
_bothFarPenalty     = 0.005f  // 양쪽 모두 먼 경우
_bothFarThreshold   = 7f      // 위 패널티 거리 기준
```

**⚠️ 참고**: 이 값들은 **씬(Inspector) 오버라이드**로 매치업별로 다를 수 있음.
현재 학습 중인 Hybrid_Hybrid_Close_v2 매치업 오버라이드:
```
_stepPenalty        = 0.0002
_playerKillReward   = 0.35
_approachRewardScale = 0.003
_hitDeadPenalty     = 0.04
_hitDeadRange       = 8
_bothFarPenalty     = 0.004
_bothFarThreshold   = 18
_forcedP1Archetype  = "Ranged"
_forcedP2Archetype  = "Hybrid"
```

---

## I. Episode 종료 조건 및 보상

| 조건 | _endReason | 보상 |
|------|-----------|------|
| Boss HP ≤ 0 | "BossLose" | -_lossPenalty (-1.0) |
| P1 + P2 모두 사망 | "BossWin" | +_winReward (+1.5) |
| elapsed ≥ 720s | "Timeout" | -_timeoutPenalty (-0.5) |
| boss.y < -5 | "OutOfBounds" | -1.0 |
| 플레이어 1명 사망 | (계속) | +_playerKillReward, FreezePlayer |

---

## J. Boss Skills (11개)

| Skill | CD | Range | AIHint_ConeOrAoE | AIHint_Category | Damage |
|-------|----|-------|-------------------|-----------------|--------|
| ExecutionSpike_Boss | 10s | 18m | 38 (deg) | Directional | 76 |
| CrushingBarrage_Boss | 10s | 15m | 40 (deg) | Directional | 20×4 |
| FortressArmor_Boss | 12s | 16m | 35 (deg) | Directional | 65 |
| CollapseRoar_Boss | 14s | 24m | 12 (m) | AoE | 55×2 |
| MarkWave_Boss | 12s | 22m | 65 (deg) | Directional | 50 |
| BarrierBreaker_Boss | 14s | 48m | 0 | Projectile | 62 |
| ErosionField_Boss | 14s | 22m | 20 (m) | AoE | 8 DoT/s |
| SurvivalPulse_Boss | 20s | Self | 0 | Self | HP×5% |
| OverchargeMode_Boss | 18s | Self | 0 | Self | +12%/-12% |
| SealChain_Boss | — | — | 0 | None | UNIMPL |
| RuptureMagazine_Boss | — | — | 0 | None | UNIMPL |

---

## K. Player Skills (12개)

| Skill | CD | Range | AIHint_ConeOrAoE | AIHint_Category | Damage |
|-------|----|-------|-------------------|-----------------|--------|
| PiercingShot | 10s | 60m | 0 | Projectile | 110 |
| ExecutionSpike | 8s | 24m | 32 (deg) | Directional | 100 |
| CrushingBarrage | 6s | 24m | 38 (deg) | Directional | 28×4 |
| FortressArmor | 8s | 24m | 38 (deg) | Directional | 75 |
| CollapseRoar | 10s | 27m | 12 (m) | AoE | 80×2 |
| BarrierBreaker | 8s | 66m | 0 | Projectile | 88 |
| HuntingMark | 7s | 66m | 0 | Projectile | 60 |
| ErosionField | 10s | 42m | 9 (m) | Projectile | 8 DoT/s |
| SealChain | 9s | 66m | 0 | Projectile | 50 |
| RuptureMagazine | 9s | 66m | 0 | Projectile | 95 |
| SurvivalPulse | 14s | Self | 0 | Self | HP×6% |
| OverchargeMode | 18s | Self | 0 | Self | +15%/-10% |

---

## L. SkillCategoryFlag enum

```csharp
public enum SkillCategoryFlag : byte {
    None = 0,
    Directional = 1,
    AoE = 2,
    Projectile = 3,
    Self = 4,
}
```

AddSlotObservation 내 coneAoE 계산:
- Directional → `ConeOrAoE / 180f`
- AoE → `ConeOrAoE / 25f`
- 그 외 → `0f`

---

## M. PlayerProfile (BT 이동 파라미터)

4개 archetype의 BT 파라미터 (BossInferenceAgent 내 `_archetypeProfiles` 배열):

```csharp
public struct PlayerProfile {
    string ArchetypeName;
    SkillPoolSO SkillPool;
    BehaviorGraph MoveGraph;
    float DangerRange;      // 위험 거리
    float OptimalMin;       // 최적 거리 최소
    float OptimalMax;       // 최적 거리 최대
    float FleeDistance;     // 도주 거리
    float FlankRadius;      // 측면 우회 반경
    float StrafeRadius;     // 회전이동 반경
    float StrafeAngleStep;  // 회전이동 각도 단위
    float MinSpacing;       // 아군 간 최소 간격
    float AttackRangeMin;   // 공격 범위 최소
    float AttackRangeMax;   // 공격 범위 최대
    float SafeRangeMin;     // 안전 범위 최소
    float SafeRangeMax;     // 안전 범위 최대
    float MinFlankAngle;    // 최소 측면 각도
}
```

**참고값** (Inspector 설정이므로 씬마다 다를 수 있음):

| Archetype | DangerRange | OptimalMin | OptimalMax |
|-----------|-------------|------------|------------|
| Melee | 3 | 2 | 5 |
| Ranged | 16 | 18 | 30 |
| CC | 6 | 8 | 14 |
| Hybrid | 5 | 6 | 30 |

---

## N. Training Config (PPO Hyperparameters)

```yaml
behaviors:
  BossInference:
    trainer_type: ppo
    hyperparameters:
      batch_size: 1024
      buffer_size: 10240
      learning_rate: 0.0003
      beta: 0.005
      epsilon: 0.2
      lambd: 0.95
      num_epoch: 3
      learning_rate_schedule: linear
      beta_schedule: linear
      epsilon_schedule: linear
    network_settings:
      normalize: false
      hidden_units: 256
      num_layers: 3
    reward_signals:
      extrinsic:
        gamma: 0.995
        strength: 1.0
    max_steps: 40000000
    time_horizon: 1024
    summary_freq: 50000
    keep_checkpoints: 30
    checkpoint_interval: 200000
```

---

## O. 3단계 커리큘럼 학습 체인

```
Touch → Engage → Combat (initialize-from 체인)

1단계: mlagents-learn BossInference_config.yaml --run-id=BossInference_touch_v1
2단계: mlagents-learn BossInference_config.yaml --run-id=BossInference_engage_v1 --initialize-from=BossInference_touch_v1
3단계: mlagents-learn BossInference_config.yaml --run-id=BossInference_<matchup> --initialize-from=BossInference_engage_v1
```

Touch/Engage 모드는 BossInferenceAgent 내 `_trainingMode` enum으로 전환.

---

## P. 검증 체크리스트

아래 각 항목에 ✅/❌/⚠️ 표시해 주세요:

- [ ] **A** — BehaviorParameters (129, 1, [5], 0)
- [ ] **B** — 정규화 상수 5개 일치
- [ ] **C** — 129ch 채널 순서 완전 일치 (#0~#128)
  - [ ] #14 phase 계산: `(phase + 1) / 4` 맞는지
  - [ ] AddSlotObservation 순서: remCD, effectCD, range, coneAoE, 3 one-hots
  - [ ] Player 슬롯도 boss와 동일 순서
  - [ ] #126-127: `/5` (BossSkillSlots) 나누기 맞는지
- [ ] **D** — Action 5개 매핑 + backward 0.7 + IsCasting 마스킹
- [ ] **E** — HP/Speed/Duration 일치
- [ ] **F** — Phase multipliers 4단계 일치
- [ ] **G** — Skill unlock cadence (Boss 1/5/175s, Player 1/4/180s)
- [ ] **H** — Reward 파라미터 (코드 기본값 또는 씬 오버라이드)
- [ ] **I** — 종료 조건 5가지 + 보상값
- [ ] **J** — Boss 스킬 11개 값 일치
- [ ] **K** — Player 스킬 12개 값 일치
- [ ] **L** — SkillCategoryFlag enum + coneAoE 정규화 로직
- [ ] **M** — PlayerProfile 14개 파라미터 구조체
- [ ] **N** — PPO 하이퍼파라미터 일치

---

## Q. 알려진 문서-코드 불일치 (이미 확인된 것)

1. **HANDOFF §5 Player 슬롯 순서**: 문서에 `range, remCD, maxCD` 순으로 적혀있으나, 실제 코드는 boss와 동일하게 `remCD, effectCD, range` 순. **코드가 정답**.
2. **HANDOFF §5 #14 phase**: 문서에 `phase / 4`로 적혀있으나, 코드는 `(phase + 1) / 4`. **코드가 정답**.
3. **HANDOFF §10 Reward**: 문서 기본값과 실제 코드 기본값이 다름 (Win 1.0→1.5, Timeout -0.3→-0.5 등). **코드가 정답**.

이 불일치들은 HANDOFF 문서 작성 이후 코드가 업데이트되었기 때문입니다.
당신 쪽 코드가 **이 프롬프트의 값**(= 최신 코드 추출)과 일치하면 정합성 OK입니다.

---

**검증 완료 후 불일치 항목이 있으면 해당 파일명:줄번호와 함께 보고해 주세요.**
