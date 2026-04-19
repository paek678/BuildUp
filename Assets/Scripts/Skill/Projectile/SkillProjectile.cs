using UnityEngine;

// 스킬 투사체 프리팹에 붙는 컴포넌트
// ProjectilePool에서 꺼내서 Launch → 콜라이더 이벤트 → onHit(SkillStep) 실행 → 풀 반환
[RequireComponent(typeof(Rigidbody))]
[RequireComponent(typeof(Collider))]
public class SkillProjectile : MonoBehaviour, IProjectile
{
    [SerializeField] private Color _color = Color.red;

    private Rigidbody   _rb;
    private Collider    _col;
    private Renderer    _renderer;
    private ProjectilePool _pool;

    private SkillStep   _onHit;
    private SkillContext _ctx;
    private bool        _pierce;
    private float       _range;
    private Vector3     _spawnPos;
    private bool        _active;

    // ── 초기화 (풀에서 한 번만 실행) ────────────────────────
    private void Awake()
    {
        _rb           = GetComponent<Rigidbody>();
        _col          = GetComponent<Collider>();
        _renderer     = GetComponentInChildren<Renderer>();
        _rb.useGravity = false;
        _col.isTrigger = true;
    }

    // ProjectilePool이 생성 시 주입
    public void SetPool(ProjectilePool pool) => _pool = pool;

    // ── IProjectile ──────────────────────────────────────────

    public void Launch(Vector3 direction, float speed, float range)
    {
        _range    = range;
        _spawnPos = transform.position;
        _active   = true;
        _rb.linearVelocity = direction.normalized * speed;
    }

    public void SetHitCallback(SkillStep onHit, SkillContext ctx, bool pierce)
    {
        _onHit  = onHit;
        _ctx    = ctx;
        _pierce = pierce;
    }

    // ── 수명 체크 ────────────────────────────────────────────
    private void Update()
    {
        if (!_active) return;
        if (Vector3.Distance(_spawnPos, transform.position) >= _range)
            ReturnToPool();
    }

    // ── 충돌 이벤트 ──────────────────────────────────────────
    private void OnTriggerEnter(Collider other)
    {
        if (!_active) return;
        if (!other.TryGetComponent<ICombatant>(out var target)) return;
        if (_ctx != null && ReferenceEquals(target, _ctx.Caster)) return;

        if (_ctx != null)
        {
            _ctx.PrimaryTarget = target;
            _ctx.HitLanded     = true;
            _ctx.CastPosition  = transform.position;
            _ctx.RefreshSnapshot();
        }

        _onHit?.Invoke(_ctx);

        if (!_pierce) ReturnToPool();
    }

    // ── IPoolable ────────────────────────────────────────────

    public void OnSpawn()
    {
        _active            = false;
        _onHit             = null;
        _ctx               = null;
        _pierce            = false;
        _rb.linearVelocity = Vector3.zero;
        if (_renderer != null) _renderer.material.color = _color;
    }

    public void OnDespawn()
    {
        _active            = false;
        _rb.linearVelocity = Vector3.zero;
    }

    // ── 풀 반환 ──────────────────────────────────────────────
    private void ReturnToPool()
    {
        _active = false;
        _pool?.Return(this);
    }
}
