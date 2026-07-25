## 1. Retract misinformation

- [x] 1.1 Remove "single-tenant omits target_reference" language from README branch remediation section, `lookup_target_reference.py`, `delete_mismatched_targets.py`, and `reimport_mismatched_targets.py` docstrings
- [x] 1.2 Replace with correct model: Targets API = identity; Projects API = branch (all tenants)

## 2. Target matching fix

- [x] 2.1 Replace `_find_matching_targets` branch filter with shared display-name-only matcher (import or extract from [`branch_mismatch_delete.py`](../../../src/snyk/branch_mismatch_delete.py))
- [x] 2.2 Remove branch-centric `not_found` diagnostics (`same_display_name_branches`); keep `near_match_display_names`
- [x] 2.3 Wire `resolve_reimport_coordinates` with discovery index in monolithic reimport when `--discovery` is set
- [x] 2.4 Update [`tests/test_branch_mismatch_reimport.py`](../../../tests/test_branch_mismatch_reimport.py): Scotia case should match target without branch on Targets API; remove tests asserting dual-field match behavior

## 3. Discovery coordinate index

- [x] 3.1 Change `load_discovery_coordinate_index` to key by `repository_path` instead of discovery `repository_name`
- [x] 3.2 Update [`tests/test_branch_mismatch_coordinates.py`](../../../tests/test_branch_mismatch_coordinates.py) with juice-shop example (path matches diff, slug differs)
- [x] 3.3 Verify delete script path uses updated index (shared helper)

## 4. Integration type flag

- [x] 4.1 Generalize `pick_bitbucket_server_integration_id` → `pick_integration_id(integrations, integration_type)` in [`client.py`](../../../src/integrations/snyk/client.py); keep existing function as thin wrapper
- [x] 4.2 Add `integration_type: str = "bitbucket-server"` to `BranchMismatchReimportOptions`
- [x] 4.3 Filter matched targets by org integration id when integration relationship is present on list payload
- [x] 4.4 Add `--integration-type` to [`scripts/reimport_mismatched_targets.py`](../../../scripts/reimport_mismatched_targets.py) CLI (choices: `bitbucket-server`, `bitbucket-cloud`)
- [x] 4.5 Unit tests for integration-type filtering

## 5. Monolithic CLI parity

- [x] 5.1 Add `--discovery` to `reimport_mismatched_targets.py`
- [x] 5.2 Update script docstring: remove incorrect deprecation rationale; document correct API model
- [x] 5.3 README: document `--integration-type bitbucket-cloud` for testing vs prod `bitbucket-server` default

## 6. Test fixture cleanup

- [x] 6.1 Update [`tests/test_snyk_client_targets.py`](../../../tests/test_snyk_client_targets.py) target mocks: omit `target_reference` from list/get fixtures unless explicitly testing ignore behavior
- [x] 6.2 Audit remaining branch mismatch tests for realistic Targets API payloads

## 7. Verification

- [x] 7.1 Run `pytest tests/test_branch_mismatch_reimport.py tests/test_branch_mismatch_coordinates.py tests/test_branch_mismatch_delete.py`
- [x] 7.2 Manual dry-run against cloud test org: `--integration-type bitbucket-cloud --dry-run --limit 5 --input data/diff.json`
