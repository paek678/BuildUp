using System.Collections.Generic;
using UnityEngine;

// ══════════════════════════════════════════════════════════════════
// SkillManager — 자동 시전 스킬 매니저 (Stage 6 / 디버그·학습용 모드)
//
// 슬롯 index 순서 = 우선순위. 매 프레임 CanCast 를 검사해 첫 번째 가능한
// 스킬을 자동 시전한다. 수동 발동 API (TryExecute) 도 유지.
//
// 슬롯 지정 방식:
//   Inspector 의 Slots 배열에 SkillDefinition SO 를 직접 드래그.
//   Element 0 = 최우선. 비어있는(null) 슬롯은 건너뜀.
//   카드 드래프트 연동은 추후 — 현재는 Inspector 만 사용.
//
// 시전 가능 조건 (CanCast):
//   1) Executor 쿨타임 만료
//   2) IsAlive
//   3) !IsCasting
//   4) !IsParrying
//   5) !HasStatus(Stunned/HitStun/Silence/Rooted)
//   6) 타겟 존재 + 생존 (Self 타입은 skip)
//   7) 거리 ≤ skill.Range (Self 타입은 skip)
// ══════════════════════════════════════════════════════════════════
[RequireComponent(typeof(SkillExecutor))]
public class SkillManager : MonoBehaviour
{
    public const int SlotCount = 5;

    [Header("슬롯 (index 0 = 최우선, null = 빈 슬롯)")]
    [SerializeField] private SkillDefinition[] _slots = new SkillDefinition[SlotCount];

    [Header("설정")]
    [SerializeField] private bool _autoCastEnabled = true;
    [SerializeField] private bool _logAutoCast = true;
    [SerializeField] private bool _roundRobinEnabled = false;

    private int _roundRobinStart = 0;

    [Header("참조")]
    [SerializeField] private StatManager _statManager;
    [SerializeField] private StateManager _stateManager;
    [SerializeField] private GameManager _gameManager;
    [SerializeField] private PlayerController _owner;   // Caster 로 사용

    private SkillExecutor _executor;

    // ── 외부 조회 ────────────────────────────────────────────
    public int  MaxSlots        => SlotCount;
    public bool AutoCastEnabled => _autoCastEnabled;
    public bool RoundRobinEnabled
    {
        get => _roundRobinEnabled;
        set => _roundRobinEnabled = value;
    }
    public IReadOnlyList<SkillDefinition> Slots => _slots;

    // ══════════════════════════════════════════════════════════
    // 초기화
    // ══════════════════════════════════════════════════════════
/// <summary>
/// 
/// </summary>
    private void Awake()
    {
        _executor = GetComponent<SkillExecutor>();
        if (_statManager  == null) _statManager  = GetComponent<StatManager>();
        if (_stateManager == null) _stateManager = GetComponent<StateManager>();
        if (_owner        == null) _owner        = GetComponent<PlayerController>();

        // 배열 크기 강제 보정 (Inspector 에서 누가 Size 를 바꿨을 때 대비)
        if (_slots == null || _slots.Length != SlotCount)
        {
            var fixedSlots = new SkillDefinition[SlotCount];
            if (_slots != null)
            {
                int copy = Mathf.Min(_slots.Length, SlotCount);
                for (int i = 0; i < copy; i++) fixedSlots[i] = _slots[i];
            }
            _slots = fixedSlots;
        }
    }

    private void OnValidate()
    {
        // 에디터에서 Inspector 값 변경 시 배열 크기 유지
        if (_slots == null || _slots.Length != SlotCount)
        {
            System.Array.Resize(ref _slots, SlotCount);
        }
    }

    private void Update()
    {
        if (!_autoCastEnabled || _statManager == null || !_statManager.IsAlive)
        {
            if (_logAutoCast && Time.frameCount % 300 == 0)
                Debug.LogWarning($"[SkillManager] Update 차단: autoCast={_autoCastEnabled}, statMgr={_statManager != null}, alive={_statManager?.IsAlive}");
            return;
        }

        int start = _roundRobinEnabled ? _roundRobinStart : 0;
        int count = _slots.Length;

        for (int n = 0; n < count; n++)
        {
            int i = (start + n) % count;
            if (_slots[i] == null) continue;
            if (!CanCast(_slots[i], out var ctx)) continue;

            if (_stateManager != null) _stateManager.NotifyCastStart();

            bool fired = _executor.Execute(_slots[i], ctx);

            if (_stateManager != null) _stateManager.NotifyCastEnd();

            if (fired)
            {
                if (_logAutoCast)
                    Debug.Log($"[AutoCast] <b>슬롯[{i}]</b> {_slots[i].DisplayName} 자동 시전 | {name}");
                if (_roundRobinEnabled)
                    _roundRobinStart = (i + 1) % count;
                break;
            }
        }
    }

    // ══════════════════════════════════════════════════════════
    // 슬롯 관리 (런타임 변경 API — 필요 시 사용)
    // ══════════════════════════════════════════════════════════

    public bool SetSlot(int index, SkillDefinition skill)
    {
        if (index < 0 || index >= SlotCount) return false;
        _slots[index] = skill;
        return true;
    }

    public void ClearSlot(int index)
    {
        if (index < 0 || index >= SlotCount) return;
        _slots[index] = null;
    }

    public void ClearAll()
    {
        for (int i = 0; i < _slots.Length; i++) _slots[i] = null;
    }

    public void SetAutoCast(bool enabled) => _autoCastEnabled = enabled;

    // ══════════════════════════════════════════════════════════
    // 수동 발동 / 조회
    // ══════════════════════════════════════════════════════════

    public bool TryExecute(int slotIndex, SkillContext ctx)
    {
        if (slotIndex < 0 || slotIndex >= _slots.Length || _slots[slotIndex] == null) return false;
        return _executor.Execute(_slots[slotIndex], ctx);
    }

    public bool CanUse(int slotIndex)
    {
        if (slotIndex < 0 || slotIndex >= _slots.Length || _slots[slotIndex] == null) return false;
        return _executor.CanUse(_slots[slotIndex]);
    }

    public float GetRemainingCooldown(int slotIndex)
    {
        if (slotIndex < 0 || slotIndex >= _slots.Length || _slots[slotIndex] == null) return 0f;
        return _executor.GetRemainingCooldown(_slots[slotIndex]);
    }

    public void ResetCooldown(int slotIndex)
    {
        if (slotIndex < 0 || slotIndex >= _slots.Length || _slots[slotIndex] == null) return;
        _executor.ResetCooldown(_slots[slotIndex].SkillId);
    }

    // ══════════════════════════════════════════════════════════
    // CanCast — 7가지 조건 전체 검사 + ctx 생성
    // ══════════════════════════════════════════════════════════

    private bool CanCast(SkillDefinition skill, out SkillContext ctx)
    {
        ctx = null;
        if (skill == null || !skill.IsReady)
        {
            if (_logAutoCast) Debug.LogWarning($"[CanCast] {skill?.SkillId ?? "null"} 실패: IsReady={skill?.IsReady}");
            return false;
        }

        if (!_executor.CanUse(skill))
            return false;   // 쿨타임 중 — 매 프레임 뜨므로 로그 생략

        if (_stateManager != null && !_stateManager.CanCast)
        {
            if (_logAutoCast) Debug.LogWarning($"[CanCast] {skill.SkillId} 실패: CanCast=false (State={_stateManager.CurrentState})");
            return false;
        }

        ICombatant target = null;
        if (skill.TargetType != TargetType.Self)
        {
            target = FindNearestTarget();
            if (target == null || !target.IsAlive)
            {
                if (_logAutoCast) Debug.LogWarning($"[CanCast] {skill.SkillId} 실패: 타겟 없음 (Bosses={_gameManager?.Bosses?.Count ?? -1})");
                return false;
            }

            float dist = Vector3.Distance(transform.position, target.Transform.position);
            if (dist > skill.Range)
            {
                if (_logAutoCast) Debug.LogWarning($"[CanCast] {skill.SkillId} 실패: 거리 초과 ({dist:F1}m > {skill.Range}m)");
                return false;
            }
        }

        ctx = BuildSkillContext(target);

        // RuntimeCondition 검사 — 조건 미충족 시 쿨타임 미소모 + 다음 슬롯 시도
        if (skill.RuntimeCondition != null && !skill.RuntimeCondition(ctx))
            return false;

        return true;
    }

    // ══════════════════════════════════════════════════════════
    // SkillContext 생성
    // ══════════════════════════════════════════════════════════

    public SkillContext BuildSkillContext(ICombatant target)
    {
        var ctx = new SkillContext
        {
            Caster         = _owner,
            PrimaryTarget  = target,
            CastPosition   = transform.position,
            CastDirection  = transform.forward,
            ParryInputTime = (_statManager != null && _statManager.IsParrying) ? Time.time : 0f,
        };
        ctx.RefreshSnapshot();
        return ctx;
    }

    // ══════════════════════════════════════════════════════════
    // 가장 가까운 보스를 타겟으로 반환
    // ══════════════════════════════════════════════════════════

    public ICombatant FindNearestTarget()
    {
        if (_gameManager == null) return null;

        ICombatant nearest  = null;
        float      bestDist = float.MaxValue;

        foreach (var bossObj in _gameManager.Bosses)
        {
            if (bossObj == null) continue;
            var combatant = bossObj.GetComponentInChildren<ICombatant>();
            if (combatant == null || !combatant.IsAlive) continue;

            float dist = Vector3.Distance(transform.position, combatant.Transform.position);
            if (dist < bestDist)
            {
                bestDist = dist;
                nearest  = combatant;
            }
        }
        return nearest;
    }
}
