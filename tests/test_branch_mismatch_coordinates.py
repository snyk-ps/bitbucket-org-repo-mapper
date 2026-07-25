"""Tests for branch mismatch reimport coordinate resolution."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from snyk.branch_mismatch_reimport import (
    DiffEntry,
    load_discovery_coordinate_index,
    resolve_reimport_coordinates,
)


def _entry(**overrides: str) -> DiffEntry:
    defaults = {
        "apm_code": "ABCD",
        "repository_name": "UATPROJ/uat-bitbucket-java-sample",
        "production_branch": "master",
        "target_reference": "develop",
    }
    defaults.update(overrides)
    return DiffEntry(**defaults)


def _target_detail(*, project_key: str = "P1", repo_slug: str = "my-service") -> dict[str, object]:
    return {
        "id": "tgt-1",
        "attributes": {
            "display_name": "BB/my-service",
            "projectKey": project_key,
            "repoSlug": repo_slug,
        },
    }


def test_resolve_reimport_coordinates_from_target() -> None:
    coords = resolve_reimport_coordinates(_target_detail(), _entry())
    assert coords.project_key == "P1"
    assert coords.repo_slug == "my-service"
    assert coords.coordinate_source == "target"


def test_resolve_reimport_coordinates_discovery_fallback() -> None:
    detail = {
        "id": "tgt-1",
        "attributes": {"display_name": "UATPROJ/uat-bitbucket-java-sample"},
        "relationships": {"integration": {"data": {"id": "int-1"}}},
    }
    index = {
        "UATPROJ/uat-bitbucket-java-sample": [
            ("ABCD", "UATPROJ", "uat-bitbucket-java-sample"),
        ],
    }
    coords = resolve_reimport_coordinates(detail, _entry(), index)
    assert coords.project_key == "UATPROJ"
    assert coords.repo_slug == "uat-bitbucket-java-sample"
    assert coords.coordinate_source == "discovery"


def test_resolve_reimport_coordinates_fail_closed_without_discovery() -> None:
    detail = {"id": "tgt-1", "attributes": {"display_name": "BB/foo"}}
    with pytest.raises(ValueError, match="pass --discovery"):
        resolve_reimport_coordinates(detail, _entry())


def test_resolve_reimport_coordinates_discovery_not_found() -> None:
    detail = {"id": "tgt-1", "attributes": {"display_name": "BB/foo"}}
    index: dict[str, list[tuple[str | None, str, str]]] = {}
    with pytest.raises(ValueError, match="discovery_not_found"):
        resolve_reimport_coordinates(detail, _entry(), index)


def test_resolve_reimport_coordinates_ambiguous_discovery() -> None:
    detail = {"id": "tgt-1", "attributes": {"display_name": "PROJ/shared"}}
    index = {
        "PROJ/shared": [
            ("ORG1", "P1", "shared"),
            ("ORG2", "P2", "shared"),
        ],
    }
    entry = _entry(apm_code="ORG1", repository_name="PROJ/shared")
    coords = resolve_reimport_coordinates(detail, entry, index)
    assert coords.project_key == "P1"
    assert coords.coordinate_source == "discovery"

    with pytest.raises(ValueError, match="ambiguous_discovery"):
        resolve_reimport_coordinates(
            detail,
            _entry(apm_code="ORG1", repository_name="PROJ/shared"),
            {
                "PROJ/shared": [
                    ("ORG1", "P1", "shared"),
                    ("ORG1", "P2", "shared"),
                ],
            },
        )


def test_load_discovery_coordinate_index_by_repository_path(tmp_path: Path) -> None:
    path = tmp_path / "discovery.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "source": "bitbucket",
                "rows": [
                    {
                        "repository_path": "UATPROJ/uat-bitbucket-java-sample",
                        "repository_name": "BB/uat-bitbucket-java-sample",
                        "apm_code": "ABCD",
                        "production_branch": "master",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    index = load_discovery_coordinate_index(path)
    assert index["UATPROJ/uat-bitbucket-java-sample"] == [
        ("ABCD", "UATPROJ", "uat-bitbucket-java-sample"),
    ]
    assert "BB/uat-bitbucket-java-sample" not in index


def test_load_discovery_coordinate_index_juice_shop_path_matches_diff(tmp_path: Path) -> None:
    """Diff repository_name matches repository_path; discovery slug differs."""
    path = tmp_path / "discovery.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "source": "bitbucket",
                "rows": [
                    {
                        "repository_path": "tcannell-test/juice-shop",
                        "repository_name": "juice-shop",
                        "apm_code": "ABCD",
                        "production_branch": "main",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    index = load_discovery_coordinate_index(path)
    assert index["tcannell-test/juice-shop"] == [
        ("ABCD", "tcannell-test", "juice-shop"),
    ]
    detail = {
        "id": "tgt-1",
        "attributes": {"display_name": "tcannell-test/juice-shop"},
    }
    entry = DiffEntry(
        apm_code="ABCD",
        repository_name="tcannell-test/juice-shop",
        production_branch="main",
        target_reference="other-branch",
    )
    coords = resolve_reimport_coordinates(detail, entry, index)
    assert coords.project_key == "tcannell-test"
    assert coords.repo_slug == "juice-shop"
