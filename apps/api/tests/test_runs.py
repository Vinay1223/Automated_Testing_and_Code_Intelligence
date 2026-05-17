from uuid import UUID


def test_create_run_uses_mock_provider_and_passes(client, sample_repo, auth_headers):
    r = client.post(
        "/v1/runs",
        json={
            "repo_path": str(sample_repo),
            "function_name": "divide_numbers",
            "language": "python",
            "framework": "pytest",
            "max_retries": 1,
        },
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    UUID(body["id"])
    assert body["state"] in {"passed", "failed"}
    assert body["target"]["name"] == "divide_numbers"


def test_get_run_round_trip(client, sample_repo, auth_headers):
    created = client.post(
        "/v1/runs",
        json={
            "repo_path": str(sample_repo),
            "function_name": "add_numbers",
            "language": "python",
            "framework": "pytest",
            "max_retries": 1,
        },
        headers=auth_headers,
    ).json()
    run_id = created["id"]
    fetched = client.get(f"/v1/runs/{run_id}", headers=auth_headers).json()
    assert fetched["id"] == run_id
