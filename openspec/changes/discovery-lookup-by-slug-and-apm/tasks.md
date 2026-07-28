## 1. Discovery index and lookup

- [x] 1.1 Replace path-keyed index with `(repository_name, apm_code)` keys in `load_discovery_coordinate_index`
- [x] 1.2 Rename/replace `discovery_lookup_name` with `discovery_lookup_slug` (strip `BB/`, take final path segment)
- [x] 1.3 Update `_lookup_discovery_coordinates` to require slug + `apm_code` match
- [x] 1.4 Update type alias / docstrings for `DiscoveryCoordinateIndex`

## 2. Tests

- [x] 2.1 Primary fixture: diff `BB/juice-shop` + apm `ABCD`, discovery path `tcannell-test/juice-shop`, name `juice-shop` → `(tcannell-test, juice-shop)`
- [x] 2.2 Unprefixed diff `tcannell-test/juice-shop` still resolves via slug `juice-shop`
- [x] 2.3 Scotia-style unprefixed `MYPROJ/my-service` still works
- [x] 2.4 Ambiguous: same slug + same apm in two paths → `ambiguous_discovery`
- [x] 2.5 No match: wrong apm → `discovery_not_found`
- [x] 2.6 Remove or rewrite tests that assumed `BB/tcannell-test/juice-shop` as the production display name
- [x] 2.7 Run `pytest tests/test_branch_mismatch_coordinates.py tests/test_branch_mismatch_delete.py tests/test_branch_mismatch_reimport.py`

## 3. Spec and docs

- [x] 3.1 README: document slug + apm discovery matching and `BB/{slug}` display name convention

## 4. Verification

- [x] 4.1 Manual dry-run with production-shaped fixtures: diff `BB/juice-shop`, discovery `tcannell-test/juice-shop` / `juice-shop`
