# AI System - 테네브리스 (Tenebris)

2인 협동 보스전 3D 탑다운 액션 로그라이트의 AI 시스템 문서.
보스는 **ML-Agents PPO**로 학습하고, 플레이어 봇은 **Unity Behavior Graph**로 행동을 제어한다.

---

## 디렉토리 구조

```
Assets/Scripts/AI/
├── BossAI/
│   ├── Agents/                        ← Phase별 ML-Agent + 학습 모델
│   │   ├── BossAgent.cs               ← Phase 1 (6 obs, 4 actions)
│   │   ├── DualTargetAgent.cs         ← Phase 2 (11 obs, 4 actions)
│   │   ├── SkillIntroAgent.cs         ← Phase 3 (24 obs, 2 Branch: 이동4+스킬4)
│   │   └── BasicMove.onnx             ← Phase 1 학습 완료 모델 (2M 스텝)
│   │
│   ├── Observation/                   ← 관측/편향/가중치 (에이전트가 참조)
│   │   ├── BossObservationCollector.cs ← Phase 3+ 관측값 중앙 수집 (34개)
│   │   ├── PlayerBiasTracker.cs        ← 9종 플레이어 편향 점수 추적
│   │   └── BossActionWeightCalculator.cs ← 9종 보스 행동 가중치 계산
│   │
│   └── Training/                      ← 학습 전용 유틸
│       └── TrainingSkillManager.cs     ← Phase 3 점진적 스킬 해금
│
└── Player/
    ├── basicMove/             ← 1인용 기본 행동 그래프 (완성)
    │   ├── OnlyMove.asset             Behavior Graph 에셋
    │   ├── PlayerBotBlackboardInit.cs 블랙보드 초기화
    │   ├── GetFleePositionAction.cs   도주 위치 계산 노드
    │   ├── PickRandomNavMeshPointAction.cs 순찰 위치 계산 노드
    │   └── WeightedRandomCompositeSequence.cs 가중치 랜덤 분기 노드
    │
    └── DoubleMove/            ← 2인 협동 행동 그래프 (예정)

프로젝트 루트/
├── BasicMove_config.yaml     ← ML-Agents 학습 설정
└── results/                  ← 학습 결과 (체크포인트, 로그)
    ├── BasicMove1/
    ├── BasicMove1_Re/
    └── BasicMove2/            ← 최종 사용 모델
```

---

## 1. 보스 AI (ML-Agents PPO)

### 개요

보스가 **도망치는 플레이어를 추적해서 접촉**하는 행동을 강화학습으로 학습한다.
학습 프레임워크는 Unity ML-Agents, 알고리즘은 PPO (Proximal Policy Optimization).

### 파일: `BossAI/BossAgent.cs`

`Agent` 클래스를 상속하며, 관측 수집 → 행동 선택 → 보상 수신 루프로 동작한다.

#### 관측값 (Observations) — 6개

| 인덱스 | 값 | 정규화 | 설명 |
|:---:|------|:---:|------|
| 0 | `dirToPlayer.x` | -1~1 | 플레이어 방향 X (정규화) |
| 1 | `dirToPlayer.z` | -1~1 | 플레이어 방향 Z (정규화) |
| 2 | `distance` | 0~1 | 플레이어 거리 (÷ maxDistance) |
| 3 | `forward.x` | -1~1 | 보스 전방 방향 X |
| 4 | `forward.z` | -1~1 | 보스 전방 방향 Z |
| 5 | `dot(forward, dir)` | -1~1 | 전방과 플레이어 방향 정렬도 |

BehaviorParameters 설정: `Vector Observation Size: 6`

#### 행동 (Actions) — 이산 1브랜치, 4가지

| 값 | 행동 | 설명 |
|:---:|------|------|
| 0 | 대기 | 아무 것도 안 함 |
| 1 | 전진 | `transform.forward * moveSpeed * dt` |
| 2 | 좌회전 | `Rotate(0, -rotSpeed * dt, 0)` |
| 3 | 우회전 | `Rotate(0, +rotSpeed * dt, 0)` |

BehaviorParameters 설정: `Discrete Branches: 1, Branch 0 Size: 4`

#### 보상 (Rewards)

| 조건 | 보상 | 설명 |
|------|:---:|------|
| 매 스텝 | -0.001 | 시간 패널티 (빠른 행동 유도) |
| 플레이어 접근 | +0.005 × (1 - dist/max) | 가까울수록 보상 |
| 벽 충돌 진입 | -0.05 | 벽에 부딪힌 순간 |
| 벽 충돌 유지 | -0.01 × dt | 벽에 붙어있는 동안 |
| 플레이어 접촉 | +1.0 | 에피소드 성공 → EndEpisode() |

#### 에피소드 흐름

```
OnEpisodeBegin()
  ├── 보스 → _bossSpawnPoint 위치로 초기화
  └── 플레이어 → _playerSpawnPoints 중 랜덤 선택

매 프레임 반복:
  CollectObservations() → 6개 관측값 수집
  OnActionReceived()   → 행동 실행 + 보상 계산
  
종료 조건:
  ├── 플레이어 접촉 (OnTriggerEnter, Tag: "Player") → +1.0, EndEpisode()
  └── MaxStep 도달 (5000) → 자동 종료
```

#### 휴리스틱 (수동 테스트)

학습 전 직접 조작으로 동작 확인:
- `W` → 전진 (action 1)
- `A` → 좌회전 (action 2)
- `D` → 우회전 (action 3)

#### 병렬 학습 지원

모든 위치/회전을 **LocalSpace** 기준으로 처리하므로, MainGame 오브젝트를 복사해서
여러 환경을 동시에 배치하면 병렬 학습이 가능하다.

### 학습 설정: `BasicMove_config.yaml`

```yaml
behaviors:
  BasicMove:
    trainer_type: ppo
    hyperparameters:
      batch_size: 1024
      buffer_size: 10240
      learning_rate: 0.0003        # linear 감쇠
      beta: 0.005                  # 엔트로피 정규화 (linear 감쇠)
      epsilon: 0.2                 # 클리핑 범위 (linear 감쇠)
      lambd: 0.95                  # GAE lambda
      num_epoch: 3
    network_settings:
      normalize: false
      hidden_units: 128            # 은닉 레이어 뉴런 수
      num_layers: 2                # 은닉 레이어 수
    reward_signals:
      extrinsic:
        gamma: 0.99                # 할인율
        strength: 1.0
    max_steps: 2000000             # 총 학습 스텝
    time_horizon: 64               # 보상 계산 시간 범위
    summary_freq: 5000             # TensorBoard 기록 간격
    keep_checkpoints: 5
```

학습 실행 명령:
```bash
mlagents-learn BasicMove_config.yaml --run-id=BasicMove2
```

### 학습 이력

| 실행 ID | 스텝 수 | 최종 보상 | 비고 |
|---------|---------|----------|------|
| BasicMove1 | 14,977 | -2.414 | 초기 시도, 수렴 실패 |
| BasicMove1_Re | 16,420 | — | 재시도, 조기 중단 |
| **BasicMove2** | **2,000,046** | **-0.741** | **최종 모델, 현재 사용 중** |

학습 결과 모델: `results/BasicMove2/BasicMove.onnx`
→ 프로젝트 내 복사본: `Assets/Scripts/AI/BossAI/BasicMove.onnx`

---

## 2. 플레이어 봇 AI (Unity Behavior Graph)

### 개요

플레이어 봇은 **Unity 6 Behavior Graph** 패키지(`com.unity.behavior` v1.0.15)로 행동을 제어한다.
ML 학습이 아닌 **규칙 기반 행동 트리**로, 시각적 노드 에디터에서 그래프를 구성하고
커스텀 C# 노드를 작성하여 로직을 구현한다.

### 구성 요소

Behavior Graph 시스템은 4가지 요소로 구성된다:

| 요소 | 역할 | 예시 |
|------|------|------|
| **BehaviorGraphAgent** | 그래프 실행기 (컴포넌트) | 게임 오브젝트에 부착 |
| **Blackboard** | 공유 데이터 저장소 | Boss, PatrolRadius 등 |
| **Action 노드** | 실행 로직 (이동, 계산 등) | GetFleePosition, PickRandomPoint |
| **Composite 노드** | 흐름 제어 (분기, 반복 등) | WeightedRandomComposite |

### 현재 구현: basicMove (1인용 순찰/도주)

#### 행동 트리 구조

```
[Start]
└── [Repeat Forever]
    └── [WeightedRandomComposite]  ← 가중치: [7, 3]
        │
        ├── Branch A (70%): 순찰
        │   ├── [PickRandomNavMeshPoint] → TargetPosition
        │   └── [NavigateTo] → TargetPosition으로 이동
        │
        └── Branch B (30%): 도주
            ├── [GetFleePosition] → FleePosition
            └── [NavigateTo] → FleePosition으로 이동
```

#### 블랙보드 변수

| 변수 | 타입 | 초기값 | 설정 위치 |
|------|------|--------|----------|
| `Boss` | `GameObject` | FindWithTag("Boss") | PlayerBotBlackboardInit |
| `PatrolRadius` | `float` | 6.0 | PlayerBotBlackboardInit |
| `FleeDistance` | `float` | 4.0 | PlayerBotBlackboardInit |
| `Weights` | `List<float>` | [7, 3] | PlayerBotBlackboardInit |
| `TargetPosition` | `Vector3` | — | PickRandomNavMeshPoint가 갱신 |
| `FleePosition` | `Vector3` | — | GetFleePosition이 갱신 |

#### 초기화: `PlayerBotBlackboardInit.cs`

`MonoBehaviour`로, 게임 시작 시 `BehaviorGraphAgent`의 블랙보드에 변수를 주입한다.

```
Awake()
  ├── BehaviorGraphAgent 컴포넌트 참조 획득
  └── Boss 오브젝트 자동 탐색 (Tag: "Boss")

Start()
  └── blackboard에 Boss, PatrolRadius, FleeDistance, Weights 설정
```

Inspector에서 값을 조절할 수 있다:
- `_boss`: 보스 오브젝트 직접 할당 (없으면 자동 탐색)
- `_patrolRadius`: 순찰 반경
- `_fleeDistance`: 도주 거리
- `_weights`: [순찰 가중치, 도주 가중치]

### 커스텀 노드 상세

#### 커스텀 노드 공통 패턴

모든 커스텀 노드는 다음 패턴을 따른다:

```csharp
using Unity.Behavior;
using Unity.Properties;
using Action = Unity.Behavior.Action;  // UnityEngine.Action과 충돌 방지

[Serializable, GeneratePropertyBag]
[NodeDescription(
    name: "노드 이름",
    story: "[Agent] 가 [Target] 으로부터 도망갈 위치를 계산",  // 에디터 표시용
    category: "Action/Navigation",
    id: "고유 GUID"
)]
public partial class 노드클래스 : Action  // 또는 Composite, Condition
{
    // 블랙보드 변수 연결
    [SerializeReference] public BlackboardVariable<GameObject> Agent;
    [SerializeReference] public BlackboardVariable<float> Distance;
    [SerializeReference] public BlackboardVariable<Vector3> Result;

    protected override Status OnStart()
    {
        // 즉시 완료되는 로직 → return Status.Success 또는 Failure
        // 지속 실행 → return Status.Running (OnUpdate에서 계속)
    }

    protected override Status OnUpdate()
    {
        // Running 상태일 때 매 프레임 호출
        return Status.Success;
    }

    protected override void OnEnd() { }
}
```

**핵심 규칙:**
- `partial class` 필수 (`[GeneratePropertyBag]`이 코드 생성)
- 블랙보드 변수는 `[SerializeReference] public BlackboardVariable<T>` 형태
- `Status` 반환: `Success` / `Failure` / `Running` / `Waiting`
- `story` 문자열의 `[변수명]`은 에디터에서 드래그 연결 가능한 슬롯이 됨

#### Node 1: GetFleePositionAction

**역할:** 보스 반대 방향으로 가장 먼 NavMesh 유효 지점을 계산한다.

| 블랙보드 변수 | 방향 | 타입 | 설명 |
|:---:|:---:|------|------|
| `Agent` | 입력 | `GameObject` | 자기 자신 |
| `Target` | 입력 | `GameObject` | 보스 |
| `Distance` | 입력 | `float` | 도주 반경 |
| `FleePosition` | 출력 | `Vector3` | 계산된 도주 위치 |

**알고리즘:**

```
agentPos 기준으로 12방향 (30° 간격) 균등 샘플링
  ↓
각 방향으로 Distance 만큼 떨어진 후보 지점 생성
  ↓
NavMesh.SamplePosition으로 유효성 검증 (반경 1.5m)
  ↓
보스와 가장 먼 유효 지점을 FleePosition에 저장
```

```
            ② ①         
          ③       ⑫       각 번호 = 30° 간격 후보 지점
        ④    [Self]   ⑪    
          ⑤       ⑩       [Boss]가 오른쪽에 있다면
            ⑥ ⑨           ④~⑥ 근처가 최적 도주 지점
          ⑦   ⑧
```

OnStart에서 즉시 계산 → `Status.Success` 반환.
유효 지점이 하나도 없으면 `Status.Failure` 반환.

#### Node 2: PickRandomNavMeshPointAction

**역할:** 자기 위치 기준 반경 내 NavMesh 위 랜덤 지점을 선택한다.

| 블랙보드 변수 | 방향 | 타입 | 설명 |
|:---:|:---:|------|------|
| `Agent` | 입력 | `GameObject` | 자기 자신 |
| `Radius` | 입력 | `float` | 순찰 반경 |
| `TargetPosition` | 출력 | `Vector3` | 선택된 순찰 지점 |

**알고리즘:**

```
최대 10회 시도:
  Random.insideUnitSphere * Radius → 후보 지점 (Y=0)
  NavMesh.SamplePosition으로 유효성 검증
  유효하면 → TargetPosition에 저장, Success 반환
  
10회 모두 실패 → Failure 반환
```

#### Node 3: WeightedRandomCompositeSequence

**역할:** 자식 브랜치 중 하나를 가중치 확률로 선택 실행한다.

| 블랙보드 변수 | 방향 | 타입 | 설명 |
|:---:|:---:|------|------|
| `Weight` | 입력 | `List<float>` | 각 브랜치의 가중치 |

`Composite` 클래스를 상속하며, `Children` 리스트로 자식 노드에 접근한다.

**알고리즘:**

```
가중치 목록: [7, 3]  →  총합 10
  ├── 0~6.99 → 브랜치 0 (순찰, 70%)
  └── 7~9.99 → 브랜치 1 (도주, 30%)

Random(0, 총합) 으로 누적 확률 선택
선택된 브랜치의 자식 노드를 StartNode()로 실행
OnUpdate()에서 자식의 Status를 그대로 반환 (Waiting/Success/Failure)
```

### 게임 오브젝트 구성

플레이어 봇 오브젝트에 필요한 컴포넌트:

```
PlayerBot (GameObject)
├── NavMeshAgent              ← Unity 내장, 경로 탐색 및 이동
├── BehaviorGraphAgent        ← Behavior Graph 실행기
│   └── Graph: OnlyMove.asset     ← 행동 그래프 에셋 연결
└── PlayerBotBlackboardInit   ← 블랙보드 변수 초기화
    ├── Boss: [Boss 오브젝트]
    ├── PatrolRadius: 6.0
    ├── FleeDistance: 4.0
    └── Weights: [7, 3]
```

---

## 3. DoubleMove — 2인 협동 행동 그래프 (상세 설계)

### 3-1. 목적

보스 학습 환경에 **2명의 플레이어 봇**을 배치하여, 서로의 위치를 인식하고
협동 전투 포지셔닝을 수행하는 행동 그래프를 구축한다.

### 3-2. basicMove와의 차이

| 항목 | basicMove (현재) | DoubleMove (예정) |
|------|:---:|:---:|
| 플레이어 수 | 1명 | 2명 |
| 아군 인식 | 없음 | 있음 (Ally 블랙보드 변수) |
| 행동 선택 | 가중치 랜덤 (순찰 70% / 도주 30%) | **우선순위 Selector** (5단계) |
| 보스 시선 인식 | 없음 | 있음 (BossLookingAtMe) |
| 협공 각도 | 없음 | 있음 (FlankAngle) |
| 이동 목적 | 랜덤 배회 + 도망 | 적정 거리 유지 + 측면 공격 + 선회 |

### 3-3. 행동 트리 전체 구조

```
[Start]                                   ← 내장 (그래프 진입점)
│
└── [Repeat Forever]                      ← 내장 (무한 반복)
    │
    └── [Sequence]                        ← 내장 (자식 4개를 순서대로 실행)
        │
        │                ┌────────────────────────────────────────────┐
        ├── ① [Action: UpdateSituationAction]                        │
        │       입력: Self(GO), Boss(GO), Ally(GO)                   │
        │       출력: BossDistance, AllyDistance, FlankAngle,         │
        │             BossLookingAtMe, StrafeSign                    │
        │       반환: 항상 Success                                    │
        │                └────────────────────────────────────────────┘
        │
        │                ┌────────────────────────────────────────────┐
        ├── ② [Selector]  ← 내장 (위→아래 우선순위 평가)              │
        │   │              첫 번째 Success 분기에서 중단               │
        │   │              └────────────────────────────────────────────┘
        │   │
        │   │   ┌─── 1순위: 긴급 회피 ─────────────────────────────┐
        │   ├── [Sequence]                                          │
        │   │   │                                                   │
        │   │   ├── [Condition: IsBossTooClose]                     │
        │   │   │     입력: BossDistance(float), CloseThreshold(float)
        │   │   │     판정: BossDistance < CloseThreshold            │
        │   │   │     false → Sequence 실패 → Selector 다음 자식으로 │
        │   │   │                                                   │
        │   │   └── [Action: CalcFleePositionAction]                │
        │   │         입력: Self(GO), Boss(GO), FleeDistance(float)  │
        │   │         출력: TargetPosition(V3)                      │
        │   │         동작: 보스 반대 방향 12방향 샘플링              │
        │   │   └───────────────────────────────────────────────────┘
        │   │
        │   │   ┌─── 2순위: 겹침 해소 ─────────────────────────────┐
        │   ├── [Sequence]                                          │
        │   │   │                                                   │
        │   │   ├── [Condition: IsAllyTooClose]                     │
        │   │   │     입력: AllyDistance(float), MinAllyDist(float)  │
        │   │   │     판정: AllyDistance < MinAllyDist               │
        │   │   │                                                   │
        │   │   └── [Action: CalcSpreadPositionAction]              │
        │   │         입력: Self(GO), Ally(GO), Boss(GO),           │
        │   │               SpreadDistance(float),                   │
        │   │               OptimalMin(float), OptimalMax(float)    │
        │   │         출력: TargetPosition(V3)                      │
        │   │         동작: 아군 반대 방향 + 보스 거리 보정           │
        │   │   └───────────────────────────────────────────────────┘
        │   │
        │   │   ┌─── 3순위: 측면 공격 ─────────────────────────────┐
        │   ├── [Sequence]                                          │
        │   │   │                                                   │
        │   │   ├── [Condition: IsBossTargetingAlly]                │
        │   │   │     입력: BossLookingAtMe(bool)                   │
        │   │   │     판정: BossLookingAtMe == false                │
        │   │   │                                                   │
        │   │   └── [Action: CalcFlankPositionAction]               │
        │   │         입력: Self(GO), Boss(GO), Ally(GO),           │
        │   │               FlankAngleOffset(float),                │
        │   │               OptimalMin(float), OptimalMax(float)    │
        │   │         출력: TargetPosition(V3)                      │
        │   │         동작: 보스 기준 아군 반대편 110° 측면 위치     │
        │   │   └───────────────────────────────────────────────────┘
        │   │
        │   │   ┌─── 4순위: 선회 유지 ─────────────────────────────┐
        │   ├── [Sequence]                                          │
        │   │   │                                                   │
        │   │   ├── [Condition: IsAtOptimalRange]                   │
        │   │   │     입력: BossDistance(float),                     │
        │   │   │           OptimalMin(float), OptimalMax(float)    │
        │   │   │     판정: OptimalMin ≤ BossDistance ≤ OptimalMax   │
        │   │   │                                                   │
        │   │   └── [Action: CalcStrafePositionAction]              │
        │   │         입력: Self(GO), Boss(GO), StrafeSign(float),  │
        │   │               StrafeStep(float),                      │
        │   │               OptimalMin(float), OptimalMax(float)    │
        │   │         출력: TargetPosition(V3)                      │
        │   │         동작: 보스 주변 StrafeSign 방향 30° 원형 선회  │
        │   │   └───────────────────────────────────────────────────┘
        │   │
        │   │   ┌─── 5순위: 접근 (기본 — 조건 없음) ───────────────┐
        │   └── [Action: CalcApproachPositionAction]                │
        │           입력: Self(GO), Boss(GO), OptimalMax(float)     │
        │           출력: TargetPosition(V3)                        │
        │           동작: 보스 방향 OptimalMax 지점까지 접근         │
        │     └───────────────────────────────────────────────────────┘
        │
        │                ┌────────────────────────────────────────────┐
        ├── ③ [Action: SetNavDestinationAction]                      │
        │       입력: Self(GO), TargetPosition(V3)                   │
        │       동작: NavMeshAgent.SetDestination(TargetPosition)    │
        │       반환: 항상 Success (이동은 NavMeshAgent가 비동기 처리)│
        │                └────────────────────────────────────────────┘
        │
        │                ┌────────────────────────────────────────────┐
        └── ④ [Wait]      ← 내장                                    │
                입력: ReEvalInterval (0.15초)                        │
                동작: 다음 틱까지 대기 → ①로 복귀                    │
                └────────────────────────────────────────────────────┘
```

#### Selector 실행 흐름

```
매 틱 Selector 진입 →
  ├→ IsBossTooClose?      YES → CalcFlee     → Selector 종료 (Success)
  │                        NO  ↓
  ├→ IsAllyTooClose?      YES → CalcSpread   → Selector 종료
  │                        NO  ↓
  ├→ IsBossTargetingAlly?  YES → CalcFlank   → Selector 종료
  │                        NO  ↓
  ├→ IsAtOptimalRange?    YES → CalcStrafe   → Selector 종료
  │                        NO  ↓
  └→ CalcApproach          무조건 실행        → Selector 종료

→ SetNavDestination → Wait 0.15s → 반복
```

한 틱에 **반드시 하나의 분기만** 실행된다.

---

### 3-4. 블랙보드 변수 전체

#### 오브젝트 참조 (Inspector 설정)

| 변수명 | 타입 | 설명 |
|--------|------|------|
| `Self` | `GameObject` | 자기 자신 (이 봇) |
| `Boss` | `GameObject` | 보스 오브젝트 |
| `Ally` | `GameObject` | 다른 플레이어 봇 |

#### 설정 상수 (Inspector 조절 가능)

| 변수명 | 타입 | 기본값 | 단위 | 설명 |
|--------|------|:------:|:----:|------|
| `CloseThreshold` | `float` | 2.0 | m | 긴급 회피 발동 거리 |
| `OptimalMin` | `float` | 3.0 | m | 보스와 적정 최소 거리 |
| `OptimalMax` | `float` | 5.0 | m | 보스와 적정 최대 거리 |
| `MinAllyDist` | `float` | 2.5 | m | 아군 겹침 판정 거리 |
| `FleeDistance` | `float` | 4.0 | m | 도주 시 이동 거리 |
| `SpreadDistance` | `float` | 3.0 | m | 겹침 해소 시 이동 거리 |
| `FlankAngleOffset` | `float` | 110.0 | ° | 측면 공격 목표 각도 |
| `StrafeStep` | `float` | 30.0 | ° | 선회 1틱당 회전 각도 |
| `ReEvalInterval` | `float` | 0.15 | s | 재평가 간격 |

#### 런타임 변수 (노드가 매 틱 갱신)

| 변수명 | 타입 | 갱신 주체 | 범위 | 설명 |
|--------|------|----------|:----:|------|
| `BossDistance` | `float` | UpdateSituation | 0~ | 보스까지 거리 (m) |
| `AllyDistance` | `float` | UpdateSituation | 0~ | 아군까지 거리 (m) |
| `FlankAngle` | `float` | UpdateSituation | 0~180 | 보스 기준 나↔아군 사이각 (°) |
| `BossLookingAtMe` | `bool` | UpdateSituation | — | 보스 전방 dot > 0.5이면 true |
| `StrafeSign` | `float` | UpdateSituation | -1/+1 | 선회 방향 (+1 우 / -1 좌) |
| `TargetPosition` | `Vector3` | Calc~Action들 | — | 최종 이동 목표 좌표 |

> 총 변수 수: **18개** (오브젝트 3 + 상수 9 + 런타임 6)

---

### 3-5. Condition 노드 상세 (4개)

#### C1. IsBossTooClose

| 항목 | 내용 |
|------|------|
| Story | `[BossDistance] 가 [CloseThreshold] 보다 가까운지 확인` |
| Category | `Condition/Combat` |
| 베이스 | `Condition` |

| 블랙보드 변수 | 방향 | 타입 |
|:---:|:---:|------|
| `BossDistance` | 입력 | `float` |
| `CloseThreshold` | 입력 | `float` |

```
판정: BossDistance < CloseThreshold
  true  → 보스 2m 이내 → 긴급 회피 분기 진입
  false → 다음 Selector 자식으로 이동
```

---

#### C2. IsAllyTooClose

| 항목 | 내용 |
|------|------|
| Story | `[AllyDistance] 가 [MinAllyDist] 보다 가까운지 확인` |
| Category | `Condition/Combat` |

| 블랙보드 변수 | 방향 | 타입 |
|:---:|:---:|------|
| `AllyDistance` | 입력 | `float` |
| `MinAllyDist` | 입력 | `float` |

```
판정: AllyDistance < MinAllyDist
  true  → 아군 2.5m 이내 → 겹침 해소 분기 진입
  false → 다음으로
```

---

#### C3. IsBossTargetingAlly

| 항목 | 내용 |
|------|------|
| Story | `보스가 아군을 주시 중인지 확인 ([BossLookingAtMe] 가 false)` |
| Category | `Condition/Combat` |

| 블랙보드 변수 | 방향 | 타입 |
|:---:|:---:|------|
| `BossLookingAtMe` | 입력 | `bool` |

```
판정: BossLookingAtMe == false
  true  → 보스가 나를 안 봄 = 아군 주시 중 → 측면 공격 기회
  false → 보스가 나를 보고 있음 → 다음으로
```

---

#### C4. IsAtOptimalRange

| 항목 | 내용 |
|------|------|
| Story | `[BossDistance] 가 [OptimalMin] ~ [OptimalMax] 사이인지 확인` |
| Category | `Condition/Combat` |

| 블랙보드 변수 | 방향 | 타입 |
|:---:|:---:|------|
| `BossDistance` | 입력 | `float` |
| `OptimalMin` | 입력 | `float` |
| `OptimalMax` | 입력 | `float` |

```
판정: BossDistance >= OptimalMin && BossDistance <= OptimalMax
  true  → 적정 거리 (3~5m) → 선회 유지 분기
  false → 너무 멀음 → 기본 접근 분기로
```

---

### 3-6. Action 노드 상세 (7개)

#### A1. UpdateSituationAction

| 항목 | 내용 |
|------|------|
| Story | `[Self] 의 전투 상황을 분석하여 블랙보드를 갱신` |
| Category | `Action/Combat` |
| 반환 | 항상 `Success` (OnStart 즉시 완료) |

| 블랙보드 변수 | 방향 | 타입 |
|:---:|:---:|------|
| `Self` | 입력 | `GameObject` |
| `Boss` | 입력 | `GameObject` |
| `Ally` | 입력 | `GameObject` |
| `BossDistance` | 출력 | `float` |
| `AllyDistance` | 출력 | `float` |
| `FlankAngle` | 출력 | `float` |
| `BossLookingAtMe` | 출력 | `bool` |
| `StrafeSign` | 출력 | `float` |

**계산 로직:**

```
selfPos  = Self.transform.position
bossPos  = Boss.transform.position
allyPos  = Ally.transform.position

// ── 거리 계산 ──
BossDistance = Vector3.Distance(selfPos, bossPos)
AllyDistance = Vector3.Distance(selfPos, allyPos)

// ── 협공 각도 (보스 기준 나↔아군 사이각) ──
bossToMe   = (selfPos - bossPos).normalized
bossToAlly = (allyPos - bossPos).normalized
FlankAngle = Vector3.Angle(bossToMe, bossToAlly)   // 0~180°

         [Boss]
        ↗  ↑   ↖
  bossToAlly    bossToMe     ← FlankAngle = 이 사이각
      ↗            ↖
  [Ally]          [Self]

// ── 보스 시선 판정 ──
toBoss  = (bossPos - selfPos).normalized
bossDot = Vector3.Dot(Boss.transform.forward, toBoss)
BossLookingAtMe = (bossDot > 0.5f)
//   dot > 0.5  → 보스 정면 60° 이내 = 나를 보고 있음
//   dot ≤ 0.5  → 나를 안 보고 있음

// ── 선회 방향 결정 ──
cross = Vector3.Cross(bossToMe, bossToAlly)
StrafeSign = (cross.y >= 0f) ? +1f : -1f
//   +1 = 시계 방향 (우회전)
//   -1 = 반시계 방향 (좌회전)
//   → 아군과 자연스럽게 벌어지는 방향으로 선회
```

---

#### A2. CalcFleePositionAction

| 항목 | 내용 |
|------|------|
| Story | `[Self] 가 [Boss] 반대 방향으로 [FleeDistance] 만큼 도주할 위치를 [TargetPosition] 에 저장` |
| Category | `Action/Navigation` |
| 반환 | `Success` (유효 지점 발견) / `Failure` (NavMesh 없음) |
| 비고 | 기존 `GetFleePositionAction` 로직 재사용 가능 |

| 블랙보드 변수 | 방향 | 타입 |
|:---:|:---:|------|
| `Self` | 입력 | `GameObject` |
| `Boss` | 입력 | `GameObject` |
| `FleeDistance` | 입력 | `float` |
| `TargetPosition` | 출력 | `Vector3` |

**계산 로직:**

```
selfPos = Self.transform.position
bossPos = Boss.transform.position

// 12방향 균등 샘플링
bestPos      = Vector3.zero
bestBossDist = -1

for i = 0 ~ 11:
    angle     = i * 30°
    dir       = Quaternion.Euler(0, angle, 0) * Vector3.forward
    candidate = selfPos + dir * FleeDistance

    if NavMesh.SamplePosition(candidate, hit, 1.5m):
        bossDist = Distance(hit.position, bossPos)
        if bossDist > bestBossDist:
            bestBossDist = bossDist
            bestPos      = hit.position

TargetPosition = bestPos

            ② ①         
          ③       ⑫       각 번호 = 30° 간격 후보 지점
        ④    [Self]   ⑪    
          ⑤       ⑩          [Boss] ← 보스가 여기에 있으면
            ⑥ ⑨              ④~⑥ 근처가 최적 도주 지점
          ⑦   ⑧
```

---

#### A3. CalcSpreadPositionAction

| 항목 | 내용 |
|------|------|
| Story | `[Self] 가 [Ally] 로부터 벌어지면서 보스 거리를 유지하는 위치를 [TargetPosition] 에 저장` |
| Category | `Action/Navigation` |
| 반환 | `Success` / `Failure` |

| 블랙보드 변수 | 방향 | 타입 |
|:---:|:---:|------|
| `Self` | 입력 | `GameObject` |
| `Ally` | 입력 | `GameObject` |
| `Boss` | 입력 | `GameObject` |
| `SpreadDistance` | 입력 | `float` |
| `OptimalMin` | 입력 | `float` |
| `OptimalMax` | 입력 | `float` |
| `TargetPosition` | 출력 | `Vector3` |

**계산 로직:**

```
selfPos = Self.position
allyPos = Ally.position
bossPos = Boss.position

// ── 1단계: 아군 반대 방향 ──
awayFromAlly = (selfPos - allyPos).normalized

// ── 2단계: 보스 거리 보정 ──
toBoss      = (bossPos - selfPos).normalized
optimalMid  = (OptimalMin + OptimalMax) / 2
currentDist = Distance(selfPos, bossPos)

if currentDist < optimalMid:
    bossWeight = -0.3f   // 보스와 가까움 → 보스에서 멀어지는 방향 가산
else:
    bossWeight = +0.3f   // 보스와 멀음 → 보스 쪽으로 가산

// ── 3단계: 합성 방향 ──
dir       = (awayFromAlly + toBoss * bossWeight).normalized
candidate = selfPos + dir * SpreadDistance

NavMesh.SamplePosition(candidate, hit, 2.0m)
TargetPosition = hit.position

        [Boss]
          ↑ toBoss (가중치 ±0.3 반영)
          ↑
    [Ally]←──[Self]───→ awayFromAlly
                  ↘
                    → 합성 방향 (벌어지면서 보스 거리 유지)
```

---

#### A4. CalcFlankPositionAction

| 항목 | 내용 |
|------|------|
| Story | `[Self] 가 [Boss] 기준으로 [Ally] 반대편 [FlankAngleOffset]° 측면 위치를 [TargetPosition] 에 저장` |
| Category | `Action/Navigation` |
| 반환 | `Success` / `Failure` |

| 블랙보드 변수 | 방향 | 타입 |
|:---:|:---:|------|
| `Self` | 입력 | `GameObject` |
| `Boss` | 입력 | `GameObject` |
| `Ally` | 입력 | `GameObject` |
| `FlankAngleOffset` | 입력 | `float` |
| `OptimalMin` | 입력 | `float` |
| `OptimalMax` | 입력 | `float` |
| `TargetPosition` | 출력 | `Vector3` |

**계산 로직:**

```
bossPos = Boss.position
allyPos = Ally.position

// ── 1단계: 보스→아군 방향 ──
bossToAlly = (allyPos - bossPos).normalized

// ── 2단계: 반대편 측면 방향 계산 ──
// 아군 방향에서 FlankAngleOffset(110°) 만큼 회전
flankDir = Quaternion.Euler(0, FlankAngleOffset, 0) * bossToAlly

// ── 3단계: 적정 거리에 목표 지점 생성 ──
optimalMid = (OptimalMin + OptimalMax) / 2
candidate  = bossPos + flankDir * optimalMid

NavMesh.SamplePosition(candidate, hit, 2.0m)
TargetPosition = hit.position

                [Ally]
               ↗
         [Boss] ─────── bossToAlly 방향 (0°)
               ↘
                 ↘  110° 회전
                   ↘
                 [목표 지점] ← Self가 여기로 이동

결과: 보스 기준 아군 반대편 측면에 배치 → 자연스러운 협공 구도
```

---

#### A5. CalcStrafePositionAction

| 항목 | 내용 |
|------|------|
| Story | `[Self] 가 [Boss] 주변을 [StrafeSign] 방향으로 [StrafeStep]° 선회하는 위치를 [TargetPosition] 에 저장` |
| Category | `Action/Navigation` |
| 반환 | `Success` / `Failure` |

| 블랙보드 변수 | 방향 | 타입 |
|:---:|:---:|------|
| `Self` | 입력 | `GameObject` |
| `Boss` | 입력 | `GameObject` |
| `StrafeSign` | 입력 | `float` |
| `StrafeStep` | 입력 | `float` |
| `OptimalMin` | 입력 | `float` |
| `OptimalMax` | 입력 | `float` |
| `TargetPosition` | 출력 | `Vector3` |

**계산 로직:**

```
bossPos = Boss.position
selfPos = Self.position

// ── 1단계: 현재 보스→나 방향 ──
bossToMe = (selfPos - bossPos).normalized

// ── 2단계: StrafeSign 방향으로 StrafeStep° 회전 ──
rotAngle   = StrafeSign * StrafeStep   // +30° 또는 -30°
rotatedDir = Quaternion.Euler(0, rotAngle, 0) * bossToMe

// ── 3단계: 적정 거리 유지 ──
optimalMid = (OptimalMin + OptimalMax) / 2
candidate  = bossPos + rotatedDir * optimalMid

NavMesh.SamplePosition(candidate, hit, 2.0m)
TargetPosition = hit.position

             [Boss]
            ↙  ↑  ↘
     이전 위치   ↑   다음 위치
       [Self] → → → [목표]     (StrafeSign = +1, 시계 방향 30°)
       
매 0.15초마다 30°씩 회전 → 보스 주변을 원형 선회
실제 이동 속도는 NavMeshAgent.speed로 제한
```

---

#### A6. CalcApproachPositionAction

| 항목 | 내용 |
|------|------|
| Story | `[Self] 가 [Boss] 방향으로 적정 거리까지 접근하는 위치를 [TargetPosition] 에 저장` |
| Category | `Action/Navigation` |
| 반환 | `Success` / `Failure` |

| 블랙보드 변수 | 방향 | 타입 |
|:---:|:---:|------|
| `Self` | 입력 | `GameObject` |
| `Boss` | 입력 | `GameObject` |
| `OptimalMax` | 입력 | `float` |
| `TargetPosition` | 출력 | `Vector3` |

**계산 로직:**

```
bossPos = Boss.position
selfPos = Self.position

// 보스 방향으로 OptimalMax 지점을 목표로
toBoss    = (bossPos - selfPos).normalized
candidate = bossPos - toBoss * OptimalMax

NavMesh.SamplePosition(candidate, hit, 2.0m)
TargetPosition = hit.position

    [Self] ─────────→ [목표: 5m 지점] ──── [Boss]
    (현재 8m)          (OptimalMax)        (0m)
```

---

#### A7. SetNavDestinationAction

| 항목 | 내용 |
|------|------|
| Story | `[Self] 의 NavMeshAgent 목적지를 [TargetPosition] 으로 설정` |
| Category | `Action/Navigation` |
| 반환 | 항상 `Success` (즉시 완료, 이동은 NavMeshAgent가 비동기 처리) |

| 블랙보드 변수 | 방향 | 타입 |
|:---:|:---:|------|
| `Self` | 입력 | `GameObject` |
| `TargetPosition` | 입력 | `Vector3` |

**계산 로직:**

```
NavMeshAgent agent = Self.GetComponent<NavMeshAgent>()

if agent == null → return Failure

agent.SetDestination(TargetPosition)
return Success

// NavMeshAgent가 경로 계산 + 이동을 자동으로 처리
// 다음 틱에서 새 TargetPosition이 들어오면 목적지 자동 교체
```

---

### 3-7. 사용하는 내장 노드

| 노드 | 타입 | 설정 | 역할 |
|------|------|------|------|
| `Start` | Entry | — | 그래프 진입점 |
| `Repeat` | Decorator | Mode: Forever | 전체 루프 |
| `Sequence` (루트) | Composite | 자식 4개 | ①→②→③→④ 순서 실행 |
| `Sequence` (분기별) | Composite | 자식 2개 | Condition + Action 쌍 |
| `Selector` | Composite | 자식 5개 | 우선순위 분기 (첫 Success에서 중단) |
| `Wait` | Action | Duration: BB `ReEvalInterval` | 재평가 전 대기 |

---

### 3-8. 생성할 노드 체크리스트

| # | 종류 | 노드명 | 에디터 생성 | 코드 작성 |
|---|------|--------|:---:|:---:|
| C1 | Condition | `IsBossTooClose` | 유저 | Claude |
| C2 | Condition | `IsAllyTooClose` | 유저 | Claude |
| C3 | Condition | `IsBossTargetingAlly` | 유저 | Claude |
| C4 | Condition | `IsAtOptimalRange` | 유저 | Claude |
| A1 | Action | `UpdateSituationAction` | 유저 | Claude |
| A2 | Action | `CalcFleePositionAction` | 기존 참고 | Claude |
| A3 | Action | `CalcSpreadPositionAction` | 유저 | Claude |
| A4 | Action | `CalcFlankPositionAction` | 유저 | Claude |
| A5 | Action | `CalcStrafePositionAction` | 유저 | Claude |
| A6 | Action | `CalcApproachPositionAction` | 유저 | Claude |
| A7 | Action | `SetNavDestinationAction` | 유저 | Claude |
| — | 내장 | Start, Repeat, Sequence, Selector, Wait | 유저 | 불필요 |

---

### 3-9. 씬 구성 — 2인 교차 참조

동일한 그래프 에셋(DoubleMove.asset)을 사용하고, **Ally 참조만 교차 설정**:

```
PlayerBot_A (GameObject)                PlayerBot_B (GameObject)
├── NavMeshAgent                        ├── NavMeshAgent
├── BehaviorGraphAgent                  ├── BehaviorGraphAgent
│   └── Graph: DoubleMove.asset         │   └── Graph: DoubleMove.asset (동일)
└── DoubleMoveBlackboardInit            └── DoubleMoveBlackboardInit
    ├── Self: PlayerBot_A               │   ├── Self: PlayerBot_B
    ├── Boss: [Boss]                    │   ├── Boss: [Boss]
    ├── Ally: PlayerBot_B  ◄──────────► │   ├── Ally: PlayerBot_A  ← 교차
    ├── CloseThreshold: 2.0             │   ├── CloseThreshold: 2.0
    ├── OptimalMin: 3.0                 │   ├── OptimalMin: 3.0
    ├── OptimalMax: 5.0                 │   ├── OptimalMax: 5.0
    ├── MinAllyDist: 2.5                │   ├── MinAllyDist: 2.5
    ├── FleeDistance: 4.0               │   ├── FleeDistance: 4.0
    ├── SpreadDistance: 3.0             │   ├── SpreadDistance: 3.0
    ├── FlankAngleOffset: 110.0         │   ├── FlankAngleOffset: 110.0
    ├── StrafeStep: 30.0                │   ├── StrafeStep: 30.0
    └── ReEvalInterval: 0.15            │   └── ReEvalInterval: 0.15
```

### 3-10. 두 플레이어 동시 움직임 예시

```
시작 상태:                         자연스러운 결과:

    [P1] [P2]                           [P1]
      ↓  ↓                            ↗
    [Boss]                       [Boss]
                                      ↖
                                       [P2]

1. 시작 시 뭉쳐있음 → 겹침 해소(2순위) 발동 → 자연스럽게 벌어짐
2. 벌어진 뒤 보스가 한쪽을 보면 → 반대쪽은 측면 공격(3순위) 진입
3. 적정 거리 도달 → 선회(4순위)로 보스 주변을 원형 선회
4. 보스가 갑자기 돌진 → 해당 플레이어만 긴급 회피(1순위) 발동
5. 결과: 양쪽에서 보스를 끼고 도는 협공 패턴 자연 발생
```

---

## 4. 보스 ↔ 플레이어 봇 관계

```
                    ┌──────────────┐
                    │   학습 환경    │
                    │              │
  ┌─────────┐      │  ┌────────┐  │
  │ PPO 학습  │ ←───│──│BossAgent│  │  보스: ML-Agents로 학습
  │ 알고리즘   │      │  └────────┘  │
  └─────────┘      │      ↕       │
                    │  ┌────────┐  │
                    │  │PlayerBot│  │  플레이어: Behavior Graph로 규칙 기반 행동
                    │  │(봇)    │  │
                    │  └────────┘  │
                    └──────────────┘

학습 흐름:
1. 플레이어 봇이 Behavior Graph에 따라 행동 (순찰/도주/협공)
2. 보스가 플레이어 봇을 관측하고 행동 선택 (PPO)
3. 접촉/시간 등 보상 수신
4. 반복 → 보스 모델 개선

추론 (게임 실행):
1. 보스: 학습된 .onnx 모델로 추론 실행
2. 플레이어: 실제 사람이 조작 (봇 대신)
```

---

## 5. 참고 사항

### 커스텀 노드 생성 방법

Unity 에디터에서:
1. Behavior Graph 에디터 열기
2. 우클릭 → `Create Node` → `New Action` / `New Condition`
3. 이름과 Story 입력 → C# 파일 자동 생성
4. 생성된 파일에서 블랙보드 변수 선언 및 로직 구현

### ML-Agents 학습 실행

```bash
# 가상 환경 활성화 (Python 3.10+)
# Unity 에디터에서 Play 누른 상태로:
mlagents-learn BasicMove_config.yaml --run-id=학습이름

# 이어서 학습:
mlagents-learn BasicMove_config.yaml --run-id=학습이름 --resume

# TensorBoard로 학습 경과 확인:
tensorboard --logdir results
```

### 학습 모델 적용

1. `results/학습이름/모델이름.onnx` 파일을 프로젝트에 복사
2. BossAgent 오브젝트의 `BehaviorParameters` → `Model` 필드에 할당
3. `Behavior Type`을 `Inference Only`로 변경

---

## 6. 전투 봇 AI — 스킬 + 포지셔닝 통합

### 6-1. 개요

기존 DoubleMove(2인 협동 이동) 위에 **스킬 자동 시전**을 통합하는 전투 봇 시스템.
3가지 독립 시스템이 협력하여 동작한다:

```
[BehaviorGraph + DoubleMove.asset]  ← 포지셔닝 (기존 그래프 재사용)
         ↓ NavMeshAgent.destination
[LookAtBossAction]                   ← 보스 방향 회전 (그래프 액션)
         ↓ transform.rotation
[SkillManager auto-cast]             ← 스킬 시전 (기존 코드)
         ↓ transform.forward = CastDirection
```

- BehaviorGraph: DoubleMove.asset 그대로 사용, Blackboard 값만 다르게 주입
- 그래프 내부 수정: LookAtBossAction 노드를 각 분기 끝에 추가
- SkillManager: 코드 수정 없음, 슬롯만 SkillDistributor가 배치

### 6-2. 신규 컴포넌트

#### PlayerBotCombatInit.cs

| 항목 | 내용 |
|------|------|
| 위치 | `Assets/Scripts/AI/Player/Combat/` |
| 역할 | 전투 봇 Blackboard 전체 주입 + BehaviorGraphAgent 시작 제어 |
| 실행 | Awake: 에이전트 비활성화 / Start: Blackboard 주입 → 에이전트 활성화 |

**주입하는 Blackboard 변수:**

| 변수 | 타입 | 용도 |
|------|------|------|
| Boss | GameObject | 위치 계산 기준 |
| Agent | NavMeshAgent | SetNavDestination |
| Ally | GameObject | 협동 판단 |
| Self | GameObject | 자기 위치 참조 |
| DangerRange ~ MinSpacing | float × 8 | 포지셔닝 파라미터 |

#### SkillDistributor.cs

| 항목 | 내용 |
|------|------|
| 위치 | `Assets/Scripts/Skill/Core/` |
| 역할 | P1/P2 플레이어에게 스킬 슬롯 분배 |
| 범위 | 플레이어 전용 (보스는 SkillManager 일반화 후 별도) |

#### LookAtBossAction.cs

| 항목 | 내용 |
|------|------|
| 위치 | `Assets/Scripts/AI/Player/DoubleMove/` |
| 역할 | 이동 후 보스 방향으로 Slerp 회전 |
| 배치 | 5개 분기 각각의 SetNavDestination 뒤 |

### 6-3. P1/P2 Blackboard 값

| 변수 | P1 근거리 | P2 원거리 |
|------|:---------:|:---------:|
| DangerRange | 8.0 | 15.0 |
| OptimalMin | 10.0 | 30.0 |
| OptimalMax | 16.0 | 40.0 |
| FleeDistance | 6.0 | 10.0 |
| FlankRadius | 13.0 | 35.0 |
| StrafeRadius | 13.0 | 35.0 |
| StrafeAngleStep | 25.0 | 15.0 |
| MinSpacing | 5.0 | 8.0 |

### 6-4. P1/P2 스킬 슬롯 (SkillDistributor 배치)

**P1 근거리:**

| 슬롯 | 스킬 | SO Range | 사유 |
|------|------|:--------:|------|
| 0 | CollapseRoar | 27 | AOE + DefDown 최우선 |
| 1 | FortressArmor | 24 | 실드 획득 생존 |
| 2 | ExecutionSpike | 24 | 저체력 마무리 |

**P2 원거리:**

| 슬롯 | 스킬 | SO Range | 사유 |
|------|------|:--------:|------|
| 0 | SealChain | 66 | 경직+침묵 방해 최우선 |
| 1 | ErosionField | 42 | 지속 피해 견제 |
| 2 | PiercingShot | 66 | 고피해 저격 |

### 6-5. 실행 순서

```
SkillBootstrap.Awake()       → RuntimeStep 바인딩
PlayerBotCombatInit.Awake()  → BehaviorGraphAgent 비활성화
──── 모든 Awake 완료 ────
SkillDistributor.Start()     → P1/P2 스킬 슬롯 분배
PlayerBotCombatInit.Start()  → Blackboard 주입 + 에이전트 활성화
```

### 6-6. 전투 봇 오브젝트 컴포넌트

```
PlayerBot (전투용)
├── NavMeshAgent
├── BehaviorGraphAgent          ← Graph: DoubleMove.asset
├── PlayerController
├── StatManager
├── StateManager
├── SkillExecutor
├── SkillManager                ← SkillDistributor가 슬롯 배치
└── PlayerBotCombatInit         ← Blackboard 값 주입
    ├── Ally: [상대 봇]
    ├── DangerRange ~ MinSpacing: P1/P2별 값
    └── GameManager: [GameManager 참조]
```

**주의:**
- `PlayerBotBlackboardInit`은 전투 봇에 **붙이지 않음** (CombatInit이 대체)
- `FaceTarget`은 **생성하지 않음** (LookAtBossAction이 대체)
- 단일 보스(Chapter 1) 전제

### 6-7. DoubleMove 그래프 수정 (에디터 수동)

각 분기의 SetNavDestination 뒤에 LookAtBossAction 추가:

```
ConditionalGuard → Sequence
                     ├── Calc~Position
                     ├── SetNavDestination
                     └── LookAtBossAction  ← 추가 (5개 분기 모두)
```

---

## 7. 보스 관측값 시스템

### 7-1. 개요

Phase 3+ ML-Agent 학습과 규칙 기반 보스 행동 선택을 위한 3개 시스템:

```
게임 상태 (위치, HP, 스킬, 이벤트)
    │
    ├── BossObservationCollector → VectorSensor (ML-Agent 학습용, 34개)
    │
    └── PlayerBiasTracker (15~20초 행동 로그)
            │
            └── BossActionWeightCalculator → weighted-random 행동 선택
```

### 7-2. Phase별 관측값 (34개, P1/P2 고정 정렬)

Phase 3+는 Phase 2(active/secondary 동적 정렬)와 의도적으로 단절됨.
Phase 2→3 initialize-from 사용하지 않음.

| Phase | # | 관측값 | 정규화 | 비고 |
|:---:|:---:|--------|:---:|------|
| 1 | 0-1 | dirToP1.x/z | -1~1 | P1 방향 |
| 1 | 2 | distToP1 | 0~1 | P1 거리 |
| 1 | 3-4 | forward.x/z | -1~1 | 보스 전방 |
| 1 | 5 | dotForwardP1 | -1~1 | 전방↔P1 정렬도 |
| 2 | 6-7 | dirToP2.x/z | -1~1 | P2 방향 |
| 2 | 8 | distToP2 | 0~1 | P2 거리 |
| 2 | 9 | distP1P2 | 0~1 | P1↔P2 거리 |
| 2 | 10 | dotForwardP2 | -1~1 | 전방↔P2 정렬도 |
| 3 | 11-13 | bossHp/p1Hp/p2Hp | 0~1 | HP 비율 3종 |
| 3 | 14-16 | skill0~2Cooldown | 0~1 | 보스 스킬 쿨다운 비율 |
| 3 | 17 | bossPhase | 0~1 | 보스 페이즈 (정규화) |
| 3 | 18 | unlockedSlotCount | 0~1 | 해금된 스킬 슬롯 수 (÷ maxSlots) |
| 4 | 19 | recentParryCount | 0~1 | 패링 시스템 미구현 → 0 고정 |
| 4 | 20 | recentBurstDamage | 0~1 | 최근 1초 수신 피해량 |
| 4 | 21-22 | p1/p2AvgMoveSpeed | 0~1 | P1/P2 평균 이동속도 |
| 4 | 23-24 | p1/p2IsCasting | 0/1 | P1/P2 캐스팅 여부 |
| 5 | 25-27 | lastSkill[0~2] | 0~1 | 직전 3회 스킬 슬롯 인덱스 |
| 5 | 28-30 | skillHitRate[0~2] | 0~1 | 스킬별 명중률 |
| 5 | 31-33 | skillUseCount[0~2] | 0~1 | 스킬별 사용 비율 |

Space Size: Phase 3=19, Phase 4=25, Phase 5=34

### 7-3. 플레이어 편향 점수 (PlayerBiasTracker)

| # | 편향 | 상승 기준 | 하락 기준 | 비고 |
|:---:|------|----------|----------|------|
| 0 | 근접 선호 | 평균 거리 짧음 +0.02/+0.05 | 거리 길면 -0.02 | |
| 1 | 원거리 유지 | 원거리 체류 높음 +0.02/+0.05 | 근접 시 -0.02 | |
| 2 | 공격 집중 | 공격 비율 높음 +0.02/+0.05 | 회피 위주면 -0.02 | |
| 3 | 생존 우선 | 이탈/회복 많음 +0.02/+0.05 | 공격 지속 시 -0.02 | |
| 4 | 패링 의존 | — | — | 미구현, 0 고정 |
| 5 | 로프 기동 | — | — | 미구현, 0 고정 |
| 6 | 스킬 중심 | 스킬 비중 높음 +0.02/+0.05 | 기본 공격 위주면 -0.02 | |
| 7 | 팀 밀착 | 팀원 가까움 +0.02/+0.05 | 멀어지면 -0.02 | |
| 8 | 팀 분산 | 팀원 멀음 +0.02/+0.05 | 가까워지면 -0.02 | |

시간축: 15~20초 장기 로그 + 0.5초 재계산 + 이벤트 트리거(즉시 반영)

### 7-4. 보스 행동 가중치 (BossActionWeightCalculator)

| # | 행동군 | 계산식 |
|:---:|--------|--------|
| 0 | 근접 압박 | 1.0 + 근접선호×0.6 + 팀밀착×0.3 - 원거리유지×0.4 |
| 1 | 원거리 견제 | 1.0 + 원거리유지×0.6 + 팀분산×0.3 - 근접선호×0.4 |
| 2 | 패링 견제 | 1.0 + 패링의존×0.7 |
| 3 | 로프 대응 | 1.0 + 로프기동×0.7 |
| 4 | 폭딜 대응 | 1.0 + 공격집중×0.5 |
| 5 | 생존 압박 | 1.0 + 생존우선×0.6 |
| 6 | 분산 대응 | 1.0 + 팀분산×0.8 |
| 7 | 밀집 대응 | 1.0 + 팀밀착×0.8 |
| 8 | 적응형 변칙 | 1.0 (게이트 없음) |

선택 흐름:
1. 비적합 게이트: 관련 편향 < 0.05 → 가중치 0
2. Legal mask: 미구현/페이즈 잠금 행동 차단
3. 반복 패널티: 직전 동일 -0.2, 3회 중 2회 -0.35, 직전 2회 동일 -0.15
4. 바닥값: 적합 행동 최소 0.1
5. Fallback: Σ=0 → legal 행동만 균등 분배
6. Weighted-random: P(i) = weight_i / Σweights

### 7-5. 적중 기록 흐름 (SkillExecutor)

```
SkillExecutor.Execute()
  ├── RecordAttempt(skillId)         ← 시도 1회 기록
  ├── ctx.HitRecorded = false
  ├── ctx.OnHitRecorded = callback   ← dedupe 콜백 주입
  └── RuntimeStep.Invoke(ctx)
        ├── ApplyInArea: anyHit → OnHitRecorded()
        ├── DealDirectionalHit: anyHit → OnHitRecorded()
        └── LaunchProjectile → SkillProjectile.ApplyHit → OnHitRecorded()
                                (관통 투사체도 시전당 1회만 기록)
```

### 7-6. 컴포넌트 구성 (보스 GameObject)

```
Boss
├── BossController
├── StatManager
├── StateManager
├── SkillExecutor
├── NavMeshAgent
├── BossObservationCollector      ← 신규
│   ├── _p1/_p2: [플레이어 참조]
│   ├── _bossSkills[3]: [스킬 SO]
│   └── _skillExecutor: [자동 GetComponent]
├── PlayerBiasTracker             ← 신규
│   └── _collector: [자동 GetComponent]
└── BossActionWeightCalculator    ← 신규
    ├── _biasTracker: [자동 GetComponent]
    └── _bossController: [자동 GetComponent]
```

---

## 8. Phase 3 — SkillIntroAgent (원거리 스킬 대응)

### 8-1. 개요

Phase 2(DualTarget)에서 학습한 이동 능력 위에 **스킬 시전** 행동을 추가.
원거리 스킬을 사용하는 플레이어를 상대로 보스가 이동 + 스킬 조합을 학습한다.

네트워크 구조(24 obs, 2 Branch)를 유지한 채 이동 프리트레인 → 스킬 학습 2단계로 진행.
DualTarget(11 obs, 1 Branch)과 구조가 달라 직접 initialize-from 불가 → SkillIntro 구조 내에서 이동 전용 프리트레인.

**더블 터치 시스템:** DualTargetAgent의 검증된 교대 접근 로직을 통합.
P1 접촉 → P2 추적, P2 접촉 → P1 추적, 양쪽 접촉 → 에피소드 성공.
한 타겟에 붙어있는 캠핑 행동을 방지하고 두 플레이어를 번갈아 접근하는 행동을 학습.

### 8-2. 파일 구성

| 파일 | 역할 |
|------|------|
| `SkillIntroAgent.cs` | Phase 3 ML-Agent (24 obs, 2 Branch, 더블터치) |
| `TrainingSkillManager.cs` | 점진적 스킬 해금 관리 (_initialUnlockCount로 시작 슬롯 지정) |
| `SkillPoolSO.cs` | 스킬 풀 SO (Inspector 배치) |
| `SkillIntro_Move_config.yaml` | 이동 프리트레인 config (0슬롯, B1 전체마스크) |
| `SkillIntro_config.yaml` | 스킬 학습 config (initialize-from: SkillIntro_Move) |

### 8-3. 관측값 (24개 — Phase3Size 22 + touch 2)

BossObservationCollector.CollectUpToPhase3() 22개 + 더블터치 상태 2개.
Phase 1(#0-5) + Phase 2(#6-10) + Phase 3(#11-21) + Touch(#22-23) 누적.

| # | 관측값 | 설명 |
|:---:|--------|------|
| 0-5 | P1 방향/거리/전방/정렬도 | Phase 1 |
| 6-10 | P2 방향/거리/P1↔P2거리/정렬도 | Phase 2 |
| 11-13 | bossHp/p1Hp/p2Hp | HP 비율 |
| 14-16 | skill0~2Cooldown | 스킬 쿨다운 비율 |
| 17 | bossPhase | 페이즈 정규화 |
| 18 | unlockedSlotCount | 해금 슬롯 수 / maxSlots |
| 19-21 | skill0~2Range | 스킬 사거리 (Clamp01, maxDistance 정규화) |
| 22 | p1Touched | P1 접촉 여부 (0/1) |
| 23 | p2Touched | P2 접촉 여부 (0/1) |

BehaviorParameters: `Vector Observation Size: 24`

### 8-4. 행동 (2 Branch)

| Branch | Size | 값 | 행동 |
|:---:|:---:|:---:|------|
| B0 (이동) | 4 | 0 | 대기 |
| | | 1 | 전진 (`transform.forward * moveSpeed * dt`) |
| | | 2 | 좌회전 (`Rotate(0, -rotSpeed * dt, 0)`) |
| | | 3 | 우회전 (`Rotate(0, +rotSpeed * dt, 0)`) |
| B1 (스킬) | 4 | 0 | 없음 |
| | | 1 | 슬롯 0 시전 |
| | | 2 | 슬롯 1 시전 |
| | | 3 | 슬롯 2 시전 |

BehaviorParameters: `Discrete Branches: 2, Branch 0 Size: 4, Branch 1 Size: 4`

**Action Masking:** 미해금 슬롯 + 쿨다운 중 슬롯 → B1 해당 action disabled

### 8-5. 보상

| 조건 | 보상 | 설명 |
|------|:---:|------|
| 매 스텝 | -0.001 | 시간 압박 |
| **P1/P2 터치** | +0.2 | 근접 반경(_proximityRadius=5) 진입 시 |
| **빠른 더블터치** | +0.3 | 양쪽 터치 간격 ≤ _doubleTouchWindow(3초) |
| **양쪽 터치 완료** | EndEpisode | _touchEndEnabled=true 시 성공 종료 |
| 스킬 시전 (범위 내) | +0.05 | 시전 자체 소보상 |
| 범위 밖 시전 | -0.1 | TargetType.Self 제외 |
| HP 감소 | delta × 0.5 | 주 보상 (P1+P2 HP% 추적) |
| Shield 감소 | delta × 0.3 | 보조 (shieldMax 정규화) |
| 적중 (HitCount) | +0.2 / hit | 보조 (TotalHitCount delta) |
| 타겟 접근 | delta × 0.3 | **ActiveTarget 기준** (터치 안 한 쪽) |
| 타겟 정렬 | +0.003 | dot > 0.7 시 (ActiveTarget 기준) |
| 정지 | -0.005 | 위치 변화 < 0.05 |
| 벽 충돌 진입 | -_wWallHitPenalty (0.05) | Inspector 조정 가능 |
| 벽 충돌 유지 | -_wWallStayPenalty × dt (0.01) | Inspector 조정 가능 |
| 맵 이탈 | -1.0 | Y < -5 |
| 시간 종료 (터치 0개) | -0.5 (_noTouchPenalty) | 60초 초과, 아무도 못 건듦 |
| 시간 종료 (터치 1개) | -0.2 (_partialTouchPenalty) | 60초 초과, 한 쪽만 건듦 |

### 8-6. 점진적 스킬 해금 (TrainingSkillManager)

```
에피소드 시작 → _initialUnlockCount만큼 해금 (Inspector에서 0~3 설정)
  └── _unlockInterval초 후 → +1 해금
       └── _unlockInterval초 후 → +1 해금 (최대 3)
```

- `_initialUnlockCount = 0`: 이동 프리트레인 (B1 전체마스크, 스킬 없음)
- `_initialUnlockCount = 1`: 기본값 (기존 동작, 1개로 시작)
- `_initialUnlockCount = 3`: 풀 스킬 고정 (점진 해금 없음)

SkillPoolSO에서 순서대로 스킬을 꺼내 SkillManager.SetSlot()으로 배치.
BossObservationCollector에 SetUnlockedSlotCount() + SetBossSkill()로 동기화.

### 8-7. BossController 학습 모드

```
BossController.TrainingMode = true
  ├── NavMeshAgent.enabled = false (컴포넌트 자체 비활성)
  ├── HandleActions() 스킵 (레거시 이펙트 공격 비활성)
  ├── HandlePhase() 유지 (페이즈 전환 관측 필요)
  ├── StatManager.SetCasting(false) + EndParryWindow()
  └── StateManager.ForceReset()
```

**중요:** NavMeshAgent는 `enabled = false`로 완전 비활성해야 함.
`updatePosition = false`만 하면 여전히 transform.position 직접 변경을 간섭함.

### 8-8. 에피소드 흐름

```
OnEpisodeBegin()
  ├── CleanupPreviousEpisode()
  │     ├── ProjectilePool.ReturnAll()  — 이전 에피소드 투사체 정리
  │     └── PersistentAreaPool.ReturnAll() — 이전 에피소드 장판 정리
  ├── SpawnObjects()
  │     ├── 보스 → _bossSpawnPoint 위치 리셋
  │     └── P1/P2 → 랜덤 스폰 (NavMeshAgent Warp)
  └── ResetEpisodeState()
        ├── StatManager.SetCasting(false) + EndParryWindow()
        ├── StateManager.ForceReset()
        ├── SkillExecutor.ResetAll() — 쿨다운+통계 전체 초기화
        ├── TrainingSkillManager.ResetForEpisode() → _initialUnlockCount만큼 해금
        └── HP/Shield/HitCount 추적 변수 초기화

매 스텝:
  TrainingSkillManager.Tick() → 해금 시간 확인
  OnActionReceived()
    ├── B0: 이동 (전진/좌회전/우회전)
    ├── NotifyMovementInput(moveAction==1)
    ├── B1: 스킬 시전 (Action Masking + Range 체크, ActiveTarget 기준)
    ├── ApplyStepRewards()
    │     ├── HP/Shield/HitCount 3중 보상
    │     ├── CheckProximityTouch() — P1/P2 근접 터치 판정
    │     └── ActiveTarget 기준 진행/정렬 보상
    └── CheckTermination()

종료 조건:
  ├── 더블 터치 (P1+P2 모두 접촉) → 성공 종료 (+빠른 보너스)
  ├── 맵 이탈 (Y < -5) → -1.0, EndEpisode()
  ├── 시간 초과 (60초, 터치 0개) → -0.5, EndEpisode()
  ├── 시간 초과 (60초, 터치 1개) → -0.2, EndEpisode()
  └── MaxStep 도달 → 자동 종료
```

### 8-9. 학습 파이프라인

```
① 이동 프리트레인 (SkillIntro_Move_config.yaml)
   Inspector: _initialUnlockCount = 0
   결과: 22obs/2branch 구조에서 이동만 학습 (B1 전체마스크)

② 스킬 학습 (SkillIntro_config.yaml, initialize-from: SkillIntro_Move)
   Inspector: _initialUnlockCount = 1, _unlockInterval = 15
   결과: 이동 가중치 유지 + 스킬 시전 학습
```

**학습 명령:**
```bash
# Step 1: 이동 프리트레인
mlagents-learn SkillIntro_Move_config.yaml --run-id=SkillIntro_Move

# Step 2: 스킬 학습 (이동 체크포인트에서 이어받기)
mlagents-learn SkillIntro_config.yaml --run-id=SkillIntro --initialize-from=SkillIntro_Move
```

**인스펙터 튜닝 시나리오:**

| 시나리오 | _initialUnlockCount | _unlockInterval | 목적 |
|:---:|:---:|:---:|------|
| 이동 전용 | 0 | — | 프리트레인 |
| 1스킬 고정 | 1 | 999 | 단일 스킬 집중 |
| 3스킬 고정 | 3 | 999 | 풀 스킬 즉시 |
| 점진 해금 | 1 | 15 | 실전 (기본값) |

### 8-10. 게임 오브젝트 구성

```
Boss (학습 환경)
├── BossController          ← TrainingMode = true (Inspector)
├── StatManager
├── StateManager
├── SkillExecutor
├── SkillManager            ← AutoCast = false, RoundRobin = true
├── NavMeshAgent            ← enabled = false (학습 모드 시 자동)
├── BossObservationCollector
├── SkillIntroAgent         ← Behavior Name: SkillIntro
│   ├── _bossSpawnPoint
│   ├── _p1Object / _p2Object
│   └── _playerSpawnPoints[]
└── TrainingSkillManager
    ├── _skillPool: [SkillPoolSO 에셋]
    ├── _initialUnlockCount: 0 (이동) / 1 (스킬, 기본값)
    └── _unlockInterval: 15
```

### 8-11. 휴리스틱

| 키 | 행동 |
|:---:|------|
| W | 전진 (B0=1) |
| A | 좌회전 (B0=2) |
| D | 우회전 (B0=3) |
| 1 | 슬롯 0 시전 (B1=1) |
| 2 | 슬롯 1 시전 (B1=2) |
| 3 | 슬롯 2 시전 (B1=3) |
