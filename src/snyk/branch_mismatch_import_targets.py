"""Build snyk-api-import batch files from a branch-mismatch delete manifest."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from snyk.branch_mismatch_delete import load_delete_manifest
from snyk.branch_mismatch_reimport import build_import_payload
from snyk.outputs import batch_import_output_paths

IMPORT_TARGETS_REPORT_VERSION = 1


@dataclass(frozen=True)
class BranchMismatchImportTargetsOptions:
    """Runtime options for generating reimport target batch files."""

    repos_per_batch: int = 50
    output_dir: Path | None = None
    output_stem: str = "branch-reimport-batch"


def build_import_payloads_from_manifest(
    manifest_entries: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Turn manifest rows into snyk-api-import target payloads."""
    out: list[dict[str, Any]] = []
    for row in manifest_entries:
        out.append(
            build_import_payload(
                org_id=row["org_id"],
                integration_id=row["integration_id"],
                project_key=row["project_key"],
                repo_slug=row["repo_slug"],
                repository_name=row["repository_name"],
                production_branch=row["production_branch"],
            ),
        )
    return out


def run_branch_mismatch_import_targets(
    manifest_path: Path,
    options: BranchMismatchImportTargetsOptions,
) -> dict[str, Any]:
    """Write one or more snyk-api-import batch JSON files from a delete manifest."""
    if options.repos_per_batch < 1:
        msg = "repos_per_batch must be >= 1"
        raise ValueError(msg)

    manifest_entries = load_delete_manifest(manifest_path)
    payloads = build_import_payloads_from_manifest(manifest_entries)
    if not payloads:
        return {
            "version": IMPORT_TARGETS_REPORT_VERSION,
            "manifest": str(manifest_path),
            "target_count": 0,
            "batch_files": [],
        }

    batch_dir = options.output_dir or Path(".")
    batch_dir.mkdir(parents=True, exist_ok=True)
    batch_size = options.repos_per_batch
    num_batches = (len(payloads) + batch_size - 1) // batch_size
    paths = batch_import_output_paths(
        batch_dir / f"{options.output_stem}.json",
        num_batches,
    )
    batch_files: list[dict[str, Any]] = []

    for batch_index, batch_path in enumerate(paths):
        start = batch_index * batch_size
        batch_payloads = payloads[start : start + batch_size]
        batch_doc = {"targets": batch_payloads}
        batch_path.write_text(json.dumps(batch_doc, indent=2), encoding="utf-8")
        batch_files.append(
            {
                "file": str(batch_path),
                "target_count": len(batch_payloads),
            },
        )

    return {
        "version": IMPORT_TARGETS_REPORT_VERSION,
        "manifest": str(manifest_path),
        "target_count": len(payloads),
        "batch_files": batch_files,
    }
