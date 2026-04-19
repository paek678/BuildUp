# 테네브리스 (Tenebris) — 기획 검증 프롬프트

## 게임 개요
- **장르**: 2인 협동 보스전 3D 탑다운 액션 로그라이트
- **구조**: Unity 6 + NGO Host-authoritative P2P
- **핵심 루프**: 드래프트(스킬 선택) → 보스전 → 반복

---

## 전투 시스템

### 스탯 관리
- **StatsManager** 가 유일한 스탯 변경 경로 (단일 진실 공급원)
- ScriptableObject(PlayerStatsSO/BossStatsSO)는 읽기 전용 초기값, Awake에서 Instantiate 복사본 사용
- 피해 → Shield 우선 소진 → HP 감소
- 회복 → HealingReceivedMultiplier 적용
- 상태이상/버프/디버프 → 코루틴 기반 자동 만료, 기존 효과는 덮어쓰기(갱신)

### 상태이상 12종
| 이름 | 효과 |
|------|------|
| Stunned | 이동+행동 불가 |
| HitStun | 짧은 경직 |
| Slowed | 이동속도 감소 (비율) |
| Rooted | 이동 불가, 행동 가능 |
| Vulnerable | 받는 피해 증가 |
| Silence | 스킬 사용 불가 |
| Invulnerable | 피해 무효 |
| Reflecting | 받는 피해를 공격자에게 반사 |
| HPRegen | 초당 HP 회복 (1초 틱) |
| DamageOverTime | 초당 피해 (1초 틱) |
| AntiHeal | 회복량 감소 |
| Marked | 추가 피해 취약 표식 |

### 버프 4종 / 디버프 4종
- **버프**: DamageUp, DefenseUp, ParryWindowUp, ParryRewardUp
- **디버프**: DamageDown, DefenseDown, SelfDefenseDown(자해형), Mark

### 패링 시스템
- 플레이어만 패링 가능 (보스는 패링 없음)
- 패링 성공 시 보상 4종: Counter(반격 피해), HitStun(경직 부여), Invulnerable(무적), Buff(공격력 증가)
- 피해 반사: Reflecting 상태 중 받은 피해의 일부를 공격자에게 되돌림

---

## 스킬 시스템

### 구조
```
SkillDefinition (ScriptableObject — 메타데이터)
  └─ RuntimeStep (SkillStep delegate — SkillLibrary에서 조립 후 주입)
       ├─ Primitive: DealDamage, ApplyStun, GainShield ...
       └─ Wrapper: ApplyInArea, SpawnPersistentArea, LaunchProjectile ...
```

- **SkillStep**: `delegate void(SkillContext ctx)` — 모든 부품의 공통 타입
- **SkillContext**: 시전자(Caster), 대상(PrimaryTarget), 위치/방향, 판정 결과(HitLanded) 등 런타임 정보

### 스킬 부품 37종 (SkillComponents.cs)

| 분류 | 부품들 |
|------|--------|
| 기본 전투 | DealDamage, DealMultiHitDamage, ApplyDamageOverTime, DealDirectionalHit |
| 생존 | RecoverHP, ApplyHPRegen, GainShield, ReflectDamage, ApplyInvulnerability |
| 상태이상 | ApplyStun, ApplyHitStun, ApplySlow, ApplyRoot, ApplyVulnerability, ApplySilence, ApplyAntiHeal |
| 능력 변화 | ApplyDamageUp/Down, ApplyDefenseUp/Down, ApplyBuff, ApplyDebuff |
| 위치 제어 | ApplyKnockback, PullTarget, MoveSelf |
| 방어 대응 | DealShieldBreakDamage, ExecuteBelowHP, CleanseStatus, DispelBuff |
| 패링 | CheckParry, ApplyParryReward |
| 범위/투사체 | ApplyInArea, SpawnPersistentArea, LaunchProjectile |
| 흐름 제어 | TriggerOnCondition, TriggerOnHit |
| 감지 | CheckTargetDistance |

### 적중 판정 방식
| 종류 | 방식 |
|------|------|
| 즉발 근접 | DealDirectionalHit → OverlapSphere + 각도 필터 |
| 범위 | ApplyInArea → OverlapSphere + shape(Circle/Cone/Line) 필터 |
| 지속 장판 | SpawnPersistentArea → 틱마다 OverlapSphere |
| 투사체 | LaunchProjectile → OnTriggerEnter 충돌 이벤트 (예외) |

---

## 스킬 목록

### 플레이어 공용 (13종)
| 이름 | 유형 | 쿨타임 | 핵심 효과 |
|------|------|--------|----------|
| 처형 송곳 | 전방 타격 | 8초 | 125 피해, 적중 시 취약+처형(30%이하 +20) |
| 분쇄 연타 | 전방 연타 | 6초 | 34×4 다단, 적중 시 실드파괴 |
| 침식 장판 | 투사체→장판 | 10초 | 착탄 지점 2중 장판 (DoT+치유감소) |
| 사냥 표식 | 유도 투사체 | 7초 | 80 피해 + Mark 디버프 |
| 생존 맥동 | 자기 생존 | 14초 | 저체력 조건 → 회복+재생+정화 |
| 요새 장갑 | 전방 타격 | 8초 | 90 피해, 적중 시 실드 획득 |
| 봉쇄 사슬 | 유도 투사체 | 9초 | 70 피해 + 경직 + 침묵 |
| 붕괴 포효 | 범위 공격 | 10초 | 95 피해 + 방어력 감소 |
| 방벽 파쇄 | 유도 투사체 | 8초 | 실드파괴 + 방어감소 + 105 피해 |
| 과충전 모드 | 자기 강화 | 18초 | 공격력↑ + 자기 방어력↓ (리스크형) |
| 관통 저격 | 관통 투사체 | 10초 | 165 피해 + 방어감소, 관통 |
| 파열 탄창 | 폭발 투사체 | 9초 | 135 피해 + 취약, 폭발 범위 |

### 플레이어 전용 트리거형 (6종)
| 이름 | 유형 | 쿨타임 | 핵심 효과 |
|------|------|--------|----------|
| 응수 태세 | 패링 반응 | 8초 | 패링 성공 → 반격200+경직+무적 |
| 패링 강화 | 자기 버프 | 12초 | 패링 윈도우↑ + 보상 강화 |
| 반격의 일섬 | 패링 반응 | 10초 | 패링 성공 → 반격230+무적 |
| 와이어 훅 | 로프 기동 | 6초 | 9m 로프 이동 + 착지 범위 피해 |
| 로프 충격파 | 착지 범위 | 9초 | 착지 범위 피해 + 넉백 |
| 붕괴 타격 | 패링 후 타격 | 18초 | 최근 패링 성공 조건 → 120 피해 + 스턴 |

### 보스 공용 (12종)
| 이름 | 유형 | 쿨타임 | 핵심 효과 | 플레이어 버전과의 차이 |
|------|------|--------|----------|----------------------|
| 처형 송곳 | 전방 타격 | 8초 | 118 피해 + 취약 + 처형 | 범위↑ 피해↓ |
| 분쇄 연타 | 전방 연타 | 6초 | 32×4 + 실드파괴 | 범위↑ 실드파괴↑ |
| 침식 장판 | 즉발 장판 | 10초 | 2중 장판 (DoT+치유감소) | 투사체 없이 즉시 생성 |
| 생존 맥동 | 자기 생존 | 14초 | 회복+재생+정화 | 회복량↓ |
| 요새 장갑 | 전방 타격 | 8초 | 82 피해 + 실드 획득 | 실드 비율↑ |
| 붕괴 포효 | 범위 공격 | 10초 | 88 피해 + 경직 + 방어감소 | 경직 추가 |
| 과충전 모드 | 자기 강화 | 18초 | 공격력↑ + 방어력↓ | 수치 조정 |
| 표식 파동 | 전방 부채꼴 | 8초 | 70 피해 + Mark | 보스 전용 |
| 봉쇄 사슬 | 4방향 투사체 | 10초 | 60 피해 + 경직 + 침묵 | 4방향 발사 |
| 방벽 파쇄 | 관통 투사체 | 9초 | 90 피해 + 실드파괴 + 방어감소 | 관통 |
| 파열 탄창 | 8방향 폭발 | 9초 | 75 피해 + 취약 | 8방향 패턴 |

---

## 카운터 관계 (가위바위보)

| 플레이어 빌드 계열 | 보스가 뽑아야 할 카운터 |
|---|---|
| Heal | AntiHeal |
| Shield | ShieldBreak |
| Parry | MultiHit, DOT, Zone |
| Mobility | Root, Pull, Catch |
| Burst | Invulnerable, Reflect, DefenseUp |
| Zone | Cleanse, Mobility |

- 드래프트: 플레이어가 스킬 3~4개 중 선택 → 보스 AI가 플레이어 선택 태그 기반으로 카운터 스킬 선택

---

## 보스 AI 계획

### FSM 구조
`Idle → Approach → AttackPattern → Cooldown → 반복`
- HP% 기반 페이즈 전환 (예: 75%, 50%, 25%)
- 페이즈마다 속도/패턴 강화

### AI 구현 단계
1. FSM + 규칙 기반 (현재 목표)
2. 플레이어 행동 편향 수집 → 패턴 가중치 적용
3. ML-Agents PPO (보스 이동/위치 학습, 스킬 발동은 규칙 유지)

### 행동 편향 분류 (9종)
근접 선호 / 원거리 유지 / 공격 집중 / 생존 우선 / 패링 의존 / 로프 기동 / 스킬 중심 / 팀 밀착 / 팀 분산

---

## 네트워크 판정 흐름

```
클라이언트: 스킬 입력 → ServerRpc
호스트: 위치 참조 → 범위 판정 → TakeDamage/ApplyStatus → NetworkVariable 동기화
클라이언트: 시각 피드백만 담당
```
- 클라이언트는 판정 권한 없음
- 투사체는 NetworkObject로 호스트 소유

---

## 현재 상태 요약

| 항목 | 상태 |
|------|------|
| 스탯/전투 시스템 | 완료 |
| 스킬 부품 37종 | 완료 |
| 스킬 조립 (SkillLibrary) | 2/31종 |
| 3D 전투 통합 (입력→스킬 실행) | 미완성 |
| 보스 FSM / 패턴 | 미완성 |
| 드래프트 ↔ 스킬 연결 | 미완성 |
| 보스전 UI | 미완성 |
