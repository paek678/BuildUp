using System;
using Unity.Behavior;
using UnityEngine;
using UnityEngine.AI;
using Action = Unity.Behavior.Action;
using Unity.Properties;

[Serializable, GeneratePropertyBag]
[NodeDescription(name: "SetNavDestinationAction", story: "[Agent] 의 목적지를 [TargetPosition] 으로 설정", category: "Action", id: "3c034b17fe232035833d36e14e95de2f")]
public partial class SetNavDestinationAction : Action
{
    [SerializeReference] public BlackboardVariable<NavMeshAgent> Agent;
    [SerializeReference] public BlackboardVariable<Vector3> TargetPosition;

    protected override Status OnStart()
    {
        if (Agent.Value == null)
        {
            Debug.LogWarning("[SetNavDest] Agent NULL — Failure");
            return Status.Failure;
        }

        if (!Agent.Value.isOnNavMesh)
        {
            Debug.LogWarning("[SetNavDest] Agent가 NavMesh 위에 없음 — Failure");
            return Status.Failure;
        }

        Agent.Value.SetDestination(TargetPosition.Value);
        return Status.Success;
    }

    protected override Status OnUpdate() => Status.Success;
    protected override void OnEnd() { }
}
