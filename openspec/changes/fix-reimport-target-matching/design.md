## Context

Branch remediation consumes `diff.json` rows produced by comparing Snyk project branch (Projects API) against desired `production_branch` (discovery). Each row contains:

| Field | Role |
|-------|------|
| `apm_code` | Resolve Snyk org by name |
| `repository_name` | Snyk target `display_name` (from Targets API / lookup output) |
| `production_branch` | Desired branch after reimport |
| `target_reference` | Current branch (from Projects API) — mismatch signal only |

Per the [Snyk Targets API](https://docs.snyk.io/developer-tools/snyk-api/reference/targets), target list/get/delete operate on target identity (`display_name`, integration relationship, etc.). Branch is **not** exposed on Target resources for client-side matching — it lives on **Projects** (`attributes.target_reference`), joined to targets by target id.

The monolithic flow in [`branch_mismatch_reimport.py`](../../../src/snyk/branch_mismatch_reimport.py) still matches on `display_name` **and** `target_reference` read from target attributes (`_find_matching_targets`). That matcher was never valid on any tenant. The split delete script ([`branch_mismatch_delete.py`](../../../src/snyk/branch_mismatch_delete.py)) already matches by display name only, but the monolithic reimport path, tests, and docs still carry incorrect assumptions — including "single-tenant omits target_reference" framing from archived [`fix-branch-reconciliation-uat`](../../archive/2026-07-16-fix-branch-reconciliation-uat/).

Example naming mismatch between artifacts:
- `diff.json`: `"repository_name": "tcannell-test/juice-shop"` (Snyk display name)
- `discovery.json`: `"repository_name": "juice-shop"`, `"repository_path": "tcannell-test/juice-shop"`

Delete matching MUST use diff `repository_name`. Discovery is for Bitbucket import coordinates only, keyed by `repository_path`.

## Goals / Non-Goals

**Goals:**

- Monolithic reimport reliably finds and deletes targets on all tenant types when Targets API omits branch (always).
- Developer can test against Bitbucket Cloud via `--integration-type bitbucket-cloud`; production defaults to `bitbucket-server`.
- Discovery fallback resolves coordinates when diff `repository_name` equals discovery `repository_path`.
- Retract incorrect single-tenant-only rationale from code, tests, README, and specs.

**Non-Goals:**

- Branch-level delete (delete whole target; reimport replaces it).
- Auto-detect integration type per org.
- Stage 1–4 pipeline changes.
- Generating `diff.json` from security.yaml.

## Decisions

### 1. Delete match: display_name only, whole target

**Choice:** Reuse the delete script strategy: match `attributes.display_name == entry.repository_name`. Ignore Targets API branch entirely. Delete the entire matched target.

**Rationale:** Targets API does not expose branch for matching on any tenant. Reimport replaces the target anyway.

**Alternative:** Match `display_name + target_reference` from Targets API — rejected; field not available per API contract. Archived UAT fix decision to keep dual-field match — superseded.

### 2. `target_reference` in diff: Projects API only, skip signal only

**Choice:** Keep `already_correct` skip when `production_branch == target_reference` in diff. Diff `target_reference` continues to come from Projects API (`lookup_target_reference.py`). Never read branch from Targets API for matching or diff provenance.

**Rationale:** Projects API is the authoritative branch source. Diff row presence implies a known mismatch; skip logic avoids no-op work without API calls.

### 3. `--integration-type` CLI flag

**Choice:** Add to `reimport_mismatched_targets.py` and plumb through `BranchMismatchReimportOptions`:

```
--integration-type {bitbucket-server,bitbucket-cloud}
  default: bitbucket-server
```

Generalize `pick_bitbucket_server_integration_id` → `pick_integration_id(integrations, integration_type)` in [`client.py`](../../../src/integrations/snyk/client.py). When matching targets, restrict candidates to those whose `relationships.integration.data.id` equals the org's integration of the requested type (when integration id is present on list payload).

**Rationale:** Operator tests with Bitbucket Cloud; Scotia prod uses Bitbucket Server. Prevents cross-SCM false matches in orgs with multiple integrations.

### 4. Discovery index keyed by `repository_path`

**Choice:** Change `load_discovery_coordinate_index` to index rows by `repository_path` (normalized strip), not discovery `repository_name`. Lookup with `entry.repository_name` from diff.

**Rationale:** Diff `repository_name` is the Snyk display name (often equals `repository_path`), not the Bitbucket slug in discovery `repository_name`.

### 5. Monolithic script gains `--discovery`

**Choice:** Add `--discovery PATH` to `reimport_mismatched_targets.py`, same semantics as delete script: fallback for `projectKey`/`repoSlug` when target GET omits them.

**Rationale:** Parity with split workflow; required when target GET lacks coordinates.

### 6. Shared matcher helper

**Choice:** Extract or import `_find_targets_by_display_name` from [`branch_mismatch_delete.py`](../../../src/snyk/branch_mismatch_delete.py) into shared use by reimport. Remove `_find_matching_targets` branch filter and branch-centric diagnostics (`same_display_name_branches`).

**Rationale:** Single source of truth; tests reflect API reality.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Multiple targets share same `display_name` | Record `ambiguous`; no delete (same as delete script) |
| Integration id missing on target list item | Match without integration filter when relationship absent; prefer target GET integration id before delete |
| Bitbucket Cloud import payload differs from Server | Capture integration from deleted target; validate with `--dry-run` on cloud test org |
| Discovery path format differs from diff display name | Document requirement; diagnostic on lookup miss suggests checking `repository_path` alignment |
| Docs/tests still assume target branch | Dedicated cleanup task; update fixtures to omit `target_reference` on target mocks |

## Migration Plan

1. Fix matcher + tests (display_name only).
2. Fix discovery index to use `repository_path`.
3. Add `--integration-type` and `--discovery` to monolithic CLI.
4. Retract single-tenant misinformation from README and docstrings.
5. Dry-run with `data/diff.json` against cloud test org (`--integration-type bitbucket-cloud --dry-run --limit 5`).
6. Prod: default `bitbucket-server` + `--discovery discovery.json`.

## Open Questions

- Should `--integration-type` also be added to `delete_mismatched_targets.py` for parity?
- Does Bitbucket Cloud reimport need a different `build_import_payload` shape (owner/repo vs projectKey/repoSlug)?
