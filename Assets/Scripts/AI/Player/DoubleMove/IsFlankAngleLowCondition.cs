using System;
using Unity.Behavior;
using UnityEngine;
using Unity.Properties;

[Serializable, GeneratePropertyBag]
[Condition(
    name: "IsFlankAngleLow",
    story: "[Boss] 에서 [Self] 와 [Ally] 의 사잇각이 [MinFlankAngle] 이하인지 검사",
    category: "Conditions",
    id: "a3f6d2e1b9c74d5e8a1f3b7c6e9d0a24")]
public partial class IsFlankAngleLowCondition : Condition
{
    [SerializeReference] public BlackboardVariable<GameObject> Boss;
    [SerializeReference] public BlackboardVariable<GameObject> Self;
    [SerializeReference] public BlackboardVariable<GameObject> Ally;
    [SerializeReference] public BlackboardVariable<float> MinFlankAngle;

    public override bool IsTrue()
    {
        if (Boss.Value == null || Self.Value == null || Ally.Value == null)
            return false;

        var allyCtrl = Ally.Value.GetComponent<PlayerController>();
        if (allyCtrl != null && !allyCtrl.IsAlive)
            return false;

        Vector3 bossPos = Boss.Value.transform.position;
        Vector3 toSelf = Self.Value.transform.position - bossPos;
        Vector3 toAlly = Ally.Value.transform.position - bossPos;
        toSelf.y = 0f;
        toAlly.y = 0f;

        if (toSelf.sqrMagnitude < 0.001f || toAlly.sqrMagnitude < 0.001f)
            return true;

        float angle = Vector3.Angle(toSelf, toAlly);
        return angle <= MinFlankAngle.Value;
    }

    public override void OnStart() { }
    public override void OnEnd() { }
}
