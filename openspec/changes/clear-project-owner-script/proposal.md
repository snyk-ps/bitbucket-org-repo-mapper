## Why

Stage 4 (`snyk-post-import-cleanup`) sets recurring test frequency to `never` via the Snyk REST Projects API. That PATCH requires a `relationships.owner` user UUID (`SNYK_USER_ID`), which **assigns a project owner** on every project touched — including projects that were previously unassigned.

Operators need a one-off cleanup script to revert those unintended owner assignments across a Snyk group or an explicit set of orgs, without re-running the full Stage 4 pipeline. A follow-up change will update Stage 4 to preserve existing owners (or use a transition UUID to keep projects unassigned); this script addresses the existing side effect until that fix ships.

## What Changes

- Add **`scripts/clear_project_owners.py`**: operational CLI that clears project owner on every project in scope.
- Scope via **exactly one** of:
  - **`--group GROUP_ID`** — iterate all orgs in the group (REST `GET /rest/groups/{groupId}/orgs`)
  - **`--orgs ORG_ID[,ORG_ID...]`** — process the listed org UUIDs only
- Per org: list all projects (REST Projects API, reusing `SnykRestClient.iter_org_projects`), then **v1 PUT** `{"owner": null}` to `/v1/org/{orgId}/project/{projectId}` for each project.
- Add **`SnykRestClient.clear_project_owner(org_id, project_id)`** (v1 PUT wrapper).
- Add **`src/snyk/clear_project_owners.py`**: testable orchestration and versioned report JSON.
- Support **`--dry-run`**, **`--limit`**, **`--output`**, HTTP retry (existing client), and non-zero exit on any failure.

**Out of scope:**

- Changes to Stage 4 recurring-test PATCH logic (future change).
- Main CLI / `dispatch.py` registration.
- Selective cleanup by owner UUID (clears owner on **all** projects in scope; skip only when already unassigned if detectable).
- v1 project list migration (continue using REST list + v1 owner PUT).

## Capabilities

### New Capabilities

- `project-owner-cleanup`: One-off script and library to unassign project owners group-wide or org-scoped via v1 PUT.

### Modified Capabilities

- (none)

## Impact

- **Code**: [`src/integrations/snyk/client.py`](../../../src/integrations/snyk/client.py), new [`src/snyk/clear_project_owners.py`](../../../src/snyk/clear_project_owners.py), new [`scripts/clear_project_owners.py`](../../../scripts/clear_project_owners.py).
- **Tests**: new [`tests/test_clear_project_owners.py`](../../../tests/test_clear_project_owners.py), client test for v1 owner PUT.
- **Docs**: [`README.md`](../../../README.md) `scripts/` section; note relationship to Stage 4 `SNYK_USER_ID` side effect.
- **APIs**: Snyk REST Projects list; Snyk v1 `PUT /org/{orgId}/project/{projectId}` with `{"owner": null}`.
