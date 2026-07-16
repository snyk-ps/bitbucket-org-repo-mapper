## Why

Scotia UAT reported 896 repos imported on the wrong branch. Branch reconciliation (`scripts/reimport_mismatched_targets.py`) drops valid entries as `target_not_found` instead of delete-and-reimport, and Stage 4 (`snyk-post-import-cleanup`) fails with HTTP 400 on live project-settings PATCH while dry-run succeeds. Both issues appear only on single-tenant UAT and stem from Snyk API identification or payload requirements not met by the current implementation.

## What Changes

- **Branch mismatch reimport:** List all org targets with `exclude_empty=false`; match client-side on `display_name` + `target_reference` (no server-side `display_name` filter); add actionable `target_not_found` diagnostics (`candidates_returned`, `same_display_name_branches`, `near_match_display_names`).
- **Diff producer alignment:** Fix [`scripts/lookup_target_reference.py`](../../../scripts/lookup_target_reference.py) so `target_reference` in diff output comes from the **target** resource (`attributes.target_reference`), matching the reimport matcher — not from project attributes alone.
- **Stage 4 PATCH:** Require `SNYK_USER_ID` (or `--user-id`); REST PATCH project settings with `relationships.owner` in the JSON:API body; sync spec requirements to REST projects API (not v1 PUT).
- **Stage 4 resilience:** Optionally treat PATCH HTTP 404 (project already deleted) as skip-with-reason rather than blocking the org.
- **Docs:** README updates for diff field provenance, diagnostics, `SNYK_USER_ID`, and single-tenant `SNYK_API`.

**Out of scope:**

- Generating `diff.json` from security.yaml (external comparison).
- Merging branch reimport into Stage 4 CLI.
- Broker or discovery pipeline changes.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `branch-mismatch-target-reimport`: Target listing (`exclude_empty=false`), client-side matching, `target_not_found` diagnostics, and diff `target_reference` provenance.
- `snyk-post-import-cleanup`: REST project listing/PATCH with required owner `user_id`; CLI credential validation; PATCH error handling for missing projects.

## Impact

- **Code**: [`src/integrations/snyk/client.py`](../../../src/integrations/snyk/client.py), [`src/snyk/branch_mismatch_reimport.py`](../../../src/snyk/branch_mismatch_reimport.py), [`src/snyk/post_import_cleanup.py`](../../../src/snyk/post_import_cleanup.py), [`src/commands/snyk_post_import_cleanup_cli.py`](../../../src/commands/snyk_post_import_cleanup_cli.py), [`scripts/lookup_target_reference.py`](../../../scripts/lookup_target_reference.py).
- **Tests**: [`tests/test_branch_mismatch_reimport.py`](../../../tests/test_branch_mismatch_reimport.py), [`tests/test_snyk_client_targets.py`](../../../tests/test_snyk_client_targets.py), [`tests/test_post_import_cleanup.py`](../../../tests/test_post_import_cleanup.py), [`tests/test_snyk_client_post_import_cleanup.py`](../../../tests/test_snyk_client_post_import_cleanup.py).
- **Docs**: [`README.md`](../../../README.md).
- **APIs**: Snyk REST Targets (`GET` with `exclude_empty=false`, `DELETE`); Snyk REST Projects (`GET`, `PATCH` with `relationships.owner`, `DELETE`).
- **Related change**: [`fix-dockerfile-project-type-filter`](../../fix-dockerfile-project-type-filter/) v1 `types=` fix is superseded by REST client-side filtering — reconcile when archiving.
