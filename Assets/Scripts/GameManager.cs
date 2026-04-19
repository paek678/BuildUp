using System.Collections.Generic;
using UnityEngine;

// 게임 전체 참조 허브 + 전투 시간 측정
public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }

    [Header("전투 오브젝트")]
    [SerializeField] private List<GameObject> _players = new();
    [SerializeField] private List<GameObject> _bosses  = new();

    [Header("스킬 레지스트리")]
    [SerializeField] private SkillRegistry _skillRegistry;

    [Header("시간")]
    private float _elapsedTime;
    private bool  _isRunning;

    // ── 외부 참조 ────────────────────────────────────────────
    public IReadOnlyList<GameObject> Players => _players;
    public IReadOnlyList<GameObject> Bosses  => _bosses;
    public float                     ElapsedTime => _elapsedTime;

    // 단건 편의 프로퍼티
    public GameObject Player1 => _players.Count > 0 ? _players[0] : null;
    public GameObject Player2 => _players.Count > 1 ? _players[1] : null;
    public GameObject Boss    => _bosses.Count  > 0 ? _bosses[0]  : null;

    // ── 런타임 등록 ──────────────────────────────────────────
    public void RegisterPlayer(GameObject player) { if (!_players.Contains(player)) _players.Add(player); }
    public void RegisterBoss  (GameObject boss)   { if (!_bosses.Contains(boss))   _bosses.Add(boss); }
    public void UnregisterPlayer(GameObject player) => _players.Remove(player);
    public void UnregisterBoss  (GameObject boss)   => _bosses.Remove(boss);

    // ══════════════════════════════════════════════════════════
    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
    }

    // ── 외부 조회 ────────────────────────────────────────────
    public SkillRegistry SkillRegistry => _skillRegistry;

    private void Start()
    {
        SkillBinder.BindAll(_skillRegistry);
        StartTimer();
    }

    private void Update()
    {
        if (_isRunning)
            _elapsedTime += Time.deltaTime;
    }

    // ── 타이머 제어 ──────────────────────────────────────────
    public void StartTimer()
    {
        _elapsedTime = 0f;
        _isRunning   = true;
    }

    public void StopTimer()  => _isRunning = false;
    public void ResumeTimer() => _isRunning = true;
}
