using System;
using Unity.Behavior;
using UnityEngine;
using UnityEngine.AI;
using Action = Unity.Behavior.Action;
using Unity.Properties;

[Serializable, GeneratePropertyBag]
[NodeDescription(name: "CalcFleePositionAction", story: "[Self] 가 [Boss] 로부터 [FleeDistance] 만큼 떨어진 NavMesh 위치를 [TargetPosition] 에 저장", category: "Action", id: "4a49ff291af1f78a5f8c568e65fe4b89")]
public partial class CalcFleePositionAction : Action
{
    [SerializeReference] public BlackboardVariable<GameObject> Self;
    [SerializeReference] public BlackboardVariable<GameObject> Boss;
    [SerializeReference] public BlackboardVariable<float> FleeDistance;
    [SerializeReference] public BlackboardVariable<Vector3> TargetPosition;

    protected override Status OnStart()
    {
        if (Self.Value == null || Boss.Value == null)
        {
            Debug.LogWarning("[CalcFlee] Self/Boss NULL — Failure");
            return Status.Failure;
        }

        Vector3 selfPos = Self.Value.transform.position;
        Vector3 bossPos = Boss.Value.transform.position;
        Vector3 awayDir = (selfPos - bossPos).normalized;
        if (awayDir.sqrMagnitude < 0.001f) awayDir = Vector3.forward;

        // 반대 방향 후보 + 측면 후보 5개 중 보스와 가장 먼 NavMesh 지점 선택
        const int sampleCount = 5;
        const float sampleRadius = 1.5f;
        const float spreadAngle = 40f;

        Vector3 bestPos = selfPos;
        float bestBossDist = -1f;

        for (int i = 0; i < sampleCount; i++)
        {
            float t = (sampleCount == 1) ? 0f : i / (float)(sampleCount - 1) * 2f - 1f;
            Vector3 dir = Quaternion.Euler(0f, t * spreadAngle, 0f) * awayDir;
            Vector3 candidate = selfPos + dir * FleeDistance.Value;

            if (!NavMesh.SamplePosition(candidate, out NavMeshHit hit, sampleRadius, NavMesh.AllAreas))
                continue;

            float d = Vector3.Distance(hit.position, bossPos);
            if (d > bestBossDist)
            {
                bestBossDist = d;
                bestPos = hit.position;
            }
        }

        if (bestBossDist < 0f)
        {
            Debug.LogWarning("[CalcFlee] 유효한 NavMesh 지점 없음");
            return Status.Failure;
        }

        TargetPosition.Value = bestPos;
        return Status.Success;
    }

    protected override Status OnUpdate() => Status.Success;
    protected override void OnEnd() { }
}
