## 1. API / diff pipeline

- [x] 1.1 Add projects branch index helper in [`src/integrations/snyk/client.py`](../../../src/integrations/snyk/client.py) (target id → `target_reference` from REST projects, filter `bitbucket-server` origin)
- [x] 1.2 Rewrite [`scripts/lookup_target_reference.py`](../../../scripts/lookup_target_reference.py) to use projects-only branch (do not require target `attributes.target_reference`)
- [x] 1.3 Add unit tests for projects branch index in [`tests/test_snyk_client_projects_branch_index.py`](../../../tests/test_snyk_client_projects_branch_index.py) or extend existing client tests

## 2. Delete script

- [x] 2.1 Add [`src/snyk/branch_mismatch_delete.py`](../../../src/snyk/branch_mismatch_delete.py): org resolve, display_name match, GET detail, DELETE, manifest output
- [x] 2.2 Add [`scripts/delete_mismatched_targets.py`](../../../scripts/delete_mismatched_targets.py) CLI (`--input`, `--output`, `--manifest`, `--dry-run`, `--limit`)
- [x] 2.3 Add tests in [`tests/test_branch_mismatch_delete.py`](../../../tests/test_branch_mismatch_delete.py): match, ambiguous, dry-run, manifest shape

## 3. Reimport targets generator

- [x] 3.1 Add [`src/snyk/branch_mismatch_import_targets.py`](../../../src/snyk/branch_mismatch_import_targets.py): build batch JSON from manifest using [`build_import_payload`](../../../src/snyk/branch_mismatch_reimport.py)
- [x] 3.2 Add [`scripts/generate_branch_reimport_targets.py`](../../../scripts/generate_branch_reimport_targets.py) CLI
- [x] 3.3 Add tests in [`tests/test_branch_mismatch_import_targets.py`](../../../tests/test_branch_mismatch_import_targets.py)

## 4. Migration / docs

- [x] 4.1 Deprecate [`scripts/reimport_mismatched_targets.py`](../../../scripts/reimport_mismatched_targets.py) in docstring; optionally reimplement as two-step wrapper
- [x] 4.2 Update [`README.md`](../../../README.md): new runbook (regenerate diff → delete → generate targets → snyk-api-import); note Projects API branch vs Targets API on single-tenant
- [x] 4.3 Update [`tests/test_branch_mismatch_reimport.py`](../../../tests/test_branch_mismatch_reimport.py) if shared helpers move or monolithic flow changes

## 5. Verification

- [x] 5.1 Run pytest for new and related branch mismatch tests
- [x] 5.2 Document UAT checklist in README: regenerate output.json/diff.json; delete dry-run `--limit 5`; generate targets; live reimport on one repo
