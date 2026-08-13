## Context

- Workspace folder: **`snyk-org-repo-mapper`**
- Package name today: **`bitbucket-org-repo-mapper`** (`pyproject.toml`, `uv.lock`)
- Stage 1 ingress: Bitbucket crawl, spreadsheet + Bitbucket, GitHub org crawl (`discover github` shipped in archived change `2026-07-08-github-discovery`)
- Console scripts use prefix **`repo-mapper-*`**, not `bitbucket-*`

## Goals / Non-Goals

**Goals:**

- Single canonical product name: **`snyk-org-repo-mapper`**
- README and OpenSpec describe a **Snyk org/repo mapping pipeline** with multiple SCM sources
- PyPI/setuptools **`project.name`** aligns with repo directory name
- **`three-stage-snyk-pipeline`** Purpose documents identity for future changes

**Non-Goals:**

- Renaming console entry points (`repo-mapper-*` stays as-is)
- Rewriting archived proposals/spec deltas
- SCM-agnostic renaming of JSON schema fields (separate, larger change)

## Decisions

### 1. Canonical name

Use **`snyk-org-repo-mapper`** everywhere for **application / package / documentation** identity. Hyphenated kebab-case matches repo folder and existing OpenSpec conventions.

### 2. Package description string

Update `pyproject.toml` **`description`** from Bitbucket-only to:

> Staged discovery and Snyk onboarding for Bitbucket Server and GitHub repositories—org planning, broker setup, import files, and post-import cleanup.

### 3. Console scripts: keep `repo-mapper-*`

**Decision:** Do **not** rename `[project.scripts]` in this change.

**Rationale:** Scripts are already SCM-neutral; renaming would break existing CI/shell scripts without functional benefit. README SHALL list scripts under a subsection for **`snyk-org-repo-mapper`** console entry points.

### 4. Spec delta scope

Update **`## Purpose`** in `three-stage-snyk-pipeline/spec.md` and add an **ADDED** requirement for product identity (package name + README title). No changes to existing stage requirement text unless audit finds contradictory Bitbucket-only wording.

### 5. Archived OpenSpec history

Leave **`openspec/changes/archive/**`** unchanged. Historical proposals correctly described Bitbucket-first evolution.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Operators pinned `pip install bitbucket-org-repo-mapper` | Document rename in README **Installation**; note old name is retired |
| Internal docs link old package name | Grep repo for `bitbucket-org-repo-mapper` before merge (exclude archive) |
| `uv.lock` drift | Run `uv lock` after `pyproject.toml` name change |

## Migration Plan

No runtime migration. After pull:

```bash
uv sync   # or pip install -e .
```

Console usage unchanged: `repo-mapper-discover-github`, `python src/main.py discover github`, etc.

## Open Questions

_(none)_
