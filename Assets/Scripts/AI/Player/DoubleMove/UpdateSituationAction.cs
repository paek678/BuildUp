using System;
using Unity.Behavior;
using UnityEngine;
using Action = Unity.Behavior.Action;
using Unity.Properties;

[Serializable, GeneratePropertyBag]
[NodeDescription(name: "UpdateSituationAction", story: "[Self] [Boss] [Ally] 의 현재 거리와 각도를 계산해서 [DistanceToBoss] [DistanceToAlly] [BossToAllyAngle] 에 저장", category: "Action", id: "7c7c8644213866612b0e9be6589be523")]
public partial class UpdateSituationAction : Action
{
    [SerializeReference] public BlackboardVariable<GameObject> Self;
    [SerializeReference] public BlackboardVariable<GameObject> Boss;
    [SerializeReference] public BlackboardVariable<GameObject> Ally;
    [SerializeReference] public BlackboardVariable<float> DistanceToBoss;
    [SerializeReference] public BlackboardVariable<float> DistanceToAlly;
    [SerializeReference] public BlackboardVariable<float> BossToAllyAngle;

    protected override Status OnStart()
    {
        if (Self.Value == null || Boss.Value == null || Ally.Value == null)
        {
            Debug.LogWarning("[UpdateSituation] Self/Boss/Ally NULL — Failure");
            return Status.Failure;
        }

        Vector3 selfPos = Self.Value.transform.position;
        Vector3 bossPos = Boss.Value.transform.position;
        Vector3 allyPos = Ally.Value.transform.position;

        DistanceToBoss.Value = Vector3.Distance(selfPos, bossPos);
        DistanceToAlly.Value = Vector3.Distance(selfPos, allyPos);

        // 보스 기준 Self -> Ally 의 방향 각도 (XZ 평면)
        Vector3 bossToSelf = new(selfPos.x - bossPos.x, 0f, selfPos.z - bossPos.z);
        Vector3 bossToAlly = new(allyPos.x - bossPos.x, 0f, allyPos.z - bossPos.z);
        BossToAllyAngle.Value = Vector3.Angle(bossToSelf, bossToAlly);

        return Status.Success;
    }

    protected override Status OnUpdate() => Status.Success;
    protected override void OnEnd() { }
}
