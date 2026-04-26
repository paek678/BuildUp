using System.Collections.Generic;
using UnityEngine;

public class PersistentAreaPool : MonoBehaviour
{
    [SerializeField] private SkillArea _prefab;
    [SerializeField] private int _initialSize = 5;

    private readonly Queue<SkillArea> _available = new();

    private void Awake()
    {
        for (int i = 0; i < _initialSize; i++)
            CreateInstance();
    }

    public SkillArea Get(Vector3 position)
    {
        var obj = _available.Count > 0 ? _available.Dequeue() : CreateInstance();
        obj.transform.position = position;
        obj.gameObject.SetActive(true);
        obj.OnSpawn();
        return obj;
    }

    public void Return(SkillArea area)
    {
        area.OnDespawn();
        area.gameObject.SetActive(false);
        _available.Enqueue(area);
    }

    public void ReturnAll()
    {
        for (int i = transform.childCount - 1; i >= 0; i--)
        {
            var child = transform.GetChild(i);
            if (!child.gameObject.activeSelf) continue;
            var area = child.GetComponent<SkillArea>();
            if (area != null) Return(area);
        }
    }

    private SkillArea CreateInstance()
    {
        var obj = Instantiate(_prefab, transform);
        obj.SetPool(this);
        obj.gameObject.SetActive(false);
        _available.Enqueue(obj);
        return obj;
    }
}
