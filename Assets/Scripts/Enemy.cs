using UnityEngine;
using System.Collections;

public class Enemy : MonoBehaviour
{
    [Header("Stats")]
    public float maxHealth = 100f;
    public float curHealth;
    public bool isDead = false;

    [Header("References")]
    public Transform player;
    public Animator anim;
    public MeshRenderer[] meshs;
    public Rigidbody rigid;
    public BoxCollider boxCollider;

    [Header("Damage Feedback")]
    public Color damageColor = Color.red;
    public float damageFlashDuration = 0.2f;


    public bool canLook = true;


    protected virtual void Awake()
    {
        curHealth = maxHealth;
        rigid = GetComponent<Rigidbody>();
        boxCollider = GetComponent<BoxCollider>();
        meshs = GetComponentsInChildren<MeshRenderer>();
        anim = GetComponentInChildren<Animator>();
    }

    protected virtual void Update()
    {
        if (isDead) return;
        if (canLook) FacePlayer();


    }

    protected void FacePlayer()
    {
        if (player == null) return;

        Vector3 dir = player.position - transform.position;
        dir.y = 0;
        if (dir != Vector3.zero)
            transform.rotation = Quaternion.LookRotation(dir);
    }

    public virtual void TakeDamage(int damage)
    {
        if (isDead) return;

        curHealth -= damage;
        curHealth = Mathf.Max(curHealth, 0);

        ShowDamageFeedback();

        if (curHealth <= 0)
            Die();
    }

    protected void ShowDamageFeedback()
    {
        foreach (MeshRenderer mesh in meshs)
            mesh.material.color = damageColor;

        Invoke(nameof(ResetColor), damageFlashDuration);
    }

    protected void ResetColor()
    {
        foreach (MeshRenderer mesh in meshs)
            mesh.material.color = Color.white;
    }

    protected virtual void Die()
    {
        if (isDead) return;

        isDead = true;
        anim.SetTrigger("Die");
        StartCoroutine(DelayedDestroy());
    }


    IEnumerator DelayedDestroy()
    {
        yield return new WaitForSeconds(2f);
        Destroy(gameObject);
    }
}
