# ML-Agents 학습 데이터 관리 가이드

## 1. 데이터 파일 구조

```
Buildup/
  matchup_log_SkillIntro.csv      <- 학습 로그 (에이전트가 자동 기록)
  results/
    SkillIntro_Comprehensive/
      analyze.py                  <- 분석 및 그래프 생성 스크립트
      configuration.yaml          <- 학습 하이퍼파라미터 설정
      SkillIntro/                 <- 체크포인트 디렉터리
        checkpoint.pt             <- 최신 학습 가중치
        SkillIntro-XXXXXX.onnx    <- 스텝별 ONNX 스냅샷 (추론용)
        SkillIntro-XXXXXX.pt      <- 스텝별 PyTorch 스냅샷 (학습 재개용)
      1_winrate.png ~ 16_*.png    <- 분석 그래프 출력
      run_logs/                   <- TensorBoard 로그
```

## 2. CSV 파일 (matchup_log_SkillIntro.csv)

### 기록 방식

- **기록 주체**: `SkillIntroAgent.cs`의 `RecordMatchResult()` 메서드
- **기록 시점**: 에피소드 종료 시 1행 추가 (승리/패배/타임아웃 무관)
- **데이터 수집**: 매 프레임 원시값 누적 -> 에피소드 종료 시 평균/비율로 변환하여 기록
- **파일 위치**: `Application.dataPath/../matchup_log_{BehaviorName}.csv`
- **인코딩**: UTF-8

### 주의사항

- 학습 세션을 재시작하면 CSV 헤더가 다시 기록됨 (중복 헤더 발생)
- analyze.py에서 `Episode` 행을 필터링하고 순서대로 재번호 매김으로 처리
- 기존 23컬럼 데이터와 신규 43컬럼 데이터가 하나의 파일에 혼재 가능

### 컬럼 정의 (43개)

#### 기본 정보 (1-7)

| # | 컬럼명 | 타입 | 설명 |
|---|--------|------|------|
| 1 | Episode | int | 에피소드 번호 (세션 내 순번) |
| 2 | Result | string | 결과 (BossWin / BossLose) |
| 3 | EndReason | string | 종료 사유 (AllPlayersDead / BossDeath / Timeout) |
| 4 | Duration | float | 전투 시간 (초) |
| 5 | BossPool | string | 보스 스킬풀 이름 |
| 6 | P1Pool | string | P1 플레이어 프로필 이름 |
| 7 | P2Pool | string | P2 플레이어 프로필 이름 |

#### 전투 결과 (8-16)

| # | 컬럼명 | 타입 | 설명 |
|---|--------|------|------|
| 8 | BossDmgDealt | float | 보스가 가한 총 데미지 |
| 9 | PlayerDmgDealt | float | 플레이어가 가한 총 데미지 |
| 10 | BossHpLeft | float | 보스 잔여 HP 비율 (0~1) |
| 11 | P1HpLeft | float | P1 잔여 HP 비율 |
| 12 | P2HpLeft | float | P2 잔여 HP 비율 |
| 13 | BossHits | int | 보스 스킬 적중 횟수 |
| 14 | BossCasts | int | 보스 스킬 시전 횟수 |
| 15 | P1Hits | int | P1 스킬 적중 횟수 |
| 16 | P2Hits | int | P2 스킬 적중 횟수 |

#### 학습 지표 (17-23)

| # | 컬럼명 | 타입 | 설명 |
|---|--------|------|------|
| 17 | CumulativeReward | float | 에피소드 누적 보상 |
| 18 | FirstTouchP1 | float | P1 최초 접촉 시간 (초, 미접촉 시 -1) |
| 19 | FirstTouchP2 | float | P2 최초 접촉 시간 |
| 20 | P1DeathTime | float | P1 사망 시간 (생존 시 -1) |
| 21 | P2DeathTime | float | P2 사망 시간 |
| 22 | BossTravelDist | float | 보스 총 이동 거리 |
| 23 | UnlockedSkills | int | 해금된 스킬 수 |

#### 거리 지표 (24-32) - 행동 데이터

| # | 컬럼명 | 타입 | 설명 |
|---|--------|------|------|
| 24 | AvgDistBP1 | float | 보스-P1 평균 거리 (P1 생존 프레임만) |
| 25 | MinDistBP1 | float | 보스-P1 최소 거리 |
| 26 | MaxDistBP1 | float | 보스-P1 최대 거리 |
| 27 | AvgDistBP2 | float | 보스-P2 평균 거리 (P2 생존 프레임만) |
| 28 | MinDistBP2 | float | 보스-P2 최소 거리 |
| 29 | MaxDistBP2 | float | 보스-P2 최대 거리 |
| 30 | AvgDistP1P2 | float | P1-P2 평균 거리 (양쪽 생존 프레임만) |
| 31 | MinDistP1P2 | float | P1-P2 최소 거리 |
| 32 | MaxDistP1P2 | float | P1-P2 최대 거리 |

#### 공간 활용 (33-35) - 행동 데이터

| # | 컬럼명 | 타입 | 설명 |
|---|--------|------|------|
| 33 | BossAreaXZ | float | 보스 활동 면적 (XZ 바운딩 박스) |
| 34 | P1AreaXZ | float | P1 활동 면적 |
| 35 | P2AreaXZ | float | P2 활동 면적 |

#### 전투 판단 (36-41) - 행동 데이터

| # | 컬럼명 | 타입 | 설명 |
|---|--------|------|------|
| 36 | TargetSwitches | int | 타겟 전환 횟수 (P1<->P2) |
| 37 | IdleRatio | float | 대기 비율 (0~1) |
| 38 | FwdRatio | float | 전진 비율 (0~1) |
| 39 | RotRatio | float | 회전 비율 (좌+우, 0~1) |
| 40 | FacingRatio | float | 타겟 정면 응시 비율 (0~1) |
| 41 | CdWaitRatio | float | 전 스킬 쿨다운 대기 비율 (0~1) |

#### 기타 (42-43) - 행동 데이터

| # | 컬럼명 | 타입 | 설명 |
|---|--------|------|------|
| 42 | AvgCastDist | float | 평균 스킬 시전 거리 (시전 없으면 0) |
| 43 | WallTime | float | 벽 접촉 누적 시간 (초) |

> 컬럼 24~43은 행동 데이터 확장 이후 추가됨. 이전 데이터(~4,700ep)에는 해당 값이 없음.

## 3. 체크포인트 파일

| 확장자 | 용도 | 설명 |
|--------|------|------|
| `.pt` | 학습 재개 | PyTorch 가중치 + 옵티마이저 상태. `--resume` 또는 `--initialize-from`에 사용 |
| `.onnx` | 추론/배포 | Unity 런타임 추론용. `NNModel`에 할당하여 사용 |
| `checkpoint.pt` | 최신 상태 | 가장 마지막 학습 시점의 전체 상태 |

- 파일명의 숫자(예: `SkillIntro-1999953`)는 **학습 스텝 수**를 의미 (에피소드 아님)
- 플레이스타일별로 나뉘지 않음 - 하나의 모델이 모든 스타일에 대응

### 학습 재개 vs 초기화

```bash
# 이어서 학습 (옵티마이저 상태 유지)
mlagents-learn config.yaml --run-id=SkillIntro --resume

# 가중치만 가져오고 새로 학습 (다음 Phase 진행 시)
mlagents-learn config.yaml --run-id=NewPhase --initialize-from=SkillIntro
```

## 4. 분석 파이프라인 (analyze.py)

### 실행 방법

```bash
python results/SkillIntro_Comprehensive/analyze.py
```

### 데이터 전처리

1. CSV 읽기 시 `#`으로 시작하는 주석 행 제거
2. `Episode`로 시작하는 중복 헤더 행 제거
3. 43컬럼 헤더를 기준으로 통합 파싱 (구 데이터의 누락 컬럼은 NaN)
4. Episode 번호를 파일 순서대로 1부터 재부여 (중복 세션 번호 해결)
5. 수치 컬럼을 `pd.to_numeric(errors='coerce')`로 변환

### 출력 그래프 (16종)

| 파일명 | 내용 | 데이터 범위 |
|--------|------|------------|
| 1_winrate.png | 승률 추이 (50ep 이동평균) | 전체 |
| 2_reward.png | 누적 보상 추이 | 전체 |
| 3_hitrate.png | 스킬 적중률 추이 | 전체 |
| 4_duration.png | 전투 시간 추이 | 전체 |
| 5_boss_pool_winrate.png | 보스풀별 승률 | 전체 |
| 6_player_pool_winrate.png | 플레이어풀별 보스 승률 | 전체 |
| 7_end_reasons.png | 종료 사유 비율 (파이차트) | 전체 |
| 8_matchup_heatmap.png | 보스풀 x 플레이어풀 승률 | 전체 |
| 9_distance.png | 거리 추이 (평균 + 최소~최대 밴드) | 행동 데이터만 |
| 10_action_ratio.png | 행동 비율 추이 (스택 영역) | 행동 데이터만 |
| 11_combat_metrics.png | 타겟전환/정면비율/쿨대기 (3단) | 행동 데이터만 |
| 12_cast_area.png | 시전거리 + 활동영역 (2단) | 행동 데이터만 |
| 13_boss_pool_behavior.png | 보스풀별 행동 비교 (6종 bar) | 행동 데이터만 |
| 14_player_pool_behavior.png | 플레이어풀별 행동 비교 (6종 bar) | 행동 데이터만 |
| 15_win_vs_lose.png | 승리 vs 패배 행동 비교 | 행동 데이터만 |
| 16_distance_hist.png | 거리 분포 히스토그램 | 행동 데이터만 |

## 5. 데이터 백업 권장사항

- 학습 재시작 전 기존 CSV를 백업할 것 (덮어쓰기 없이 append이지만 안전을 위해)
- 체크포인트는 `--run-id` 디렉터리 하위에 자동 저장됨
- 장기 보관 시 `.pt` + `.onnx` + CSV + `configuration.yaml`을 함께 보관
