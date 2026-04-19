using System.Collections.Generic;
using System.Linq;
using UnityEngine;

// 전체 스킬 풀 관리
// 드래프트 UI 와 보스 AI 카운터 선택이 이 클래스를 통해 스킬을 조회한다
[CreateAssetMenu(menuName = "Tenebris/SkillRegistry", fileName = "SkillRegistry")]
public class SkillRegistry : ScriptableObject
{
    [SerializeField] private List<SkillDefinition> _pool = new();

    // ── 단건 조회 ────────────────────────────────────────────
    public SkillDefinition Get(string skillId) =>
        _pool.Find(s => s.SkillId == skillId);

    public List<SkillDefinition> GetAll() => new(_pool);

    // ── 태그 기반 조회 ───────────────────────────────────────
    public List<SkillDefinition> GetByRoleTag(string tag) =>
        _pool.Where(s => s.RoleTags != null && System.Array.Exists(s.RoleTags, t => t == tag))
             .ToList();

    // ── 보스 카운터 스킬 선택 ────────────────────────────────
    // 플레이어들이 선택한 스킬의 RoleTags 를 넘기면
    // CounterTags 매칭 점수가 높은 상위 count 개를 반환
    public List<SkillDefinition> GetCounterCandidates(string[] playerRoleTags, int count = 3)
    {
        return _pool
            .OrderByDescending(s => ScoreCounter(s, playerRoleTags))
            .Take(count)
            .ToList();
    }

    // ── 드래프트용 랜덤 후보 ─────────────────────────────────
    // 이미 보유한 스킬 ID 목록을 제외하고 랜덤 count 개 반환
    public List<SkillDefinition> GetDraftCandidates(List<string> ownedIds, int count = 3)
    {
        var available = _pool.Where(s => !ownedIds.Contains(s.SkillId)).ToList();

        // Fisher-Yates 셔플 후 앞에서 count 개
        for (int i = available.Count - 1; i > 0; i--)
        {
            int j = Random.Range(0, i + 1);
            (available[i], available[j]) = (available[j], available[i]);
        }

        return available.Take(count).ToList();
    }

    // ── 내부 ─────────────────────────────────────────────────
    private int ScoreCounter(SkillDefinition skill, string[] playerTags)
    {
        if (skill.CounterTags == null || playerTags == null) return 0;
        return skill.CounterTags.Count(ct => System.Array.Exists(playerTags, pt => pt == ct));
    }
}
