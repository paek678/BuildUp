---
name: interface-driven-development
description: "Senior Architect for Contract-Based Modularity. Create interfaces for decoupled, testable systems following Interface Segregation Principle."
argument-hint: "interface_name='IDamageable' methods='TakeDamage(float),IsAlive'"
disable-model-invocation: false
user-invocable: true
---

# Interface-Driven Development

## Overview
Eliminate rigidity of deep inheritance and hard-coupling by programming to interfaces (contracts). Creates modular, testable systems where implementations can be swapped without modifying consumers.

## When to Use
- Use when different objects share behaviors (enemies and walls both damageable)
- Use when implementing dependency injection patterns
- Use when creating mock objects for unit testing
- Use when building plugin/extension architectures
- Use when you see "if (obj is TypeA) else if (obj is TypeB)" patterns

## Core Principle

```
┌─────────────────────────────────────────────────────────────┐
│                  PROGRAM TO INTERFACES                      │
│                 (Not to implementations)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  BAD:  Player attacks Enemy (tight coupling)                │
│                                                             │
│  GOOD: Player attacks IDamageable (any implementing type)   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Common Unity Interfaces

| Interface | Purpose | Implementations |
|-----------|---------|-----------------|
| `IDamageable` | Can receive damage | Enemy, Player, Destructible |
| `IInteractable` | Can be interacted with | Door, Chest, NPC, Lever |
| `ISaveable` | Persists state | Player, Inventory, QuestLog |
| `IPoolable` | Object pool lifecycle | Projectile, VFX, Enemy |
| `IInitializable` | Async initialization | Managers, Services |

## Interface Design Guidelines

```csharp
// GOOD: Small, focused interface (ISP)
public interface IDamageable
{
    void TakeDamage(float amount);
    bool IsAlive { get; }
}

// GOOD: Separate concern
public interface IHealable
{
    void Heal(float amount);
    float MaxHealth { get; }
}

// BAD: Fat interface (violates ISP)
public interface IEntity
{
    void TakeDamage(float amount);
    void Heal(float amount);
    void Move(Vector3 direction);
    void Attack();
    void Die();
    // Too many responsibilities!
}
```

## Best Practices
- ✅ Interfaces start with `I` prefix (e.g., `IDamageable`)
- ✅ Keep interfaces small and focused (Interface Segregation)
- ✅ Place interfaces in dedicated files to prevent circular deps
- ✅ Use `TryGetComponent<IInterface>` for safe access
- ✅ Design interfaces without MonoBehaviour dependencies when possible
- ❌ **NEVER** use "Base" suffix if interface works (use `IEnemy` not `EnemyBase`)
- ❌ **NEVER** cast interface back to concrete type
- ❌ **NEVER** include implementation details in interface

## Procedure
1. **Extract Behaviors**: Identify shared behaviors across types
2. **Define Contract**: Create minimal interface with essential methods
3. **Implement**: Have classes implement the interface
4. **Reference by Interface**: Consumers use interface type, not concrete
5. **Test**: Create mock implementations for unit testing

## Few-Shot Examples

### Example 1: Unified Damage System
**User**: "Same attack should damage enemies AND breakable walls."

**Agent**:
```csharp
public interface IDamageable
{
    void TakeDamage(float amount);
    bool IsAlive { get; }
}

// Enemy.cs
public class Enemy : MonoBehaviour, IDamageable { ... }

// DestructibleWall.cs
public class DestructibleWall : MonoBehaviour, IDamageable { ... }

// WeaponAttack.cs - works on ANY IDamageable
void OnTriggerEnter(Collider other)
{
    if (other.TryGetComponent<IDamageable>(out var target))
    {
        target.TakeDamage(_damage);
    }
}
```

### Example 2: Interaction System
**User**: "Player can interact with doors, chests, and NPCs."

**Agent**:
```csharp
public interface IInteractable
{
    string InteractionPrompt { get; }
    bool CanInteract { get; }
    void Interact(GameObject interactor);
}

// Door : IInteractable -> Opens
// Chest : IInteractable -> Shows loot
// NPC : IInteractable -> Starts dialogue
```

### Example 3: Save System
**User**: "Multiple objects need to save state."

**Agent**:
```csharp
public interface ISaveable
{
    string SaveId { get; }
    object GetSaveData();
    void LoadSaveData(object data);
}

// SaveManager finds all ISaveable, calls GetSaveData()
```

## Mockability for Testing
```csharp
// Production
public class AudioManager : IAudioService { ... }

// Test Mock
public class MockAudioService : IAudioService
{
    public bool WasSoundPlayed { get; private set; }
    public void PlaySound(string id) => WasSoundPlayed = true;
}
```



---

## TDD Contract

> ⚠️ **Legacy Skill — Refactor Pending**
> Este skill NO tiene tests automatizados aún. El siguiente boilerplate es un punto de partida.

```csharp
// Escribe estos tests ANTES de implementar:

// Test 1: should [expected behavior] when [condition]
[Test]
public void InterfaceDrivenDevelopment_Should{ExpectedBehavior}_When{Condition}()
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
public void InterfaceDrivenDevelopment_ShouldHandle{EdgeCase}()
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
public void InterfaceDrivenDevelopment_ShouldThrow_When{InvalidInput}()
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
- `@di-container-manager` - Inject interface implementations
- `@advanced-design-patterns` - Strategy, Factory use interfaces
- `@advanced-game-bootstrapper` - IInitializable pattern

## Safe Access Patterns
```csharp
// GOOD: Safe component access
if (TryGetComponent<IDamageable>(out var damageable))
{
    damageable.TakeDamage(10f);
}

// BAD: Assumes component exists
GetComponent<IDamageable>().TakeDamage(10f); // NullRef risk!

## Tenebris 프로젝트 적용 규칙

### 확정 인터페이스: ICombatant
모든 전투 가능 객체(PlayerController, BossController)는 반드시 `ICombatant` 구현.

```csharp
// MonoBehaviour와 충돌 방지 — 명시적 인터페이스 구현 필수
Transform ICombatant.Transform => transform;
GameObject ICombatant.GameObject => gameObject;
```

### 접근 패턴
```csharp
// 전투 대상 접근은 ICombatant 사용 (IDamageable 대신)
if (other.TryGetComponent<ICombatant>(out var target))
{
    statsManager.ApplyDamageToPlayer(damage);
}
```

### 추가 예정 인터페이스
```csharp
public interface IProjectile : IPoolable
{
    void Launch(Vector3 direction, float speed);
    void SetHitCallback(SkillStep onHit);
}

public interface IPersistentArea : IPoolable
{
    void Initialize(float radius, float duration, float tickInterval, SkillStep tickEffect);
}
```

### 규칙
- 새 전투 객체 추가 시 ICombatant 먼저 구현, 그 다음 StatsManager 연결
- 인터페이스 파일은 별도 파일로 분리 (순환 의존 방지)
```