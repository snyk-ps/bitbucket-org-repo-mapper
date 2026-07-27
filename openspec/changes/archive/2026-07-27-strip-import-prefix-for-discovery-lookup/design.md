## Context

Stage 3 applies `APP_TYPE_PREFIX = "BB/"` to import `target.name` in [`build_snyk_import_document`](../../../src/snyk/outputs.py). End users who import with that custom name get Snyk targets whose `display_name` is prefixed (e.g. `BB/tcannell-test/juice-shop`). [`lookup_target_reference.py`](../../../scripts/lookup_target_reference.py) emits that prefixed value as diff `repository_name`.

Stage 1 discovery stores the natural Bitbucket path without prefix:

| Field | Example |
|-------|---------|
| `repository_path` | `tcannell-test/juice-shop` |
| `repository_name` | `juice-shop` (slug only) |

Discovery coordinate index is keyed by `repository_path`. Current lookup in [`branch_mismatch_reimport.py`](../../../src/snyk/branch_mismatch_reimport.py) uses diff `repository_name` verbatim:

```python
candidates = index.get(entry.repository_name, [])
```

When diff is prefixed and discovery is not, lookup misses with `discovery_not_found`. Delete matching is unaffected — both diff and Snyk `display_name` include the prefix.

Existing prefix handling elsewhere in the same module:

- `import_target_name()` — strips then re-applies `BB/` for reimport payload
- `_repo_slug_from_repository_name()` — strips `BB/` for slug extraction

Discovery lookup should follow the same convention.

## Goals / Non-Goals

**Goals:**

- Discovery fallback succeeds when diff `repository_name` has `BB/` prefix and discovery `repository_path` does not.
- Unprefixed diff names (Scotia / standard paths) continue to work unchanged.
- Single constant (`APP_TYPE_PREFIX`); no operator configuration.

**Non-Goals:**

- Stripping prefix from target `display_name` matching (both sides already agree in production).
- Stripping prefix from discovery `repository_path` at index time (discovery stays canonical).
- Making prefix configurable per tenant via CLI.
- Changing Stage 1 discovery output or diff generation.

## Decisions

### 1. Strip prefix only at discovery lookup time

**Choice:** Add a helper `discovery_lookup_name(repository_name: str) -> str` that returns `repository_name[len(APP_TYPE_PREFIX):]` when the name starts with `APP_TYPE_PREFIX`, otherwise returns `repository_name` unchanged. Use that value as the discovery index key in `_lookup_discovery_coordinates`.

**Rationale:** Minimal change; discovery index stays keyed by canonical `repository_path`. Normalization is idempotent: unprefixed names pass through unchanged; prefixed names map to the discovery path.

**Alternative rejected:** CLI `--discovery-path-prefix` — prefix is already a project convention in `APP_TYPE_PREFIX`; automatic stripping avoids misconfiguration.

**Alternative rejected:** Index discovery rows under both prefixed and unprefixed keys — duplicates index entries and complicates ambiguity handling.

### 2. Preserve full name everywhere else

**Choice:** Do not mutate `DiffEntry.repository_name`. Only apply normalization inside `_lookup_discovery_coordinates`.

**Rationale:** Reports, delete matching (`find_targets_by_display_name`), and reimport `import_target_name()` expect the Snyk display name as stored in diff.

### 3. Shared helper location

**Choice:** Add `discovery_lookup_name()` in [`branch_mismatch_reimport.py`](../../../src/snyk/branch_mismatch_reimport.py) alongside `import_target_name()`, reusing `APP_TYPE_PREFIX` from `snyk.outputs`.

**Rationale:** Avoid duplicating prefix-stripping logic; both delete and reimport scripts already share `resolve_reimport_coordinates`.

### 4. Error messages

**Choice:** Keep error messages referencing original `entry.repository_name` (prefixed form) for operator clarity.

**Rationale:** Operators search logs/reports by the value in diff.json, not the normalized lookup key.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Future prefix change | Single constant `APP_TYPE_PREFIX` in `snyk/outputs.py` |
| Discovery row accidentally prefixed | Normalization only strips from diff side; rare edge case out of scope |
| False match after normalization | Existing `apm_code` disambiguation rules unchanged |
| Bitbucket Cloud coordinate shape from path | Separate concern if reimport fails after discovery match |

## Migration Plan

1. Implement `discovery_lookup_name()` and update `_lookup_discovery_coordinates`.
2. Add unit tests: prefixed diff + unprefixed discovery; confirm existing unprefixed tests pass.
3. No CLI or operator workflow changes — existing `--discovery discovery.json` continues to work.
4. UAT with production-shaped fixtures: diff `BB/tcannell-test/juice-shop`, discovery path `tcannell-test/juice-shop`.

## Open Questions

- Bitbucket Cloud reimport may need owner/repo instead of projectKey/repoSlug when coordinates are derived from path — track separately if UAT fails after discovery match succeeds.
