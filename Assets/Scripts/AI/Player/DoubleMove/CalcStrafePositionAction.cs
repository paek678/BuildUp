using System;
using Unity.Behavior;
using UnityEngine;
using UnityEngine.AI;
using Action = Unity.Behavior.Action;
using Unity.Properties;

// 보스 주위를 원형으로 도는 위치 계산 (StrafeAngleStep 도 만큼 회전한 다음 지점)
[Serializable, GeneratePropertyBag]
[NodeDescription(name: "CalcStrafePositionAction", story: "[Self] 이 [Boss] 주위를 [StrafeRadius] 반경으로 [StrafeAngleStep] 도 만큼 원형 이동한 [TargetPosition] 계산", category: "Action", id: "6d4118d40f638da7015bd8ddf464adf8")]
public partial class CalcStrafePositionAction : Action
{
    [SerializeReference] public BlackboardVariable<GameObject> Self;
    [SerializeReference] public BlackboardVariable<GameObject> Boss;
    [SerializeReference] public BlackboardVariable<float> StrafeRadius;
    [SerializeReference] public BlackboardVariable<float> StrafeAngleStep;
    [SerializeReference] public BlackboardVariable<Vector3> TargetPosition;

    protected override Status OnStart()
    {
        if (Self.Value == null || Boss.Value == null)
        {
            Debug.LogWarning("[CalcStrafe] Self/Boss NULL — Failure");
            return Status.Failure;
        }

        Vector3 bossPos = Boss.Value.transform.position;
        Vector3 selfPos = Self.Value.transform.position;

        Vector3 bossToSelf = selfPos - bossPos;
        bossToSelf.y = 0f;
        if (bossToSelf.sqrMagnitude < 0.001f)
            bossToSelf = Vector3.forward;

        Vector3 rotated = Quaternion.Euler(0f, StrafeAngleStep.Value, 0f) * bossToSelf.normalized;
        Vector3 candidate = PlayerArenaBounds.ClampToArena(bossPos + rotated * StrafeRadius.Value);

        if (!NavMesh.SamplePosition(candidate, out NavMeshHit hit, 2f, NavMesh.AllAreas))
        {
            Vector3 rotatedOpp = Quaternion.Euler(0f, -StrafeAngleStep.Value, 0f) * bossToSelf.normalized;
            Vector3 candidate2 = PlayerArenaBounds.ClampToArena(bossPos + rotatedOpp * StrafeRadius.Value);
            if (!NavMesh.SamplePosition(candidate2, out hit, 2f, NavMesh.AllAreas))
            {
                Debug.LogWarning("[CalcStrafe] NavMesh 샘플 실패");
                return Status.Failure;
            }
        }

        TargetPosition.Value = hit.position;
        return Status.Success;
    }

    protected override Status OnUpdate() => Status.Success;
    protected override void OnEnd() { }
}
