"""Delete Snyk targets for branch mismatch remediation (display_name match only)."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from integrations.snyk.client import SnykRestClient
from snyk.branch_mismatch_reimport import (
    DiffEntry,
    DiscoveryCoordinateIndex,
    _entry_record,
    _repo_slug_from_repository_name,
    load_discovery_coordinate_index,
    resolve_reimport_coordinates,
    target_display_name,
    target_integration_id,
)
from snyk.enrichment import build_name_to_org_id

DELETE_REPORT_VERSION = 1
MANIFEST_VERSION = 1

_REQUIRED_MANIFEST_KEYS = (
    "apm_code",
    "org_id",
    "target_id",
    "integration_id",
    "project_key",
    "repo_slug",
    "repository_name",
    "production_branch",
)


@dataclass(frozen=True)
class BranchMismatchDeleteOptions:
    """Runtime options for branch mismatch target deletion."""

    dry_run: bool = False
    limit: int | None = None
    delay_ms: int = 0
    manifest_path: Path | None = None
    discovery_path: Path | None = None


def _empty_delete_buckets() -> dict[str, list[dict[str, Any]]]:
    return {
        "deleted": [],
        "skipped": [],
        "not_found": [],
        "ambiguous": [],
        "failed": [],
    }


def _find_targets_by_display_name(
    targets: list[dict[str, Any]],
    entry: DiffEntry,
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for target in targets:
        display = target_display_name(target)
        if display == entry.repository_name:
            matches.append(target)
    return matches


def _target_not_found_diagnostics(
    targets: list[dict[str, Any]],
    entry: DiffEntry,
) -> dict[str, Any]:
    near_match_names: list[str] = []
    slug = _repo_slug_from_repository_name(entry.repository_name)
    for target in targets:
        display = target_display_name(target)
        if display is None:
            continue
        if display != entry.repository_name and slug and slug in display:
            if display not in near_match_names:
                near_match_names.append(display)
    out: dict[str, Any] = {"candidates_returned": len(targets)}
    if near_match_names:
        out["near_match_display_names"] = near_match_names
    return out


def _manifest_entry(
    entry: DiffEntry,
    *,
    org_id: str,
    target_id: str,
    integration_id: str,
    project_key: str,
    repo_slug: str,
    coordinate_source: str | None = None,
) -> dict[str, str]:
    row = {
        "apm_code": entry.apm_code,
        "org_id": org_id,
        "target_id": target_id,
        "integration_id": integration_id,
        "project_key": project_key,
        "repo_slug": repo_slug,
        "repository_name": entry.repository_name,
        "production_branch": entry.production_branch,
    }
    if coordinate_source is not None:
        row["coordinate_source"] = coordinate_source
    return row


def load_delete_manifest(path: Path) -> list[dict[str, str]]:
    """Load and validate a delete manifest written by the delete script."""
    parsed = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        msg = "delete manifest must be a JSON object"
        raise ValueError(msg)
    entries = parsed.get("entries")
    if not isinstance(entries, list):
        msg = "delete manifest missing entries array"
        raise ValueError(msg)
    out: list[dict[str, str]] = []
    for i, item in enumerate(entries):
        if not isinstance(item, dict):
            msg = f"manifest.entries[{i}] must be an object"
            raise ValueError(msg)
        row: dict[str, str] = {}
        for key in _REQUIRED_MANIFEST_KEYS:
            raw = item.get(key)
            if not isinstance(raw, str) or not raw.strip():
                msg = f"manifest.entries[{i}] missing or empty {key!r}"
                raise ValueError(msg)
            row[key] = raw.strip()
        out.append(row)
    return out


def run_branch_mismatch_delete(
    client: SnykRestClient,
    entries: list[DiffEntry],
    options: BranchMismatchDeleteOptions,
) -> dict[str, Any]:
    """Delete targets matched by display_name; optionally write reimport manifest."""
    if options.limit is not None:
        if options.limit < 1:
            msg = "limit must be >= 1 when set"
            raise ValueError(msg)
        entries = entries[: options.limit]

    name_to_org_id = build_name_to_org_id(client.iter_group_orgs())
    buckets = _empty_delete_buckets()
    manifest_entries: list[dict[str, str]] = []
    org_targets_cache: dict[str, list[dict[str, Any]]] = {}
    discovery_index: DiscoveryCoordinateIndex | None = None
    if options.discovery_path is not None:
        discovery_index = load_discovery_coordinate_index(options.discovery_path)

    def targets_for_org(org_id: str) -> list[dict[str, Any]]:
        if org_id not in org_targets_cache:
            org_targets_cache[org_id] = client.iter_org_targets(org_id)
        return org_targets_cache[org_id]

    for entry in entries:
        if entry.production_branch == entry.target_reference:
            buckets["skipped"].append(
                _entry_record(entry, reason="already_correct"),
            )
            continue

        org_id = name_to_org_id.get(entry.apm_code)
        if org_id is None:
            buckets["not_found"].append(
                _entry_record(entry, reason="org_not_found"),
            )
            continue

        try:
            candidates = targets_for_org(org_id)
            matches = _find_targets_by_display_name(candidates, entry)
        except RuntimeError as exc:
            buckets["failed"].append(
                _entry_record(entry, org_id=org_id, error=str(exc)),
            )
            continue

        if not matches:
            buckets["not_found"].append(
                _entry_record(
                    entry,
                    org_id=org_id,
                    reason="target_not_found",
                    **_target_not_found_diagnostics(candidates, entry),
                ),
            )
            continue
        if len(matches) > 1:
            buckets["ambiguous"].append(
                _entry_record(
                    entry,
                    org_id=org_id,
                    target_ids=[m.get("id") for m in matches],
                ),
            )
            continue

        target = matches[0]
        target_id = target.get("id")
        if not isinstance(target_id, str) or not target_id.strip():
            buckets["failed"].append(
                _entry_record(entry, org_id=org_id, error="target missing id"),
            )
            continue
        target_id = target_id.strip()

        if options.dry_run:
            buckets["skipped"].append(
                _entry_record(
                    entry,
                    org_id=org_id,
                    target_id=target_id,
                    reason="dry_run",
                ),
            )
            continue

        try:
            detail = client.get_org_target(org_id, target_id)
            integration_id = target_integration_id(detail)
            if integration_id is None:
                msg = "target missing integration id"
                raise ValueError(msg)
            coords = resolve_reimport_coordinates(detail, entry, discovery_index)
            manifest_entries.append(
                _manifest_entry(
                    entry,
                    org_id=org_id,
                    target_id=target_id,
                    integration_id=integration_id,
                    project_key=coords.project_key,
                    repo_slug=coords.repo_slug,
                    coordinate_source=coords.coordinate_source,
                ),
            )
            client.delete_org_target(org_id, target_id)
            buckets["deleted"].append(
                _entry_record(
                    entry,
                    org_id=org_id,
                    target_id=target_id,
                    coordinate_source=coords.coordinate_source,
                ),
            )
        except (RuntimeError, ValueError) as exc:
            buckets["failed"].append(
                _entry_record(entry, org_id=org_id, target_id=target_id, error=str(exc)),
            )

        if options.delay_ms > 0:
            time.sleep(options.delay_ms / 1000.0)

    if options.manifest_path is not None and manifest_entries:
        manifest_doc = {
            "version": MANIFEST_VERSION,
            "group_id": client.group_id,
            "entries": manifest_entries,
        }
        options.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        options.manifest_path.write_text(
            json.dumps(manifest_doc, indent=2),
            encoding="utf-8",
        )

    return {
        "version": DELETE_REPORT_VERSION,
        "group_id": client.group_id,
        "dry_run": options.dry_run,
        "entries_processed": len(entries),
        "manifest_path": str(options.manifest_path) if options.manifest_path else None,
        "manifest_entries": len(manifest_entries),
        **buckets,
    }
