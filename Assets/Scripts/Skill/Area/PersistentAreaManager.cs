using UnityEngine;

// 씬에 하나 배치. SpawnPersistentArea(#31) 부품이 이 매니저를 통해 장판을 소환한다.
// Inspector에서 PersistentAreaPool을 연결해야 동작한다.
public class PersistentAreaManager : MonoBehaviour
{
    [SerializeField] private PersistentAreaPool _pool;

    public static PersistentAreaManager Instance { get; private set; }

    private void Awake()
    {
        if (Instance != null)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;
    }

    // SpawnPersistentArea(#31) 에서 호출
    public void Spawn(Vector3 position, Vector3 forward, float radius,
                      AreaShape shape, float angleDeg,
                      float duration, float tickInterval,
                      SkillStep tickEffect, SkillContext ctx)
    {
        if (_pool == null)
        {
            Debug.LogWarning("[PersistentAreaManager] PersistentAreaPool 미연결");
            return;
        }

        var area = _pool.Get(position);
        area.Initialize(forward, radius, shape, angleDeg, duration, tickInterval, tickEffect, ctx);
    }
}
