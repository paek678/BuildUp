using UnityEngine;

// 보스 행동 가중치 계산기 (9종)
// PlayerBiasTracker 편향 점수 기반으로 보스 행동군별 가중치 계산
// weighted-random 선택 + 반복 방지 + 비적합 게이트 + legal mask
public class BossActionWeightCalculator : MonoBehaviour
{
    public const int ActionCount = 9;

    [Header("참조")]
    [SerializeField] private PlayerBiasTracker _biasTracker;
    [SerializeField] private BossController    _bossController;

    [Header("가중치 설정")]
    [SerializeField] private float _baseWeight        = 1.0f;
    [SerializeField] private float _floorWeight       = 0.1f;
    [SerializeField] private float _gateThreshold     = 0.05f;

    [Header("반복 방지")]
    [SerializeField] private float _sameActionPenalty  = -0.20f;
    [SerializeField] private float _recentRepeatPenalty = -0.35f;
    [SerializeField] private float _consecutivePenalty  = -0.15f;

    [Header("페이즈 보정")]
    [SerializeField] private float _phaseTransitionBonus = 0.20f;

    // 최근 행동 이력
    private readonly int[] _recentActions = { -1, -1, -1 };
    private int _historyIndex;
    private int _lastSelectedPhase = -1;

    // legal mask: 현재 사용 가능한 행동
    // 외부에서 설정 (Phase별 스킬 구현 상황에 따라)
    [SerializeField] private bool[] _legalActions = new bool[ActionCount];

    private void Awake()
    {
        if (_biasTracker == null)  _biasTracker  = GetComponent<PlayerBiasTracker>();
        if (_bossController == null) _bossController = GetComponent<BossController>();

        for (int i = 0; i < ActionCount; i++)
            _legalActions[i] = true;
    }

    // ══════════════════════════════════════════════════════════
    // Legal Mask 관리
    // ══════════════════════════════════════════════════════════

    public void SetLegal(BossActionType action, bool legal)
    {
        _legalActions[(int)action] = legal;
    }

    public void SetLegalMask(bool[] mask)
    {
        int len = Mathf.Min(mask.Length, ActionCount);
        System.Array.Copy(mask, _legalActions, len);
    }

    // ══════════════════════════════════════════════════════════
    // 가중치 계산 + 행동 선택
    // ══════════════════════════════════════════════════════════

    public BossActionType SelectAction()
    {
        float[] weights = CalculateWeights();
        int selected    = WeightedRandomSelect(weights);

        RecordAction(selected);
        return (BossActionType)selected;
    }

    public float[] CalculateWeights()
    {
        float[] w = new float[ActionCount];

        if (_biasTracker == null)
        {
            for (int i = 0; i < ActionCount; i++)
                w[i] = _legalActions[i] ? _baseWeight : 0f;
            return w;
        }

        float melee   = _biasTracker.GetBias(PlayerBiasType.MeleePrefer);
        float range   = _biasTracker.GetBias(PlayerBiasType.RangeKeep);
        float attack  = _biasTracker.GetBias(PlayerBiasType.AttackFocus);
        float survive = _biasTracker.GetBias(PlayerBiasType.SurvivalFirst);
        float parry   = _biasTracker.GetBias(PlayerBiasType.ParryDepend);
        float rope    = _biasTracker.GetBias(PlayerBiasType.RopeManeuver);
        float skill   = _biasTracker.GetBias(PlayerBiasType.SkillCentric);
        float cluster = _biasTracker.GetBias(PlayerBiasType.TeamCluster);
        float spread  = _biasTracker.GetBias(PlayerBiasType.TeamSpread);

        // 기본 가중치 + 편향 기반 보정
        w[0] = _baseWeight + melee  * 0.6f + cluster * 0.3f - range   * 0.4f; // 근접 압박형
        w[1] = _baseWeight + range  * 0.6f + spread  * 0.3f - melee   * 0.4f; // 원거리 견제형
        w[2] = _baseWeight + parry  * 0.7f;                                    // 패링 견제형
        w[3] = _baseWeight + rope   * 0.7f;                                    // 로프 대응형
        w[4] = _baseWeight + attack * 0.5f;                                    // 폭딜 대응형
        w[5] = _baseWeight + survive * 0.6f;                                   // 생존 압박형
        w[6] = _baseWeight + spread  * 0.8f;                                   // 분산 대응형
        w[7] = _baseWeight + cluster * 0.8f;                                   // 밀집 대응형
        w[8] = _baseWeight;                                                    // 적응형 변칙형

        // 비적합 게이트: 편향 < gateThreshold → 가중치 0
        if (melee   < _gateThreshold && cluster < _gateThreshold) w[0] = 0f;
        if (range   < _gateThreshold && spread  < _gateThreshold) w[1] = 0f;
        if (parry   < _gateThreshold) w[2] = 0f;
        if (rope    < _gateThreshold) w[3] = 0f;
        if (attack  < _gateThreshold) w[4] = 0f;
        if (survive < _gateThreshold) w[5] = 0f;
        if (spread  < _gateThreshold) w[6] = 0f;
        if (cluster < _gateThreshold) w[7] = 0f;
        // 적응형(#8)은 게이트 없음 — 항상 후보

        // legal mask 적용
        for (int i = 0; i < ActionCount; i++)
        {
            if (!_legalActions[i]) w[i] = 0f;
        }

        // 반복 방지 패널티
        ApplyRepetitionPenalty(w);

        // 페이즈 전환 보정
        ApplyPhaseBonus(w);

        // 바닥값 적용 (legal + 게이트 통과한 행동만)
        for (int i = 0; i < ActionCount; i++)
        {
            if (w[i] > 0f && w[i] < _floorWeight)
                w[i] = _floorWeight;
        }

        // fallback: 모든 가중치 0이면 legal 행동만 균등 분배
        float total = 0f;
        for (int i = 0; i < ActionCount; i++) total += w[i];

        if (total <= 0f)
        {
            for (int i = 0; i < ActionCount; i++)
            {
                if (_legalActions[i]) w[i] = 1f;
            }
        }

        return w;
    }

    // ══════════════════════════════════════════════════════════
    // 내부
    // ══════════════════════════════════════════════════════════

    private void ApplyRepetitionPenalty(float[] w)
    {
        int last = _recentActions[(_historyIndex - 1 + 3) % 3];
        if (last >= 0 && last < ActionCount)
            w[last] += _sameActionPenalty;

        // 최근 3회 중 2회 이상 같은 행동
        for (int a = 0; a < ActionCount; a++)
        {
            int repeatCount = 0;
            for (int h = 0; h < 3; h++)
            {
                if (_recentActions[h] == a) repeatCount++;
            }
            if (repeatCount >= 2) w[a] += _recentRepeatPenalty;
        }

        // 직전 2회 동일 행동
        int prev1 = _recentActions[(_historyIndex - 1 + 3) % 3];
        int prev2 = _recentActions[(_historyIndex - 2 + 3) % 3];
        if (prev1 >= 0 && prev1 == prev2)
            w[prev1] += _consecutivePenalty;
    }

    private void ApplyPhaseBonus(float[] w)
    {
        if (_bossController == null) return;

        int currentPhase = _bossController.CurrentPhase;
        if (currentPhase != _lastSelectedPhase && _lastSelectedPhase >= 0)
        {
            // 페이즈 전환 직후: 근접 압박, 폭딜 대응에 보너스
            w[0] += _phaseTransitionBonus;
            w[4] += _phaseTransitionBonus;
        }
        _lastSelectedPhase = currentPhase;
    }

    private void RecordAction(int actionIndex)
    {
        _recentActions[_historyIndex % 3] = actionIndex;
        _historyIndex++;
    }

    private int WeightedRandomSelect(float[] weights)
    {
        float total = 0f;
        for (int i = 0; i < weights.Length; i++)
        {
            if (weights[i] < 0f) weights[i] = 0f;
            total += weights[i];
        }

        if (total <= 0f)
        {
            // 최종 안전망: 첫 번째 legal 행동
            for (int i = 0; i < ActionCount; i++)
            {
                if (_legalActions[i]) return i;
            }
            return 0;
        }

        float roll = Random.Range(0f, total);
        float cumulative = 0f;
        for (int i = 0; i < weights.Length; i++)
        {
            cumulative += weights[i];
            if (roll <= cumulative) return i;
        }
        return weights.Length - 1;
    }

    // ══════════════════════════════════════════════════════════
    // 디버그 / 외부 조회
    // ══════════════════════════════════════════════════════════

    public float GetWeight(BossActionType action)
    {
        float[] w = CalculateWeights();
        return w[(int)action];
    }

    public int LastAction => _recentActions[(_historyIndex - 1 + 3) % 3];
}

// ══════════════════════════════════════════════════════════════
// 보스 행동 타입 열거형
// ══════════════════════════════════════════════════════════════
public enum BossActionType
{
    MeleePressure    = 0,  // 근접 압박형
    RangeHarass      = 1,  // 원거리 견제형
    ParryCounter     = 2,  // 패링 견제형
    RopeCounter      = 3,  // 로프 대응형
    BurstCounter     = 4,  // 폭딜 대응형
    SurvivalPressure = 5,  // 생존 압박형
    SpreadCounter    = 6,  // 분산 대응형
    ClusterCounter   = 7,  // 밀집 대응형
    Adaptive         = 8   // 적응형 변칙형
}
