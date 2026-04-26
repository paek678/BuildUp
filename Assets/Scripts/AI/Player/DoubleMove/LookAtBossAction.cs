using System;
using Unity.Behavior;
using UnityEngine;
using UnityEngine.AI;
using Action = Unity.Behavior.Action;
using Unity.Properties;

[Serializable, GeneratePropertyBag]
[NodeDescription(name: "LookAtBossAction", story: "[Self] 가 [Boss] 를 바라보도록 회전", category: "Action", id: "a7e3c9f14d2b8a6e90f1d5c3b7e24680")]
public partial class LookAtBossAction : Action
{
    [SerializeReference] public BlackboardVariable<GameObject> Self;
    [SerializeReference] public BlackboardVariable<GameObject> Boss;

    private Quaternion _targetRot;
    private Transform _selfTf;
    private const float RotSpeed = 12f;
    private const float DoneThreshold = 2f;

    protected override Status OnStart()
    {
        if (Self.Value == null || Boss.Value == null)
        {
            Debug.LogWarning("[LookAtBoss] Self/Boss NULL — Failure");
            return Status.Failure;
        }

        _selfTf = Self.Value.transform;

        Vector3 dir = Boss.Value.transform.position - _selfTf.position;
        dir.y = 0f;
        if (dir.sqrMagnitude < 0.001f)
            return Status.Success;

        _targetRot = Quaternion.LookRotation(dir);

        if (Quaternion.Angle(_selfTf.rotation, _targetRot) < DoneThreshold)
            return Status.Success;

        var agent = Self.Value.GetComponent<NavMeshAgent>();
        if (agent != null)
            agent.updateRotation = false;

        return Status.Running;
    }

    protected override Status OnUpdate()
    {
        _selfTf.rotation = Quaternion.Slerp(
            _selfTf.rotation, _targetRot, RotSpeed * Time.deltaTime);

        if (Quaternion.Angle(_selfTf.rotation, _targetRot) < DoneThreshold)
            return Status.Success;

        return Status.Running;
    }

    protected override void OnEnd() { }
}
