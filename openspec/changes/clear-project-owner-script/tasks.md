## 1. Client extension

- [ ] 1.1 Add `SnykRestClient.clear_project_owner(org_id, project_id)` — v1 PUT `{"owner": null}` to `/org/{orgId}/project/{projectId}` in [`src/integrations/snyk/client.py`](../../../src/integrations/snyk/client.py)
- [ ] 1.2 Optionally extend `normalize_rest_project` or add helper to extract owner id from REST project resource (for skip-if-unassigned)
- [ ] 1.3 Unit test for v1 PUT URL, method, and body in [`tests/test_snyk_client_post_import_cleanup.py`](../../../tests/test_snyk_client_post_import_cleanup.py) or new client test file

## 2. Orchestration library

- [ ] 2.1 Add [`src/snyk/clear_project_owners.py`](../../../src/snyk/clear_project_owners.py): resolve org list from `--group` or `--orgs`, iterate projects, clear owner, build versioned report (`cleared`, `skipped`, `failed`)
- [ ] 2.2 Support `--dry-run`, `--limit` (max projects), partial-failure continue
- [ ] 2.3 Tests in [`tests/test_clear_project_owners.py`](../../../tests/test_clear_project_owners.py) (mocked client, dry-run, failure aggregation)

## 3. Scripts entrypoint

- [ ] 3.1 Add [`scripts/clear_project_owners.py`](../../../scripts/clear_project_owners.py) with `--group GROUP_ID` or `--orgs ORG_ID[,ORG_ID...]` (mutually exclusive, one required), `--env-file`, `--output` (default `clear-project-owner-report.json`), `--dry-run`, `--limit`
- [ ] 3.2 Validate: reject both/neither scope flags; reject empty `--orgs`

## 4. Settings / group handling

- [ ] 4.1 Allow script to run with `--orgs` without `SNYK_GROUP_ID` (minimal settings change or local construction in script)

## 5. Documentation

- [ ] 5.1 Update [`README.md`](../../../README.md) `scripts/` section: purpose (Stage 4 cleanup), example invocations, `--dry-run` first, token permissions
- [ ] 5.2 Cross-reference future Stage 4 owner-preservation change

## 6. Verification

- [ ] 6.1 Run pytest for new and related tests
- [ ] 6.2 Manual UAT: `--dry-run --group <uat-group-id>` then live on one org
