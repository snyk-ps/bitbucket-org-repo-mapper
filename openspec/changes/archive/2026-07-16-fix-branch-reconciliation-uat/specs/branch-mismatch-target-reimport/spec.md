# branch-mismatch-target-reimport Specification (change delta)

## MODIFIED Requirements

### Requirement: Match target by repository_name and target_reference

For each entry, the script SHALL list all targets in the resolved org via `GET /rest/orgs/{org_id}/targets` with query parameter `exclude_empty=false`, SHALL NOT rely on a server-side `display_name` filter for matching, and SHALL find exactly one target where `attributes.display_name` equals `repository_name` and `attributes.target_reference` equals `target_reference` (case-sensitive), matching client-side against the full paginated list.

#### Scenario: Single matching target found

- **WHEN** exactly one target matches both fields
- **THEN** the script proceeds to delete (or dry-run skip) that target

#### Scenario: No matching target

- **WHEN** zero targets match
- **THEN** the entry is recorded under `not_found` with reason `target_not_found`

#### Scenario: Ambiguous match

- **WHEN** more than one target matches
- **THEN** the entry is recorded under `ambiguous`
- **AND** no delete is performed

#### Scenario: Already correct branch skipped

- **WHEN** `production_branch` equals `target_reference`
- **THEN** the entry is recorded under `skipped` with reason `already_correct`

#### Scenario: Same display name different branch

- **WHEN** zero targets match `target_reference`
- **AND** one or more targets share `repository_name` on other branches
- **THEN** the `not_found` entry includes `same_display_name_branches` listing those branch values

## ADDED Requirements

### Requirement: Diff target_reference provenance

The `target_reference` field in `diff.json` SHALL reflect the current branch on the Snyk **target** resource (`attributes.target_reference`), not project-level `target_reference` alone, so it matches the reimport lookup key.

#### Scenario: Diff builder uses target branch

- **WHEN** `lookup_target_reference.py` (or equivalent diff producer) emits an entry for a Bitbucket Server target
- **THEN** `target_reference` is read from the target resource `attributes.target_reference`

### Requirement: Actionable target_not_found diagnostics

When an entry is recorded under `not_found` with reason `target_not_found`, the report entry SHALL include `candidates_returned` (count of targets listed for the org) and MAY include `same_display_name_branches` and `near_match_display_names` to aid operator triage.

#### Scenario: Diagnostics on failed lookup

- **WHEN** no target matches `repository_name` and `target_reference`
- **THEN** the `not_found` entry includes `reason: target_not_found` and `candidates_returned`
- **AND** when applicable includes `same_display_name_branches` or `near_match_display_names`
