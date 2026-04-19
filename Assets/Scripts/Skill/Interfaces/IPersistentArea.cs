using UnityEngine;

public interface IPersistentArea : IPoolable
{
    void Initialize(Vector3 forward, float radius, AreaShape shape, float angleDeg,
                    float duration, float tickInterval, SkillStep tickEffect, SkillContext ctx);
}
