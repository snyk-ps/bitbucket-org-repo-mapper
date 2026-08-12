## 1. Branch mismatch target lookup

- [x] 1.1 Verify `SnykRestClient.iter_org_targets` defaults `exclude_empty=false` and appends query param in [`src/integrations/snyk/client.py`](../../../src/integrations/snyk/client.py)
- [x] 1.2 Verify full-org client-side match and per-org cache in [`src/snyk/branch_mismatch_reimport.py`](../../../src/snyk/branch_mismatch_reimport.py) (no server-side `display_name` filter)
- [x] 1.3 Fix [`scripts/lookup_target_reference.py`](../../../scripts/lookup_target_reference.py): read `target_reference` from target `attributes`; use `SNYK_API` env and `token {SNYK_TOKEN}` auth header
- [x] 1.4 Extend tests in [`tests/test_branch_mismatch_reimport.py`](../../../tests/test_branch_mismatch_reimport.py) and [`tests/test_snyk_client_targets.py`](../../../tests/test_snyk_client_targets.py) for diagnostics and `exclude_empty=false`
- [x] 1.5 Update README branch mismatch section: diff field provenance and `target_not_found` diagnostic fields

## 2. Stage 4 project settings PATCH

- [x] 2.1 Verify `_build_project_patch_body` and `update_project_settings` REST PATCH with `relationships.owner` in [`src/integrations/snyk/client.py`](../../../src/integrations/snyk/client.py)
- [x] 2.2 Verify CLI `SNYK_USER_ID` / `--user-id` validation in [`src/commands/snyk_post_import_cleanup_cli.py`](../../../src/commands/snyk_post_import_cleanup_cli.py)
- [x] 2.3 Add or extend test asserting PATCH body includes `relationships.owner` in [`tests/test_snyk_client_post_import_cleanup.py`](../../../tests/test_snyk_client_post_import_cleanup.py)
- [x] 2.4 Implement PATCH HTTP 404 skip (`reason: project_not_found`) in [`src/snyk/post_import_cleanup.py`](../../../src/snyk/post_import_cleanup.py)
- [x] 2.5 Update README Stage 4 section: `SNYK_USER_ID` requirement and dry-run vs live PATCH behavior

## 3. Verification

- [x] 3.1 Run `pytest tests/test_branch_mismatch_reimport.py tests/test_snyk_client_targets.py tests/test_post_import_cleanup.py tests/test_snyk_client_post_import_cleanup.py -q`
- [x] 3.2 Document UAT re-test checklist in README or change notes: dry-run reimport on `BB/uat-bitbucket-java-sample`; live Stage 4 on one org with valid `SNYK_USER_ID`

## 4. Related cleanup

- [x] 4.1 Reconcile or close [`fix-dockerfile-project-type-filter`](../../fix-dockerfile-project-type-filter/) (superseded by REST client-side dockerfile filter)
