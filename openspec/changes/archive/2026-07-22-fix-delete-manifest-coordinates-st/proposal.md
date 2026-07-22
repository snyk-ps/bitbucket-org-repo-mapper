## Why

Scotia single-tenant UAT delete runs fail after target match with `"target missing projectKey/repoSlug"` (e.g. `BB/uat-bitbucket-java-sample`). The delete script captures reimport coordinates from `GET /rest/orgs/{org_id}/targets/{target_id}`, but on single-tenant the Targets API often omits `projectKey` / `repoSlug` — the same class of API shape gap fixed for branch via the Projects API in [`2026-07-16-split-branch-mismatch-delete-reimport`](../../archive/2026-07-16-split-branch-mismatch-delete-reimport/).

The script correctly **fail-closes** (no DELETE, empty manifest), but operators cannot complete delete → reimport without manual manifest construction.

## What Changes

- **Coordinate resolution chain:** After target GET, fall back to Bitbucket discovery data when target attributes lack `projectKey` / `repoSlug`.
- **Discovery index:** Build `repository_name` (+ optional `apm_code` disambiguation) → `(project_key, repo_slug)` from Stage 1 `discovery.json` rows (`repository_path`).
- **Delete CLI:** Add optional `--discovery PATH` to [`scripts/delete_mismatched_targets.py`](../../../scripts/delete_mismatched_targets.py).
- **Report enrichment:** Record `coordinate_source` (`target` | `discovery`) on manifest entries; improve error message when all sources exhausted.
- **Shared helper:** Add `resolve_reimport_coordinates()` used by delete (reusing [`target_project_key_and_slug`](../../../src/snyk/branch_mismatch_reimport.py)).

**Out of scope:**

- Parsing `BB/` display name as Bitbucket project key (unsafe — `BB` is app-type prefix).
- Stage 1–4 pipeline changes.
- Projects API coordinate spike unless UAT confirms fields exist (see design Open Questions).

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `branch-mismatch-target-reimport`: manifest coordinate provenance with discovery fallback; delete CLI `--discovery` flag; coordinate resolution requirements.

## Impact

- **Code:** [`src/snyk/branch_mismatch_delete.py`](../../../src/snyk/branch_mismatch_delete.py), [`src/snyk/branch_mismatch_reimport.py`](../../../src/snyk/branch_mismatch_reimport.py), [`scripts/delete_mismatched_targets.py`](../../../scripts/delete_mismatched_targets.py), reuse of [`src/common/output_state.py`](../../../src/common/output_state.py) `row_repo_key`.
- **Tests:** delete with target coords missing + discovery fallback; no discovery → fail-closed; ambiguous discovery match.
- **Docs:** README delete section — `--discovery` on single-tenant when target GET lacks coordinates.
- **APIs:** Snyk Targets GET (primary); discovery.json (fallback).
