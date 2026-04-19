# StateManager 설계 문서

> 전투 오브젝트(Player / Boss)의 **행동 상태 FSM 단일 소스**.
> StatManager 가 보유한 수치/타이머를 **읽어** 파생 상태를 계산한다.
> 중복 저장 금지 — StateManager 는 상태 필드를 자체 보관하지 않는다 (CurrentState 캐시만 유지).

관련 문서:
- [GAME_DESIGN.md](GAME_DESIGN.md)
- [Assets/CHANGES.md](Assets/CHANGES.md)

---

## 1. 목적

| 기존 문제 | StateManager 도입 후 |
|---|---|
| 상태 질의가 `IsCasting / IsParrying / HasStatus(Stunned/HitStun/Silence/Rooted)` 6개 필드 조합으로 분산 | `CurrentState` enum 하나 + Capability 플래그 4개로 단일화 |
| SkillManager.CanCast 에서 상태 검사 6줄 | `_stateManager.CanCast` 1줄 |
| 애니메이션 / ML-Agent 관측용 상태 표현 없음 | CurrentState 를 one-hot 인코딩 가능 |
| Casting 중 Stun 진입 시 정합성 미정 | 우선순위 기반 **강제 인터럽트** 규칙 확정 |

---

## 2. 핵심 원칙

1. **스킬 시전 가능 상태 = `Idle` 또는 `Moving` 만**
   그 외 모든 상태(Dead/Stunned/HitStun/Parrying/Casting)에서는 CanCast = false.
2. **상태 계층 3단계** — 강제 > 의지 > 기본
3. **ChangeState() 단일 관문** — 모든 전이는 이 메서드를 거침. 중복 진입 차단, 이벤트 보장 발행.
4. **StateManager 는 StatManager 의 읽기 전용 투영** — 순환 의존 금지.
5. **Owner 는 ICombatant** — Player / Boss 공용 설계.

---

## 3. CombatantState enum (7종)

```csharp
public enum CombatantState
{
    Idle,        // 기본 대기
    Moving,      // 이동 중
    Casting,     // 스킬 시전 중 (의지)
    Parrying,    // 패링 윈도우 중 (의지)
    HitStun,     // 피격 경직 (강제)
    Stunned,     // 스킬 상태이상 (강제)
    Dead,        // 사망 (영구)
}
```

---

## 4. 상태 계층 및 우선순위 테이블

| 계층 | State | 우선순위<br/>(작을수록 강함) | 진입 조건 | 해제 조건 |
|---|---|:---:|---|---|
| **0. 영구** | Dead | **0** | Owner.IsAlive == false | 없음 (씬 리로드 / ForceReset) |
| **1. 강제** | Stunned | **1** | StatManager.HasStatus(Stunned) | 상태이상 타이머 만료 |
| **1. 강제** | HitStun | **2** | HasStatus(HitStun) | 타이머 만료 |
| **2. 의지** | Parrying | **3** | Owner.IsParrying == true | 패링 윈도우 종료 |
| **2. 의지** | Casting | **4** | Owner.IsCasting == true | SkillExecutor 시전 완료 |
| **3. 기본** | Moving | **5** | 이동 입력 활성 (Notify) | 입력 종료 |
| **3. 기본** | Idle | **6** | 그 외 전부 | — (기본값) |

### 계층 상하 규칙

- **상위 계층은 하위 계층을 강제 종료한다.**
  예: Casting 중 Stun 적용 → 즉시 Stunned 전이 + `StatManager.SetCasting(false)` + 시전 코루틴 Abort 이벤트.
- **하위 계층은 상위 계층을 절대 덮지 못한다.**
  예: Stunned 중 이동 입력 Notify → 상태 변화 없음 (입력만 무시, 입력 큐잉 X).
- **같은 계층 내에서는 숫자 작은 값이 승**.
  예: Stunned(1) vs HitStun(2) 동시 존재 → Stunned.

### 상태별 대기열 / 인터럽트 동작

| 전이 시나리오 | 결과 | 부수 효과 |
|---|---|---|
| Idle/Moving → Casting (CanCast 통과) | Casting | — |
| Casting → Stunned | Stunned | StatManager.SetCasting(false), 시전 아보트 이벤트 |
| Casting → HitStun | HitStun | 동일 (시전 취소) |
| Casting → Parrying | **차단** | `CanParry = false` (Parrying 은 Casting 을 덮지 않음) |
| Parrying → Casting 입력 | **차단** | 패링 중 스킬 시전 불가 |
| Stunned → Parrying 입력 | **차단** | 강제 상태 해제 전 의지 불가 |
| HitStun → Dead | Dead | 이벤트 발행 |
| 모든 상태 → Dead | Dead | 다른 모든 코루틴 종료, Owner.Die() 호출 |

---

## 5. 상태 계산 로직 (ComputeState)

매 Tick 우선순위 테이블을 **위에서 아래로** 순회, 최초 매칭 반환.

```csharp
CombatantState ComputeState()
{
    if (!_owner.IsAlive)                             return CombatantState.Dead;
    if (_stat.HasStatus(StatusType.Stunned))         return CombatantState.Stunned;
    if (_stat.HasStatus(StatusType.HitStun))         return CombatantState.HitStun;
    if (_owner.IsParrying)                           return CombatantState.Parrying;
    if (_owner.IsCasting)                            return CombatantState.Casting;
    if (_movementInputActive)                        return CombatantState.Moving;
    return CombatantState.Idle;
}
```

**핵심 특성:**
- O(1) 상수 분기 — 매 프레임 호출 안전
- 순수 함수 (부수 효과 없음) — 테스트 용이
- ChangeState() 안에서만 호출

---

## 6. Capability 플래그 (파생)

상태와 별개로, **능력 게이트용 플래그**를 계산해 외부에 노출.

| 플래그 | 계산식 |
|---|---|
| `CanAct` | State ∈ { Idle, Moving, Casting, Parrying } |
| `CanMove` | State ∈ { Idle, Moving } && !HasStatus(Rooted) |
| **`CanCast`** | **State ∈ { Idle, Moving } && !HasStatus(Silence)** |
| `CanParry` | State ∈ { Idle, Moving } && !HasStatus(Silence) |

**CanCast 가 Idle / Moving 으로 제한되는 것이 본 설계의 핵심 룰**.
Silence / Rooted 는 FSM 상태가 아니라 능력 차단 모디파이어로 유지 (StatManager 소관).

---

## 7. StateManager API 명세

```csharp
public class StateManager : MonoBehaviour
{
    // ── 상태 ────────────────────────────────────────
    public CombatantState CurrentState   { get; }
    public CombatantState PreviousState  { get; }
    public float          TimeInState    { get; }

    // ── Capability 플래그 ───────────────────────────
    public bool CanAct    { get; }
    public bool CanMove   { get; }
    public bool CanCast   { get; }
    public bool CanParry  { get; }

    // ── 이벤트 (ChangeState 에서만 발행) ─────────────
    public event Action<CombatantState, CombatantState> OnStateChanged;  // prev, next
    public event Action<CombatantState>                 OnStateEntered;
    public event Action<CombatantState>                 OnStateExited;

    // ── 외부 Notify (입력/시전 신호 수신) ────────────
    public void NotifyMovementInput(bool isMoving);   // PlayerController / BossAI
    public void NotifyCastStart();                    // SkillExecutor
    public void NotifyCastEnd();                      // SkillExecutor
    public void NotifyParryStart();                   // Parry Input (추후)
    public void NotifyParryEnd();                     // Parry Input (추후)

    // ── 제어 ────────────────────────────────────────
    public void Tick(float dt);          // Owner 의 Update 에서 호출
    public void ForceReset();            // 씬 리로드 / ML 에피소드 리셋용
}
```

### ChangeState 내부 구현 규칙

```csharp
void ChangeState(CombatantState next)
{
    if (next == CurrentState) return;               // 중복 전이 차단
    var prev = CurrentState;
    OnStateExited?.Invoke(prev);                    // 1. Exit
    CurrentState  = next;                           // 2. 갱신
    PreviousState = prev;
    TimeInState   = 0f;
    OnStateEntered?.Invoke(next);                   // 3. Enter
    OnStateChanged?.Invoke(prev, next);             // 4. Changed
    HandleForceInterrupts(prev, next);              // 5. 인터럽트 부수 효과
}
```

`HandleForceInterrupts`:
- `prev == Casting && next ∈ {Stunned, HitStun, Dead}` → `_stat.SetCasting(false)`, SkillExecutor 아보트 이벤트
- `next == Dead` → `Owner.Die()` 호출 (코루틴 정리는 Owner 책임)

---

## 8. 통합 대상

| 대상 파일 | 변경 내용 |
|---|---|
| `PlayerController.Awake` | StateManager 참조 바인딩 |
| `PlayerController.HandleMovement` | `if (!_state.CanMove) return;` 가드 + moveDir.magnitude > 0 시 `NotifyMovementInput(true/false)` |
| `PlayerController.Update` | 기존 `_stat.Tick(dt)` 뒤에 `_state.Tick(dt)` 추가 |
| `PlayerController.Die` | StateManager 가 Dead 전이 시 이벤트로 호출되도록 구독 |
| `BossController.Awake` | StateManager 참조 바인딩 |
| `BossController.HandleMovement` | `_navAgent.isStopped = !_state.CanMove;` + velocity 기반 NotifyMovementInput |
| `SkillManager.CanCast` | 6개 상태 분기 → `_state.CanCast` 1줄 |
| `SkillExecutor.Execute` | 시전 시작/종료 시 `_state.NotifyCastStart/End` |

---

## 9. 파일 구조

```
Assets/Scripts/State/
├─ CombatantState.cs       (enum only)
└─ StateManager.cs         (MonoBehaviour)
```

StateCapability 구조체는 초기엔 StateManager 프로퍼티로 노출, 관측 개수 많아지면 분리.

---

## 10. 구현 단계 (Phase)

### Phase 1 — 자료형 + 골격
- [x] `CombatantState` enum 추가
- [x] `StateManager` 기본 골격 — ComputeState + ChangeState + 이벤트

### Phase 2 — Player/Boss 부착
- [x] PlayerController / BossController 에 `[RequireComponent(typeof(StateManager))]` + 참조 바인딩
- [x] 각 Update 에서 `_state.Tick(dt)` 호출
- [ ] 상태 전이 로그 확인 (플레이 검증 필요 — 인스펙터 Log Transitions 토글)

### Phase 3 — Notify 연결
- [x] HandleMovement 에서 입력 기반 NotifyMovementInput
- [x] Boss NavAgent velocity 기반 NotifyMovementInput
- [x] SkillManager 시전 시작/종료 Notify (SkillExecutor 가 아닌 SkillManager 에서 처리 — 동기 실행)

### Phase 4 — 기존 로직 치환
- [x] SkillManager.CanCast 상태 검사 축약
- [x] HandleMovement 가드 적용
- [x] BossController NavAgent isStopped 연동

### Phase 5 — (선택) ML/Animator 훅
- [ ] CollectObservations one-hot 인코딩
- [ ] Animator Trigger 매핑

---

## 11. 리스크 / 트레이드오프

| 리스크 | 대응 |
|---|---|
| ComputeState 매 프레임 호출 부담 | O(1) 분기 — 측정 후 이슈 시 변경 이벤트 기반으로 전환 |
| StatManager ↔ StateManager 순환 의존 | 단방향 (StateManager → StatManager) 강제. StatManager 내부에 StateManager 참조 금지 |
| IsCasting / IsParrying 중복 저장 | StatManager 가 마스터. StateManager 는 캐시만 (CurrentState). 쓰지 않음 |
| Notify 누락 시 Idle 고착 | Phase 3 연결 즉시 로그로 검증. 누락 시 이동/시전 시 로그 부재로 즉시 발견 |
| ML 에피소드 리셋 시 Dead 고착 | `ForceReset()` API 로 PreviousState 무시하고 Idle 로 강제 복귀 |
| 시전 중 Stun 인터럽트 시 쿨타임 처리 | 정책 결정 필요: (A) 쿨타임 소모 / (B) 환불 — 초기엔 (A) 고정, 추후 옵션화 |

---

## 12. 결정 사항 요약

1. 스킬 시전은 **Idle / Moving 에서만** 가능.
2. 계층: **강제(0-1) > 의지(2) > 기본(3)**.
3. 상위 계층은 하위를 강제 종료하며, 반대는 차단.
4. 모든 전이는 `ChangeState()` 단일 관문.
5. StateManager 는 StatManager 의 읽기 전용 투영 (중복 저장 금지).
6. Silence / Rooted / Slowed 등은 FSM 에 넣지 않고 Capability 또는 수치 모디파이어로 유지.
