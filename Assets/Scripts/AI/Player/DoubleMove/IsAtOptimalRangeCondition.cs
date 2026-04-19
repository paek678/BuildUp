using System;
using Unity.Behavior;
using UnityEngine;

[Serializable, Unity.Properties.GeneratePropertyBag]
[Condition(name: "IsAtOptimalRange", story: "[Self] 과 [Boss] 의 거리가 [OptimalMin] ~ [OptimalMax] 범위 내인지 검사", category: "Conditions", id: "3902238f9ff2eb019ea69418b70690ca")]
public partial class IsAtOptimalRangeCondition : Condition
{
    [SerializeReference] public BlackboardVariable<GameObject> Self;
    [SerializeReference] public BlackboardVariable<GameObject> Boss;
    [SerializeReference] public BlackboardVariable<float> OptimalMin;
    [SerializeReference] public BlackboardVariable<float> OptimalMax;

    public override bool IsTrue()
    {
        if (Self.Value == null || Boss.Value == null) return false;

        float dist = Vector3.Distance(Self.Value.transform.position, Boss.Value.transform.position);
        return dist >= OptimalMin.Value && dist <= OptimalMax.Value;
    }

    public override void OnStart() { }
    public override void OnEnd() { }
}
