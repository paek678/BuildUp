using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;
using System.Collections;

public class AutoDialogueManager : MonoBehaviour
{
    public GameObject narrationPanel;
    public Text narrationNameText;
    public Text narrationDialogueText;

    public GameObject character1Panel;
    public Text character1NameText;
    public Text character1DialogueText;

    public GameObject character2Panel;
    public Text character2NameText;
    public Text character2DialogueText;

    public GameObject character3Panel;
    public Text character3NameText;
    public Text character3DialogueText;

    // Intro 텍스트
    public Text introText;
    public float fadeDuration = 1.5f;
    public float holdTime = 2f;

    // 프롤로그 끝나고 켜질 프리팹과 씬 이름
    public GameObject endPrefab;
    public string nextSceneName;

    [System.Serializable]
    public class DialogueLine
    {
        public string speaker; // "Narration", "Character1", "Character2", "Character3"
        public string name;    // 화자 이름
        [TextArea(2, 5)]
        public string sentence;
        public Color textColor = Color.white; // 대사 색상 지정
    }

    public DialogueLine[] dialogueLines;

    public float typingSpeed = 0.05f;
    public float waitTime = 2f;

    private int index = 0;

    void Start()
    {
        // 시작할 때 모든 패널 끄기
        narrationPanel.SetActive(false);
        character1Panel.SetActive(false);
        character2Panel.SetActive(false);
        character3Panel.SetActive(false);

        // Intro 텍스트 페이드 실행 후 대사 시작
        StartCoroutine(IntroSequence());
    }

    IEnumerator IntroSequence()
    {
        Color baseColor = introText.color;

        // 페이드 인
        yield return StartCoroutine(FadeTextAlpha(0f, 1f, baseColor));

        // 유지
        yield return new WaitForSeconds(holdTime);

        // 페이드 아웃
        yield return StartCoroutine(FadeTextAlpha(1f, 0f, baseColor));

        // Intro 끝나면 본격적인 대사 시작
        StartCoroutine(ShowDialogue());
    }

    IEnumerator FadeTextAlpha(float start, float end, Color baseColor)
    {
        float elapsed = 0f;
        while (elapsed < fadeDuration)
        {
            elapsed += Time.deltaTime;
            float alpha = Mathf.Lerp(start, end, elapsed / fadeDuration);
            introText.color = new Color(baseColor.r, baseColor.g, baseColor.b, alpha);
            yield return null;
        }
        introText.color = new Color(baseColor.r, baseColor.g, baseColor.b, end);
    }

    IEnumerator ShowDialogue()
    {
        while (index < dialogueLines.Length)
        {
            DialogueLine line = dialogueLines[index];
            yield return StartCoroutine(TypeSentence(line));
            yield return new WaitForSeconds(waitTime);
            index++;
        }

        EndDialogue();
    }

    IEnumerator TypeSentence(DialogueLine line)
    {
        // 모든 패널 끄기
        narrationPanel.SetActive(false);
        character1Panel.SetActive(false);
        character2Panel.SetActive(false);
        character3Panel.SetActive(false);

        // 모든 텍스트 초기화
        narrationNameText.text = "";
        narrationDialogueText.text = "";
        character1NameText.text = "";
        character1DialogueText.text = "";
        character2NameText.text = "";
        character2DialogueText.text = "";
        character3NameText.text = "";
        character3DialogueText.text = "";

        Text targetDialogue = null;
        Text targetName = null;
        GameObject targetPanel = null;

        switch (line.speaker)
        {
            case "Narration":
                targetPanel = narrationPanel;
                targetDialogue = narrationDialogueText;
                targetName = narrationNameText;
                break;
            case "Character1":
                targetPanel = character1Panel;
                targetDialogue = character1DialogueText;
                targetName = character1NameText;
                break;
            case "Character2":
                targetPanel = character2Panel;
                targetDialogue = character2DialogueText;
                targetName = character2NameText;
                break;
            case "Character3":
                targetPanel = character3Panel;
                targetDialogue = character3DialogueText;
                targetName = character3NameText;
                break;
        }

        // 선택된 패널 켜기
        if (targetPanel != null)
            targetPanel.SetActive(true);

        if (targetName != null)
            targetName.text = line.name;

        // 대사 색상 적용
        if (targetDialogue != null)
            targetDialogue.color = line.textColor;

        targetDialogue.text = "";

        foreach (char letter in line.sentence.ToCharArray())
        {
            targetDialogue.text += letter;
            yield return new WaitForSeconds(typingSpeed);
        }
    }

    void EndDialogue()
    {
        // 프리팹 켜기
        if (endPrefab != null)
            endPrefab.SetActive(true);

        // 1초 뒤 씬 전환
        StartCoroutine(LoadNextSceneAfterDelay());
    }

    IEnumerator LoadNextSceneAfterDelay()
    {
        yield return new WaitForSeconds(1f);

        if (!string.IsNullOrEmpty(nextSceneName))
        {
            SceneManager.LoadScene(nextSceneName);
        }
        else
        {
            Debug.LogWarning("다음 씬 이름이 Inspector에서 설정되지 않았습니다!");
        }
    }
}