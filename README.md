# 테네브리스(Tenebris) | 보스 이동 AI 학습

보스가 두 플레이어를 상대할 때 **언제 전진하고, 돌아서고, 물러날지** 학습하는 Unity 프로젝트입니다. 서로 다른 전투 성향을 가진 플레이어 봇 두 명을 상대로 전투를 반복하고, 학습한 이동 모델을 [테네브리스 게임 실행 프로젝트](https://github.com/paek678/ArenaCombat_server)에 전달합니다.

## 학습 환경 실행 화면

![학습용 보스와 두 플레이어 봇이 함께 교전하는 Unity 실행 화면](docs/screenshots/training-environment.png)

BuildUp은 멀티플레이 접속과 화면 연출 부담을 줄이기 위해 보스 이동 학습을 별도 Unity 씬에서 진행합니다. 두 플레이어 봇과 보스의 교전을 반복하며 이동·공격·스킬 판정에 필요한 전투 상태를 수집합니다. 혼합형·군중제어형 조합의 학습 설정은 화면 크기 84×84와 시뮬레이션 시간 배율 20을 사용해 화면 출력 부담을 낮추고 대전을 빠르게 반복하도록 구성했습니다. [학습 실행 설정](results/BossInference_Hybrid_CC/configuration.yaml)

위 화면은 저장된 ONNX 모델을 적용해 보스의 이동과 두 플레이어 봇의 교전을 확인한 장면입니다.

## 보스는 무엇을 학습하나요?

| 단계 | 내용 |
| --- | --- |
| 전투 관찰 | 두 봇과 보스의 상대 위치·거리, 체력, 스킬 상태 등을 **129개 관측값**으로 입력합니다. |
| 이동 선택 | 관측값을 바탕으로 **대기·전진·좌회전·우회전·후진** 중 하나를 고릅니다. |
| 반복 학습 | Unity ML-Agents의 **PPO** 알고리즘으로 이동 정책을 학습하고, 에피소드별 승패·전투 시간·이동 행동 비율을 CSV에 기록합니다. |
| 게임에 적용 | 학습한 정책을 **ONNX 모델**로 내보냅니다. 게임에서는 두 플레이어의 성향 조합에 맞는 모델을 선택해 이동을 결정합니다. 스킬 선택과 피해 판정은 게임의 전투 로직이 담당합니다. |

## 아키텍처

![BuildUp의 봇 대전, 관측·보상, PPO와 에피소드 기록, ArenaCombat_server의 ONNX 모델 선택·추론을 연결한 아키텍처](docs/figures/training-architecture.png)

1. **Unity 학습 환경** — 플레이어 봇 두 명과 보스가 전투를 반복합니다. 위치·거리·체력·스킬 상태를 관측하고, 이동과 전투 결과에 따라 보상 및 에피소드 종료 여부를 계산합니다.
2. **ML-Agents PPO** — 보스는 129개 관측값을 바탕으로 다섯 가지 이동 행동 중 하나를 선택합니다. PPO 학습기는 대전에서 수집한 보상을 이용해 이동 정책을 갱신합니다.
3. **CSV 기록 · ONNX 출력** — 에피소드별 승패·전투 시간·행동 비율은 분석용 CSV로 보관하고, 학습한 이동 정책은 ONNX 모델로 내보냅니다.
4. **게임 호스트** — ArenaCombat_server는 두 플레이어의 성향 조합에 맞는 모델을 선택하고, 현재 전투 상태를 입력해 보스의 다음 이동을 추론합니다. 대응 스킬과 피해는 호스트의 전투 로직에서 처리합니다.

[관측값과 행동 규격](docs/portfolio/observation-action-spec.md) · [학습 결과 분석](docs/portfolio/training-analysis.md)

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

## 팀원

<div align="center">
<table>
  <thead>
    <tr>
      <th>백성열</th>
      <th>홍채영</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center">
        <a href="https://github.com/paek678"><img src="https://avatars.githubusercontent.com/paek678?size=150" width="150" height="150" alt="백성열 GitHub 프로필 사진"></a>
        <br><a href="https://github.com/paek678">@paek678</a>
      </td>
      <td align="center">
        <a href="https://github.com/hongchaeyoung0918-code"><img src="https://avatars.githubusercontent.com/hongchaeyoung0918-code?size=150" width="150" height="150" alt="홍채영 GitHub 프로필 사진"></a>
        <br><a href="https://github.com/hongchaeyoung0918-code">@hongchaeyoung0918-code</a>
      </td>
    </tr>
    <tr>
      <td align="center">기획 · 서버 구축 · 몬스터 AI 구현</td>
      <td align="center">클라이언트 개발 · 서버 연결 · 셰이더 추가</td>
    </tr>
  </tbody>
</table>
</div>
