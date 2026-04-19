# 스크립트 변경 이력

> 원본에서 변경된 스크립트들을 기록한다.
> 스크립트가 변경될 때마다 이 파일을 반드시 업데이트한다.

---

## 스킬 범위 표시 가시성 강화 + 자동 시전 거리 40m 확장 (수정)
**경로:** `Assets/Scripts/Skill/Core/SkillRangeDisplay.cs`, `Assets/ScriptableObjects/Skills/*.asset` (23개 전체)
**변경일:** 2026-04-18

### 수정
- **SkillRangeDisplay** — 가시성 대폭 강화
  - Y 높이 0.05→0.15, 두께 0.02→0.15, Line 폭 0.6→1.0
  - 알파값 강화 (HIT 0.85, MISS 0.7, Projectile 0.8)
  - 지속시간 0.8s→1.5s
- **전체 스킬 SO Range** — 2.2~11m → 40m 일괄 변경 (자동 시전 거리 확장)

---

## 스킬 범위 시각 표시 + 디버그 로그 추가 (신규/수정)
**경로:** `Assets/Scripts/Skill/Core/SkillRangeDisplay.cs` (신규), `Assets/Scripts/Skill/Core/SkillComponents.cs`, `Assets/Scripts/Skill/Core/SkillExecutor.cs`, `Assets/Scripts/Skill/Core/SkillManager.cs`, `Assets/Scripts/Stats/StatManager.cs`
**변경일:** 2026-04-18

### 신규
- **SkillRangeDisplay** — 스킬 범위 시각 표시 싱글톤 (프리팹 기반, URP 호환)
  - 런타임 셰이더 생성 → 프리팹 풀링 방식으로 변경 (PersistentAreaPool 패턴)
  - `MaterialPropertyBlock`으로 색상 제어 — Material 인스턴스 누수 없음
  - Inspector에 `_indicatorPrefab` 슬롯 — URP 투명 Material 적용된 Cylinder 프리팹 드래그
  - `_logRange` 토글 — 범위 표시 시 콘솔 로그 출력
  - `DealDirectionalHit` → 주황색 콘 (HIT/MISS 색상 구분)
  - `ApplyInArea` → 주황색 원형 (HIT/MISS 색상 구분)
  - `LaunchProjectile` → 파란색 직선 (발사 경로)
  - Inspector `Show Range` 해제로 비활성화 가능
### 수정
- **SkillExecutor** — `_logExecution` 토글 추가. 스킬 실행 시 시전자/대상/HP/쿨타임/실행 로그 출력
- **SkillManager** — `_logAutoCast` 토글 추가 + CanCast 실패 사유 경고 로그
- **StatManager** — `_logCombat` 토글 + Inspector 실시간 모니터 (HP/Shield/배율/상태이상 표시)
- **SkillComponents** — DealDirectionalHit/ApplyInArea/LaunchProjectile에 SkillRangeDisplay 호출 추가

---

## 스킬 시스템 버그 수정 2차 — CrushingBarrage / 조건형 쿨타임 / SkillArea HitLanded (수정)
**경로:** `Assets/Scripts/Skill/Core/SkillLibrary.cs`, `Assets/Scripts/Skill/Core/SkillDefinition.cs`, `Assets/Scripts/Skill/Core/SkillExecutor.cs`, `Assets/Scripts/Skill/Core/SkillManager.cs`, `Assets/Scripts/Skill/Core/SkillBinder.cs`, `Assets/Scripts/Skill/Area/SkillArea.cs`
**변경일:** 2026-04-17

### 수정
- **CrushingBarrage (플레이어/보스)** — `DealMultiHitDamage` 가 `DealDirectionalHit` MISS 시에도 무조건 실행
  - 수정 전: MISS → 멀티히트 + 광역 재시도 + 광역 멀티히트 = 이중 데미지
  - 수정 후: 멀티히트를 `TriggerOnHit(onHit:)` 내부로 이동
- **OverchargeMode / SurvivalPulse (플레이어/보스)** — 조건 미충족 시에도 쿨타임 소모
  - `SkillDefinition.RuntimeCondition` 필드 추가 (실행 전 조건, null = 항상 실행)
  - `SkillExecutor.Execute` — RuntimeCondition false 시 쿨타임 미기록 + false 반환
  - `SkillManager.CanCast` — RuntimeCondition 검사 추가 (다음 슬롯 시도 가능)
  - `SkillBinder.Bind` — `SkillCondition condition` 옵션 파라미터 추가
  - `SkillLibrary` — 4종 Condition 메서드 추가 (SurvivalPulse/OverchargeMode × 플레이어/보스)
- **SkillArea.TickArea** — `ctx.HitLanded` 미저장/미복원 → 틱 이펙트가 HitLanded 수정 시 오염
  - `PrimaryTarget` 과 동일하게 save/restore 패턴 적용

---

## 스킬 시스템 버그 수정 — ApplyInArea HitLanded + 투사체 이중발사 (수정)
**경로:** `Assets/Scripts/Skill/Core/SkillComponents.cs`, `Assets/Scripts/Skill/Core/SkillLibrary.cs`
**변경일:** 2026-04-17

### 수정
- **ApplyInArea** — `ctx.HitLanded` 미기록 버그 수정
  - 범위 내 타겟 1명 이상 적중 시 `HitLanded = true` 설정
  - 영향: 붕괴 포효(플레이어/보스)의 좁은범위→광역 분기가 정상 작동
  - 수정 전: 항상 이중 발동 (좁은범위 + 광역 둘 다 실행)
- **관통 저격 / 파열 탄창** — 투사체(비동기) + TriggerOnHit(동기) 타이밍 충돌로 항상 2발 발사
  - 약점 판정(NoCoreHit) 시스템 구현 전까지 재발사 분기 제거, 1발만 발사
- 보스 공용 주석 "12종" → "11종" 수정 (실제 구현 수량 반영)

---

## 스킬 SO 자동 생성 + 부트스트랩 (신규)
**경로:** `Assets/Editor/SkillDefinitionGenerator.cs`, `Assets/Scripts/Skill/Core/SkillBootstrap.cs`
**변경일:** 2026-04-17

### 신규
- **SkillDefinitionGenerator** (에디터 스크립트)
  - 메뉴: `Tenebris > 스킬 SO 전체 생성 (공용 12종 + 보스 12종)`
  - 23종 SkillDefinition SO 자동 생성 (`Assets/ScriptableObjects/Skills/`)
  - SkillRegistry SO 자동 생성 + 전체 스킬 풀 등록
  - 재실행 시 기존 SO 메타데이터 갱신 (중복 생성 없음)
- **SkillBootstrap** (MonoBehaviour)
  - 씬에 배치 → SkillRegistry 연결
  - Awake 시 `SkillBinder.BindAll(registry)` 호출 → 모든 SO에 RuntimeStep 주입

---

## DualTargetAgent Phase 2b — 추격 품질 향상 (수정)
**경로:** `Assets/Scripts/AI/BossAI/DualTargetAgent.cs`
**변경일:** 2026-04-17

### 변경
- Phase 2a(순차 추격) 기반 위에 추격 품질 요소 추가:
  - `_wAlign = 0.003` — active 타겟을 바라보며 접근 시 보상 (dot > 0.7)
  - `_wIdlePenalty = 0.005` — 정지/회전만 시 패널티 (위치 변화 < 0.05)
  - `_wStepPenalty` 0.002 → 0.005 — 시간 압박 강화
- 관측값 11개 변경 없음 → `--resume` 으로 이어서 학습 가능
- DualTarget 학습 결과 → `results/DualTarget_backup/` 에 백업

---

## DualTargetAgent 순차 추격 학습 — secondary 보상 제거 (수정)
**경로:** `Assets/Scripts/AI/BossAI/DualTargetAgent.cs`
**변경일:** 2026-04-17

### 문제
active + secondary 동시 progress 보상 → 두 힘의 균형점인 가운데로 가서 빙글빙글 도는 local optimum.

### 변경
- **`_wSecondaryProgress` 제거** — secondary 방향 보상이 가운데로 끌던 원인
- active 하나만 쫓다가 근접하면 → `ActiveIsP1()` 이 자동으로 나머지를 active로 전환 → 다음 것 추격
- 관련 필드/변수 정리: `_prevSecondaryDist`, `secondaryDist` 제거
- 최종 보상 구조 (2개만):
  - `_wStepPenalty = 0.002` (가벼운 시간 압박)
  - `_wProgress = 0.50` (active 거리 감소만)
  - 근접 성공 보너스: 0.5 × 2 + FAST 0.5

---

## DualTargetAgent 근접 거리 종료 + 정적 보상 제거 (수정)
**경로:** `Assets/Scripts/AI/BossAI/DualTargetAgent.cs`
**변경일:** 2026-04-17

### 문제
학습 중간부터 보스가 두 플레이어를 바라보면서 그 자리에서 빙글빙글 회전만 하고 접촉을 시도하지 않음. 정적 보상(closeness/midpoint/align)을 챙기는 local optimum에 갇힘.

### 변경
- **종료 조건 변경**: trigger collision → **근접 거리 진입(`_proximityRadius = 3.0f`)**
  - `OnTriggerEnter` 의 Player 처리 블록 전체 제거
  - `ApplyStepRewards` 안에 `CheckProximityTouch(distP1, distP2)` 매 스텝 호출
  - 양쪽 다 근접 진입 → `_successCount++` + `EndEpisode()`
- **정적 보상 전부 제거** (빙글빙글 방지):
  - `_wTargetCloseness`   0.005 → **0**
  - `_wMidpointCloseness` 0.002 → **0**
  - `_wAlign`             0.001 → **0**
- **진행/패널티 보상 강화** (실제 이동 유도):
  - `_wProgress`          0.30  → **0.50**
  - `_wSecondaryProgress` 0.10  → **0.20**
  - `_wIdlePenalty`       0.005 → **0.015**
  - `_wStepPenalty`       0.005 → **0.01**
- 미사용 필드 정리: `_alignDotThreshold`, `_targetSwitchReward` 제거
- 로그/주석 "접촉" → "근접" 으로 변경

### 효과 예측
- 가만히 회전만 하면: 시간 압박(−0.01) + 정지 패널티(−0.015) = 매 스텝 −0.025 누적
- 실제 거리 좁히면: progress 보상이 압도적으로 커서 이동 학습 강제
- 양쪽 한번씩 근접하기만 하면 종료 → 접촉(trigger) 정확도 의존성 제거

---

## DualTargetAgent 양쪽 균형 + 성공 카운터 (수정)
**경로:** `Assets/Scripts/AI/BossAI/DualTargetAgent.cs`
**변경일:** 2026-04-17

### 변경
- **`_wSecondaryProgress = 0.10f`** 신규 — secondary 거리 감소도 보상
  - active 진행 보상의 1/3 가중치
  - secondary 가 이미 접촉됐으면 적용 안 함
  - 효과: 한 명에게만 직진 → 양쪽 모두 압박하는 경로 학습
- **`_wMidpointCloseness`** 0.001 → **0.002** (살짝 회복)
- 성공 카운터 신규: `_successCount`, `_fastSuccessCount`, `_slowSuccessCount`
- `OnTriggerEnter` 양쪽 접촉 성공 시 카운터 증가 + 누적 횟수 로그
- 성공 시 보상 명세:
  - 첫 접촉 +0.5, 두 번째 접촉 +0.5, FAST(gap≤3s) 보너스 +0.5
  - 누적: 1.0(SLOW) ~ 1.5(FAST)
- 로그 포맷: `[DualTarget] ✅ FAST 성공 #N (FAST=A / SLOW=B) gap=X.XXs reward=Y.YY`

---

## DualTargetAgent 진동/정지 회전 spam 해결 — 관측 정렬 + 보상 재설계 (수정)
**경로:** `Assets/Scripts/AI/BossAI/DualTargetAgent.cs`
**변경일:** 2026-04-17

### 문제
- 보스가 두 타겟을 번갈아 보면서 회전만 함 (이동 학습 안 됨)
- 원인 ① 관측이 P1/P2 고정 슬롯 → 정책이 두 타겟에 균등 반응 (진동 학습)
- 원인 ② 회전·정지 비용이 0에 가까움 → activeTarget 보상만으로 가만히 있어도 양수 누적
- 원인 ③ 진행 보상 가중치 0.05 — 너무 약해서 위치 보상이 압도

### 변경 — 관측 재설계 (P1/P2 → Active/Secondary 정렬)
- `ActiveIsP1(distP1, distP2)` 헬퍼 추가 (관측/보상 공통 사용)
- 관측 11개 슬롯을 활성/2차 타겟 우선순위로 정렬:
  - [0~3] activeTarget (방향x, 방향z, 거리, 정렬도)
  - [4~7] secondaryTarget (방향x, 방향z, 거리, 정렬도)
  - [8]   두 플레이어 사이 거리
  - [9]   secondaryTouched 플래그
  - [10]  에피소드 시간 진행도 (긴박감 신호 — 신규)
- 효과: 정책이 "active 슬롯은 항상 추격 대상"이라는 일관성 학습 → 진동 제거

### 변경 — 보상 재설계 (정지/회전 spam 제거)
| 가중치 | 기존 | 신규 | 변화 |
|--------|------|------|------|
| `_wStepPenalty` (시간 압박) | 0.002 | **0.005** | 2.5× 강화 |
| `_wTargetCloseness` (근접) | 0.015 | **0.005** | 1/3 감소 |
| `_wMidpointCloseness` (중점) | 0.008 | **0.001** | 거의 제거 |
| `_wProgress` (진행, 메인) | 0.05  | **0.30**  | **6× 강화** |
| `_wAlign` (정렬) | 0.005 | **0.001** | 1/5 감소 (회전 spam 방지) |
| `_wIdlePenalty` (정지) | (없음) | **0.005** | 신규 |
| `_minMoveDelta` (정지 임계) | (없음) | **0.05** | 신규 |

### 변경 — 정지 패널티 신규
- `_prevBossPos`, `_prevPosValid` 필드 추가
- 매 스텝 `Distance(현재, 이전) < _minMoveDelta` 면 `−_wIdlePenalty` 부과
- 효과: 가만히 회전만 하면 매 스텝 −0.01 (스텝 + 정지) 손실 → 반드시 직진해야 양수

### 학습 영향
- "두 타겟 중간에서 회전만" 지역 최적점 제거
- 진행 보상이 메인 신호 → "다가가기" 행동에 강한 보상
- 처음부터 학습 권장 (`--initialize-from` 제거, `--force` 사용)

---

## DualTargetAgent 시간 하드 컷오프 단순화 (수정)
**경로:** `Assets/Scripts/AI/BossAI/DualTargetAgent.cs`
**변경일:** 2026-04-17

### 변경
- 기존 단계별 타임아웃(`_noTouchTimeoutSec`/`_firstTouchTimeoutSec`) 제거
- `_episodeMaxDurationSec` 단일 하드 컷오프로 통합 (기본 30s)
- 시간 종료 시 접촉 상태별 차등 패널티:
  - 둘 다 미접촉 → `_noTouchPenalty (-0.5)` (마젠타)
  - 한쪽만 접촉 → `_partialTouchPenalty (-0.2)` (검정)
  - 양쪽 접촉(비정상) → 0 (흰색)

---

## DualTargetAgent 첫 접촉 자체 타임아웃 추가 (수정)
**경로:** `Assets/Scripts/AI/BossAI/DualTargetAgent.cs`
**변경일:** 2026-04-16

### 문제
- 기존 종료 조건이 첫 접촉을 전제로 함 (XOR 한쪽만 접촉 시) → **둘 다 한 번도 안 만지면 영원히 안 끝남**
- Agent.MaxStep 기본값 0(무한)이라 글로벌 컷오프도 없음

### 변경
- `_noTouchTimeoutSec = 15f`, `_noTouchFailPenalty = -0.5f` 필드 추가
- `_episodeStartTime` 필드 추가, `ResetEpisodeState()` 에서 `Time.time` 기록
- `CheckTerminationConditions()` 에 신규 케이스: 둘 다 미접촉 + 15초 경과 → 패널티 후 EndEpisode (마젠타 색)

### 종료 경로 (최종)
1. ✅ 성공 — 양쪽 접촉 완료 (`OnTriggerEnter`)
2. ❌ 맵 밖 낙하 (Y < -5)
3. ❌ **첫 접촉 자체 타임아웃 (15초)** — 신규
4. ❌ 첫 접촉 후 두 번째 접촉 실패 (5초)

---

## DualTargetAgent 보상 구조 재설계 — "중점 압박 + 단일 집중" 하이브리드 (수정)
**경로:** `Assets/Scripts/AI/BossAI/DualTargetAgent.cs`
**변경일:** 2026-04-16

### 배경
- 플레이어 AI는 카이팅(거리 유지) 전략 — 보스 속도 = 플레이어 속도일 때 단일 추격은 수학적으로 불가능
- 기하학적 최적: 두 플레이어의 **중점**에 위치 → 양쪽 도망 방향 차단 → MinSpacing 제약으로 분산도 한계
- 한쪽 접촉 후엔 단일 타겟 집중이 자연스러움

### 변경
- **activeTarget 결정 로직** — 안 만진 쪽 우선, 둘 다 미접촉이면 더 가까운 쪽
- **하이브리드 보상**:
  - activeTarget 근접: `_wTargetCloseness = 0.015f` (주 압박)
  - 중점 근접: `_wMidpointCloseness = 0.008f` (둘 다 미접촉 시만)
  - 거리 감소 진행: `(prevDist − currDist) * _wProgress(0.05f)`
  - activeTarget 정렬: `_wAlign = 0.005f`
- 매 스텝 패널티 −0.001 → **−0.002** (지연 페널티 2배)
- **타겟 전환 보상 제거** (`_targetSwitchReward` 필드는 호환성 유지, 미사용)
- `_prevTargetDist` 필드 추가, `OnTriggerEnter`/`ResetEpisodeState()` 에서 −1f 리셋
- 4개 가중치를 `[Header("위치 전략 가중치")]` 로 Inspector 노출 (튜닝 용이)

### 학습 영향
- **둘 다 미접촉 단계**: 보스가 두 플레이어 사이로 진입 → 압박 → 가까운 쪽 직진
- **한쪽 접촉 후**: 안 만진 쪽 단일 추격 (Phase 1 BasicMove 정책 재활용)
- 중점 가중치(0.008)가 단일 타겟 가중치(0.015)의 약 절반 — 중점 ≠ 종착지, 압박 도구

---

## DualTargetAgent 스폰 로직 개선 (수정)
**경로:** `Assets/Scripts/AI/BossAI/DualTargetAgent.cs`
**변경일:** 2026-04-16

### 변경 사항
- 스폰 시 `localPosition` → **월드 좌표(`position`)** 사용 (스폰포인트 부모 transform 에 영향받던 버그 제거)
- **`PlaceOnSpawn()`** 헬퍼 추가 — 플레이어에 `NavMeshAgent` 가 있으면 `Warp()` 로 NavMesh 상태 재동기화 + `ResetPath()` + `velocity = 0`
- 리스트 2개 미만이면 경고 로그 후 스폰 스킵

### 설정 가이드 (Inspector)
- Boss → DualTargetAgent → `Player Spawn Points` 리스트에 **4개 Transform 드래그**
- 에피소드 시작 시 자동으로 4개 중 서로 다른 2개 선택하여 P1 / P2 배치

---

## DualTargetAgent 관측 거리 확장 (수정)
**경로:** `Assets/Scripts/AI/BossAI/DualTargetAgent.cs`
**변경일:** 2026-04-16

### 변경 사항
- `_maxDistance` : `15f` → **`55f`**

### 이유
- Plane scale 80 (실제 800m × 800m) 맵에서 봇 공전 반경 40m 운용 대응
- 기존 15m 정규화는 40m 밖에서 관측값이 `Clamp01(dist/15) = 1` 로 포화되어 학습 불가
- `OptimalMax(50)` 대비 약간의 여유를 두어 55f 채택

### 연동 Blackboard (참고 — 에디터에서 수동 설정)
```
DangerRange=15, MinSpacing=8, OptimalMin=30, OptimalMax=50,
FleeDistance=20, FlankRadius=35, StrafeRadius=40, StrafeAngleStep=60
NavMeshAgent.Speed=12 (Boss/1P/2P 공통)
```

---

## DualTargetAgent 종료 조건 재설계 (수정)
**경로:** `Assets/Scripts/AI/BossAI/DualTargetAgent.cs`
**변경일:** 2026-04-16

### 이전 문제
- 종료 조건이 "양쪽 접촉" 단 하나뿐 — 한쪽만 접촉한 채 MaxStep까지 방치되어 샘플 효율 저조
- `_targetSwitchReward = 0.08` 너무 커서 좌우 진동 익스플로잇 가능
- `_doubleTouchWindow = 2.0s` 타이트해서 보너스 획득 거의 불가

### 신규 종료 조건
1. **FAST 성공** (초록) — 양쪽 접촉 + 윈도우(3초) 이내 → `+1.5` (0.5 × 2 + 0.5 보너스) + EndEpisode
2. **SLOW 성공** (청록) — 양쪽 접촉 + 윈도우 초과 → `+1.0` (0.5 × 2) + EndEpisode
3. **타임아웃 실패** (검정) — 첫 접촉 후 5초 내 두 번째 실패 → `-0.3` + EndEpisode
4. **맵 이탈 실패** (회색) — Y < -5 낙하 → `-1.0` + EndEpisode
5. **MaxStep 초과** — ML-Agents 프레임워크 자동

### 튜닝 조정
| 필드 | Before | After |
|---|---|---|
| `_doubleTouchWindow` | 2.0s | **3.0s** |
| `_targetSwitchReward` | 0.08 | **0.03** |

### 신규 인스펙터 필드
- `_firstTouchTimeoutSec` = 5.0 (2번째 접촉 제한시간)
- `_timeoutFailPenalty` = -0.3
- `_outOfBoundsY` = -5
- `_outOfBoundsPenalty` = -1.0
- `_fastDoubleTouchBonus` = 0.5

### 신규 메서드
- `CheckTerminationConditions()` — OnActionReceived 매 스텝 호출, 실패 조건 2종 검사

---

## BossController 듀얼 플레이어 대응 (수정)
**경로:** `Assets/Scripts/BossController.cs`
**변경일:** 2026-04-15

### 변경 사항
- `playerTarget` (단일 Transform) 필드 **삭제** — 두 플레이어 환경에서 한쪽만 추적하던 한계 제거
- `Awake()` 에서 `_gameManager = GameManager.Instance` 자동 바인딩 추가
- `TrackPlayer()` 메서드 **삭제** (이미 주석 처리되어 있었고, 이동은 ML-Agents 가 담당)
- `HandleActions()` → `FindNearestPlayer()` 로 가장 가까운 살아있는 플레이어 거리 기반 공격 트리거
- `FindNearestPlayer()` 신규 — `GameManager.Players` 순회, `ICombatant.IsAlive` 필터링

### 호환성
- Inspector 의 `playerTarget` 슬롯은 사용되지 않으므로 무시 가능 (직렬화 데이터만 잔존)
- `EffectAttackRoutine` 360° 회전 이펙트는 그대로 양쪽 플레이어 모두 피격 가능

---

## StateManager 도입 (신규)
**경로:** `Assets/Scripts/State/CombatantState.cs`, `Assets/Scripts/State/StateManager.cs`
**변경일:** 2026-04-13
**설계 문서:** [STATE_MANAGER_DESIGN.md](../STATE_MANAGER_DESIGN.md)

### 신규 파일
- **CombatantState** — 7종 배타 상태 enum (Idle / Moving / Casting / Parrying / HitStun / Stunned / Dead)
- **StateManager** — StatManager 를 읽어 파생 상태 계산. 자체 저장 없음
  - 우선순위 기반 단일 패스 `ComputeState()` — 상위 계층이 하위를 강제 인터럽트
  - `ChangeState()` 단일 관문 — OnStateExited → Enter → Changed 이벤트 보장
  - Capability 플래그: `CanAct / CanMove / CanCast / CanParry`
  - **CanCast = State ∈ {Idle, Moving} && !Silence** — 스킬은 Idle/Moving 에서만 시전 가능
  - 외부 Notify API: `NotifyMovementInput / NotifyCastStart / NotifyCastEnd / NotifyParryStart / NotifyParryEnd`
  - `ForceReset()` — ML 에피소드 리셋용

### PlayerController.cs 연동
- `[RequireComponent(typeof(StateManager))]` 추가
- `_stateManager` 필드 + `StateMgr` 프로퍼티 노출
- `Start()` 에서 `BindOwner(this)` 호출
- `Update()` 순서: StatManager.Tick → HandleMovement → StateManager.Tick
- `HandleMovement()` 이동 입력 시 `NotifyMovementInput(hasInput)` 호출 + `CanMove` 가드

### BossController.cs 연동
- `[RequireComponent(typeof(StateManager))]` 추가
- `_stateManager` 필드 + `StateMgr` 프로퍼티 노출
- `Start()` 에서 `BindOwner(this)` 호출
- `Update()` 에 NavAgent velocity 기반 `NotifyMovementInput` + `agent.isStopped = !CanMove` 연동
- `EffectAttackRoutine` 의 `SetCasting` 직접 호출 → `NotifyCastStart/End` 경유로 교체

### SkillManager.cs 연동
- `_stateManager` 필드 추가 (Awake 자동 바인딩)
- `CanCast()` 의 6개 상태 분기 → `_stateManager.CanCast` 1줄로 축약
- `Update()` 시전 시점에 `NotifyCastStart → Execute → NotifyCastEnd` 순차 호출
  (현재 RuntimeStep 동기 실행 — 캐스팅 타임 도입 시 코루틴화 예정)

---

## SkillManager.cs (디버그/학습 모드 리팩터)
**경로:** `Assets/Scripts/Skill/Core/SkillManager.cs`
**변경일:** 2026-04-13

### 배경
카드 드래프트는 추후로 미루고 Inspector 슬롯 직접 지정 방식으로 단순화.

### 변경
- 슬롯 자료구조 `List<SkillDefinition>` → **고정 크기 `SkillDefinition[5]` + [SerializeField]** 로 교체
  - Inspector 의 "Slots" 배열에 SkillDefinition SO 를 드래그해 슬롯별 스킬 지정
  - `null` 엔트리는 Update 루프가 건너뜀
  - `OnValidate()` 로 Inspector 에서 배열 크기 변경되어도 5 로 강제 복원
- `_maxSlots`, `_preloadSkills`, `Start()`(preload 로직) 제거
- API 교체: `Equip/Unequip/UnequipAll` → **`SetSlot(int, SkillDefinition)`, `ClearSlot(int)`, `ClearAll()`**
  - 카드 드래프트가 슬롯 index 를 명시적으로 지정하도록 구조 변경

### 영향
- **CardManager.cs** — `skillManager.Equip(...)` 제거, 빈 슬롯 탐색 후 `SetSlot(i, skill)` 호출로 변경

---

## SkillLibrary.cs / SkillBinder.cs
**경로:** `Assets/Scripts/Skill/Core/SkillLibrary.cs`, `Assets/Scripts/Skill/Core/SkillBinder.cs`
**변경일:** 2026-04-13

### 배경
기획표 스펙 대조 후 확실 구현 가능한 스킬만 남기고 나머지는 null 반환으로 비활성화.
`RuntimeStep = null` → `SkillDefinition.IsReady = false` → SkillManager 시전 시도 자체 차단.

### SkillLibrary 수정
- **ErosionField** — inner tick 중복 `ApplyDamageOverTime(1,1)` 제거 (스펙에 없음)
- **CounterStance / CounterSlash** — `null` 반환. 사유: 패링 입력 바인딩 부재 → `IsParrying` 영원히 false
- **WireHook / RopeShockwave** — `null` 반환. 사유: RopeLanding 이벤트 추적 시스템 부재
- **CollapseStrike** — `null` 반환. 사유: ParrySuccessRecent 이력 추적 시스템 부재
- **SealChain_Boss** — `null` 반환. 사유: 4방향 멀티 디렉션 투사체 래퍼 부재
- **RuptureMagazine_Boss** — `null` 반환. 사유: 8방향 폭발 패턴 래퍼 부재

### 유지 (동작 검증 완료)
- 플레이어: ExecutionSpike, CrushingBarrage, ErosionField, HuntingMark, SurvivalPulse,
  FortressArmor, SealChain, CollapseRoar, BarrierBreaker, OverchargeMode, PiercingShot,
  RuptureMagazine, ParryEnhance (버프 적용만)
- 보스: ExecutionSpike_Boss, CrushingBarrage_Boss, ErosionField_Boss, SurvivalPulse_Boss,
  FortressArmor_Boss, CollapseRoar_Boss, OverchargeMode_Boss, MarkWave_Boss, BarrierBreaker_Boss

### SkillBinder 수정
- `Bind()` 가 `step == null` 일 때 카운트 제외 → 로그 `[SkillBinder] N종 바인딩 완료` 의 N 이 실제 구현 개수만 반영

---

## StatsManager.cs
**경로:** `Assets/StatsManager.cs`
**변경일:** 2026-03-30

### 변경 전
- `GetPlayerHP()`, `ApplyDamageToPlayer()`, `GetBossHP()`, `ApplyDamageToBoss()`, `GetBossPhase()` 5개 메서드만 존재
- 피해 처리 시 Shield 로직 없음

### 변경 후 (추가된 로직)
- **조회**
  - `GetPlayerMaxHP()`, `GetPlayerHPPercent()`, `GetPlayerShield()`
  - `GetBossMaxHP()`, `GetBossHPPercent()`
  - `GetPlayerMoveControl()`, `GetBossMoveControl()`
  - `HasStatusPlayer(StatusType)`, `HasStatusBoss(StatusType)`

- **피해 / 회복 / 실드**
  - `ApplyDamageToPlayer()` — Shield 우선 소진 로직 추가
  - `TakeShieldBreakDamagePlayer(float amount, float multiplier)`
  - `TakeShieldBreakDamageBoss(float amount, float multiplier)`
  - `RecoverHPPlayer(float amount)` — HealingReceivedMultiplier 반영
  - `RecoverHPBoss(float amount)`
  - `AddShieldPlayer(float amount)` — ShieldMax 클램프

- **상태이상 (Player / Boss 각각)**
  - `ApplyStatusPlayer(StatusType, float duration, float value)`
  - `RemoveStatusesPlayer(CleanseType, int count)`
  - `ApplyStatusBoss(StatusType, float duration, float value)`
  - `RemoveStatusesBoss(CleanseType, int count)`
  - 내부: 코루틴 기반 자동 해제, StunDurationMultiplier / DebuffDurationResistance 반영
  - 내부: HPRegen / DamageOverTime → 1초 틱 루프 처리

- **버프 (Player / Boss 각각)**
  - `ApplyBuffPlayer(BuffType, float duration, float value)`
  - `RemoveBuffsPlayer(DispelType, int count)`
  - `ApplyBuffBoss(BuffType, float duration, float value)`
  - `RemoveBuffsBoss(DispelType, int count)`

- **디버프 (Player / Boss 각각)**
  - `ApplyDebuffPlayer(DebuffType, float duration, float value)`
  - `ApplyDebuffBoss(DebuffType, float duration, float value)`

---

## PlayerController.cs
**경로:** `Assets/Scripts/PlayerController.cs`
**변경일:** 2026-03-30

### 변경 전
- `private float currentHP` / `private float currentShield` 필드를 Controller가 직접 보관
- `TakeDamage()` 내부에서 `currentHP`, `currentShield` 직접 수정
- `RegenerateHP()` 내부에서 `currentHP` 직접 수정
- 이동 속도에 MoveControlMultiplier 미반영
- `ICombatant` 미구현

### 변경 후
- `currentHP`, `currentShield` 필드 **제거**
- `public StatsManager statsManager` 참조 추가
- `ICombatant` 구현 — 모든 스탯 변경은 StatsManager 경유
- `TakeDamage()`, `TakeShieldBreakDamage()` → StatsManager 위임
- `RecoverHP()`, `AddShield()` → StatsManager 위임
- `ApplyStatus/Buff/Debuff/RemoveStatuses/RemoveBuffs` → StatsManager 위임
- `Knockback()` → Rigidbody.AddForce(Impulse)
- `Pull()`, `MoveBy()` → 코루틴 기반 Lerp 이동
- `NotifyParryReward()` → Invulnerable / Buff 구현, Counter/HitStun 추후
- 이동 속도 → `playerStats.MoveSpeed * statsManager.GetPlayerMoveControl()` (스턴/슬로우 자동 반영)

### 변경 (2026-04-06)
- `TakeDamage(float, ICombatant attacker)` — attacker 파라미터 추가
  - 패링 중 + attacker 존재 → 임시 반격 피해 전달
  - Reflecting 상태 + attacker → `statsManager.GetPlayerReflectRatio()` 비율만큼 반사 피해
- `TakeShieldBreakDamage(float, float, ICombatant attacker)` — attacker 파라미터 추가
- `NotifyParryReward()` — Counter(반격 피해) / HitStun(경직 부여) / Invulnerable(무적) / Buff(DamageUp) 4종 전부 구현, attacker 파라미터 추가
- `GameManager _gameManager` SerializeField 참조 추가

---

## BossController.cs
**경로:** `Assets/Scripts/BossController.cs`
**변경일:** 2026-03-30

### 변경 전
- `private float currentHP` 필드를 Controller가 직접 보관
- `TakeDamage()` 내부에서 `currentHP` 직접 수정
- `HandlePhase()` 내부에서 `currentHP / bossStats.BossMaxHP` 직접 계산
- `ICombatant` 미구현

### 변경 후
- `currentHP` 필드 **제거**
- `public StatsManager statsManager` 참조 추가
- `ICombatant` 구현 — 모든 스탯 변경은 StatsManager 경유
- `TakeDamage()`, `TakeShieldBreakDamage()` → StatsManager 위임
- `RecoverHP()` → StatsManager 위임 / `AddShield()` → 보스 실드 없음(빈 구현)
- `ApplyStatus/Buff/Debuff/RemoveStatuses/RemoveBuffs` → StatsManager 위임
- `Knockback()`, `Pull()`, `MoveBy()` → NavMeshAgent.Warp() 기반
- `NotifyParryReward()` → 보스는 패링 없음(빈 구현)
- `HandlePhase()` → `statsManager.GetBossHPPercent()` 참조
- `TrackPlayer()` → NavMeshAgent 속도에 `statsManager.GetBossMoveControl()` 반영
- `EffectAttackRoutine()` → 공격 중 `isCasting = true` 설정 (CheckTargetCasting 조건 반영)

### 변경 (2026-04-06)
- `TakeDamage(float, ICombatant attacker)` — attacker 파라미터 추가 (시그니처 맞춤)
- `TakeShieldBreakDamage(float, float, ICombatant attacker)` — attacker 파라미터 추가
- `NotifyParryReward(ParryRewardType, float, float, ICombatant attacker)` — attacker 파라미터 추가
- `GameManager _gameManager` SerializeField 참조 추가

---

## ICombatant.cs
**경로:** `Assets/Scripts/Skill/Interfaces/ICombatant.cs`
**변경일:** 2026-04-06

### 변경 후
- `TakeDamage(float amount, ICombatant attacker = null)` — attacker 파라미터 추가
- `TakeShieldBreakDamage(float amount, float multiplier, ICombatant attacker = null)` — attacker 파라미터 추가
- `NotifyParryReward(ParryRewardType rewardType, float value, float duration, ICombatant attacker = null)` — attacker 파라미터 추가

---

## StatsManager.cs (2차)
**경로:** `Assets/StatsManager.cs`
**변경일:** 2026-04-06

### 변경 후
- `GetPlayerReflectRatio()` public getter 추가 — PlayerController.TakeDamage 피해 반사에서 사용

---

## SkillComponents.cs
**경로:** `Assets/Scripts/Skill/Core/SkillComponents.cs`
**변경일:** 2026-04-06

### 변경 후
- 37종 완성본 작성
- `CheckRecentDamage` (구 #36), `CheckTargetCasting` (구 #37) 제거
- `MoveSelf` → 새 #36, `CheckTargetDistance` → 새 #37로 번호 재정렬
- DealDamage(#1), DealMultiHitDamage(#2), ExecuteBelowHP(#29), DealDirectionalHit(#35), DealShieldBreakDamage(#28) — `ctx.Caster`를 attacker로 전달
- ApplyParryReward(#24) — `ctx.PrimaryTarget`를 attacker로 전달
- LaunchProjectile(#32) — ProjectilePool 싱글턴 사용, pool 파라미터 제거

---

## SkillContext.cs
**경로:** `Assets/Scripts/Skill/Core/SkillContext.cs`
**변경일:** 2026-04-06

### 변경 후
- `RecentDamageTaken` 필드 제거 (dead field)

---

## SkillTypes.cs
**경로:** `Assets/Scripts/Skill/Core/SkillTypes.cs`
**변경일:** 2026-04-06

### 변경 후
- `CastingCheckType` 열거형 제거 (dead type)

---

## 신규 파일 (2026-04-06)

| 파일 | 경로 | 설명 |
|------|------|------|
| GameManager.cs | `Assets/Scripts/GameManager.cs` | 싱글턴, 플레이어/보스 리스트 관리, 전투 타이머 |
| SkillDefinition.cs | `Assets/Scripts/Skill/Core/SkillDefinition.cs` | ScriptableObject — 스킬 메타데이터 + RuntimeStep |
| SkillExecutor.cs | `Assets/Scripts/Skill/Core/SkillExecutor.cs` | 스킬 실행 + 쿨타임 관리 |
| SkillRegistry.cs | `Assets/Scripts/Skill/Core/SkillRegistry.cs` | ScriptableObject — 스킬 풀 관리, 태그 조회, 드래프트/카운터 후보 |
| ProjectilePool.cs | `Assets/Scripts/Skill/Projectile/ProjectilePool.cs` | 싱글턴 오브젝트 풀 — SkillProjectile 관리 |
| SkillProjectile.cs | `Assets/Scripts/Skill/Projectile/SkillProjectile.cs` | 투사체 프리팹 컴포넌트 — IProjectile 구현 |
| PersistentAreaManager.cs | `Assets/Scripts/Skill/Area/PersistentAreaManager.cs` | 싱글턴 — 장판 소환 허브 |
| PersistentAreaPool.cs | `Assets/Scripts/Skill/Area/PersistentAreaPool.cs` | 오브젝트 풀 — SkillArea 관리 |
| SkillArea.cs | `Assets/Scripts/Skill/Area/SkillArea.cs` | 장판 프리팹 컴포넌트 — IPersistentArea 구현 |
| IProjectile.cs | `Assets/Scripts/Skill/Interfaces/IProjectile.cs` | 투사체 인터페이스 (IPoolable 상속) |
| IPersistentArea.cs | `Assets/Scripts/Skill/Interfaces/IPersistentArea.cs` | 장판 인터페이스 (IPoolable 상속) |
| IPoolable.cs | `Assets/Scripts/Skill/Interfaces/IPoolable.cs` | 풀링 공통 인터페이스 — OnSpawn/OnDespawn |

---

## 삭제된 파일 (2026-04-06)

| 파일 | 경로 | 사유 |
|------|------|------|
| GoalDetector.cs | `Assets/Scripts/AI/BossAI/GoalDetector.cs` | BossAgent.cs에 병합 완료

---

## 스킬 슬롯 연동 — 드래프트→실행 파이프라인 구축 (2026-04-08)

### AbilityCard.cs
**경로:** `Assets/Scripts/AbilityCard.cs`
- `SkillDefinition skillDefinition` 필드 추가 (신규 스킬 시스템 연결)
- 기존 `skillObjectName` 필드는 레거시 호환용으로 유지

### PlayerController.cs
**경로:** `Assets/Scripts/PlayerController.cs`
- `PlayerSkillSlot _skillSlot` SerializeField 추가
- `HandleActions()` → Q/W/E/R/T 키 입력 시 PlayerSkillSlot.TryExecute 호출로 교체
- `BuildSkillContext()` 추가 — Caster/Target/Position/Direction 자동 생성
- `FindNearestBoss()` 추가 — GameManager.Bosses에서 가장 가까운 보스 탐색

### CardManager.cs
**경로:** `Assets/Scripts/CardManager.cs`
- `UnlockSkill()` → SkillDefinition 기반으로 교체 (PlayerSkillSlot.Equip 호출)
- skillDefinition 없을 경우 레거시(skillObjectName) 폴백 유지

### GameManager.cs
**경로:** `Assets/Scripts/GameManager.cs`
- `SkillRegistry _skillRegistry` SerializeField 추가
- `Start()`에서 `SkillBinder.BindAll(_skillRegistry)` 호출 추가

### 신규 파일

| 파일 | 경로 | 역할 |
|------|------|------|
| PlayerSkillSlot.cs | `Assets/Scripts/Skill/Core/PlayerSkillSlot.cs` | 스킬 슬롯 관리 (장착/해제/실행/쿨타임 조회) |
| SkillBinder.cs | `Assets/Scripts/Skill/Core/SkillBinder.cs` | SkillLibrary → SkillDefinition.RuntimeStep 일괄 주입 |

---

## SkillLibrary.cs (전체 재작성)
**경로:** `Assets/Scripts/Skill/Core/SkillLibrary.cs`
**변경일:** 2026-04-11

### 변경 전
- `ErosionField_Boss()`, `SealChain()` 2개 메서드만 존재
- SkillBinder에서 참조하는 27개 메서드 미정의 → CS0117 컴파일 에러

### 변경 후
- **29개 전체 스킬 메서드 구현 완료**
- 플레이어 공용 (12): ExecutionSpike, CrushingBarrage, ErosionField, HuntingMark, SurvivalPulse, FortressArmor, SealChain, CollapseRoar, BarrierBreaker, OverchargeMode, PiercingShot, RuptureMagazine
- 플레이어 전용 (6): CounterStance, ParryEnhance, CounterSlash, WireHook, RopeShockwave, CollapseStrike
- 보스 공용 (11): ExecutionSpike_Boss, CrushingBarrage_Boss, ErosionField_Boss, SurvivalPulse_Boss, FortressArmor_Boss, CollapseRoar_Boss, OverchargeMode_Boss, MarkWave_Boss, SealChain_Boss, BarrierBreaker_Boss, RuptureMagazine_Boss
- 비율형(Vulnerability/AntiHeal) → 0~1 decimal 변환 (5% → 0.05f)
- 정수형(DamageUp/DefenseDown) → 그대로 전달 (15 → 15f)
- 최대HP 기반 계산 → `ctx.Caster?.MaxHP ?? 0f` 사용
- **스텁 조건**: WireHook/CollapseStrike의 RopeLanding, ParrySuccessRecent → `cond => true` (상태 추적 미구현)
- **단순화**: SealChain_Boss/RuptureMagazine_Boss → 단일 투사체 (다방향 래퍼 추후)

---

## SkillComponents.cs (TriggerOnHit 시그니처 변경)
**경로:** `Assets/Scripts/Skill/Core/SkillComponents.cs`
**변경일:** 2026-04-11

### 변경 전
- `TriggerOnHit(SkillStep onHit, SkillStep onMiss = null)` — onHit 필수 파라미터

### 변경 후
- `TriggerOnHit(SkillStep onHit = null, SkillStep onMiss = null)` — **onHit도 선택 파라미터로 변경**
- SkillLibrary에서 `TriggerOnHit(onMiss: ...)` 형태로 onMiss만 전달하는 7곳의 CS7036 에러 해결
- 내부 로직 `(ctx.HitLanded ? onHit : onMiss)?.Invoke(ctx)` 가 null-safe이므로 동작 변화 없음

---

## 신규 파일 (2026-04-11)

| 파일 | 경로 | 설명 |
|------|------|------|
| AI_SYSTEM.md | `Assets/Scripts/AI/AI_SYSTEM.md` | AI 시스템 전체 문서 — BossAgent(ML-Agents PPO), 플레이어 봇(Behavior Graph), 학습 설정/이력, DoubleMove 설계 |

---

## PlayerController / CardManager Stage 7 — 수동 입력 제거 + SkillManager 전환 (2026-04-13)

**경로:**
- `Assets/Scripts/PlayerController.cs` (정리)
- `Assets/Scripts/CardManager.cs` (SkillManager 우선 경로 추가)

### PlayerController 제거/이관
- `[SerializeField] PlayerSkillSlot _skillSlot` **삭제** → `[SerializeField] SkillManager _skillManager`
- `static readonly KeyCode[] SkillKeys (Q/W/E/R/T)` **삭제**
- `HandleActions()` **삭제** (수동 Input.GetKeyDown 루프)
- `BuildSkillContext()` / `FindNearestBoss()` **삭제** (SkillManager 로 이관)
- `[SerializeField] GameManager _gameManager` **삭제** (SkillManager 가 자체 참조)
- `Update()` → `Tick + HandleMovement` 만 남음, 스킬 시전은 SkillManager 자동 처리
- 외부 프로퍼티: `SkillSlot` → `SkillMgr` 로 교체
- `Awake()` 에 `_skillManager` GetComponent fallback 추가

### CardManager 변경
- `Equip` 경로에서 `SkillManager` 를 먼저 조회, 없으면 `PlayerSkillSlot` 폴백
- 로그 메시지 "SkillManager / PlayerSkillSlot 둘 다 없음" 으로 교체

### 최종 PlayerController 책임
1. 이동 입력(WASD → Rigidbody)
2. ICombatant 프록시 (전부 StatManager 위임)
3. 위치 제어 코루틴 (Knockback/Pull/MoveBy)
4. 사망 처리

### Scene 작업 필요
- Player GameObject 에 `SkillManager` 컴포넌트 부착 (RequireComponent 아님 — 수동)
- `SkillManager` 의 `_statManager / _gameManager / _owner` Inspector 바인딩 (Awake 에 GetComponent fallback 있지만 `_gameManager` 는 scene 참조 필요)
- 기존 `PlayerSkillSlot` 컴포넌트는 남겨도 무방 (CardManager 폴백 경로)

---

## SkillManager Stage 6 — 자동 시전 매니저 신규 (2026-04-13)

**경로:** `Assets/Scripts/Skill/Core/SkillManager.cs` (신규)

### 개요
`PlayerSkillSlot` 의 확장판. 슬롯 index 순서 = 우선순위. 매 프레임 `CanCast` 를 돌려
첫 번째 가능한 스킬을 자동 시전한다. Q/W/E/R/T 수동 입력 없이 동작.

### 공통 구조 (PlayerSkillSlot 과 동일)
- `[RequireComponent(typeof(SkillExecutor))]`
- `Equip / Unequip / UnequipAll`
- `TryExecute / CanUse / GetRemainingCooldown / ResetCooldown`

### 신규 기능
- `Update()` — `_autoCastEnabled && IsAlive` 일 때 슬롯 순회, 첫 CanCast 통과 스킬 1개 실행 후 break
- `SetAutoCast(bool)` — 토글
- `CanCast(skill, out ctx)` — 7조건 검사
- `BuildSkillContext(target)` / `FindNearestTarget()` — PlayerController 에서 이관

### CanCast 7조건
| # | 조건 | 체크 |
|---|------|------|
| 1 | 쿨타임 만료 | `_executor.CanUse(skill)` |
| 2 | 플레이어 생존 | `_statManager.IsAlive` (Update 진입 단계) |
| 3 | 시전 중 아님 | `!_statManager.IsCasting` |
| 4 | 패링 중 아님 | `!_statManager.IsParrying` |
| 5 | 무력화 없음 | `!HasStatus(Stunned/HitStun/Silence/Rooted)` |
| 6 | 타겟 존재 + 생존 | `target != null && target.IsAlive` (Self 는 skip) |
| 7 | 사거리 내 | `dist ≤ skill.Range` (Self 는 skip) |

### 직렬화 참조
- `_statManager` / `_gameManager` / `_owner(PlayerController)` — Inspector 바인딩, Awake 에 GetComponent fallback

### TODO (Stage 7)
- `PlayerController.HandleActions` 의 Q/W/E/R/T 수동 입력 제거
- 기존 `PlayerSkillSlot` 을 `SkillManager` 로 치환 (또는 공존)
- 통합 테스트 + AI_SYSTEM.md 갱신

---

## BossController Stage 5 — StatManager 위임 + 모놀리스 삭제 (2026-04-13)

**경로:** `Assets/Scripts/BossController.cs`, `Assets/StatsManager.cs` (삭제)

### BossController 변경
- 필드 `public StatsManager statsManager` → `[SerializeField] private StatManager _statManager`
- `[RequireComponent(typeof(StatManager))]` 추가
- `isCasting / isParrying` 로컬 필드 **삭제** → `_statManager.IsCasting / IsParrying`
  - EffectAttackRoutine 에서 `_statManager.SetCasting(true/false)` 호출
- `Start()` 에서 `_statManager.Initialize(bossStats, BossMaxHP, shieldMax=0, hpRegenRate=0, parryWindow=0, Boss)` + `BindOwner(this)`
- `Update()` 에서 `_statManager.Tick(Time.deltaTime)` 호출
- HP/상태 조회: `GetBossHP/GetBossMaxHP/GetBossHPPercent` → `GetHP/GetMaxHP/GetHPPercent` 통합
- 모든 ICombatant 메서드를 `_statManager` 로 위임 (Player 와 동일 구조)
- `NotifyParryReward` 도 StatManager 위임 — 보스는 실사용 안하지만 인터페이스 통일

### 삭제
- **`Assets/StatsManager.cs`** 삭제 (모놀리스 — Player/Boss 전용 메서드 28개 중복, StatManager 로 통합 완료)
- `Assets/StatsManager.cs.meta` 함께 삭제

### 주의 — Scene 재연결 필요
- `Chapter1.unity`, `_Recovery/*.unity` 에는 GUID 로 StatsManager 컴포넌트가 참조되어 있음 — Unity 에디터에서 열면 "missing script" 경고 발생
- 해당 GameObject 에서 StatsManager 컴포넌트 제거 후 StatManager 컴포넌트로 교체 필요
- Player / Boss GameObject 에 `StatManager` 컴포넌트 부착 (RequireComponent 이 자동 처리)
- Inspector 의 `_statManager` 필드는 Awake 에서 GetComponent fallback, 명시 바인딩도 가능

### TODO (Stage 6)
- SkillManager 신규 생성 (자동 시전, 플레이어 상태별 CanCast 판정)

---

## PlayerController Stage 4 — StatManager 위임 리팩터 (2026-04-13)

**경로:** `Assets/Scripts/PlayerController.cs`

### 변경 내용
- 필드 `public StatsManager statsManager` → `[SerializeField] private StatManager _statManager` 교체
- `[RequireComponent(typeof(StatManager))]` 추가 — 같은 GameObject 자동 부착
- `private bool isCasting / isParrying` 로컬 필드 **삭제** → `_statManager.IsCasting / IsParrying`
- `private void RegenerateHP()` **삭제** → `_statManager.Tick(Time.deltaTime)` 로 대체
- `Start()` 에서 `_statManager.Initialize(playerStats, MaxHP, ShieldMax, HPRegenRate, ParryWindow, Player)` + `BindOwner(this)`

### ICombatant 구현 — 전부 StatManager 위임
| 메서드 | 위임 대상 |
|---|---|
| TakeDamage | `_statManager.ReceiveDamage(amount, attacker)` + Die 체크 |
| TakeShieldBreakDamage | `_statManager.ReceiveShieldBreakDamage(...)` + Die 체크 |
| RecoverHP / AddShield | `_statManager.RecoverHP / AddShield` |
| ApplyStatus / Buff / Debuff | `_statManager.Apply...` |
| HasStatus / RemoveStatuses / RemoveBuffs | `_statManager.Has... / Remove...` |
| NotifyParryReward | `_statManager.NotifyParryReward` (분기 전부 StatManager 에서 처리) |

### 제거된 중복 로직
- `TakeDamage` 내부의 패링 반격 / 반사 / DamageTakenMultiplier / Shield 분기 → 전부 StatManager.ReceiveDamage 1곳에 있음
- `NotifyParryReward` 의 switch 4분기 → StatManager 에서 Counter/HitStun/Invulnerable/Buff 전부 구현

### 새 scene 연결
- GameObject 에 `StatManager` 컴포넌트를 **같이 부착** (RequireComponent 가 자동 추가)
- Inspector 에서 `_statManager` 필드는 자동 바인딩 (Awake 에서 `GetComponent<StatManager>()` fallback)

### TODO (Stage 5)
- BossController 도 동일 리팩터
- 모놀리스 `Assets/StatsManager.cs` 삭제

---

## StatManager Stage 3 — 상태/버프/디버프/회복/실드 (2026-04-13)

**경로:** `Assets/Scripts/Stats/StatManager.cs`

### 추가된 기능
- `RecoverHP(amount)` — `HealingReceivedMultiplier` 반영 후 MaxHP 클램프
- `AddShield(amount)` — `ShieldMax` 클램프
- `ApplyStatus(StatusType, duration, value)` — `CalcStatusDuration` 적용, 기존 코루틴 중복 시 교체
- `RemoveStatuses(CleanseType, count)` — All/DamageOverTime/Debuff 필터
- `ApplyBuff(BuffType, duration, value)` — DamageUp/DefenseUp (+value/100), ParryWindowUp (+base×value/100), ParryRewardUp
- `RemoveBuffs(DispelType, count)` — All/DefenseBuff/OffenseBuff 필터
- `ApplyDebuff(DebuffType, duration, value)` — `DebuffDurationResistance` 반영
- `HasBuff(BuffType)` / `HasDebuff(DebuffType)` 조회
- `NotifyParryReward` 의 **Invulnerable** / **Buff** 분기 완성 → `ApplyStatus` / `ApplyBuff` 위임

### 내부 설계
- `_baseStats` 필드로 원본 SO 참조 보관 (RevertStatus/Buff/Debuff 시 기준값 복원)
- `_baseParryWindow` 로 ParryWindowUp Revert 시 원상 복구
- `WaitOneSec` 정적 캐시 (HPRegen/DamageOverTime 틱)
- 상태별 ApplyStatusValue/RevertStatus switch — 기존 monolith 패턴 이관
- DamageOverTime 은 직접 `SetHP(cur - value × DamageTakenMultiplier)` 로 처리 (ReceiveDamage 우회, 패링/반사 무시)

### TODO (Stage 4 이후)
- Controller 측 연결 (PlayerController → StatManager 위임)
- 모놀리스 `Assets/StatsManager.cs` 제거

---

## StatManager Stage 2 — DealDamage/ReceiveDamage + 패링 (2026-04-13)

**경로:** `Assets/Scripts/Stats/StatManager.cs`

### 추가된 기능
- `BindOwner(ICombatant)` — DealDamage 시 attacker 참조용 소유자 바인딩
- `DealDamage(target, amount)` — DamageUp 반영 후 `target.TakeDamage(adjusted, _owner)` 호출
- `DealShieldBreakDamage(target, amount, multiplier)` — 동일 경로, shield break 전용
- `ReceiveDamage(amount, attacker)` — 패링/반사/DamageTakenMultiplier/Shield/HP 전체 플로우
- `ReceiveShieldBreakDamage(amount, multiplier, attacker)` — shield 우선 차감 + 초과 HP
- `BeginParryWindow() / EndParryWindow()` — `WaitForSeconds` 캐싱 코루틴
- `NotifyParryReward(type, value, duration, attacker)` — Counter/HitStun 구현 (Invulnerable/Buff 는 Stage 3 TODO)
- `HasStatus(type)` 조회 메서드
- `_parryWait` WaitForSeconds 캐시 (Initialize 시점 생성)

### 피해 처리 순서 (ReceiveDamage 내부)
1. `!IsAlive` → 조기 종료
2. `IsParrying && attacker != null` → `attacker.TakeDamage(amount, _owner)` → 피해 무효
3. `HasStatus(Reflecting)` → `attacker.TakeDamage(amount × ReflectRatio, _owner)` (자신도 피해 받음)
4. `finalDamage = amount × DamageTakenMultiplier`
5. Shield > 0 이면 Shield 우선 차감, 음수면 초과분 HP 로
6. Shield == 0 이면 바로 HP 차감
7. HP == 0 이면 `IsAlive = false`

### TODO (Stage 3)
- `ApplyStatus / ApplyBuff / ApplyDebuff / RemoveStatuses / RemoveBuffs / RecoverHP / AddShield`
- Parry Invulnerable / Buff 보상 분기 본체

---

## StatManager Stage 1 — 통합 스켈레톤 (2026-04-13)

**경로:** `Assets/Scripts/Stats/StatManager.cs` (신규)

### 신규 파일
- `StatManager.cs` — Player/Boss 공용 통합 스탯 매니저 스켈레톤
- `CombatantKind` enum (Player/Boss 구분)

### 구현 범위 (Stage 1)
- `Initialize(BaseStatsSO, maxHP, shieldMax, hpRegenRate, parryWindow, kind)` — 런타임 복사본 생성
- 조회: GetHP / GetMaxHP / GetHPPercent / GetShield / GetShieldMax / GetMoveControl / GetReflectRatio 등
- 상태 플래그: IsAlive / IsCasting / IsParrying + SetCasting / SetParrying
- `Tick(float dt)` — HP 자동 재생 틱
- 내부 유틸: SetHP / SetShield (Stage 2+ 에서 ReceiveDamage 가 사용)
- 코루틴 추적용 Dictionary 3종 (StatusType / BuffType / DebuffType) — Stage 3 에서 활용

### 설계 포인트
- 런타임 HP/Shield 는 StatManager **내부 필드**로 관리 (SO 내부값에 의존 X)
- SO 는 Multiplier / ReflectRatio 등 공통 값만 제공
- Player/Boss 호출자가 Initialize 시 타입별 필드(MaxHP vs BossMaxHP 등) 읽어서 넘김

### 다음 Stage
- Stage 2: DealDamage ↔ ReceiveDamage 쌍 + 패링/반사 로직
- Stage 3: 상태이상/버프/디버프/정화 이관

---

## DoubleMove 커스텀 노드 구현 (2026-04-12)

**경로:** `Assets/Scripts/AI/Player/DoubleMove/`

2인 협동 플레이어 봇용 Behavior Graph 커스텀 노드 11개 로직 구현 (기존에는 스켈레톤만 존재).

### Condition 노드 (4개) — `bool IsTrue()` 구현
| 파일 | 역할 |
|------|------|
| IsBossTooCloseCondition.cs | Self↔Boss 거리 < DangerRange 검사 (sqrMagnitude 사용) |
| IsAllyTooCloseCondition.cs | Self↔Ally 거리 < MinSpacing 검사 (겹침 방지) |
| IsBossTargetingAllyCondition.cs | Boss.forward와 Self/Ally 방향 내적 비교 → Ally 쪽이 더 정렬되면 true |
| IsAtOptimalRangeCondition.cs | OptimalMin ≤ Self↔Boss 거리 ≤ OptimalMax 검사 |

### Action 노드 (7개) — `Status OnStart()` 구현
| 파일 | 역할 |
|------|------|
| UpdateSituationAction.cs | Self/Boss/Ally 위치로 DistanceToBoss, DistanceToAlly, BossToAllyAngle 3개 Out 변수 갱신 |
| CalcFleePositionAction.cs | Boss 반대 방향으로 5개 후보 샘플링 → NavMesh 유효 지점 중 보스와 가장 먼 곳 선택 |
| CalcSpreadPositionAction.cs | Ally 반대 방향 MinSpacing×1.2 위치 NavMesh 샘플 |
| CalcFlankPositionAction.cs | Boss 중심, Ally 반대편 FlankRadius 위치 NavMesh 샘플 (측면 협공) |
| CalcStrafePositionAction.cs | Boss 주위 StrafeRadius 반경을 StrafeAngleStep 도 회전한 지점 (실패 시 반대 회전 재시도) |
| CalcApproachPositionAction.cs | Boss 기준 Self 방향으로 (OptimalMin+OptimalMax)/2 거리 위치 |
| SetNavDestinationAction.cs | NavMeshAgent.SetDestination(TargetPosition) (isOnNavMesh 검사 포함) |

### 변수명/타입 수정 (스켈레톤 오타)
- UpdateSituationAction: `Ally의` → `Ally`, `BossToAllyAngle에` → `BossToAllyAngle`
- CalcFleePositionAction: `NavMesh` (Vector3) → `TargetPosition` (Vector3)
- CalcStrafePositionAction: `StrafeAngleStep` 타입 Vector3 → float

### 공통 설계
- 모든 Action: Self/Boss/Ally/Agent null 검사 → Failure 반환
- NavMesh 샘플 실패 시 Warning 로그 + Failure
- Story 텍스트에 `[변수명]` 형식으로 블랙보드 바인딩 슬롯 명시
