using System;
using Unity.Behavior;
using UnityEngine;
using Action = Unity.Behavior.Action;
using Unity.Properties;

[Serializable, GeneratePropertyBag]
[NodeDescription(name: "abc", story: "[A] 가 [B] 로부터 도망감", category: "Action", id: "855b86a7a5e467127dced83118431f50")]
public partial class AbcAction : Action
{
    [SerializeReference] public BlackboardVariable<GameObject> A;
    [SerializeReference] public BlackboardVariable<GameObject> B;

    protected override Status OnStart()
    {
        return Status.Running;
    }

    protected override Status OnUpdate()
    {
        return Status.Success;
    }

    protected override void OnEnd()
    {
    }
}

