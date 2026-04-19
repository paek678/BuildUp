using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement; // 추가
using System.Collections;

public class PrologueText : MonoBehaviour
{
    public Text text1;
    public Text text2;
    public Text text3;
    public Text text4;

    public GameObject targetPrefab; // 마지막에 켜질 프리팹
    public GameObject canvas1;      // 기존 Canvas

    public string nextSceneName;    // 전환할 씬 이름

    void Start()
    {
        text1.gameObject.SetActive(false);
        text2.gameObject.SetActive(false);
        text3.gameObject.SetActive(false);
        text4.gameObject.SetActive(false);

        if (targetPrefab != null)
            targetPrefab.SetActive(false);

        canvas1.SetActive(true);

        StartCoroutine(PlaySequence());
    }

    IEnumerator PlaySequence()
    {
        yield return StartCoroutine(FadeText(text1, 0f, 1f, 2f));

        yield return new WaitForSeconds(2f);
        yield return StartCoroutine(FadeText(text1, 1f, 0f, 2f));

        StartCoroutine(FadeText(text2, 0f, 1f, 2f));
        yield return StartCoroutine(FadeText(text3, 0f, 1f, 2f));

        yield return new WaitForSeconds(1f);
        yield return StartCoroutine(TypewriterEffect(text4, "자신이 꿈을 꾸고 있다는 것을 인지하고 있는 상태에서 꿈을 꾸는 것"));

        yield return new WaitForSeconds(3f);

        StartCoroutine(FadeText(text1, text1.color.a, 0f, 2f));
        StartCoroutine(FadeText(text2, text2.color.a, 0f, 2f));
        StartCoroutine(FadeText(text3, text3.color.a, 0f, 2f));
        StartCoroutine(FadeText(text4, text4.color.a, 0f, 2f));

        yield return new WaitForSeconds(1.55f);
        if (targetPrefab != null)
            targetPrefab.SetActive(true);

        // Canvas 전환 대신 Scene 전환
        yield return new WaitForSeconds(2f);
        SceneManager.LoadScene(nextSceneName);
    }

    IEnumerator FadeText(Text txt, float startAlpha, float endAlpha, float duration)
    {
        txt.gameObject.SetActive(true);

        float time = 0f;
        Color c = txt.color;
        c.a = startAlpha;
        txt.color = c;

        while (time < duration)
        {
            float t = time / duration;
            c.a = Mathf.Lerp(startAlpha, endAlpha, t);
            txt.color = c;
            time += Time.deltaTime;
            yield return null;
        }

        c.a = endAlpha;
        txt.color = c;

        if (endAlpha <= 0f)
            txt.gameObject.SetActive(false);
    }

    IEnumerator TypewriterEffect(Text txt, string message)
    {
        txt.gameObject.SetActive(true);
        txt.text = "";
        foreach (char c in message)
        {
            txt.text += c;
            yield return new WaitForSeconds(0.1f);
        }
    }
}