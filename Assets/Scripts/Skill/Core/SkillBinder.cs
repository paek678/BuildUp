using UnityEngine;

// SkillLibrary 에서 조립한 RuntimeStep 을 SkillDefinition SO 에 주입하는 바인더
// 게임 시작 시 SkillBinder.BindAll(registry) 를 한 번 호출해야 한다
//
// SkillDefinition.RuntimeStep 은 [NonSerialized] 이므로
// 도메인 리로드 / 씬 전환마다 재주입이 필요하다
public static class SkillBinder
{
    // ── 전체 바인딩 ──────────────────────────────────────────
    public static void BindAll(SkillRegistry registry)
    {
        if (registry == null)
        {
            Debug.LogWarning("[SkillBinder] SkillRegistry 가 null");
            return;
        } 

        int bound = 0;

        // ── 플레이어 공용 ────────────────────────────────────
        bound += Bind(registry, "ExecutionSpike",     SkillLibrary.ExecutionSpike());
        bound += Bind(registry, "CrushingBarrage",    SkillLibrary.CrushingBarrage());
        bound += Bind(registry, "ErosionField",       SkillLibrary.ErosionField());
        bound += Bind(registry, "HuntingMark",        SkillLibrary.HuntingMark());
        bound += Bind(registry, "SurvivalPulse",      SkillLibrary.SurvivalPulse(),      SkillLibrary.SurvivalPulseCondition());
        bound += Bind(registry, "FortressArmor",      SkillLibrary.FortressArmor());
        bound += Bind(registry, "SealChain",          SkillLibrary.SealChain());
        bound += Bind(registry, "CollapseRoar",       SkillLibrary.CollapseRoar());
        bound += Bind(registry, "BarrierBreaker",     SkillLibrary.BarrierBreaker());
        bound += Bind(registry, "OverchargeMode",     SkillLibrary.OverchargeMode(),     SkillLibrary.OverchargeModeCondition());
        bound += Bind(registry, "PiercingShot",       SkillLibrary.PiercingShot());
        bound += Bind(registry, "RuptureMagazine",    SkillLibrary.RuptureMagazine());

        // ── 플레이어 전용 ────────────────────────────────────
        bound += Bind(registry, "CounterStance",      SkillLibrary.CounterStance());
        bound += Bind(registry, "ParryEnhance",       SkillLibrary.ParryEnhance());
        bound += Bind(registry, "CounterSlash",       SkillLibrary.CounterSlash());
        bound += Bind(registry, "WireHook",           SkillLibrary.WireHook());
        bound += Bind(registry, "RopeShockwave",      SkillLibrary.RopeShockwave());
        bound += Bind(registry, "CollapseStrike",     SkillLibrary.CollapseStrike());

        // ── 보스 공용 ────────────────────────────────────────
        bound += Bind(registry, "ExecutionSpike_Boss",    SkillLibrary.ExecutionSpike_Boss());
        bound += Bind(registry, "CrushingBarrage_Boss",   SkillLibrary.CrushingBarrage_Boss());
        bound += Bind(registry, "ErosionField_Boss",      SkillLibrary.ErosionField_Boss());
        bound += Bind(registry, "SurvivalPulse_Boss",     SkillLibrary.SurvivalPulse_Boss(),     SkillLibrary.SurvivalPulseCondition_Boss());
        bound += Bind(registry, "FortressArmor_Boss",     SkillLibrary.FortressArmor_Boss());
        bound += Bind(registry, "CollapseRoar_Boss",      SkillLibrary.CollapseRoar_Boss());
        bound += Bind(registry, "OverchargeMode_Boss",    SkillLibrary.OverchargeMode_Boss(),    SkillLibrary.OverchargeModeCondition_Boss());
        bound += Bind(registry, "MarkWave_Boss",          SkillLibrary.MarkWave_Boss());
        bound += Bind(registry, "SealChain_Boss",         SkillLibrary.SealChain_Boss());
        bound += Bind(registry, "BarrierBreaker_Boss",    SkillLibrary.BarrierBreaker_Boss());
        bound += Bind(registry, "RuptureMagazine_Boss",   SkillLibrary.RuptureMagazine_Boss());

        Debug.Log($"[SkillBinder] {bound}종 바인딩 완료");
    }

    // ── 단건 바인딩 ──────────────────────────────────────────
    // 성공 시 1, 실패 시 0 반환 (카운팅용)
    // step 이 null 이면 미구현 스킬 — SO 는 유지하되 카운트 제외
    private static int Bind(SkillRegistry registry, string skillId, SkillStep step,
                            SkillCondition condition = null)
    {
        var def = registry.Get(skillId);
        if (def == null) return 0;   // 아직 SO 미생성 — 무시

        def.RuntimeStep      = step;
        def.RuntimeCondition = condition;
        return step != null ? 1 : 0;
    }
}
