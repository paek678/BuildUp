using System.Collections;
using UnityEngine;

[RequireComponent(typeof(Rigidbody))]

public class RopeAction : MonoBehaviour
{
    public float grappleRange = 50f;       // ���� �����Ÿ�
    public float launchSpeed = 50f;        // ���ư��� �ʱ� �ӵ�
    public LineRenderer lineRenderer;      // ���� �ð�ȭ�� LineRenderer
    public float stopDistance = 2f;        // ��ǥ �������� �ּ� �Ÿ�

    private Rigidbody rb;
    private bool isGrappling = false;
    private Vector3 grapplePoint;

    void Awake()
    {
        rb = GetComponent<Rigidbody>();
    }

    void Update()
    {
        // ���콺 ���� ��ư Ŭ�� �� ���� �߻�
        if (Input.GetMouseButtonDown(0) && !isGrappling)
        {
            ShootGrapple();
        }

        // ���� ������Ʈ
        if (isGrappling)
        {
            lineRenderer.SetPosition(0, transform.position);
            lineRenderer.SetPosition(1, grapplePoint);

            if (Vector3.Distance(transform.position, grapplePoint) < stopDistance)
            {
                StopGrapple();
            }
        }
    }

    void ShootGrapple()
    {
        // ���콺 ������ ��ġ���� Ray ����
        Ray ray = Camera.main.ScreenPointToRay(Input.mousePosition);
        RaycastHit hit;

        if (Physics.Raycast(ray, out hit, grappleRange))
        {
            // y���� ���� �÷��̾� ��ġ�� ����
            grapplePoint = new Vector3(hit.point.x, transform.position.y, hit.point.z);

            isGrappling = true;

            lineRenderer.enabled = true;
            lineRenderer.SetPosition(1, grapplePoint);

            LaunchTowardsPoint();
        }
    }

    void LaunchTowardsPoint()
    {
        Vector3 direction = (grapplePoint - transform.position).normalized;

        // ���� �ӵ� �ʱ�ȭ �� ���� �ӵ� �ο�
        rb.linearVelocity = Vector3.zero;
        rb.AddForce(direction * launchSpeed, ForceMode.VelocityChange);
    }

    void StopGrapple()
    {
        isGrappling = false;
        rb.linearVelocity = Vector3.zero;
        lineRenderer.enabled = false;
    }


}