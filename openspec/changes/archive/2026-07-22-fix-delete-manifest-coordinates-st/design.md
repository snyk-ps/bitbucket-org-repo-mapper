## Context

[`run_branch_mismatch_delete`](../../../src/snyk/branch_mismatch_delete.py) matches by `display_name`, then calls `get_org_target()` and `target_project_key_and_slug()`. On Scotia ST, target detail returns `integration_id` but not `projectKey` / `repoSlug`, producing:

```json
{ "error": "target missing projectKey/repoSlug", "manifest_entries": 0 }
```

Prior change [`2026-07-16-split-branch-mismatch-delete-reimport`](../../archive/2026-07-16-split-branch-mismatch-delete-reimport/) deferred discovery fallback (design §4 Alternative). Stage 3 already derives coordinates from discovery `repository_path` (`projectKey` / `repoSlug`).

## Goals / Non-Goals

**Goals:**

- Allow delete + manifest on single-tenant when Targets API omits coordinates.
- Reuse existing discovery.json (version 1 `rows` array) as authoritative Bitbucket path source.
- Preserve fail-closed behavior when coordinates cannot be resolved from any source.
- Surface provenance in report for operator audit.

**Non-Goals:**

- Inferring project key from `repository_name` (`BB/...` prefix).
- Making discovery mandatory for all tenants (multitenant may still populate target GET).
- Changing reimport batch shape.

## Decisions

### 1. Coordinate resolution order

**Choice:**

1. Target GET attributes: `projectKey`/`repoSlug` (or `project_key`/`repo_slug`) — existing.
2. Target GET partial: `project_key` + `remote_repo_url` tail — existing.
3. **Discovery fallback** (when `--discovery` supplied): match diff row to discovery row by `repository_name` (case-sensitive); if multiple rows, require matching `apm_code`; extract `(project_key, repo_slug)` from `repository_path`.
4. Fail with error listing attempted sources.

**Rationale:** Mirrors Stage 3 enrichment; discovery is already produced for Scotia onboarding.

**Alternative:** Projects API for coordinates — defer pending UAT field confirmation (Open Questions).

### 2. Discovery matching key

**Choice:** Primary key `repository_name`; disambiguate with `apm_code` when multiple discovery rows share the same name.

**Rationale:** Diff entries already carry both fields; matches operator mental model.

### 3. CLI surface

**Choice:** Optional `--discovery PATH` on delete script. When target GET lacks coords and flag omitted, fail with message: *"target missing projectKey/repoSlug; pass --discovery discovery.json"*.

**Rationale:** Multitenant unchanged; ST operators already have discovery.json from Stage 1.

### 4. Manifest provenance

**Choice:** Add optional manifest/report field `coordinate_source`: `"target"` | `"discovery"`.

**Rationale:** Supports UAT sign-off and debugging without changing snyk-api-import payload.

### 5. Integration id source

**Choice:** Unchanged — still from target GET `relationships.integration`. Customer failure had integration present; only repo coords missing.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Discovery row missing or stale `repository_name` | Fail with `discovery_not_found`; operator refreshes Stage 1 |
| Multiple discovery rows same name, different apm | Require `apm_code` match; else `ambiguous_discovery` |
| Discovery path wrong vs actual Bitbucket repo | Same risk as Stage 3; document need for current discovery |
| Repo renamed since import | Operator resolves manually; out of scope |

## Migration Plan

1. Implement discovery index + resolution chain.
2. UAT: re-run failed repo with `--discovery discovery.json`; confirm manifest + delete succeed.
3. Update README runbook; re-test `generate_branch_reimport_targets.py` → `snyk-api-import` on one repo.
4. Full batch after sign-off.

## Open Questions

- Do REST **Projects** resources on Scotia ST expose Bitbucket `projectKey` / repo slug (e.g. in `name` or `remoteUrl`)? If yes, add as fallback **before** discovery to avoid extra file dependency.
- Should [`generate_branch_reimport_targets.py`](../../../scripts/generate_branch_reimport_targets.py) accept `--discovery` to repair manifests from a partial delete report? (Defer unless needed.)
