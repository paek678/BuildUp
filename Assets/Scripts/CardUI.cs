using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;
using System.Collections;

public class CardUI : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler
{
    public Image icon;
    private AbilityCard cardData;
    private CardManager cardManager;

    private Material cardMaterial;
    private Vector3 originalScale;

    // 이미 선택되었는지 체크하는 플래그
    private bool isSelected = false;

    public void Setup(AbilityCard card, CardManager manager)
    {
        cardData = card;
        icon.sprite = card.cardIcon;
        cardManager = manager;

        originalScale = transform.localScale;

        cardMaterial = Instantiate(icon.material);
        icon.material = cardMaterial;

        cardMaterial.SetTexture("_MainTex", card.cardIcon.texture);
        cardMaterial.SetFloat("_Dissolve", 1.0f);

        StartCoroutine(PlayAppearAnimation());

        // 초기화 시 선택 상태 해제
        isSelected = false;
    }

    private IEnumerator PlayAppearAnimation()
    {
        float duration = 1.5f;
        float elapsed = 0f;

        while (elapsed < duration)
        {
            elapsed += Time.unscaledDeltaTime;
            float t = elapsed / duration;
            cardMaterial.SetFloat("_Dissolve", Mathf.Lerp(1.0f, 0f, t));
            yield return null;
        }

        cardMaterial.SetFloat("_Dissolve", 0f);
    }

    public IEnumerator PlayDisappearAnimation()
    {
        float duration = 1.0f;
        float elapsed = 0f;

        while (elapsed < duration)
        {
            elapsed += Time.unscaledDeltaTime;
            float t = elapsed / duration;
            cardMaterial.SetFloat("_Dissolve", Mathf.Lerp(0f, 1f, t));
            yield return null;
        }

        cardMaterial.SetFloat("_Dissolve", 1f);
    }

    public void OnClick()
    {
        // 이미 선택된 경우 무시
        if (cardData == null || isSelected) return;

        isSelected = true; // 선택 상태로 변경
        cardManager.OnCardSelected(cardData);
    }

    public void OnPointerEnter(PointerEventData eventData)
    {
        if (!isSelected)
            transform.localScale = originalScale * 1.05f;
    }

    public void OnPointerExit(PointerEventData eventData)
    {
        transform.localScale = originalScale;
    }
}