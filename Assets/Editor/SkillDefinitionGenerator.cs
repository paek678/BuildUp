using UnityEngine;
using UnityEditor;
using System.IO;

public static class SkillDefinitionGenerator
{
    private const string SkillFolder   = "Assets/ScriptableObjects/Skills";
    private const string RegistryPath  = "Assets/ScriptableObjects/Skills/SkillRegistry.asset";

    [MenuItem("Tenebris/스킬 SO 전체 생성 (공용 12종 + 보스 12종)")]
    public static void GenerateAll()
    {
        if (!Directory.Exists(SkillFolder))
            Directory.CreateDirectory(SkillFolder);

        var registry = AssetDatabase.LoadAssetAtPath<SkillRegistry>(RegistryPath);
        if (registry == null)
        {
            registry = ScriptableObject.CreateInstance<SkillRegistry>();
            AssetDatabase.CreateAsset(registry, RegistryPath);
        }

        int created = 0;

        // ── 플레이어 공용 12종 ──────────────────────────────
        created += Create("ExecutionSpike",  "처형 송곳",  "좁은 범위 정확 타격. 적중 시 취약 + 처형 피해, 빗나가면 넓은 범위 재시도.",
            8f, 24f, TargetType.Direction, new[]{"Burst","Execute","Melee"}, new[]{"Shield","Heal"});

        created += Create("CrushingBarrage", "분쇄 연타",  "4단 연속 타격. 적중 시 실드 파괴 추가타, 빗나가면 광역 재시도.",
            6f, 24f, TargetType.Direction, new[]{"ShieldBreak","Melee","MultiHit"}, new[]{"Shield"});

        created += Create("ErosionField",    "침식 장판",  "유도 투사체 명중 지점에 2중 장판 생성. 지속 피해 + 치유 감소.",
            10f, 42f, TargetType.Single, new[]{"DOT","Zone","AntiHeal"}, new[]{"Heal","Regen"});

        created += Create("HuntingMark",     "사냥 표식",  "유도 투사체. 명중 시 피해 + 표식 디버프.",
            7f, 66f, TargetType.Single, new[]{"Mark","Ranged"}, new[]{"Stealth"});

        created += Create("SurvivalPulse",   "생존 맥동",  "저체력 시 즉시 회복 + 체력 재생 + 정화 1회.",
            14f, 0f, TargetType.Self, new[]{"Heal","Cleanse","Survival"}, null);

        created += Create("FortressArmor",   "요새 장갑",  "전방 타격. 적중 시 최대HP 비례 실드 획득, 빗나가면 광역 재시도.",
            8f, 24f, TargetType.Direction, new[]{"Shield","Melee"}, new[]{"ShieldBreak"});

        created += Create("SealChain",       "봉쇄 사슬",  "유도 투사체. 명중 시 피해 + 경직 + 침묵.",
            9f, 66f, TargetType.Single, new[]{"Silence","CC","Ranged"}, new[]{"Buff"});

        created += Create("CollapseRoar",    "붕괴 포효",  "자기 중심 범위 공격. 좁은 범위 우선(피해+방어력감소), 빗나가면 광역.",
            10f, 27f, TargetType.Area, new[]{"AOE","DefDown","Melee"}, new[]{"DefUp"});

        created += Create("BarrierBreaker",  "방벽 파쇄",  "유도 투사체. 실드 파괴 + 방어력 감소 + 본 피해.",
            8f, 66f, TargetType.Single, new[]{"ShieldBreak","DefDown","Ranged"}, new[]{"Shield","DefUp"});

        created += Create("OverchargeMode",  "과충전 모드", "저체력/페이즈 진입 시 공격력 +15%, 자기 방어력 -10%. 6초.",
            18f, 0f, TargetType.Self, new[]{"DamageUp","SelfBuff"}, null);

        created += Create("PiercingShot",    "관통 저격",  "직선 관통 투사체. 방어력 감소 + 고피해. 빗나가면 재발사.",
            10f, 66f, TargetType.Direction, new[]{"Pierce","DefDown","Ranged"}, new[]{"DefUp"});

        created += Create("RuptureMagazine", "파열 탄창",  "폭발 투사체. 취약 부여 + 고피해. 빗나가면 재발사.",
            9f, 66f, TargetType.Direction, new[]{"Vulnerable","AOE","Ranged"}, new[]{"DefUp"});

        // ── 보스 공용 12종 ──────────────────────────────────
        created += Create("ExecutionSpike_Boss",  "처형 송곳(보스)", "넓은 범위 처형 타격.",
            8f, 24f, TargetType.Direction, new[]{"Burst","Execute","Melee"}, new[]{"Shield","Heal"});

        created += Create("CrushingBarrage_Boss", "분쇄 연타(보스)", "4단 연속 + 실드 파괴.",
            6f, 24f, TargetType.Direction, new[]{"ShieldBreak","Melee","MultiHit"}, new[]{"Shield"});

        created += Create("ErosionField_Boss",    "침식 장판(보스)", "시전 위치에 2중 원형 장판.",
            10f, 42f, TargetType.Area, new[]{"DOT","Zone","AntiHeal"}, new[]{"Heal","Regen"});

        created += Create("SurvivalPulse_Boss",   "생존 맥동(보스)", "저체력 시 회복 + 재생 + 정화.",
            14f, 0f, TargetType.Self, new[]{"Heal","Cleanse","Survival"}, null);

        created += Create("FortressArmor_Boss",   "요새 장갑(보스)", "전방 타격 + 실드 획득.",
            8f, 24f, TargetType.Direction, new[]{"Shield","Melee"}, new[]{"ShieldBreak"});

        created += Create("CollapseRoar_Boss",    "붕괴 포효(보스)", "경직 + 방어력 감소 범위 공격.",
            10f, 27f, TargetType.Area, new[]{"AOE","CC","DefDown","Melee"}, new[]{"DefUp"});

        created += Create("OverchargeMode_Boss",  "과충전 모드(보스)", "페이즈 강화. 공격 +12%, 방어 -12%.",
            18f, 0f, TargetType.Self, new[]{"DamageUp","SelfBuff"}, null);

        created += Create("MarkWave_Boss",        "표식 파동(보스)", "전방 부채꼴 80도 / 5m 표식 부여.",
            8f, 33f, TargetType.Area, new[]{"Mark","AOE"}, new[]{"Cleanse"});

        created += Create("SealChain_Boss",       "봉쇄 사슬(보스)", "4방향 투사체 회피 강제.",
            10f, 42f, TargetType.Area, new[]{"Silence","CC","Ranged"}, new[]{"Buff"});

        created += Create("BarrierBreaker_Boss",  "방벽 파쇄(보스)", "관통 투사체. 실드 파괴 + 방어력 감소.",
            9f, 66f, TargetType.Direction, new[]{"ShieldBreak","DefDown","Pierce"}, new[]{"Shield","DefUp"});

        created += Create("RuptureMagazine_Boss", "파열 탄창(보스)", "8방향 폭발 패턴.",
            9f, 42f, TargetType.Area, new[]{"Vulnerable","AOE","Ranged"}, new[]{"DefUp"});

        // ── 빠진 보스 스킬 보완 ──────────────────────────────
        // 사냥 표식은 보스 버전이 "표식 파동"으로 대체되므로 별도 생성 불필요

        // ── SkillRegistry 에 전체 등록 ────────────────────────
        PopulateRegistry(registry);

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();

        Debug.Log($"[SkillDefinitionGenerator] {created}종 SO 생성/갱신 완료. 경로: {SkillFolder}");
    }

    private static void PopulateRegistry(SkillRegistry registry)
    {
        var guids = AssetDatabase.FindAssets("t:SkillDefinition", new[] { SkillFolder });
        var so = new SerializedObject(registry);
        var pool = so.FindProperty("_pool");
        pool.ClearArray();

        foreach (var guid in guids)
        {
            var path = AssetDatabase.GUIDToAssetPath(guid);
            var skill = AssetDatabase.LoadAssetAtPath<SkillDefinition>(path);
            if (skill == null) continue;

            pool.InsertArrayElementAtIndex(pool.arraySize);
            pool.GetArrayElementAtIndex(pool.arraySize - 1).objectReferenceValue = skill;
        }

        so.ApplyModifiedProperties();
        EditorUtility.SetDirty(registry);
        Debug.Log($"[SkillDefinitionGenerator] SkillRegistry 에 {pool.arraySize}종 등록 완료");
    }

    private static int Create(string id, string displayName, string desc,
                              float cooldown, float range, TargetType targetType,
                              string[] roleTags, string[] counterTags)
    {
        string path = $"{SkillFolder}/{id}.asset";
        var existing = AssetDatabase.LoadAssetAtPath<SkillDefinition>(path);

        if (existing != null)
        {
            existing.SkillId     = id;
            existing.DisplayName = displayName;
            existing.Description = desc;
            existing.Cooldown    = cooldown;
            existing.Range       = range;
            existing.TargetType  = targetType;
            existing.RoleTags    = roleTags;
            existing.CounterTags = counterTags;
            EditorUtility.SetDirty(existing);
            return 0;
        }

        var so = ScriptableObject.CreateInstance<SkillDefinition>();
        so.SkillId     = id;
        so.DisplayName = displayName;
        so.Description = desc;
        so.Cooldown    = cooldown;
        so.Range       = range;
        so.TargetType  = targetType;
        so.RoleTags    = roleTags;
        so.CounterTags = counterTags;

        AssetDatabase.CreateAsset(so, path);
        return 1;
    }
}
