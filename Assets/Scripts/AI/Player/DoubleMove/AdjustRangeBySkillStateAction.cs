using System;
using Unity.Behavior;
using UnityEngine;
using Action = Unity.Behavior.Action;
using Unity.Properties;

[Serializable, GeneratePropertyBag]
[NodeDescription(name: "AdjustRangeBySkillState", story: "[Self] 의 스킬 상태에 따라 [OptimalMin] / [OptimalMax] 를 [AttackRangeMin] ~ [AttackRangeMax] ↔ [SafeRangeMin] ~ [SafeRangeMax] 로 전환", category: "Action", id: "26b1dd0cd6740d612345657bbfe1cda8")]
public partial class AdjustRangeBySkillStateAction : Action
{
    [SerializeReference] public BlackboardVariable<GameObject> Self;
    [SerializeReference] public BlackboardVariable<float> OptimalMin;
    [SerializeReference] public BlackboardVariable<float> OptimalMax;
    [SerializeReference] public BlackboardVariable<float> AttackRangeMin;
    [SerializeReference] public BlackboardVariable<float> AttackRangeMax;
    [SerializeReference] public BlackboardVariable<float> SafeRangeMin;
    [SerializeReference] public BlackboardVariable<float> SafeRangeMax;

    private SkillManager _cachedSkillManager;
    private GameObject _cachedSelf;

    protected override Status OnStart()
    {
        if (Self.Value == null) return Status.Success;

        if (_cachedSelf != Self.Value)
        {
            _cachedSelf = Self.Value;
            _cachedSkillManager = Self.Value.GetComponent<SkillManager>();
        }

        if (_cachedSkillManager == null) return Status.Success;

        bool anyReady = false;
        for (int i = 0; i < _cachedSkillManager.MaxSlots; i++)
        {
            if (_cachedSkillManager.Slots[i] != null && _cachedSkillManager.CanUse(i))
            {
                anyReady = true;
                break;
            }
        }

        if (anyReady)
        {
            OptimalMin.Value = AttackRangeMin.Value;
            OptimalMax.Value = AttackRangeMax.Value;
        }
        else
        {
            OptimalMin.Value = SafeRangeMin.Value;
            OptimalMax.Value = SafeRangeMax.Value;
        }

        return Status.Success;
    }

    protected override Status OnUpdate() => Status.Success;
    protected override void OnEnd() { }
}

