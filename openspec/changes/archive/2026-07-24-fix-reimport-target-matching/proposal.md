## Why

Branch mismatch remediation matches targets for deletion using `attributes.target_reference` from the **Targets API**. That field is not part of the Targets API contract — branch information lives on **Projects** (`attributes.target_reference`), joined to targets by target id. See [Snyk Targets API](https://docs.snyk.io/developer-tools/snyk-api/reference/targets).

The monolithic [`scripts/reimport_mismatched_targets.py`](../../../scripts/reimport_mismatched_targets.py) therefore cannot reliably find targets on **any** tenant. This is not a single-tenant vs multi-tenant difference; the original v1 design and the archived [`fix-branch-reconciliation-uat`](../../archive/2026-07-16-fix-branch-reconciliation-uat/) "fix" both assumed a Targets API field that does not exist for this purpose.

## What Changes

- **Delete matching:** Match by `attributes.display_name == diff.repository_name` only. Delete the entire target. Never read or compare Targets API branch (it is not available).
- **Retract incorrect prior assumptions:** Remove "single-tenant omits target_reference" language from code comments, README, and specs. Branch was never on Targets API.
- **`--integration-type` flag:** Add to monolithic reimport (default `bitbucket-server`, allow `bitbucket-cloud`) for operator testing against cloud integrations.
- **Discovery coordinate lookup:** Index by `repository_path`, looked up via diff `repository_name`. Discovery `repository_name` (Bitbucket slug) is for import only, not delete matching.
- **Align monolithic with delete script:** Wire `--discovery`; share display-name matcher from [`branch_mismatch_delete.py`](../../../src/snyk/branch_mismatch_delete.py).
- **Tests:** Stop asserting Targets API returns `target_reference`. Test matchers against realistic target payloads (display_name only).

**Out of scope:** Generating `diff.json` from security.yaml; Stage 1–4 pipeline changes.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `branch-mismatch-target-reimport`: Correct API model (Projects = branch, Targets = identity); display-name-only delete; integration-type flag; discovery keyed by `repository_path`; retract Targets API branch assumptions.

## Impact

- **Code:** [`src/snyk/branch_mismatch_reimport.py`](../../../src/snyk/branch_mismatch_reimport.py), [`scripts/reimport_mismatched_targets.py`](../../../scripts/reimport_mismatched_targets.py), [`src/integrations/snyk/client.py`](../../../src/integrations/snyk/client.py), [`scripts/lookup_target_reference.py`](../../../scripts/lookup_target_reference.py), [`scripts/delete_mismatched_targets.py`](../../../scripts/delete_mismatched_targets.py), [`README.md`](../../../README.md)
- **Tests:** [`tests/test_branch_mismatch_reimport.py`](../../../tests/test_branch_mismatch_reimport.py), [`tests/test_snyk_client_targets.py`](../../../tests/test_snyk_client_targets.py), [`tests/test_branch_mismatch_coordinates.py`](../../../tests/test_branch_mismatch_coordinates.py)
- **APIs:** Snyk REST Targets (list/get/delete by `display_name`); Snyk REST Projects (branch for diff only); external `snyk-api-import`
