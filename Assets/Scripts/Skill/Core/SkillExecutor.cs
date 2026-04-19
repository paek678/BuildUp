using System.Collections.Generic;
using UnityEngine;

// 스킬 실행 및 쿨타임 관리
// Host-authoritative 구조이므로 실제 판정은 Host 에서만 실행되어야 한다
// 컴포넌트로 붙여 PlayerController / BossController 가 참조해서 사용
public class SkillExecutor : MonoBehaviour
{
    [Header("디버그")]
    [SerializeField] private bool _logExecution = true;

    // SkillId → 마지막 사용 시각
    private readonly Dictionary<string, float> _lastUseTimes = new();

    // ── 쿨타임 조회 ──────────────────────────────────────────
    public bool CanUse(SkillDefinition skill)
    {
        if (skill == null || !skill.IsReady) return false;
        return Time.time - GetLastUseTime(skill) >= skill.Cooldown;
    }

    public float GetRemainingCooldown(SkillDefinition skill)
    {
        if (skill == null) return 0f;
        return Mathf.Max(0f, skill.Cooldown - (Time.time - GetLastUseTime(skill)));
    }

    // ── 실행 ─────────────────────────────────────────────────
    // 성공 시 true 반환, 쿨타임 중이거나 RuntimeStep 미주입이면 false
    public bool Execute(SkillDefinition skill, SkillContext ctx)
    {
        if (!CanUse(skill)) return false;

        ctx.CurrentTime = Time.time;
        ctx.RefreshSnapshot();

        if (skill.RuntimeCondition != null && !skill.RuntimeCondition(ctx))
            return false;

        _lastUseTimes[skill.SkillId] = Time.time;
        skill.RuntimeStep.Invoke(ctx);

        if (_logExecution)
        {
            string target = ctx.PrimaryTarget != null
                ? $"{ctx.PrimaryTarget.Transform.name}(HP:{ctx.PrimaryTarget.CurrentHPPercent * 100f:F0}%)"
                : "없음";
            string caster = ctx.Caster?.Transform.name ?? "?";
            Debug.Log($"[Skill] {caster} → <b>{skill.DisplayName}</b>({skill.SkillId}) | 대상: {target} | CD: {skill.Cooldown}s\n" +
                      $"  실행 로그: {string.Join(" → ", ctx.GetLog())}");
        }

        return true;
    }

    // ── 쿨타임 강제 초기화 (패링 보상, 퍼크 등) ─────────────
    public void ResetCooldown(string skillId) =>
        _lastUseTimes.Remove(skillId);

    // ── 내부 ─────────────────────────────────────────────────
    private float GetLastUseTime(SkillDefinition skill) =>
        _lastUseTimes.TryGetValue(skill.SkillId, out float t) ? t : float.NegativeInfinity;
}
