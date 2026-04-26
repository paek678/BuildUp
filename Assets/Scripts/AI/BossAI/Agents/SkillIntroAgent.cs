using System.Collections.Generic;
using UnityEngine;
using Unity.MLAgents;
using Unity.MLAgents.Actuators;
using Unity.MLAgents.Sensors;

// Phase 3 — SkillIntro
// 더블 터치 이동 + 원거리 스킬 플레이어 대응 보스 학습 에이전트
//
// BehaviorParameters:
//   Behavior Name           : SkillIntro
//   Vector Observation Size : 55 (Phase3 28 + touch 2 + playerSkills 18 + extra 7)
//   Discrete Branches       : 2 (B0=4 이동, B1=4 스킬)
//   Max Step                : 8000 (권장)
public class SkillIntroAgent : Agent
{
    private const int TouchObsCount       = 2;
    private const int PlayerSkillObsCount = 18;
    private const int PlayerSkillSlots    = 3;
    private const int ExtraObsCount       = 7;

    [Header("이동")]
    [SerializeField] private float _moveSpeed     = 5f;
    [SerializeField] private float _rotationSpeed = 200f;

    [Header("스폰 설정")]
    [SerializeField] private Transform       _bossSpawnPoint;
    [SerializeField] private GameObject      _p1Object;
    [SerializeField] private GameObject      _p2Object;
    [SerializeField] private List<Transform> _playerSpawnPoints;

    [Header("참조")]
    [SerializeField] private BossController           _bossController;
    [SerializeField] private BossObservationCollector  _collector;
    [SerializeField] private TrainingSkillManager      _trainingSkillManager;
    [SerializeField] private SkillManager              _skillManager;
    [SerializeField] private SkillExecutor             _skillExecutor;

    [Header("플레이어 스킬 분배")]
    [SerializeField] private TrainingSkillManager _p1TrainingSkillMgr;
    [SerializeField] private TrainingSkillManager _p2TrainingSkillMgr;

    [Header("더블 터치")]
    [SerializeField] private float _proximityRadius       = 5f;
    [SerializeField] private float _touchReward           = 0.2f;
    [SerializeField] private float _fastDoubleTouchBonus  = 0.3f;
    [SerializeField] private float _doubleTouchWindow     = 3f;
    [SerializeField] private bool  _touchEndEnabled       = true;
    [SerializeField] private float _noTouchPenalty         = -0.5f;
    [SerializeField] private float _partialTouchPenalty    = -0.2f;

    [Header("보상 튜닝")]
    [SerializeField] private float _wStepPenalty        = 0.001f;
    [SerializeField] private float _wFireReward         = 0f;
    [SerializeField] private float _wMissPenalty        = 0.05f;
    [SerializeField] private float _wOutOfRangePenalty  = 0.1f;
    [SerializeField] private float _wDamageReward       = 0.5f;
    [SerializeField] private float _wShieldDamageReward = 0.3f;
    [SerializeField] private float _wHitReward          = 0.2f;
    [SerializeField] private float _wProgress           = 0.3f;
    [SerializeField] private float _wAlign              = 0.003f;
    [SerializeField] private float _wIdlePenalty        = 0.005f;
    [SerializeField] private float _alignDotThreshold   = 0.7f;
    [SerializeField] private float _minMoveDelta        = 0.05f;

    [Header("터치 후 행동")]
    [SerializeField] private float _wRangeMaintain      = 0.1f;
    [SerializeField] private float _rangeTolerance       = 2f;

    [Header("벽 충돌")]
    [SerializeField] private float _wWallHitPenalty  = 0.05f;
    [SerializeField] private float _wWallStayPenalty = 0.01f;

    [Header("종료 조건")]
    [SerializeField] private float _episodeMaxDuration    = 60f;
    [SerializeField] private float _outOfBoundsY          = -5f;
    [SerializeField] private float _outOfBoundsPenalty    = -1.0f;

    [Header("사망 종료")]
    [SerializeField] private float _bossDiedPenalty       = 1.0f;
    [SerializeField] private float _allKilledReward       = 1.0f;
    [SerializeField] private float _playerKilledReward    = 0.3f;
    [SerializeField] private float _hitDeadPlayerPenalty   = 0.3f;

    private Renderer _renderer;
    private float    _episodeStartTime;
    private float    _prevTargetDist = -1f;
    private Vector3  _prevBossPos;
    private bool     _prevPosValid;
    private int      _currentEpisode;

    // 더블 터치 추적
    private bool  _p1Touched;
    private bool  _p2Touched;
    private float _p1TouchTime;
    private float _p2TouchTime;

    // 사망 처리 플래그 (킬 보상 1회 보장)
    private bool _p1DeathHandled;
    private bool _p2DeathHandled;

    // HP/Shield/Hit 추적
    private StatManager  _p1StatManager;
    private StatManager  _p2StatManager;
    private SkillExecutor _p1SkillExecutor;
    private SkillExecutor _p2SkillExecutor;
    private float _prevP1Hp;
    private float _prevP2Hp;
    private float _prevP1Shield;
    private float _prevP2Shield;
    private int   _prevTotalHits;

    // 풀 캐시
    private ProjectilePool     _projectilePool;
    private PersistentAreaPool _areaPool;

    // ══════════════════════════════════════════════════════════
    // 초기화
    // ══════════════════════════════════════════════════════════

    public override void Initialize()
    {
        _renderer = GetComponent<Renderer>();

        if (_bossController == null) _bossController = GetComponent<BossController>();
        if (_collector == null)      _collector      = GetComponent<BossObservationCollector>();
        if (_trainingSkillManager == null) _trainingSkillManager = GetComponent<TrainingSkillManager>();
        if (_skillManager == null)   _skillManager   = GetComponent<SkillManager>();
        if (_skillExecutor == null)  _skillExecutor   = GetComponent<SkillExecutor>();

        _projectilePool = FindAnyObjectByType<ProjectilePool>();
        _areaPool       = FindAnyObjectByType<PersistentAreaPool>();

        _bossController.TrainingMode = true;
        _skillManager.SetAutoCast(false);
        _skillManager.RoundRobinEnabled = true;
    }

    public override void OnEpisodeBegin()
    {
        if (_renderer != null) _renderer.material.color = Color.red;

        CleanupPreviousEpisode();
        SpawnObjects();
        ResetEpisodeState();

        _currentEpisode++;
    }

    private void CleanupPreviousEpisode()
    {
        if (_projectilePool != null) _projectilePool.ReturnAll();
        if (_areaPool != null)       _areaPool.ReturnAll();
    }

    private void ResetEpisodeState()
    {
        _bossController.StatMgr.ResetForTraining();
        _bossController.StateMgr?.ForceReset();

        ResetPlayer(_p1Object);
        ResetPlayer(_p2Object);

        _skillExecutor.ResetAll();
        _trainingSkillManager.ResetForEpisode();

        if (_p1TrainingSkillMgr != null) _p1TrainingSkillMgr.ResetForEpisode();
        if (_p2TrainingSkillMgr != null) _p2TrainingSkillMgr.ResetForEpisode();

        _prevTargetDist   = -1f;
        _prevPosValid     = false;
        _prevBossPos      = transform.position;
        _episodeStartTime = Time.time;
        _prevTotalHits    = 0;

        _p1Touched       = false;
        _p2Touched       = false;
        _p1TouchTime     = -1f;
        _p2TouchTime     = -1f;
        _p1DeathHandled  = false;
        _p2DeathHandled  = false;

        CachePlayerStats();
    }

    private void ResetPlayer(GameObject player)
    {
        if (player == null) return;

        if (player.TryGetComponent(out StatManager stat))
            stat.ResetForTraining();

        if (player.TryGetComponent(out StateManager state))
            state.ForceReset();

        if (player.TryGetComponent(out SkillExecutor executor))
            executor.ResetAll();

        UnfreezePlayer(player);
    }

    private void FreezePlayer(GameObject player)
    {
        if (player == null) return;

        foreach (var mb in player.GetComponents<MonoBehaviour>())
            mb.StopAllCoroutines();

        if (player.TryGetComponent(out UnityEngine.AI.NavMeshAgent nav) && nav.enabled)
        {
            nav.ResetPath();
            nav.velocity = Vector3.zero;
            nav.isStopped = true;
        }

        if (player.TryGetComponent(out Rigidbody rb))
        {
            rb.linearVelocity  = Vector3.zero;
            rb.angularVelocity = Vector3.zero;
            rb.isKinematic     = true;
        }
    }

    private void UnfreezePlayer(GameObject player)
    {
        if (player == null) return;

        if (player.TryGetComponent(out UnityEngine.AI.NavMeshAgent nav))
            nav.isStopped = false;

        if (player.TryGetComponent(out Rigidbody rb))
            rb.isKinematic = false;
    }

    private void CachePlayerStats()
    {
        _p1StatManager   = _p1Object != null ? _p1Object.GetComponent<StatManager>()  : null;
        _p2StatManager   = _p2Object != null ? _p2Object.GetComponent<StatManager>()  : null;
        _p1SkillExecutor = _p1Object != null ? _p1Object.GetComponent<SkillExecutor>() : null;
        _p2SkillExecutor = _p2Object != null ? _p2Object.GetComponent<SkillExecutor>() : null;

        _prevP1Hp     = _p1StatManager != null ? _p1StatManager.GetHPPercent() : 0f;
        _prevP2Hp     = _p2StatManager != null ? _p2StatManager.GetHPPercent() : 0f;
        _prevP1Shield = _p1StatManager != null ? _p1StatManager.GetShield()    : 0f;
        _prevP2Shield = _p2StatManager != null ? _p2StatManager.GetShield()    : 0f;
    }

    private void SpawnObjects()
    {
        if (_bossSpawnPoint != null)
            transform.SetPositionAndRotation(_bossSpawnPoint.position, _bossSpawnPoint.rotation);
        else
            transform.SetPositionAndRotation(Vector3.zero, Quaternion.Euler(0f, 180f, 0f));

        if (_p1Object == null || _p2Object == null) return;
        if (_playerSpawnPoints == null || _playerSpawnPoints.Count < 2) return;

        int idx1 = Random.Range(0, _playerSpawnPoints.Count);
        int idx2;
        do { idx2 = Random.Range(0, _playerSpawnPoints.Count); } while (idx2 == idx1);

        PlaceOnSpawn(_p1Object, _playerSpawnPoints[idx1]);
        PlaceOnSpawn(_p2Object, _playerSpawnPoints[idx2]);

        _collector.SetPlayers(_p1Object, _p2Object);
    }

    private void PlaceOnSpawn(GameObject target, Transform spawn)
    {
        if (target == null || spawn == null) return;

        foreach (var mb in target.GetComponents<MonoBehaviour>())
            mb.StopAllCoroutines();

        if (target.TryGetComponent(out Rigidbody rb))
        {
            rb.linearVelocity  = Vector3.zero;
            rb.angularVelocity = Vector3.zero;
        }

        if (target.TryGetComponent(out UnityEngine.AI.NavMeshAgent nav) && nav.enabled)
        {
            nav.Warp(spawn.position);
            target.transform.rotation = spawn.rotation;
            nav.ResetPath();
            nav.velocity = Vector3.zero;
        }
        else
        {
            target.transform.SetPositionAndRotation(spawn.position, spawn.rotation);
        }
    }

    // ══════════════════════════════════════════════════════════
    // 관측 (55개 — Phase3 28 + touch 2 + playerSkills 18 + extra 7)
    // ══════════════════════════════════════════════════════════

    public override void CollectObservations(VectorSensor sensor)
    {
        int totalObs = BossObservationCollector.Phase3Size + TouchObsCount + PlayerSkillObsCount + ExtraObsCount;

        if (_collector == null)
        {
            sensor.AddObservation(new float[totalObs]);
            return;
        }

        _collector.CollectUpToPhase3(sensor);
        sensor.AddObservation(_p1Touched ? 1f : 0f);
        sensor.AddObservation(_p2Touched ? 1f : 0f);
        CollectPlayerSkillObs(sensor);
        CollectExtraObs(sensor);
    }

    private void CollectPlayerSkillObs(VectorSensor sensor)
    {
        float maxDist    = 55f;
        float maxCd      = 30f;
        int   ttCount    = System.Enum.GetValues(typeof(TargetType)).Length;
        float ttDivisor  = Mathf.Max(ttCount - 1, 1);

        CollectOnePlayerSkills(sensor, _p1TrainingSkillMgr, _p1SkillExecutor, _p1StatManager, maxDist, maxCd, ttDivisor);
        CollectOnePlayerSkills(sensor, _p2TrainingSkillMgr, _p2SkillExecutor, _p2StatManager, maxDist, maxCd, ttDivisor);
    }

    private void CollectOnePlayerSkills(
        VectorSensor sensor,
        TrainingSkillManager tsMgr,
        SkillExecutor executor,
        StatManager statMgr,
        float maxDist, float maxCd, float ttDivisor)
    {
        bool alive = statMgr != null && statMgr.IsAlive;

        for (int i = 0; i < PlayerSkillSlots; i++)
        {
            SkillDefinition skill = (alive && tsMgr != null) ? tsMgr.GetEquippedSkill(i) : null;

            float range = (skill != null) ? Mathf.Clamp01(skill.Range / maxDist) : 0f;
            sensor.AddObservation(range);

            float cdRatio = 0f;
            if (skill != null && executor != null)
            {
                float remaining = executor.GetRemainingCooldown(skill);
                float total     = skill.Cooldown;
                cdRatio = total > 0f ? Mathf.Clamp01(remaining / total) : 0f;
            }
            sensor.AddObservation(cdRatio);

            float tt = (skill != null) ? (float)skill.TargetType / ttDivisor : 0f;
            sensor.AddObservation(tt);
        }
    }

    private void CollectExtraObs(VectorSensor sensor)
    {
        const float maxSpeed    = 12f;
        const float maxBurstDmg = 50f;

        bool p1Alive = _p1StatManager != null && _p1StatManager.IsAlive;
        bool p2Alive = _p2StatManager != null && _p2StatManager.IsAlive;

        // #48 — P1 캐스팅 여부
        sensor.AddObservation(p1Alive && _p1StatManager.IsCasting ? 1f : 0f);
        // #49 — P2 캐스팅 여부
        sensor.AddObservation(p2Alive && _p2StatManager.IsCasting ? 1f : 0f);

        // #50 — P1 평균 이동속도
        sensor.AddObservation(p1Alive ? Mathf.Clamp01(_collector.P1AvgSpeed / maxSpeed) : 0f);
        // #51 — P2 평균 이동속도
        sensor.AddObservation(p2Alive ? Mathf.Clamp01(_collector.P2AvgSpeed / maxSpeed) : 0f);

        // #52 — P1 해금 스킬 수
        int p1Unlocked = (_p1TrainingSkillMgr != null) ? _p1TrainingSkillMgr.UnlockedCount : 0;
        sensor.AddObservation(Mathf.Clamp01((float)p1Unlocked / PlayerSkillSlots));
        // #53 — P2 해금 스킬 수
        int p2Unlocked = (_p2TrainingSkillMgr != null) ? _p2TrainingSkillMgr.UnlockedCount : 0;
        sensor.AddObservation(Mathf.Clamp01((float)p2Unlocked / PlayerSkillSlots));

        // #54 — 보스 최근 피격 버스트 데미지
        sensor.AddObservation(Mathf.Clamp01(_collector.RecentBurstDamage / maxBurstDmg));
    }

    // ══════════════════════════════════════════════════════════
    // 행동 (2 Branch)
    // B0: 0=대기 1=전진 2=좌회전 3=우회전
    // B1: 0=없음 1=슬롯0 2=슬롯1 3=슬롯2
    // ══════════════════════════════════════════════════════════

    public override void OnActionReceived(ActionBuffers actionBuffers)
    {
        _trainingSkillManager.Tick();

        bool p1Alive = _p1StatManager != null && _p1StatManager.IsAlive;
        bool p2Alive = _p2StatManager != null && _p2StatManager.IsAlive;
        if (_p1TrainingSkillMgr != null && p1Alive) _p1TrainingSkillMgr.Tick();
        if (_p2TrainingSkillMgr != null && p2Alive) _p2TrainingSkillMgr.Tick();

        int moveAction  = actionBuffers.DiscreteActions[0];
        int skillAction = actionBuffers.DiscreteActions[1];

        switch (moveAction)
        {
            case 1: transform.position += transform.forward * (_moveSpeed * Time.deltaTime); break;
            case 2: transform.Rotate(0f, -_rotationSpeed * Time.deltaTime, 0f); break;
            case 3: transform.Rotate(0f,  _rotationSpeed * Time.deltaTime, 0f); break;
        }

        bool isMoving = moveAction == 1;
        _bossController.StateMgr?.NotifyMovementInput(isMoving);

        if (skillAction >= 1 && skillAction <= 3)
        {
            int slot = skillAction - 1;
            TryExecuteSkill(slot);
        }

        ApplyStepRewards();
        CheckTermination();
    }

    private void TryExecuteSkill(int slot)
    {
        if (!_trainingSkillManager.CanUseSlot(slot)) return;

        SkillDefinition skill = _trainingSkillManager.GetEquippedSkill(slot);
        if (skill == null) return;

        Transform activeTarget = GetActiveTarget();

        // 살아있는 타겟이 없으면 스킬 사용 자체를 차단 + 페널티
        if (activeTarget == null && skill.TargetType != TargetType.Self)
        {
            AddReward(-_hitDeadPlayerPenalty);
            return;
        }

        ICombatant target = activeTarget != null ? activeTarget.GetComponent<ICombatant>() : null;

        float dist = activeTarget != null
            ? Vector3.Distance(transform.position, activeTarget.position)
            : float.MaxValue;

        var ctx = new SkillContext
        {
            Caster        = _bossController,
            PrimaryTarget = target,
            CastPosition  = transform.position,
            CastDirection = transform.forward,
        };
        ctx.RefreshSnapshot();

        int hitsBefore = _skillExecutor.TotalHitCount;
        bool fired = _skillExecutor.Execute(skill, ctx);

        if (fired)
        {
            if (skill.TargetType != TargetType.Self && dist > skill.Range)
            {
                AddReward(-_wOutOfRangePenalty);
            }
            else
            {
                if (_wFireReward > 0f) AddReward(_wFireReward);

                int hitsAfter = _skillExecutor.TotalHitCount;
                if (hitsAfter == hitsBefore && skill.TargetType != TargetType.Self)
                    AddReward(-_wMissPenalty);
            }
        }
    }

    // ══════════════════════════════════════════════════════════
    // 타겟 전환 — DualTargetAgent 검증 완료 로직
    // ══════════════════════════════════════════════════════════

    private bool ActiveIsP1(float distP1, float distP2)
    {
        bool p1Alive = _p1StatManager != null && _p1StatManager.IsAlive;
        bool p2Alive = _p2StatManager != null && _p2StatManager.IsAlive;

        if (!p1Alive && p2Alive)  return false;
        if (p1Alive  && !p2Alive) return true;

        if (_p1Touched && !_p2Touched) return false;
        if (_p2Touched && !_p1Touched) return true;
        if (_p1Touched && _p2Touched) return distP1 >= distP2;
        return distP1 <= distP2;
    }

    private Transform GetActiveTarget()
    {
        if (_p1Object == null && _p2Object == null) return null;

        bool p1Alive = _p1StatManager != null && _p1StatManager.IsAlive;
        bool p2Alive = _p2StatManager != null && _p2StatManager.IsAlive;
        if (!p1Alive && !p2Alive) return null;

        if (_p1Object == null) return p2Alive ? _p2Object.transform : null;
        if (_p2Object == null) return p1Alive ? _p1Object.transform : null;

        if (!p1Alive) return _p2Object.transform;
        if (!p2Alive) return _p1Object.transform;

        float distP1 = Vector3.Distance(transform.position, _p1Object.transform.position);
        float distP2 = Vector3.Distance(transform.position, _p2Object.transform.position);

        return ActiveIsP1(distP1, distP2) ? _p1Object.transform : _p2Object.transform;
    }

    // ══════════════════════════════════════════════════════════
    // 근접 터치 판정
    // ══════════════════════════════════════════════════════════

    private bool CheckProximityTouch(float distP1, float distP2)
    {
        float now = Time.time;
        bool p1Alive = _p1StatManager != null && _p1StatManager.IsAlive;
        bool p2Alive = _p2StatManager != null && _p2StatManager.IsAlive;

        if (!_p1Touched && p1Alive && distP1 < _proximityRadius)
        {
            _p1Touched = true;
            _p1TouchTime = now;
            AddReward(_touchReward);
            _prevTargetDist = -1f;
        }
        if (!_p2Touched && p2Alive && distP2 < _proximityRadius)
        {
            _p2Touched = true;
            _p2TouchTime = now;
            AddReward(_touchReward);
            _prevTargetDist = -1f;
        }

        if (!_p1Touched || !_p2Touched) return false;
        if (!_touchEndEnabled) return false;

        float gap  = Mathf.Abs(_p1TouchTime - _p2TouchTime);
        bool isFast = gap <= _doubleTouchWindow;
        if (isFast) AddReward(_fastDoubleTouchBonus);

        if (_renderer != null) _renderer.material.color = isFast ? Color.green : Color.cyan;
        EndEpisode();
        return true;
    }

    // ══════════════════════════════════════════════════════════
    // Action Masking
    // ══════════════════════════════════════════════════════════

    public override void WriteDiscreteActionMask(IDiscreteActionMask actionMask)
    {
        for (int slot = 0; slot < 3; slot++)
        {
            int actionIndex = slot + 1;
            if (!_trainingSkillManager.CanUseSlot(slot))
            {
                actionMask.SetActionEnabled(1, actionIndex, false);
            }
        }
    }

    // ══════════════════════════════════════════════════════════
    // 스텝 보상
    // ══════════════════════════════════════════════════════════

    private void ApplyStepRewards()
    {
        AddReward(-_wStepPenalty);

        ApplyDamageRewards();

        if (_p1Object == null && _p2Object == null) return;

        bool p1Alive = _p1StatManager != null && _p1StatManager.IsAlive;
        bool p2Alive = _p2StatManager != null && _p2StatManager.IsAlive;
        if (!p1Alive && !p2Alive) return;

        Vector3 bossPos = transform.position;

        float distP1 = _p1Object != null ? Vector3.Distance(bossPos, _p1Object.transform.position) : float.MaxValue;
        float distP2 = _p2Object != null ? Vector3.Distance(bossPos, _p2Object.transform.position) : float.MaxValue;

        if (CheckProximityTouch(distP1, distP2)) return;

        bool    activeIsP1 = ActiveIsP1(distP1, distP2);
        float   targetDist = activeIsP1 ? distP1 : distP2;
        Vector3 targetPos  = activeIsP1 ? _p1Object.transform.position : _p2Object.transform.position;
        Vector3 targetDir  = (targetPos - bossPos).normalized;
        Vector3 fwd        = transform.forward;

        bool bothTouched = _p1Touched && _p2Touched;

        if (bothTouched)
        {
            float optimalRange = GetAverageSkillRange();
            float deviation = Mathf.Abs(targetDist - optimalRange);
            if (deviation < _rangeTolerance)
                AddReward(_wRangeMaintain);
            else
                AddReward(-_wRangeMaintain * 0.5f);
        }
        else if (_prevTargetDist > 0f)
        {
            float delta = _prevTargetDist - targetDist;
            AddReward(delta * _wProgress);
        }
        _prevTargetDist = targetDist;

        if (Vector3.Dot(fwd, targetDir) > _alignDotThreshold)
            AddReward(_wAlign);

        if (_prevPosValid)
        {
            float moveDelta = Vector3.Distance(bossPos, _prevBossPos);
            if (moveDelta < _minMoveDelta)
                AddReward(-_wIdlePenalty);
        }
        _prevBossPos  = bossPos;
        _prevPosValid = true;
    }

    private void ApplyDamageRewards()
    {
        float curP1Hp = _p1StatManager != null ? _p1StatManager.GetHPPercent() : 0f;
        float curP2Hp = _p2StatManager != null ? _p2StatManager.GetHPPercent() : 0f;

        float hpDelta = (_prevP1Hp - curP1Hp) + (_prevP2Hp - curP2Hp);
        if (hpDelta > 0f)
            AddReward(hpDelta * _wDamageReward);

        _prevP1Hp = curP1Hp;
        _prevP2Hp = curP2Hp;

        float curP1Shield = _p1StatManager != null ? _p1StatManager.GetShield() : 0f;
        float curP2Shield = _p2StatManager != null ? _p2StatManager.GetShield() : 0f;

        float shieldDelta = (_prevP1Shield - curP1Shield) + (_prevP2Shield - curP2Shield);
        if (shieldDelta > 0f)
        {
            float p1Max = _p1StatManager != null ? _p1StatManager.GetShieldMax() : 1f;
            float p2Max = _p2StatManager != null ? _p2StatManager.GetShieldMax() : 1f;
            float maxShield = Mathf.Max(p1Max + p2Max, 1f);
            AddReward((shieldDelta / maxShield) * _wShieldDamageReward);
        }

        _prevP1Shield = curP1Shield;
        _prevP2Shield = curP2Shield;

        int curHits = _skillExecutor.TotalHitCount;
        if (curHits > _prevTotalHits)
        {
            int newHits = curHits - _prevTotalHits;
            AddReward(newHits * _wHitReward);
        }
        _prevTotalHits = curHits;
    }

    private float GetAverageSkillRange()
    {
        float sum = 0f;
        int count = 0;
        for (int i = 0; i < 3; i++)
        {
            SkillDefinition skill = _trainingSkillManager.GetEquippedSkill(i);
            if (skill != null && skill.TargetType != TargetType.Self)
            {
                sum += skill.Range;
                count++;
            }
        }
        return count > 0 ? sum / count : _proximityRadius;
    }

    // ══════════════════════════════════════════════════════════
    // 종료 조건
    // ══════════════════════════════════════════════════════════

    private void CheckTermination()
    {
        if (!_bossController.IsAlive)
        {
            Debug.Log($"[SkillIntro] EP#{_currentEpisode} 종료: 보스 사망 (elapsed={Time.time - _episodeStartTime:F1}s)");
            AddReward(-_bossDiedPenalty);
            if (_renderer != null) _renderer.material.color = Color.black;
            EndEpisode();
            return;
        }

        bool p1Dead = _p1StatManager != null && !_p1StatManager.IsAlive;
        bool p2Dead = _p2StatManager != null && !_p2StatManager.IsAlive;

        if (p1Dead && !_p1DeathHandled)
        {
            _p1DeathHandled = true;
            Debug.Log($"[SkillIntro] EP#{_currentEpisode} P1 사망 (elapsed={Time.time - _episodeStartTime:F1}s)");
            AddReward(_playerKilledReward);
            if (!_p1Touched) { _p1Touched = true; _p1TouchTime = Time.time; }
            _prevTargetDist = -1f;
            FreezePlayer(_p1Object);
        }
        if (p2Dead && !_p2DeathHandled)
        {
            _p2DeathHandled = true;
            Debug.Log($"[SkillIntro] EP#{_currentEpisode} P2 사망 (elapsed={Time.time - _episodeStartTime:F1}s)");
            AddReward(_playerKilledReward);
            if (!_p2Touched) { _p2Touched = true; _p2TouchTime = Time.time; }
            _prevTargetDist = -1f;
            FreezePlayer(_p2Object);
        }

        if (p1Dead && p2Dead)
        {
            Debug.Log($"[SkillIntro] EP#{_currentEpisode} 종료: 양쪽 플레이어 사망 (elapsed={Time.time - _episodeStartTime:F1}s)");
            AddReward(_allKilledReward);
            if (_renderer != null) _renderer.material.color = Color.green;
            EndEpisode();
            return;
        }

        if (transform.position.y < _outOfBoundsY)
        {
            Debug.Log($"[SkillIntro] EP#{_currentEpisode} 종료: 맵 밖 추락 y={transform.position.y:F1} (elapsed={Time.time - _episodeStartTime:F1}s)");
            AddReward(_outOfBoundsPenalty);
            if (_renderer != null) _renderer.material.color = Color.gray;
            EndEpisode();
            return;
        }

        if (Time.time - _episodeStartTime > _episodeMaxDuration)
        {
            string touchInfo = _p1Touched && _p2Touched ? "양쪽터치"
                : _p1Touched ? "P1만터치" : _p2Touched ? "P2만터치" : "터치없음";
            Debug.Log($"[SkillIntro] EP#{_currentEpisode} 종료: 시간초과 {_episodeMaxDuration}s ({touchInfo})");

            if (!_p1Touched && !_p2Touched)
                AddReward(_noTouchPenalty);
            else if (_p1Touched ^ _p2Touched)
                AddReward(_partialTouchPenalty);

            if (_renderer != null) _renderer.material.color = Color.magenta;
            EndEpisode();
        }
    }

    // ══════════════════════════════════════════════════════════
    // 벽 충돌 패널티
    // ══════════════════════════════════════════════════════════

    private void OnCollisionEnter(Collision collision)
    {
        if (!collision.gameObject.CompareTag("Wall")) return;
        AddReward(-_wWallHitPenalty);
        if (_renderer != null) _renderer.material.color = Color.yellow;
    }

    private void OnCollisionStay(Collision collision)
    {
        if (!collision.gameObject.CompareTag("Wall")) return;
        AddReward(-_wWallStayPenalty * Time.fixedDeltaTime);
    }

    // ══════════════════════════════════════════════════════════
    // 휴리스틱
    // ══════════════════════════════════════════════════════════

    public override void Heuristic(in ActionBuffers actionsOut)
    {
        var d = actionsOut.DiscreteActions;
        d[0] = 0;
        d[1] = 0;

        if (Input.GetKey(KeyCode.W))      d[0] = 1;
        else if (Input.GetKey(KeyCode.A)) d[0] = 2;
        else if (Input.GetKey(KeyCode.D)) d[0] = 3;

        if (Input.GetKey(KeyCode.Alpha1)) d[1] = 1;
        if (Input.GetKey(KeyCode.Alpha2)) d[1] = 2;
        if (Input.GetKey(KeyCode.Alpha3)) d[1] = 3;
    }
}
