using UnityEngine;
using System.Collections;

public class BossEffectSpawner : MonoBehaviour
{
    [Header("이펙트 프리팹")]
    public GameObject effectPrefab;

    [Header("이펙트 설정")]
    public float spawnInterval = 0.2f;   // 생성 간격
    public float effectLifetime = 0.5f; // 이펙트 유지 시간
    public int spawnCount = 36;         // 총 생성 개수
    public float rotationStep = 10f;    // Y 회전 증가값
    public float restTime = 10f;        // 쿨타임

    private bool isSpawning = false;

    void Update()
    {
        // 테스트용: 스페이스바 누르면 시작
        if (Input.GetKeyDown(KeyCode.Space) && !isSpawning)
        {
            StartCoroutine(SpawnRoutine());
        }
    }

    IEnumerator SpawnRoutine()
    {
        isSpawning = true;

        float currentRotation = 0f;

        for (int i = 0; i < spawnCount; i++)
        {
            // 보스 위치 기준으로 회전값 적용
            Quaternion rotation = Quaternion.Euler(0, currentRotation, 0);
            GameObject fx = Instantiate(effectPrefab, transform.position, rotation);

            // 0.5초 후 삭제
            Destroy(fx, effectLifetime);

            // 회전값 누적
            currentRotation += rotationStep;

            // 0.2초 대기
            yield return new WaitForSeconds(spawnInterval);
        }

        // 36개 다 끝나면 10초 쉬기
        yield return new WaitForSeconds(restTime);

        isSpawning = false;
    }
}