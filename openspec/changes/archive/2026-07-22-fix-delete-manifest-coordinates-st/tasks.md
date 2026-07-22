## 1. Coordinate resolution

- [x] 1.1 Add `load_discovery_coordinate_index()` (repository_name → project_key, repo_slug; apm_code disambiguation) using `row_repo_key` from [`src/common/output_state.py`](../../../src/common/output_state.py)
- [x] 1.2 Add `resolve_reimport_coordinates(target_detail, entry, discovery_index?)` in [`src/snyk/branch_mismatch_reimport.py`](../../../src/snyk/branch_mismatch_reimport.py) with ordered fallback and `coordinate_source`
- [x] 1.3 Unit tests for resolution chain: target-only, discovery fallback, fail-closed, ambiguous discovery

## 2. Delete script integration

- [x] 2.1 Wire discovery index + resolver into [`run_branch_mismatch_delete`](../../../src/snyk/branch_mismatch_delete.py); include `coordinate_source` in manifest entries
- [x] 2.2 Add `--discovery PATH` to [`scripts/delete_mismatched_targets.py`](../../../scripts/delete_mismatched_targets.py)
- [x] 2.3 Extend [`tests/test_branch_mismatch_delete.py`](../../../tests/test_branch_mismatch_delete.py): ST-shaped target GET (no projectKey) + discovery success/failure

## 3. Docs / verification

- [x] 3.1 Update README delete runbook: `--discovery discovery.json` on single-tenant; example command
- [x] 3.2 UAT checklist note: confirm customer repo `BB/uat-bitbucket-java-sample` with discovery file
- [x] 3.3 Run pytest for branch mismatch delete + resolver tests
