using UnityEngine;

// 게임 시작 시 SkillLibrary 의 조립 결과를 SkillDefinition SO 에 주입
// 씬에 빈 GameObject 하나에 이 컴포넌트를 붙이고 SkillRegistry SO 를 연결
//
// 실행 순서:
//   1) Awake → SkillBinder.BindAll(registry)
//   2) 각 SkillDefinition.RuntimeStep 이 채워짐
//   3) SkillManager / PlayerSkillSlot 에서 스킬 사용 가능
public class SkillBootstrap : MonoBehaviour
{
    [SerializeField] private SkillRegistry _registry;

    private void Awake()
    {
        if (_registry == null)
        {
            Debug.LogError("[SkillBootstrap] SkillRegistry 가 연결되지 않았습니다");
            return;
        }

        SkillBinder.BindAll(_registry);
    }
}
