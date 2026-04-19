# 테네브리스 (Tenebris) — 자체 완결형 프로젝트 프롬프트

> 이 문서는 외부 세션에서 스크립트 파일 접근 없이도 프로젝트를 이해하고 작업을 이어갈 수 있도록 작성된 자체 완결형 프롬프트입니다.

---

## 1. 프로젝트 개요

| 항목 | 내용 |
|------|------|
| 기획명 | 테네브리스 (Tenebris) |
| 장르 | 2인 협동 보스전 3D 탑다운 멀티플레이 액션 로그라이트 |
| Unity 버전 | 6000.3.11f1 (Unity 6) |
| 렌더 파이프라인 | URP 17.3.0 |
| 네트워크 | Unity NGO + Relay + Unity Transport (Host-authoritative) |
| ML | ML-Agents 4.0.2 |
| UniTask | **미설치** — 코루틴 사용, `WaitForSeconds` 반드시 캐싱 |
| Addressables | **미설치** — `[SerializeField] private` 직접 참조 |

---

## 2. 핵심 아키텍처 원칙

1. **StatsManager = 단일 진실 공급원**: 모든 스탯 변경은 StatsManager 경유 (직접 필드 수정 금지)
2. **Host-authoritative**: 클라이언트는 입력 의도만 전송, Host가 최종 판정
3. **ICombatant 인터페이스**: 전투 가능 객체(Player, Boss)는 반드시 구현
4. **ScriptableObject = 읽기 전용 템플릿**: SO는 초기값만 보관, Awake에서 Instantiate 복사
5. **SkillComponents = static class**: 스킬 부품은 SkillComponents.cs에만 추가
6. **2D 레거시 코드 기준 금지**: 3D Host-authoritative 경로 기준으로만 작업

---

## 3. 네트워크 구조

```
[Client A (Host)]
  ├─ NetworkManager (NGO)
  ├─ Unity Relay
  ├─ PlayerController (Owner)
  └─ BossController (Server-side)

[Client B (Guest)]
  ├─ NetworkManager (NGO)
  └─ PlayerController (Owner)
```

- 클라이언트 → Host : 입력 의도 RPC 전송
- Host → 클라이언트 : NetworkVariable 동기화
- 투사체는 NetworkObject로 호스트가 소유
- 모든 TakeDamage/ApplyStatus는 호스트에서만 호출

---

## 4. 파일 구조

```
Assets/
├── BaseStatsSO.cs                    # SO 공통 스탯 베이스
├── PlayerStatsSO.cs                  # 플레이어 초기 스탯 SO
├── BossStatsSO.cs                    # 보스 초기 스탯 SO
├── StatsManager.cs                   # 단일 진실 공급원 (HP/Shield/Status/Buff/Debuff)
├── CHANGES.md                        # 변경 이력
├── SKILL_DESIGN.md                   # 스킬 기획 문서
│
├── Scripts/
│   ├── GameManager.cs                # 싱글턴 — 플레이어/보스 리스트, 타이머
│   ├── PlayerController.cs           # ICombatant 구현 — Rigidbody 기반
│   ├── BossController.cs             # ICombatant 구현 — NavMeshAgent 기반
│   │
│   └── Skill/
│       ├── Core/
│       │   ├── SkillTypes.cs         # delegate + enum 정의
│       │   ├── SkillContext.cs       # 스킬 런타임 컨텍스트
│       │   ├── SkillComponents.cs    # 스킬 부품 37종 (static)
│       │   ├── SkillLibrary.cs       # 스킬 조립 코드 (SkillStep 반환)
│       │   ├── SkillDefinition.cs    # ScriptableObject — 메타 + RuntimeStep
│       │   ├── SkillExecutor.cs      # 실행 + 쿨타임 관리
│       │   └── SkillRegistry.cs      # SO — 스킬 풀, 태그 조회, 드래프트
│       │
│       ├── Projectile/
│       │   ├── ProjectilePool.cs     # 싱글턴 오브젝트 풀
│       │   └── SkillProjectile.cs    # 투사체 프리팹 컴포넌트
│       │
│       ├── Area/
│       │   ├── PersistentAreaManager.cs  # 싱글턴 — 장판 소환 허브
│       │   ├── PersistentAreaPool.cs     # 오브젝트 풀
│       │   └── SkillArea.cs              # 장판 프리팹 컴포넌트
│       │
│       └── Interfaces/
│           ├── ICombatant.cs         # 전투 공통 인터페이스
│           ├── IProjectile.cs        # 투사체 인터페이스
│           ├── IPersistentArea.cs    # 장판 인터페이스
│           └── IPoolable.cs          # 풀링 공통
```

---

## 5. 타입 시스템 (SkillTypes.cs 전체)

```csharp
// 실행 단위
public delegate void SkillStep(SkillContext ctx);
// 조건 판정 단위
public delegate bool SkillCondition(SkillContext ctx);

public enum AreaShape    { Circle, Cone, Line }
public enum TargetType   { Single, Area, Self, Direction }
public enum MoveType     { Dash, Charge, Jump, Rope }

public enum ParryRewardType
{
    Counter,      // 공격자에게 반격 피해
    HitStun,      // 공격자에게 경직 부여
    Invulnerable, // 시전자에게 무적 부여
    Buff,         // 시전자에게 DamageUp 버프 부여
}

public enum StatusType
{
    Stunned,        // 이동+행동 불가
    HitStun,        // 짧은 경직
    Slowed,         // 이동속도 감소
    Rooted,         // 이동 불가 (행동 가능)
    Vulnerable,     // 받는 피해 증가
    Silence,        // 스킬 사용 불가
    Invulnerable,   // 피해 무효
    Reflecting,     // 받는 피해 반사
    HPRegen,        // 초당 HP 회복
    DamageOverTime, // 초당 피해 (DoT)
    AntiHeal,       // 회복량 감소
    Marked,         // 추가 피해 취약 표식
}

public enum BuffType
{
    DamageUp,      // 공격력 증가
    DefenseUp,     // 방어력 증가
    ParryWindowUp, // 패링 유효 시간 증가
    ParryRewardUp, // 패링 보상 강화
}

public enum DebuffType
{
    DamageDown,      // 공격력 감소
    DefenseDown,     // 방어력 감소
    SelfDefenseDown, // 자기 방어력 감소 (자해형)
    Mark,            // 취약 표식
}

public enum CleanseType
{
    All,            // 모든 상태이상
    Debuff,         // 디버프 계열만
    DamageOverTime, // DoT만
}

public enum DispelType
{
    All,         // 모든 버프
    DefenseBuff, // 방어 버프만
    OffenseBuff, // 공격 버프만
}
```

---

## 6. ICombatant 인터페이스 (전체)

```csharp
public interface ICombatant
{
    // ── 참조 ──
    Transform  Transform  { get; }
    GameObject GameObject { get; }

    // ── 상태 읽기 ──
    float MaxHP            { get; }
    float CurrentHPPercent { get; }   // 0~1
    float Shield           { get; }
    bool  IsAlive          { get; }
    bool  IsCasting        { get; }
    bool  IsParrying       { get; }
    float ParryWindow      { get; }

    // ── 피해 / 회복 ──
    void TakeDamage(float amount, ICombatant attacker = null);
    void TakeShieldBreakDamage(float amount, float multiplier, ICombatant attacker = null);
    void RecoverHP(float amount);
    void AddShield(float amount);

    // ── 상태이상 ──
    void ApplyStatus(StatusType type, float duration, float value = 0f);
    bool HasStatus(StatusType type);

    // ── 버프 / 디버프 ──
    void ApplyBuff  (BuffType   type, float duration, float value);
    void ApplyDebuff(DebuffType type, float duration, float value);

    // ── 정화 / 버프 제거 ──
    void RemoveStatuses(CleanseType type, int count);
    void RemoveBuffs   (DispelType  type, int count);

    // ── 위치 제어 ──
    void Knockback(Vector3 direction, float distance);
    void Pull(Vector3 towardPosition, float distance, float duration);
    void MoveBy(Vector3 direction, float distance, float duration, MoveType moveType);

    // ── 패링 보상 ──
    void NotifyParryReward(ParryRewardType rewardType, float value, float duration,
                           ICombatant attacker = null);
}
```

---

## 7. SkillContext (전체 필드)

```csharp
public class SkillContext
{
    // 시전자 / 대상
    public ICombatant       Caster;
    public ICombatant       PrimaryTarget;
    public List<ICombatant> TargetList = new();

    // 위치 / 방향
    public Vector3 CastPosition;
    public Vector3 CastDirection;

    // 판정 결과 (DealDirectionalHit/CheckParry/LaunchProjectile이 기록)
    public bool HitLanded;

    // 대상 스냅샷 (RefreshSnapshot 호출 시점 기준)
    public float TargetHpPercent;  // 0~1
    public float TargetDistance;   // Caster ↔ PrimaryTarget 거리
    public bool  TargetCasting;

    // 패링 입력 시각
    public float ParryInputTime;

    // 시간
    public float CurrentTime;

    // 로그
    public void AddLog(string msg);
    public IReadOnlyList<string> GetLog();

    // 스냅샷 갱신 — PrimaryTarget 변경 시 호출
    public void RefreshSnapshot();
}
```

---

## 8. ScriptableObject 스탯 구조

### BaseStatsSO (공통 베이스)

```csharp
public class BaseStatsSO : ScriptableObject
{
    public float DamageTakenMultiplier = 1f;
    public float HealingReceivedMultiplier = 1f;
    public float MoveControlMultiplier = 1f;
    public float RopeCancelResistance = 0f;
    public float SkillCooldownMultiplier = 1f;
    public float ChannelDurationMultiplier = 1f;
    public float SpawnInvulnerableDuration = 0f;
    public float StunDurationMultiplier = 1f;
    public float CrowdControlPower = 1f;
    public float CrowdControlResistance = 0f;
    public float HitStunResistance = 0f;
    public float DebuffDurationResistance = 0f;
    public float DamageUpMultiplier = 1f;
    public float DefenseUpMultiplier = 1f;
    public float VulnerabilityBonus = 0f;
    public float ReflectRatio = 0f;
}
```

### PlayerStatsSO (: BaseStatsSO)

```csharp
public class PlayerStatsSO : BaseStatsSO
{
    public float MaxHP = 100f;           public float CurrentHP = 100f;
    public float BaseDamage = 10f;       public float BaseDefense = 5f;
    public float MoveSpeed = 5f;         public float TurnSpeed = 180f;
    public float ActionSpeed = 1f;
    public float MoveAcceleration = 10f; public float MoveDeceleration = 10f;
    public float RopeRange = 10f;        public float RopeSpeed = 15f;
    public float RopeCooldown = 5f;      public float RopeAttachTime = 0.2f;
    public float RopeReleaseRecovery = 0.5f;
    public float AttackAreaScale = 1f;   public float SkillPower = 1f;
    public float ParryWindow = 0.3f;     public float ParryCooldown = 2f;
    public float CounterWindow = 0.5f;
    public float ShieldMax = 50f;        public float CurrentShield = 0f;
    public float HPRegenRate = 1f;       public float ReviveTime = 5f;
    public float AggroWeight = 1f;
}
```

### BossStatsSO (: BaseStatsSO)

```csharp
public class BossStatsSO : BaseStatsSO
{
    public float BossMaxHP = 1000f;
    public float BossCurrentHP = 1000f;
    public float BossBaseDamage = 50f;
    public float BossBaseDefense = 20f;
    public float[] BossPhaseThresholds;   // 예: [0.75, 0.5, 0.25]
    public float BossTelegraphTimeMultiplier = 1f;
    public float BossAggroSensitivity = 1f;
}
```

---

## 9. StatsManager API 전체

```csharp
public class StatsManager : MonoBehaviour
{
    // Awake에서 Instantiate로 SO 런타임 복사본 생성

    // ── 조회 ──
    float GetPlayerHP();           float GetPlayerMaxHP();
    float GetPlayerHPPercent();    float GetPlayerShield();
    float GetBossHP();             float GetBossMaxHP();
    float GetBossHPPercent();
    float GetPlayerMoveControl();  float GetBossMoveControl();
    float GetPlayerReflectRatio();
    bool  HasStatusPlayer(StatusType);  bool HasStatusBoss(StatusType);

    // ── 피해 ──
    void ApplyDamageToPlayer(float damage);  // Shield 우선 소진
    void ApplyDamageToBoss(float damage);
    void TakeShieldBreakDamagePlayer(float amount, float multiplier);
    void TakeShieldBreakDamageBoss(float amount, float multiplier);

    // ── 회복 / 실드 ──
    void RecoverHPPlayer(float amount);  // HealingReceivedMultiplier 반영
    void RecoverHPBoss(float amount);
    void AddShieldPlayer(float amount);  // ShieldMax 클램프

    // ── 상태이상 ── (코루틴 자동 해제)
    void ApplyStatusPlayer(StatusType, float duration, float value = 0f);
    void ApplyStatusBoss  (StatusType, float duration, float value = 0f);
    void RemoveStatusesPlayer(CleanseType, int count);
    void RemoveStatusesBoss  (CleanseType, int count);
    // 내부: CalcStatusDuration → StunDurationMultiplier / HitStunResistance / DebuffDurationResistance
    // 내부: HPRegen/DamageOverTime → WaitOneSec 캐싱된 1초 틱 루프

    // ── 버프 ──
    void ApplyBuffPlayer(BuffType, float duration, float value);
    void ApplyBuffBoss  (BuffType, float duration, float value);
    void RemoveBuffsPlayer(DispelType, int count);
    void RemoveBuffsBoss  (DispelType, int count);

    // ── 디버프 ──
    void ApplyDebuffPlayer(DebuffType, float duration, float value);
    void ApplyDebuffBoss  (DebuffType, float duration, float value);

    // ── 페이즈 ──
    int GetBossPhase();  // BossPhaseThresholds 기반
}
```

### StatsManager 내부 동작 상세

| StatusType | ApplyStatusValue 동작 | Revert 동작 |
|------------|----------------------|-------------|
| Stunned/HitStun/Rooted | MoveControlMultiplier = 0 | 원본값 복원 |
| Slowed | MoveControlMultiplier *= (1 - value) | 원본값 복원 |
| Vulnerable | DamageTakenMultiplier += value | 원본값 복원 |
| Invulnerable | DamageTakenMultiplier = 0 | 원본값 복원 |
| Reflecting | ReflectRatio = value | 원본값 복원 |
| AntiHeal | HealingReceivedMultiplier *= (1 - value) | 원본값 복원 |
| Marked | VulnerabilityBonus += value | 원본값 복원 |
| HPRegen | 1초 틱 루프 → RecoverHP(value) | 자동 |
| DamageOverTime | 1초 틱 루프 → ApplyDamage(value) | 자동 |
| Silence | HasStatus 조회만 (행동 제한은 Controller에서) | 자동 |

| BuffType | ApplyBuffValue 동작 |
|----------|-------------------|
| DamageUp | DamageUpMultiplier += value / 100 |
| DefenseUp | DefenseUpMultiplier += value / 100 |
| ParryWindowUp | ParryWindow += 원본ParryWindow * (value / 100) |
| ParryRewardUp | (별도 필드 없음) |

| DebuffType | ApplyDebuffValue 동작 |
|------------|---------------------|
| DamageDown / SelfDefenseDown | DamageUpMultiplier -= value / 100 |
| DefenseDown | DamageTakenMultiplier += value / 100 |
| Mark | VulnerabilityBonus += value |

---

## 10. SkillComponents 37종 (코드 시그니처 전체)

### 규칙
- `using static SkillComponents;` 후 함수명으로 직접 호출
- `ctx.Caster`를 attacker로 전달하는 부품: DealDamage(#1), DealMultiHitDamage(#2), ExecuteBelowHP(#29), DealDirectionalHit(#35), DealShieldBreakDamage(#28)
- `ctx.PrimaryTarget`를 attacker로 전달하는 부품: ApplyParryReward(#24)
- SKILL_DESIGN.md의 LaunchProjectile 파라미터 순서는 `(사거리, 속도)` 이지만 코드 시그니처는 `(speed, range)` — **순서 반전 주의**

```csharp
// ── 기본 전투 ──
SkillStep DealDamage(float amount)
    // → ctx.PrimaryTarget.TakeDamage(amount, ctx.Caster)

SkillStep DealMultiHitDamage(float amount, int hits)
    // → TakeDamage × hits회, 각각 ctx.Caster 전달

SkillStep ApplyDamageOverTime(float duration, float dps)
    // → ctx.PrimaryTarget.ApplyStatus(DamageOverTime, duration, dps)

SkillStep DealDirectionalHit(float damage, float range, float angleDeg, int layerMask = -1)
    // → OverlapSphere(origin, range) → 각도 필터 → TakeDamage(damage, ctx.Caster)
    // → ctx.HitLanded = anyHit, ctx.PrimaryTarget = 마지막 적중 대상

// ── 생존 ──
SkillStep RecoverHP(float amount)                           // → ctx.Caster.RecoverHP
SkillStep ApplyHPRegen(float duration, float perSecond)     // → ctx.Caster.ApplyStatus(HPRegen)
SkillStep GainShield(float amount)                          // → ctx.Caster.AddShield
SkillStep ReflectDamage(float duration, float ratio)        // → ctx.Caster.ApplyStatus(Reflecting)
SkillStep ApplyInvulnerability(float duration)              // → ctx.Caster.ApplyStatus(Invulnerable)

// ── 상태이상 ──
SkillStep ApplyStun(float duration)                         // → ctx.PrimaryTarget.ApplyStatus(Stunned)
SkillStep ApplyHitStun(float duration)                      // → ctx.PrimaryTarget.ApplyStatus(HitStun)
SkillStep ApplySlow(float duration, float ratio)            // → ctx.PrimaryTarget.ApplyStatus(Slowed, ratio)
SkillStep ApplyRoot(float duration)                         // → ctx.PrimaryTarget.ApplyStatus(Rooted)
SkillStep ApplyVulnerability(float duration, float ratio)   // → ctx.PrimaryTarget.ApplyStatus(Vulnerable, ratio)
SkillStep ApplySilence(float duration)                      // → ctx.PrimaryTarget.ApplyStatus(Silence)
SkillStep ApplyAntiHeal(float duration, float ratio)        // → ctx.PrimaryTarget.ApplyStatus(AntiHeal, ratio)

// ── 능력 변화 ──
SkillStep ApplyDamageUp(float duration, float ratio)        // → ctx.Caster.ApplyBuff(DamageUp)
SkillStep ApplyDamageDown(float duration, float ratio)      // → ctx.PrimaryTarget.ApplyDebuff(DamageDown)
SkillStep ApplyDefenseUp(float duration, float ratio)       // → ctx.Caster.ApplyBuff(DefenseUp)
SkillStep ApplyDefenseDown(float duration, float ratio)     // → ctx.PrimaryTarget.ApplyDebuff(DefenseDown)
SkillStep ApplyBuff(float duration, BuffType type, float value)     // → ctx.Caster.ApplyBuff
SkillStep ApplyDebuff(float duration, DebuffType type, float value) // → ctx.PrimaryTarget.ApplyDebuff

// ── 위치 제어 ──
SkillStep ApplyKnockback(float distance)                    // → ctx.PrimaryTarget.Knockback
SkillStep PullTarget(float distance, float duration)        // → ctx.PrimaryTarget.Pull
SkillStep MoveSelf(float distance, float duration, MoveType moveType) // → ctx.Caster.MoveBy

// ── 방어 대응 / 처형 / 해제 ──
SkillStep DealShieldBreakDamage(float amount, float multiplier)
    // → ctx.PrimaryTarget.TakeShieldBreakDamage(amount, multiplier, ctx.Caster)

SkillStep ExecuteBelowHP(float hpThreshold, float bonusDamage)
    // → TargetHpPercent*100 < hpThreshold 이면 TakeDamage(bonusDamage, ctx.Caster)

SkillStep CleanseStatus(CleanseType type, int count)        // → ctx.Caster.RemoveStatuses
SkillStep DispelBuff(DispelType type, int count)            // → ctx.PrimaryTarget.RemoveBuffs

// ── 패링 ──
SkillStep CheckParry()
    // → (Time.time - ctx.ParryInputTime) <= ctx.Caster.ParryWindow 이면 ctx.HitLanded = true

SkillStep ApplyParryReward(ParryRewardType type, float value, float duration)
    // → ctx.Caster.NotifyParryReward(type, value, duration, ctx.PrimaryTarget)

// ── 범위 래퍼 ──
SkillStep ApplyInArea(float radius, AreaShape shape, SkillStep inner,
                      float angleDeg = 360f, float lineWidth = 0.5f, int layerMask = -1)
    // → OverlapSphere(ctx.CastPosition, radius) → shape 필터 → inner.Invoke per target

SkillStep SpawnPersistentArea(float duration, float radius, AreaShape shape,
                              float tickInterval, SkillStep tickAction, float angleDeg = 360f)
    // → PersistentAreaManager.Instance.Spawn → SkillArea 틱 루프

// ── 투사체 래퍼 ──
SkillStep LaunchProjectile(float speed, float range, bool pierce, SkillStep onImpact)
    // → ProjectilePool.Instance.Get → SetHitCallback(onImpact, ctx, pierce) → Launch
    // ⚠ 기획서 파라미터 순서: (사거리, 속도) ↔ 코드: (speed, range) — 순서 반전

// ── 흐름 제어 ──
SkillStep TriggerOnCondition(string name, SkillCondition condition,
                             SkillStep onTrue, SkillStep onFalse = null)
    // → condition(ctx) ? onTrue : onFalse

SkillStep TriggerOnHit(SkillStep onHit, SkillStep onMiss = null)
    // → ctx.HitLanded ? onHit : onMiss

// ── 감지 (SkillCondition 반환) ──
SkillCondition CheckTargetDistance(float minDistance, float maxDistance)
    // → ctx.TargetDistance >= min && ctx.TargetDistance <= max
```

---

## 11. SkillDefinition / SkillExecutor / SkillRegistry

### SkillDefinition (ScriptableObject)

```csharp
[CreateAssetMenu(menuName = "Tenebris/SkillDefinition")]
public class SkillDefinition : ScriptableObject
{
    public string     SkillId;
    public string     DisplayName;
    public string     Description;
    public Sprite     Icon;
    public float      Cooldown;
    public float      Range;
    public TargetType TargetType;
    public string[]   RoleTags;      // 스킬 성격 태그
    public string[]   CounterTags;   // 카운터 대상 태그

    [NonSerialized] public SkillStep RuntimeStep;  // SkillLibrary에서 주입
    public bool IsReady => RuntimeStep != null;
}
```

### SkillExecutor (MonoBehaviour)

```csharp
public class SkillExecutor : MonoBehaviour
{
    bool  CanUse(SkillDefinition skill);              // 쿨타임 확인
    float GetRemainingCooldown(SkillDefinition skill);
    bool  Execute(SkillDefinition skill, SkillContext ctx); // RuntimeStep.Invoke
    void  ResetCooldown(string skillId);              // 패링 보상 등
}
```

### SkillRegistry (ScriptableObject)

```csharp
[CreateAssetMenu(menuName = "Tenebris/SkillRegistry")]
public class SkillRegistry : ScriptableObject
{
    SkillDefinition        Get(string skillId);
    List<SkillDefinition>  GetAll();
    List<SkillDefinition>  GetByRoleTag(string tag);
    List<SkillDefinition>  GetCounterCandidates(string[] playerRoleTags, int count = 3);
    List<SkillDefinition>  GetDraftCandidates(List<string> ownedIds, int count = 3);
}
```

---

## 12. 풀링 시스템

### ProjectilePool (싱글턴)

```csharp
public class ProjectilePool : MonoBehaviour
{
    public static ProjectilePool Instance { get; }
    SkillProjectile Get(Vector3 position, Quaternion rotation);  // 풀에서 꺼내기
    void            Return(SkillProjectile projectile);          // 풀 반환
}
```

### SkillProjectile (프리팹 컴포넌트)

```csharp
[RequireComponent(typeof(Rigidbody), typeof(Collider))]
public class SkillProjectile : MonoBehaviour, IProjectile
{
    void Launch(Vector3 direction, float speed, float range);
    void SetHitCallback(SkillStep onHit, SkillContext ctx, bool pierce);
    // OnTriggerEnter → ICombatant 탐색 → ctx.PrimaryTarget 설정 → onHit.Invoke
    // !pierce 시 풀 반환 / 사거리 초과 시 풀 반환
}
```

### PersistentAreaManager (싱글턴)

```csharp
public class PersistentAreaManager : MonoBehaviour
{
    public static PersistentAreaManager Instance { get; }
    [SerializeField] private PersistentAreaPool _pool;

    void Spawn(Vector3 position, Vector3 forward, float radius,
               AreaShape shape, float angleDeg,
               float duration, float tickInterval,
               SkillStep tickEffect, SkillContext ctx);
}
```

### SkillArea (장판 프리팹 컴포넌트)

```csharp
public class SkillArea : MonoBehaviour, IPersistentArea
{
    void Initialize(Vector3 forward, float radius, AreaShape shape, float angleDeg,
                    float duration, float tickInterval, SkillStep tickEffect, SkillContext ctx);
    // 내부: 코루틴 틱 루프 → OverlapSphere → shape 필터 → tickEffect.Invoke
    // duration 경과 후 자동 풀 반환
}
```

### 인터페이스

```csharp
public interface IPoolable { void OnSpawn(); void OnDespawn(); }
public interface IProjectile : IPoolable
{
    void Launch(Vector3 direction, float speed, float range);
    void SetHitCallback(SkillStep onHit, SkillContext ctx, bool pierce);
}
public interface IPersistentArea : IPoolable
{
    void Initialize(Vector3 forward, float radius, AreaShape shape, float angleDeg,
                    float duration, float tickInterval, SkillStep tickEffect, SkillContext ctx);
}
```

---

## 13. GameManager

```csharp
public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; }

    IReadOnlyList<GameObject> Players { get; }
    IReadOnlyList<GameObject> Bosses  { get; }
    float ElapsedTime { get; }

    GameObject Player1 { get; }  // Players[0]
    GameObject Player2 { get; }  // Players[1]
    GameObject Boss    { get; }  // Bosses[0]

    void RegisterPlayer(GameObject);    void UnregisterPlayer(GameObject);
    void RegisterBoss(GameObject);      void UnregisterBoss(GameObject);
    void StartTimer();  void StopTimer();  void ResumeTimer();
}
```

---

## 14. PlayerController ICombatant 구현 요약

```csharp
[RequireComponent(typeof(Rigidbody))]
public class PlayerController : MonoBehaviour, ICombatant
{
    public PlayerStatsSO playerStats;       // SO 참조
    public StatsManager  statsManager;      // 인스펙터 연결
    [SerializeField] private GameManager _gameManager;

    // 이동: Rigidbody.MovePosition, MoveSpeed * statsManager.GetPlayerMoveControl()
    // HandleActions(): 현재 Debug.Log만 — SkillExecutor 연동 필요

    // TakeDamage:
    //   isParrying && attacker → attacker.TakeDamage (임시 반격)
    //   Reflecting && attacker → attacker.TakeDamage(amount * ReflectRatio)
    //   statsManager.ApplyDamageToPlayer(amount)

    // NotifyParryReward: 4종 전부 구현
    //   Counter     → attacker.TakeDamage(value)
    //   HitStun     → attacker.ApplyStatus(HitStun, duration)
    //   Invulnerable → statsManager.ApplyStatusPlayer(Invulnerable, duration)
    //   Buff        → statsManager.ApplyBuffPlayer(DamageUp, duration, value)

    // 위치 제어:
    //   Knockback → rb.AddForce(Impulse)
    //   Pull/MoveBy → 코루틴 Lerp
}
```

---

## 15. BossController ICombatant 구현 요약

```csharp
[RequireComponent(typeof(NavMeshAgent))]
public class BossController : MonoBehaviour, ICombatant
{
    public BossStatsSO  bossStats;
    public StatsManager statsManager;
    [SerializeField] private GameManager _gameManager;
    public Transform playerTarget;

    // Shield → 0f (보스 실드 없음)
    // ParryWindow → 0f (보스 패링 없음)
    // NotifyParryReward → 빈 구현

    // TakeDamage → statsManager.ApplyDamageToBoss
    // HandlePhase → HP% 기반 페이즈 전환 (BossPhaseThresholds)
    // TrackPlayer → NavMeshAgent, speed *= statsManager.GetBossMoveControl()

    // 위치 제어: 전부 NavMeshAgent.Warp
    //   Knockback → Warp(position + dir * distance)
    //   Pull → Warp(toward direction)
    //   MoveBy → Warp(direction * distance)
}
```

---

## 16. SkillLibrary 현재 코드 (2종 완성)

```csharp
using static SkillComponents;

public static class SkillLibrary
{
    // ═══ 보스 공용 — 침식 장판 ═══
    // 시전 위치에 2중 원형 장판 생성
    // 내부(1.2m): DoT 7/s + 치유감소 20%   4초 지속, 1초 틱
    // 외부(3.7m): DoT 7/s                   4초 지속, 1초 틱
    public static SkillStep ErosionField_Boss() =>
        ctx =>
        {
            SpawnPersistentArea(4f, 1.2f, AreaShape.Circle, 1f,
                tick =>
                {
                    ApplyDamageOverTime(1f, 7f).Invoke(tick);
                    ApplyAntiHeal(1f, 0.20f).Invoke(tick);
                }
            ).Invoke(ctx);

            SpawnPersistentArea(4f, 3.7f, AreaShape.Circle, 1f,
                tick =>
                {
                    ApplyDamageOverTime(1f, 7f).Invoke(tick);
                }
            ).Invoke(ctx);
        };

    // ═══ 플레이어 공용 — 봉쇄 사슬 ═══
    // 유도 투사체 발사, 적중 시 70 피해 + 경직 0.08초 + 침묵 0.5초
    // 속도 13, 사거리 8, 비관통
    public static SkillStep SealChain() =>
        LaunchProjectile(13f, 8f, false,
            hit =>
            {
                DealDamage(70f).Invoke(hit);
                ApplyHitStun(0.08f).Invoke(hit);
                ApplySilence(0.5f).Invoke(hit);
            }
        );
}
```

---

## 17. 스킬 기획 — 전체 조합식

### 플레이어 공용 (13종)

| 이름 | 쿨타임 | 조합식 |
|------|--------|--------|
| 처형 송곳 | 8초 | `DealDirectionalHit(125,2.0,30)` → `TriggerOnHit([ApplyVulnerability(2,5), ExecuteBelowHP(30,20)])` → `TriggerOnCondition(NoHit,[DealDirectionalHit(125,2.4,70)])` |
| 분쇄 연타 | 6초 | `DealDirectionalHit(34,1.8,35)` → `DealMultiHitDamage(34,4)` → `TriggerOnHit([DealShieldBreakDamage(45,1.2)])` → `TriggerOnCondition(NoHit,[DealDirectionalHit(34,2.2,75), DealMultiHitDamage(34,4)])` |
| 침식 장판 | 10초 | `LaunchProjectile(7,12,false,true,[SpawnPersistentArea(4,1.0,원,1,[ApplyDamageOverTime(1,8), ApplyAntiHeal(1,20)]), SpawnPersistentArea(4,3.4,원,1,[ApplyDamageOverTime(1,8)])])` |
| 사냥 표식 | 7초 | `LaunchProjectile(8,14,false,false,[DealDamage(80), ApplyDebuff(4,Mark,1)])` |
| 생존 맥동 | 14초 | `TriggerOnCondition(LowHP,[RecoverHP(최대HP의6%), ApplyHPRegen(3,최대HP의1.2%), CleanseStatus(전체,1)])` |
| 요새 장갑 | 8초 | `DealDirectionalHit(90,1.9,35)` → `TriggerOnHit([GainShield(최대HP의6%)])` → `TriggerOnCondition(NoHit,[DealDirectionalHit(90,2.3,75)])` |
| 봉쇄 사슬 | 9초 | `LaunchProjectile(8,13,false,false,[DealDamage(70), ApplyHitStun(0.08), ApplySilence(0.5)])` |
| 붕괴 포효 | 10초 | `ApplyInArea(1.4,원,[DealDamage(95), ApplyDefenseDown(2,5)])` → `TriggerOnCondition(NoHit,[ApplyInArea(4.0,원,[DealDamage(95)])])` |
| 방벽 파쇄 | 8초 | `LaunchProjectile(7,12,false,false,[DealShieldBreakDamage(60,1.4), ApplyDefenseDown(3,6), DealDamage(105)])` |
| 과충전 모드 | 18초 | `TriggerOnCondition(CombatPhaseOrLowHP,[ApplyDamageUp(6,15), ApplyDebuff(6,SelfDefenseDown,10)])` |
| 관통 저격 | 10초 | `LaunchProjectile(10,16,true,false,[ApplyDefenseDown(3,8), DealDamage(165)])` → `TriggerOnCondition(NoCoreHit,[LaunchProjectile(10,16,true,false,[DealDamage(165)])])` |
| 파열 탄창 | 9초 | `LaunchProjectile(8,13,false,true,[ApplyVulnerability(3,10), DealDamage(135)])` → `TriggerOnCondition(NoCoreHit,[LaunchProjectile(8,13,false,true,[DealDamage(135)])])` |

> **참고**: LaunchProjectile 기획서 표기 `(사거리, 속도)` → 코드 `(speed, range)` 순서 반전

### 플레이어 전용 트리거형 (6종)

| 이름 | 쿨타임 | 조합식 |
|------|--------|--------|
| 응수 태세 | 8초 | `TriggerOnCondition(CheckParry(),[ApplyParryReward(Counter,200,0), ApplyParryReward(HitStun,0.20,0), ApplyParryReward(Invulnerable,0.15,0)])` |
| 패링 강화 | 12초 | `ApplyBuff(5,ParryWindowUp,15)` → `ApplyBuff(5,ParryRewardUp,10)` |
| 반격의 일섬 | 10초 | `TriggerOnCondition(CheckParry(),[ApplyParryReward(Counter,230,0), ApplyParryReward(Invulnerable,0.15,0)])` |
| 와이어 훅 | 6초 | `MoveSelf(9,시간,Rope)` → `TriggerOnCondition(RopeLanding,[ApplyInArea(0.6,원,[DealDamage(80), ApplyHitStun(0.08)]), TriggerOnCondition(NoHit,[ApplyInArea(1.2,원,[DealDamage(80)])])])` |
| 로프 충격파 | 9초 | `TriggerOnCondition(RopeLanding,[ApplyInArea(0.8,원,[DealDamage(75), ApplyKnockback(1.2)]), TriggerOnCondition(NoHit,[ApplyInArea(1.8,원,[DealDamage(75)])])])` |
| 붕괴 타격 | 18초 | `TriggerOnCondition(ParrySuccessRecent,[DealDirectionalHit(120,1.5,25), TriggerOnHit([ApplyStun(0.35)]), TriggerOnCondition(NoHit,[DealDirectionalHit(120,2.0,60)])])` |

### 보스 공용 (12종)

| 이름 | 쿨타임 | 조합식 |
|------|--------|--------|
| 처형 송곳 | 8초 | `DealDirectionalHit(118,2.2,35)` → `TriggerOnHit([ApplyVulnerability(2.5,6), ExecuteBelowHP(30,26)])` → `TriggerOnCondition(NoHit,[DealDirectionalHit(118,2.7,75)])` |
| 분쇄 연타 | 6초 | `DealDirectionalHit(32,2.0,40)` → `DealMultiHitDamage(32,4)` → `TriggerOnHit([DealShieldBreakDamage(55,1.35)])` → `TriggerOnCondition(NoHit,[DealDirectionalHit(32,2.5,80), DealMultiHitDamage(32,4)])` |
| 침식 장판 | 10초 | `SpawnPersistentArea(4,1.2,원,1,[ApplyDamageOverTime(1,7), ApplyAntiHeal(1,20)])` → `SpawnPersistentArea(4,3.7,원,1,[ApplyDamageOverTime(1,7)])` |
| 생존 맥동 | 14초 | `TriggerOnCondition(LowHP,[RecoverHP(최대HP의5%), ApplyHPRegen(3,최대HP의1.0%), CleanseStatus(전체,1)])` |
| 요새 장갑 | 8초 | `DealDirectionalHit(82,2.1,35)` → `TriggerOnHit([GainShield(최대HP의8%)])` → `TriggerOnCondition(NoHit,[DealDirectionalHit(82,2.6,80)])` |
| 붕괴 포효 | 10초 | `ApplyInArea(1.6,원,[DealDamage(88), ApplyHitStun(0.16), ApplyDefenseDown(3,6)])` → `TriggerOnCondition(NoHit,[ApplyInArea(4.4,원,[DealDamage(88)])])` |
| 과충전 모드 | 18초 | `TriggerOnCondition(CombatPhaseOrLowHP,[ApplyDamageUp(6,12), ApplyDebuff(6,SelfDefenseDown,12)])` |
| 표식 파동 | 8초 | `ApplyInArea(5,Cone,[DealDamage(70), ApplyDebuff(4,Mark,1)],80)` |
| 봉쇄 사슬 | 10초 | `LaunchProjectile(7,11,false,false,[DealDamage(60), ApplyHitStun(0.10), ApplySilence(0.7)])` |
| 방벽 파쇄 | 9초 | `LaunchProjectile(8,12,true,false,[DealDamage(90), DealShieldBreakDamage(70,1.5), ApplyDefenseDown(4,8)])` |
| 파열 탄창 | 9초 | `ApplyInArea(0.7,원,[LaunchProjectile(7,10,false,true,[ApplyVulnerability(2.5,6), DealDamage(75)])])` → `TriggerOnCondition(NoHit,[ApplyInArea(1.8,원,[LaunchProjectile(7,10,false,true,[DealDamage(75)])])])` |

> 보스 봉쇄 사슬은 4방향 발사 — SkillLibrary에서 반복문 또는 4회 호출

---

## 18. 역할 태그 / 카운터 관계

| 계열 | 약점 |
|------|------|
| Heal | AntiHeal |
| Shield | ShieldBreak |
| Parry | MultiHit, DOT, Zone |
| Mobility | Root, Pull, Catch |
| Burst | Invulnerable, Reflect, DefenseUp |
| Zone | Cleanse, Mobility |

---

## 19. 현재 구현 상태

### 완료

- 로비 생성/참가, 씬 전환
- 플레이어 스폰, 오너십 분리
- 이동/로프/카드 드래프트 동기화
- **StatsManager** 완전 구현 (HP/Shield/Status/Buff/Debuff/Duration 코루틴, ReflectRatio)
- **PlayerController** — ICombatant, 패링 반격/반사/NotifyParryReward 4종
- **BossController** — ICombatant, NavMeshAgent 기반
- **ICombatant** — attacker 파라미터 전체 적용
- **SkillComponents.cs** — 37종 전부 구현
- **SkillContext/SkillTypes** — dead field/enum 정리 완료
- **SkillDefinition/SkillExecutor/SkillRegistry** 구현
- **GameManager** 싱글턴 (플레이어/보스 리스트, 타이머)
- **ProjectilePool** + SkillProjectile
- **PersistentAreaManager** + PersistentAreaPool + SkillArea
- **IProjectile/IPersistentArea/IPoolable** 인터페이스
- **SkillLibrary** — 2종 (ErosionField_Boss, SealChain) 완성

### 미완성

| 항목 | 설명 |
|------|------|
| **SkillLibrary** | 29종 추가 조립 필요 (현재 2종만 완성) |
| **3D 전투 통합** | PlayerController.HandleActions() → SkillExecutor 연동, 스킬 슬롯, 입력→ctx→Execute 흐름 |
| **CardManager ↔ SkillRegistry** | 레거시 skillObjectName → SkillDefinition 기반 리팩토링 |
| **보스 FSM / 패턴** | 규칙 기반 스킬 발동 로직 |
| **보스전 UI** | HP 바, 스킬 쿨타임 아이콘 |
| **씬 배치** | GameManager, PersistentAreaManager+Pool, SkillArea 프리팹, SkillExecutor on Player, _gameManager 연결 |

### 씬에 누락된 오브젝트 (Chapter1.unity 분석 결과)

| 항목 | 상태 | 필요 조치 |
|------|------|----------|
| GameManager | **없음** | 빈 GameObject 생성 → GameManager 컴포넌트 추가 |
| PersistentAreaManager | **없음** | 빈 GameObject 생성 → 컴포넌트 추가 + PersistentAreaPool 연결 |
| PersistentAreaPool | **없음** | 빈 GameObject 생성 → SkillArea 프리팹 연결 |
| SkillArea 프리팹 | **없음** | 프리팹 생성 (SkillArea + Visual 자식) |
| SkillExecutor on Player | **없음** | PlayerController 오브젝트에 SkillExecutor 추가 |
| _gameManager (Player) | **미연결** | PlayerController._gameManager → GameManager 연결 |
| _gameManager (Boss) | **미연결** | BossController._gameManager → GameManager 연결 |
| ProjectilePool | **있음** | ProjectTile 프리팹 연결됨, initialSize=10 |
| StatsManager | **있음** | PlayerStatsSO/BossStatsSO 연결됨 |

---

## 20. 매니저 초기화 순서

| Order | Manager | 비고 |
|-------|---------|------|
| 0 | NetworkManager (NGO) | 모든 네트워크 기반 |
| 5 | StatsManager | 전투 단일 진실 공급원 |
| 10 | PoolManager | 투사체/장판 풀 프리워밍 |
| 15 | SkillRegistry | 스킬 풀 등록 |
| 20 | PersistentAreaManager | 장판 시스템 |

---

## 21. SkillLibrary 조립 규칙

### 조립 패턴

```csharp
using static SkillComponents;

public static class SkillLibrary
{
    // 단순 래퍼형 (투사체/장판 하나로 끝나는 스킬)
    public static SkillStep SkillName() =>
        LaunchProjectile(speed, range, pierce,
            hit =>
            {
                DealDamage(amount).Invoke(hit);
                ApplyHitStun(dur).Invoke(hit);
            }
        );

    // 복합형 (여러 부품을 순차 실행)
    public static SkillStep SkillName() =>
        ctx =>
        {
            Step1().Invoke(ctx);
            Step2().Invoke(ctx);
        };

    // 조건 분기형
    public static SkillStep SkillName() =>
        ctx =>
        {
            DealDirectionalHit(dmg, range, angle).Invoke(ctx);
            TriggerOnHit(
                hit => { /* 적중 시 */ },
                miss => { /* 빗나감 시 */ }
            ).Invoke(ctx);
        };
}
```

### 핵심 주의사항

1. **LaunchProjectile 파라미터 순서**: 기획서 `(사거리, 속도)` ↔ 코드 `(speed, range)` — **반드시 반전**
2. **중첩 Invoke 패턴**: 부품이 SkillStep을 반환하므로 `.Invoke(ctx)` 또는 `.Invoke(hit)` 호출 필요
3. **최대HP 참조 스킬**: RecoverHP(최대HP의6%) 등은 `ctx.Caster.MaxHP * 0.06f` 로 변환
4. **TriggerOnCondition의 조건**: `LowHP`, `NoHit`, `CombatPhaseOrLowHP` 등은 SkillCondition으로 작성 필요
5. **attacker 전달**: DealDamage 계열은 자동으로 `ctx.Caster` 전달, ApplyParryReward는 `ctx.PrimaryTarget` 전달

---

## 22. 개발 우선순위

1. SkillLibrary 나머지 29종 조립
2. 3D 전투 판정 통합 (HandleActions → SkillExecutor)
3. 보스 FSM / 패턴
4. CardManager ↔ SkillRegistry 연결
5. 보스전 UI
6. 씬 오브젝트 배치
7. 행동 편향 수집
8. ML-Agents 연동
