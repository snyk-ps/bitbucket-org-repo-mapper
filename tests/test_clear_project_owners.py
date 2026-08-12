"""Tests for project owner cleanup script and orchestration."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from snyk.clear_project_owners import (
    ClearProjectOwnerOptions,
    parse_org_ids,
    run_clear_project_owners,
)

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "clear_project_owners.py"


def _script_main():
    spec = importlib.util.spec_from_file_location(
        "clear_project_owners_script",
        _SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.main


def test_parse_org_ids_valid() -> None:
    assert parse_org_ids("a,b, c") == ["a", "b", "c"]


def test_parse_org_ids_rejects_empty() -> None:
    with pytest.raises(ValueError, match="at least one org UUID"):
        parse_org_ids("  ,  ")


def test_run_clear_project_owners_dry_run() -> None:
    client = MagicMock()
    client.iter_org_projects.return_value = [
        {"id": "p1", "name": "App", "type": "npm", "owner_id": "user-1"},
        {"id": "p2", "name": "Lib", "type": "npm"},
    ]
    options = ClearProjectOwnerOptions(
        org_ids=["org-1"],
        dry_run=True,
    )

    report = run_clear_project_owners(client, options)

    assert report["version"] == 1
    assert report["org_ids"] == ["org-1"]
    assert len(report["skipped"]) == 2
    assert all(entry["reason"] == "dry_run" for entry in report["skipped"])
    assert report["cleared"] == []
    client.clear_project_owner.assert_not_called()


def test_run_clear_project_owners_skips_unassigned() -> None:
    client = MagicMock()
    client.iter_org_projects.return_value = [
        {"id": "p1", "name": "App", "type": "npm"},
    ]
    options = ClearProjectOwnerOptions(org_ids=["org-1"])

    report = run_clear_project_owners(client, options)

    assert report["skipped"] == [
        {
            "org_id": "org-1",
            "org_name": "org-1",
            "project_id": "p1",
            "project_name": "App",
            "project_type": "npm",
            "reason": "already_unassigned",
        }
    ]
    client.clear_project_owner.assert_not_called()


def test_run_clear_project_owners_clears_assigned() -> None:
    client = MagicMock()
    client.iter_org_projects.return_value = [
        {"id": "p1", "name": "App", "type": "npm", "owner_id": "user-1"},
    ]
    options = ClearProjectOwnerOptions(org_ids=["org-1"])

    report = run_clear_project_owners(client, options)

    client.clear_project_owner.assert_called_once_with("org-1", "p1")
    assert report["cleared"] == [
        {
            "org_id": "org-1",
            "org_name": "org-1",
            "project_id": "p1",
            "project_name": "App",
            "project_type": "npm",
        }
    ]


def test_run_clear_project_owners_records_failure_and_continues() -> None:
    client = MagicMock()
    client.iter_org_projects.return_value = [
        {"id": "p1", "name": "App", "type": "npm", "owner_id": "user-1"},
        {"id": "p2", "name": "Lib", "type": "npm", "owner_id": "user-2"},
    ]
    client.clear_project_owner.side_effect = [
        RuntimeError("HTTP 403"),
        None,
    ]
    options = ClearProjectOwnerOptions(org_ids=["org-1"])

    report = run_clear_project_owners(client, options)

    assert len(report["failed"]) == 1
    assert report["failed"][0]["project_id"] == "p1"
    assert len(report["cleared"]) == 1
    assert report["cleared"][0]["project_id"] == "p2"


def test_run_clear_project_owners_respects_limit() -> None:
    client = MagicMock()
    client.iter_org_projects.return_value = [
        {"id": "p1", "name": "One", "type": "npm", "owner_id": "user-1"},
        {"id": "p2", "name": "Two", "type": "npm", "owner_id": "user-2"},
    ]
    options = ClearProjectOwnerOptions(org_ids=["org-1"], limit=1)

    report = run_clear_project_owners(client, options)

    assert len(report["cleared"]) == 1
    client.clear_project_owner.assert_called_once_with("org-1", "p1")


def test_run_clear_project_owners_group_scope() -> None:
    client = MagicMock()
    client.iter_group_orgs.return_value = [{"id": "org-1", "name": "APM1"}]
    client.iter_org_projects.return_value = []
    options = ClearProjectOwnerOptions(group_id="group-1")

    report = run_clear_project_owners(client, options)

    client.iter_group_orgs.assert_called_once_with(group_id="group-1")
    assert report["group_id"] == "group-1"


def test_clear_project_owners_cli_rejects_both_scope_flags() -> None:
    main = _script_main()
    with pytest.raises(SystemExit) as exc:
        main(["--group", "g1", "--orgs", "o1"])
    assert exc.value.code == 2


def test_clear_project_owners_cli_rejects_empty_orgs() -> None:
    main = _script_main()
    assert main(["--orgs", "  , "]) == 2
