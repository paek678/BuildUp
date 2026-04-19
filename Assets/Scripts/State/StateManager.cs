using System;
using UnityEngine;

// ══════════════════════════════════════════════════════════════════
// StateManager — 전투 개체 행동 상태 FSM 단일 소스
//
// StatManager 의 수치/타이머를 읽어 파생 상태를 계산한다. 자체 저장 금지.
// 모든 전이는 ChangeState() 단일 관문을 통해 이벤트 보장 발행.
//
// 계층 (강함 → 약함):
//   Dead > Stunned > HitStun > Parrying > Casting > Moving > Idle
//
// 스킬 시전 가능: CanCast = State ∈ {Idle, Moving} && !Silence
// 자세한 규칙은 STATE_MANAGER_DESIGN.md 참조
// ══════════════════════════════════════════════════════════════════
[RequireComponent(typeof(StatManager))]
public class StateManager : MonoBehaviour
{
    [Header("디버그 (Inspector 확인용)")]
    [SerializeField] private CombatantState _debugCurrent;
    [SerializeField] private CombatantState _debugPrevious;
    [SerializeField] private float          _debugTimeInState;

    [Header("전이 로그")]
    [SerializeField] private bool _logTransitions = false;

    // ── 참조 ────────────────────────────────────────────────
    private StatManager _stat;
    private ICombatant  _owner;   // IsAlive / IsCasting / IsParrying 조회용

    // ── 상태 (캐시, 계산된 값만 보관) ─────────────────────
    public CombatantState CurrentState  { get; private set; } = CombatantState.Idle;
    public CombatantState PreviousState { get; private set; } = CombatantState.Idle;
    public float          TimeInState   { get; private set; } = 0f;

    // ── 외부 Notify 수신 플래그 ───────────────────────────
    private bool _movementInputActive;

    // ── Capability 플래그 (파생) ──────────────────────────
    public bool CanAct   => CurrentState != CombatantState.Dead
                         && CurrentState != CombatantState.Stunned
                         && CurrentState != CombatantState.HitStun;

    public bool CanMove  => (CurrentState == CombatantState.Idle || CurrentState == CombatantState.Moving)
                         && !_stat.HasStatus(StatusType.Rooted);

    // 스킬 시전 가능 — Idle / Moving 전용 + Silence 차단
    public bool CanCast  => (CurrentState == CombatantState.Idle || CurrentState == CombatantState.Moving)
                         && !_stat.HasStatus(StatusType.Silence);

    public bool CanParry => (CurrentState == CombatantState.Idle || CurrentState == CombatantState.Moving)
                         && !_stat.HasStatus(StatusType.Silence);

    // ── 이벤트 ──────────────────────────────────────────────
    public event Action<CombatantState, CombatantState> OnStateChanged;  // (prev, next)
    public event Action<CombatantState> OnStateEntered;
    public event Action<CombatantState> OnStateExited;

    // ══════════════════════════════════════════════════════
    // 초기화
    // ══════════════════════════════════════════════════════

    private void Awake()
    {
        _stat = GetComponent<StatManager>();
    }

    // Controller 가 자기 자신을 ICombatant 로 바인딩
    public void BindOwner(ICombatant owner) => _owner = owner;

    // ══════════════════════════════════════════════════════
    // 외부 Notify API
    // ══════════════════════════════════════════════════════

    public void NotifyMovementInput(bool isMoving) => _movementInputActive = isMoving;

    // 시전 시작/종료 — SkillManager 또는 Controller 가 호출
    // StatManager.SetCasting 을 함께 토글해 IsCasting 이 일관되게 유지되도록 한다
    public void NotifyCastStart()
    {
        _stat.SetCasting(true);
    }

    public void NotifyCastEnd()
    {
        _stat.SetCasting(false);
    }

    public void NotifyParryStart()
    {
        _stat.BeginParryWindow();
    }

    public void NotifyParryEnd()
    {
        _stat.EndParryWindow();
    }

    // ══════════════════════════════════════════════════════
    // Tick — Owner 의 Update 에서 호출
    // ══════════════════════════════════════════════════════

    public void Tick(float dt)
    {
        TimeInState += dt;
        var computed = ComputeState();
        if (computed != CurrentState)
            ChangeState(computed);

        _debugCurrent     = CurrentState;
        _debugPrevious    = PreviousState;
        _debugTimeInState = TimeInState;
    }

    // 우선순위 테이블 단일 패스 — 계층 규칙 자동 적용
    private CombatantState ComputeState()
    {
        if (_owner == null) return CombatantState.Idle;

        if (!_owner.IsAlive)                            return CombatantState.Dead;
        if (_stat.HasStatus(StatusType.Stunned))        return CombatantState.Stunned;
        if (_stat.HasStatus(StatusType.HitStun))        return CombatantState.HitStun;
        if (_owner.IsParrying)                          return CombatantState.Parrying;
        if (_owner.IsCasting)                           return CombatantState.Casting;
        if (_movementInputActive)                       return CombatantState.Moving;
        return CombatantState.Idle;
    }

    // ══════════════════════════════════════════════════════
    // ChangeState — 모든 전이의 단일 관문
    // ══════════════════════════════════════════════════════

    private void ChangeState(CombatantState next)
    {
        if (next == CurrentState) return;

        var prev = CurrentState;
        OnStateExited?.Invoke(prev);
        HandleForceInterrupts(prev, next);

        PreviousState = prev;
        CurrentState  = next;
        TimeInState   = 0f;

        OnStateEntered?.Invoke(next);
        OnStateChanged?.Invoke(prev, next);

        if (_logTransitions)
            Debug.Log($"[StateManager:{name}] {prev} → {next}");
    }

    // 상위 계층이 하위 계층을 덮는 경우 부수 효과 처리
    private void HandleForceInterrupts(CombatantState prev, CombatantState next)
    {
        // Casting / Parrying 강제 종료 — 상위 계층(Stunned/HitStun/Dead) 진입 시
        bool forcedBySuperior =
            next == CombatantState.Dead ||
            next == CombatantState.Stunned ||
            next == CombatantState.HitStun;

        if (forcedBySuperior)
        {
            if (prev == CombatantState.Casting)   _stat.SetCasting(false);
            if (prev == CombatantState.Parrying)  _stat.EndParryWindow();
        }
    }

    // ══════════════════════════════════════════════════════
    // 리셋 (ML 에피소드 / 씬 리로드)
    // ══════════════════════════════════════════════════════
    public void ForceReset()
    {
        _movementInputActive = false;
        PreviousState = CurrentState;
        CurrentState  = CombatantState.Idle;
        TimeInState   = 0f;
    }
}
