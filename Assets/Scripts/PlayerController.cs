using System.Collections;
using UnityEngine;

// ══════════════════════════════════════════════════════════════════
// PlayerController — Stage 7 리팩터 (스킬 자동 시전)
//
// 책임:
//   - 이동 입력 (WASD → Rigidbody)
//   - ICombatant 인터페이스 프록시 (StatManager 위임)
//   - 위치 제어 (Knockback / Pull / MoveBy) 코루틴
//   - 사망 처리
//
// 제거된 기능:
//   - isCasting / isParrying            → StatManager
//   - RegenerateHP()                    → StatManager.Tick
//   - TakeDamage 의 패링/반사/실드      → StatManager.ReceiveDamage
//   - ApplyStatus / Buff / Debuff 등    → StatManager 위임
//   - Q/W/E/R/T 수동 스킬 입력         → SkillManager 자동 시전
//   - BuildSkillContext / FindNearest   → SkillManager
// ══════════════════════════════════════════════════════════════════
[RequireComponent(typeof(Rigidbody))]
[RequireComponent(typeof(StatManager))]
[RequireComponent(typeof(StateManager))]
public class PlayerController : MonoBehaviour, ICombatant
{
    [Header("플레이어 스탯 에셋")]
    public PlayerStatsSO playerStats;

    [Header("스탯 매니저 참조")]
    [SerializeField] private StatManager _statManager;

    [Header("상태 매니저 참조")]
    [SerializeField] private StateManager _stateManager;

    [Header("스킬 매니저 (자동 시전)")]
    [SerializeField] private SkillManager _skillManager;

    private Rigidbody rb;

    // ── 외부 접근 ────────────────────────────────────────────
    public SkillManager  SkillMgr => _skillManager;
    public StatManager   StatMgr  => _statManager;
    public StateManager  StateMgr => _stateManager;

    // ── ICombatant 프로퍼티 ──────────────────────────────────
    Transform  ICombatant.Transform   => transform;
    GameObject ICombatant.GameObject  => gameObject;
    public float MaxHP            => _statManager.GetMaxHP();
    public float CurrentHPPercent => _statManager.GetHPPercent();
    public float Shield           => _statManager.GetShield();
    public bool  IsAlive          => _statManager.IsAlive;
    public bool  IsCasting        => _statManager.IsCasting;
    public bool  IsParrying       => _statManager.IsParrying;
    public float ParryWindow      => _statManager.GetParryWindow();

    // ══════════════════════════════════════════════════════════
    // Unity 생명주기
    // ══════════════════════════════════════════════════════════

    void Awake()
    {
        if (_statManager  == null) _statManager  = GetComponent<StatManager>();
        if (_stateManager == null) _stateManager = GetComponent<StateManager>();
        if (_skillManager == null) _skillManager = GetComponent<SkillManager>();
    }

    void Start()
    {
        rb = GetComponent<Rigidbody>();
        rb.constraints = RigidbodyConstraints.FreezeRotation;

        if (_statManager != null && playerStats != null)
        {
            _statManager.Initialize(
                baseStats:   playerStats,
                maxHP:       playerStats.MaxHP,
                shieldMax:   playerStats.ShieldMax,
                hpRegenRate: playerStats.HPRegenRate,
                parryWindow: playerStats.ParryWindow,
                kind:        CombatantKind.Player);
            _statManager.BindOwner(this);
        }

        if (_stateManager != null)
            _stateManager.BindOwner(this);
    }

    void Update()
    {
        if (_statManager != null) _statManager.Tick(Time.deltaTime);
        HandleMovement();
        if (_stateManager != null) _stateManager.Tick(Time.deltaTime);
        // 스킬 시전은 SkillManager.Update() 가 자동 처리
    }

    // ══════════════════════════════════════════════════════════
    // 입력 처리
    // ══════════════════════════════════════════════════════════

    private void HandleMovement()
    {
        if (_statManager == null || playerStats == null) return;

        float moveX = Input.GetAxisRaw("Horizontal");
        float moveZ = Input.GetAxisRaw("Vertical");

        Vector3 moveDir = new Vector3(moveX, 0, moveZ).normalized;
        bool    hasInput = moveDir.magnitude > 0f;

        // StateManager 로 입력 상태 통지 — Moving / Idle 전이 판정에 사용
        if (_stateManager != null)
            _stateManager.NotifyMovementInput(hasInput);

        // 이동 불가 상태(Stunned/HitStun/Casting/Parrying/Dead/Rooted) 면 차단
        if (_stateManager != null && !_stateManager.CanMove) return;
        if (!hasInput) return;

        float speed = playerStats.MoveSpeed * _statManager.GetMoveControl();
        rb.MovePosition(transform.position + moveDir * speed * Time.deltaTime);

        Quaternion targetRotation = Quaternion.LookRotation(moveDir);
        transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, playerStats.TurnSpeed * Time.deltaTime);
    }

    // ══════════════════════════════════════════════════════════
    // ICombatant — 피해 / 회복 / 실드 (StatManager 로 위임)
    // ══════════════════════════════════════════════════════════

    public void TakeDamage(float amount, ICombatant attacker = null)
    {
        _statManager.ReceiveDamage(amount, attacker);
        if (!IsAlive) Die();
    }

    public void TakeShieldBreakDamage(float amount, float multiplier, ICombatant attacker = null)
    {
        _statManager.ReceiveShieldBreakDamage(amount, multiplier, attacker);
        if (!IsAlive) Die();
    }

    public void RecoverHP(float amount) => _statManager.RecoverHP(amount);
    public void AddShield(float amount) => _statManager.AddShield(amount);

    // ══════════════════════════════════════════════════════════
    // ICombatant — 상태이상 / 버프 / 디버프
    // ══════════════════════════════════════════════════════════

    public void ApplyStatus(StatusType type, float duration, float value = 0f)
        => _statManager.ApplyStatus(type, duration, value);

    public bool HasStatus(StatusType type) => _statManager.HasStatus(type);

    public void ApplyBuff(BuffType type, float duration, float value)
        => _statManager.ApplyBuff(type, duration, value);

    public void ApplyDebuff(DebuffType type, float duration, float value)
        => _statManager.ApplyDebuff(type, duration, value);

    public void RemoveStatuses(CleanseType type, int count)
        => _statManager.RemoveStatuses(type, count);

    public void RemoveBuffs(DispelType type, int count)
        => _statManager.RemoveBuffs(type, count);

    // ══════════════════════════════════════════════════════════
    // ICombatant — 위치 제어
    // ══════════════════════════════════════════════════════════

    public void Knockback(Vector3 direction, float distance)
    {
        rb.AddForce(direction.normalized * distance, ForceMode.Impulse);
    }

    public void Pull(Vector3 towardPosition, float distance, float duration)
        => StartCoroutine(PullRoutine(towardPosition, distance, duration));

    public void MoveBy(Vector3 direction, float distance, float duration, MoveType moveType)
        => StartCoroutine(MoveByRoutine(direction, distance, duration));

    // ══════════════════════════════════════════════════════════
    // ICombatant — 패링 보상 (StatManager 로 위임)
    // ══════════════════════════════════════════════════════════

    public void NotifyParryReward(ParryRewardType rewardType, float value, float duration, ICombatant attacker = null)
        => _statManager.NotifyParryReward(rewardType, value, duration, attacker);

    // ══════════════════════════════════════════════════════════
    // 코루틴
    // ══════════════════════════════════════════════════════════

    private IEnumerator PullRoutine(Vector3 towardPosition, float distance, float duration)
    {
        float elapsed = 0f;
        Vector3 start = transform.position;
        Vector3 end   = start + (towardPosition - start).normalized * distance;

        while (elapsed < duration)
        {
            elapsed += Time.deltaTime;
            rb.MovePosition(Vector3.Lerp(start, end, elapsed / duration));
            yield return null;
        }
    }

    private IEnumerator MoveByRoutine(Vector3 direction, float distance, float duration)
    {
        float elapsed = 0f;
        Vector3 start = transform.position;
        Vector3 end   = start + direction.normalized * distance;

        while (elapsed < duration)
        {
            elapsed += Time.deltaTime;
            rb.MovePosition(Vector3.Lerp(start, end, elapsed / duration));
            yield return null;
        }
    }

    // ══════════════════════════════════════════════════════════
    // 사망
    // ══════════════════════════════════════════════════════════

    private void Die()
    {
        Debug.Log("플레이어 사망! 부활 대기 시간: " + playerStats.ReviveTime);
        // 부활 로직은 GameManager 에서 처리 예정
    }
}
