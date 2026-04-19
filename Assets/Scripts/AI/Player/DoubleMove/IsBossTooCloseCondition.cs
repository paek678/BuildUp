using System;
using Unity.Behavior;
using UnityEngine;

[Serializable, Unity.Properties.GeneratePropertyBag]
[Condition(name: "IsBossTooClose", story: "[Self] 과 [Boss] 의 거리가 [DangerRange] 보다 가까운지 검사", category: "Conditions", id: "8792a8361a41c7742f32a98a3cf9cf5a")]
public partial class IsBossTooCloseCondition : Condition
{
    [SerializeReference] public BlackboardVariable<GameObject> Self;
    [SerializeReference] public BlackboardVariable<GameObject> Boss;
    [SerializeReference] public BlackboardVariable<float> DangerRange;

    public override bool IsTrue()
    {
        if (Self.Value == null || Boss.Value == null) return false;

        float sqrDist = (Self.Value.transform.position - Boss.Value.transform.position).sqrMagnitude;
        float sqrRange = DangerRange.Value * DangerRange.Value;
        return sqrDist < sqrRange;
    }

    public override void OnStart() { }
    public override void OnEnd() { }
}
