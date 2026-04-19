using System;
using System.Collections.Generic;
using Unity.Behavior;
using UnityEngine;
using Composite = Unity.Behavior.Composite;
using Unity.Properties;

[Serializable, GeneratePropertyBag]
[NodeDescription(name: "WeightedRandomComposite", story: "자식 브랜치 각각에 [Weight] 숫자를 지정해서, 가중치 비율에 따라 하나의 브랜치를 선택 실행", category: "Flow", id: "661b0732e4af87a197915b95c0ca7599")]
public partial class WeightedRandomCompositeSequence : Composite
{
    [SerializeReference] public BlackboardVariable<List<float>> Weight;

    private int _selectedIndex;

    protected override Status OnStart()
    {
        if (Weight.Value == null || Weight.Value.Count == 0 || Children.Count == 0)
        {
            Debug.LogWarning($"[WeightedRandom] Failure — Weight: {(Weight.Value == null ? "NULL" : Weight.Value.Count.ToString())}, Children: {Children.Count}");
            return Status.Failure;
        }

        _selectedIndex = PickWeightedIndex();
        Debug.Log($"[WeightedRandom] 선택된 브랜치: {_selectedIndex} (총 {Children.Count}개)");
        var status = StartNode(Children[_selectedIndex]);
        if (status is Status.Success or Status.Failure)
            return status;

        return Status.Waiting;
    }

    protected override Status OnUpdate()
    {
        var status = Children[_selectedIndex].CurrentStatus;
        if (status is Status.Success or Status.Failure)
            return status;

        return Status.Waiting;
    }

    protected override void OnEnd()
    {
    }

    private int PickWeightedIndex()
    {
        float total = 0f;
        int count = Mathf.Min(Weight.Value.Count, Children.Count);
        for (int i = 0; i < count; i++)
            total += Weight.Value[i];

        float roll = UnityEngine.Random.Range(0f, total);
        float cumulative = 0f;
        for (int i = 0; i < count; i++)
        {
            cumulative += Weight.Value[i];
            if (roll < cumulative)
                return i;
        }
        return count - 1;
    }
}

