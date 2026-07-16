## Why

Scotia single-tenant UAT still cannot reconcile branch-mismatched targets. The monolithic [`scripts/reimport_mismatched_targets.py`](../../../scripts/reimport_mismatched_targets.py) matches targets using `attributes.target_reference` from the **Targets API**, but on Scotia ST that field is always `None`. Branch is available on **Project** resources instead. Delete matching therefore always fails (`target_not_found`), and the prior UAT fix ([`2026-07-16-fix-branch-reconciliation-uat`](../../archive/2026-07-16-fix-branch-reconciliation-uat/)) assumed the wrong API as authoritative.

Rami proposes splitting the workflow: a simple delete script driven by `diff.json`, then a separate step to generate a `snyk-api-import` targets file and reimport.

## What Changes

- **Diff / lookup pipeline:** Use **Projects API** `attributes.target_reference` (keyed by target id) as the canonical branch for `output.json` and `diff.json` generation on single-tenant.
- **Delete script:** New [`scripts/delete_mismatched_targets.py`](../../../scripts/delete_mismatched_targets.py) — resolve org by `apm_code`, match target by `repository_name` == `display_name` only; `GET` target detail; `DELETE`; write optional delete manifest for reimport coordinates.
- **Reimport targets generator:** New [`scripts/generate_branch_reimport_targets.py`](../../../scripts/generate_branch_reimport_targets.py) — build `{ "targets": [...] }` batch JSON from diff + manifest for `snyk-api-import import`.
- **Client helper:** Index `target_id → target_reference` from REST projects for lookup/diff scripts.
- **Migration:** Deprecate or reimplement [`scripts/reimport_mismatched_targets.py`](../../../scripts/reimport_mismatched_targets.py) as a two-step wrapper.

**Out of scope:**

- Stage 1–4 pipeline changes.
- Broker or discovery logic.
- Customer-owned security.yaml comparison ( [`scripts/branch_diff.py`](../../../scripts/branch_diff.py) stays external).

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `branch-mismatch-target-reimport`: Projects API branch provenance; delete by `display_name` only; split delete + reimport scripts; delete manifest for enrichment.

## Impact

- **Code**: [`src/integrations/snyk/client.py`](../../../src/integrations/snyk/client.py), new [`src/snyk/branch_mismatch_delete.py`](../../../src/snyk/branch_mismatch_delete.py), new [`src/snyk/branch_mismatch_import_targets.py`](../../../src/snyk/branch_mismatch_import_targets.py), [`src/snyk/branch_mismatch_reimport.py`](../../../src/snyk/branch_mismatch_reimport.py) (shared helpers / deprecation), [`scripts/lookup_target_reference.py`](../../../scripts/lookup_target_reference.py), new scripts under [`scripts/`](../../../scripts/).
- **Tests**: new unit tests for projects branch index, delete-by-display-name, manifest + import batch generation.
- **Docs**: [`README.md`](../../../README.md) operator runbook (delete → generate targets → snyk-api-import).
- **APIs**: Snyk REST Projects (branch index), Targets (list/get/delete), external `snyk-api-import`.
