using System.Collections.Generic;
using UnityEngine;

// 플레이어의 스킬 슬롯 관리 전담 컴포넌트
// 드래프트에서 선택한 스킬을 슬롯에 등록하고, 입력 키와 매핑한다
// PlayerController 와 CardManager 가 이 컴포넌트를 통해 스킬을 관리한다
//
// 사용법:
//   playerSkillSlot.Equip(skillDefinition);  // 드래프트 선택 시
//   playerSkillSlot.TryExecute(slotIndex, ctx);  // 입력 시
[RequireComponent(typeof(SkillExecutor))]
public class PlayerSkillSlot : MonoBehaviour
{
    [Header("슬롯 설정")]
    [SerializeField] private int _maxSlots = 5;

    private SkillExecutor _executor;
    private readonly List<SkillDefinition> _slots = new();

    // ── 외부 조회 ────────────────────────────────────────────
    public int MaxSlots => _maxSlots;
    public int Count    => _slots.Count;
    public IReadOnlyList<SkillDefinition> Slots => _slots;

    // ══════════════════════════════════════════════════════════
    // 초기화
    // ══════════════════════════════════════════════════════════

    private void Awake()
    {
        _executor = GetComponent<SkillExecutor>();
    }

    // ══════════════════════════════════════════════════════════
    // 슬롯 관리
    // ══════════════════════════════════════════════════════════

    // 스킬 장착 — 성공 시 슬롯 인덱스 반환, 실패 시 -1
    public int Equip(SkillDefinition skill)
    {
        if (skill == null) return -1;
        if (_slots.Count >= _maxSlots)
        {
            Debug.LogWarning($"[PlayerSkillSlot] 슬롯 가득 참 ({_maxSlots})");
            return -1;
        }
        if (_slots.Exists(s => s.SkillId == skill.SkillId))
        {
            Debug.LogWarning($"[PlayerSkillSlot] 이미 장착됨: {skill.DisplayName}");
            return -1;
        }

        _slots.Add(skill);
        Debug.Log($"[PlayerSkillSlot] 장착 [{_slots.Count - 1}]: {skill.DisplayName}");
        return _slots.Count - 1;
    }

    // 스킬 해제
    public bool Unequip(string skillId)
    {
        return _slots.RemoveAll(s => s.SkillId == skillId) > 0;
    }

    // 전체 해제
    public void UnequipAll() => _slots.Clear();

    // ══════════════════════════════════════════════════════════
    // 실행
    // ══════════════════════════════════════════════════════════

    // 슬롯 인덱스 기반 실행 — 성공 시 true
    public bool TryExecute(int slotIndex, SkillContext ctx)
    {
        if (slotIndex < 0 || slotIndex >= _slots.Count) return false;
        return _executor.Execute(_slots[slotIndex], ctx);
    }

    // ── 쿨타임 조회 ──────────────────────────────────────────

    public bool CanUse(int slotIndex)
    {
        if (slotIndex < 0 || slotIndex >= _slots.Count) return false;
        return _executor.CanUse(_slots[slotIndex]);
    }

    public float GetRemainingCooldown(int slotIndex)
    {
        if (slotIndex < 0 || slotIndex >= _slots.Count) return 0f;
        return _executor.GetRemainingCooldown(_slots[slotIndex]);
    }

    // ── 쿨타임 초기화 (패링 보상 등) ─────────────────────────

    public void ResetCooldown(int slotIndex)
    {
        if (slotIndex < 0 || slotIndex >= _slots.Count) return;
        _executor.ResetCooldown(_slots[slotIndex].SkillId);
    }
}
