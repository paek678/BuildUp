using UnityEngine;

// 스킬 부품 37종 전체 목록
// 스킬 조립 파일에서 using static SkillComponents; 선언 후 번호/이름으로 바로 사용
//
// SkillStep      반환 : 실행 부품 (Primitive / Wrapper)
// SkillCondition 반환 : 조건 부품 — TriggerOnCondition(#33) 의 condition 인자로 사용
//
// ══════════════════════════════════════════════════════════════════
//  #   함수명                분류          대상
// ──────────────────────────────────────────────────────────────────
//  1   DealDamage            기본 전투      대상
//  2   DealMultiHitDamage    기본 전투      대상
//  3   ApplyDamageOverTime   기본 전투      대상
//  4   RecoverHP             생존           시전자
//  5   ApplyHPRegen          생존           시전자
//  6   GainShield            생존           시전자
//  7   ReflectDamage         생존           시전자
//  8   ApplyInvulnerability  생존           시전자
//  9   ApplyStun             상태이상       대상
// 10   ApplyHitStun          상태이상       대상
// 11   ApplySlow             상태이상       대상
// 12   ApplyRoot             상태이상       대상
// 13   ApplyVulnerability    상태이상       대상
// 14   ApplyDamageUp         능력 변화      시전자
// 15   ApplyDamageDown       능력 변화      대상
// 16   ApplyDefenseUp        능력 변화      시전자
// 17   ApplyDefenseDown      능력 변화      대상
// 18   ApplyKnockback        위치 제어      대상
// 19   PullTarget            위치 제어      대상
// 20   ApplyInArea           범위 래퍼      범위 내 전체
// 21   ApplyBuff             전투 구조      시전자
// 22   ApplyDebuff           전투 구조      대상
// 23   CheckParry            핵심 시스템    시전자
// 24   ApplyParryReward      핵심 시스템    시전자
// 25   ApplySilence          상태이상       대상
// 26   CleanseStatus         해제           시전자
// 27   ApplyAntiHeal         능력 변화      대상
// 28   DealShieldBreakDamage 방어 대응      대상
// 29   ExecuteBelowHP        처형           대상
// 30   DispelBuff            해제           대상
// 31   SpawnPersistentArea   범위 래퍼      ctx.CastPosition
// 32   LaunchProjectile      투사체 래퍼    ctx.CastDirection
// 33   TriggerOnCondition    흐름 제어      —
// 34   TriggerOnHit          흐름 제어      —
// 35   DealDirectionalHit    기본 전투      전방 부채꼴
// 36   MoveSelf              이동           시전자
// 37   CheckTargetDistance   감지 (Cond)    —
// ══════════════════════════════════════════════════════════════════

public static class SkillComponents
{
    // ══════════════════════════════════════════════════════════════
    // 기본 전투
    // ══════════════════════════════════════════════════════════════

    // ── 1. 단일 피해 ─────────────────────────────────────────────
    public static SkillStep DealDamage(float amount) =>
        ctx =>
        {
            ctx.PrimaryTarget?.TakeDamage(amount, ctx.Caster);
            ctx.AddLog($"DealDamage({amount})");
        };

    // ── 2. 다단 히트 ─────────────────────────────────────────────
    public static SkillStep DealMultiHitDamage(float amount, int hits) =>
        ctx =>
        {
            if (ctx.PrimaryTarget == null) return;
            for (int i = 0; i < hits; i++)
                ctx.PrimaryTarget.TakeDamage(amount, ctx.Caster);
            ctx.AddLog($"DealMultiHitDamage({amount}x{hits})");
        };

    // ── 3. 지속 피해 ─────────────────────────────────────────────
    public static SkillStep ApplyDamageOverTime(float duration, float dps) =>
        ctx =>
        {
            ctx.PrimaryTarget?.ApplyStatus(StatusType.DamageOverTime, duration, dps);
            ctx.AddLog($"ApplyDamageOverTime({duration}s,{dps}/s)");
        };

    // ── 35. 방향 타격 ─────────────────────────────────────────────
    // 전방 부채꼴 범위 내 ICombatant 전부 타격, ctx.HitLanded 기록
    public static SkillStep DealDirectionalHit(float damage, float range, float angleDeg, int layerMask = -1) =>
        ctx =>
        {
            if (ctx.Caster == null) return;

            Vector3 origin  = ctx.Caster.Transform.position;
            Vector3 forward = ctx.CastDirection != Vector3.zero
                ? ctx.CastDirection.normalized
                : ctx.Caster.Transform.forward;

            var  saved     = ctx.PrimaryTarget;
            bool anyHit    = false;
            var  processed = new System.Collections.Generic.HashSet<ICombatant>();

            foreach (var col in Physics.OverlapSphere(origin, range, layerMask))
            {
                var target = col.GetComponentInParent<ICombatant>();
                if (target == null || ReferenceEquals(target, ctx.Caster)) continue;
                if (!processed.Add(target)) continue;
                if (Vector3.Angle(forward, col.transform.position - origin) > angleDeg * 0.5f) continue;

                ctx.PrimaryTarget = target;
                ctx.HitLanded     = true;
                ctx.RefreshSnapshot();
                target.TakeDamage(damage, ctx.Caster);
                anyHit = true;
            }

            if (!anyHit) { ctx.PrimaryTarget = saved; ctx.HitLanded = false; }
            else         ctx.OnHitRecorded?.Invoke();
            SkillRangeDisplay.Instance?.ShowCone(origin, forward, range, angleDeg, anyHit);
            ctx.AddLog($"DealDirectionalHit(dmg:{damage},r:{range},a:{angleDeg})=>{(anyHit ? "HIT" : "MISS")}");
        };

    // ══════════════════════════════════════════════════════════════
    // 생존
    // ══════════════════════════════════════════════════════════════

    // ── 4. 체력 회복 ──────────────────────────────────────────────
    public static SkillStep RecoverHP(float amount) =>
        ctx =>
        {
            ctx.Caster?.RecoverHP(amount);
            ctx.AddLog($"RecoverHP({amount})");
        };

    // ── 5. 체력 재생 ──────────────────────────────────────────────
    public static SkillStep ApplyHPRegen(float duration, float perSecond) =>
        ctx =>
        {
            ctx.Caster?.ApplyStatus(StatusType.HPRegen, duration, perSecond);
            ctx.AddLog($"ApplyHPRegen({duration}s,{perSecond}/s)");
        };

    // ── 6. 방어막 획득 ────────────────────────────────────────────
    public static SkillStep GainShield(float amount) =>
        ctx =>
        {
            ctx.Caster?.AddShield(amount);
            ctx.AddLog($"GainShield({amount})");
        };

    // ── 7. 피해 반사 ──────────────────────────────────────────────
    // Reflecting 상태 적용 → PlayerController.TakeDamage 에서 반사 처리
    public static SkillStep ReflectDamage(float duration, float ratio) =>
        ctx =>
        {
            ctx.Caster?.ApplyStatus(StatusType.Reflecting, duration, ratio);
            ctx.AddLog($"ReflectDamage({duration}s,{ratio * 100f:F0}%)");
        };

    // ── 8. 무적 ───────────────────────────────────────────────────
    public static SkillStep ApplyInvulnerability(float duration) =>
        ctx =>
        {
            ctx.Caster?.ApplyStatus(StatusType.Invulnerable, duration);
            ctx.AddLog($"ApplyInvulnerability({duration}s)");
        };

    // ══════════════════════════════════════════════════════════════
    // 상태이상
    // ══════════════════════════════════════════════════════════════

    // ── 9. 스턴 ───────────────────────────────────────────────────
    public static SkillStep ApplyStun(float duration) =>
        ctx =>
        {
            ctx.PrimaryTarget?.ApplyStatus(StatusType.Stunned, duration);
            ctx.AddLog($"ApplyStun({duration}s)");
        };

    // ── 10. 경직 ──────────────────────────────────────────────────
    public static SkillStep ApplyHitStun(float duration) =>
        ctx =>
        {
            ctx.PrimaryTarget?.ApplyStatus(StatusType.HitStun, duration);
            ctx.AddLog($"ApplyHitStun({duration}s)");
        };

    // ── 11. 둔화 ──────────────────────────────────────────────────
    // ratio : 0~1 (0.3 = 30% 감소)
    public static SkillStep ApplySlow(float duration, float ratio) =>
        ctx =>
        {
            ctx.PrimaryTarget?.ApplyStatus(StatusType.Slowed, duration, ratio);
            ctx.AddLog($"ApplySlow({duration}s,{ratio * 100f:F0}%)");
        };

    // ── 12. 속박 ──────────────────────────────────────────────────
    public static SkillStep ApplyRoot(float duration) =>
        ctx =>
        {
            ctx.PrimaryTarget?.ApplyStatus(StatusType.Rooted, duration);
            ctx.AddLog($"ApplyRoot({duration}s)");
        };

    // ── 13. 취약 ──────────────────────────────────────────────────
    // ratio : 추가 받는 피해 비율 (0.2 = 20% 추가)
    public static SkillStep ApplyVulnerability(float duration, float ratio) =>
        ctx =>
        {
            ctx.PrimaryTarget?.ApplyStatus(StatusType.Vulnerable, duration, ratio);
            ctx.AddLog($"ApplyVulnerability({duration}s,+{ratio * 100f:F0}%)");
        };

    // ── 25. 침묵 ──────────────────────────────────────────────────
    public static SkillStep ApplySilence(float duration) =>
        ctx =>
        {
            ctx.PrimaryTarget?.ApplyStatus(StatusType.Silence, duration);
            ctx.AddLog($"ApplySilence({duration}s)");
        };

    // ── 27. 치유 감소 ─────────────────────────────────────────────
    // ratio : 0~1 (0.5 = 치유량 50% 감소)
    public static SkillStep ApplyAntiHeal(float duration, float ratio) =>
        ctx =>
        {
            ctx.PrimaryTarget?.ApplyStatus(StatusType.AntiHeal, duration, ratio);
            ctx.AddLog($"ApplyAntiHeal({duration}s,{ratio * 100f:F0}%)");
        };

    // ══════════════════════════════════════════════════════════════
    // 능력 변화 (버프 / 디버프)
    // ══════════════════════════════════════════════════════════════

    // ── 14. 공격력 증가 ───────────────────────────────────────────
    public static SkillStep ApplyDamageUp(float duration, float ratio) =>
        ctx =>
        {
            ctx.Caster?.ApplyBuff(BuffType.DamageUp, duration, ratio);
            ctx.AddLog($"ApplyDamageUp({duration}s,+{ratio}%)");
        };

    // ── 15. 공격력 감소 ───────────────────────────────────────────
    public static SkillStep ApplyDamageDown(float duration, float ratio) =>
        ctx =>
        {
            ctx.PrimaryTarget?.ApplyDebuff(DebuffType.DamageDown, duration, ratio);
            ctx.AddLog($"ApplyDamageDown({duration}s,{ratio}%)");
        };

    // ── 16. 방어력 증가 ───────────────────────────────────────────
    public static SkillStep ApplyDefenseUp(float duration, float ratio) =>
        ctx =>
        {
            ctx.Caster?.ApplyBuff(BuffType.DefenseUp, duration, ratio);
            ctx.AddLog($"ApplyDefenseUp({duration}s,+{ratio}%)");
        };

    // ── 17. 방어력 감소 ───────────────────────────────────────────
    public static SkillStep ApplyDefenseDown(float duration, float ratio) =>
        ctx =>
        {
            ctx.PrimaryTarget?.ApplyDebuff(DebuffType.DefenseDown, duration, ratio);
            ctx.AddLog($"ApplyDefenseDown({duration}s,{ratio}%)");
        };

    // ── 21. 버프 적용 ─────────────────────────────────────────────
    public static SkillStep ApplyBuff(float duration, BuffType type, float value) =>
        ctx =>
        {
            ctx.Caster?.ApplyBuff(type, duration, value);
            ctx.AddLog($"ApplyBuff({type},{duration}s,{value})");
        };

    // ── 22. 디버프 적용 ───────────────────────────────────────────
    public static SkillStep ApplyDebuff(float duration, DebuffType type, float value) =>
        ctx =>
        {
            ctx.PrimaryTarget?.ApplyDebuff(type, duration, value);
            ctx.AddLog($"ApplyDebuff({type},{duration}s,{value})");
        };

    // ══════════════════════════════════════════════════════════════
    // 위치 제어
    // ══════════════════════════════════════════════════════════════

    // ── 18. 넉백 ──────────────────────────────────────────────────
    // 시전자 → 대상 방향으로 distance만큼 밀어냄
    public static SkillStep ApplyKnockback(float distance) =>
        ctx =>
        {
            if (ctx.PrimaryTarget == null || ctx.Caster == null) return;
            Vector3 dir = (ctx.PrimaryTarget.Transform.position - ctx.Caster.Transform.position).normalized;
            ctx.PrimaryTarget.Knockback(dir, distance);
            ctx.AddLog($"ApplyKnockback({distance}m)");
        };

    // ── 19. 끌어당기기 ────────────────────────────────────────────
    // 대상을 시전자 위치 방향으로 distance만큼 당김
    public static SkillStep PullTarget(float distance, float duration) =>
        ctx =>
        {
            if (ctx.PrimaryTarget == null || ctx.Caster == null) return;
            ctx.PrimaryTarget.Pull(ctx.Caster.Transform.position, distance, duration);
            ctx.AddLog($"PullTarget({distance}m,{duration}s)");
        };

    // ── 36. 자기 이동 ─────────────────────────────────────────────
    // ctx.CastDirection 방향으로 distance만큼 이동
    public static SkillStep MoveSelf(float distance, float duration, MoveType moveType) =>
        ctx =>
        {
            if (ctx.Caster == null) return;
            ctx.Caster.MoveBy(ctx.CastDirection, distance, duration, moveType);
            ctx.AddLog($"MoveSelf({moveType},{distance}m,{duration}s)");
        };

    // ══════════════════════════════════════════════════════════════
    // 방어 대응 / 처형 / 해제
    // ══════════════════════════════════════════════════════════════

    // ── 28. 실드 파괴 피해 ────────────────────────────────────────
    // 실드 있으면 multiplier 배율 피해, 초과분은 HP 감소
    public static SkillStep DealShieldBreakDamage(float amount, float multiplier) =>
        ctx =>
        {
            ctx.PrimaryTarget?.TakeShieldBreakDamage(amount, multiplier, ctx.Caster);
            ctx.AddLog($"DealShieldBreakDamage({amount},x{multiplier})");
        };

    // ── 29. 처형 피해 ─────────────────────────────────────────────
    // hpThreshold % 이하일 때 bonusDamage 추가 적용
    public static SkillStep ExecuteBelowHP(float hpThreshold, float bonusDamage) =>
        ctx =>
        {
            if (ctx.PrimaryTarget == null) return;
            if (ctx.TargetHpPercent * 100f < hpThreshold)
            {
                ctx.PrimaryTarget.TakeDamage(bonusDamage, ctx.Caster);
                ctx.AddLog($"ExecuteBelowHP(<{hpThreshold}%,+{bonusDamage})");
            }
        };

    // ── 26. 정화 ──────────────────────────────────────────────────
    // 시전자의 상태이상을 count개 제거 (count=0 이면 전체)
    public static SkillStep CleanseStatus(CleanseType type, int count) =>
        ctx =>
        {
            ctx.Caster?.RemoveStatuses(type, count);
            ctx.AddLog($"CleanseStatus({type},{count})");
        };

    // ── 30. 버프 제거 ─────────────────────────────────────────────
    // 대상의 버프를 count개 제거 (count=0 이면 전체)
    public static SkillStep DispelBuff(DispelType type, int count) =>
        ctx =>
        {
            ctx.PrimaryTarget?.RemoveBuffs(type, count);
            ctx.AddLog($"DispelBuff({type},{count})");
        };

    // ══════════════════════════════════════════════════════════════
    // 핵심 시스템 — 패링
    // ══════════════════════════════════════════════════════════════

    // ── 23. 패링 판정 ─────────────────────────────────────────────
    // ctx.Caster.IsParrying && 입력 후 ParryWindow 이내 → ctx.HitLanded = true
    // ctx.ParryInputTime : PlayerController가 패링 입력 시 Time.time 기록
    public static SkillStep CheckParry() =>
        ctx =>
        {
            if (ctx.Caster == null) { ctx.HitLanded = false; return; }
            bool inWindow = (Time.time - ctx.ParryInputTime) <= ctx.Caster.ParryWindow;
            ctx.HitLanded = ctx.Caster.IsParrying && inWindow;
            ctx.AddLog($"CheckParry(window:{ctx.Caster.ParryWindow}s)=>{ctx.HitLanded}");
        };

    // ── 24. 패링 성공 보상 ────────────────────────────────────────
    // ctx.PrimaryTarget = 패링 당한 공격자 → Counter/HitStun 시 해당 대상에게 효과 적용
    public static SkillStep ApplyParryReward(ParryRewardType type, float value, float duration) =>
        ctx =>
        {
            ctx.Caster?.NotifyParryReward(type, value, duration, ctx.PrimaryTarget);
            ctx.AddLog($"ApplyParryReward({type},v:{value},d:{duration}s)");
        };

    // ══════════════════════════════════════════════════════════════
    // 범위 래퍼
    // ══════════════════════════════════════════════════════════════

    // ── 20. 범위 지정 래퍼 ────────────────────────────────────────
    // ctx.CastPosition 중심으로 radius 내 ICombatant 전부에 inner 적용
    // angleDeg : Cone 전용 — 부채꼴 전체 각도 (360 = Circle 동일)
    // lineWidth: Line 전용 — 전방 직선 좌우 허용 폭 (m)
    public static SkillStep ApplyInArea(float radius, AreaShape shape, SkillStep inner,
                                        float angleDeg = 360f, float lineWidth = 0.5f, int layerMask = -1) =>
        ctx =>
        {
            var     saved     = ctx.PrimaryTarget;
            bool    anyHit    = false;
            var     processed = new System.Collections.Generic.HashSet<ICombatant>();
            Vector3 forward   = ctx.CastDirection != Vector3.zero
                ? ctx.CastDirection.normalized
                : Vector3.forward;

            foreach (var col in Physics.OverlapSphere(ctx.CastPosition, radius, layerMask))
            {
                var target = col.GetComponentInParent<ICombatant>();
                if (target == null || ReferenceEquals(target, ctx.Caster)) continue;
                if (!processed.Add(target)) continue;

                Vector3 toTarget = col.transform.position - ctx.CastPosition;

                if (shape == AreaShape.Cone)
                {
                    if (Vector3.Angle(forward, toTarget) > angleDeg * 0.5f) continue;
                }
                else if (shape == AreaShape.Line)
                {
                    float forwardDot = Vector3.Dot(forward, toTarget);
                    if (forwardDot < 0f) continue;
                    Vector3 side = toTarget - forward * forwardDot;
                    if (side.magnitude > lineWidth) continue;
                }

                ctx.PrimaryTarget = target;
                ctx.RefreshSnapshot();
                inner?.Invoke(ctx);
                anyHit = true;
            }

            ctx.HitLanded     = anyHit;
            if (anyHit) ctx.OnHitRecorded?.Invoke();
            ctx.PrimaryTarget = saved;
            switch (shape)
            {
                case AreaShape.Cone:
                    SkillRangeDisplay.Instance?.ShowCone(ctx.CastPosition, forward, radius, angleDeg, anyHit);
                    break;
                case AreaShape.Line:
                    SkillRangeDisplay.Instance?.ShowLine(ctx.CastPosition, forward, radius);
                    break;
                default:
                    SkillRangeDisplay.Instance?.ShowCircle(ctx.CastPosition, radius, anyHit);
                    break;
            }
            ctx.AddLog($"ApplyInArea(r:{radius},{shape},angle:{angleDeg},width:{lineWidth})=>{(anyHit ? "HIT" : "MISS")}");
        };

    // ── 31. 지속 장판 생성 ────────────────────────────────────────
    // ctx.CastPosition 에 장판 소환, tickInterval마다 범위 내 대상에게 tickAction 적용
    // 씬에 PersistentAreaManager + PersistentAreaPool 배치 필요
    public static SkillStep SpawnPersistentArea(float duration, float radius, AreaShape shape,
                                                float tickInterval, SkillStep tickAction,
                                                float angleDeg = 360f) =>
        ctx =>
        {
            if (PersistentAreaManager.Instance == null)
            {
                Debug.LogWarning("[SpawnPersistentArea] PersistentAreaManager 씬에 없음");
                return;
            }

            Vector3 pos     = ctx.CastPosition  != Vector3.zero ? ctx.CastPosition            : ctx.Caster?.Transform.position ?? Vector3.zero;
            Vector3 forward = ctx.CastDirection != Vector3.zero ? ctx.CastDirection.normalized : Vector3.forward;

            PersistentAreaManager.Instance.Spawn(pos, forward, radius, shape, angleDeg,
                                                 duration, tickInterval, tickAction, ctx);

            if (shape == AreaShape.Cone)
                SkillRangeDisplay.Instance?.ShowCone(pos, forward, radius, angleDeg, true);
            else
                SkillRangeDisplay.Instance?.ShowCircle(pos, radius, true);

            ctx.AddLog($"SpawnPersistentArea(r:{radius},{shape},{angleDeg}°,{duration}s,tick:{tickInterval}s)");
        };

    // ══════════════════════════════════════════════════════════════
    // 투사체 래퍼
    // ══════════════════════════════════════════════════════════════

    // ── 32. 투사체 발사 ───────────────────────────────────────────
    // ctx.CastDirection 방향으로 투사체 발사, 적중 시 onImpact 실행
    // pierce=true : 관통 (첫 적중 후 계속 날아감)
    // 씬에 ProjectilePool 배치 필요
    public static SkillStep LaunchProjectile(float speed, float range, bool pierce, SkillStep onImpact) =>
        ctx =>
        {
            if (ctx.Caster == null) return;
            if (ProjectilePool.Instance == null)
            {
                Debug.LogWarning("[LaunchProjectile] ProjectilePool 씬에 없음");
                return;
            }

            Vector3 origin = ctx.CastPosition  != Vector3.zero ? ctx.CastPosition            : ctx.Caster.Transform.position;
            Vector3 dir    = ctx.CastDirection  != Vector3.zero ? ctx.CastDirection.normalized : ctx.Caster.Transform.forward;

            var proj = ProjectilePool.Instance.Get(origin, Quaternion.LookRotation(dir));
            proj.SetHitCallback(onImpact, ctx, pierce);
            proj.Launch(dir, speed, range);

            SkillRangeDisplay.Instance?.ShowLine(origin, dir, range);
            ctx.AddLog($"LaunchProjectile(spd:{speed},r:{range},pierce:{pierce})");
        };

    // ══════════════════════════════════════════════════════════════
    // 흐름 제어
    // ══════════════════════════════════════════════════════════════

    // ── 33. 조건 분기 ─────────────────────────────────────────────
    // condition 결과에 따라 onTrue / onFalse 분기 실행
    public static SkillStep TriggerOnCondition(string name, SkillCondition condition,
                                               SkillStep onTrue, SkillStep onFalse = null) =>
        ctx =>
        {
            bool result = condition?.Invoke(ctx) ?? false;
            ctx.AddLog($"[Cond:{name}]=>{result}");
            (result ? onTrue : onFalse)?.Invoke(ctx);
        };

    // ── 34. 적중 시 후속 실행 ─────────────────────────────────────
    // ctx.HitLanded 를 DealDirectionalHit(#35) / CheckParry(#23) / LaunchProjectile(#32) 가 기록
    // onHit / onMiss 둘 다 선택 — 한쪽만 제공하는 분기형 사용 허용
    public static SkillStep TriggerOnHit(SkillStep onHit = null, SkillStep onMiss = null) =>
        ctx =>
        {
            ctx.AddLog($"[TriggerOnHit] HitLanded={ctx.HitLanded}");
            (ctx.HitLanded ? onHit : onMiss)?.Invoke(ctx);
        };

    // ══════════════════════════════════════════════════════════════
    // 감지 조건 (SkillCondition)
    // ══════════════════════════════════════════════════════════════

    // ── 37. 거리 판정 ─────────────────────────────────────────────
    // minDistance 이상 maxDistance 이하일 때 true
    public static SkillCondition CheckTargetDistance(float minDistance, float maxDistance) =>
        ctx => ctx.TargetDistance >= minDistance && ctx.TargetDistance <= maxDistance;
}
