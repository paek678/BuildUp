---
name: scriptableobject-architecture
description: "Senior Architect for Data-Driven Design using ScriptableObjects. Create SO-based event channels, runtime sets, and configuration data."
argument-hint: "type='event' name='OnPlayerDamaged' OR type='data' name='WeaponConfig'"
disable-model-invocation: false
user-invocable: true
---

# ScriptableObject Architecture

## Overview
Decouple gameplay data and signals from MonoBehaviour logic using ScriptableObjects as the "Single Source of Truth" for design constants and event broadcasting.

## When to Use
- Use when creating inspector-configurable game data (stats, costs, timings)
- Use when implementing SO-based event channels (alternative to static EventBus)
- Use when tracking active objects without GameObject.Find (Runtime Sets)
- Use when sharing data between scenes or objects
- Use when designers need to tweak values without code changes

## Architecture

### Data-Driven Configuration
```
┌─────────────────────────────────────────────────────────────┐
│                    ScriptableObject Asset                   │
│                     (WeaponConfigSO)                        │
├─────────────────────────────────────────────────────────────┤
│  [SerializeField] private float _damage = 10f;              │
│  [SerializeField] private float _fireRate = 0.5f;           │
│  [SerializeField] private GameObject _projectilePrefab;     │
│                                                             │
│  public float Damage => _damage;                            │
│  public float FireRate => _fireRate;                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
      Shared by multiple weapons without duplication
```

### Event Channels
```
┌──────────────┐           ┌──────────────────┐
│   Trigger    │  Raise()  │   GameEventSO    │
│ (Door opens) │ ─────────→│ (OnDoorOpened)   │
└──────────────┘           └────────┬─────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              ↓                     ↓                     ↓
      ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
      │  AudioManager │    │  UI Manager   │    │  Quest System │
      │  (Listener)   │    │  (Listener)   │    │  (Listener)   │
      └───────────────┘    └───────────────┘    └───────────────┘
```

## Components

| Component | Purpose |
|-----------|---------|
| `GameEventSO` | SO-based event for inspector-assignable broadcasts |
| `GameEventListener` | MonoBehaviour that listens to GameEventSO |
| `RuntimeSetSO<T>` | Dynamic collection of active objects |
| `ConfigSO` | Base for configuration data containers |

## Best Practices
- ✅ Use `[SerializeField] private` with public getters
- ✅ Include validation attributes (`[Range]`, `[Min]`)
- ✅ Use `[CreateAssetMenu]` with hierarchical paths
- ✅ Reset runtime data in `OnDisable` for editor play mode
- ✅ Keep SO as data containers, NOT execution logic
- ❌ **NEVER** put Update loops in ScriptableObjects
- ❌ **NEVER** store direct MonoBehaviour references in persistent SOs
- ❌ **NEVER** use heavy assets (textures) directly (use AssetReference)

## Few-Shot Examples

### Example 1: Weapon Configuration
**User**: "Create configurable weapon stats for the RPG."

**Agent**:
```csharp
[CreateAssetMenu(menuName = "Game/Combat/WeaponConfig")]
public class WeaponConfigSO : ScriptableObject
{
    [Header("Damage")]
    [SerializeField, Min(1)] private float _baseDamage = 10f;
    [SerializeField] private DamageType _damageType;
    
    [Header("Timing")]
    [SerializeField, Range(0.1f, 2f)] private float _attackSpeed = 1f;
    
    public float BaseDamage => _baseDamage;
    public DamageType DamageType => _damageType;
    public float AttackSpeed => _attackSpeed;
}
```

### Example 2: SO Event Channel
**User**: "Door should play sound and update UI without coupling."

**Agent**:
```csharp
// 1. Create GameEventSO asset "OnDoorOpened"
// 2. Door.cs calls: _onDoorOpenedEvent.Raise();
// 3. AudioManager has GameEventListener pointing to same SO
// 4. UI has another GameEventListener pointing to same SO
```

### Example 3: Runtime Set
**User**: "Track all active enemies for wave completion check."

**Agent**:
```csharp
[CreateAssetMenu(menuName = "Game/Runtime/EnemySet")]
public class EnemyRuntimeSetSO : RuntimeSetSO<Enemy> { }

// Enemy.cs
void OnEnable() => _enemySet.Add(this);
void OnDisable() => _enemySet.Remove(this);

// WaveManager.cs
bool IsWaveComplete => _enemySet.Count == 0;
```



---

## TDD Contract

> ⚠️ **Legacy Skill — Refactor Pending**
> Este skill NO tiene tests automatizados aún. El siguiente boilerplate es un punto de partida.

```csharp
// Escribe estos tests ANTES de implementar:

// Test 1: should [expected behavior] when [condition]
[Test]
public void ScriptableobjectArchitecture_Should{ExpectedBehavior}_When{Condition}()
{{
    // Arrange
    // TODO: Setup test fixtures
    
    // Act
    // TODO: Execute system under test
    
    // Assert
    Assert.Fail("Not implemented — write test first");
}}

// Test 2: should handle [edge case]
[Test]
public void ScriptableobjectArchitecture_ShouldHandle{EdgeCase}()
{{
    // Arrange
    // TODO: Setup edge case scenario
    
    // Act
    // TODO: Execute
    
    // Assert
    Assert.Fail("Not implemented");
}}

// Test 3: should throw when [invalid input]
[Test]
public void ScriptableobjectArchitecture_ShouldThrow_When{InvalidInput}()
{{
    // Arrange
    var invalidInput = default;
    
    // Act & Assert
    Assert.Throws<Exception>(() => {{ /* execute */ }});
}}
```

### Pasos para completar el TDD:

1. **Descomenta** los tests above
2. **Implementa** la funcionalidad mínima para que compile
3. **Ejecuta** los tests — deben fallar (RED)
4. **Implementa** la funcionalidad real
5. **Verifica** que los tests pasen (GREEN)
6. **Refactorea** manteniendo los tests verdes

---

**Nota**: Este skill fue marcado como `tdd_first: false` durante la auditoría v2.0.1. La sección TDD fue agregada automáticamente pero requiere customización manual para reflejar el comportamiento real del skill.


## Related Skills
- `@event-bus-system` - Static alternative to SO events
- `@advanced-design-patterns` - Patterns using SO data
- `@di-container-manager` - Injecting SO dependencies

## Template Files
- `templates/GameEventSO.cs.txt` - Event channel
- `templates/GameEventListener.cs.txt` - Event listener
- `templates/RuntimeSetSO.cs.txt` - Active object tracking

## Tenebris 프로젝트 적용 규칙

### 확정 SO 구조

```
PlayerStatsSO  (읽기 전용 초기값 — ScriptableObject)
  └─ StatsManager.currentPlayerStats  (런타임 복사본 — 여기서만 변경)

BossStatsSO    (읽기 전용 초기값 — ScriptableObject)
  └─ StatsManager.currentBossStats    (런타임 복사본 — 여기서만 변경)
```

### 규칙
- SO에는 Update/수치 변경 로직 절대 없음 — 데이터 컨테이너 역할만
- 런타임 수치 변경은 반드시 StatsManager 전용 메서드 경유
- 씬 종료 시 SO 원본은 오염되지 않음 (StatsManager가 Awake에서 복사본 생성)
- SO에 MonoBehaviour 직접 참조 저장 금지

### 향후 스킬 SO 확장 시 동일 패턴 적용
- SkillDefinitionSO (읽기 전용 조합 데이터) → SkillRegistry (런타임 참조 테이블)