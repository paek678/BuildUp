using System;
using Unity.Behavior;
using UnityEngine;
using UnityEngine.AI;
using Action = Unity.Behavior.Action;
using Unity.Properties;

// 보스 중심으로 Ally 의 정반대편에 위치하도록 계산 (측면 협공)
[Serializable, GeneratePropertyBag]
[NodeDescription(name: "CalcFlankPositionAction", story: "[Boss] 를 중심으로 [Ally] 의 반대편 [FlankRadius] 위치를 [TargetPosition] 에 저장 (측면 협공)", category: "Action", id: "68d8755e3048a53fe721c983a19cc7f2")]
public partial class CalcFlankPositionAction : Action
{
    [SerializeReference] public BlackboardVariable<GameObject> Boss;
    [SerializeReference] public BlackboardVariable<GameObject> Ally;
    [SerializeReference] public BlackboardVariable<float> FlankRadius;
    [SerializeReference] public BlackboardVariable<Vector3> TargetPosition;

    protected override Status OnStart()
    {
        if (Boss.Value == null || Ally.Value == null)
        {
            Debug.LogWarning("[CalcFlank] Boss/Ally NULL — Failure");
            return Status.Failure;
        }

        Vector3 bossPos = Boss.Value.transform.position;
        Vector3 allyPos = Ally.Value.transform.position;

        Vector3 bossToAlly = allyPos - bossPos;
        bossToAlly.y = 0f;
        if (bossToAlly.sqrMagnitude < 0.001f)
            bossToAlly = Vector3.forward;
        bossToAlly.Normalize();

        Vector3 flankDir = -bossToAlly;
        Vector3 candidate = bossPos + flankDir * FlankRadius.Value;

        if (!NavMesh.SamplePosition(candidate, out NavMeshHit hit, 2f, NavMesh.AllAreas))
        {
            Debug.LogWarning("[CalcFlank] NavMesh 샘플 실패");
            return Status.Failure;
        }

        TargetPosition.Value = hit.position;
        return Status.Success;
    }

    protected override Status OnUpdate() => Status.Success;
    protected override void OnEnd() { }
}
