# 테네브리스 — 스킬 설계 문서

---

## 스킬 부품 목록 (37종)

| # | 분류 | 이름 | 시그니처 | 설명 |
|---|------|------|----------|------|
| 1 | 기본 전투 | 단일 피해 | `DealDamage(값)` | 대상 1명에게 기본 피해를 준다. 가장 기본이 되는 공격 처리 단위. |
| 2 | 기본 전투 | 다단 히트 | `DealMultiHitDamage(값, 타수)` | 같은 공격으로 여러 번 연속 피해를 준다. 연타형 스킬에 사용. |
| 3 | 기본 전투 | 지속 피해 | `ApplyDamageOverTime(지속시간, 초당데미지)` | 일정 시간 주기적으로 피해를 준다. 디버프나 장판형 효과에 사용. |
| 4 | 생존 | 체력 회복 | `RecoverHP(값)` | 즉시 체력을 회복한다. 회복 스킬, 퍼크, 보상 효과에 사용. |
| 5 | 생존 | 체력 재생 | `ApplyHPRegen(지속시간, 초당회복량)` | 일정 시간 체력을 서서히 회복한다. 생존 보조 버프에 적합. |
| 6 | 생존 | 방어막 획득 | `GainShield(값)` | 피해를 대신 흡수하는 방어막을 부여한다. |
| 7 | 생존 | 피해 반사 | `ReflectDamage(지속시간, 반사비율)` | 받은 피해의 일부를 공격자에게 되돌려준다. |
| 8 | 생존 | 무적 | `ApplyInvulnerability(지속시간)` | 일정 시간 피해를 받지 않는다. 패링 보상이나 긴급 생존 효과로 사용. |
| 9 | 상태 이상 | 스턴 | `ApplyStun(지속시간)` | 대상의 행동을 일정 시간 완전히 멈춘다. 강한 제어 효과. |
| 10 | 상태 이상 | 경직 | `ApplyHitStun(지속시간)` | 대상의 행동을 짧게 끊는다. 스턴보다 짧고 자주 사용. |
| 11 | 상태 이상 | 둔화 | `ApplySlow(지속시간, 감소비율)` | 이동속도 또는 행동속도를 감소시킨다. |
| 12 | 상태 이상 | 속박 | `ApplyRoot(지속시간)` | 일정 시간 동안 이동을 제한한다. |
| 13 | 상태 이상 | 취약 | `ApplyVulnerability(지속시간, 증가비율)` | 받는 피해를 증가시킨다. 협동 공격 타이밍 설계에 활용. |
| 14 | 상태 이상 | 침묵 | `ApplySilence(지속시간)` | 스킬 사용을 차단한다. |
| 15 | 능력 변화 | 공격력 증가 | `ApplyDamageUp(지속시간, 증가비율)` | 공격 피해량을 증가시킨다. |
| 16 | 능력 변화 | 공격력 감소 | `ApplyDamageDown(지속시간, 감소비율)` | 공격 피해량을 감소시킨다. |
| 17 | 능력 변화 | 방어력 증가 | `ApplyDefenseUp(지속시간, 증가비율)` | 받는 피해를 감소시킨다. |
| 18 | 능력 변화 | 방어력 감소 | `ApplyDefenseDown(지속시간, 감소비율)` | 받는 피해를 증가시킨다. |
| 19 | 능력 변화 | 치유 감소 | `ApplyAntiHeal(지속시간, 감소비율)` | 체력 회복 및 재생 효율을 감소시킨다. |
| 20 | 위치 제어 | 넉백 | `ApplyKnockback(거리)` | 대상을 뒤로 밀어낸다. |
| 21 | 위치 제어 | 끌어당기기 | `PullTarget(거리, 시간)` | 대상을 시전자 방향으로 끌어당긴다. |
| 22 | 위치 제어 | 자기 이동 | `MoveSelf(거리, 시간, 방식)` | 시전자를 지정 방향으로 이동시킨다. 대시/돌진/점프/로프 이동 가능. |
| 23 | 방어 대응 | 실드 파괴 | `DealShieldBreakDamage(값, 배율)` | 방어막에 추가 피해를 주고 우선 삭감한다. |
| 24 | 방어 대응 | 처형 피해 | `ExecuteBelowHP(체력비율, 추가피해)` | 대상 HP가 일정 이하일 때 추가 피해를 준다. |
| 25 | 방어 대응 | 정화 | `CleanseStatus(제거타입, 개수)` | 디버프/DoT/약화 효과를 제거한다. |
| 26 | 방어 대응 | 버프 제거 | `DispelBuff(제거타입, 개수)` | 대상의 강화 효과를 제거한다. |
| 27 | 전투 구조 | 버프 적용 | `ApplyBuff(지속시간, 버프종류, 값)` | 강화 효과를 부여한다. |
| 28 | 전투 구조 | 디버프 적용 | `ApplyDebuff(지속시간, 디버프종류, 값)` | 약화 효과를 부여한다. |
| 29 | 전투 구조 | 조건 발동 | `TriggerOnCondition(조건, 실행함수)` | 조건 만족 시 지정한 효과를 실행한다. |
| 30 | 전투 구조 | 적중 분기 | `TriggerOnHit(적중시, 빗나갈시)` | 적중 여부에 따라 다른 효과를 실행한다. |
| 31 | 범위 | 범위 적용 | `ApplyInArea(반경, 형태, 효과, 각도, 폭)` | 원형/부채꼴/직선 범위 내 대상에게 효과를 적용한다. |
| 32 | 범위 | 지속 장판 | `SpawnPersistentArea(지속시간, 반경, 형태, 틱간격, 효과)` | 유지되는 장판을 생성해 범위 내 대상에게 주기적으로 효과를 준다. |
| 33 | 범위 | 투사체 발사 | `LaunchProjectile(사거리, 속도, 관통, 폭발, 적중효과)` | 투사체를 발사해 적중 시 지정한 효과를 실행한다. |
| 34 | 방향 타격 | 방향 타격 | `DealDirectionalHit(피해, 사거리, 각도)` | 전방 부채꼴 범위에 즉시 근접 피해를 준다. 적중 여부를 기록해 분기 처리에 활용. |
| 35 | 패링 시스템 | 패링 판정 | `CheckParry()` | 패링 입력 유효 타이밍 내 성공 여부를 판정한다. 시전자 스탯의 패링 윈도우 참조. |
| 36 | 패링 시스템 | 패링 보상 | `ApplyParryReward(보상종류, 값, 지속시간)` | 패링 성공 시 반격/경직/무적/버프 보상을 부여한다. |
| 37 | 감지 | 거리 판정 | `CheckTargetDistance(최소거리, 최대거리)` | 대상과의 거리가 지정 범위 내인지 판정한다. |

---

## 공용 스킬 (플레이어)

| 구분 | 이름 | 사거리 유형 | 범위 크기 | 쿨타임 | 함수 |
|------|------|------------|----------|--------|------|
| 공격 | 처형 송곳 | 근거리 전방 타격 | 전방 2.4m / 부채꼴 70도 | 8초 | `34.DealDirectionalHit(125,2.0,30)` `30.TriggerOnHit([13.ApplyVulnerability(2,5), 24.ExecuteBelowHP(30,20)])` `29.TriggerOnCondition(NoHit,[34.DealDirectionalHit(125,2.4,70)])` |
| 공격 | 분쇄 연타 | 근거리 전방 연속 타격 | 전방 2.2m / 부채꼴 75도 | 6초 | `34.DealDirectionalHit(34,1.8,35)` `2.DealMultiHitDamage(34,4)` `30.TriggerOnHit([23.DealShieldBreakDamage(45,1.2)])` `29.TriggerOnCondition(NoHit,[34.DealDirectionalHit(34,2.2,75), 2.DealMultiHitDamage(34,4)])` |
| 공격 | 침식 장판 | 자동 유도 투사체 + 장판 | 사거리 10m / 반경 3.4m | 10초 | `33.LaunchProjectile(7,12,false,true,[32.SpawnPersistentArea(4,1.0,원,1,[3.ApplyDamageOverTime(1,8), 19.ApplyAntiHeal(1,20)]), 32.SpawnPersistentArea(4,3.4,원,1,[3.ApplyDamageOverTime(1,8)])])` |
| 제어 | 사냥 표식 | 자동 유도 투사체 | 사거리 11m / 단일 | 7초 | `33.LaunchProjectile(8,14,false,false,[1.DealDamage(80), 28.ApplyDebuff(4,Mark,1)])` |
| 방어 | 생존 맥동 | 자기중심 생존 | 본인 | 14초 | `29.TriggerOnCondition(LowHP,[4.RecoverHP(최대HP의6%), 5.ApplyHPRegen(3,최대HP의1.2%), 25.CleanseStatus(전체,1)])` |
| 방어 | 요새 장갑 | 근거리 전방 타격 | 전방 2.3m / 부채꼴 75도 | 8초 | `34.DealDirectionalHit(90,1.9,35)` `30.TriggerOnHit([6.GainShield(최대HP의6%)])` `29.TriggerOnCondition(NoHit,[34.DealDirectionalHit(90,2.3,75)])` |
| 유틸/제어 | 봉쇄 사슬 | 자동 유도 투사체 | 사거리 8m / 단일 | 9초 | `33.LaunchProjectile(8,13,false,false,[1.DealDamage(70), 10.ApplyHitStun(0.08), 14.ApplySilence(0.5)])` |
| 제어 | 붕괴 포효 | 근거리 범위공격 | 반경 4.0m / 본인 중심 | 10초 | `31.ApplyInArea(1.4,원,[1.DealDamage(95), 18.ApplyDefenseDown(2,5)])` `29.TriggerOnCondition(NoHit,[31.ApplyInArea(4.0,원,[1.DealDamage(95)])])` |
| 공격 | 방벽 파쇄 | 자동 유도 투사체 | 사거리 7m / 단일 | 8초 | `33.LaunchProjectile(7,12,false,false,[23.DealShieldBreakDamage(60,1.4), 18.ApplyDefenseDown(3,6), 1.DealDamage(105)])` |
| 특수 | 과충전 모드 | 자기강화 | 본인 | 18초 | `29.TriggerOnCondition(CombatPhaseOrLowHP,[15.ApplyDamageUp(6,15), 28.ApplyDebuff(6,SelfDefenseDown,10)])` |
| 공격 | 관통 저격 | 수동 직선 원거리 | 사거리 10m / 직선 폭 0.6m | 10초 | `33.LaunchProjectile(10,16,true,false,[18.ApplyDefenseDown(3,8), 1.DealDamage(165)])` `29.TriggerOnCondition(NoCoreHit,[33.LaunchProjectile(10,16,true,false,[1.DealDamage(165)])])` |
| 공격 | 파열 탄창 | 수동 투사체 원거리 | 사거리 8m / 폭발 반경 2.2m | 9초 | `33.LaunchProjectile(8,13,false,true,[13.ApplyVulnerability(3,10), 1.DealDamage(135)])` `29.TriggerOnCondition(NoCoreHit,[33.LaunchProjectile(8,13,false,true,[1.DealDamage(135)])])` |

---

## 플레이어 전용 트리거형 스킬

| 구분 | 이름 | 사거리 유형 | 범위 크기 | 쿨타임 | 함수 |
|------|------|------------|----------|--------|------|
| 방어 | 응수 태세 | 반응형 단일 | 패링 성공 대상 1명 | 8초 | `29.TriggerOnCondition(35.CheckParry(),[36.ApplyParryReward(반격,200,0), 36.ApplyParryReward(경직,0.20,0), 36.ApplyParryReward(무적,0.15,0)])` |
| 방어 | 패링 강화 | 자기강화 | 본인 | 12초 | `27.ApplyBuff(5,ParryWindowUp,15)` `27.ApplyBuff(5,ParryRewardUp,10)` |
| 공격 | 반격의 일섬 | 반응형 단일 | 패링 성공 대상 1명 | 10초 | `29.TriggerOnCondition(35.CheckParry(),[36.ApplyParryReward(반격,230,0), 36.ApplyParryReward(무적,0.15,0)])` |
| 유틸 | 와이어 훅 | 기동형 | 9m 이상 로프 이동 / 도착지 반경 1.2m | 6초 | `22.MoveSelf(9,시간,RopeMove)` `29.TriggerOnCondition(RopeLanding,[31.ApplyInArea(0.6,원,[1.DealDamage(80), 10.ApplyHitStun(0.08)]), 29.TriggerOnCondition(NoHit,[31.ApplyInArea(1.2,원,[1.DealDamage(80)])])])` |
| 유틸 | 로프 충격파 | 착지 범위공격 | 도착지 반경 1.8m | 9초 | `29.TriggerOnCondition(RopeLanding,[31.ApplyInArea(0.8,원,[1.DealDamage(75), 20.ApplyKnockback(1.2)]), 29.TriggerOnCondition(NoHit,[31.ApplyInArea(1.8,원,[1.DealDamage(75)])])])` |
| 특수 제어 | 붕괴 타격 | 근거리 전방 타격 | 전방 2.0m / 부채꼴 60도 | 18초 | `29.TriggerOnCondition(ParrySuccessRecent,[34.DealDirectionalHit(120,1.5,25), 30.TriggerOnHit([9.ApplyStun(0.35)]), 29.TriggerOnCondition(NoHit,[34.DealDirectionalHit(120,2.0,60)])])` |

---

## 공용 스킬 (보스)

| 구분 | 이름 | 사거리 유형 | 범위 크기 | 쿨타임 | 용도 | 함수 |
|------|------|------------|----------|--------|------|------|
| 공격 | 처형 송곳 | 근거리 전방 타격 | 전방 2.7m / 부채꼴 75도 | 8초 | 저체력 마무리 | `34.DealDirectionalHit(118,2.2,35)` `30.TriggerOnHit([13.ApplyVulnerability(2.5,6), 24.ExecuteBelowHP(30,26)])` `29.TriggerOnCondition(NoHit,[34.DealDirectionalHit(118,2.7,75)])` |
| 공격 | 분쇄 연타 | 근거리 전방 연속 타격 | 전방 2.5m / 부채꼴 80도 | 6초 | 실드/근접 압박 | `34.DealDirectionalHit(32,2.0,40)` `2.DealMultiHitDamage(32,4)` `30.TriggerOnHit([23.DealShieldBreakDamage(55,1.35)])` `29.TriggerOnCondition(NoHit,[34.DealDirectionalHit(32,2.5,80), 2.DealMultiHitDamage(32,4)])` |
| 공격 | 침식 장판 | 범위 패턴 | 반경 3.7m / 4초 지속 | 10초 | 위치 강제 | `32.SpawnPersistentArea(4,1.2,원,1,[3.ApplyDamageOverTime(1,7), 19.ApplyAntiHeal(1,20)])` `32.SpawnPersistentArea(4,3.7,원,1,[3.ApplyDamageOverTime(1,7)])` |
| 방어 | 생존 맥동 | 자기중심 생존 | 본인 | 14초 | 위기 복구 | `29.TriggerOnCondition(LowHP,[4.RecoverHP(최대HP의5%), 5.ApplyHPRegen(3,최대HP의1.0%), 25.CleanseStatus(전체,1)])` |
| 방어 | 요새 장갑 | 근거리 전방 타격 | 전방 2.6m / 부채꼴 80도 | 8초 | 생존 보강 | `34.DealDirectionalHit(82,2.1,35)` `30.TriggerOnHit([6.GainShield(최대HP의8%)])` `29.TriggerOnCondition(NoHit,[34.DealDirectionalHit(82,2.6,80)])` |
| 제어 | 붕괴 포효 | 근거리 범위공격 | 반경 4.4m / 본인 중심 | 10초 | 근접 압박 | `31.ApplyInArea(1.6,원,[1.DealDamage(88), 10.ApplyHitStun(0.16), 18.ApplyDefenseDown(3,6)])` `29.TriggerOnCondition(NoHit,[31.ApplyInArea(4.4,원,[1.DealDamage(88)])])` |
| 특수 | 과충전 모드 | 자기강화 | 본인 | 18초 | 페이즈 강화 | `29.TriggerOnCondition(CombatPhaseOrLowHP,[15.ApplyDamageUp(6,12), 28.ApplyDebuff(6,SelfDefenseDown,12)])` |
| 제어 | 표식 파동 | 중거리 전방 패턴 | 전방 5m / 부채꼴 80도 | 8초 | 표식 부여 | `31.ApplyInArea(5,부채꼴,[1.DealDamage(70), 28.ApplyDebuff(4,Mark,1)],80)` |
| 유틸/제어 | 봉쇄 사슬 | 4방향 원거리 패턴 | 사거리 7m / 4방향 | 10초 | 회피 강제 | `33.LaunchProjectile(7,11,false,false,[1.DealDamage(60), 10.ApplyHitStun(0.10), 14.ApplySilence(0.7)])` |
| 공격 | 방벽 파쇄 | 직선 원거리 패턴 | 사거리 8m / 직선 폭 0.8m | 9초 | 실드 카운터 | `33.LaunchProjectile(8,12,true,false,[1.DealDamage(90), 23.DealShieldBreakDamage(70,1.5), 18.ApplyDefenseDown(4,8)])` |
| 공격 | 파열 탄창 | 8방향 폭발 패턴 | 사거리 7m / 폭발 반경 1.8m | 9초 | 공간 압박 | `31.ApplyInArea(0.7,원,[33.LaunchProjectile(7,10,false,true,[13.ApplyVulnerability(2.5,6), 1.DealDamage(75)])])` `29.TriggerOnCondition(NoHit,[31.ApplyInArea(1.8,원,[33.LaunchProjectile(7,10,false,true,[1.DealDamage(75)])])])` |
