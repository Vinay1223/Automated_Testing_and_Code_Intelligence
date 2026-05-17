def test_runs_require_bearer_token(client):
    r = client.post("/v1/runs", json={"repo_path": ".", "function_name": "x"})
    assert r.status_code == 401


def test_dev_bearer_token_is_accepted(client, sample_repo, auth_headers):
    payload = {
        "repo_path": str(sample_repo),
        "function_name": "add_numbers",
        "language": "python",
        "framework": "pytest",
    }
    r = client.post("/v1/runs", json=payload, headers=auth_headers)
    assert r.status_code == 200, r.text
