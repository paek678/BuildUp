using UnityEngine;

[CreateAssetMenu(fileName = "PlayerStatsSO", menuName = "Scriptable Objects/PlayerStatsSO")]
public class PlayerStatsSO : BaseStatsSO

{
    // 기본 전투 스탯
    public float MaxHP = 100f;
    public float CurrentHP = 100f;
    public float BaseDamage = 10f;
    public float BaseDefense = 5f;

    // 이동 / 기동 스탯
    public float MoveSpeed = 5f;
    public float TurnSpeed = 180f;
    public float ActionSpeed = 1f;
    public float MoveAcceleration = 10f;
    public float MoveDeceleration = 10f;

    // 로프 액션 스탯
    public float RopeRange = 10f;
    public float RopeSpeed = 15f;
    public float RopeCooldown = 5f;
    public float RopeAttachTime = 0.2f;
    public float RopeReleaseRecovery = 0.5f;

    // 공격 / 스킬 스탯
    public float AttackAreaScale = 1f;
    public float SkillPower = 1f;

    // 패링 / 대응 스탯
    public float ParryWindow = 0.3f;
    public float ParryCooldown = 2f;
    public float CounterWindow = 0.5f;

    // 생존 / 회복 스탯
    public float ShieldMax = 50f;
    public float CurrentShield = 0f;
    public float HPRegenRate = 1f;
    public float ReviveTime = 5f;

    // 협동 / 보스전 전용 스탯
    public float AggroWeight = 1f;

}
