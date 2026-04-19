# 테네브리스 (Tenebris) — 게임 기획 및 기술 설계

## 프로젝트 기본 정보

| 항목 | 내용 |
|------|------|
| 코드명 | Arena Combat |
| 기획명 | 테네브리스 (Tenebris) |
| 장르 | 2인 협동 보스전 3D 탑다운 멀티플레이 액션 로그라이트 |
| Unity 버전 | 6000.3.11f1 (Unity 6) |
| 렌더 파이프라인 | URP 17.3.0 |
| 네트워크 | Unity NGO + Relay + Unity Transport (Host-authoritative) |
| ML | ML-Agents 4.0.2 |

---

## 기술 스택 (확정 패키지)

| 패키지 | 버전 | 용도 |
|--------|------|------|
| com.unity.inputsystem | 1.19.0 | 입력 처리 (New Input System) |
| com.unity.ml-agents | 4.0.2 | 보스 AI 학습 |
| com.unity.ai.navigation | 2.0.11 | 보스 NavMesh 이동 |
| com.unity.render-pipelines.universal | 17.3.0 | URP 렌더링 |
| com.unity.visualeffectgraph | 17.3.0 | VFX |
| com.unity.ugui | 2.0.0 | UI (현재 사용) |
| UniTask | **미설치** | 코루틴으로 대체 (WaitForSeconds 캐싱) |
| Addressables | **미설치** | 직접 프리팹 참조 사용 |

---

## 핵심 아키텍처 원칙

1. **StatsManager = 단일 진실 공급원**: 모든 스탯 변경은 StatsManager 경유
2. **Host-authoritative**: 클라이언트는 입력 의도만 전송, Host가 최종 판정
3. **ICombatant 인터페이스**: 전투 가능 객체(Player, Boss)는 반드시 구현
4. **ScriptableObject = 읽기 전용 템플릿**: SO는 초기값만 보관, Update 로직 없음
5. **SkillComponents = static class**: 스킬 부품은 SkillComponents.cs에만 추가
6. **2D 레거시 코드 기준 금지**: 3D Host-authoritative 경로 기준으로만 작업

---

## 네트워크 구조

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

- Host = 이동/전투/드래프트 최종 판정자
- 클라이언트 → Host : 입력 의도 RPC 전송
- Host → 클라이언트 : NetworkVariable 동기화

### 스킬 판정 네트워크 흐름

#### 위치 기반 판정 (즉발/범위/장판)
```
클라이언트: 스킬 발동 입력
    → ServerRpc("스킬 발동 요청")
호스트: GameManager 위치 참조 → 범위 내 대상 탐색 → TakeDamage 적용
    → NetworkVariable 동기화 → 모든 클라 반영
```

#### 투사체 판정
```
클라이언트: 발사 입력
    → ServerRpc("투사체 발사 요청") 1회 전송
호스트: SkillProjectile(NetworkObject) Spawn → 호스트가 이동/판정 전담
    → OnTriggerEnter 감지 → TakeDamage 직접 적용
클라이언트: NetworkTransform으로 투사체 위치 수신 → 렌더링만 담당
```

#### 원칙
- 클라이언트는 판정 권한 없음 — 입력 전송과 시각 피드백만 담당
- 투사체는 NetworkObject로 호스트가 소유 — 위치를 매 프레임 전송하지 않음
- 모든 TakeDamage/ApplyStatus는 호스트에서만 호출

---

## 플레이어 상태 구조 (3계층)

### Main State
`Idle` / `Move` / `Attack` / `Skill` / `Parry` / `Rope` / `Hit` / `Down` / `Dead` / `Respawn` / `Locked`

### Sub State
`None` / `Startup` / `Active` / `Recovery` / `Interrupted` / `Channeling` / `Attach` / `Pull` / `Release` / `Counter` / `Knockback` / `GetUp` / `Drafting` / `PhaseTransition`

### Status (중첩 가능)
`Stunned` / `Rooted` / `Slowed` / `Vulnerable` / `Invulnerable` / `Shielded` / `Reflecting` / `HPRegen` / `DamageOverTime` / `DamageUp` / `DefenseUp` / `Marked`

---

## 스탯 구조

```
PlayerStatsSO (읽기 전용 초기값 — ScriptableObject)
  └─ StatsManager.currentPlayerStats (런타임 복사본 — 여기서만 변경)

BossStatsSO (읽기 전용 초기값 — ScriptableObject)
  └─ StatsManager.currentBossStats (런타임 복사본 — 여기서만 변경)
```

변경 방법: `StatsManager.ApplyDamageToPlayer()`, `ApplyStatusToPlayer()` 등 전용 메서드만 사용

---

## PlayerStatManager (플레이어 개별 스탯 매니저) — 계획

### 목적
기존 모놀리스 `StatsManager` 에서 플레이어 부분을 **개별 컴포넌트로 분리**하고,
`PlayerController` 에 혼재된 **공격/패링/스탯** 로직을 한 곳으로 통합한다.

> 플레이어 1명당 1개의 `PlayerStatManager` 를 가진다. 보스 측은 추후 `BossStatManager` 로 분리 예정.

### 책임 분리

| 역할                         | 이전 위치               | 이후 위치              |
|------------------------------|-------------------------|------------------------|
| HP/Shield/버프/디버프/상태이상 | `StatsManager`(모놀리스) | `PlayerStatManager`    |
| isCasting / isParrying 플래그 | `PlayerController`      | `PlayerStatManager`    |
| 패링 윈도우 타이머            | `PlayerController`      | `PlayerStatManager`    |
| 반격 / 피해 반사              | `PlayerController`      | `PlayerStatManager`    |
| 자동 HP 재생                  | `PlayerController.Update` | `PlayerStatManager.Tick` |
| 공격 적용 (DealDamage)        | (없음)                  | `PlayerStatManager`    |
| 입력 / 이동 / 스킬 시전 트리거 | `PlayerController`      | `PlayerController`     |

### 피해 주고받기 플로우 (양방향 StatManager 호출)

```
[공격자] PlayerStatManager.DealDamage(target, raw)
    ├─ DamageUp 버프 반영 → adjusted
    └─ target.ICombatant.TakeDamage(adjusted, attacker)
            └─ [수신자] PlayerStatManager.ReceiveDamage(adjusted, attacker)
                  ├─ IsParrying → NotifyParryReward(...)
                  ├─ Reflecting → attacker.ReceiveDamage(adj × ReflectRatio)
                  ├─ DamageTakenMultiplier 적용
                  ├─ Shield 우선 소진 → HP
                  └─ HP == 0 → Die()
```

### 핵심 API (요약)

```csharp
public class PlayerStatManager : MonoBehaviour
{
    void Initialize(PlayerStatsSO baseStats);

    // 상태
    bool IsAlive, IsCasting, IsParrying;
    float GetHP(), GetMaxHP(), GetHPPercent(), GetShield();

    // 공격 — 이쪽에서 대상에게 줌
    void DealDamage(ICombatant target, float amount, DamageType type = DamageType.Normal);
    void DealShieldBreakDamage(ICombatant target, float amount, float multiplier);

    // 피해 — 대상에서 받음 (TakeDamage 내부에서 호출)
    void ReceiveDamage(float amount, ICombatant attacker);
    void ReceiveShieldBreakDamage(float amount, float multiplier, ICombatant attacker);

    // 패링
    void BeginParryWindow();      // WaitForSeconds 캐싱 코루틴
    void EndParryWindow();
    void NotifyParryReward(ParryRewardType, float value, float duration, ICombatant attacker);

    // 상태 / 버프 / 회복
    void ApplyStatus(StatusType, float duration, float value = 0f);
    void ApplyBuff(BuffType, float duration, float value);
    void ApplyDebuff(DebuffType, float duration, float value);
    void RemoveStatuses(CleanseType, int count);
    void RemoveBuffs(DispelType, int count);
    void RecoverHP(float amount);
    void AddShield(float amount);

    // 매 프레임
    void Tick(float dt);
}
```

### 구현 순서
1. `PlayerStatManager.cs` 신규 작성 (기존 StatsManager Player 부분 이관)
2. `DealDamage / ReceiveDamage` 쌍 추가
3. 패링 윈도우 코루틴 + isCasting/isParrying 플래그 이관
4. `PlayerController.ICombatant` 본체 전부 `_statManager` 위임으로 축소
5. 모놀리스 `StatsManager` 에서 Player 메서드 삭제 → Boss 부분만 남김
6. 컴파일 정리 → CHANGES.md / AI_SYSTEM.md 반영

---

## SkillManager (자동 시전 스킬 매니저) — 계획

### 목적
`PlayerSkillSlot` 을 확장해서 **쿨타임이 돌아오면 자동으로 사용**되는 시스템으로 교체.
플레이어 상태를 근거로 시전 가능 여부를 판정한다.

### 설계 원칙
- 슬롯 index 순서 = 우선순위 (낮을수록 먼저 시도)
- 자동 시전 기본 ON, 토글 시 수동 발동 API (`TryExecute`) 사용 가능
- `SkillExecutor` / `SkillContext` / `SkillDefinition` 구조 **재사용** (변경 X)

### 시전 가능 조건 (`CanCast`)

| 조건                        | 체크                                    |
|-----------------------------|-----------------------------------------|
| 쿨타임 만료                 | `SkillExecutor.CanUse(skill)`           |
| 플레이어 Alive              | `StatManager.IsAlive`                   |
| 시전 중 아님                | `!StatManager.IsCasting`                |
| 패링 중 아님                | `!StatManager.IsParrying`               |
| 경직/스턴/빙결/침묵 없음    | `!StatManager.HasStatus(...)`           |
| 타겟 존재 + 생존            | `target != null && target.IsAlive`      |
| 사거리 내                   | `distance(Caster, target) ≤ skill.Range`|

### 자동 시전 루프

```csharp
void Update()
{
    if (!_autoCastEnabled) return;

    foreach (var slot in _slots)   // 슬롯 순서 = 우선순위
    {
        if (!CanCast(slot, out var ctx)) continue;
        _executor.Execute(slot, ctx);
        break;                      // 한 프레임 1개만 발동
    }
}
```

### 핵심 API (요약)

```csharp
[RequireComponent(typeof(SkillExecutor))]
public class SkillManager : MonoBehaviour
{
    [SerializeField] int _maxSlots = 5;
    [SerializeField] bool _autoCastEnabled = true;

    int  Equip(SkillDefinition skill);
    bool Unequip(string skillId);
    void UnequipAll();

    int  Count { get; }
    IReadOnlyList<SkillDefinition> Slots { get; }
    bool CanUse(int slotIndex);
    float GetRemainingCooldown(int slotIndex);

    void SetAutoCast(bool enabled);
    bool TryExecute(int slotIndex, SkillContext ctx);   // 수동 발동 (디버그/예외)
    void ResetCooldown(int slotIndex);

    // 내부
    bool CanCast(SkillDefinition skill, out SkillContext ctx);
    SkillContext BuildSkillContext(ICombatant target);
    ICombatant FindNearestTarget();
}
```

### 구현 순서
1. `SkillManager.cs` 생성 — `PlayerSkillSlot` Equip/Unequip 로직 복사
2. `_statManager` / `_gameManager` 참조 직렬화
3. `CanCast(skill, out ctx)` 헬퍼 + `FindNearestTarget()` 구현
4. `Update()` 에 자동 시전 루프 추가
5. `PlayerController.HandleActions` 의 Q/W/E/R/T 수동 입력 제거
6. 기존 `PlayerSkillSlot` 을 `SkillManager` 로 치환 (또는 deprecated)
7. 테스트 → CHANGES.md / AI_SYSTEM.md 갱신

---

## 스킬 시스템 (조립형)

### 구조

```
SkillDefinition
  └─ SkillStep[] (delegate void(SkillContext ctx))
       ├─ Primitive: DealDamage, ApplyStun, GainShield ...
       └─ Wrapper:   TriggerOnHit, ApplyInArea, SpawnPersistentArea ...

SkillContext
  ├─ Caster (ICombatant)
  ├─ PrimaryTarget (ICombatant)
  ├─ TargetList
  ├─ CastPosition / CastDirection
  ├─ HitLanded / TargetHpPercent
  └─ RuntimeLog
```

### 스킬 부품 37종 (SkillComponents.cs)

| 분류 | 부품 |
|------|------|
| 기본 전투 | DealDamage, DealMultiHitDamage, ApplyDamageOverTime, DealDirectionalHit |
| 생존 | RecoverHP, ApplyHPRegen, GainShield, ReflectDamage, ApplyInvulnerability |
| 상태 이상 | ApplyStun, ApplyHitStun, ApplySlow, ApplyRoot, ApplyVulnerability, ApplySilence |
| 능력 변화 | ApplyDamageUp, ApplyDamageDown, ApplyDefenseUp, ApplyDefenseDown, ApplyAntiHeal |
| 위치 제어 | ApplyKnockback, PullTarget, MoveSelf |
| 방어 대응 | DealShieldBreakDamage, ExecuteBelowHP, CleanseStatus, DispelBuff |
| Wrapper | ApplyBuff, ApplyDebuff, TriggerOnCondition, TriggerOnHit |
| 범위/투사체 | ApplyInArea, SpawnPersistentArea, LaunchProjectile |
| 핵심 시스템 | CheckParry, ApplyParryReward |
| 감지(Condition) | CheckTargetDistance |

### 스킬 적중 판정 방식

#### 기본 원칙
- 모든 위치 기반 판정은 **GameManager를 통해 보스/플레이어 위치를 참조**
- 스킬 사용 시 시전자 위치 기준으로 범위 계산 → 범위 내에 상대 오브젝트가 존재하면 적중
- 투사체(LaunchProjectile) 판정만 예외 — 발사 노트 충돌 이벤트(OnTriggerEnter) 기준

#### 판정 종류별 구조

| 판정 종류 | 부품 | 위치 참조 방식 |
|-----------|------|---------------|
| 즉발 근접 | DealDirectionalHit | ctx.Caster 위치 기준 OverlapSphere → 각도 필터 |
| 범위 | ApplyInArea (Circle/Cone/Line) | ctx.CastPosition 기준 OverlapSphere → shape 필터 |
| 지속 장판 | SpawnPersistentArea | 생성 지점 기준 틱마다 OverlapSphere |
| 투사체 | LaunchProjectile | **예외 — OnTriggerEnter 충돌 이벤트** |

#### SkillContext 위치 주입 흐름
```
스킬 발동
  → ctx.CastPosition  = GameManager.Instance.Boss/Player 위치 (또는 시전자 위치)
  → ctx.CastDirection = 시전자 전방 방향
  → SkillExecutor.Execute(skill, ctx)
  → 각 부품이 ctx.CastPosition 기준으로 범위 내 ICombatant 탐색 후 적용
```

#### 대상 탐색 규칙
- 플레이어가 시전 → GameManager.Bosses 목록에서 범위 내 대상 탐색
- 보스가 시전 → GameManager.Players 목록에서 범위 내 대상 탐색
- 자기 자신(ctx.Caster)은 항상 제외

---

### 역할 태그 / 카운터 관계

| 계열 | 약점 |
|------|------|
| Heal | AntiHeal |
| Shield | ShieldBreak |
| Parry | MultiHit, DOT, Zone |
| Mobility | Root, Pull, Catch |
| Burst | Invulnerable, Reflect, DefenseUp |
| Zone | Cleanse, Mobility |

---

## 보스 AI

### FSM 구조
`Idle` → `Approach` → `AttackPattern` → `Cooldown` → 반복
HP% 기반 페이즈 전환 (`StatsManager.GetBossHPPercent()`)

### 행동 편향 분류 (9종)
근접 선호 / 원거리 유지 / 공격 집중 / 생존 우선 / 패링 의존 / 로프 기동 / 스킬 중심 / 팀 밀착 / 팀 분산

### AI 구현 단계
1. FSM + 규칙 기반 대응 (현재 목표)
2. 플레이어 행동 데이터 수집 → 편향 점수화 → 패턴 가중치 적용
3. ML-Agents 연동 (보스 위치/이동 학습, 스킬 발동은 규칙 유지)
   - 학습/테스트용 봇: Behavior Tree 기반 플레이어 봇 먼저 구성

---

## 현재 구현 상태

### 완료
- 로비 생성·참가, 씬 전환
- 플레이어 스폰, 오너십 분리
- 이동 동기화, 로프 동기화
- 카드 드래프트 동기화
- StatsManager 완전 구현 (HP/Shield/Status/Buff/Debuff/Duration 코루틴, ReflectRatio)
- PlayerController — ICombatant 구현, 패링 반격/피해 반사/NotifyParryReward 4종 구현
- BossController — ICombatant 구현, attacker 파라미터 시그니처 완료
- ICombatant — TakeDamage/TakeShieldBreakDamage/NotifyParryReward에 attacker 파라미터 추가
- SkillComponents.cs — 37종 전부 구현 완료
- SkillContext / SkillTypes — dead field(RecentDamageTaken) 및 dead enum(CastingCheckType) 제거
- SkillDefinition / SkillExecutor / SkillRegistry 구현
- GameManager 싱글턴 구현 (플레이어/보스 리스트, 타이머)
- ProjectilePool 싱글턴 + SkillProjectile 구현
- PersistentAreaManager + PersistentAreaPool + SkillArea 구현
- IProjectile / IPersistentArea / IPoolable 인터페이스 구현

### 미완성
- SkillLibrary (스킬 조합 코드 — SkillDefinition.RuntimeStep 주입)
- CardManager ↔ SkillRegistry 연결
- 3D 최종 공격/스킬/패링 판정
- 보스 FSM / 패턴
- 보스전 UI
- 씬 설정 (ProjectilePool / PersistentAreaManager+Pool GameObject 배치, 프리팹 생성)
- **PlayerStatManager (플레이어별 분리)** — 기존 StatsManager Player 부분 이관 + DealDamage/ReceiveDamage 쌍
- **SkillManager (자동 시전)** — PlayerSkillSlot 확장, 쿨타임 + 상태 기반 자동 발동
- BossStatManager (보스 분리) — PlayerStatManager 구축 후

---

## 매니저 초기화 순서

| Order | Manager | 비고 |
|-------|---------|------|
| 0 | NetworkManager (NGO) | 모든 네트워크 기반 |
| 5 | StatsManager | 전투 단일 진실 공급원 |
| 10 | PoolManager | 투사체/장판 풀 프리워밍 |
| 15 | SkillRegistry | 스킬 풀 등록 |
| 20 | PersistentAreaManager | 장판 시스템 |

- BossController, PlayerController는 Bootstrap 대상 아님 — 씬 로드 후 Spawn

---

## 인스펙터 연결 필요 항목

- `PlayerController.statsManager` → StatsManager 오브젝트
- `BossController.statsManager` → StatsManager 오브젝트

---

## 개발 우선순위

1. 3D 전투 판정 통합 (DealDirectionalHit 기반)
2. 보스 FSM / 패턴
3. 공용 스킬 풀 적용 (SkillLibrary)
4. PersistentAreaManager + ProjectilePool
5. 공격 이벤트 시스템 (AttackHitEvent)
6. 행동 편향 수집
7. ML-Agents 연동
8. UI/UX 고도화
