using UnityEngine;

public class SkillDistributor : MonoBehaviour
{
    [System.Serializable]
    public class SkillLoadout
    {
        public string Name;
        public SkillManager Target;
        public SkillDefinition[] Skills;
    }

    [SerializeField] private SkillLoadout[] _loadouts;

    private void Start()
    {
        if (_loadouts == null) return;

        foreach (var loadout in _loadouts)
        {
            if (loadout.Target == null)
            {
                Debug.LogWarning($"[SkillDistributor] {loadout.Name}: Target 없음");
                continue;
            }

            loadout.Target.ClearAll();

            if (loadout.Skills != null)
            {
                for (int i = 0; i < loadout.Skills.Length && i < SkillManager.SlotCount; i++)
                    loadout.Target.SetSlot(i, loadout.Skills[i]);
            }

            Debug.Log($"[SkillDistributor] {loadout.Name}: {loadout.Skills?.Length ?? 0}종 배치 완료");
        }
    }
}
