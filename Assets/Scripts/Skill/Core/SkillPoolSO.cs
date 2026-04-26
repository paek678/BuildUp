using UnityEngine;

[CreateAssetMenu(menuName = "Tenebris/SkillPoolSO", fileName = "NewSkillPool")]
public class SkillPoolSO : ScriptableObject
{
    [Header("스킬 풀 (3개 이상 권장)")]
    [SerializeField] private SkillDefinition[] _skills;

    [Header("원거리 분류 기준")]
    [SerializeField] private float _rangedThreshold = 20f;

    public SkillDefinition[] Skills => _skills;
    public int Count => _skills != null ? _skills.Length : 0;

    public bool IsRangedPool
    {
        get
        {
            if (_skills == null || _skills.Length == 0) return false;
            int rangedCount = 0;
            for (int i = 0; i < _skills.Length; i++)
            {
                if (_skills[i] != null && _skills[i].Range >= _rangedThreshold)
                    rangedCount++;
            }
            return rangedCount >= 2;
        }
    }

    public SkillDefinition GetSkill(int index)
    {
        if (_skills == null || index < 0 || index >= _skills.Length) return null;
        return _skills[index];
    }
}
