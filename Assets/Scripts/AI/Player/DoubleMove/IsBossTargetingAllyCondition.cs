using System;
using Unity.Behavior;
using UnityEngine;

// 보스에 명시적 Target 필드가 없으므로 "보스의 전방 방향과 더 일치하는 쪽"을 타겟으로 판정
[Serializable, Unity.Properties.GeneratePropertyBag]
[Condition(name: "IsBossTargetingAlly", story: "[Boss] 의 타겟이 [Self] 가 아닌 [Ally] 인지 검사", category: "Conditions", id: "2b76250e498306126fee4ec792926442")]
public partial class IsBossTargetingAllyCondition : Condition
{
    [SerializeReference] public BlackboardVariable<GameObject> Boss;
    [SerializeReference] public BlackboardVariable<GameObject> Self;
    [SerializeReference] public BlackboardVariable<GameObject> Ally;

    public override bool IsTrue()
    {
        if (Boss.Value == null || Self.Value == null || Ally.Value == null) return false;

        Vector3 bossPos = Boss.Value.transform.position;
        Vector3 bossFwd = Boss.Value.transform.forward;

        Vector3 toSelf = (Self.Value.transform.position - bossPos).normalized;
        Vector3 toAlly = (Ally.Value.transform.position - bossPos).normalized;

        float dotSelf = Vector3.Dot(bossFwd, toSelf);
        float dotAlly = Vector3.Dot(bossFwd, toAlly);

        return dotAlly > dotSelf;
    }

    public override void OnStart() { }
    public override void OnEnd() { }
}
