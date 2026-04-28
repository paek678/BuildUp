using UnityEngine;

public static class PlayerArenaBounds
{
    private static readonly Vector3 ArenaCenter = new(9.86f, 0f, 7.62f);
    private const float ArenaHalf  = 74f;
    private const float EdgeMargin = 3f;
    private const float Limit      = ArenaHalf - EdgeMargin;

    public static Vector3 ClampToArena(Vector3 candidate)
    {
        Vector3 offset = candidate - ArenaCenter;
        offset.x = Mathf.Clamp(offset.x, -Limit, Limit);
        offset.z = Mathf.Clamp(offset.z, -Limit, Limit);
        candidate.x = ArenaCenter.x + offset.x;
        candidate.z = ArenaCenter.z + offset.z;
        return candidate;
    }
}
