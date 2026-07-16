"""Tests for branch mismatch delete (display_name match)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from integrations.snyk.client import SnykRestClient
from snyk.branch_mismatch_delete import (
    BranchMismatchDeleteOptions,
    load_delete_manifest,
    run_branch_mismatch_delete,
)
from snyk.branch_mismatch_reimport import DiffEntry


def _target(
    *,
    target_id: str = "tgt-1",
    display_name: str = "BB/my-service",
) -> dict[str, object]:
    return {
        "id": target_id,
        "attributes": {"display_name": display_name},
    }


def _detail() -> dict[str, object]:
    return {
        "id": "tgt-1",
        "attributes": {
            "display_name": "BB/my-service",
            "projectKey": "P1",
            "repoSlug": "my-service",
        },
        "relationships": {"integration": {"data": {"id": "int-1"}}},
    }


def test_run_branch_mismatch_delete_dry_run() -> None:
    entry = DiffEntry(
        apm_code="ORG1",
        repository_name="BB/my-service",
        production_branch="master",
        target_reference="develop",
    )
    client = MagicMock(spec=SnykRestClient)
    client.group_id = "group-uuid"
    client.iter_group_orgs.return_value = [{"id": "org-1", "name": "ORG1"}]
    client.iter_org_targets.return_value = [_target()]

    report = run_branch_mismatch_delete(
        client,
        [entry],
        BranchMismatchDeleteOptions(dry_run=True),
    )

    assert report["skipped"][0]["reason"] == "dry_run"
    client.delete_org_target.assert_not_called()


def test_run_branch_mismatch_delete_matches_without_target_branch() -> None:
    """Targets API may omit target_reference; match by display_name only."""
    entry = DiffEntry(
        apm_code="ORG1",
        repository_name="BB/my-service",
        production_branch="snyk-pr-scan-test",
        target_reference="master",
    )
    client = MagicMock(spec=SnykRestClient)
    client.group_id = "group-uuid"
    client.iter_group_orgs.return_value = [{"id": "org-1", "name": "ORG1"}]
    client.iter_org_targets.return_value = [
        {
            "id": "tgt-1",
            "attributes": {"display_name": "BB/my-service"},
        },
    ]
    client.get_org_target.return_value = _detail()

    report = run_branch_mismatch_delete(
        client,
        [entry],
        BranchMismatchDeleteOptions(),
    )

    assert len(report["deleted"]) == 1
    client.delete_org_target.assert_called_once_with("org-1", "tgt-1")


def test_run_branch_mismatch_delete_ambiguous() -> None:
    entry = DiffEntry(
        apm_code="ORG1",
        repository_name="BB/my-service",
        production_branch="master",
        target_reference="develop",
    )
    client = MagicMock(spec=SnykRestClient)
    client.group_id = "group-uuid"
    client.iter_group_orgs.return_value = [{"id": "org-1", "name": "ORG1"}]
    client.iter_org_targets.return_value = [
        _target(target_id="tgt-a"),
        _target(target_id="tgt-b"),
    ]

    report = run_branch_mismatch_delete(client, [entry], BranchMismatchDeleteOptions())

    assert len(report["ambiguous"]) == 1


def test_run_branch_mismatch_delete_writes_manifest(tmp_path: Path) -> None:
    entry = DiffEntry(
        apm_code="ORG1",
        repository_name="BB/my-service",
        production_branch="master",
        target_reference="develop",
    )
    client = MagicMock(spec=SnykRestClient)
    client.group_id = "group-uuid"
    client.iter_group_orgs.return_value = [{"id": "org-1", "name": "ORG1"}]
    client.iter_org_targets.return_value = [_target()]
    client.get_org_target.return_value = _detail()
    manifest_path = tmp_path / "manifest.json"

    run_branch_mismatch_delete(
        client,
        [entry],
        BranchMismatchDeleteOptions(manifest_path=manifest_path),
    )

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["version"] == 1
    assert len(data["entries"]) == 1
    row = data["entries"][0]
    assert row["integration_id"] == "int-1"
    assert row["production_branch"] == "master"
    load_delete_manifest(manifest_path)


def test_load_delete_manifest_rejects_invalid(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps({"entries": [{"apm_code": "org-a"}]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="org_id"):
        load_delete_manifest(path)
