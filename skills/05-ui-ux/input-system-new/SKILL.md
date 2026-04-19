---
name: input-system-new
description: "Unity New Input System wrapper with ScriptableObject events for multi-device input handling."
argument-hint: "action='Jump' OR device='Gamepad' scheme='Controller'"
disable-model-invocation: false
user-invocable: true
---

# New Input System

## Overview
Unity New Input System abstraction layer. Wraps input actions into ScriptableObject-based event channels for decoupled, multi-device input handling.

## When to Use
- Use for multi-platform input (keyboard, gamepad, touch)
- Use for rebindable controls
- Use for local multiplayer
- Use for UI navigation input
- Use for action-based input (not polling)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  INPUT SYSTEM ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  INPUT ACTIONS ASSET     INPUT READER (SO)    CONSUMERS    │
│  ┌──────────────────┐   ┌──────────────┐    ┌──────────┐  │
│  │ .inputactions    │──▶│ InputReader  │───▶│ Player   │  │
│  │ ┌──────────────┐ │   │              │    │ UI       │  │
│  │ │ Move         │ │   │ OnMove       │    │ Camera   │  │
│  │ │ Jump         │ │   │ OnJump       │    │ Vehicle  │  │
│  │ │ Attack       │ │   │ OnAttack     │    │ etc.     │  │
│  │ └──────────────┘ │   └──────────────┘    └──────────┘  │
│  └──────────────────┘                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Input Action Types

| Type | Use | C# Type |
|------|-----|---------|
| **Button** | Jump, Attack | `bool` |
| **Value** | Move, Look | `Vector2` |
| **PassThrough** | Continuous input | Any |

## Control Schemes

| Scheme | Devices |
|--------|---------|
| **Keyboard&Mouse** | Keyboard + Mouse |
| **Gamepad** | Xbox, PlayStation, Switch |
| **Touch** | Touchscreen |

## Best Practices
- ✅ Create InputReader ScriptableObject
- ✅ Use C# events, not direct polling
- ✅ Generate C# class from .inputactions
- ✅ Use PlayerInput component for multiplayer
- ✅ Implement rebinding system
- ❌ **NEVER** poll Input directly (Input.GetKey)
- ❌ **NEVER** reference InputActions in consumers
- ❌ **NEVER** forget to enable action maps

## Few-Shot Examples

### Example 1: Input Reader ScriptableObject
**User**: "Create an input reader."

**Agent**:
```csharp
[CreateAssetMenu(fileName = "InputReader", menuName = "Input/Input Reader")]
public class InputReader : ScriptableObject, GameInput.IPlayerActions
{
    private GameInput _gameInput;
    
    public event Action<Vector2> OnMoveEvent;
    public event Action OnJumpEvent;
    public event Action OnAttackEvent;
    public event Action<bool> OnSprintEvent;
    
    public Vector2 MoveInput { get; private set; }
    
    private void OnEnable()
    {
        _gameInput ??= new GameInput();
        _gameInput.Player.SetCallbacks(this);
        _gameInput.Player.Enable();
    }
    
    private void OnDisable()
    {
        _gameInput.Player.Disable();
    }
    
    public void OnMove(InputAction.CallbackContext context)
    {
        MoveInput = context.ReadValue<Vector2>();
        OnMoveEvent?.Invoke(MoveInput);
    }
    
    public void OnJump(InputAction.CallbackContext context)
    {
        if (context.performed)
            OnJumpEvent?.Invoke();
    }
    
    public void OnAttack(InputAction.CallbackContext context)
    {
        if (context.performed)
            OnAttackEvent?.Invoke();
    }
    
    public void OnSprint(InputAction.CallbackContext context)
    {
        OnSprintEvent?.Invoke(context.performed);
    }
}
```

### Example 2: Consumer (PlayerController)
**User**: "Connect input to player."

**Agent**:
```csharp
public class PlayerController : MonoBehaviour
{
    [SerializeField] private InputReader _inputReader;
    
    private void OnEnable()
    {
        _inputReader.OnJumpEvent += HandleJump;
        _inputReader.OnAttackEvent += HandleAttack;
    }
    
    private void OnDisable()
    {
        _inputReader.OnJumpEvent -= HandleJump;
        _inputReader.OnAttackEvent -= HandleAttack;
    }
    
    private void Update()
    {
        Vector2 move = _inputReader.MoveInput;
        // Use move for continuous input
    }
    
    private void HandleJump() => _jumpRequested = true;
    private void HandleAttack() => _attackRequested = true;
}
```

### Example 3: UI Navigation
**User**: "Enable gamepad UI navigation."

**Agent**:
```csharp
private void SwitchToUI()
{
    _gameInput.Player.Disable();
    _gameInput.UI.Enable();
    
    // UI Toolkit focus
    _uiDocument.rootVisualElement.Q<Button>().Focus();
}

private void SwitchToGameplay()
{
    _gameInput.UI.Disable();
    _gameInput.Player.Enable();
}
```

## Rebinding Flow
1. Start rebinding: `action.PerformInteractiveRebinding()`
2. Wait for input
3. Save to PlayerPrefs: `action.SaveBindingOverridesAsJson()`
4. Load on startup: `action.LoadBindingOverridesFromJson()`



---

## TDD Contract

> ⚠️ **Legacy Skill — Refactor Pending**
> Este skill NO tiene tests automatizados aún. El siguiente boilerplate es un punto de partida.

```csharp
// Escribe estos tests ANTES de implementar:

// Test 1: should [expected behavior] when [condition]
[Test]
public void InputSystemNew_Should{ExpectedBehavior}_When{Condition}()
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
public void InputSystemNew_ShouldHandle{EdgeCase}()
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
public void InputSystemNew_ShouldThrow_When{InvalidInput}()
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
- `@menu-navigation-flow` - UI with gamepad
- `@ui-toolkit-modern` - Focusable elements
- `@advanced-character-controller` - Movement input

## Tenebris 프로젝트 적용 규칙

패키지 확정: `com.unity.inputsystem 1.19.0`

### Tenebris 액션 맵 구조

```
Player (Action Map)
  ├─ Move    : Vector2  (WASD / 좌스틱)
  ├─ Attack  : Button   (마우스 좌클릭 / 게임패드 X)
  ├─ Skill1  : Button   (Q / 게임패드 LT)
  ├─ Skill2  : Button   (E / 게임패드 RT)
  ├─ Skill3  : Button   (R / 게임패드 Y)
  ├─ Skill4  : Button   (F / 게임패드 B)
  ├─ Parry   : Button   (스페이스 / 게임패드 LB)
  └─ Rope    : Button   (마우스 우클릭 / 게임패드 RB)
```

### 적용 규칙
- `Input.GetKeyDown` 방식 사용 금지 — InputReader ScriptableObject 경유
- 멀티플레이어: `PlayerInput` 컴포넌트로 Player1/Player2 분리
- 입력 이벤트는 OnEnable 구독 / OnDisable 해제 필수
