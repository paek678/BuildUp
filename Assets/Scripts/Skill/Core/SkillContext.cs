using System.Collections.Generic;
using UnityEngine;

// 스킬 실행 중 모든 노드가 공유하는 런타임 정보
// 실행 시작 전 Caster / PrimaryTarget / CastPosition / CastDirection 을 채운 뒤
// SkillExecutor.Execute() 에 넘긴다
public class SkillContext
{
    // ── 시전자 / 대상 ────────────────────────────────────────────
    public ICombatant       Caster;
    public ICombatant       PrimaryTarget;
    public List<ICombatant> TargetList = new();

    // ── 위치 / 방향 ──────────────────────────────────────────────
    // CastPosition  : 스킬 발동 기준 지점 (시전자 위치, 착탄 지점 등 — Wrapper가 갱신)
    // CastDirection : 시전 방향 (플레이어 입력 또는 AI 방향)
    public Vector3 CastPosition;
    public Vector3 CastDirection;

    // ── 판정 결과 ────────────────────────────────────────────────
    // DealDirectionalHit(#35) / CheckParry(#23) / LaunchProjectile(#32) 가 기록
    // TriggerOnHit(#34) 이 이 값을 읽어 분기
    public bool HitLanded;

    // ── 대상 상태 스냅샷 (RefreshSnapshot 호출 시점 기준) ─────────
    public float TargetHpPercent;  // 0 ~ 1
    public float TargetDistance;   // Caster ↔ PrimaryTarget 거리 (m)
    public bool  TargetCasting;    // 대상이 시전 중인지 (IsCasting)

    // ── 패링 입력 시각 ───────────────────────────────────────────
    // PlayerController 가 패링 입력 시 Time.time 을 기록
    // CheckParry(#23) 에서 ParryWindow 이내인지 판정에 사용
    public float ParryInputTime;

    // ── 시간 ─────────────────────────────────────────────────────
    public float CurrentTime;

    // ── 실행 로그 ────────────────────────────────────────────────
    private readonly List<string> _log = new();

    public void AddLog(string msg) =>
        _log.Add($"[{CurrentTime:F2}] {msg}");

    public IReadOnlyList<string> GetLog() => _log;

    // ── 스냅샷 갱신 ──────────────────────────────────────────────
    // PrimaryTarget 이 바뀔 때마다 (ApplyInArea 순회 등) 호출
    public void RefreshSnapshot()
    {
        CurrentTime = Time.time;

        if (PrimaryTarget == null) return;

        TargetHpPercent = PrimaryTarget.CurrentHPPercent;
        TargetCasting   = PrimaryTarget.IsCasting;
        TargetDistance  = Caster != null
            ? Vector3.Distance(Caster.Transform.position, PrimaryTarget.Transform.position)
            : 0f;
    }
}
