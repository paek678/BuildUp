using System;
using Unity.Behavior;
using UnityEngine;

[Serializable, Unity.Properties.GeneratePropertyBag]
[Condition(name: "IsAllyTooClose", story: "[Self] 와 [Ally] 의 거리가 [MinSpacing] 보다 가까운지 검사 (겹침 방지)", category: "Conditions", id: "d70f3bc9f4e1f8e66d104aa8cc27b75b")]
public partial class IsAllyTooCloseCondition : Condition
{
    [SerializeReference] public BlackboardVariable<GameObject> Self;
    [SerializeReference] public BlackboardVariable<GameObject> Ally;
    [SerializeReference] public BlackboardVariable<float> MinSpacing;

    public override bool IsTrue()
    {
        if (Self.Value == null || Ally.Value == null) return false;

        float sqrDist = (Self.Value.transform.position - Ally.Value.transform.position).sqrMagnitude;
        float sqrRange = MinSpacing.Value * MinSpacing.Value;
        return sqrDist < sqrRange;
    }

    public override void OnStart() { }
    public override void OnEnd() { }
}
