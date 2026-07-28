## Why

Branch mismatch remediation falls back to Stage 1 discovery when target GET omits `projectKey`/`repoSlug`. The current discovery coordinate lookup matches diff `repository_name` (after stripping `BB/`) against discovery `repository_path`. That works when the Snyk display name embeds the full Bitbucket path (`BB/{project}/{slug}`), but Stage 3 import naming uses `BB/{slug}` only (`APP_TYPE_PREFIX` + discovery `repository_name`). Diff rows therefore look like `BB/juice-shop` while discovery stores `repository_path` `tcannell-test/juice-shop` and `repository_name` `juice-shop`. Lookup fails with `discovery_not_found` for the same repository.

Operators already disambiguate repos by org (`apm_code`) during delete matching. Discovery fallback should use the same identity: **repo slug + APM code**, ignoring any path or import prefix on the diff side.

## What Changes

- Change discovery coordinate index and lookup to match on **discovery `repository_name` (slug) + `apm_code`**, not `repository_path`.
- Extract repo slug from diff `repository_name` by stripping `APP_TYPE_PREFIX` when present, then taking the final path segment when `/` remains (so `BB/juice-shop` → `juice-shop`, and `tcannell-test/juice-shop` → `juice-shop`).
- Require matching `apm_code` on the diff entry (not only as a tie-breaker when multiple path matches exist).
- Continue returning `(project_key, repo_slug)` from discovery `repository_path` for reimport payloads.
- Delete matching unchanged: still exact `display_name == diff.repository_name`.
- Replace incorrect test fixtures that assumed `BB/{full-path}` with production-shaped `BB/{slug}` fixtures.

**Out of scope:** Changing Stage 3 import naming; changing diff generation; making prefix configurable.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `branch-mismatch-target-reimport`: Discovery coordinate lookup matches by repo slug and `apm_code`, disregarding import prefix and project/workspace prefix on diff `repository_name`.

## Impact

- **Code:** [`src/snyk/branch_mismatch_reimport.py`](../../../src/snyk/branch_mismatch_reimport.py) (`load_discovery_coordinate_index`, `discovery_lookup_name` → slug extractor, `_lookup_discovery_coordinates`)
- **Consumers:** [`src/snyk/branch_mismatch_delete.py`](../../../src/snyk/branch_mismatch_delete.py) (reuses same helpers)
- **Tests:** [`tests/test_branch_mismatch_coordinates.py`](../../../tests/test_branch_mismatch_coordinates.py) — fix juice-shop fixture; add `BB/juice-shop` + `tcannell-test/juice-shop` discovery case
- **Spec:** [`openspec/specs/branch-mismatch-target-reimport/spec.md`](../../../openspec/specs/branch-mismatch-target-reimport/spec.md)
- **Docs:** README branch remediation section
