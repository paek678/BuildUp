using UnityEngine;

[CreateAssetMenu(fileName = "AbilityCard", menuName = "Cards/AbilityCard")]
public class AbilityCard : ScriptableObject
{
    [Header("카드 정보")]
    public string cardName;
    public Sprite cardIcon;
    [TextArea] public string description;

    [Header("스킬 연결")]
    public SkillDefinition skillDefinition;

    [Header("레거시 (하위 호환)")]
    public string skillObjectName;
}