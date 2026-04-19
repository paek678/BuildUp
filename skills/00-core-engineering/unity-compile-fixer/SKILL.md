---
name: unity-compile-fixer
description: "Agentic repair loop for C# compilation errors. Reads compiler output, classifies errors by pattern, and applies targeted, minimal fixes to restore a green build."
argument-hint: "action='diagnose' OR action='fix' target='Assets/Scripts/MyScript.cs'"
disable-model-invocation: false
user-invocable: true
---

# Unity Compile Fixer

## Overview
An agentic repair loop that diagnoses C# compilation errors reported by the Unity Editor console, classifies them into known error patterns, and applies the smallest possible fix to restore a green build. It is not a refactoring tool — it is a **surgical fixer**.

## When to Use
- Use when the Unity Editor console shows **CS errors** that block compilation.
- Use after a large refactor that broke multiple files simultaneously.
- Use when the user pastes a compiler error and asks "how do I fix this?".
- ❌ Do NOT use for architectural redesigns — use `@advanced-design-patterns` instead.
- ❌ Do NOT use for runtime errors — those require `@memory-profiler-expert`.

## Architecture

```
┌────────────────────────────────────────────────┐
│               REPAIR LOOP PIPELINE             │
├────────────────────────────────────────────────┤
│                                                │
│  1. INGEST          2. CLASSIFY        3. FIX  │
│  ┌──────────┐       ┌──────────────┐   ┌────┐ │
│  │ Console  │──────▶│ Error Router │──▶│ Δ  │ │
│  │ CS Error │       │ (Pattern Map)│   └────┘ │
│  └──────────┘       └──────────────┘          │
│                             │                  │
│                    ┌────────▼──────────┐      │
│                    │  Fix Strategies   │      │
│                    │  • missing using  │      │
│                    │  • wrong type     │      │
│                    │  • null ref       │      │
│                    │  • interface gap  │      │
│                    └───────────────────┘      │
│                                                │
│  4. VERIFY → re-read console → Green? Done.   │
└────────────────────────────────────────────────┘
```

## Error Classification Map

| CS Code | Common Cause | Fix Strategy |
|---------|-------------|--------------|
| `CS0246` | Missing `using` directive | Add `using Namespace;` to file top |
| `CS0103` | Undeclared variable / member | Declare field; check typo |
| `CS0117` | Type member does not exist | Update API call to current version |
| `CS0029` | Cannot implicitly convert type | Add explicit cast or fix generic type |
| `CS0533` | Interface member not implemented | Add missing interface method |
| `CS1061` | Member not found | Check spelling; check Unity version |
| `CS0234` | Namespace/type not found | Add package via Package Manager |
| `CS8600` | Nullable dereference warning | Add null-check guard |

## Repair Loop Procedure

1.  **INGEST**: Read the Unity console via `mcp_unityMCP_read_console` or parse the user-provided error string.
2.  **ISOLATE**: Extract `{FILE_PATH}({LINE},{COL}): error CS{CODE}: {MESSAGE}`.
3.  **READ CONTEXT**: Use `read_resource` or `view_file` to read ±10 lines around the error location.
4.  **CLASSIFY**: Match the `CS{CODE}` to the Error Classification Map above.
5.  **PROPOSE FIX**: State the fix in words before applying it. "I will add `using UnityEngine.UI;` at line 3."
6.  **APPLY**: Use `mcp_unityMCP_apply_text_edits` for surgical edits. Never rewrite the whole file.
7.  **VALIDATE**: Run `mcp_unityMCP_validate_script` on the modified file.
8.  **LOOP**: If new errors surface, return to step 1. Max 5 iterations before escalating to the user.

## Best Practices

- ✅ Fix ONE error at a time. Cascading errors often disappear once root causes are fixed.
- ✅ **Always read the file before editing** — confirm the line context hasn't shifted.
- ✅ State your intention before each edit ("I am adding `using X` to fix CS0246 at line 4").
- ✅ Prefer `apply_text_edits` over full file rewrites.
- ❌ **NEVER** silently delete code to make a compilation error go away.
- ❌ **NEVER** suppress nullable warnings with `!` operators without understanding the root cause.
- ❌ **NEVER** ignore CS0234 — a missing namespace usually means a package needs installation.

## Few-Shot Examples

### Example 1: Missing Using Directive (CS0246)
**User**: "I get `CS0246: The type or namespace name 'TextMeshPro' could not be found.`"

**Agent**:
1. Reads the file → confirms `TMPro` namespace is referenced but not imported.
2. "I'll add `using TMPro;` at the top of the file and verify `com.unity.textmeshpro` exists in manifest.json."
```csharp
// Add at top of file
using TMPro;
```

### Example 2: Interface Not Implemented (CS0535)
**User**: "CS0535: 'EnemyAI' does not implement interface member 'IDamageable.TakeDamage(float)'."

**Agent**:
1. Reads `EnemyAI.cs` → confirms `IDamageable` is declared but `TakeDamage` is missing.
2. Inserts the missing method stub.
```csharp
public void TakeDamage(float amount)
{
    _health -= amount;
    if (_health <= 0f) Die();
}
```

### Example 3: API Change (CS1061)
**User**: "CS1061: 'Rigidbody' does not contain a definition for 'velocity'."

**Agent**: "In Unity 6 with Rigidbody, `velocity` is now `linearVelocity`. Applying rename."



---

## TDD Contract

> ⚠️ **Legacy Skill — Refactor Pending**
> Este skill NO tiene tests automatizados aún. El siguiente boilerplate es un punto de partida.

```csharp
// Escribe estos tests ANTES de implementar:

// Test 1: should [expected behavior] when [condition]
[Test]
public void UnityCompileFixer_Should{ExpectedBehavior}_When{Condition}()
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
public void UnityCompileFixer_ShouldHandle{EdgeCase}()
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
public void UnityCompileFixer_ShouldThrow_When{InvalidInput}()
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

- `@unified-style-guide` — Prevents style-based errors upstream
- `@automated-unit-testing` — Catches type errors before runtime
- `@context-discovery-agent` — Validates package dependencies before flagging CS0234

## Tenebris 프로젝트 적용 규칙

> ⚠️ MCP 미연결 — `mcp_unityMCP_*` 도구 사용 불가. Read/Edit 도구로 수동 수정.

### 수동 수정 절차
1. 에러 메시지에서 `{파일}({라인}): error CS{코드}` 추출
2. 오류 분류표에서 CS코드 확인
3. Read 도구로 해당 파일 ±10줄 확인
4. Edit 도구로 최소 수정 (전체 파일 재작성 금지)

### Tenebris에서 자주 발생하는 에러

| 에러 코드 | 원인 | 처리 |
|-----------|------|------|
| CS0535 | ICombatant 메서드 미구현 | 명시적 인터페이스 구현 추가 |
| CS0246 | using 누락 (UnityEngine.AI, Unity.Netcode 등) | 파일 상단 using 추가 |
| CS1061 | NGO/Unity 6 API 변경 (`velocity` → `linearVelocity`) | API 확인 후 수정 |
| CS0234 | 패키지 미설치 참조 (Addressables, UniTask 등) | manifest.json 확인 — Tenebris 미설치 패키지 사용 금지 |
