// 전투 개체 행동 상태 FSM — 7종 배타적 상태
// 자세한 계층 / 전이 규칙은 STATE_MANAGER_DESIGN.md 참고
//
// 우선순위 (작을수록 강함):
//   Dead(0) > Stunned(1) > HitStun(2) > Parrying(3) > Casting(4) > Moving(5) > Idle(6)
//
// 스킬 시전 가능 상태 = { Idle, Moving } 만
public enum CombatantState
{
    Idle     = 0,
    Moving   = 1,
    Casting  = 2,
    Parrying = 3,
    HitStun  = 4,
    Stunned  = 5,
    Dead     = 6,
}
