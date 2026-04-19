using System;
using Unity.Behavior;
using UnityEngine;
using UnityEngine.AI;
using Action = Unity.Behavior.Action;
using Unity.Properties;

[Serializable, GeneratePropertyBag]
[NodeDescription(name: "CalcApproachPositionAction", story: "[Self] 이 [Boss] 와 [OptimalMin] ~ [OptimalMax] 거리를 유지하도록 [TargetPosition] 계산", category: "Action", id: "8cc4750f535ab66a55fbf4641d11b53f")]
public partial class CalcApproachPositionAction : Action
{
    [SerializeReference] public BlackboardVariable<GameObject> Self;
    [SerializeReference] public BlackboardVariable<GameObject> Boss;
    [SerializeReference] public BlackboardVariable<float> OptimalMin;
    [SerializeReference] public BlackboardVariable<float> OptimalMax;
    [SerializeReference] public BlackboardVariable<Vector3> TargetPosition;

    protected override Status OnStart()
    {
        if (Self.Value == null || Boss.Value == null)
        {
            Debug.LogWarning("[CalcApproach] Self/Boss NULL — Failure");
            return Status.Failure;
        }

        Vector3 bossPos = Boss.Value.transform.position;
        Vector3 selfPos = Self.Value.transform.position;

        Vector3 bossToSelf = selfPos - bossPos;
        bossToSelf.y = 0f;
        if (bossToSelf.sqrMagnitude < 0.001f)
            bossToSelf = Vector3.forward;
        Vector3 dir = bossToSelf.normalized;

        float optimal = (OptimalMin.Value + OptimalMax.Value) * 0.5f;
        Vector3 candidate = bossPos + dir * optimal;

        if (!NavMesh.SamplePosition(candidate, out NavMeshHit hit, 2f, NavMesh.AllAreas))
        {
            Debug.LogWarning("[CalcApproach] NavMesh 샘플 실패");
            return Status.Failure;
        }

        TargetPosition.Value = hit.position;
        return Status.Success;
    }

    protected override Status OnUpdate() => Status.Success;
    protected override void OnEnd() { }
}
