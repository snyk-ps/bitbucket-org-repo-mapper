"""Tests for branch mismatch import target batch generation."""

from __future__ import annotations

import json
from pathlib import Path

from snyk.branch_mismatch_import_targets import (
    BranchMismatchImportTargetsOptions,
    build_import_payloads_from_manifest,
    run_branch_mismatch_import_targets,
)


def test_build_import_payloads_from_manifest() -> None:
    rows = [
        {
            "apm_code": "ORG1",
            "org_id": "org-1",
            "target_id": "tgt-1",
            "integration_id": "int-1",
            "project_key": "P1",
            "repo_slug": "my-service",
            "repository_name": "BB/my-service",
            "production_branch": "master",
        },
    ]
    payloads = build_import_payloads_from_manifest(rows)
    assert payloads[0]["orgId"] == "org-1"
    assert payloads[0]["target"]["branch"] == "master"
    assert payloads[0]["target"]["name"] == "BB/my-service"


def test_run_branch_mismatch_import_targets_writes_batches(tmp_path: Path) -> None:
    manifest = {
        "version": 1,
        "group_id": "group-uuid",
        "entries": [
            {
                "apm_code": "ORG1",
                "org_id": "org-1",
                "target_id": "tgt-1",
                "integration_id": "int-1",
                "project_key": "P1",
                "repo_slug": "my-service",
                "repository_name": "BB/my-service",
                "production_branch": "master",
            },
        ],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = run_branch_mismatch_import_targets(
        manifest_path,
        BranchMismatchImportTargetsOptions(output_dir=tmp_path),
    )

    assert report["target_count"] == 1
    batch_file = Path(report["batch_files"][0]["file"])
    assert batch_file.exists()
    batch = json.loads(batch_file.read_text(encoding="utf-8"))
    assert len(batch["targets"]) == 1
