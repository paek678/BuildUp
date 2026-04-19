# 스킬 시스템 구조 문서

> 이 파일은 Scripts/Skill 폴더의 설계 방식과 진행 상태를 기록한다.
> 구조나 방식이 변경될 때마다 반드시 이 파일도 함께 수정한다.

---

## 설계 방향

스킬 하나를 직접 하드코딩하지 않는다.
작은 부품(Primitive / Wrapper / Condition)을 조합해서 스킬을 만든다.
모든 부품은 `SkillStep` 또는 `SkillCondition` 타입 하나로 통일된다.
플레이어와 보스는 같은 스킬 풀을 공유하고, 보스는 태그 기반으로 카운터 스킬을 선택한다.

---

## 핵심 타입 (SkillTypes.cs)

```csharp
delegate void SkillStep(SkillContext ctx);       // 모든 실행 단위
delegate bool SkillCondition(SkillContext ctx);  // 모든 조건 판정 단위
```

이 두 타입만 존재한다. Primitive든 Wrapper든 전부 `SkillStep`을 반환한다.

---

## 파일 구성

| 파일 | 역할 |
|---|---|
| `SkillTypes.cs` | `SkillStep` / `SkillCondition` delegate 및 전체 enum 정의 |
| `ICombatant.cs` | 플레이어 / 보스가 구현해야 하는 전투 인터페이스 |
| `SkillContext.cs` | 스킬 실행 중 모든 노드가 공유하는 런타임 정보 |
| `SkillDefinition.cs` | 스킬 메타데이터 ScriptableObject + NonSerialized RuntimeStep |
| `SkillExecutor.cs` | 쿨타임 관리 + `Execute()` 실행 (MonoBehaviour) |
| `SkillRegistry.cs` | 전체 스킬 풀 관리, 드래프트 후보, 보스 카운터 선택 |
| `SkillComponents.cs` | **부품 39종 전체** — 한 파일에서 번호순 확인 및 조합 가능 |

---

## 실행 흐름

```
SkillExecutor.Execute(def, ctx)
  └─ def.RuntimeStep(ctx)               ← SkillLibrary 가 조립한 루트 노드
       └─ Wrapper(ctx)                  ← 범위 수집 / 조건 분기 / 투사체
            └─ 조건 판정 / 타겟 확정
                 └─ Primitive(ctx)      ← 실제 수치 변화 (피해 / 버프 / 이동 등)
                      └─ 후속 Trigger  ← TriggerOnHit / TriggerOnCondition
```

---

## 부품 조합 패턴

### 모든 Primitive — 동일한 패턴
```csharp
public static SkillStep DealDamage(float amount) =>
    ctx => { ctx.PrimaryTarget?.TakeDamage(amount); };
```

### 모든 Wrapper — 동일한 패턴
```csharp
public static SkillStep TriggerOnCondition(string name, SkillCondition cond, SkillStep onTrue, SkillStep onFalse = null) =>
    ctx => { (cond(ctx) ? onTrue : onFalse)?.Invoke(ctx); };
```

### 모든 Condition — 동일한 패턴
```csharp
public static SkillCondition HpBelow(float threshold) =>
    ctx => ctx.TargetHpPercent < threshold;
```

---

## 스킬 조립 방식 (SkillLibrary 에서 작성)

```csharp
using static SkillComponents;

// 처형 송곳
SkillStep 처형송곳 = Sequence(
    DealDirectionalHit(125, 2.0f, 30f),
    TriggerOnHit(
        onHit: Sequence(
            ApplyVulnerability(2f, 5f),
            ExecuteBelowHP(30f, 20f)
        )
    ),
    TriggerOnCondition("NoHit", NoHit(),
        onTrue: DealDirectionalHit(125, 2.4f, 70f)
    )
);
```

---

## SkillContext 주요 필드

| 필드 | 설명 | 누가 채우나 |
|---|---|---|
| `Caster` | 시전자 | 호출부 |
| `PrimaryTarget` | 주 대상 | 호출부 / Wrapper 가 순회 중 갱신 |
| `CastPosition` | 발동 기준 지점 | 호출부 / LaunchProjectile 이 착탄 시 갱신 |
| `CastDirection` | 발동 방향 | 호출부 |
| `HitLanded` | 핵심 판정 적중 여부 | DealDirectionalHit / LaunchProjectile |
| `TargetHpPercent` | 대상 HP 비율 (0~1) | `RefreshSnapshot()` |
| `TargetDistance` | 시전자 ↔ 대상 거리 | `RefreshSnapshot()` |
| `RecentDamageTaken` | 시전자가 최근 받은 피해 | 전투 시스템 (실행 전 주입) |

---

## ICombatant 구현 대상

- `PlayerController` — 플레이어
- `BossController` — 보스

두 클래스 모두 `ICombatant` 를 구현해야 스킬 시스템이 동작한다.

---

## 보스 AI 카운터 선택 흐름

```
플레이어 스킬 선택
  → 선택된 스킬들의 RoleTags 수집
  → SkillRegistry.GetCounterCandidates(playerRoleTags, 3)
  → CounterTags 매칭 점수 상위 3개 반환
  → 보스가 그 중 하나 선택
```

---

## 현재 TODO (미구현 / 연동 필요)

| 항목 | 파일 | 내용 |
|---|---|---|
| 투사체 프리팹 풀 | `SkillWrappers.cs` | `LaunchProjectile` — 현재 즉시 Raycast 대체 |
| 지속 장판 생성 | `SkillWrappers.cs` | `SpawnPersistentArea` — PersistentAreaManager 연동 필요 |
| 로프 착지 감지 | `SkillConditions.cs` | `RopeLanding()` — 현재 항상 false |
| ICombatant 구현 | `PlayerController`, `BossController` | 두 클래스에 인터페이스 구현 필요 |
| SkillLibrary | ✅ 완료 | 플레이어 공용 12 + 전용 6 + 보스 공용 12 조립 완료 |
| SkillDefinition SO | ✅ 완료 | Editor 메뉴 `Tenebris > 스킬 SO 전체 생성` 으로 23종 자동 생성 |
| SkillBootstrap | ✅ 완료 | 씬 배치 후 SkillRegistry 연결 → Awake 에서 BindAll 호출 |

---

## 변경 이력

| 날짜 | 변경 내용 |
|---|---|
| 2026-03-29 | 최초 구조 생성 (SkillTypes / ICombatant / SkillContext / SkillDefinition / SkillExecutor / SkillRegistry / SkillPrimitives / SkillWrappers / SkillConditions) |
| 2026-03-29 | 부품 파일 3개(SkillPrimitives / SkillWrappers / SkillConditions) → SkillComponents.cs 단일 파일로 통합. 원본 39종만 유지, 임의 추가 항목 제거 |
