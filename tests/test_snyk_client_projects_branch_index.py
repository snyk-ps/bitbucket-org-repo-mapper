"""Tests for Projects API target branch index."""

from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import patch

from config.snyk_settings import SnykSettings
from integrations.snyk.client import (
    SnykRestClient,
    build_project_target_branch_index,
    target_branch_from_rest_project_item,
)


def _settings() -> SnykSettings:
    return SnykSettings(
        token="t",
        group_id="group-uuid",
        api_origin="https://api.snyk.io",
        rest_root="https://api.snyk.io/rest",
        v1_root="https://api.snyk.io/v1",
        integrations_api="v1",
        api_version="2024-10-15",
        http_max_attempts=1,
        http_backoff_seconds=0.0,
    )


def test_target_branch_from_rest_project_item() -> None:
    item = {
        "id": "proj-1",
        "attributes": {
            "origin": "bitbucket-server",
            "target_reference": "master",
        },
        "relationships": {"target": {"data": {"id": "tgt-1"}}},
    }
    assert target_branch_from_rest_project_item(item) == ("tgt-1", "master")


def test_target_branch_from_rest_project_item_skips_other_origin() -> None:
    item = {
        "id": "proj-1",
        "attributes": {"origin": "github", "target_reference": "main"},
        "relationships": {"target": {"data": {"id": "tgt-1"}}},
    }
    assert target_branch_from_rest_project_item(item) is None


def test_build_project_target_branch_index_first_wins() -> None:
    items = [
        {
            "attributes": {
                "origin": "bitbucket-server",
                "target_reference": "develop",
            },
            "relationships": {"target": {"data": {"id": "tgt-1"}}},
        },
        {
            "attributes": {
                "origin": "bitbucket-server",
                "target_reference": "master",
            },
            "relationships": {"target": {"data": {"id": "tgt-1"}}},
        },
    ]
    assert build_project_target_branch_index(items) == {"tgt-1": "develop"}


def test_build_org_project_target_branch_index_pagination() -> None:
    calls: list[str] = []

    def fake_urlopen(req: object, timeout: float | None = None) -> object:
        url = getattr(req, "full_url", "")
        calls.append(url)
        if "starting_after" not in url:
            body = json.dumps(
                {
                    "data": [
                        {
                            "id": "p1",
                            "attributes": {
                                "origin": "bitbucket-server",
                                "target_reference": "master",
                            },
                            "relationships": {"target": {"data": {"id": "tgt-1"}}},
                        },
                    ],
                    "links": {
                        "next": "/rest/orgs/org-uuid/projects?version=2024-10-15&limit=100&starting_after=cursor",
                    },
                }
            ).encode()
        else:
            body = json.dumps(
                {
                    "data": [
                        {
                            "id": "p2",
                            "attributes": {
                                "origin": "bitbucket-server",
                                "target_reference": "develop",
                            },
                            "relationships": {"target": {"data": {"id": "tgt-2"}}},
                        },
                    ],
                    "links": {},
                }
            ).encode()
        return BytesIO(body)

    client = SnykRestClient(_settings())
    with patch("integrations.snyk.client.urlopen", side_effect=fake_urlopen):
        index = client.build_org_project_target_branch_index("org-uuid")

    assert index == {"tgt-1": "master", "tgt-2": "develop"}
    assert len(calls) == 2
