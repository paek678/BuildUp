using UnityEngine;
using System.Collections;

public class SelectableUICard : MonoBehaviour
{
    private bool isExpanded = false;
    private Vector3 originalPosition;
    private Vector3 originalScale;
    private Quaternion originalRotation;

    private RectTransform rectTransform;

    // 모든 카드가 공유하는 전역 플래그: 어떤 카드가 확장 상태인지
    private static bool cardExpanded = false;

    void Start()
    {
        rectTransform = GetComponent<RectTransform>();
        if (rectTransform != null)
        {
            originalPosition = rectTransform.anchoredPosition;
            originalScale = rectTransform.localScale;
            originalRotation = rectTransform.localRotation;
        }
    }

    public void OnCardClick()
    {
        // 다른 카드가 이미 확장 상태라면 클릭 불가
        if (!isExpanded && cardExpanded) return;
        if (!gameObject.activeInHierarchy) return;

        StopAllCoroutines();

        if (!isExpanded)
        {
            StartCoroutine(AnimateCard(Vector3.zero, originalScale * 2f, Quaternion.identity));
            cardExpanded = true; // 이 카드가 확장됨 → 다른 카드 클릭 막기
        }
        else
        {
            StartCoroutine(AnimateCard(originalPosition, originalScale, originalRotation));
            cardExpanded = false; // 원래 자리로 돌아옴 → 다른 카드 클릭 가능
        }

        isExpanded = !isExpanded;
    }

    private IEnumerator AnimateCard(Vector3 targetPos, Vector3 targetScale, Quaternion targetRot)
    {
        float duration = 0.5f;
        float elapsed = 0f;

        Vector3 startPos = rectTransform.anchoredPosition;
        Vector3 startScale = rectTransform.localScale;
        Quaternion startRot = rectTransform.localRotation;

        while (elapsed < duration)
        {
            elapsed += Time.unscaledDeltaTime;
            float t = elapsed / duration;

            rectTransform.anchoredPosition = Vector3.Lerp(startPos, targetPos, t);
            rectTransform.localScale = Vector3.Lerp(startScale, targetScale, t);
            rectTransform.localRotation = Quaternion.Lerp(startRot, targetRot, t);

            yield return null;
        }

        rectTransform.anchoredPosition = targetPos;
        rectTransform.localScale = targetScale;
        rectTransform.localRotation = targetRot;
    }
}