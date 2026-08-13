# three-stage-snyk-pipeline Specification (change delta)

## Purpose

**snyk-org-repo-mapper** is a staged Python CLI for onboarding SCM repositories into Snyk. **Stage 1** produces a versioned discovery JSON from one of: Bitbucket Server (full crawl), a spreadsheet-driven Bitbucket repo list, or GitHub organization repositories. **Stages 2–4** operate on Snyk APIs and local artifacts: org list generation, optional Universal Broker plan/apply and integration settings, import target enrichment with `orgId`/`integrationId`, and optional post-import cleanup. Bitbucket and GitHub are supported discovery sources; downstream stages are Snyk-centric and do not call the source SCM (except spreadsheet mode, which uses Bitbucket HTTP during Stage 1 only).

## ADDED Requirements

### Requirement: Product identity

The tool SHALL be named and documented as **snyk-org-repo-mapper**. Package metadata and primary documentation SHALL describe it as a multi-SCM Snyk onboarding pipeline, not a Bitbucket-only mapper.

#### Scenario: README names the product

- **WHEN** a reader opens the repository README
- **THEN** the title SHALL be **snyk-org-repo-mapper**
- **AND** the introduction SHALL describe Stage 1 as supporting Bitbucket and GitHub discovery

#### Scenario: Package metadata names the product

- **WHEN** a user inspects `pyproject.toml` `[project].name`
- **THEN** the value SHALL be `snyk-org-repo-mapper`

#### Scenario: Console scripts unchanged

- **WHEN** a user runs `pip install -e .`
- **THEN** the existing **`repo-mapper-*`** console entry points SHALL remain available on `PATH`
