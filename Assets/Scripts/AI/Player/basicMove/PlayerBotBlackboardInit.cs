using System.Collections.Generic;
using Unity.Behavior;
using UnityEngine;

public class PlayerBotBlackboardInit : MonoBehaviour
{
    [Header("블랙보드 연결 대상")]
    [SerializeField] private BehaviorGraphAgent _behaviorAgent;

    [Header("블랙보드 값")]
    [SerializeField] private GameObject _boss;
    [SerializeField] private float _patrolRadius = 6f;
    [SerializeField] private float _fleeDistance = 4f;
    [SerializeField] private List<float> _weights = new List<float> { 7f, 3f };

    private void Awake()
    {
        if (_behaviorAgent == null)
            _behaviorAgent = GetComponent<BehaviorGraphAgent>();

        if (_boss == null)
            _boss = GameObject.FindWithTag("Boss");
    }

    private void Start()
    {
        if (_behaviorAgent == null)
        {
            Debug.LogWarning("[PlayerBotBlackboardInit] BehaviorGraphAgent 없음");
            return;
        }

        var blackboard = _behaviorAgent.BlackboardReference;
        if (blackboard == null)
        {
            Debug.LogWarning("[PlayerBotBlackboardInit] Blackboard 없음");
            return;
        }

        blackboard.SetVariableValue("Boss", _boss);
        blackboard.SetVariableValue("PatrolRadius", _patrolRadius);
        blackboard.SetVariableValue("FleeDistance", _fleeDistance);
        blackboard.SetVariableValue("Weights", _weights);

        Debug.Log($"[BotInit] Boss: {(_boss != null ? _boss.name : "NULL")}");
        Debug.Log($"[BotInit] PatrolRadius: {_patrolRadius}, FleeDistance: {_fleeDistance}");
        Debug.Log($"[BotInit] Weights: [{string.Join(", ", _weights)}]");
    }
}
