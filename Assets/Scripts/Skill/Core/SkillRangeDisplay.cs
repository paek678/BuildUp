using System.Collections;
using System.Collections.Generic;
using UnityEngine;

// 스킬 범위를 시각적으로 표시하는 디버그용 싱글톤 (프리팹 기반)
//
// 프리팹 구조:
//   RangeIndicator (빈 오브젝트)
//   └── Visual (MeshRenderer + MeshFilter — Cylinder 권장, URP Unlit 투명 Material)
//
// Inspector 에서 Indicator Prefab 에 프리팹 드래그 → 자동 풀링
public class SkillRangeDisplay : MonoBehaviour
{
    public static SkillRangeDisplay Instance { get; private set; }

    [Header("설정")]
    [SerializeField] private bool  _showRange = true;
    [SerializeField] private bool  _logRange  = true;
    [SerializeField] private float _duration  = 1.5f;

    [Header("프리팹 (URP 투명 Material 적용된 Cylinder)")]
    [SerializeField] private GameObject _indicatorPrefab;
    [SerializeField] private int _poolSize = 8;

    [Header("색상")]
    [SerializeField] private Color _hitColor  = new Color(1f, 0.2f, 0.1f, 0.85f);
    [SerializeField] private Color _missColor = new Color(0.8f, 0.8f, 0.8f, 0.7f);
    [SerializeField] private Color _projColor = new Color(0.2f, 0.5f, 1f, 0.8f);

    private readonly Queue<GameObject> _pool = new();

    private static readonly int BaseColor = Shader.PropertyToID("_BaseColor");

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;

        if (_indicatorPrefab == null)
        {
            Debug.LogWarning("[SkillRangeDisplay] Indicator Prefab 미지정 — 범위 표시 불가");
            return;
        }

        for (int i = 0; i < _poolSize; i++)
            _pool.Enqueue(CreateInstance());

        Debug.Log($"[SkillRangeDisplay] 초기화 완료 (풀 {_poolSize}개)");
    }

    public void ShowCircle(Vector3 center, float radius, bool hit)
    {
        if (!_showRange || _indicatorPrefab == null) return;
        if (_logRange) Debug.Log($"[RangeDisplay] Circle center={center} r={radius} hit={hit}");
        StartCoroutine(IndicatorRoutine(center, Vector3.forward, radius, AreaShape.Circle, 360f, hit ? _hitColor : _missColor));
    }

    public void ShowCone(Vector3 center, Vector3 forward, float radius, float angleDeg, bool hit)
    {
        if (!_showRange || _indicatorPrefab == null) return;
        if (_logRange) Debug.Log($"[RangeDisplay] Cone center={center} r={radius} angle={angleDeg} hit={hit}");
        StartCoroutine(IndicatorRoutine(center, forward, radius, AreaShape.Cone, angleDeg, hit ? _hitColor : _missColor));
    }

    public void ShowLine(Vector3 origin, Vector3 forward, float length)
    {
        if (!_showRange || _indicatorPrefab == null) return;
        if (_logRange) Debug.Log($"[RangeDisplay] Line origin={origin} len={length}");
        StartCoroutine(IndicatorRoutine(origin + forward.normalized * length * 0.5f, forward, length * 0.5f, AreaShape.Line, 0f, _projColor));
    }

    private IEnumerator IndicatorRoutine(Vector3 center, Vector3 forward, float radius,
                                          AreaShape shape, float angleDeg, Color color)
    {
        var go = GetFromPool();
        go.transform.position = new Vector3(center.x, 0.15f, center.z);

        Transform visual = go.transform.childCount > 0 ? go.transform.GetChild(0) : go.transform;

        switch (shape)
        {
            case AreaShape.Circle:
                visual.localScale = new Vector3(radius * 2f, 0.15f, radius * 2f);
                go.transform.rotation = Quaternion.identity;
                break;
            case AreaShape.Cone:
                visual.localScale = new Vector3(radius * 2f, 0.15f, radius * 2f);
                if (forward != Vector3.zero)
                    go.transform.rotation = Quaternion.LookRotation(forward);
                break;
            case AreaShape.Line:
                visual.localScale = new Vector3(1.0f, 0.15f, radius * 2f);
                if (forward != Vector3.zero)
                    go.transform.rotation = Quaternion.LookRotation(forward);
                break;
        }

        var rend = go.GetComponentInChildren<Renderer>();
        if (rend == null) { ReturnToPool(go); yield break; }

        var mat = rend.material;
        mat.SetColor(BaseColor, color);
        mat.color = color;

        float elapsed = 0f;
        while (elapsed < _duration)
        {
            elapsed += Time.deltaTime;
            float alpha = Mathf.Lerp(color.a, 0f, elapsed / _duration);
            var c = new Color(color.r, color.g, color.b, alpha);
            mat.SetColor(BaseColor, c);
            mat.color = c;
            yield return null;
        }

        ReturnToPool(go);
    }

    private GameObject GetFromPool()
    {
        var go = _pool.Count > 0 ? _pool.Dequeue() : CreateInstance();
        go.SetActive(true);
        return go;
    }

    private void ReturnToPool(GameObject go)
    {
        go.SetActive(false);
        _pool.Enqueue(go);
    }

    private GameObject CreateInstance()
    {
        var go = Instantiate(_indicatorPrefab, transform);
        go.name = "[RangeIndicator]";
        go.SetActive(false);

        var col = go.GetComponentInChildren<Collider>();
        if (col != null) Destroy(col);

        return go;
    }
}
