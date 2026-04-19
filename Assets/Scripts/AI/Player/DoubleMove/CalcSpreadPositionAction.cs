using System;
using Unity.Behavior;
using UnityEngine;
using UnityEngine.AI;
using Action = Unity.Behavior.Action;
using Unity.Properties;

[Serializable, GeneratePropertyBag]
[NodeDescription(name: "CalcSpreadPositionAction", story: "[Self] 이 [Ally] 로부터 [MinSpacing] 이상 떨어지도록 [TargetPosition] 계산", category: "Action", id: "a9a4702e177c2df78f96e499d14bcf90")]
public partial class CalcSpreadPositionAction : Action
{
    [SerializeReference] public BlackboardVariable<GameObject> Self;
    [SerializeReference] public BlackboardVariable<GameObject> Ally;
    [SerializeReference] public BlackboardVariable<float> MinSpacing;
    [SerializeReference] public BlackboardVariable<Vector3> TargetPosition;

    protected override Status OnStart()
    {
        if (Self.Value == null || Ally.Value == null)
        {
            Debug.LogWarning("[CalcSpread] Self/Ally NULL — Failure");
            return Status.Failure;
        }

        Vector3 selfPos = Self.Value.transform.position;
        Vector3 allyPos = Ally.Value.transform.position;
        Vector3 awayDir = selfPos - allyPos;
        awayDir.y = 0f;
        if (awayDir.sqrMagnitude < 0.001f)
            awayDir = UnityEngine.Random.insideUnitSphere;
        awayDir.y = 0f;
        awayDir.Normalize();

        Vector3 candidate = selfPos + awayDir * (MinSpacing.Value * 1.2f);

        if (!NavMesh.SamplePosition(candidate, out NavMeshHit hit, 2f, NavMesh.AllAreas))
        {
            Debug.LogWarning("[CalcSpread] NavMesh 샘플 실패");
            return Status.Failure;
        }

        TargetPosition.Value = hit.position;
        return Status.Success;
    }

    protected override Status OnUpdate() => Status.Success;
    protected override void OnEnd() { }
}
