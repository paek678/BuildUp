using Unity.Behavior;
using UnityEngine;
using UnityEngine.AI;

public class PlayerBotCombatInit : MonoBehaviour
{
    [Header("컴포넌트 참조")]
    [SerializeField] private BehaviorGraphAgent _behaviorAgent;
    [SerializeField] private GameManager _gameManager;

    [Header("Blackboard 참조")]
    [SerializeField] private GameObject _ally;

    [Header("Blackboard 값")]
    [SerializeField] private float _dangerRange;
    [SerializeField] private float _optimalMin;
    [SerializeField] private float _optimalMax;
    [SerializeField] private float _fleeDistance;
    [SerializeField] private float _flankRadius;
    [SerializeField] private float _strafeRadius;
    [SerializeField] private float _strafeAngleStep;
    [SerializeField] private float _minSpacing;

    private NavMeshAgent _navAgent;

    private void Awake()
    {
        if (_behaviorAgent == null)
            _behaviorAgent = GetComponent<BehaviorGraphAgent>();
        _navAgent = GetComponent<NavMeshAgent>();

        if (_behaviorAgent != null)
            _behaviorAgent.enabled = false;
    }

    private void Start()
    {
        if (_behaviorAgent == null)
        {
            Debug.LogWarning($"[PlayerBotCombatInit] {name}: BehaviorGraphAgent 없음");
            return;
        }

        var bb = _behaviorAgent.BlackboardReference;
        if (bb == null)
        {
            Debug.LogWarning($"[PlayerBotCombatInit] {name}: BlackboardReference 없음");
            _behaviorAgent.enabled = true;
            return;
        }

        if (_navAgent == null)
            Debug.LogWarning($"[PlayerBotCombatInit] {name}: NavMeshAgent 없음");

        if (_ally == null)
            Debug.LogWarning($"[PlayerBotCombatInit] {name}: Ally 미지정");

        GameObject bossObj = null;
        if (_gameManager != null && _gameManager.Bosses.Count > 0)
            bossObj = _gameManager.Bosses[0];
        if (bossObj == null)
            bossObj = GameObject.FindWithTag("Boss");

        bb.SetVariableValue("Boss", bossObj);
        bb.SetVariableValue("Agent", _navAgent);
        bb.SetVariableValue("Ally", _ally);
        bb.SetVariableValue("Self", gameObject);

        bb.SetVariableValue("DangerRange", _dangerRange);
        bb.SetVariableValue("OptimalMin", _optimalMin);
        bb.SetVariableValue("OptimalMax", _optimalMax);
        bb.SetVariableValue("FleeDistance", _fleeDistance);
        bb.SetVariableValue("FlankRadius", _flankRadius);
        bb.SetVariableValue("StrafeRadius", _strafeRadius);
        bb.SetVariableValue("StrafeAngleStep", _strafeAngleStep);
        bb.SetVariableValue("MinSpacing", _minSpacing);

        _behaviorAgent.enabled = true;

        Debug.Log($"[PlayerBotCombatInit] {name}: Blackboard 주입 완료 (Boss={bossObj?.name ?? "NULL"}, Ally={_ally?.name ?? "NULL"})");
    }
}
