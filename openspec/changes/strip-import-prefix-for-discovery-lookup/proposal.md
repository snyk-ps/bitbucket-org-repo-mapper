## Why

Branch mismatch remediation falls back to Stage 1 discovery when target GET omits `projectKey`/`repoSlug`. Discovery coordinate lookup matches diff `repository_name` to discovery `repository_path` exactly. Tenants that apply the Stage 3 import naming convention (`BB/{path}`) emit diff rows whose `repository_name` includes the `BB/` prefix (Snyk target `display_name`), while discovery `repository_path` remains the unprefixed Bitbucket path (`{workspace}/{slug}`). Lookup then fails with `discovery_not_found` even for the same repository. Delete matching is unaffected — both diff and Snyk `display_name` carry the prefix.

## What Changes

- Normalize diff `repository_name` for discovery lookup by stripping the existing `APP_TYPE_PREFIX` (`BB/`) when present, before matching against discovery `repository_path`.
- Reuse `APP_TYPE_PREFIX` from `snyk/outputs.py` — no new CLI flag.
- Delete matching, diff validation, and report `repository_name` fields remain unchanged (full prefixed name preserved).
- Tests for prefixed diff name + unprefixed discovery path (production case).

**Out of scope:** CLI-configurable prefix; changing Stage 1 discovery output; changing how diff.json is generated.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `branch-mismatch-target-reimport`: Discovery coordinate lookup strips `APP_TYPE_PREFIX` from diff `repository_name` before matching discovery `repository_path`.

## Impact

- **Code:** [`src/snyk/branch_mismatch_reimport.py`](../../../src/snyk/branch_mismatch_reimport.py) (`_lookup_discovery_coordinates` or shared normalizer)
- **Tests:** [`tests/test_branch_mismatch_coordinates.py`](../../../tests/test_branch_mismatch_coordinates.py)
- **Docs:** README branch remediation section (prefixed Snyk display names vs unprefixed discovery paths)
