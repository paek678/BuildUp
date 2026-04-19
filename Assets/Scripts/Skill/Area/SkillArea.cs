using System.Collections;
using UnityEngine;

// 지속 장판 프리팹에 붙는 컴포넌트
// 프리팹 구조:
//   SkillArea (이 스크립트)
//   └── Visual (MeshRenderer + MeshFilter — Cylinder 또는 Plane 권장)
//
// PersistentAreaPool에서 꺼내 Initialize 호출 → tickInterval마다 범위 내 ICombatant에 tickEffect 적용
// duration 경과 후 자동으로 풀 반환
public class SkillArea : MonoBehaviour, IPersistentArea
{
    [SerializeField] private Color _areaColor = new Color(1f, 0.2f, 0.2f, 0.35f); // 반투명 빨강

    private Renderer           _renderer;
    private PersistentAreaPool _pool;
    private Coroutine          _routine;

    // 초기화 시 채워지는 런타임 값
    private float     _radius;
    private float     _angleDeg;
    private AreaShape _shape;
    private SkillStep _tickEffect;
    private SkillContext _ctx;
    private Vector3   _forward;

    // ── 초기화 (풀에서 한 번만 실행) ────────────────────────
    private void Awake()
    {
        // 자식 오브젝트에서 Renderer 캐싱 (없으면 자기 자신 확인)
        _renderer = GetComponentInChildren<Renderer>();
    }

    public void SetPool(PersistentAreaPool pool) => _pool = pool;

    // ── IPersistentArea ──────────────────────────────────────

    public void Initialize(Vector3 forward, float radius, AreaShape shape, float angleDeg,
                           float duration, float tickInterval, SkillStep tickEffect, SkillContext ctx)
    {
        _forward    = forward;
        _radius     = radius;
        _shape      = shape;
        _angleDeg   = angleDeg;
        _tickEffect = tickEffect;
        _ctx        = ctx;

        ApplyVisual(forward, radius, shape);

        if (_routine != null) StopCoroutine(_routine);
        _routine = StartCoroutine(AreaRoutine(duration, tickInterval));
    }

    // ── 비주얼 적용 ──────────────────────────────────────────
    // 자식 메시 오브젝트(Visual)의 스케일로 범위를 표현
    private void ApplyVisual(Vector3 forward, float radius, AreaShape shape)
    {
        if (_renderer != null) _renderer.material.color = _areaColor;

        Transform visual = transform.childCount > 0 ? transform.GetChild(0) : transform;

        switch (shape)
        {
            case AreaShape.Circle:
                visual.localScale = new Vector3(radius * 2f, 0.02f, radius * 2f);
                break;

            case AreaShape.Cone:
                // 부채꼴은 원형 기반으로 스케일 설정 후 시전 방향으로 회전
                // 실제 각도 필터링은 TickArea에서 처리
                visual.localScale = new Vector3(radius * 2f, 0.02f, radius * 2f);
                if (forward != Vector3.zero)
                    transform.rotation = Quaternion.LookRotation(forward);
                break;

            case AreaShape.Line:
                // 선형 장판: 폭 0.5 고정, 길이 = radius * 2
                visual.localScale = new Vector3(0.5f, 0.02f, radius * 2f);
                if (forward != Vector3.zero)
                    transform.rotation = Quaternion.LookRotation(forward);
                break;
        }
    }

    // ── 틱 루프 ──────────────────────────────────────────────
    private IEnumerator AreaRoutine(float duration, float tickInterval)
    {
        var wait    = new WaitForSeconds(tickInterval);
        float elapsed = 0f;

        while (elapsed < duration)
        {
            yield return wait;
            elapsed += tickInterval;
            TickArea();
        }

        ReturnToPool();
    }

    private void TickArea()
    {
        if (_ctx == null) return;

        ICombatant original    = _ctx.PrimaryTarget;
        bool       originalHit = _ctx.HitLanded;
        var colliders = Physics.OverlapSphere(transform.position, _radius);

        foreach (var col in colliders)
        {
            if (!col.TryGetComponent<ICombatant>(out var target)) continue;
            if (ReferenceEquals(target, _ctx.Caster)) continue;

            if (_shape == AreaShape.Cone)
            {
                Vector3 toTarget = col.transform.position - transform.position;
                if (Vector3.Angle(_forward, toTarget) > _angleDeg * 0.5f) continue;
            }

            _ctx.PrimaryTarget = target;
            _ctx.RefreshSnapshot();
            _tickEffect?.Invoke(_ctx);
        }

        _ctx.PrimaryTarget = original;
        _ctx.HitLanded     = originalHit;
    }

    // ── IPoolable ────────────────────────────────────────────

    public void OnSpawn()
    {
        if (_renderer != null) _renderer.material.color = _areaColor;
    }

    public void OnDespawn()
    {
        if (_routine != null)
        {
            StopCoroutine(_routine);
            _routine = null;
        }
        _tickEffect = null;
        _ctx        = null;
    }

    private void ReturnToPool() => _pool?.Return(this);
}
