using UnityEngine;
using UnityEngine.UI;
using System.Collections;
using System.Collections.Generic;

public class CardManager : MonoBehaviour
{
    public AbilityCard[] allCards;
    public CardUI[] cardSlots;
    public GameObject cardUIPanel;

    public Canvas mainCanvas;
    public Image[] selectedCardSlots;

    private List<AbilityCard> selectedCards = new List<AbilityCard>();
    private int selectionCount = 0;
    private int maxSelections = 5;

    // ���� �ߺ� ���� �÷���
    private bool isSelecting = false;

    void Start()
    {
        cardUIPanel.SetActive(false);
        Invoke("ShowCardSelection", 10f);

        foreach (var slot in selectedCardSlots)
        {
            slot.gameObject.SetActive(false);
        }
    }

    public void ShowCardSelection()
    {
        if (selectionCount >= maxSelections) return;

        selectionCount++;
        isSelecting = false; // �� ���� ���� �� �ʱ�ȭ

        cardUIPanel.SetActive(true);
        Time.timeScale = 0f;

        List<AbilityCard> availableCards = new List<AbilityCard>(allCards);

        for (int i = 0; i < cardSlots.Length; i++)
        {
            if (availableCards.Count == 0) break;

            int randomIndex = Random.Range(0, availableCards.Count);
            AbilityCard randomCard = availableCards[randomIndex];

            cardSlots[i].Setup(randomCard, this);
            availableCards.RemoveAt(randomIndex);
        }
    }

    public void OnCardSelected(AbilityCard card)
    {
        // �̹� ���� ���̸� ����
        if (isSelecting) return;
        isSelecting = true;

        if (selectedCards.Contains(card)) return;

        selectedCards.Add(card);
        Debug.Log("���õ� ī��: " + card.cardName);

        int slotIndex = selectedCards.Count - 1;
        if (slotIndex < selectedCardSlots.Length)
        {
            selectedCardSlots[slotIndex].sprite = card.cardIcon;
            selectedCardSlots[slotIndex].gameObject.SetActive(true);
        }

        UnlockSkill(card);
        StartCoroutine(HideAllCards());
    }

    private void UnlockSkill(AbilityCard card)
    {
        GameObject player = GameObject.FindGameObjectWithTag("Player");
        if (player == null)
        {
            Debug.LogWarning("[CardManager] Player 오브젝트를 찾을 수 없음");
            return;
        }

        // 신규 스킬 시스템 — SkillDefinition 기반
        // 현재 디버그/학습 모드: SkillManager 슬롯은 Inspector 에서 직접 지정한다.
        // 카드 드래프트는 추후 빈 슬롯 탐색 → SetSlot 호출 방식으로 재연결 예정.
        if (card.skillDefinition != null)
        {
            var skillManager = player.GetComponent<SkillManager>();
            if (skillManager != null)
            {
                for (int i = 0; i < skillManager.MaxSlots; i++)
                {
                    if (skillManager.Slots[i] == null)
                    {
                        skillManager.SetSlot(i, card.skillDefinition);
                        Debug.Log($"[CardManager] 빈 슬롯[{i}] 에 장착: {card.cardName}");
                        return;
                    }
                }
                Debug.LogWarning("[CardManager] 슬롯 가득 참");
                return;
            }
            var skillSlot = player.GetComponent<PlayerSkillSlot>();
            if (skillSlot != null)
            {
                skillSlot.Equip(card.skillDefinition);
                return;
            }
            Debug.LogWarning("[CardManager] SkillManager / PlayerSkillSlot 둘 다 없음");
        }

        // 레거시 폴백 — skillObjectName 기반
        if (!string.IsNullOrEmpty(card.skillObjectName))
        {
            Transform skillTransform = player.transform.Find(card.skillObjectName);
            if (skillTransform != null)
            {
                skillTransform.gameObject.SetActive(true);
                Debug.Log($"[CardManager] 레거시 스킬 해금: {card.skillObjectName}");
            }
        }
    }

    private IEnumerator HideAllCards()
    {
        foreach (var slot in cardSlots)
        {
            slot.StartCoroutine(slot.PlayDisappearAnimation());
        }

        yield return new WaitForSecondsRealtime(1.0f);

        cardUIPanel.SetActive(false);
        Time.timeScale = 1f;

        if (selectionCount < maxSelections)
        {
            Invoke("ShowCardSelection", 10f);
        }
    }
}
