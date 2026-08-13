## 1. Package identity

- [ ] 1.1 Rename `[project].name` to `snyk-org-repo-mapper` in `pyproject.toml`
- [ ] 1.2 Update `[project].description` to multi-SCM / Snyk onboarding wording
- [ ] 1.3 Regenerate `uv.lock` (`uv lock`)

## 2. Documentation

- [ ] 2.1 Update `README.md` — title `# snyk-org-repo-mapper`, intro paragraph (Bitbucket **and** GitHub Stage 1), installation section package name
- [ ] 2.2 Update `openspec/project.md` — title and one-paragraph summary (Bitbucket + GitHub + Snyk stages)
- [ ] 2.3 Grep active tree (exclude `openspec/changes/archive/`) for `bitbucket-org-repo-mapper`; fix any remaining hits

## 3. OpenSpec specification

- [ ] 3.1 Merge change delta Purpose text into `openspec/specs/three-stage-snyk-pipeline/spec.md` (replace `TBD` placeholder)
- [ ] 3.2 Run `openspec validate rename-snyk-org-repo-mapper`

## 4. Code comments (no behavior change)

- [ ] 4.1 Update console-script docstrings in `src/commands/dispatch.py` if they imply Bitbucket-only product name
- [ ] 4.2 Update any CLI help strings that say `bitbucket-org-repo-mapper` (e.g. `bitbucket_cli.py`)

## 5. Verification

- [ ] 5.1 `pytest` (no regressions)
- [ ] 5.2 Confirm `pip install -e .` exposes same `repo-mapper-*` scripts
