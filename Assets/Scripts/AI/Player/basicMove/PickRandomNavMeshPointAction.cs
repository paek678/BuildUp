using Unity.Behavior;
using UnityEngine;
using UnityEngine.AI;
using Action = Unity.Behavior.Action;
using Unity.Properties;
using System;

[Serializable, GeneratePropertyBag]
[NodeDescription(name: "PickRandomNavMeshPointAction", story: "[Agent] 기준으로 [Radius] 반경 내 NavMesh 위 랜덤 위치를 골라 [TargetPosition] 블랙보드 변수에 저장", category: "Action/Navigation", id: "e0cffd962c5e06fc2116d50744bd87a8")]
public partial class PickRandomNavMeshPointAction : Action
{
    [SerializeReference] public BlackboardVariable<GameObject> Agent;
    [SerializeReference] public BlackboardVariable<float> Radius;
    [SerializeReference] public BlackboardVariable<Vector3> TargetPosition;

    private const int MaxAttempts = 10;

    protected override Status OnStart()
    {
        if (Agent.Value == null)
        {
            Debug.LogWarning("[PickNavPoint] Agent가 NULL");
            return Status.Failure;
        }

        Debug.Log($"[PickNavPoint] Agent: {Agent.Value.name}, Radius: {Radius.Value}, 위치: {Agent.Value.transform.position}");

        Vector3 agentPos = Agent.Value.transform.position;

        for (int i = 0; i < MaxAttempts; i++)
        {
            Vector3 randomDir = UnityEngine.Random.insideUnitSphere * Radius.Value;
            randomDir.y = 0f;
            Vector3 candidate = agentPos + randomDir;

            if (NavMesh.SamplePosition(candidate, out NavMeshHit hit, Radius.Value, NavMesh.AllAreas))
            {
                TargetPosition.Value = hit.position;
                Debug.Log($"[PickNavPoint] 목적지 확정: {hit.position} (시도 {i + 1}회)");
                return Status.Success;
            }
        }

        Debug.LogWarning($"[PickNavPoint] {MaxAttempts}회 시도 실패 — NavMesh 범위 밖일 가능성");
        return Status.Failure;
    }

    protected override Status OnUpdate()
    {
        return Status.Success;
    }

    protected override void OnEnd()
    {
    }
}

