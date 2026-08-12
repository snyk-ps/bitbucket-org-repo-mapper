"""Clear project owner on all projects in a Snyk group or org list."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from integrations.snyk.client import SnykRestClient

CLEAR_PROJECT_OWNER_REPORT_VERSION = 1


@dataclass(frozen=True)
class ClearProjectOwnerOptions:
    """Runtime options for project owner cleanup."""

    group_id: str | None = None
    org_ids: list[str] | None = None
    dry_run: bool = False
    limit: int | None = None


def parse_org_ids(raw: str) -> list[str]:
    """Parse comma-separated org UUIDs from ``--orgs``."""
    parts = [part.strip() for part in raw.split(",")]
    org_ids = [part for part in parts if part]
    if not org_ids:
        msg = "--orgs must contain at least one org UUID"
        raise ValueError(msg)
    return org_ids


def resolve_orgs(
    client: SnykRestClient,
    *,
    group_id: str | None,
    org_ids: list[str] | None,
) -> list[dict[str, str]]:
    """Resolve org id/name pairs from group scope or explicit org list."""
    if org_ids is not None:
        return [{"id": org_id, "name": org_id} for org_id in org_ids]
    if group_id is None or not group_id.strip():
        msg = "group_id is required for group scope"
        raise ValueError(msg)
    return client.iter_group_orgs(group_id=group_id.strip())


def _project_field(project: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        raw = project.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return None


def run_clear_project_owners(
    client: SnykRestClient,
    options: ClearProjectOwnerOptions,
) -> dict[str, Any]:
    """Clear project owner on every project in scope."""
    orgs = resolve_orgs(
        client,
        group_id=options.group_id,
        org_ids=options.org_ids,
    )

    cleared: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []

    processed = 0
    limit = options.limit

    for org in orgs:
        org_id = org["id"]
        org_name = org["name"]

        for project in client.iter_org_projects(org_id):
            if limit is not None and processed >= limit:
                break

            project_id = _project_field(project, "id")
            project_name = _project_field(project, "name", "projectName")
            project_type = _project_field(project, "type")
            owner_id = _project_field(project, "owner_id")
            if not project_id:
                continue

            processed += 1
            base_entry = {
                "org_id": org_id,
                "org_name": org_name,
                "project_id": project_id,
                "project_name": project_name,
                "project_type": project_type,
            }

            if options.dry_run:
                skipped.append({**base_entry, "reason": "dry_run"})
                continue

            if owner_id is None:
                skipped.append({**base_entry, "reason": "already_unassigned"})
                continue

            try:
                client.clear_project_owner(org_id, project_id)
                cleared.append(base_entry)
            except RuntimeError as exc:
                failed.append({**base_entry, "error": str(exc)})

        if limit is not None and processed >= limit:
            break

    report: dict[str, Any] = {
        "version": CLEAR_PROJECT_OWNER_REPORT_VERSION,
        "cleared": cleared,
        "skipped": skipped,
        "failed": failed,
    }
    if options.org_ids is not None:
        report["org_ids"] = options.org_ids
    else:
        report["group_id"] = options.group_id
    return report
