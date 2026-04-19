using UnityEngine;

public interface IProjectile : IPoolable
{
    void Launch(Vector3 direction, float speed, float range);
    void SetHitCallback(SkillStep onHit, SkillContext ctx, bool pierce);
}
