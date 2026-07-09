## Context

Scotia UAT (single-tenant) reported two failures during post-onboarding remediation:

1. **Branch mismatch reimport** (`scripts/reimport_mismatched_targets.py`) — entries like `BB/uat-bitbucket-java-sample` with `target_reference: master` and `production_branch: snyk-pr-scan-test` land in `not_found` with `reason: target_not_found` instead of being deleted and reimported. The difference between `production_branch` and `target_reference` is intentional (that is the mismatch being fixed).

2. **Stage 4 post-import cleanup** (`snyk-post-import-cleanup`) — dry-run succeeds but live runs fail with HTTP 400 on `update_project_settings`.

The original [`branch-mismatch-target-reimport`](../../archive/2026-06-25-branch-mismatch-target-reimport/) change shipped v1 without UAT hardening. Several fixes exist in the working tree but are not yet captured in OpenSpec or fully verified on Scotia single-tenant.

[`scripts/lookup_target_reference.py`](../../../scripts/lookup_target_reference.py) (diff producer) reads `target_reference` from **project** attributes while reimport matches **target** `attributes.target_reference` — a proven source of false `target_not_found` when project and target disagree.

Stage 4 migrated project listing and settings to REST, but archived specs still describe v1 `PUT` settings. REST PATCH requires `relationships.owner` with a user id — dry-run never exercises PATCH, so missing `user_id` only surfaces on live runs.

## Goals / Non-Goals

**Goals:**

- Reliably resolve Snyk targets for branch reconciliation on single-tenant UAT (including empty targets).
- Align diff `target_reference` with the reimport matcher field source.
- Make `target_not_found` actionable via diagnostics, not silent drops.
- Fix Stage 4 live PATCH (required owner `user_id`, valid JSON:API body).
- Sync OpenSpec requirements to REST project APIs.

**Non-Goals:**

- Generating `diff.json` from security.yaml.
- Merging branch reimport into Stage 4 CLI.
- Broker or discovery changes.
- Relaxing match semantics to `display_name` only (ambiguous when multiple branches exist).

## Decisions

### 1. Target listing: `exclude_empty=false`, full org list, client-side match

**Choice:** `GET /rest/orgs/{org_id}/targets?version=...&exclude_empty=false`; cache full list per `org_id`; match client-side on `display_name` + `target_reference`. Do not pass `display_name` as a server-side filter during reconciliation.

**Rationale:** Snyk omits empty targets by default; Scotia may need to delete/reimport targets with no projects. Server-side `display_name` filter plus per-org cache caused incomplete lists when multiple repos share an org.

**Alternative:** Server-side `display_name` filter — rejected; caused cache/list gaps for multi-repo orgs.

### 2. Match key unchanged: `display_name` + `target_reference` (case-sensitive)

**Choice:** Keep dual-field match from v1 spec.

**Rationale:** Disambiguates multiple branch targets for the same repo. `production_branch` is only used for reimport, not lookup.

### 3. Diff `target_reference` from target resource

**Choice:** [`lookup_target_reference.py`](../../../scripts/lookup_target_reference.py) SHALL set `target_reference` from `target.attributes.target_reference` (with same attribute aliases as reimport). Projects API may still be used to discover which target ids are Bitbucket Server, but branch value comes from the target.

**Rationale:** Matcher reads target attributes; project-level `target_reference` can differ on single-tenant.

**Alternative:** Fallback match by `display_name` only when branch mismatches — rejected; risks deleting wrong branch when multiple exist.

### 4. Actionable `target_not_found` diagnostics

**Choice:** `not_found` entries with `reason: target_not_found` include `candidates_returned`, and when applicable `same_display_name_branches` and `near_match_display_names`.

**Rationale:** Operators can distinguish stale diff (branch changed since diff generation) from wrong `repository_name`.

### 5. Stage 4 PATCH: REST with required `relationships.owner`

**Choice:** `PATCH /rest/orgs/{orgId}/projects/{projectId}` with `attributes.settings.recurring_tests.frequency: never` and `relationships.owner.data` set to configured `user_id`. CLI requires `SNYK_USER_ID` or `--user-id` before live runs.

**Rationale:** REST API rejects PATCH without owner; explains dry-run vs live divergence.

**Alternative:** v1 PUT settings — superseded by REST migration already in code.

### 6. PATCH HTTP 404 handling

**Choice:** When PATCH returns HTTP 404 (project deleted in dockerfile pass or race), record under `recurring_test_frequency.skipped` with `reason: project_not_found` and continue.

**Rationale:** Avoid failing the whole org when a project no longer exists after dockerfile deletion.

### 7. Single-tenant configuration

**Choice:** Document `SNYK_API` as tenant origin (e.g. `https://api.example.my.snyk.io`); use `Authorization: token {SNYK_TOKEN}` consistently in scripts and client.

**Rationale:** Scotia issues reported only on single-tenant UAT, not multitenant test env.

### 8. Relationship to `fix-dockerfile-project-type-filter`

**Choice:** REST `iter_org_projects` with client-side `dockerfile` type filter supersedes the v1 `types=` query-parameter fix in [`fix-dockerfile-project-type-filter`](../../fix-dockerfile-project-type-filter/). Close or archive that change when this change lands.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Large org target lists (896+ repos) | Per-org cache; paginate via `links.next` |
| Stale `diff.json` after branch changes | `same_display_name_branches` diagnostic prompts re-generation |
| Wrong `user_id` for PATCH owner | CLI validation; document how to obtain user UUID |
| PATCH 404 masked as skip | Record `reason: project_not_found` in report for audit |
| Project vs target field drift on other attributes | Reimport reads integration/projectKey from target detail GET before delete |

## Migration Plan

1. Land code + spec changes; run unit tests.
2. Scotia UAT: regenerate `diff.json` with fixed lookup script.
3. Dry-run reimport on `--limit 5` including `BB/uat-bitbucket-java-sample`.
4. Live reimport on 1–2 repos; verify `target_reference` matches `production_branch` after import.
5. Stage 4 dry-run then live on one org with valid `SNYK_USER_ID`.
6. Full batch remediation after sign-off.

## Open Questions

- None blocking implementation. Confirm Scotia `SNYK_USER_ID` value for Stage 4 live run during UAT re-test.
