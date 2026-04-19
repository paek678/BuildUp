# 스킬 시스템 사용 가이드

## 전체 구조 요약

```
SkillDefinition (SO)         스킬 메타데이터 (이름, 쿨타임, 사거리, 태그)
     ↑ 바인딩
SkillLibrary (static)        스킬 조립 코드 — 부품을 조합해 SkillStep 생성
     ↑ 주입
SkillBinder (static)         SkillLibrary 결과를 SO.RuntimeStep 에 주입
     ↑ 호출
SkillBootstrap (MonoBehaviour) Awake 에서 SkillBinder.BindAll() 호출
```

---

## 실행 플로우

```
매 프레임 Update
     │
     ▼
SkillManager.Update()
     │  슬롯 0~4 순회, 첫 번째 CanCast 성공 스킬 실행
     │
     ▼
SkillManager.CanCast()  ────── 7가지 조건 검사
     │  1) skill.IsReady (RuntimeStep 주입됨?)
     │  2) SkillExecutor.CanUse (쿨타임 만료?)
     │  3) StateManager.CanCast (Stunned/HitStun/Silence/Casting 아닌지)
     │  4) 타겟 존재 + 생존 (Self 타입은 skip)
     │  5) 거리 ≤ skill.Range (Self 타입은 skip)
     │  6) RuntimeCondition 검사 (null이면 통과)
     │  7) SkillContext 생성
     │
     ▼
SkillExecutor.Execute()
     │  1) ctx.RefreshSnapshot()
     │  2) RuntimeCondition 재검사 (실패 시 쿨타임 미소모)
     │  3) 쿨타임 기록
     │  4) skill.RuntimeStep.Invoke(ctx) ← 실제 스킬 실행
     │  5) 실행 로그 출력
     │
     ▼
SkillStep (delegate chain)
     │  SkillComponents 부품들이 순서대로 실행
     │  예: DealDirectionalHit → TriggerOnHit → DealMultiHitDamage
     │
     ▼
ICombatant.TakeDamage() / ApplyStatus() / ...
     │  StatManager 경유 피해/상태이상 적용
```

---

## 핵심 클래스별 역할

### SkillDefinition (SO)
- **위치**: `Assets/ScriptableObjects/Skills/`
- **역할**: 스킬 하나의 메타데이터 보관
- **주요 필드**:
  - `SkillId` — 고유 식별자 (SkillBinder 매칭용)
  - `Cooldown` — 쿨타임 (초)
  - `Range` — 자동 시전 거리 (m). Self 타입은 무시됨
  - `TargetType` — Enemy(0), Self(1), Ally(2), Direction(3)
  - `RuntimeStep` — [NonSerialized] 실제 실행 로직. SkillBinder가 주입
  - `RuntimeCondition` — [NonSerialized] 실행 전 조건. 실패 시 쿨타임 미소모
  - `IsReady` — RuntimeStep != null 이면 true

### SkillContext
- **역할**: 스킬 실행 중 모든 노드가 공유하는 런타임 정보
- **주요 필드**:
  - `Caster` — 시전자 (ICombatant)
  - `PrimaryTarget` — 현재 대상 (범위 스킬에서 순회 중 바뀜)
  - `CastPosition` — 발동 기준 위치
  - `CastDirection` — 시전 방향
  - `HitLanded` — 직전 판정 결과 (DealDirectionalHit/CheckParry가 기록)
  - `TargetHpPercent` — 대상 HP% (RefreshSnapshot 시점)
  - `ParryInputTime` — 패링 입력 시각

### SkillComponents (static)
- **위치**: `Assets/Scripts/Skill/Core/SkillComponents.cs`
- **역할**: 스킬 조립용 부품 37종
- **반환 타입**:
  - `SkillStep` (delegate) — 실행 부품
  - `SkillCondition` (delegate) — 조건 부품

### SkillLibrary (static)
- **위치**: `Assets/Scripts/Skill/Core/SkillLibrary.cs`
- **역할**: SkillComponents 부품을 조합해 완성된 SkillStep 반환
- **예시**:
```csharp
public static SkillStep CollapseRoar() =>
    ctx =>
    {
        ApplyInArea(1.4f, AreaShape.Circle,
            inner =>
            {
                DealDamage(95f).Invoke(inner);
                ApplyDefenseDown(2f, 5f).Invoke(inner);
            }
        ).Invoke(ctx);
        TriggerOnHit(
            onMiss: ApplyInArea(4.0f, AreaShape.Circle, DealDamage(95f))
        ).Invoke(ctx);
    };
```

### SkillBinder (static)
- **역할**: SkillLibrary 결과를 SkillDefinition SO에 주입
- **호출**: SkillBootstrap.Awake() → SkillBinder.BindAll(registry)
- **바인딩 예시**:
```csharp
Bind(registry, "CollapseRoar", SkillLibrary.CollapseRoar());
Bind(registry, "SurvivalPulse", SkillLibrary.SurvivalPulse(), SkillLibrary.SurvivalPulseCondition());
```

### SkillManager (MonoBehaviour)
- **역할**: 자동 시전 매니저. 매 프레임 슬롯 순회, 첫 CanCast 스킬 실행
- **Inspector 설정**:
  - `Slots[0~4]` — SkillDefinition SO 드래그 (index 0 = 최우선)
  - `Auto Cast Enabled` — 자동 시전 ON/OFF
  - `Log Auto Cast` — CanCast 실패 사유 콘솔 출력
- **참조 필수**: StatManager, StateManager, GameManager, PlayerController

### SkillExecutor (MonoBehaviour)
- **역할**: 스킬 실행 + 쿨타임 관리
- **API**:
  - `Execute(skill, ctx)` — 실행 (성공 시 true)
  - `CanUse(skill)` — 쿨타임 체크
  - `GetRemainingCooldown(skill)` — 남은 쿨타임
  - `ResetCooldown(skillId)` — 쿨타임 초기화

---

## 보조 시스템

### SkillRangeDisplay (싱글톤)
- **역할**: 스킬 범위를 바닥에 반투명 원판으로 표시 (디버그용)
- **동작**: SkillComponents에서 스킬 실행 시 자동 호출
  - `DealDirectionalHit` → ShowCone (주황/회색)
  - `ApplyInArea` → ShowCircle (주황/회색)
  - `LaunchProjectile` → ShowLine (파란색)
- **프리팹 구조**:
```
RangeIndicator (빈 오브젝트)
 └── Visual (Cylinder, CapsuleCollider 삭제, URP Unlit Transparent Material)
```
- **Inspector**: Indicator Prefab 슬롯에 프리팹 드래그

### PersistentAreaManager + PersistentAreaPool
- **역할**: 지속 장판(SpawnPersistentArea) 소환 및 풀링
- **프리팹 구조**:
```
SkillArea (빈 오브젝트 + SkillArea 스크립트)
 └── Visual (Cylinder, CapsuleCollider 삭제, 투명 Material)
```
- **Inspector**: PersistentAreaManager → Pool 슬롯에 PersistentAreaPool 연결
  PersistentAreaPool → Prefab 슬롯에 SkillArea 프리팹 드래그

### ProjectilePool + SkillProjectile
- **역할**: 투사체(LaunchProjectile) 발사 및 풀링
- **프리팹**: Rigidbody + Collider(isTrigger) + SkillProjectile 스크립트
- **충돌 판정**: OnTriggerEnter → ICombatant 검색 → onHit 실행

---

## 씬 필수 오브젝트

| 오브젝트 | 컴포넌트 | Inspector 연결 |
|---------|---------|---------------|
| SkillBootstrap | SkillBootstrap | Registry → SkillRegistry SO |
| PersistentAreaManager | PersistentAreaManager | Pool → PersistentAreaPool |
| PersistentAreaPool | PersistentAreaPool | Prefab → SkillArea 프리팹 |
| ProjectPool | ProjectilePool | Prefab → ProjectileTile 프리팹 |
| SkillRangeDisplay | SkillRangeDisplay | Indicator Prefab → RangeIndicator 프리팹 |
| Player 1P/2P | SkillManager + SkillExecutor | Slots에 SO 드래그, StatManager/StateManager/GameManager/PlayerController 연결 |

---

## 새 스킬 추가 절차

### 1단계 — SO 생성
- Unity 메뉴: `Tenebris > 스킬 SO 전체 생성`
- 또는 수동: `Assets/ScriptableObjects/Skills/` 우클릭 → Create → Tenebris → SkillDefinition
- SkillId, DisplayName, Cooldown, Range, TargetType 설정
- SkillRegistry SO의 Pool 배열에 추가

### 2단계 — 스킬 조립 (SkillLibrary)
```csharp
// SkillLibrary.cs 에 추가
public static SkillStep NewSkillName() =>
    ctx =>
    {
        DealDirectionalHit(100f, 3.0f, 45f).Invoke(ctx);
        TriggerOnHit(
            onHit: hit => ApplyStun(1f).Invoke(hit)
        ).Invoke(ctx);
    };
```

### 3단계 — 바인딩 (SkillBinder)
```csharp
// SkillBinder.cs BindAll() 에 추가
bound += Bind(registry, "NewSkillName", SkillLibrary.NewSkillName());

// 조건부 스킬이면:
bound += Bind(registry, "NewSkillName", SkillLibrary.NewSkillName(), SkillLibrary.NewSkillCondition());
```

### 4단계 — 슬롯 배치
- Player의 SkillManager Inspector → Slots 배열에 SO 드래그

---

## 부품 목록 (37종)

### 기본 전투
| # | 부품 | 설명 |
|---|------|------|
| 1 | `DealDamage(amount)` | 단일 피해 |
| 2 | `DealMultiHitDamage(amount, hits)` | 다단 히트 |
| 3 | `ApplyDamageOverTime(duration, dps)` | 지속 피해 |
| 35 | `DealDirectionalHit(dmg, range, angle)` | 전방 부채꼴 타격 |

### 생존
| # | 부품 | 설명 |
|---|------|------|
| 4 | `RecoverHP(amount)` | 즉시 회복 |
| 5 | `ApplyHPRegen(duration, perSec)` | 지속 재생 |
| 6 | `GainShield(amount)` | 방어막 획득 |
| 7 | `ReflectDamage(duration, ratio)` | 피해 반사 |
| 8 | `ApplyInvulnerability(duration)` | 무적 |

### 상태이상
| # | 부품 | 설명 |
|---|------|------|
| 9 | `ApplyStun(duration)` | 스턴 |
| 10 | `ApplyHitStun(duration)` | 경직 |
| 11 | `ApplySlow(duration, ratio)` | 둔화 |
| 12 | `ApplyRoot(duration)` | 속박 |
| 13 | `ApplyVulnerability(duration, ratio)` | 취약 |
| 25 | `ApplySilence(duration)` | 침묵 |
| 27 | `ApplyAntiHeal(duration, ratio)` | 치유 감소 |

### 능력 변화
| # | 부품 | 설명 |
|---|------|------|
| 14 | `ApplyDamageUp(duration, ratio)` | 공격력 증가 |
| 15 | `ApplyDamageDown(duration, ratio)` | 공격력 감소 |
| 16 | `ApplyDefenseUp(duration, ratio)` | 방어력 증가 |
| 17 | `ApplyDefenseDown(duration, ratio)` | 방어력 감소 |
| 21 | `ApplyBuff(duration, type, value)` | 버프 적용 |
| 22 | `ApplyDebuff(duration, type, value)` | 디버프 적용 |

### 위치 제어
| # | 부품 | 설명 |
|---|------|------|
| 18 | `ApplyKnockback(distance)` | 넉백 |
| 19 | `PullTarget(distance, duration)` | 끌어당기기 |
| 36 | `MoveSelf(distance, duration, moveType)` | 자기 이동 |

### 방어 대응 / 처형 / 해제
| # | 부품 | 설명 |
|---|------|------|
| 28 | `DealShieldBreakDamage(amount, mult)` | 실드 파괴 피해 |
| 29 | `ExecuteBelowHP(hpThreshold, bonusDmg)` | 처형 (HP% 이하 시 추가 피해) |
| 26 | `CleanseStatus(type, count)` | 상태이상 정화 |
| 30 | `DispelBuff(type, count)` | 버프 해제 |

### 핵심 시스템 (패링)
| # | 부품 | 설명 |
|---|------|------|
| 23 | `CheckParry()` | 패링 판정 → HitLanded 기록 |
| 24 | `ApplyParryReward(type, value, dur)` | 패링 성공 보상 |

### 범위 / 투사체 래퍼
| # | 부품 | 설명 |
|---|------|------|
| 20 | `ApplyInArea(radius, shape, inner)` | 범위 내 전체 적용 |
| 31 | `SpawnPersistentArea(dur, r, shape, tick, action)` | 지속 장판 생성 |
| 32 | `LaunchProjectile(speed, range, pierce, onHit)` | 투사체 발사 |

### 흐름 제어
| # | 부품 | 설명 |
|---|------|------|
| 33 | `TriggerOnCondition(name, cond, onTrue, onFalse)` | 조건 분기 |
| 34 | `TriggerOnHit(onHit, onMiss)` | 적중/빗나감 분기 |

### 감지 조건 (SkillCondition)
| # | 부품 | 설명 |
|---|------|------|
| 37 | `CheckTargetDistance(min, max)` | 거리 판정 |

---

## 디버그 도구

| 토글 | 위치 | 설명 |
|------|------|------|
| `_logExecution` | SkillExecutor | 스킬 실행 시 시전자/대상/HP/쿨타임/로그 체인 출력 |
| `_logAutoCast` | SkillManager | CanCast 실패 사유 경고 로그 |
| `_logCombat` | StatManager | 피해/회복/상태이상/사망 로그 |
| `_logRange` | SkillRangeDisplay | 범위 표시 생성 로그 |
| `_showRange` | SkillRangeDisplay | 범위 표시 ON/OFF |
| Inspector 모니터 | StatManager | HP/Shield/배율/상태이상 실시간 표시 |
