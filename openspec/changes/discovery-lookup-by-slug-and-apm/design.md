## Context

| Artifact | Example |
|----------|---------|
| diff `repository_name` (Snyk display name) | `BB/juice-shop` |
| diff `apm_code` | `ABCD` |
| discovery `repository_path` | `tcannell-test/juice-shop` |
| discovery `repository_name` | `juice-shop` |
| discovery `apm_code` | `ABCD` |

Stage 3 sets `target.name = BB/{slug}` in [`build_snyk_import_document`](../../../src/snyk/outputs.py). The prior fix ([`2026-07-27-strip-import-prefix-for-discovery-lookup`](../../archive/2026-07-27-strip-import-prefix-for-discovery-lookup/)) normalized diff names to match `repository_path`, which only works when the display name includes the project segment.

Current index in [`branch_mismatch_reimport.py`](../../../src/snyk/branch_mismatch_reimport.py) is keyed by `repository_path`. Lookup strips `BB/` from diff `repository_name` and searches that key — so `BB/juice-shop` becomes `juice-shop`, which never matches `tcannell-test/juice-shop`.

## Goals / Non-Goals

**Goals:**

- Discovery fallback succeeds for `BB/{slug}` diff names against discovery rows with different `repository_path` prefixes.
- Unprefixed diff names (`MYPROJ/my-service`, `tcannell-test/juice-shop`) continue to resolve via slug extraction.
- Lookup is deterministic when slug + `apm_code` uniquely identifies a discovery row.

**Non-Goals:**

- Fuzzy or partial matching on display names for delete.
- Changing how discovery.json is produced in Stage 1.
- Inferring project key from diff `repository_name` alone without discovery.

## Decisions

### 1. Index by discovery slug, not path

**Choice:** `load_discovery_coordinate_index` builds `(repository_name, apm_code) → (project_key, repo_slug)` from each row's `repository_name` and `apm_code`, with coordinates parsed from `repository_path`.

**Rationale:** Discovery `repository_name` is the canonical Bitbucket slug. Diff side may omit project/workspace entirely when Stage 3 naming applies.

**Rejected:** Keep path-keyed index and strip only `BB/` — fails for `BB/juice-shop` vs `tcannell-test/juice-shop`.

### 2. Slug extraction from diff `repository_name`

**Choice:** Add `discovery_lookup_slug(repository_name: str) -> str`:

1. Strip `APP_TYPE_PREFIX` (`BB/`) when present.
2. If result contains `/`, take the segment after the final `/`.
3. Otherwise return the whole string.

Examples:

- `BB/juice-shop` → `juice-shop`
- `BB/tcannell-test/juice-shop` → `juice-shop` (backward compatible)
- `tcannell-test/juice-shop` → `juice-shop`
- `MYPROJ/my-service` → `my-service`

**Rationale:** Disregards any prefix/path on the diff side while preserving slug identity.

### 3. Match requires `apm_code`

**Choice:** Lookup uses `(discovery_lookup_slug(entry.repository_name), entry.apm_code)`. Fail with `discovery_not_found` when no row matches; fail with `ambiguous_discovery` when multiple rows share slug + apm (data error).

**Rationale:** Matches delete flow (org resolved by `apm_code`) and avoids cross-org slug collisions.

**Rejected:** Slug-only match with optional apm disambiguation — too loose when same slug exists under different APM codes in discovery.

### 4. Preserve delete matching and reports

**Choice:** Do not mutate `DiffEntry.repository_name`. Slug extraction applies only inside discovery coordinate lookup.

**Rationale:** Delete still matches exact Snyk `display_name`; reports stay aligned with diff.json.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Same slug under same APM in two projects | `ambiguous_discovery`; operator fixes discovery data |
| Stale discovery slug vs renamed repo | Same as today — refresh Stage 1 |
| Diff display name doesn't follow Stage 3 convention | Delete match may fail before discovery is consulted; out of scope |

## Migration Plan

1. Change index + lookup helpers; update superseded tests.
2. Run coordinate + delete + reimport test suites.
3. UAT with production fixtures: diff `BB/juice-shop`, discovery `tcannell-test/juice-shop` / `juice-shop`.

## Open Questions

- Should slug matching be case-sensitive? (Recommend: yes, consistent with existing delete matching.)
