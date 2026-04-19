using Unity.Behavior;
using UnityEngine;
using UnityEngine.AI;
using Action = Unity.Behavior.Action;
using Unity.Properties;
using System;

[Serializable, GeneratePropertyBag]
[NodeDescription(name: "GetFleePositionAction", story: "[Agent] 가 [Target] 으로부터 [Distance] 만큼 반대 방향으로 도망갈 NavMesh 위 위치를 계산해서 [FleePosition] 블랙보드 변수에 저장", category: "Action/Navigation", id: "50a235e0dc951f9f083e8632fbd5adc6")]
public partial class GetFleePositionAction : Action
{
    [SerializeReference] public BlackboardVariable<GameObject> Agent;
    [SerializeReference] public BlackboardVariable<GameObject> Target;
    [SerializeReference] public BlackboardVariable<float> Distance;
    [SerializeReference] public BlackboardVariable<Vector3> FleePosition;

    protected override Status OnStart()
    {
        if (Agent.Value == null || Target.Value == null)
        {
            Debug.LogWarning($"[GetFlee] Failure — Agent: {(Agent.Value == null ? "NULL" : Agent.Value.name)}, Target: {(Target.Value == null ? "NULL" : Target.Value.name)}");
            return Status.Failure;
        }

        Vector3 agentPos  = Agent.Value.transform.position;
        Vector3 targetPos = Target.Value.transform.position;
        float   radius    = Distance.Value;

        // 원형으로 12방향 균등 샘플링 후 보스와 가장 먼 유효 지점 선택
        const int   sampleCount  = 12;
        const float sampleRadius = 1.5f;

        Vector3 bestPos      = Vector3.zero;
        float   bestBossDist = -1f;

        for (int i = 0; i < sampleCount; i++)
        {
            float   angle     = i * (360f / sampleCount);
            Vector3 dir       = Quaternion.Euler(0f, angle, 0f) * Vector3.forward;
            Vector3 candidate = agentPos + dir * radius;

            if (!NavMesh.SamplePosition(candidate, out NavMeshHit hit, sampleRadius, NavMesh.AllAreas))
                continue;

            float bossDist = Vector3.Distance(hit.position, targetPos);
            if (bossDist > bestBossDist)
            {
                bestBossDist = bossDist;
                bestPos      = hit.position;
            }
        }

        if (bestBossDist < 0f)
        {
            Debug.LogWarning("[GetFlee] 유효한 NavMesh 지점 없음 — Failure");
            return Status.Failure;
        }

        FleePosition.Value = bestPos;
        Debug.Log($"[GetFlee] 최적 도주 지점: {bestPos}, 보스와 거리: {bestBossDist:F1}");
        return Status.Success;
    }

    protected override Status OnUpdate()
    {
        return Status.Success;
    }

    protected override void OnEnd()
    {
    }
}

