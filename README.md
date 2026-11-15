# 테네브리스(Tenebris) | 보스 이동 AI 학습

보스가 두 플레이어를 상대할 때 **언제 전진하고, 돌아서고, 물러날지** 학습하는 Unity 프로젝트입니다. 서로 다른 전투 성향을 가진 플레이어 봇 두 명을 상대로 전투를 반복하고, 학습한 이동 모델을 [테네브리스 게임 실행 프로젝트](https://github.com/paek678/ArenaCombat_server)에 전달합니다.

## 학습 환경 실행 화면

![학습용 보스와 두 플레이어 봇이 함께 교전하는 Unity 실행 화면](docs/screenshots/training-environment.png)

큰 캐릭터가 학습 대상 보스, 작은 두 캐릭터가 플레이어 봇입니다. 사진은 저장된 `BossInference-418782` ONNX 모델을 학습 환경에 지정해 이동 추론을 실행한 장면입니다. 촬영 당시 Unity 6000.3.28f1에서 일부 이펙트의 셰이더 표시 문제로 공격 범위가 분홍색으로 나타났습니다.

## 보스는 무엇을 학습하나요?

| 단계 | 내용 |
| --- | --- |
| 전투 관찰 | 두 봇과 보스의 상대 위치·거리, 체력, 스킬 상태 등을 **129개 관측값**으로 입력합니다. |
| 이동 선택 | 관측값을 바탕으로 **대기·전진·좌회전·우회전·후진** 중 하나를 고릅니다. |
| 반복 학습 | Unity ML-Agents의 **PPO** 알고리즘으로 이동 정책을 학습하고, 에피소드별 승패·전투 시간·이동 행동 비율을 CSV에 기록합니다. |
| 게임에 적용 | 학습한 정책을 **ONNX 모델**로 내보냅니다. 게임에서는 두 플레이어의 성향 조합에 맞는 모델을 선택해 이동을 결정합니다. 스킬 선택과 피해 판정은 게임의 전투 로직이 담당합니다. |

## 관측값·이동 모델과 플레이어 봇 설정

![보스의 Behavior Parameters에 지정된 129개 관측값, 5개 이산 이동 행동과 ONNX 모델](docs/screenshots/observation-action-model.png)

보스의 `Behavior Parameters`에는 관측값 크기 129, 이산 행동 분기 1개와 행동 수 5, 추론에 사용할 ONNX 모델을 지정합니다. 입력받은 전투 정보를 다섯 가지 이동 행동 중 하나로 연결하는 설정입니다.

![플레이어 봇에 연결된 Behavior Graph와 행동 변수](docs/screenshots/player-bot-behavior.png)

플레이어 봇은 `Behavior Graph Agent`에 연결된 행동 그래프를 실행합니다. 보스와의 교전 거리와 스킬 사용 등 봇의 전투 행동을 구성해, 서로 다른 성향 조합을 상대로 이동 정책을 학습하는 환경을 만듭니다.

## 학습 결과 | 상대 조합에 따라 이동은 어떻게 달랐나요?

2026년 5월 25일 분석에서는 **봇 성향 5개 조합, 총 2,585에피소드**의 전투 기록을 비교했습니다. 보스의 후진 비율은 **혼합형 + 군중제어형** 조합에서 **14.9%**, **원거리형 + 원거리형** 조합에서 **47.9%**였습니다. 아래 그림은 이 학습 구간에서 기록한 행동 비율이며, 좌회전과 우회전은 ‘회전’으로 묶었습니다.

![다섯 봇 조합별 보스의 대기·전진·회전·후진 비율. 후진 비율은 혼합형과 군중제어형 조합에서 14.9%, 원거리형 두 명 조합에서 47.9%이다.](docs/figures/boss-movement-by-matchup.png)

[조합별 에피소드 수와 승률](docs/portfolio/training-analysis.md) · [행동 비율과 전투 결과 분석 원문](TRAINING_ANALYSIS.md)

## 학습 산출물

| 자료 | 확인할 내용 |
| --- | --- |
| [PPO 학습 설정](BossInference_config.yaml) · [학습 코드](Assets/Scripts/AI/BossAI/) | 보스 에이전트와 관측값 수집, 학습 설정 |
| [에피소드 기록](results/) | 봇 조합별 전투 결과와 행동 비율을 기록한 CSV |
| [학습한 ONNX 모델](onnx_9matchup/) | 게임에서 불러올 수 있도록 내보낸 이동 모델 |
| [게임 내 모델 선택 코드](https://github.com/paek678/ArenaCombat_server/blob/main/Assets/ArenaCombat/Scripts/Core/AI/BossAIPoolManager.cs) | 두 플레이어의 성향 조합에 따라 호스트가 이동 모델을 선택·교체하는 과정 |

학습 환경은 Unity 6000.3.11f1과 ML-Agents 4.0.2를 사용합니다. 관측값의 구성, 행동 번호, 학습·실행 환경의 후진 속도 차이는 [관측값과 행동 규격](docs/portfolio/observation-action-spec.md)에 정리했습니다. [학습 프로젝트 개요](docs/portfolio/overview.md)
