using System.Collections.Generic;
using UnityEngine;

// 씬에 빈 GameObject를 만들고 이 컴포넌트를 붙인다.
// Inspector에서 SkillProjectile 프리팹과 초기 풀 크기를 지정.
// LaunchProjectile(#32) 부품이 이 풀을 참조해서 투사체를 꺼낸다.
public class ProjectilePool : MonoBehaviour
{
    public static ProjectilePool Instance { get; private set; }

    [SerializeField] private SkillProjectile _prefab;
    [SerializeField] private int _initialSize = 10;

    private readonly Queue<SkillProjectile> _available = new();

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;

        for (int i = 0; i < _initialSize; i++)
            CreateInstance();
    }

    // 풀에서 투사체 꺼내기 — 없으면 새로 생성 (Expandable)
    public SkillProjectile Get(Vector3 position, Quaternion rotation)
    {
        var obj = _available.Count > 0 ? _available.Dequeue() : CreateInstance();
        obj.transform.SetPositionAndRotation(position, rotation);
        obj.gameObject.SetActive(true);
        obj.OnSpawn();
        return obj;
    }

    // 투사체 풀 반환
    public void Return(SkillProjectile projectile)
    {
        projectile.OnDespawn();
        projectile.gameObject.SetActive(false);
        _available.Enqueue(projectile);
    }

    private SkillProjectile CreateInstance()
    {
        var obj = Instantiate(_prefab, transform);
        obj.SetPool(this);
        obj.gameObject.SetActive(false);
        _available.Enqueue(obj);
        return obj;
    }
}
