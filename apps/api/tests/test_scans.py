def test_scan_returns_targets_and_coverage(client, sample_repo, auth_headers):
    r = client.post(
        "/v1/scans",
        json={"repo_path": str(sample_repo)},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    names = {t["name"] for t in body["targets"]}
    assert {"add_numbers", "divide_numbers"} <= names
    assert body["total"] >= 2
    assert 0.0 <= body["coverage_pct"] <= 100.0


def test_scan_404_for_missing_path(client, auth_headers):
    r = client.post(
        "/v1/scans",
        json={"repo_path": "/nonexistent/path-does-not-exist"},
        headers=auth_headers,
    )
    assert r.status_code == 404
