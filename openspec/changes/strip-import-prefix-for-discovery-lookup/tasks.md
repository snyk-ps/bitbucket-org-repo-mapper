## 1. Discovery lookup normalization

- [ ] 1.1 Add `discovery_lookup_name(repository_name: str) -> str` in `branch_mismatch_reimport.py`, stripping `APP_TYPE_PREFIX` when present
- [ ] 1.2 Update `_lookup_discovery_coordinates` to use `discovery_lookup_name(entry.repository_name)` as the index key
- [ ] 1.3 Keep error messages referencing original `entry.repository_name` for operator clarity

## 2. Tests

- [ ] 2.1 Add test: diff `BB/tcannell-test/juice-shop`, discovery path `tcannell-test/juice-shop` → coordinates `(tcannell-test, juice-shop)`
- [ ] 2.2 Confirm existing unprefixed juice-shop test in `test_branch_mismatch_coordinates.py` still passes
- [ ] 2.3 Add test: diff without prefix still matches unprefixed discovery (Scotia path)

## 3. Documentation

- [ ] 3.1 README: note that discovery fallback strips `BB/` from diff `repository_name` when matching `repository_path`
- [ ] 3.2 Add brief comment on `_lookup_discovery_coordinates` explaining prefix stripping

## 4. Verification

- [ ] 4.1 Run `pytest tests/test_branch_mismatch_coordinates.py tests/test_branch_mismatch_reimport.py tests/test_branch_mismatch_delete.py`
- [ ] 4.2 Manual dry-run with production-shaped fixtures: diff with `BB/` prefix, discovery without
