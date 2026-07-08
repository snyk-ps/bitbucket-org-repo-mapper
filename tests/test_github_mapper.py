"""Tests for GitHub discovery mapping."""

from __future__ import annotations

import re
from unittest.mock import MagicMock

import pytest

from common.github_mapper import (
    DEFAULT_APM_TOPIC_REGEX,
    apm_code_from_topics,
    compile_apm_topic_regex,
    iter_github_mapping,
)


def test_apm_code_from_topics_extracts_capture_group() -> None:
    pattern = re.compile(DEFAULT_APM_TOPIC_REGEX)
    assert apm_code_from_topics(["apm-ABC1"], pattern) == "ABC1"


def test_apm_code_from_topics_returns_none_without_match() -> None:
    pattern = re.compile(DEFAULT_APM_TOPIC_REGEX)
    assert apm_code_from_topics(["other-topic"], pattern) is None


def test_apm_code_from_topics_uses_first_lexicographic_match() -> None:
    pattern = re.compile(DEFAULT_APM_TOPIC_REGEX)
    assert apm_code_from_topics(["apm-DEF2", "apm-ABC1"], pattern) == "ABC1"


def test_compile_apm_topic_regex_rejects_invalid_pattern() -> None:
    with pytest.raises(ValueError, match="invalid --apm-topic-regex"):
        compile_apm_topic_regex("[")


def test_compile_apm_topic_regex_requires_capture_group() -> None:
    with pytest.raises(ValueError, match="exactly one capture group"):
        compile_apm_topic_regex("^apm-.+$")


def test_iter_github_mapping_empty_repo_skips_yaml_and_topics() -> None:
    client = MagicMock()
    client.iter_org_repositories.return_value = [
        {"name": "empty-repo", "default_branch": "main"},
    ]
    client.repository_latest_commit.return_value = None
    pattern = re.compile(DEFAULT_APM_TOPIC_REGEX)

    rows = list(
        iter_github_mapping(
            client,
            "appsec.yaml",
            ["acme"],
            completed_keys=set(),
            apm_topic_pattern=pattern,
        )
    )

    assert len(rows) == 1
    assert rows[0]["is_empty"] is True
    assert rows[0]["repository_path"] == "acme/empty-repo"
    assert rows[0]["github_org"] == "acme"
    assert "bitbucket_project_name" not in rows[0]
    client.fetch_file_contents.assert_not_called()
    client.repository_topics.assert_not_called()


def test_iter_github_mapping_non_empty_uses_topic_apm_and_yaml_branch() -> None:
    client = MagicMock()
    client.iter_org_repositories.return_value = [
        {"name": "svc", "default_branch": "main"},
    ]
    client.repository_latest_commit.return_value = {
        "commit": {
            "committer": {"name": "charlie", "email": "charlie@example.com", "date": "2024-01-01T00:00:00Z"},
            "author": {"name": "charlie", "email": "charlie@example.com", "date": "2024-01-01T00:00:00Z"},
        }
    }
    client.repository_topics.return_value = ["apm-ABC1"]
    yaml_text = b"security:\n  apmCode: ZZZZ\n  productionBranch: develop\n"
    client.fetch_file_contents.return_value = yaml_text
    pattern = re.compile(DEFAULT_APM_TOPIC_REGEX)

    rows = list(
        iter_github_mapping(
            client,
            "appsec.yaml",
            ["acme"],
            completed_keys=set(),
            apm_topic_pattern=pattern,
        )
    )

    assert len(rows) == 1
    assert rows[0]["is_empty"] is False
    assert rows[0]["github_org"] == "acme"
    assert rows[0]["apm_code"] == "ABC1"
    assert rows[0]["production_branch"] == "develop"
    assert "bitbucket_project_name" not in rows[0]
    client.fetch_file_contents.assert_called_once_with(
        "acme",
        "svc",
        "appsec.yaml",
        ref="main",
    )
    client.repository_topics.assert_called_once_with("acme", "svc")
