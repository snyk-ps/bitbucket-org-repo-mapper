## Context

Branch remediation for Scotia processes a pre-built `diff.json` (896+ entries) where each row has `apm_code`, `repository_name`, `production_branch`, and `target_reference`. The current monolithic flow in [`branch_mismatch_reimport.py`](../../../src/snyk/branch_mismatch_reimport.py) lists targets via `iter_org_targets()` and matches on `display_name` **and** `target_reference` read from target attributes.

On Scotia single-tenant UAT, Targets API responses omit `attributes.target_reference` (always `None`). Projects API responses include `attributes.target_reference` on Bitbucket Server projects. The archived change [`2026-07-16-fix-branch-reconciliation-uat`](../../archive/2026-07-16-fix-branch-reconciliation-uat/) incorrectly moved diff provenance to the target resource and tightened delete matching — both fail on this tenant.

Rami's operator proposal:

1. Delete targets from `diff.json` with a simple deletion script (no branch match on Targets API).
2. Reimport by generating a targets batch file and running `snyk-api-import`.

Delete match strategy confirmed: **`apm_code` + `repository_name` (`display_name`) only**.

## Goals / Non-Goals

**Goals:**

- Reliable diff generation using Projects API branch on single-tenant.
- Split delete and reimport into independent, debuggable scripts.
- Delete manifest capturing `integration_id`, `project_key`, `repo_slug` from target GET before DELETE so reimport does not depend on the deleted target.
- Preserve `target_reference` in diff for comparison purposes ([`branch_diff.py`](../../../scripts/branch_diff.py)) but not for delete matching.

**Non-Goals:**

- Changing Stage 3 import enrichment or Stage 4 cleanup.
- Matching delete by Targets API branch (broken on ST).
- Automatic security.yaml diff generation.

## Decisions

### 1. Branch source for diff / output.json

**Choice:** `GET /rest/orgs/{org_id}/projects` → `attributes.target_reference`, keyed by `relationships.target.data.id`. Join with Targets API for `display_name`.

**Rationale:** Rami confirmed Projects API returns branch on Scotia ST; Targets API does not.

**Alternative:** Target resource branch — rejected; returns `None` on ST.

### 2. Delete target identification

**Choice:** Match exactly one target where `attributes.display_name == repository_name` within the org resolved from `apm_code`. Do not filter by `target_reference`.

**Rationale:** User confirmed; avoids dependency on absent target branch field.

**Alternative:** Match `display_name + target_reference` — rejected; branch unavailable on target resource.

### 3. Ambiguous delete handling

**Choice:** If more than one target shares `display_name`, record under `ambiguous` and skip DELETE.

**Rationale:** Prevents deleting wrong branch when multi-target repos exist.

### 4. Delete manifest for reimport enrichment

**Choice:** Delete script writes `delete-manifest.json` with per-row: `org_id`, `target_id`, `integration_id`, `project_key`, `repo_slug`, `repository_name`, `production_branch`, captured from target GET immediately before DELETE.

**Rationale:** After DELETE, target detail is gone; manifest is the durable source for `snyk-api-import` payload fields.

**Alternative:** Re-derive from discovery + Stage 3 enrichment — viable fallback but requires discovery.json and extra API calls; manifest is simpler for operators.

### 5. Script split

**Choice:**

| Script | Role |
|--------|------|
| [`scripts/delete_mismatched_targets.py`](../../../scripts/delete_mismatched_targets.py) | Delete only + manifest |
| [`scripts/generate_branch_reimport_targets.py`](../../../scripts/generate_branch_reimport_targets.py) | Build batch JSON from manifest |
| Operator runs `snyk-api-import import --file=...` | Reimport (unchanged external tool) |

**Rationale:** Matches Rami; isolates failures.

**Alternative:** Keep monolithic [`reimport_mismatched_targets.py`](../../../scripts/reimport_mismatched_targets.py) — deprecate; optionally reimplement as wrapper invoking both steps.

### 6. Reimport batch shape

**Choice:** Reuse [`build_import_payload`](../../../src/snyk/branch_mismatch_reimport.py): `orgId`, `integrationId`, `target.{projectKey, repoSlug, name, branch}` where `branch = production_branch`.

**Rationale:** Same validated UAT workflow as Stage 3 / original branch reimport.

### 7. Supersedes prior UAT spec assumptions

**Choice:** This change reverses [`branch-mismatch-target-reimport`](../../../openspec/specs/branch-mismatch-target-reimport/spec.md) requirements that target resource branch is authoritative for diff and delete matching.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Multiple targets same `display_name` | `ambiguous` bucket; operator resolves manually |
| Manifest lost between delete and import | Document runbook; optional `--manifest` path flag; wrapper script |
| Projects API branch differs from discovery `production_branch` | Expected — that is why row is in diff |
| Multitenant still has target branch populated | Delete-by-display-name works regardless; diff uses projects index consistently |

## Migration Plan

1. Fix [`lookup_target_reference.py`](../../../scripts/lookup_target_reference.py) to projects-only branch (Track 1).
2. UAT: regenerate `output.json` / `diff.json`; dry-run delete script on `--limit 5`.
3. Live delete on 1–2 repos; generate targets batch; run `snyk-api-import`.
4. Full batch after sign-off; deprecate monolithic script in README.

## Open Questions

- Remove [`run_branch_mismatch_reimport`](../../../src/snyk/branch_mismatch_reimport.py) in this change vs follow-up deprecation PR.
- Whether manifest should be mandatory or optional when discovery.json is supplied to import generator.
