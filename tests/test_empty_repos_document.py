"""Tests for bitbucket-empty-repos.json builder."""

from common.empty_repos_document import build_empty_repos_document


def test_build_empty_repos_document_filters_and_sorts() -> None:
    rows = [
        {
            "repository_path": "P2/s",
            "repository_name": "s",
            "bitbucket_project_name": "P2",
            "is_empty": True,
        },
        {
            "repository_path": "P1/s",
            "repository_name": "s",
            "bitbucket_project_name": "P1",
            "is_empty": True,
        },
        {
            "repository_path": "P1/full",
            "repository_name": "full",
            "bitbucket_project_name": "P1",
            "is_empty": False,
        },
    ]
    doc = build_empty_repos_document(rows, source="bitbucket")
    assert doc["version"] == 1
    assert doc["source"] == "bitbucket"
    assert len(doc["repositories"]) == 2
    assert doc["repositories"][0]["repository_path"] == "P1/s"
    assert doc["repositories"][1]["repository_path"] == "P2/s"


def test_build_empty_repos_document_empty_list() -> None:
    doc = build_empty_repos_document([], source="bitbucket")
    assert doc["repositories"] == []


def test_build_empty_repos_document_github_uses_github_org() -> None:
    rows = [
        {
            "repository_path": "snyk-ps/marketplace",
            "repository_name": "marketplace",
            "github_org": "snyk-ps",
            "is_empty": True,
        },
        {
            "repository_path": "snyk-ps/full",
            "repository_name": "full",
            "github_org": "snyk-ps",
            "is_empty": False,
        },
    ]
    doc = build_empty_repos_document(rows, source="github")
    assert doc["source"] == "github"
    assert len(doc["repositories"]) == 1
    entry = doc["repositories"][0]
    assert entry["github_org"] == "snyk-ps"
    assert "bitbucket_project_name" not in entry
