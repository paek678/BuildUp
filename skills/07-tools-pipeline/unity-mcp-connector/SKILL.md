---
name: unity-mcp-connector
description: "Orchestration bridge between AI Agents and the running Unity Editor instance via MCP (Model Context Protocol)."
argument-hint: "action='ping' OR target='selection' scope='scene'"
disable-model-invocation: false
user-invocable: false
---

> ⚠️ **Tenebris 프로젝트 미연결** — MCP 서버 미연결 상태. 이 skill의 `mcp_unityMCP_*` 도구는 사용 불가.
> MCP 연결 시까지 `unity-compile-fixer`의 수동 수정 절차를 따를 것.

# Unity MCP Connector

## Overview
Connects the file-based AI Brain with the live Unity Editor state. Allows the agent to "see" the scene hierarchy, inspect selected objects, and validate the existence of components dynamically.

## When to Use
- Use to check if Unity Editor is open and listening
- Use to find the currently selected GameObject context
- Use to validate scene contents that aren't serialized to disk yet
- Use to trigger Editor actions (Play, Pause, Refresh)
- Use to read console logs for errors

## Capabilities

| Capability | Tool | Description |
|------------|------|-------------|
| **Telemetry** | `manage_editor` | Check connection health (Ping) |
| **Selection** | `manage_editor` | Get/Set user selection |
| **Hierarchy** | `find_gameobjects` | Search active scene objects |
| **State** | `manage_editor` | Play/Pause/Stop mode control |
| **Scene** | `manage_scene` | Open/Save scenes |

## Procedure

### 1. Connection Check (First Step)
Always verify the bridge is active before attempting complex operations.
```json
{
  "tool": "mcp_unityMCP_manage_editor",
  "args": { "action": "telemetry_ping" }
}
```

### 2. Context Retrieval
If the user says "Add script to **this** object", fetch the selection.
```json
{
  "tool": "mcp_unityMCP_manage_editor",
  "args": { "action": "get_selection" } // (Hypothetical param, usually implied or via finding)
}
```
*Note: Currently `telemetry_status` or specific find commands might be needed depending on server implementation.*

### 3. Graceful Fallback
If MCP tools fails or returns "Not Connected":
1. **Log**: "Unity Editor not reachable. Proceeding in File-System Mode."
2. **Ask**: "Please specify the file path or GameObject name manually."
3. **Continue**: Do not halt the workflow.

## Best Practices
- ✅ **Ping First**: Always check `telemetry_ping` before deep operations.
- ✅ **Read-Only Default**: Prefer reading state to modifying state unless explicitly requested.
- ✅ **Error Handling**: Catch tool failures gracefully (Editor might be compiling).
- ❌ **NEVER** assume Editor is open.
- ❌ **NEVER** rely solely on MCP for critical data (File System is truth).

## Few-Shot Examples

### Example 1: Check Status
**User**: "Is Unity connected?"

**Agent**:
```javascript
// Calls mcp_unityMCP_manage_editor with action='telemetry_ping'
// Output: "pong"
// Response: "Yes, Unity Editor is connected and responding."
```

### Example 2: Find Player
**User**: "Where is the player in the scene?"

**Agent**:
```javascript
// Calls mcp_unityMCP_find_gameobjects with search_term='Player'
// Output: [{ name: "Player", id: 1234, ... }]
// Response: "Found 'Player' with InstanceID 1234."
```



---

## TDD Contract

> ⚠️ **Legacy Skill — Refactor Pending**
> Este skill NO tiene tests automatizados aún. El siguiente boilerplate es un punto de partida.

```csharp
// Escribe estos tests ANTES de implementar:

// Test 1: should [expected behavior] when [condition]
[Test]
public void UnityMcpConnector_Should{ExpectedBehavior}_When{Condition}()
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
public void UnityMcpConnector_ShouldHandle{EdgeCase}()
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
public void UnityMcpConnector_ShouldThrow_When{InvalidInput}()
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
- `@custom-editor-scripting` - Build tools utilizing this connection
- `@automated-unit-testing` - Trigger tests via MCP
