## Context

Stage 4 ([`post_import_cleanup.py`](../../../src/snyk/post_import_cleanup.py)) calls `SnykRestClient.update_project_settings`, which PATCHes via REST and **always** sets `relationships.owner` to `SNYK_USER_ID`. The Snyk API requires a user UUID when modifying project settings via REST PATCH, but that inadvertently assigns an owner on projects that were previously unassigned.

Clearing ownership uses a **different** API surface: v1 **PUT** on the project resource with `{"owner": null}` to `/v1/org/{orgId}/project/{projectId}` — not the REST PATCH or `/settings` path.

Existing one-off scripts ([`scripts/reimport_mismatched_targets.py`](../../../scripts/reimport_mismatched_targets.py)) follow the pattern: thin `scripts/` entrypoint + `src/snyk/` library + `SnykRestClient` extension.

## Goals / Non-Goals

**Goals:**

- Clear project owner on every project in a group or explicit org list.
- Mutually exclusive `--group` vs `--orgs` scope flags.
- `--dry-run`, versioned report, partial-failure continue, non-zero exit if any `failed`.
- Reuse `SNYK_TOKEN`, `SNYK_API`, HTTP retry, and `iter_org_projects`.

**Non-Goals:**

- Fixing Stage 4 owner preservation (documented as follow-up).
- Dispatcher / console script registration.
- Filtering by a specific owner UUID (e.g. only `SNYK_USER_ID`).

## Decisions

### 1. Script location: `scripts/` + `src/snyk/`

**Choice:** `scripts/clear_project_owners.py` CLI; logic in `src/snyk/clear_project_owners.py`.

**Rationale:** Matches [`reimport_mismatched_targets.py`](../../../scripts/reimport_mismatched_targets.py) and keeps orchestration testable.

### 2. Scope selection: `--group` XOR `--orgs`

**Choice:** Require exactly one scope mode:

| Flag | Value | Org resolution |
|------|-------|----------------|
| `--group GROUP_ID` | Single group UUID | `SnykRestClient.iter_group_orgs()` (group id from flag or env) |
| `--orgs ORG_IDS` | Comma-separated org UUIDs | Use list as-is; validate non-empty after split |

**Rationale:** Matches operator request; `--orgs` supports targeted cleanup without group membership listing.

**Credentials:**

- `SNYK_TOKEN` always required.
- `SNYK_GROUP_ID` **not** required when `--orgs` is used.
- For `--group`: accept `--group` flag; fall back to `SNYK_GROUP_ID` env when flag omitted.

**Implementation note:** `load_snyk_settings()` currently requires `SNYK_GROUP_ID`. For `--orgs`-only runs, construct `SnykSettings` with a placeholder `group_id` (unused) or add optional group_id to settings loading — minimal change preferred.

### 3. List projects via REST; clear owner via v1 PUT

**Choice:**

- **List:** `GET /rest/orgs/{orgId}/projects` (existing `iter_org_projects`).
- **Clear:** `PUT {v1_root}/org/{orgId}/project/{projectId}` with body `{"owner": null}`.

**Rationale:** User-validated endpoint for unassigning owner; REST list already paginated and tested.

**Alternative:** v1 project list — rejected; REST list is already the Stage 4 standard.

### 4. Skip projects already unassigned (best-effort)

**Choice:** If project list payload exposes owner (REST `relationships.owner.data.id` or v1 GET when needed), skip PUT and record under `skipped` with `reason: already_unassigned`. If owner is not present in list response, issue PUT anyway (idempotent).

**Rationale:** Reduces API calls; safe if PUT is idempotent for null owner.

### 5. Partial failure semantics

**Choice:** Continue per project on error; exit `1` if report `failed` is non-empty (Stage 4 / reimport pattern).

### 6. Future Stage 4 fix (document only)

**Planned follow-up (not this change):**

When Stage 4 PATCHes recurring test frequency:

1. Read existing project owner UUID from project detail if present.
2. If owner exists → pass that UUID in REST PATCH `relationships.owner`.
3. If no owner → pass a **dummy transition UUID** known to the org; after settings change, v1 PUT `{"owner": null}` (same endpoint as this script) to restore unassigned state.

This preserves assigned owners and avoids permanently assigning `SNYK_USER_ID` to previously unassigned projects.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| v1 PUT clears owner but REST PATCH re-assigns on next Stage 4 run | Document run order; Stage 4 fix is follow-up |
| Large groups — many PUTs | HTTP retry; optional `--limit` for UAT |
| Token lacks project edit permission | Fail fast with HTTP error in report |
| `--orgs` org not in token scope | Per-org/per-project errors under `failed` |

## Migration Plan

1. Run `--dry-run --group <id>` (or `--orgs`) on UAT; confirm project counts.
2. Live run on one org with `--limit`.
3. Full group/org cleanup after Stage 4 has been run live.
4. Re-run Stage 4 only after owner-preservation fix is deployed (otherwise owners will be re-assigned).

## Open Questions

- Confirm dummy transition UUID for future Stage 4 work (org-specific service account vs fixed sentinel).
- Confirm v1 PUT succeeds on projects with no prior owner (expect 200/no-op or skip).
