using UnityEngine;

[CreateAssetMenu(fileName = "BossStatsSO", menuName = "Scriptable Objects/BossStatsSO")]
public class BossStatsSO : BaseStatsSO

{
    // 보스 전용 스탯
    public float BossMaxHP = 1000f;
    public float BossCurrentHP = 1000f;
    public float BossBaseDamage = 50f;
    public float BossBaseDefense = 20f;

    [Tooltip("페이즈 전환 기준 체력 비율 (예: 0.75, 0.5, 0.25)")]
    public float[] BossPhaseThresholds;

    public float BossTelegraphTimeMultiplier = 1f;
    public float BossAggroSensitivity = 1f;

}
