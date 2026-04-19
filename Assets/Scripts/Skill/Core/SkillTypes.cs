// 스킬 시스템 전체에서 사용하는 기본 타입 정의
// SkillStep      : 실행 단위 (Primitive / Wrapper 모두 이 타입으로 통일)
// SkillCondition : 조건 판정 단위 — TriggerOnCondition(#33) 의 condition 인자

public delegate void SkillStep(SkillContext ctx);
public delegate bool SkillCondition(SkillContext ctx);

// ── 범위 형태 ──────────────────────────────────────────────────────
public enum AreaShape
{
    Circle,
    Cone,
    Line,
}

// ── 타겟 방식 ──────────────────────────────────────────────────────
public enum TargetType
{
    Single,
    Area,
    Self,
    Direction,
}

// ── 이동 방식 ──────────────────────────────────────────────────────
public enum MoveType
{
    Dash,
    Charge,
    Jump,
    Rope,
}

// ── 패링 보상 종류 ─────────────────────────────────────────────────
public enum ParryRewardType
{
    Counter,      // 공격자에게 반격 피해
    HitStun,      // 공격자에게 경직 부여
    Invulnerable, // 시전자에게 무적 부여
    Buff,         // 시전자에게 DamageUp 버프 부여
}

// ── 상태이상 ───────────────────────────────────────────────────────
public enum StatusType
{
    Stunned,        // 이동 불가 + 행동 불가
    HitStun,        // 짧은 경직 (이동 제한)
    Slowed,         // 이동 속도 감소
    Rooted,         // 이동 불가 (행동 가능)
    Vulnerable,     // 받는 피해 증가
    Silence,        // 스킬 사용 불가
    Invulnerable,   // 피해 무효
    Reflecting,     // 받는 피해를 공격자에게 반사
    HPRegen,        // 초당 HP 회복
    DamageOverTime, // 초당 피해 (DoT)
    AntiHeal,       // 회복량 감소
    Marked,         // 추가 피해 취약 표식
}

// ── 버프 종류 ──────────────────────────────────────────────────────
public enum BuffType
{
    DamageUp,      // 공격력 증가
    DefenseUp,     // 방어력 증가
    ParryWindowUp, // 패링 유효 시간 증가
    ParryRewardUp, // 패링 보상 강화
}

// ── 디버프 종류 ────────────────────────────────────────────────────
public enum DebuffType
{
    DamageDown,     // 공격력 감소
    DefenseDown,    // 방어력 감소
    SelfDefenseDown,// 자기 방어력 감소 (자해형)
    Mark,           // 취약 표식
}

// ── 정화 범위 ──────────────────────────────────────────────────────
public enum CleanseType
{
    All,            // 모든 상태이상
    Debuff,         // 디버프 계열만
    DamageOverTime, // DoT만
}

// ── 버프 제거 범위 ─────────────────────────────────────────────────
public enum DispelType
{
    All,         // 모든 버프
    DefenseBuff, // 방어 버프만
    OffenseBuff, // 공격 버프만
}
