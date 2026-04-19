---
name: event-bus-system
description: "Implements a global decoupled Event Bus for cross-system communication. Zero-allocation struct events prevent GC spikes."
argument-hint: "event_name='PlayerDamaged' namespace='Game.Events'"
disable-model-invocation: false
user-invocable: true
---

# Event Bus System

## Overview
Implement global decoupled communication between systems using a static Event Bus. Uses struct-based events to avoid garbage collection allocations during gameplay.

## When to Use
- Use when systems need to communicate without direct references
- Use when implementing publish-subscribe patterns
- Use when reducing dependencies between unrelated systems
- Use when broadcasting global game events (PlayerDied, LevelCompleted)
- Use when UI needs to react to gameplay without coupling

## Architecture

```
┌──────────────┐    Publish(event)    ┌──────────────┐
│   Player     │ ───────────────────→ │   EventBus   │
│  (Publisher) │                      │   (Static)   │
└──────────────┘                      └───────┬──────┘
                                              │
              ┌───────────────────────────────┼───────────────────────────────┐
              ↓                               ↓                               ↓
      ┌───────────────┐              ┌───────────────┐              ┌───────────────┐
      │   HealthUI    │              │ AchievementSys│              │   Analytics   │
      │  (Subscriber) │              │  (Subscriber) │              │  (Subscriber) │
      └───────────────┘              └───────────────┘              └───────────────┘
```

## Components

| Component | Purpose |
|-----------|---------|
| `IEvent` | Marker interface for all events |
| `EventBus` | Static class handling subscriptions |
| `GameEvents.cs` | Collection of event struct definitions |
| `EventListenerBase<T>` | Abstract MonoBehaviour for automatic lifecycle |

## Procedure
1. **Define Events**: Create structs implementing `IEvent`
2. **Publish Events**: Call `EventBus.Publish(new YourEvent { ... })`
3. **Subscribe**: Call `EventBus.Subscribe<YourEvent>(HandleEvent)` in `OnEnable`
4. **Unsubscribe**: Call `EventBus.Unsubscribe<YourEvent>(HandleEvent)` in `OnDisable`

## Best Practices
- ✅ Use **structs** for events (zero allocation)
- ✅ Keep events immutable (readonly fields)
- ✅ ALWAYS unsubscribe in `OnDisable` or `OnDestroy`
- ✅ Use `EventListenerBase<T>` for automatic lifecycle
- ✅ Group related events in single file (e.g., `CombatEvents.cs`)
- ❌ **NEVER** forget to unsubscribe (causes memory leaks)
- ❌ **NEVER** use events for high-frequency per-frame logic
- ❌ **NEVER** put heavy logic in event handlers (defer to next frame if needed)

## Event Definition Guidelines

```csharp
// GOOD: Struct with relevant data
public struct EnemyKilledEvent : IEvent
{
    public readonly int EnemyId;
    public readonly Vector3 Position;
    public readonly int ExperienceReward;
}

// BAD: Class (causes allocation)
public class EnemyKilledEvent : IEvent { }

// BAD: Too much data
public struct EnemyKilledEvent : IEvent
{
    public Enemy FullEnemyReference; // Don't include references!
}
```

## Few-Shot Examples

### Example 1: UI Reacting to Damage
**User**: "Update health bar when player takes damage without coupling."

**Agent**:
```csharp
// In PlayerHealth.cs
public void TakeDamage(float amount)
{
    _currentHealth -= amount;
    EventBus.Publish(new PlayerDamagedEvent 
    { 
        DamageAmount = amount,
        CurrentHealth = _currentHealth,
        MaxHealth = _maxHealth
    });
}

// In HealthBarUI.cs : EventListenerBase<PlayerDamagedEvent>
protected override void OnEventReceived(PlayerDamagedEvent evt)
{
    _slider.value = evt.CurrentHealth / evt.MaxHealth;
}
```

### Example 2: Achievement System
**User**: "Unlock achievement when player kills 100 enemies."

**Agent**:
```csharp
// Subscribe to EnemyKilledEvent
// Track kill count, check threshold, show achievement
```

### Example 3: Sound Effects
**User**: "Play death sound when any enemy dies."

**Agent**:
```csharp
// AudioManager subscribes to EnemyKilledEvent
// Plays sound at event.Position
```



---

## TDD Contract

> ⚠️ **Legacy Skill — Refactor Pending**
> Este skill NO tiene tests automatizados aún. El siguiente boilerplate es un punto de partida.

```csharp
// Escribe estos tests ANTES de implementar:

// Test 1: should [expected behavior] when [condition]
[Test]
public void EventBusSystem_Should{ExpectedBehavior}_When{Condition}()
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
public void EventBusSystem_ShouldHandle{EdgeCase}()
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
public void EventBusSystem_ShouldThrow_When{InvalidInput}()
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
- `@advanced-design-patterns` - Observer pattern fundamentals
- `@scriptableobject-architecture` - SO-based event channels alternative
- `@di-container-manager` - For injecting event-dependent services

## Template Files
- `templates/EventBus.cs.txt` - Core event bus implementation
- `templates/GameEvents.cs.txt` - Example event definitions
- `templates/EventListenerBase.cs.txt` - Auto-lifecycle listener

## Tenebris 프로젝트 적용 규칙

struct 기반 이벤트 버스 패턴 그대로 적용. 이벤트는 반드시 struct + IEvent.

### 확정 필요 이벤트

```csharp
// ApplyParryReward Counter/HitStun 구현을 위해 필수
public struct AttackHitEvent : IEvent
{
    public readonly ICombatant Attacker;
    public readonly ICombatant Target;
    public readonly float Damage;
    public readonly Vector3 HitPosition;
}

// 보스 페이즈 전환 브로드캐스트
public struct BossPhaseChangedEvent : IEvent
{
    public readonly int NewPhase;
    public readonly float BossHpPercent;
}

// 패링 성공 알림
public struct ParrySuccessEvent : IEvent
{
    public readonly ICombatant Parrier;
    public readonly ICombatant Attacker;
}
```

### 적용 위치
- `AttackHitEvent`: BossController/PlayerController 공격 판정 성공 시 Publish
- `ParrySuccessEvent`: PlayerController.isParrying 판정 성공 시 Publish
- `ApplyParryReward` Counter/HitStun은 `AttackHitEvent`를 Subscribe해서 구현