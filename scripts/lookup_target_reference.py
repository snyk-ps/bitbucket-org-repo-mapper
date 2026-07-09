"""Build diff.json input for branch mismatch reimport from Snyk REST APIs.

Each output entry uses target.attributes.target_reference (not project-level
target_reference) so values match reimport_mismatched_targets lookup keys.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from urllib.parse import urljoin

GROUP_ID = os.environ["SNYK_GROUP_ID"]
TOKEN = os.environ.get("SNYK_TOKEN") or os.environ.get("SNYK_API_KEY", "")
if not TOKEN.strip():
    print("SNYK_TOKEN (or SNYK_API_KEY) is required", file=sys.stderr)
    sys.exit(2)

BASE_URL = os.environ.get("SNYK_API", "https://api.snyk.io").rstrip("/")
API_VERSION = os.environ.get("SNYK_API_VERSION", "2024-10-15").strip()

HEADERS = {
    "Authorization": f"token {TOKEN.strip()}",
    "Accept": "application/vnd.api+json",
}


def _target_reference(attrs: dict[str, object]) -> str | None:
    for key in ("target_reference", "targetReference", "branch"):
        raw = attrs.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return None


def get_json(url: str) -> dict[str, object]:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as response:
        parsed = json.loads(response.read().decode("utf-8"))
    if not isinstance(parsed, dict):
        msg = f"Unexpected JSON from {url}"
        raise TypeError(msg)
    return parsed


results: list[dict[str, str]] = []

orgs_url = (
    f"{BASE_URL}/rest/groups/{GROUP_ID}/orgs"
    f"?version={API_VERSION}&limit=100"
)

while orgs_url:
    print(f"Fetching organizations: {orgs_url}")
    orgs_response = get_json(orgs_url)
    data = orgs_response.get("data")
    if not isinstance(data, list):
        break

    for org in data:
        if not isinstance(org, dict):
            continue
        org_id = org.get("id")
        attrs = org.get("attributes")
        if not isinstance(org_id, str) or not isinstance(attrs, dict):
            continue
        org_name = attrs.get("name")
        if not isinstance(org_name, str):
            continue

        print(f"Processing org: {org_name}")

        bitbucket_target_ids: set[str] = set()

        projects_url = (
            f"{BASE_URL}/rest/orgs/{org_id}/projects"
            f"?version={API_VERSION}&limit=100"
        )

        while projects_url:
            projects_response = get_json(projects_url)
            projects = projects_response.get("data")
            if not isinstance(projects, list):
                break

            for project in projects:
                if not isinstance(project, dict):
                    continue
                try:
                    project_attrs = project.get("attributes")
                    if not isinstance(project_attrs, dict):
                        continue
                    if project_attrs.get("origin") != "bitbucket-server":
                        continue
                    rel = project.get("relationships")
                    if not isinstance(rel, dict):
                        continue
                    target_rel = rel.get("target")
                    if not isinstance(target_rel, dict):
                        continue
                    target_data = target_rel.get("data")
                    if not isinstance(target_data, dict):
                        continue
                    target_id = target_data.get("id")
                    if isinstance(target_id, str) and target_id.strip():
                        bitbucket_target_ids.add(target_id.strip())
                except (KeyError, TypeError):
                    continue

            next_projects = projects_response.get("links")
            next_link = None
            if isinstance(next_projects, dict):
                raw = next_projects.get("next")
                if isinstance(raw, str):
                    next_link = raw
            projects_url = urljoin(BASE_URL, next_link) if next_link else None

        print(f"  Found {len(bitbucket_target_ids)} Bitbucket Server targets")

        targets_url = (
            f"{BASE_URL}/rest/orgs/{org_id}/targets"
            f"?version={API_VERSION}&limit=100&exclude_empty=false"
        )

        while targets_url:
            targets_response = get_json(targets_url)
            targets = targets_response.get("data")
            if not isinstance(targets, list):
                break

            for target in targets:
                if not isinstance(target, dict):
                    continue
                target_id = target.get("id")
                if not isinstance(target_id, str) or target_id not in bitbucket_target_ids:
                    continue
                target_attrs = target.get("attributes")
                if not isinstance(target_attrs, dict):
                    continue
                display_name = target_attrs.get("display_name")
                branch = _target_reference(target_attrs)
                if not isinstance(display_name, str) or branch is None:
                    continue
                results.append(
                    {
                        "apm_code": org_name,
                        "repository_name": display_name,
                        "target_reference": branch,
                    }
                )

            next_targets = targets_response.get("links")
            next_link = None
            if isinstance(next_targets, dict):
                raw = next_targets.get("next")
                if isinstance(raw, str):
                    next_link = raw
            targets_url = urljoin(BASE_URL, next_link) if next_link else None

        print(f"  Completed {org_name}")

    next_orgs = orgs_response.get("links")
    next_link = None
    if isinstance(next_orgs, dict):
        raw = next_orgs.get("next")
        if isinstance(raw, str):
            next_link = raw
    orgs_url = urljoin(BASE_URL, next_link) if next_link else None

with open("output.json", "w", encoding="utf-8") as fp:
    json.dump(results, fp, indent=2)

print(f"Created output.json with {len(results)} entries")
