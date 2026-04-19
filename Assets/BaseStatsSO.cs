using UnityEngine;

[CreateAssetMenu(fileName = "BaseStatsSO", menuName = "Scriptable Objects/BaseStatsSO")]
public class BaseStatsSO : ScriptableObject
{
    // 전투 스탯
    public float DamageTakenMultiplier = 1f;
    public float HealingReceivedMultiplier = 1f;

    // 이동 / 기동 스탯
    public float MoveControlMultiplier = 1f;

    // 로프 액션 스탯
    public float RopeCancelResistance = 0f;

    // 공격 / 스킬 스탯
    public float SkillCooldownMultiplier = 1f;
    public float ChannelDurationMultiplier = 1f;

    // 생존 / 회복 스탯
    public float SpawnInvulnerableDuration = 0f;

    // 상태이상 / 제어 저항 스탯
    public float StunDurationMultiplier = 1f;
    public float CrowdControlPower = 1f;
    public float CrowdControlResistance = 0f;
    public float HitStunResistance = 0f;
    public float DebuffDurationResistance = 0f;

    // 버프 / 디버프 적용 스탯
    public float DamageUpMultiplier = 1f;
    public float DefenseUpMultiplier = 1f;
    public float VulnerabilityBonus = 0f;
    public float ReflectRatio = 0f;

}
