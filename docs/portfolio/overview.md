# 프로젝트 개요

BuildUp은 Unity ML-Agents PPO를 사용하여 2인 협동 보스전의 보스 이동 정책을 학습하는 프로젝트입니다. 반복 학습, 플레이어 성향 조합별 분석, ONNX 모델 출력은 실제 멀티플레이 게임 실행 환경과 분리하여 관리합니다.

## 프로젝트 역할

| 프로젝트 | 담당 영역 |
| --- | --- |
| BuildUp | 학습 환경, 플레이어 봇, 이동 정책 학습, 결과 분석, ONNX 모델 출력 |
| ArenaCombat_server | 멀티플레이 권한, 전투 판정, 스킬 실행, 이동 정책 추론 |

## 학습 과정

Behavior Tree 기반 플레이어 봇이 보스의 상대 역할을 수행합니다. `BossInferenceAgent`는 기초 접근(Touch), 교전 위치 선정(Engage), 전투(Combat) 학습 모드를 지원하며, 129개 관측값과 5개 행동으로 구성된 단일 이산 이동 분기를 사용합니다.

학습된 정책은 이동을 제어합니다. 스킬 실행은 학습 환경의 자동 시전 도우미가 별도로 처리합니다. 출력한 ONNX 모델은 ArenaCombat_server 실행 환경에 지정하여 사용할 수 있습니다.

## 관련 코드 및 문서

- [관측값과 행동 규격](observation-action-spec.md)
- [학습 결과 분석](training-analysis.md)
- [학습 에이전트](../../Assets/Scripts/AI/BossAI/Agents/BossInferenceAgent.cs)
- [관측값 수집기](../../Assets/Scripts/AI/BossAI/Observation/BossObservationCollector.cs)
- [전투 학습 설정](../../BossInference_config.yaml)
- [학습 환경 변경 이력](../../Assets/CHANGES.md)
- [ArenaCombat_server 저장소](https://github.com/paek678/ArenaCombat_server)

## 실행 환경과의 정합성 및 검증

학습 환경과 실제 실행 환경은 관측값 순서, 정규화 방식, 행동 인덱스, 이동 동작이 일치해야 합니다. 현재 확인된 후진 속도 차이는 [관측값과 행동 규격](observation-action-spec.md#runtime-alignment)에 기록되어 있습니다.

저장소에는 학습 결과와 출력한 모델이 포함되어 있습니다. 최종 모델 선정, 실제 2인 네트워크 세션에서의 동작, 전투 밸런스는 실행 환경에서 별도로 검증해야 합니다.
