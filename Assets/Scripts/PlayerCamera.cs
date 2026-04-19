using UnityEngine;

public class PlayerCamera : MonoBehaviour
{
    public Transform player;        // 따라갈 플레이어
    public Vector3 offset = new Vector3(0, 15, -5); // 카메라 위치 오프셋
    public float smoothSpeed = 5f;  // 부드럽게 따라오는 속도

    void LateUpdate()
    {
        if (player == null) return;

        // 목표 위치 = 플레이어 위치 + 오프셋
        Vector3 targetPosition = player.position + offset;

        // 카메라 이동 (부드럽게 보간)
        transform.position = Vector3.Lerp(transform.position, targetPosition, smoothSpeed * Time.deltaTime);

        // rotation은 고정 → LookAt 제거
        // transform.rotation = Quaternion.Euler(45f, 0f, 0f); // 예시: 원하는 각도로 고정
    }
}