# Codex 시스템 프롬프트 — 테네브리스 (Tenebris)

> 이 프롬프트를 Codex의 System Prompt / Instructions에 붙여넣어 사용할 것.

---

## 프로젝트 개요

- **프로젝트명**: 테네브리스 (Tenebris) / 코드명 Arena Combat
- **장르**: 2인 협동 보스전 3D 탑다운 멀티플레이 액션 로그라이트
- **엔진**: Unity 6 (6000.3.11f1)
- **렌더 파이프라인**: URP 17.3.0
- **네트워크**: Unity NGO + Relay + Unity Transport (Host-authoritative)
- **ML**: ML-Agents 4.0.2
- **언어**: C#, 주석/커밋/문서는 한국어

---

## 병행 작업 환경 (중요)

- **Claude Code + OpenAI Codex 병행 사용 중**
- 작업 전 반드시 `Assets/CHANGES.md`를 읽어 최근 변경사항 파악 후 진행
- 스크립트 생성/수정/삭제 시 `Assets/CHANGES.md`에 변경 내용 기록 (날짜, 경로, 변경 사유)
- AI 관련 코드 변경 시 `Assets/Scripts/AI/AI_SYSTEM.md`도 함께 업데이트
- 변경 의도와 맥락을 명확히 남겨서 다른 AI가 이어받을 수 있도록 할 것

---

## 핵심 원칙 (반드시 준수)

1. **모든 스탯 변경 → StatManager 경유** — HP, Shield, 상태이상, 버프/디버프 직접 필드 수정 금지
2. **새 스킬 부품 → SkillComponents.cs에만 추가** — 다른 파일에 스킬 로직 분산 금지
3. **새 전투 객체 → ICombatant 인터페이스 먼저 구현**
4. **ScriptableObject는 읽기 전용** — 런타임에 SO 수치 변경 금지
5. **2D 레거시 코드 기준 금지** — 3D + Host-authoritative 경로 기준만
6. **UniTask 미설치** — 코루틴 사용, `WaitForSeconds` 반드시 캐싱 (`new WaitForSeconds()` 반복 생성 금지)
7. **Addressables 미설치** — `[SerializeField] private` 직접 참조만 사용

---

## 프로젝트 구조

```
Assets/
├── Scripts/
│   ├── PlayerController.cs          — 플레이어 (ICombatant 구현)
│   ├── BossController.cs            — 보스 (ICombatant 구현)
│   ├── GameManager.cs               — 게임 흐름, Bosses 리스트 관리
│   ├── CardManager.cs               — 카드 드래프트 UI
│   │
│   ├── Stats/
│   │   └── StatManager.cs           — HP/Shield/상태이상/버프/디버프 중앙 관리
│   │
│   ├── State/
│   │   └── StateManager.cs          — 7상태 FSM (Idle/Moving/Casting/Parrying/HitStun/Stunned/Dead)
│   │
│   ├── Skill/
│   │   ├── Core/
│   │   │   ├── SkillDefinition.cs   — SO 메타데이터 + RuntimeStep/RuntimeCondition
│   │   │   ├── SkillComponents.cs   — 스킬 부품 37종 (static class)
│   │   │   ├── SkillLibrary.cs      — 부품 조립 → 완성 스킬 (static class)
│   │   │   ├── SkillBinder.cs       — Library 결과를 SO에 주입 (static class)
│   │   │   ├── SkillBootstrap.cs    — Awake에서 BindAll 호출
│   │   │   ├── SkillExecutor.cs     — 실행 + 쿨타임 관리
│   │   │   ├── SkillManager.cs      — 자동 시전 (슬롯 0~4 순회)
│   │   │   ├── SkillContext.cs      — 실행 중 공유 런타임 정보
│   │   │   ├── SkillRegistry.cs     — SO 전체 풀 관리
│   │   │   └── SkillRangeDisplay.cs — 범위 시각 표시 (프리팹 풀링)
│   │   ├── Area/
│   │   │   ├── SkillArea.cs         — 지속 장판
│   │   │   ├── PersistentAreaManager.cs
│   │   │   └── PersistentAreaPool.cs
│   │   ├── Projectile/
│   │   │   ├── SkillProjectile.cs   — 투사체
│   │   │   └── ProjectilePool.cs
│   │   ├── Interfaces/
│   │   │   ├── ICombatant.cs        — 전투 객체 공통 인터페이스
│   │   │   ├── IPersistentArea.cs
│   │   │   └── IProjectile.cs
│   │   └── Prefab/                  — 프리팹 및 Material
│   │
│   └── AI/
│       └── BossAI/
│           └── DualTargetAgent.cs   — ML-Agents 보스 AI
│
├── ScriptableObjects/
│   └── Skills/                      — 스킬 SO 23개 + SkillRegistry
│
├── Editor/
│   └── SkillDefinitionGenerator.cs  — 메뉴에서 SO 자동 생성
│
├── Scenes/
│   └── Chapter1.unity               — 메인 테스트 씬
│
└── CHANGES.md                       — 변경 이력 (필수 업데이트)
```

---

## 스킬 시스템 구조

### delegate 기반 조립형

```csharp
public delegate void SkillStep(SkillContext ctx);       // 실행 부품
public delegate bool SkillCondition(SkillContext ctx);   // 조건 부품
```

### 실행 플로우

```
SkillManager.Update() → CanCast() → SkillExecutor.Execute() → skill.RuntimeStep.Invoke(ctx)
```

### CanCast 7가지 조건
1. `skill.IsReady` (RuntimeStep 주입됨?)
2. `SkillExecutor.CanUse` (쿨타임 만료?)
3. `StateManager.CanCast` (Stunned/HitStun/Silence/Casting 아닌지)
4. 타겟 존재 + 생존 (Self 타입은 skip)
5. 거리 ≤ skill.Range (Self 타입은 skip)
6. `RuntimeCondition` 검사 (null이면 통과)
7. SkillContext 생성

### 새 스킬 추가 절차
1. SO 생성 (SkillId, Cooldown, Range, TargetType 설정 → SkillRegistry에 등록)
2. `SkillLibrary.cs`에 조립 메서드 추가
3. `SkillBinder.cs`의 `BindAll()`에 바인딩 추가
4. Inspector에서 SkillManager.Slots에 SO 드래그

### 스킬 구현 현황

| 분류 | 전체 | 구현 | 미구현 |
|------|------|------|--------|
| 플레이어 공용 | 12 | 12 | 0 |
| 플레이어 전용 | 6 | 1 | 5 (패링 입력/로프 이벤트 시스템 부재) |
| 보스 공용 | 11 | 9 | 2 (멀티 방향 투사체 래퍼 부재) |

미구현 사유:
- **CounterStance, CounterSlash, CollapseStrike**: 패링 입력 바인딩 부재
- **WireHook, RopeShockwave**: RopeLanding 이벤트 시스템 부재
- **SealChain_Boss**: 4방향 멀티 투사체 래퍼 부재
- **RuptureMagazine_Boss**: 8방향 폭발 패턴 래퍼 부재

---

## ICombatant 인터페이스

PlayerController와 BossController 모두 구현. 주요 메서드:

```csharp
void TakeDamage(float amount, ICombatant attacker = null);
void TakeShieldBreakDamage(float amount, float multiplier, ICombatant attacker = null);
void RecoverHP(float amount);
void AddShield(float amount);
void ApplyStatus(StatusType type, float duration, float value = 0f);
void ApplyBuff(BuffType type, float duration, float value);
void ApplyDebuff(DebuffType type, float duration, float value);
void Knockback(Vector3 direction, float distance);
void Pull(Vector3 towardPosition, float distance, float duration);
void MoveBy(Vector3 direction, float distance, float duration, MoveType moveType);
```

---

## StateManager FSM (7상태)

```
우선순위: Dead > Stunned > HitStun > Parrying > Casting > Moving > Idle
CanCast = true: Idle, Moving 만
CanMove = true: Idle, Moving, Casting 만
```

---

## StatManager 피해 파이프라인

```
TakeDamage(amount, attacker)
  → 패링 체크 (IsParrying → 반사/보상)
  → 배율 적용 (DamageUp, Vulnerable 등)
  → 방어막 흡수 (Shield 우선 소진)
  → HP 감소
  → 사망 체크 (HP ≤ 0 → Dead)
```

---

## 씬 필수 오브젝트 (Chapter1)

| 오브젝트 | 컴포넌트 | Inspector 연결 |
|---------|---------|---------------|
| SkillBootstrap | SkillBootstrap | Registry → SkillRegistry SO |
| PersistentAreaManager | PersistentAreaManager | Pool → PersistentAreaPool |
| PersistentAreaPool | PersistentAreaPool | Prefab → SkillArea 프리팹 |
| ProjectPool | ProjectilePool | Prefab → ProjectileTile 프리팹 |
| SkillRangeDisplay | SkillRangeDisplay | Indicator Prefab → RangeIndicator 프리팹 |
| Player 1P/2P | SkillManager + SkillExecutor + StatManager + StateManager | |

---

## 코딩 컨벤션

### 네이밍
- **private 필드**: `_camelCase` (언더스코어 접두사)
- **public 프로퍼티**: `PascalCase`
- **static readonly**: `PascalCase`
- **enum**: `PascalCase`
- **메서드**: `PascalCase`
- **로컬 변수/파라미터**: `camelCase`

### 스타일
- 싱글톤: `public static Instance { get; private set; }` + Awake 중복 체크
- 코루틴의 WaitForSeconds: 반드시 필드에 캐싱 (`private static readonly WaitForSeconds Wait = new(0.5f);`)
- [SerializeField] private 사용 (public 필드 최소화)
- 주석은 한국어, 불필요한 주석 금지
- 한 파일에 한 클래스 원칙

### 패턴
- 오브젝트 풀링: Queue 기반 (`PersistentAreaPool`, `ProjectilePool` 참고)
- 이벤트: delegate/Action 또는 C# event
- SO: CreateAssetMenu 어트리뷰트, 런타임 수정 금지

---

## 알려진 이슈

1. **투사체 → 보스 충돌 불발**: `SkillProjectile.OnTriggerEnter`에서 `TryGetComponent<ICombatant>`로 검색하는데, 보스의 Collider가 자식 오브젝트에 있으면 부모의 BossController(ICombatant)를 못 찾음. `GetComponentInParent<ICombatant>` 변경 필요
2. **SkillBinder.BindAll 이중 호출**: SkillBootstrap(Awake)과 GameManager(Start) 양쪽에서 호출. 동작에 문제 없으나 중복
3. **플레이어 전용 스킬 5종 미구현**: 패링 입력 시스템/로프 이벤트 시스템 구축 필요
4. **보스 스킬 2종 미구현**: 멀티 방향 투사체 래퍼 구현 필요

---

## 디버그 토글 (Inspector)

| 토글 | 위치 | 설명 |
|------|------|------|
| `_logExecution` | SkillExecutor | 스킬 실행 로그 |
| `_logAutoCast` | SkillManager | CanCast 실패 사유 |
| `_logCombat` | StatManager | 피해/회복/상태이상/사망 |
| `_logRange` | SkillRangeDisplay | 범위 표시 생성 |
| `_showRange` | SkillRangeDisplay | 범위 시각 표시 ON/OFF |

---

## 참조 문서

- `GAME_DESIGN.md` — 전체 기획 및 기술 설계
- `STATE_MANAGER_DESIGN.md` — 7상태 FSM 설계
- `Assets/SKILL_DESIGN.md` — 스킬 부품/조합식 기획
- `Assets/CHANGES.md` — 변경 이력 (작업 전 필수 확인)
- `Assets/Scripts/Skill/SKILL_SYSTEM_README.md` — 스킬 시스템 사용 가이드
- `Assets/Scripts/AI/AI_SYSTEM.md` — AI 시스템 문서
- `Assets/Scripts/AI/BOSS_CURRICULUM.md` — ML 학습 커리큘럼
