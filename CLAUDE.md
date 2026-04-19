# 테네브리스 (Tenebris) — Claude 작업 지침

전체 기획 및 기술 설계는 [GAME_DESIGN.md](GAME_DESIGN.md) 참조.
상태 FSM 설계는 [STATE_MANAGER_DESIGN.md](STATE_MANAGER_DESIGN.md) 참조.

---

## 핵심 원칙 (항상 준수)

- **모든 스탯 변경 → StatManager 경유** (직접 필드 수정 금지)
- **새 스킬 부품 → SkillComponents.cs에만 추가**
- **새 전투 객체 → ICombatant 먼저 구현**
- **SO는 읽기 전용** — 런타임 수치 변경 금지
- **2D 레거시 코드 기준 금지** — 3D + Host-authoritative 경로 기준만
- **UniTask 미설치** — 코루틴 사용, `WaitForSeconds` 반드시 캐싱
- **Addressables 미설치** — `[SerializeField] private` 직접 참조

---

## 구현 시 Skill 파일 참조 규칙

작업 유형에 맞는 skill 파일을 **구현 전에 읽고** 해당 규칙을 따를 것.

| 작업 유형 | 읽을 Skill 파일 |
|-----------|----------------|
| 코딩 스타일 / 네이밍 / 리팩토링 | [unified-style-guide](skills/00-core-engineering/unified-style-guide/SKILL.md) |
| CS 컴파일 에러 수정 | [unity-compile-fixer](skills/00-core-engineering/unity-compile-fixer/SKILL.md) |
| 이벤트 시스템 구현 (어택/패링/페이즈) | [event-bus-system](skills/01-architecture/event-bus-system/SKILL.md) |
| 투사체 / 장판 풀링 | [object-pooling-system](skills/06-performance/object-pooling-system/SKILL.md) |
| 새 인터페이스 설계 (IProjectile 등) | [interface-driven-development](skills/01-architecture/interface-driven-development/SKILL.md) |
| ScriptableObject 추가 / 수정 | [scriptableobject-architecture](skills/01-architecture/scriptableobject-architecture/SKILL.md) |
| 입력 처리 / 키 바인딩 | [input-system-new](skills/05-ui-ux/input-system-new/SKILL.md) |
| 코루틴 / async 작업 | [asynchronous-programming](skills/01-architecture/asynchronous-programming/SKILL.md) |
| 매니저 초기화 순서 / Bootstrap | [advanced-game-bootstrapper](skills/01-architecture/advanced-game-bootstrapper/SKILL.md) |
| UI 작업 (현재 UGUI 기준) | [ui-toolkit-modern](skills/05-ui-ux/ui-toolkit-modern/SKILL.md) |

---



## 변경 이력 추적

스크립트 수정 시 [CHANGES.md](Assets/CHANGES.md) 업데이트.

---

## 교차 검증 워크플로우 (필수)

모든 기획, 설계, 코드 변경 계획은 **구현 전에 반드시 Codex 교차 검증**을 거쳐야 한다.

1. Claude Code가 기획/설계/변경 계획을 작성한다
2. 사용자에게 **Codex에 전달할 검증용 프롬프트**를 함께 출력한다
3. 사용자가 Codex의 승인/수정/거부 결과를 가져온다
4. 승인된 내용만 구현을 진행한다

**검증용 프롬프트에 포함할 내용:**
- 변경 대상 파일과 변경 범위
- 변경 사유와 의도
- 핵심 원칙 준수 여부 자체 점검 결과
- 기존 시스템과의 충돌/영향 분석
- Codex에게 승인/수정/거부 판단을 요청하는 문구

**예외:** 단순 오타 수정, CHANGES.md 업데이트, 문서만의 수정은 교차 검증 없이 진행 가능

---

## 병행 작업 환경

- **Claude Code + OpenAI Codex 병행 사용 중**
- 어느 쪽에서 작업하든 모든 변경점, 질문, 결정 사항을 [CHANGES.md](Assets/CHANGES.md)에 기록할 것
- 다른 AI가 수정한 코드를 이어받을 수 있으므로, 변경 의도와 맥락을 명확히 남길 것
- 작업 전 반드시 CHANGES.md를 읽어 최근 변경사항을 파악한 뒤 진행
