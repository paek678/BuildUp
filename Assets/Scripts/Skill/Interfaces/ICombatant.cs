using UnityEngine;

// 스킬 시스템이 플레이어/보스를 다루는 공통 인터페이스
// PlayerController, BossController 모두 이 인터페이스를 구현해야 한다
public interface ICombatant
{
    // ── 참조 ────────────────────────────────────────────────
    Transform  Transform  { get; }
    GameObject GameObject { get; }

    // ── 상태 읽기 ────────────────────────────────────────────
    float MaxHP            { get; }
    float CurrentHPPercent { get; }   // 0 ~ 1
    float Shield           { get; }
    bool  IsAlive          { get; }
    bool  IsCasting        { get; }   // 차징 / 채널링 / 패턴 준비 중
    bool  IsParrying       { get; }   // 현재 패링 입력 윈도우 중
    float ParryWindow      { get; }   // 패링 유효 판정 시간 (PlayerStatsSO.ParryWindow)

    // ── 피해 / 회복 ──────────────────────────────────────────
    // attacker : 공격자 참조 — 패링 반격/경직, 피해 반사 처리에 사용
    void TakeDamage(float amount, ICombatant attacker = null);

    // 보호막 우선 소진, 보호막 대상에게 multiplier 배율 추가 피해
    void TakeShieldBreakDamage(float amount, float multiplier, ICombatant attacker = null);

    void RecoverHP(float amount);
    void AddShield(float amount);

    // ── 상태이상 ─────────────────────────────────────────────
    // value 의미는 StatusType에 따라 다름
    // (DamageOverTime → DPS, Slowed → 감소율, Reflecting → 반사율 등)
    void ApplyStatus(StatusType type, float duration, float value = 0f);
    bool HasStatus(StatusType type);

    // ── 버프 / 디버프 ────────────────────────────────────────
    void ApplyBuff  (BuffType   type, float duration, float value);
    void ApplyDebuff(DebuffType type, float duration, float value);

    // ── 정화 / 버프 제거 ─────────────────────────────────────
    void RemoveStatuses(CleanseType type, int count);
    void RemoveBuffs   (DispelType  type, int count);

    // ── 위치 제어 ────────────────────────────────────────────
    void Knockback(Vector3 direction, float distance);
    void Pull(Vector3 towardPosition, float distance, float duration);
    void MoveBy(Vector3 direction, float distance, float duration, MoveType moveType);

    // ── 패링 보상 알림 ───────────────────────────────────────
    // 패링 성공 판정 후 어떤 보상을 줄지 스킬 레이어에서 결정해서 통보
    // attacker : Counter/HitStun 보상 시 공격자에게 효과를 적용하기 위해 필요
    void NotifyParryReward(ParryRewardType rewardType, float value, float duration, ICombatant attacker = null);
}
