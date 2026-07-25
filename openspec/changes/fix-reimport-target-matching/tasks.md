## 1. Retract misinformation

- [ ] 1.1 Remove "single-tenant omits target_reference" language from README branch remediation section, `lookup_target_reference.py`, `delete_mismatched_targets.py`, and `reimport_mismatched_targets.py` docstrings
- [ ] 1.2 Replace with correct model: Targets API = identity; Projects API = branch (all tenants)

## 2. Target matching fix

- [ ] 2.1 Replace `_find_matching_targets` branch filter with shared display-name-only matcher (import or extract from [`branch_mismatch_delete.py`](../../../src/snyk/branch_mismatch_delete.py))
- [ ] 2.2 Remove branch-centric `not_found` diagnostics (`same_display_name_branches`); keep `near_match_display_names`
- [ ] 2.3 Wire `resolve_reimport_coordinates` with discovery index in monolithic reimport when `--discovery` is set
- [ ] 2.4 Update [`tests/test_branch_mismatch_reimport.py`](../../../tests/test_branch_mismatch_reimport.py): Scotia case should match target without branch on Targets API; remove tests asserting dual-field match behavior

## 3. Discovery coordinate index

- [ ] 3.1 Change `load_discovery_coordinate_index` to key by `repository_path` instead of discovery `repository_name`
- [ ] 3.2 Update [`tests/test_branch_mismatch_coordinates.py`](../../../tests/test_branch_mismatch_coordinates.py) with juice-shop example (path matches diff, slug differs)
- [ ] 3.3 Verify delete script path uses updated index (shared helper)

## 4. Integration type flag

- [ ] 4.1 Generalize `pick_bitbucket_server_integration_id` → `pick_integration_id(integrations, integration_type)` in [`client.py`](../../../src/integrations/snyk/client.py); keep existing function as thin wrapper
- [ ] 4.2 Add `integration_type: str = "bitbucket-server"` to `BranchMismatchReimportOptions`
- [ ] 4.3 Filter matched targets by org integration id when integration relationship is present on list payload
- [ ] 4.4 Add `--integration-type` to [`scripts/reimport_mismatched_targets.py`](../../../scripts/reimport_mismatched_targets.py) CLI (choices: `bitbucket-server`, `bitbucket-cloud`)
- [ ] 4.5 Unit tests for integration-type filtering

## 5. Monolithic CLI parity

- [ ] 5.1 Add `--discovery` to `reimport_mismatched_targets.py`
- [ ] 5.2 Update script docstring: remove incorrect deprecation rationale; document correct API model
- [ ] 5.3 README: document `--integration-type bitbucket-cloud` for testing vs prod `bitbucket-server` default

## 6. Test fixture cleanup

- [ ] 6.1 Update [`tests/test_snyk_client_targets.py`](../../../tests/test_snyk_client_targets.py) target mocks: omit `target_reference` from list/get fixtures unless explicitly testing ignore behavior
- [ ] 6.2 Audit remaining branch mismatch tests for realistic Targets API payloads

## 7. Verification

- [ ] 7.1 Run `pytest tests/test_branch_mismatch_reimport.py tests/test_branch_mismatch_coordinates.py tests/test_branch_mismatch_delete.py`
- [ ] 7.2 Manual dry-run against cloud test org: `--integration-type bitbucket-cloud --dry-run --limit 5 --input data/diff.json`
